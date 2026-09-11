#!/usr/bin/env python3
"""eval_v3_blast.py - BLAST acceptance test for the v3 per-region CNNs.

Calls the held-out test wells with the 4 per-region CNNs (begin/mid/tail/
tail-tail), assembles a read per well, and BLASTs it against M13mp18 with
the SAME pipeline used for the Cimarron 3.12 DLL (blast_bench.blast_eval).
Reporter: DLL (Cimarron 3.12 ESD read) vs OURS on every test well, plus
plate means of matched_bp / pident / coverage / full-identity.

Acceptance (user rule): OURS equal or better than Cimarron 3.12 per NCBI
blast over the held-out wells.

Also prints the internal-standard check (calls T, not M13's C, at the
mutation) and writes per-well FASTA of our reads for optional web BLAST.
"""
import os, sys, argparse
import numpy as np
os.environ.setdefault('TF_CPP_MIN_LOG_LEVEL', '3')

HERE = os.path.dirname(os.path.realpath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, ROOT)

import extract_v3 as ex
from extract_training_data import parse_rsd, parse_esd
import tensorflow as tf

sys.path.insert(0, os.path.join(ROOT, 'sanger_toolkit'))
from blast_bench import blast_eval, report as bb_report

LABELS = 'ACGT'
REGIONS = ['begin', 'mid', 'tail', 'tailtail']


def load_models():
    mm = {}
    for r, name in enumerate(REGIONS):
        p = os.path.join(HERE, f'base_caller_model_v3_{name}.keras')
        if not os.path.isfile(p):
            print(f'MISSING {p}')
            continue
        mm[r] = tf.keras.models.load_model(p, compile=False)
        print(f'loaded region {name}')
    return mm


