#!/usr/bin/env python3
"""N-plex window grid: test window sizes containing 2, 3, 5, 7, 10 peaks.

Each window covers N consecutive bases.  The greedy caller within the window
produces peaks; we compare the called N-mer against the expected reference
N-mer.  More peaks per window = more context + more redundancy when windows
overlap (stride < N bases).

For each (N_peaks, window_width) combo, runs the optimizer on test positions
from A01 and records accuracy, drift, and timing.

Stride is fixed at 1 base (maximum overlap = N-1 bases shared between
consecutive windows).  The user can vary stride later once N is chosen.

Usage:
  python3 nplex_grid.py                        # default 100 positions
  python3 nplex_grid.py --n-positions 50       # faster
"""
import argparse, json, os, sys, time
import numpy as np
from scipy.optimize import differential_evolution

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'sanger_toolkit'))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, '99_archive'))

from optimize_duplex import (call_duplex, _obj_worker, GLOBAL, _sep_cache,
                             _decode_duplex, MAX_DRIFT, HARD_DRIFT, START_OFF,
                             MIN_WIN_LEN, MAX_WIN_LEN, NORM_LIST, _sep_key,
                             _separate)
from optimize_windows_esd import load_well
from plate_duplex_bench import align_well, window_init, init_params

ESD_SUB = 'MB1000_M13_DT_Cp312_MD1'


def nplex_score(seq, pos, target, exp_scans, n_peak):
    """Score an N-peak call vs expected N-mer + expected scan positions.

    The expected N-mer may appear ANYWHERE as a contiguous run in the greedy
    output (not only at the start): the window is wider than N peaks and can
    contain extra peaks, so the target is matched as a substring."""
    if len(target) < n_peak:
        return -100.0 * n_peak
    tgt = target[:n_peak]
    if len(seq) == 0:
        return -100.0 * n_peak
    # find contiguous target run (best offset)
    best_off, best_sc = -1, -1e9
    for off in range(len(seq) - n_peak + 1):
        run = seq[off:off + n_peak]
        matches = sum(1 for k in range(n_peak) if run[k] == tgt[k])
        # position penalty: the run's peaks should sit near expected scans
        ppen = 0.0
        mdrift = 0.0
        for k in range(n_peak):
            if off + k < len(pos) and k < len(exp_scans):
                ppen += 1.0 * abs(pos[off + k] - exp_scans[k])
                mdrift = max(mdrift, abs(pos[off + k] - exp_scans[k]))
        sc = 20.0 * n_peak + 60.0 * matches - ppen
        if mdrift > HARD_DRIFT:
            sc = -1.0e6
        if sc > best_sc:
            best_sc, best_off = sc, off
    # penalize excess peaks outside the matched run (the window is too wide clue)
    extra = max(0, len(seq) - n_peak)
    best_sc -= 4.0 * extra
    if abs(best_off - 0) > 3 and best_off > 0:
        best_sc -= 8.0 * best_off  # bias toward runs starting near window start
    return max(best_sc, 0.0)


