"""Batch plate processor — headless, no Qt dependency.

Processes all wells in a plate directory through the DSP + basecall
pipeline, collecting sequences, quality scores, and alignment stats.

Usage (script):
    from batch import BatchProcessor
    bp = BatchProcessor('/path/to/MB1000_M13_DT')
    results = bp.run()
    bp.export_fastq('/output/dir')

Usage (CLI):
    python3 batch.py /path/to/MB1000_M13_DT --out /output/dir
"""
import os
import sys
import time
import numpy as np
from concurrent.futures import ThreadPoolExecutor, as_completed

from extract_training_data import parse_rsd, parse_esd
from constants import _TUNED_SSM
from dsp import dsp_full_pipeline, find_esd_subdirs
from basecall import (
    pc_call_bases_with_shifts, pc_call_bases_greedy,
    pc_signal_region, pc_estimate_mobility_shifts,
)
from quality import pmax_to_phred, quality_distribution
from trim import sliding_window_trim, trailing_trim
from export import write_fasta_multi, write_fastq_multi, write_fastq, write_phred_table

try:
    from cnn_confidence import get_estimator as _get_cnn
    _CNN_AVAILABLE = True
except Exception:
    _CNN_AVAILABLE = False

try:
    import cimarrontv as _cim
    _CIMARRON_AVAILABLE = True
except Exception:
    _CIMARRON_AVAILABLE = False

BASELINE = 'AsyLS'
BL_WINDOW = 50010
SMOOTH = 'Butterworth'
SM_WIN = 9
SM_ORD = 5
MATRIX_POINT = 'smoothed'
DEFAULT_SHIFT = [5, 11, 10, 10]
METHOD_GREEDY = 0
METHOD_CLUSTER = 1
DEFAULT_METHOD = METHOD_GREEDY
METHOD_CIMARRON_CNN = 2  # Cimarron engine + CNN scoring
DISTANCE = 5
PROM_FRAC = 0.200
NORM_WINDOW = 800
TOLERANCE = 3
MIN_SIGNAL_FRAC = 0.30
FILL_GAP = 1
FILL_MARGIN_PCT = 30


def _intensity_confidence(intens):
    """Fallback: extract confidence from peak intensities (list-of-dicts)."""
    if intens and isinstance(intens[0], dict):
        arr = np.array([max(d.values()) for d in intens], dtype=np.float64)
    else:
        arr = np.asarray(intens, dtype=np.float64) if len(intens) else np.array([0.5])
    return np.clip(arr / (arr.max() + 1e-10), 0, 1)


class WellResult:
    __slots__ = [
        'well', 'sequence', 'phred', 'positions', 'intensities',
        'confidence', 'mean_q', 'median_q', 'q20_pct', 'q30_pct',
        'total_bases', 'trimmed_seq', 'trimmed_phred', 'trim_start',
        'trim_end', 'success', 'error', 'elapsed',
    ]

    def __init__(self):
        self.well = ''
        self.sequence = ''
        self.phred = np.array([], dtype=np.int8)
        self.positions = np.array([], dtype=np.int64)
        self.intensities = np.array([], dtype=np.float64)
        self.confidence = np.array([], dtype=np.float64)
        self.mean_q = 0.0
        self.median_q = 0.0
        self.q20_pct = 0.0
        self.q30_pct = 0.0
        self.total_bases = 0
        self.trimmed_seq = ''
        self.trimmed_phred = np.array([], dtype=np.int8)
        self.trim_start = 0
        self.trim_end = 0
        self.success = False
        self.error = ''
        self.elapsed = 0.0


def _detect_esd_variant(data_dir, well):
    """Auto-detect ESD subdirectory for a well."""
    rsd_path = os.path.join(data_dir, f'{well}.rsd')
    if not os.path.exists(rsd_path):
        return None
    subdirs = find_esd_subdirs(data_dir)
    if not subdirs:
        return None
    for name in ['Cp312', 'Cp1']:
        if name in subdirs:
            esd = os.path.join(data_dir, subdirs[name], f'{well}.esd')
            if os.path.exists(esd):
                return subdirs[name]
    first_name = sorted(subdirs)[0]
    esd = os.path.join(data_dir, subdirs[first_name], f'{well}.esd')
    if os.path.exists(esd):
        return subdirs[first_name]
    return None