def call_well(well, models, ref_rc, d):
    """Return (n_usable, called_bases_str, region_correct_ok_mask, info)."""
    ch = parse_rsd(os.path.join(ex.PLATE, well + '.rsd'))[ex.CH_NAMES].values.astype(np.float64)
    esd = parse_esd(os.path.join(ex.GT, well + '.esd'))
    r, why = ex.extract_well(well, ch, esd, ref_rc)
    if r is None:
        return None, why
    n = r['n_usable']
    rank = np.arange(n, dtype=float) / max(1, n - 1)
    region = np.array([ex.region_of(x) for x in rank])
    X = np.array([ex.make_window(ch, int(s)) for s in r['scan']])
    mu = X.mean(axis=1, keepdims=True)
    sd = X.std(axis=1, keepdims=True) + 1e-8
    X = ((X - mu) / sd).astype(np.float32)
    called = np.empty(n, dtype='<U1')
    for rg in sorted(set(region)):
        sel = region == rg
        probs = models[int(rg)].predict(X[sel], verbose=0)[:, :4]
        called[sel] = [LABELS[i] for i in probs.argmax(1)]
    read = ''.join(called)          # read-orientation, front-masked, aligned span
    return r, read, region, called


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--wells', default=None,
                    help='comma list; default = all 48 held-out test wells')
    ap.add_argument('--outdir', default=os.path.join(HERE, 'v3_blast_reads'))
    args = ap.parse_args()

    models = load_models()
    if len(models) != 4:
        print(f'ABORT only {len(models)}/4 region models present'); return

    d = np.load(os.path.join(HERE, 'v3_training.npz'), allow_pickle=True)
    mut_lo, mut_hi = int(d['mut_lo']), int(d['mut_hi'])
    cblo = d['cband_lo']; cbhi = d['cband_hi']

    if args.wells:
        wells = sorted(args.wells.split(','))
    else:
        wells = sorted({w for w, s in zip(d['well'], d['split']) if not s})
    print(f'{len(wells)} wells: {", ".join(wells)}\n')

    ref_rc = ex.load_clean_ref()
    os.makedirs(args.outdir, exist_ok=True)
    rows = []
    mut_ok = mut_n = 0
    for well in wells:
        r, read, region, called = call_well(well, models, ref_rc, d)
        if r is None:
            print(f'{well}: skip ({read})'); continue
        clam = blast_eval(read)
        dllr = blast_eval(parse_esd(os.path.join(ex.GT, well + '.esd'))['sequence'])
        with open(os.path.join(args.outdir, f'{well}_ours.fa'), 'w') as f:
            f.write(f'>v3_{well}\n{read}\n')
        mutcol = ((r['refpos0'] >= mut_lo) & (r['refpos0'] <= mut_hi)
                  & (r['esd_base'] != r['rbase']))
        mstmt = ' mut?: none'
        if mutcol.any():
            mut_n += 1
            ok = called[mutcol][0] == r['esd_base'][mutcol][0]
            mut_ok += int(ok)
            mstmt = (f" mut:{int(ok)} called {called[mutcol][0]} esd "
                     f"{r['esd_base'][mutcol][0]} m13 {r['rbase'][mutcol][0]}")
        band_ok = np.zeros(len(r['refpos0']), bool)
        for k, rp in enumerate(r['refpos0']):
            for blo, bhi in zip(cblo, cbhi):
                if int(blo) <= int(rp) <= int(bhi):
                    band_ok[k] = True
        evalcols = ~band_ok
        ncols = int(evalcols.sum())
        ident = 100.0 * (called[evalcols] == r['rbase'][evalcols]).sum() / ncols
        print(f'=== {well} (span-id {ident:.2f}%, n={ncols}){mstmt}')
        bb_report('OURS', clam)
        bb_report('DLL', dllr)
        rows.append((well, ncols, ident, clam, dllr))

    have = [(w, i, id_, c, dl) for w, i, id_, c, dl in rows if c and dl]
    if not have:
        print('\nNO BLAST ALIGNMENTS'); return
    o_m = float(np.mean([x[3]['matched'] for x in have]))
    d_m = float(np.mean([x[4]['matched'] for x in have]))
    o_p = float(np.mean([x[3]['identity'] for x in have]))
    d_p = float(np.mean([x[4]['identity'] for x in have]))
    o_c = float(np.mean([x[3]['coverage'] for x in have]))
    d_c = float(np.mean([x[4]['coverage'] for x in have]))
    o_f = float(np.mean([x[3]['full_identity'] for x in have]))
    d_f = float(np.mean([x[4]['full_identity'] for x in have]))
    o_b = float(np.mean([x[3]['bases_detected'] for x in have]))
    d_b = float(np.mean([x[4]['bases_detected'] for x in have]))
    span_mean = float(np.mean([x[2] for x in have]))
    n_beat = sum(1 for x in have if x[3]['matched'] >= x[4]['matched'])
    print('\n== PLATE MEANS (held-out, both-aligned wells) ==')
    print(f'  span identity (vs M13, same columns): {span_mean:.2f}%')
    print(f'  {"":20s} {"OURS":>18s} {"DLL":>18s}')
    print(f'  {"bases_detected":20s} {o_b:18.1f} {d_b:18.1f}')
    print(f'  {"matched_bp":20s} {o_m:18.1f} {d_m:18.1f}')
    print(f'  {"pident":20s} {o_p:18.2f} {d_p:18.2f}')
    print(f'  {"coverage":20s} {o_c:18.1f} {d_c:18.1f}')
    print(f'  {"full_identity":20s} {o_f:18.2f} {d_f:18.2f}')
    print(f'  OURS matched_bp >= DLL on {n_beat}/{len(have)} wells')
    ok = o_m >= d_m and o_f >= d_f and o_p >= d_p
    print(f'  INTERNAL STANDARD: {mut_ok}/{mut_n} wells call T (construct), '
          f'not M13 C')
    print(f'  ACCEPTANCE ({">=".join("matched_bp,pident,full_identity")}): '
          f'{"PASS" if ok else "FAIL"}')


if __name__ == '__main__':
    main()