def run_nplex(raw, tgt, exp_scans, anchor, init, n_peak, seed,
              maxiter=18, popsize=6):
    """Run one N-plex DE via a local objective (does not touch bench code)."""

    def _local_obj(x):
        p, off, wl = _decode_duplex(x, init, True, None, 0, True)
        s = int(round(anchor + off))
        region = (max(0, s), min(len(raw), s + int(round(wl))))
        # worst over norm_window variants + nplex scoring
        base = dict(p)
        n = max(20.0, float(p.get('norm_window', 200)))
        scs, lens = [], []
        for f in NORM_LIST:
            p2 = dict(base)
            p2['norm_window'] = float(np.clip(n * f, 20, 4000))
            pos, seq = call_duplex(raw, p2, region)
            scs.append(nplex_score(seq, pos, tgt, exp_scans, n_peak))
            lens.append(len(seq))
        final = min(scs)
        if len(lens) >= 3:
            final -= 0.02 * (max(lens) - min(lens))
        return -max(final, 0.0)

    t0 = time.time()
    res = differential_evolution(_local_obj, [(0, 1)] * 6,
                                maxiter=maxiter, popsize=popsize,
                                seed=seed, workers=1, polish=False, tol=0.0,
                                mutation=(0.5, 1.5), recombination=0.7)
    p, off, wl = _decode_duplex(res.x, init, True, None, 0, True)
    s = int(round(anchor + off))
    region = (max(0, s), min(len(raw), s + int(round(wl))))
    pos, seq = call_duplex(raw, p, region)
    dt = time.time() - t0
    # ok = target N-mer appears as a contiguous run of the greedy output
    # AND the matching peaks are within HARD_DRIFT of their expected scans.
    ok = False
    tgt = tgt[:n_peak]
    for k in range(len(seq) - n_peak + 1):
        if seq[k:k + n_peak] == tgt:
            inbounds = True
            for j in range(n_peak):
                if k + j < len(pos) and j < len(exp_scans):
                    if abs(pos[k + j] - exp_scans[j]) > HARD_DRIFT:
                        inbounds = False
            if inbounds:
                ok = True
                break
    called_nmer = seq[:n_peak]
    return called_nmer, ok, off, int(region[1] - region[0]), dt


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--well', default='A01')
    ap.add_argument('--ref', default=os.path.join(ROOT, 'M13.md'))
    ap.add_argument('--n-positions', type=int, default=100)
    ap.add_argument('--seed', type=int, default=42)
    ap.add_argument('--maxiter', type=int, default=18)
    ap.add_argument('--popsize', type=int, default=6)
    ap.add_argument('--out', default=os.path.join(ROOT, 'sanger_toolkit', 'nplex_grid.json'))
    args = ap.parse_args()

    ref = open(args.ref).read().strip().upper()
    raw, esd_seq, esd_pp = load_well(os.path.join(ROOT, 'MB1000_M13_DT'),
                                      args.well, ESD_SUB)
    coord = align_well(raw, esd_seq, esd_pp, ref)
    n = len(esd_seq)

    # test positions: need room for the largest N-mer in the ref
    max_n = 10
    valid = [(i, int(coord[i])) for i in range(5, n - 5)
             if coord[i] >= 0 and coord[i] + max_n < len(ref)]
    step = max(1, len(valid) // args.n_positions)
    test_pos = valid[::step][:args.n_positions]
    print(f'well={args.well}  test_positions={len(test_pos)}  '
          f'raw={len(raw)}  esd={n}  ref={len(ref)}  '
          f'MAX_DRIFT={MAX_DRIFT} HARD_DRIFT={HARD_DRIFT}')

    # grid: N_peaks × window_width
    n_peaks_list = [2, 3, 5, 7, 10]
    # window widths: must be wide enough for N peaks (~5.5 scans/peak)
    # and narrow enough to stay focused
    window_widths = [20, 30, 40, 50, 60, 80, 100, 120, 150]

    results = []
    total_combos = sum(1 for N in n_peaks_list
                       for ws in window_widths
                       if ws >= N * 3 and ws <= N * 20)
    run = 0
    for N in n_peaks_list:
        for ws in window_widths:
            if ws < N * 3 or ws > N * 20:
                continue
            run += 1
            t_start = time.time()
            n_ok = 0
            n_tot = 0
            drifts = []
            widths_found = []
            times = []

            for seq_idx, (i, ci) in enumerate(test_pos):
                tgt = ref[ci:ci + N]
                anchor = int(esd_pp[i])
                # expected scans: N consecutive ESD peaks
                exp = []
                for k in range(N):
                    if i + k < len(esd_pp):
                        exp.append(int(esd_pp[i + k]))
                    else:
                        exp.append(int(esd_pp[i]) + int(round(k * 5.5)))
                exp_scans = tuple(exp)

                init = init_params(window_init(anchor), 'a01')
                called, ok, drift, wl, dt = run_nplex(
                    raw, tgt, exp_scans, anchor, init, N,
                    args.seed + i, args.maxiter, args.popsize)
                n_tot += 1
                n_ok += int(ok)
                drifts.append(drift)
                widths_found.append(wl)
                times.append(dt)

            acc = 100.0 * n_ok / n_tot if n_tot else 0
            avg_drift = float(np.mean(np.abs(drifts)))
            avg_width = float(np.mean(widths_found))
            avg_time = np.mean(times)
            elapsed = time.time() - t_start

            rec = dict(n_peaks=N, window_width_target=ws,
                       window_width_avg=round(avg_width, 1),
                       n_positions=n_tot, accuracy=round(acc, 2), n_ok=n_ok,
                       avg_abs_drift=round(avg_drift, 2),
                       avg_time_s=round(avg_time, 2),
                       elapsed_s=round(elapsed, 1))
            results.append(rec)
            print(f'[{run}/{total_combos}] N={N} ws={ws:3d}  '
                  f'acc={acc:5.1f}%  avg_ws={avg_width:5.0f}  '
                  f'drift={avg_drift:.1f}  t={avg_time:.1f}s  '
                  f'({elapsed:.0f}s)', flush=True)

    # best combos
    results.sort(key=lambda r: (-r['accuracy'], r['avg_abs_drift']))
    print('\n=== TOP 15 COMBOS ===')
    print(f'{"N":>3} {"ws":>5} {"acc%":>6} {"drift":>6} {"t/s":>5} {"overlap":>8}')
    for r in results[:15]:
        overlap = r['n_peaks'] - 1  # stride=1 => overlap = N-1
        print(f'{r["n_peaks"]:>3} {r["window_width_target"]:>5} '
              f'{r["accuracy"]:>5.1f}%  {r["avg_abs_drift"]:>5.1f}  '
              f'{r["avg_time_s"]:>4.1f}  {overlap:>6}+1')

    # per-N summary
    print('\n=== ACCURACY BY N_PEAKS (best window_width) ===')
    for N in n_peaks_list:
        rs = [r for r in results if r['n_peaks'] == N]
        if rs:
            best = max(rs, key=lambda r: r['accuracy'])
            print(f'  N={N}: best={best["accuracy"]:.1f}% '
                  f'(ws={best["window_width_target"]}, '
                  f'drift={best["avg_abs_drift"]:.1f}, '
                  f't={best["avg_time_s"]:.1f}s)')

    # per-region breakdown for best combo
    if results:
        best = results[0]
        N = best['n_peaks']
        print(f'\n=== REGION BREAKDOWN for best combo (N={N}, ws={best["window_width_target"]}) ===')
        # re-run best on test positions with region info
        for region, lo, hi in [('head', 0, 60), ('mid', 60, 770), ('tail', 770, 999)]:
            region_pos = [(i, ci) for i, ci in test_pos if lo <= ci < hi]
            if not region_pos:
                continue
            r_ok = 0
            for i, ci in region_pos[:30]:
                tgt = ref[ci:ci + N]
                anchor = int(esd_pp[i])
                exp = [int(esd_pp[i + k]) if i + k < len(esd_pp)
                       else int(esd_pp[i]) + int(round(k * 5.5))
                       for k in range(N)]
                init = init_params(window_init(anchor), 'a01')
                called, ok, _, _, _ = run_nplex(raw, tgt, tuple(exp), anchor,
                                                init, N, args.seed + i)
                r_ok += int(ok)
            ra = 100.0 * r_ok / len(region_pos[:30])
            print(f'  {region:>6}: {ra:.1f}%  n={len(region_pos[:30])}')

    json.dump(results, open(args.out, 'w'), indent=1)
    print(f'\nWROTE {args.out}  ({len(results)} combos)')


if __name__ == '__main__':
    main()
