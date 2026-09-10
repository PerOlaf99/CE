#!/usr/bin/env python3
"""plate_blast.py - run the BLAST benchmark over all (or selected) wells.

Loads the CNN ensemble once, then for every well runs our de-novo caller
(CNN re-call at our own seed peaks, optional confidence dropout) and the
Cimarron DLL ESD call through the same blastn/megablast pipeline, reporting
per-well and plate-wide means of: bases detected, coverage %, identity %.

Usage:
  python3 plate_blast.py                     # all 96 wells, drop=0.5
  python3 plate_blast.py --wells A01 A02      # subset
  python3 plate_blast.py --drop 0.55 --bgn-end legacy --threads 8
"""
import os, sys, glob, argparse, tempfile, subprocess, threading
from concurrent.futures import ThreadPoolExecutor
import numpy as np

HERE = os.path.dirname(os.path.realpath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, ROOT)
os.environ.setdefault('TF_CPP_MIN_LOG_LEVEL', '3')

REF = os.path.join(HERE, 'refs', 'm13_M77815.1.fa')
GT_DIR = os.path.join(ROOT, 'MB1000_M13_DT', 'MB1000_M13_DT_Cp312_MD1')
PLATE = os.path.join(ROOT, 'MB1000_M13_DT')

_MODELS = None
_LOCK = threading.Lock()


def ref_seq():
    return ''.join(l.strip() for l in open(REF) if not l.startswith('>'))


def load_models(args):
    global _MODELS
    with _LOCK:
        if _MODELS is None:
            import perfect_basecaller as pb
            pat = os.path.join(ROOT, '02_denovo_cnn_ensemble_91.53pct')
            files = ['base_caller_model_v4_clean.keras',
                     'base_caller_model_v4_pos.keras',
                     'base_caller_model_v4_pos_b.keras']
            _MODELS = [__import__('tensorflow').keras.models.load_model(
                os.path.join(pat, f), compile=False) for f in files]
    return _MODELS


def _blast_seq(seq):
    """blastn(megablast) best-HSP of seq vs M13.

    Returns a dict with the caller's detected base count (qlen), the BLAST
    pident (matched/aligned, which ignores the read's unaligned tail), the
    HSP query coverage, AND the FAIR full-read metrics your "1 base pair =
    100%"? rule calls for:
      matched_bp = aligned_length - mismatch - gapopen  (bases that really
                   match M13)
      full_ident = matched_bp / qlen   (true identity over ALL detected
                   bases, counting the unaligned tail as errors)
      full_cov   = matched_bp / qlen   == full_ident here when each detected
                   base maps to at most one M13 base; unmatched/extra bases
                   lower it (they were detected but never matched).
                   qlen is the caller's OWN denominator, so DLL vs ours are
                   compared on equal "1 detected base = a slot to fill"
                   footing despite different read lengths.
    Returns None if too short / no alignment.
    """
    clean = ''.join(c for c in seq if c in 'ACGT')
    if len(clean) < 30:
        return None
    seqr = ref_seq()
    with tempfile.TemporaryDirectory() as td:
        with open(os.path.join(td, 'm13.fa'), 'w') as f:
            f.write('>M13mp18\n' + seqr + '\n')
        with open(os.path.join(td, 'q.fa'), 'w') as f:
            f.write('>q\n' + clean + '\n')
        subprocess.run(['makeblastdb', '-in', os.path.join(td, 'm13.fa'),
                        '-dbtype', 'nucl', '-out', os.path.join(td, 'db')],
                       check=True, capture_output=True)
        out = os.path.join(td, 'o.txt')
        subprocess.run(['blastn', '-db', os.path.join(td, 'db'),
                        '-query', os.path.join(td, 'q.fa'), '-task', 'megablast',
                        '-outfmt',
                        '6 qlen qstart qend length pident mismatch gapopen bitscore',
                        '-out', out], check=True, capture_output=True)
        rows = [l.split('\t') for l in open(out) if l.strip()]
        if not rows:
            return None
        r = max(rows, key=lambda x: float(x[7]))
        qlen, qs, qe, ln, pident, mm, gap, bs = (
            int(r[0]), int(r[1]), int(r[2]), int(r[3]), float(r[4]),
            int(r[5]), int(r[6]), float(r[7]))
        matched = ln - mm - gap
        if qlen <= 0:
            return None
        hsp_cov = 100.0 * (qe - qs + 1) / qlen        # fraction inside HSP
        full = 100.0 * matched / qlen                  # matched / detected
        return dict(bases=qlen, hsp_cov=hsp_cov, pident=pident,
                    matched=matched, full_ident=full,
                    full_cov=full, outs=qlen - (qe - qs + 1))


def _dll_seq(well):
    import extract_training_data as etd
    d = etd.parse_esd(os.path.join(GT_DIR, well + '.esd'))
    return d['sequence']


