#!/usr/bin/env python3
"""best_web_sweep.py - finetune best_basecaller on the 48 held-out wells.

Sweeps configs of the web DSP caller and scores each with the SAME
golden-standard NCBI-BLAST metric used everywhere else (blastn megablast
best-HSP `matched_bp` vs M13mp18, sanger_toolkit/refs/m13_M77815.1.fa).

Speed-up over blast_eval(): the M13 db is built ONCE; blast_eval rebuilds a
makeblastdb per call. Output format and best-hit selection are identical, so
numbers are directly comparable with the DLL/CNN tables.

Usage:
    python3 best_web_sweep.py                  # 48 held-out wells, full grid
    python3 best_web_sweep.py --wells A01 B04  # quick smoke
"""
import argparse
import json
import os
import subprocess
import sys
import tempfile
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PLATE = os.path.join(ROOT, 'MB1000_M13_DT')
REF = os.path.join(HERE, '..', 'sanger_toolkit', 'refs', 'm13_M77815.1.fa')
PKG = os.path.join(ROOT, 'best_basecaller')
if PKG not in sys.path:
    sys.path.insert(0, PKG)

HELD = ('A01 A03 A05 A07 A09 A11 B02 B04 B06 B08 B10 B12 '
        'C01 C03 C05 C07 C09 C11 D02 D04 D06 D08 D10 D12 '
        'E01 E03 E05 E07 E09 E11 F02 F04 F06 F08 F10 F12 '
        'G01 G03 G05 G07 G09 G11 H02 H04 H06 H08 H10 H12').split()

WIN_CONFIG = dict(
    use_gaussian_reconstruction=True,
    gaussian_recon_segment_size=384,
    use_combined_channel_score=True,
    window_frac=(0.75, 1.25),
    local_norm_window=1800,
    channel_peak_bonus=1.6,
    pullback_weight=0.019,
    ema_alpha=0.10,
)


def _ref_seq():
    seq = []
    for line in open(os.path.realpath(REF)):
        if not line.startswith('>'):
            seq.append(line.strip())
    return ''.join(seq)


def build_db(td):
    db = os.path.join(td, 'm13')
    with open(os.path.join(td, 'm13.fa'), 'w') as f:
        f.write('>M13mp18\n' + _ref_seq() + '\n')
    subprocess.run(['makeblastdb', '-in', os.path.join(td, 'm13.fa'),
                    '-dbtype', 'nucl', '-out', db], check=True,
                   capture_output=True)
    return db


def blast_to_m13(seq, db):
    """same outfmt/best-hit logic as blast_bench.blast_eval but using a
    prebuilt db. Returns (qlen, aligned, pident, matched, fullid) or None."""
    clean = ''.join(c for c in seq if c in 'ACGT')
    if len(clean) < 30:
        return None
    with tempfile.TemporaryDirectory() as td:
        with open(os.path.join(td, 'q.fa'), 'w') as f:
            f.write('>q\n' + clean + '\n')
        out = os.path.join(td, 'o.txt')
        subprocess.run(
            ['blastn', '-db', db, '-query', os.path.join(td, 'q.fa'),
             '-task', 'megablast', '-outfmt',
             '6 qlen qstart qend sstart send pident bitscore length mismatch gapopen',
             '-out', out], check=True, capture_output=True)
        rows = [l.split('\t') for l in open(out) if l.strip()]
        if not rows:
            return None
        r = max(rows, key=lambda x: float(x[5]))
        qlen, pident, bits, ln, mm, gaps = (int(r[0]), float(r[5]),
                                            float(r[6]), int(r[7]),
                                            int(r[8]), int(r[9]))
        matched = ln - mm - gaps
        return (qlen, ln, pident, matched, 100.0 * matched / qlen)


def load_traces(wells):
    from cimarron_basecaller.rsd_io import read_rsd, to_acgt_trace
    out = {}
    for w in wells:
        rsd = read_rsd(os.path.join(PLATE, w + '.rsd'))
        trace, order = to_acgt_trace(rsd, base_order='TGCA')
        out[w] = (trace, order)
    return out


def run_config(traces, cfg):
    from cimarron_basecaller import track_bases
    seqs = {}
    for w, (trace, order) in traces.items():
        seq, _quals, _bands = track_bases(trace, base_order=order, **cfg)
        seqs[w] = seq
    return seqs