def process_well(data_dir, well, esd_subdir=None,
                 baseline=BASELINE, bl_window=BL_WINDOW,
                 smooth=SMOOTH, sm_win=SM_WIN, sm_ord=SM_ORD,
                 matrix_point=MATRIX_POINT, shifts=None,
                 method=DEFAULT_METHOD, trim=True):
    """Process a single well through the full pipeline.

    Returns a WellResult (or raises on fatal error).
    """
    t0 = time.time()
    r = WellResult()
    r.well = well
    if shifts is None:
        shifts = list(DEFAULT_SHIFT)
    try:
        rsd_path = os.path.join(data_dir, f'{well}.rsd')
        if not os.path.exists(rsd_path):
            r.error = f'No RSD file: {rsd_path}'
            return r
        df = parse_rsd(rsd_path)
        rsd_raw = df[['Channel1', 'Channel2', 'Channel3',
                       'Channel4']].values.astype(np.float64)
        if esd_subdir is None:
            esd_subdir = _detect_esd_variant(data_dir, well)
        if esd_subdir:
            esd_path = os.path.join(data_dir, esd_subdir, f'{well}.esd')
        else:
            esd_path = ''
        # DSP pipeline
        pipeline_out = dsp_full_pipeline(
            rsd_raw, shifts, baseline, bl_window,
            smooth, sm_win, sm_ord,
            _TUNED_SSM, 0.0, matrix_point,
        )
        separated = pipeline_out[4]  # (raw, bl, corr, sm, separated, matrix)
        # Basecall
        LABELS = 'ACGT'
        if method == METHOD_CIMARRON_CNN and _CIMARRON_AVAILABLE:
            # Use Cimarron engine for peak detection + CNN for scoring
            ch_raw_T = rsd_raw.T.copy() if rsd_raw.shape[1] == 4 else rsd_raw.copy()
            scans_arr = np.arange(len(rsd_raw), dtype=float)
            eng = _cim.Cimarron312(
                variant='3.12', spec_sep_matrix=_TUNED_SSM,
                mobility_shifts=tuple(shifts),
                baseline_method=baseline, baseline_window=bl_window,
                smooth_method=smooth, smooth_window=sm_win,
                smooth_order=sm_ord, matrix_apply_point=matrix_point,
                caller='greedy', greedy_window=6,
            )
            res = eng.call(ch_raw_T, scans_arr)
            seq_list, pos_list, conf_list = [], [], []
            for base, pk in zip(res.sequence, res.peaks):
                if base in LABELS:
                    seq_list.append(base)
                    pos_list.append(int(round(pk.time)))
            if not seq_list:
                r.error = 'No bases called'
                r.elapsed = time.time() - t0
                return r
            pos = np.array(pos_list, dtype=np.int64)
            seq = ''.join(seq_list)
            # CNN scoring at Cimarron peak positions
            if _CNN_AVAILABLE:
                try:
                    cnn = _get_cnn()
                    conf = cnn.predict_pmax(rsd_raw, pos)
                except Exception:
                    conf = np.ones(len(pos)) * 0.5
            else:
                conf = np.ones(len(pos)) * 0.5
            intens = [{}] * len(pos)
        else:
            # Apply mobility shifts for display + peak calling
            shifted = separated.copy()
            for ch in range(4):
                s = int(shifts[ch])
                if s != 0:
                    from dsp import dsp_shift_channel
                    shifted[:, ch] = dsp_shift_channel(shifted[:, ch], s)
            region = pc_signal_region(shifted)
            if method == METHOD_GREEDY:
                pos, seq, bases, intens = pc_call_bases_greedy(
                    shifted, shifts, window=DISTANCE,
                    min_frac=PROM_FRAC, norm_window=NORM_WINDOW, region=region,
                )
            else:
                pos, seq, bases, intens = pc_call_bases_with_shifts(
                    shifted, shifts, min_distance=DISTANCE,
                    prominence_frac=PROM_FRAC, tolerance=TOLERANCE,
                    min_signal_frac=MIN_SIGNAL_FRAC,
                    norm_window=NORM_WINDOW, region=region,
                )
            if not seq or len(seq) == 0:
                r.error = 'No bases called'
                r.elapsed = time.time() - t0
                return r
            # CNN scoring at our peak positions
            if _CNN_AVAILABLE and len(pos) > 0:
                try:
                    cnn = _get_cnn()
                    conf = cnn.predict_pmax(rsd_raw, pos)
                except Exception:
                    conf = _intensity_confidence(intens)
            else:
                conf = _intensity_confidence(intens)
        # Phred Q-scores
        q = pmax_to_phred(conf)
        # Quality stats
        qd = quality_distribution(q)
        r.sequence = seq
        r.phred = q
        r.positions = pos
        r.intensities = intens
        r.confidence = conf
        r.mean_q = qd['mean_q']
        r.median_q = qd['median_q']
        r.q20_pct = qd['pct_q20']
        r.q30_pct = qd['pct_q30']
        r.total_bases = qd['total_bases']
        # Trim
        if trim and len(seq) > 0:
            ts, te, tseq, tq = sliding_window_trim(seq, q, window=20,
                                                    threshold=20,
                                                    min_length=50)
            r.trim_start = ts
            r.trim_end = te
            r.trimmed_seq = tseq
            r.trimmed_phred = tq
        else:
            r.trimmed_seq = seq
            r.trimmed_phred = q
        r.success = True
    except Exception as e:
        r.error = str(e)
    r.elapsed = time.time() - t0
    return r


