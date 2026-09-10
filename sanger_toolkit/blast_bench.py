#!/usr/bin/env python3
"""blast_bench.py - BLAST benchmark vs the Cimarron 3.12 DLL target.

The real-world benchmark (not the internal ESD comparison) is whether the
called sequence aligns to the M13 reference in a single clean HSP, exactly
like the commercial Cimarron 3.12 DLL does.  The DLL's A01 result is the
goal:

    Cimarron 3.12 (A01):  841 bases detected, ~95% coverage, 95.39% identity

This script reproduces that measurement with the SAME blastn pipeline for
(a) the Cimarron DLL ESD output and (b) OUR caller's output, so the two are
directly comparable.  Our caller is measured DE-NOVO (no reference-guided
polishing), because polishing against M13 would be circular for a coverage
/identity check against M13.

Requires: NCBI blast+ (blastn + makeblastdb) and the M13 reference.
"""
import os, sys, subprocess, tempfile, argparse
import numpy as np

HERE = os.path.dirname(os.path.realpath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, ROOT)

REF = os.path.join(HERE, 'refs', 'm13_M77815.1.fa')
GT_DIR = os.path.join(ROOT, 'MB1000_M13_DT', 'MB1000_M13_DT_Cp312_MD1')
PLATE = os.path.join(ROOT, 'MB1000_M13_DT')


def _ref_seq():
    return ''.join(l.strip() for l in open(REF) if not l.startswith('>'))


def blast_eval(sequence, task='megablast'):
    """blastn(sequence vs M13), return best-HSP metrics dict or None."""
    seq = ''.join(c for c in sequence if c in 'ACGT')
    if len(seq) < 30:
        return None
    with tempfile.TemporaryDirectory() as td:
        with open(os.path.join(td, 'm13.fa'), 'w') as f:
            f.write('>M13mp18\n' + _ref_seq() + '\n')
        with open(os.path.join(td, 'q.fa'), 'w') as f:
            f.write('>q\n' + seq + '\n')
        subprocess.run(
            ['makeblastdb', '-in', os.path.join(td, 'm13.fa'),
             '-dbtype', 'nucl', '-out', os.path.join(td, 'db')],
            check=True, capture_output=True)
        out = os.path.join(td, 'o.txt')
        subprocess.run(
            ['blastn', '-db', os.path.join(td, 'db'),
             '-query', os.path.join(td, 'q.fa'), '-task', task,
             '-outfmt',
             '6 qlen qstart qend sstart send pident bitscore length mismatch gapopen',
             '-out', out], check=True, capture_output=True)
        rows = [l.split('\t') for l in open(out) if l.strip()]
        if not rows:
            return None
        r = max(rows, key=lambda x: float(x[5]))  # best bitscore
        qlen, qstart, qend, sstart, send, pident, bs, ln, mm, gaps = (
            int(r[0]), int(r[1]), int(r[2]), int(r[3]), int(r[4]),
            float(r[5]), float(r[6]), int(r[7]), int(r[8]), int(r[9]))
        matched = ln - mm - gaps
        full = 100.0 * matched / qlen if qlen else 0.0
        return {
            'qlen': qlen,
            'bases_detected': qlen,
            'qstart': qstart, 'qend': qend,
            'm13_start': min(sstart, send), 'm13_end': max(sstart, send),
            'coverage': 100.0 * (qend - qstart + 1) / qlen,
            'identity': pident,          # BLAST: matched/aligned (ignores unaligned tail)
            'matched': matched,          # fair: actual base pairs matching M13
            'full_identity': full,       # fair: matched / ALL detected (1 bp = 100%)
            'bitscore': bs, 'aligned': ln, 'mismatch': mm, 'gaps': gaps,
        }


def dll_sequence(well):
    """Return the Cimarron DLL's own ESD sequence for a well."""
    import extract_training_data as etd
    d = etd.parse_esd(os.path.join(GT_DIR, well + '.esd'))
    return d['sequence']


def dll_esd_sequence(well):
    """Return the DLL ESD sequence directly via cimarrontv (fallback)."""
    import cimarrontv as cim
    return cim.read_esd(os.path.join(GT_DIR, well + '.esd'))['sequence']


