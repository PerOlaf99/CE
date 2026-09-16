#!/usr/bin/env python3
"""eval_region_stitch.py - overlapping per-region basecallers + stitch, BLAST.

For each held-out well we predict EVERY region model on EVERY usable column
once, then sweep (region count, overlap margin, stitch method) in numpy and
BLAST each stitched read vs M13mp18 (same pipeline as Cimarron 3.12 DLL).

Answer sought: how many overlapping regions are needed, and does stitching
adjacent per-region models beat the hard-cut baseline?

Usage:
  python3 eval_region_stitch.py                      # full sweep, 48 holdout
  python3 eval_region_stitch.py --wells A01,A03      # quick subset
  python3 eval_region_stitch.py --splits 3,4 --margins 0,0.04 \
         --stitches none,conf,vote
"""
import os, sys, argparse, json
import numpy as np
os.environ.setdefault('TF_CPP_MIN_LOG_LEVEL', '3')

HERE = os.path.dirname(os.path.realpath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'sanger_toolkit'))

import extract_v3 as ex
import region_common as rc
from extract_training_data import parse_rsd, parse_esd
from blast_bench import blast_eval, report as bb_report

LABELS = rc.LABELS


def load_all_models(want_splits, tag4=None, tag_all=None):
    """{n: (tag, {r: model})} for the requested splits."""
    cfg = json.load(open(rc.SPLIT_JSON))
    out = {}
    for n in want_splits:
        n = int(n)
        if n not in rc.SPLITS:
            continue
        tag = tag_all or cfg[str(n)].get('tag', 's')
        if n == 4 and tag4:
            tag = tag4
        mm, err = rc.load_models(n, tag)
        if err:
            print(f'split {n}: SKIP ({err[0]})')
            continue
        out[n] = (tag, mm)
        print(f'loaded split {n} ({tag}) regions={len(mm)} cuts='
              f'{rc.SPLITS[n]["cuts"]}')
    return out


def predict_well(ch, r, models, n_regions):
    X = rc.build_windows(ch, [int(s) for s in r['scan']])
    Xn = rc.zscore(X)
    return rc.predict_all_models(models, Xn, n_regions)