class BatchProcessor:
    """Process all wells in a plate directory.

    Attributes:
        data_dir:     path to folder with .rsd files
        esd_subdir:   ESD subfolder name (auto-detected if None)
        results:      dict[well_name -> WellResult] after run()
        errors:       list of (well, error_msg) tuples
        method:       0=Greedy, 1=Cluster
        shifts:       [ch0..ch3] mobility shifts
    """

    def __init__(self, data_dir, esd_subdir=None, shifts=None,
                 method=DEFAULT_METHOD):
        self.data_dir = data_dir
        self.esd_subdir = esd_subdir
        self.shifts = shifts or list(DEFAULT_SHIFT)
        self.method = method
        self.results = {}
        self.errors = []
        self._cancelled = False

    def cancel(self):
        self._cancelled = True

    def _find_wells(self):
        if not os.path.isdir(self.data_dir):
            return []
        return sorted(f[:-4] for f in os.listdir(self.data_dir)
                      if f.endswith('.rsd'))

    def run(self, max_workers=4, progress_callback=None):
        """Process all wells.  Returns dict[well -> WellResult].

        progress_callback(well, done, total) is called after each well.
        """
        self._cancelled = False
        wells = self._find_wells()
        total = len(wells)
        if total == 0:
            return self.results
        self.results = {}
        self.errors = []
        done = 0
        with ThreadPoolExecutor(max_workers=max_workers) as pool:
            futures = {}
            for well in wells:
                f = pool.submit(
                    process_well, self.data_dir, well,
                    esd_subdir=self.esd_subdir, shifts=self.shifts,
                    method=self.method, trim=True,
                )
                futures[f] = well
            for future in as_completed(futures):
                if self._cancelled:
                    pool.shutdown(wait=False, cancel_futures=True)
                    break
                well = futures[future]
                try:
                    result = future.result()
                    self.results[well] = result
                    if not result.success:
                        self.errors.append((well, result.error))
                except Exception as e:
                    self.errors.append((well, str(e)))
                done += 1
                if progress_callback:
                    progress_callback(well, done, total)
        return self.results

    def run_sequential(self, progress_callback=None):
        """Process wells one at a time (for debugging)."""
        self._cancelled = False
        wells = self._find_wells()
        total = len(wells)
        self.results = {}
        self.errors = []
        for i, well in enumerate(wells):
            if self._cancelled:
                break
            result = process_well(
                self.data_dir, well,
                esd_subdir=self.esd_subdir, shifts=self.shifts,
                method=self.method, trim=True,
            )
            self.results[well] = result
            if not result.success:
                self.errors.append((well, result.error))
            if progress_callback:
                progress_callback(well, i + 1, total)
        return self.results

    def export_fasta(self, output_dir, trimmed=True, prefix='plate'):
        """Export all sequences to a multi-record FASTA file."""
        os.makedirs(output_dir, exist_ok=True)
        path = os.path.join(output_dir, f'{prefix}.fasta')
        records = []
        for well, r in sorted(self.results.items()):
            if not r.success:
                continue
            seq = r.trimmed_seq if trimmed else r.sequence
            if not seq:
                continue
            records.append((f'{well}', seq))
        write_fasta_multi(path, records)
        return path

    def export_fastq(self, output_dir, trimmed=True, prefix='plate'):
        """Export all sequences to a multi-record FASTQ file."""
        os.makedirs(output_dir, exist_ok=True)
        path = os.path.join(output_dir, f'{prefix}.fastq')
        records = []
        for well, r in sorted(self.results.items()):
            if not r.success:
                continue
            seq = r.trimmed_seq if trimmed else r.sequence
            q = r.trimmed_phred if trimmed else r.phred
            if not seq:
                continue
            records.append((f'{well}', seq, q))
        write_fastq_multi(path, records)
        return path

    def export_per_well(self, output_dir, trimmed=True):
        """Export each well as a separate FASTQ + quality table."""
        os.makedirs(output_dir, exist_ok=True)
        paths = []
        for well, r in sorted(self.results.items()):
            if not r.success:
                continue
            seq = r.trimmed_seq if trimmed else r.sequence
            q = r.trimmed_phred if trimmed else r.phred
            if not seq:
                continue
            fastq_path = os.path.join(output_dir, f'{well}.fastq')
            write_fastq(fastq_path, well, seq, q)
            table_path = os.path.join(output_dir, f'{well}_quality.tsv')
            write_phred_table(table_path, r.positions[:len(seq)], seq, q)
            paths.append((fastq_path, table_path))
        return paths

    def summary_table(self):
        """Return a list of dicts with per-well summary stats."""
        rows = []
        for well, r in sorted(self.results.items()):
            row = {
                'well': well,
                'success': r.success,
                'error': r.error,
                'total_bases': r.total_bases,
                'mean_q': round(r.mean_q, 1),
                'median_q': round(r.median_q, 1),
                'q20_pct': round(r.q20_pct, 1),
                'q30_pct': round(r.q30_pct, 1),
                'trimmed_bases': len(r.trimmed_seq),
                'elapsed_s': round(r.elapsed, 2),
            }
            rows.append(row)
        return rows

    def summary_stats(self):
        """Return aggregate stats across all wells."""
        rows = self.summary_table()
        ok = [r for r in rows if r['success']]
        if not ok:
            return {'total_wells': len(rows), 'success': 0, 'failed': len(rows)}
        return {
            'total_wells': len(rows),
            'success': len(ok),
            'failed': len(rows) - len(ok),
            'mean_bases': round(np.mean([r['total_bases'] for r in ok]), 1),
            'mean_q20': round(np.mean([r['q20_pct'] for r in ok]), 1),
            'mean_q30': round(np.mean([r['q30_pct'] for r in ok]), 1),
            'mean_time': round(np.mean([r['elapsed_s'] for r in ok]), 2),
        }