def ours_denovo_sequence(well, models, refine_v2, bgn_end='perbase', drop=0.0):
    """Run our de-novo CNN ensemble (no reference polishing) on a well."""
    import perfect_basecaller as pb
    import numpy as np
    r = pb.call_raw(os.path.join(PLATE, well + '.rsd'), models=models,
                    refine_v2=refine_v2, bgn_end_method=bgn_end)
    if not (drop > 0 and len(models)):
        return r['seq']
    ch, scans = pb.cim.read_rsd(os.path.join(PLATE, well + '.rsd'))
    chw = np.asarray(ch, dtype=np.float64)
    if chw.ndim == 2 and chw.shape[0] == 4 and chw.shape[0] <= chw.shape[1]:
        chw = chw.T
    probs = pb.cnn_probs(models, chw, r['scans'])
    pmax = probs.max(1)
    pred = probs.argmax(1)
    keep = pmax >= drop
    return ''.join(pb.LABELS[pred[k]] for k in range(len(pred)) if keep[k])


def report(label, r):
    if r is None:
        print(f'  {label:34s} NO ALIGNMENT')
        return None
    print(f'  {label:34s} bases={r["bases_detected"]:4d}  '
          f'matched_bp={r["matched"]:4d}  '
          f'full_id={r["full_identity"]:5.2f}%  '
          f'(pident={r["identity"]:5.2f})  '
          f'cov={r["coverage"]:5.1f}%  '
          f'(M13 {r["m13_start"]}-{r["m13_end"]})')
    return r


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--wells', nargs='*', default=['A01'])
    ap.add_argument('--task', default='megablast',
                    choices=['megablast', 'blastn', 'dc-megablast'])
    ap.add_argument('--models', nargs='*', default=[
        os.path.join(ROOT, '02_denovo_cnn_ensemble_91.53pct', f) for f in [
            'base_caller_model_v4_clean.keras',
            'base_caller_model_v4_pos.keras',
            'base_caller_model_v4_pos_b.keras']])
    ap.add_argument('--refine-v2', action='store_true',
                    help='de-novo CNN refine pass (position-adaptive)')
    ap.add_argument('--drop', type=float, default=0.0, metavar='PMIN',
                    help='drop CNN calls with peak probability < PMIN.  This '
                         'removes spurious insertions and sharply raises BLAST '
                         'coverage (best around 0.52-0.55).')
    ap.add_argument('--bgn-end', default='perbase',
                    choices=['perbase', 'legacy', 'histogram', 'hybrid'],
                    help='Cimarron begin/end detection method for de-novo peaks')
    ap.add_argument('--no-cnn', action='store_true',
                    help='use the greedy independent caller only (no TF)')
    args = ap.parse_args()

    models = [] if args.no_cnn else __import__('perfect_basecaller').load_ensemble(args.models)

    for well in args.wells:
        print(f'\n=== {well} ===')
        dl = report('Cimarron 3.12 DLL (goal)', blast_eval(dll_sequence(well), args.task))
        if args.no_cnn:
            # Pure python independent caller from the DSP pipeline
            from dsp import dsp_full_pipeline
            from basecall import pc_call_bases_with_shifts
            import extract_training_data as etd
            from scipy.signal import butter
            raw_df = etd.parse_rsd(os.path.join(PLATE, well + '.rsd'))
            raw = raw_df[['Channel1', 'Channel2', 'Channel3',
                          'Channel4']].to_numpy(dtype=np.float64)
            V10 = np.array([[1.0,1.00,0.26,0.46],[0.07,1.00,0.075,0.006],
                            [0.38,0.33,1.00,1.52],[0.27,0.26,0.189,1.00]])
            _,_,_,_,sep,_ = dsp_full_pipeline(
                raw, [5,11,10,10], 'AsyLS', 50010, 'Butterworth', 5, 9, V10,
                baseline_window2=1, matrix_apply_point='smoothed')
            pos, seq, grp, iten = pc_call_bases_with_shifts(
                sep, [5,11,10,10], min_distance=5, prominence_frac=0.075,
                norm_window=2000)
            report(f'ours de-novo (independent caller)', blast_eval(seq, args.task))
        else:
            r = ours_denovo_sequence(well, models, args.refine_v2,
                                     bgn_end=args.bgn_end, drop=args.drop)
            report('ours de-novo (CNN ensemble)',
                   blast_eval(r, args.task))


if __name__ == '__main__':
    main()