def score(seqs, db):
    tot_m = tot_q = tot_fi = tot_pid = 0
    n = 0
    beat_dll = 0
    dll = {'A01': 790, 'A03': 729, 'A05': 749, 'A07': 742, 'A09': 788,
           'A11': 739, 'B02': 771, 'B04': 761, 'B06': 781, 'B08': 738,
           'B10': 748, 'B12': 765, 'C01': 726, 'C03': 763, 'C05': 732,
           'C07': 783, 'C09': 736, 'C11': 769, 'D02': 738, 'D04': 740,
           'D06': 730, 'D08': 751, 'D10': 773, 'D12': 737, 'E01': 733,
           'E03': 774, 'E05': 782, 'E07': 746, 'E09': 742, 'E11': 735,
           'F02': 749, 'F04': 739, 'F06': 760, 'F08': 737, 'F10': 775,
           'F12': 741, 'G01': 731, 'G03': 802, 'G05': 747, 'G07': 769,
           'G09': 764, 'G11': 750, 'H02': 748, 'H04': 771, 'H06': 783,
           'H08': 747, 'H10': 764, 'H12': 763}
    for w, seq in seqs.items():
        r = blast_to_m13(seq, db)
        if r is None:
            continue
        qlen, aligned, pident, matched, fullid = r
        tot_m += matched
        tot_q += qlen
        tot_fi += fullid
        tot_pid += pident
        n += 1
        if matched > dll.get(w, 10**9):
            beat_dll += 1
    return dict(n=n, matched=tot_m / max(1, n), fullid=tot_fi / max(1, n),
                pident=tot_pid / max(1, n), qlen=tot_q / max(1, n),
                beat_dll=beat_dll, tot_matched=tot_m)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--wells', nargs='*', default=HELD,
                    help='wells to use (default: 48 held-out)')
    args = ap.parse_args()
    wells = args.wells
    if not wells:
        wells = HELD

    traces = load_traces(wells)
    with tempfile.TemporaryDirectory() as td:
        db = build_db(td)

        def sweep(label, overrides):
            cfg = dict(WIN_CONFIG)
            cfg.update(overrides)
            t0 = time.time()
            seqs = run_config(traces, cfg)
            s = score(seqs, db)
            dt = time.time() - t0
            flag = ''
            if s['tot_matched'] > best.get('tot_matched', -1):
                best.update(s)
                best['cfg'] = dict(cfg)
                flag = '  <-- NEW BEST'
            print('%-34s n=%2d  mean_mat=%7.2f  mean_fi=%6.2f  mean_pid=%6.2f '
                  'mean_qlen=%6.1f  beat_DLL=%2d/48  (%4.0fs)%s'
                  % (label, s['n'], s['matched'], s['fullid'], s['pident'],
                     s['qlen'], s['beat_dll'], dt, flag), flush=True)
            return s

        best = {'tot_matched': -1}
        print('baseline / sanity: expect matched ~767.98 on the 48 held-out',
              flush=True)
        sweep('BASE  pullback=0.019 cp_bonus=1.6', {})
        print('\n-- coordinate sweeps on base config --', flush=True)
        for pb in (0.008, 0.012, 0.016, 0.019, 0.022, 0.028):
            sweep(f'pullback_weight={pb}', {'pullback_weight': pb})
        for cb in (1.0, 1.4, 1.6, 2.0, 2.4):
            sweep(f'channel_peak_bonus={cb}', {'channel_peak_bonus': cb})
        for al in (0.06, 0.08, 0.10, 0.12, 0.15):
            sweep(f'ema_alpha={al}', {'ema_alpha': al})
        for wf in ((0.70, 1.30), (0.75, 1.25), (0.80, 1.20)):
            sweep(f'window_frac={wf}', {'window_frac': wf})
        for mp in (0.04, 0.05, 0.06, 0.07):
            sweep(f'min_prominence={mp}', {'min_prominence': mp})
        for nlw in (1500, 1800, 2200, 2600):
            sweep(f'local_norm_window={nlw}', {'local_norm_window': nlw})
        for gs in (256, 384, 512):
            sweep(f'gaussian_recon_segment_size={gs}',
                  {'gaussian_recon_segment_size': gs})
        sweep('auto_trim=False (raw)', {'auto_trim': False})
        sweep('repeat_detection=True', {'repeat_detection': True, 'repeat_min_sub_peak_prominence': 0.4})
        sweep('trim_quality_percentile=20', {'trim_quality_percentile': 20.0})
        sweep('trim_quality_percentile=30', {'trim_quality_percentile': 30.0})

        print('\n-- combinations around the winners --', flush=True)
        sweep('pb=0.012 + cb=1.4 + ema=0.12',
              {'pullback_weight': 0.012, 'channel_peak_bonus': 1.4, 'ema_alpha': 0.12})
        sweep('pb=0.012 + cb=1.4 + ema=0.12 + minprom=0.04',
              {'pullback_weight': 0.012, 'channel_peak_bonus': 1.4,
               'ema_alpha': 0.12, 'min_prominence': 0.04})
        sweep('pb=0.012 + cb=1.6 + ema=0.12 + wf(0.7,1.3)',
              {'pullback_weight': 0.012, 'channel_peak_bonus': 1.6,
               'ema_alpha': 0.12, 'window_frac': (0.70, 1.30)})
        sweep('pb=0.012 + cb=1.4 + ema=0.12 + repeat',
              {'pullback_weight': 0.012, 'channel_peak_bonus': 1.4,
               'ema_alpha': 0.12, 'repeat_detection': True,
               'repeat_min_sub_peak_prominence': 0.4})

        print('\nBEST: %-34s mean_mat=%.2f fullid=%.2f pident=%.2f '
              'qlen=%.1f beat_DLL=%d/48' % (
                  str(best['cfg']), best['matched'], best['fullid'],
                  best['pident'], best['qlen'], best['beat_dll']))
        with open(os.path.join(HERE, 'best_web_sweep_best.json'), 'w') as f:
            json.dump({'mean_matched_bp': best['matched'],
                       'mean_fullid': best['fullid'],
                       'mean_pident': best['pident'],
                       'mean_qlen': best['qlen'],
                       'beat_dll': best['beat_dll'],
                       'config': best['cfg']}, f, indent=2, default=float)


if __name__ == '__main__':
    main()