def _ours_seq(well, models, drop, bgn_end):
    import perfect_basecaller as pb
    import numpy as np
    r = pb.call_raw(os.path.join(PLATE, well + '.rsd'), models=models,
                    bgn_end_method=bgn_end)
    seq = r['seq']
    if not (drop > 0 and len(models)):
        return seq
    ch, scans = pb.cim.read_rsd(os.path.join(PLATE, well + '.rsd'))
    chw = np.asarray(ch, dtype=np.float64)
    if chw.ndim == 2 and chw.shape[0] == 4 and chw.shape[0] <= chw.shape[1]:
        chw = chw.T
    probs = pb.cnn_probs(models, chw, r['scans'])
    pmax = probs.max(1)
    pred = probs.argmax(1)
    keep = pmax >= drop
    return ''.join(pb.LABELS[pred[k]] for k in range(len(pred)) if keep[k])


def process_well(well, args, models):
    dll = _blast_seq(_dll_seq(well))
    ours = _blast_seq(_ours_seq(well, models, args.drop, args.bgn_end))
    return well, dll, ours


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--wells', nargs='*', default=None, help='e.g. A01 B02; default all 96')
    ap.add_argument('--drop', type=float, default=0.50)
    ap.add_argument('--bgn-end', default='perbase',
                    choices=['perbase', 'legacy', 'histogram', 'hybrid'])
    ap.add_argument('--threads', type=int, default=4)
    ap.add_argument('--out')
    args = ap.parse_args()

    if args.wells:
        wells = [w.upper() for w in args.wells]
    else:
        wells = [f'{r}{c:02d}' for r in 'ABCDEFGH' for c in range(1, 13)]
    wells = [w for w in wells
             if os.path.isfile(os.path.join(PLATE, w + '.rsd'))
             and os.path.isfile(os.path.join(GT_DIR, w + '.esd'))]
    print(f'loading CNN ensemble and running {len(wells)} wells '
          f'(drop={args.drop}, bgn_end={args.bgn_end}, threads={args.threads})',
          flush=True)
    models = load_models(args)

    results = {}
    with ThreadPoolExecutor(max_workers=args.threads) as ex:
        futs = {ex.submit(process_well, w, args, models): w for w in wells}
        for i, f in enumerate(futs):
            w, dll, ours = f.result()
            results[w] = (dll, ours)
            if (i + 1) % 8 == 0 or (i + 1) == len(futs):
                print(f'  {i+1}/{len(wells)} done ({w})', flush=True)

    print('\nrow  bases_dll  match_dll  fullid_dll | bases_ours  match_ours  fullid_ours')
    d_agg, o_agg = [], []
    for w in wells:
        dll, ours = results[w]
        d_b = dll['bases'] if dll else float('nan')
        d_m = dll['matched'] if dll else float('nan')
        d_f = dll['full_ident'] if dll else float('nan')
        d_p = dll['pident'] if dll else float('nan')
        o_b = ours['bases'] if ours else float('nan')
        o_m = ours['matched'] if ours else float('nan')
        o_f = ours['full_ident'] if ours else float('nan')
        o_p = ours['pident'] if ours else float('nan')
        print(f'{w:4s}  {d_b:6.0f}  {d_m:7.0f}  {d_f:6.2f} ({d_p:5.2f}) | '
              f'{o_b:7.0f}  {o_m:7.0f}  {o_f:6.2f} ({o_p:5.2f})')
        d_agg.append((d_b, d_m, d_f))
        o_agg.append((o_b, o_m, o_f))

    darr = np.array(d_agg, dtype=float)
    oarr = np.array(o_agg, dtype=float)
    print()
    print('FULL-READ metric (matched bp / detected bp): "1 detected base = 100%"')
    def row_mean(a, name):
        return (f'{name:14s} bases={np.nanmean(a[:,0]):6.1f}  '
                f'matched_bp={np.nanmean(a[:,1]):6.1f}  '
                f'full_ident={np.nanmean(a[:,2]):5.2f}%')
    print(row_mean(darr, 'DLL (goal)'))
    print(row_mean(oarr, 'ours de-novo'))
    o_id, d_id = np.nanmean(oarr[:, 2]), np.nanmean(darr[:, 2])
    o_mr, d_mr = np.nanmean(oarr[:, 1]), np.nanmean(darr[:, 1])
    ib = '>' if o_id > d_id else '<'
    mb = '>' if o_mr > d_mr else '<'
    print(f'vs DLL: full identity {ib} ({o_id:.2f} vs {d_id:.2f}%), '
          f'matched bp {mb} ({o_mr:.0f} vs {d_mr:.0f})')

    if args.out:
        with open(args.out, 'w') as fo:
            fo.write('well,bases_dll,matched_dll,fullid_dll,bases_ours,matched_ours,fullid_ours\n')
            for w in wells:
                dll, ours = results[w]
                d = (f"{dll['bases']},{dll['matched']},{dll['full_ident']:.2f}"
                     if dll else ',,')
                o = (f"{ours['bases']},{ours['matched']},{ours['full_ident']:.2f}"
                     if ours else ',,')
                fo.write(f'{w},{d},{o}\n')


if __name__ == '__main__':
    main()