def assemble(P, rank, cuts, margin, stitch, tail_frac=None,
             tail_stitch='wmax'):
    """If tail_frac is set, bases with rank > tail_frac use tail_stitch over
    ALL region models (overriding the margin-limited coverage)."""
    n = len(rank)
    called = np.empty(n, dtype='<U1')
    for k in range(n):
        if tail_frac is not None and rank[k] > tail_frac:
            cov = list(range(len(cuts) + 1))
        else:
            cov = rc.covering_regions(rank[k], cuts, margin)
        st = tail_stitch if tail_frac is not None and rank[k] > tail_frac \
            else stitch
        b = rc.stitch_call({r: P[r][k] for r in cov}, cov, st)
        called[k] = LABELS[int(b)]
    return ''.join(called)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--wells', default=None)
    ap.add_argument('--splits', default=None, help='comma list; default all')
    ap.add_argument('--margins', default='0,0.02,0.04,0.08,0.12')
    ap.add_argument('--stitches', default='none,conf,vote,wmax')
    ap.add_argument('--tag4', default=None,
                    help="override 4-region model tag: 's' (retrained) or "
                         "'v3' (original 701.3 baseline); default from json")
    ap.add_argument('--tail-fracs', default=None,
                    help='comma list of tail-zone thresholds to ALSO sweep; '
                         'bases with rank>threshold use max-confidence over '
                         'all models (default None)')
    ap.add_argument('--tail-stitch', default='wmax',
                    help='stitch method inside the tail zone (default wmax)')
    ap.add_argument('--cal', action='store_true',
                    help='predict on calibrated (separated) lanes from '
                         'ROOT/cache_sep instead of raw channels')
    ap.add_argument('--tag', default=None,
                    help='override model tag for ALL splits (e.g. cal)')
    args = ap.parse_args()

    d = np.load(os.path.join(HERE, 'v3_training.npz'), allow_pickle=True)
    if args.wells:
        wells = sorted(args.wells.split(','))
    else:
        wells = sorted({w for w, s in zip(d['well'], d['split']) if not s})

    if args.splits:
        want = [int(x) for x in args.splits.split(',')]
    else:
        want = list(rc.SPLITS.keys())
    models_by_n = load_all_models(want, tag4=args.tag4, tag_all=args.tag)
    if not models_by_n:
        print('no usable splits'); return
    margins = [float(x) for x in args.margins.split(',')]
    stitches = args.stitches.split(',')
    tail_fracs = ([float(x) for x in args.tail_fracs.split(',')]
                  if args.tail_fracs else [None])
    print(f'{len(wells)} wells  splits={sorted(models_by_n)}  '
          f'margins={margins}  stitches={stitches}  '
          f'tail_fracs={tail_fracs} (tail-stitch={args.tail_stitch})\n')

    ref_rc = ex.load_clean_ref()
    jobs = [(n, m, s, t) for n in models_by_n for m in margins for s in stitches
            for t in tail_fracs]
    acc = {j: {'matched': [], 'fi': [], 'pident': [], 'beat': 0, 'n': 0}
           for j in jobs}
    dll_m = []
    rows = []

    for i, well in enumerate(wells, 1):
        if args.cal:
            ch = np.load(os.path.join(ROOT, 'cache_sep',
                                      well + '.npy')).astype(np.float64)
        else:
            ch = parse_rsd(os.path.join(ex.PLATE, well + '.rsd')
                           )[ex.CH_NAMES].values.astype(np.float64)
        esd = parse_esd(os.path.join(ex.GT, well + '.esd'))
        r, why = ex.extract_well(well, ch, esd, ref_rc)
        if r is None:
            print(f'{well}: skip ({why})'); continue
        n = r['n_usable']
        rank = np.arange(n, dtype=float) / max(1, n - 1)
        dj = blast_eval(parse_esd(os.path.join(ex.GT,
                                               well + '.esd'))['sequence'])
        dll_m.append(dj['matched'] if dj else 0.0)

        per_n = {}
        for n_reg in models_by_n:
            tag, mm = models_by_n[n_reg]
            P = predict_well(ch, r, mm, n_reg)
            for m in margins:
                for s in stitches:
                    for t in tail_fracs:
                        read = assemble(P, rank, rc.SPLITS[n_reg]['cuts'],
                                        m, s, tail_frac=t,
                                        tail_stitch=args.tail_stitch)
                        bj = blast_eval(read)
                        key = (n_reg, m, s, t)
                        if bj:
                            acc[key]['matched'].append(bj['matched'])
                            acc[key]['fi'].append(bj['full_identity'])
                            acc[key]['pident'].append(bj['identity'])
                            acc[key]['n'] += 1
                            acc[key]['beat'] += int(bj['matched'] >=
                                                   (dj['matched'] if dj else 0))
                            rows.append((well, n_reg, m, s, t, bj['matched'],
                                         bj['full_identity'], bj['identity'],
                                         dj['matched'] if dj else 0))
        print(f'{well}: n_usable={n}  dll_matched={dll_m[-1]:.0f}  '
              f'({i}/{len(wells)}) done', flush=True)

    print('\n== SWEEP SUMMARY (48-well means) ==')
    print(f'{"split":>6} {"margin":>7} {"stitch":>7} {"tailT":>6} | '
          f'{"matched_bp":>10} {"full_id%":>8} {"pident%":>8} | '
          f'{"beats DLL":>9}  {"DLL matched":>12}')
    for (n, m, s, t), a in sorted(acc.items(),
                                  key=lambda kv: -np.mean(kv[1]['matched'] or [0])):
        if not a['n']:
            continue
        ts = 'all' if t is None else f'{t:.2f}'
        print(f'{n:>6} {m:>7.3f} {s:>7} {ts:>6} | {np.mean(a["matched"]):>10.1f} '
              f'{np.mean(a["fi"]):>8.2f} {np.mean(a["pident"]):>8.2f} | '
              f'{"%d/%d" % (a["beat"], a["n"]):>9}  {np.mean(dll_m):>12.1f}')

    best = max(acc, key=lambda j: np.mean(acc[j]['matched'] or [0]))
    print(f'\nBEST config: {best[0]}-region, margin {best[1]}, stitch '
          f'{best[2]}, tail_frac={best[3]} -> matched_bp '
          f'{np.mean(acc[best]["matched"]):.1f} '
          f'(DLL {np.mean(dll_m):.1f})  pident {np.mean(acc[best]["pident"]):.2f} '
          f'fi {np.mean(acc[best]["fi"]):.2f}, beats DLL on '
          f'{acc[best]["beat"]}/{acc[best]["n"]} wells')

    import csv
    fname = (f'region_stitch_rows_s{",".join(map(str, sorted(models_by_n)))}'
             f'_m{"_".join("%.2g" % x for x in margins)}'
             f'_s{"-".join(sorted(stitches))}'
             f'_t{"_".join("all" if x is None else "%.2f" % x
                           for x in tail_fracs)}.csv')
    with open(os.path.join(HERE, fname), 'w', newline='') as f:
        wr = csv.writer(f)
        wr.writerow(['well', 'n_regions', 'margin', 'stitch', 'tail_frac',
                     'matched', 'full_identity', 'pident', 'dll_matched'])
        wr.writerows(rows)
    print(f'wrote {len(rows)} per-well rows -> {fname}')


if __name__ == '__main__':
    main()