# ── CLI ─────────────────────────────────────────────────────────────────

def _main():
    import argparse
    parser = argparse.ArgumentParser(
        description='Batch-process a plate of Sanger traces')
    parser.add_argument('data_dir', help='Folder with .rsd files')
    parser.add_argument('--out', '-o', default='batch_output',
                        help='Output directory (default: batch_output)')
    parser.add_argument('--esd', default=None,
                        help='ESD subdirectory name (auto-detect if omitted)')
    parser.add_argument('--method', type=int, default=0, choices=[0, 1, 2],
                        help='0=Greedy, 1=Cluster, 2=Cimarron+CNN')
    parser.add_argument('--threads', type=int, default=4,
                        help='Parallel threads')
    parser.add_argument('--prefix', default='plate',
                        help='Output file prefix')
    parser.add_argument('--no-trim', action='store_true',
                        help='Skip quality trimming')
    args = parser.parse_args()

    bp = BatchProcessor(args.data_dir, esd_subdir=args.esd,
                        method=args.method)

    def progress(well, done, total):
        sys.stdout.write(f'\r  [{done}/{total}] {well}    ')
        sys.stdout.flush()

    print(f'Processing {len(bp._find_wells())} wells from {args.data_dir}')
    bp.run(max_workers=args.threads, progress_callback=progress)
    print()
    stats = bp.summary_stats()
    print(f'Done: {stats["success"]}/{stats["total_wells"]} wells succeeded')
    if stats.get('failed', 0):
        print(f'  Mean bases: {stats["mean_bases"]}, '
              f'Q20: {stats["mean_q20"]}%, Q30: {stats["mean_q30"]}%')
    bp.export_fastq(args.out, trimmed=not args.no_trim, prefix=args.prefix)
    bp.export_fasta(args.out, trimmed=not args.no_trim, prefix=args.prefix)
    bp.export_per_well(args.out, trimmed=not args.no_trim)
    print(f'Exported to {args.out}/')


if __name__ == '__main__':
    _main()
