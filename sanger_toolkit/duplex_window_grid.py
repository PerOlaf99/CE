#!/usr/bin/env python3
"""Empirical grid: run standard duplex on test positions, then analyze accuracy
as a function of actual window width, drift, and position-in-read.

The DE finds the best window geometry per position.  We bin the results by
window width and compute per-bin accuracy.  This reveals the empirical
accuracy-vs-width curve and the optimal overlap region (where adjacent windows
share enough scans to agree on the shared base).

For a true overlap grid (stride sweep), we additionally run the full-read
duplex at different strides and measure stitching accuracy.

Usage:
  python3 duplex_window_grid.py                    # A01, 200 positions
  python3 duplex_window_grid.py --n-positions 50   # quick test
"""
import argparse, json, os, sys, time
import numpy as np
from scipy.optimize import differential_evolution

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'sanger_toolkit'))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, '99_archive'))

from optimize_duplex import (call_duplex, _obj_worker, GLOBAL, _sep_cache,
                             _decode_duplex, MAX_DRIFT, HARD_DRIFT)
from optimize_windows_esd import load_well
from plate_duplex_bench import align_well, window_init, init_params

ESD_SUB = 'MB1000_M13_DT_Cp312_MD1'


def run_duplex(raw, tgt, exp_scans, anchor, init, seed, maxiter=18, popsize=6):
    """Run one duplex DE and return (called, ok, drift, window_width, elapsed)."""
    GLOBAL['ctx'] = (raw, tgt, exp_scans, anchor, True, init, True, None, 0)
    t0 = time.time()
    res = differential_evolution(_obj_worker, [(0, 1)] * 6,
                                maxiter=maxiter, popsize=popsize,
                                seed=seed, workers=1, polish=False, tol=0.0,
                                mutation=(0.5, 1.5), recombination=0.7)
    p, off, wl = _decode_duplex(res.x, init, True, None, 0, True)
    s = int(round(anchor + off))
    region = (max(0, s), min(len(raw), s + int(round(wl))))
    pos, seq = call_duplex(raw, p, region)
    dt = time.time() - t0
    drift = off
    return seq, seq == tgt, drift, int(region[1] - region[0]), dt


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--well', default='A01')
    ap.add_argument('--ref', default=os.path.join(ROOT, 'M13.md'))
    ap.add_argument('--n-positions', type=int, default=200)
    ap.add_argument('--seed', type=int, default=42)
    ap.add_argument('--maxiter', type=int, default=22)
    ap.add_argument('--popsize', type=int, default=8)
    ap.add_argument('--out', default=os.path.join(ROOT, 'sanger_toolkit', 'duplex_window_grid.json'))
    args = ap.parse_args()

    ref = open(args.ref).read().strip().upper()
    raw, esd_seq, esd_pp = load_well(os.path.join(ROOT, 'MB1000_M13_DT'),
                                      args.well, ESD_SUB)
    coord = align_well(raw, esd_seq, esd_pp, ref)
    n = len(esd_seq)

    valid = [(i, int(coord[i])) for i in range(5, n - 5)
             if coord[i] >= 0 and coord[i] + 1 < len(ref)]
    step = max(1, len(valid) // args.n_positions)
    test_pos = valid[::step][:args.n_positions]
    print(f'well={args.well}  test_positions={len(test_pos)}  '
          f'raw={len(raw)}  esd={n}  ref={len(ref)}  '
          f'MAX_DRIFT={MAX_DRIFT} HARD_DRIFT={HARD_DRIFT}')

    rows = []
    for k, (i, ci) in enumerate(test_pos):
        tgt = ref[ci:ci + 2]
        anchor = int(esd_pp[i])
        init = init_params(window_init(anchor), 'a01')
        seq, ok, drift, wl, dt = run_duplex(
            raw, tgt,
            (anchor, int(esd_pp[i + 1]) if i + 1 < len(esd_pp) else anchor + 8),
            anchor, init, args.seed + i, args.maxiter, args.popsize)
        rows.append(dict(i=i, coord=ci, tgt=tgt, called=seq, ok=ok,
                         drift=round(drift, 1), window_width=wl,
                         time_s=round(dt, 2), scan=anchor))
        if (k + 1) % 20 == 0 or k + 1 == len(test_pos):
            print(f'  {k + 1}/{len(test_pos)} done ({time.time():.0f}s)',
                  flush=True)

    json.dump(rows, open(args.out, 'w'), indent=1)
    print(f'\nWROTE {args.out}  ({len(rows)} positions)')

    # --- analysis ---
    ok = [r['ok'] for r in rows]
    acc = 100.0 * sum(ok) / len(ok)
    trustworthy = [r for r in rows if r['ok'] and abs(r['drift']) <= MAX_DRIFT]
    trust_acc = 100.0 * len(trustworthy) / len(rows)
    print(f'\nOVERALL: {acc:.1f}%  ({sum(ok)}/{len(ok)})  '
          f'TRUSTWORTHY(|drift|<=MAX_DRIFT): {trust_acc:.1f}%  ({len(trustworthy)}/{len(rows)})')

    # bin by window width
    ws_bins = {}
    for r in rows:
        b = r['window_width'] // 10 * 10  # 10-scan bins
        ws_bins.setdefault(b, []).append(r)
    print(f'\n{"ws_bin":>8} {"n":>4} {"acc%":>6} {"drift":>6} {"t/s":>5}')
    for b in sorted(ws_bins):
        rs = ws_bins[b]
        ba = 100.0 * sum(r['ok'] for r in rs) / len(rs)
        bd = np.mean([abs(r['drift']) for r in rs])
        bt = np.mean([r['time_s'] for r in rs])
        print(f'{b:>5}-{b+9:<3} {len(rs):>4} {ba:>5.1f}% {bd:>5.1f} {bt:>4.1f}')

    # bin by |drift|
    d_bins = {}
    for r in rows:
        b = int(abs(r['drift']))
        d_bins.setdefault(b, []).append(r)
    print(f'\n{"drift":>6} {"n":>4} {"acc%":>6} {"ws":>5}')
    for b in sorted(d_bins):
        rs = d_bins[b]
        ba = 100.0 * sum(r['ok'] for r in rs) / len(rs)
        bw = np.mean([r['window_width'] for r in rs])
        print(f'{b:>4}+  {len(rs):>4} {ba:>5.1f}% {bw:>4.0f}')

    # per-region accuracy
    for region, lo, hi in [('head', 0, 60), ('mid', 60, 770), ('tail', 770, 999)]:
        rs = [r for r in rows if lo <= r['coord'] < hi]
        if rs:
            ra = 100.0 * sum(r['ok'] for r in rs) / len(rs)
            rw = np.mean([r['window_width'] for r in rs])
            print(f'\n{region:>6}: {ra:.1f}%  avg_ws={rw:.0f}  n={len(rs)}')


if __name__ == '__main__':
    main()
