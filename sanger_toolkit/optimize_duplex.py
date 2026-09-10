#!/usr/bin/env python3
"""
2-peak duplex self-correcting optimizer.

Each window must contain EXACTLY 2 peaks (2 consecutive bases), and the search
adjusts window position, window width (NOT fixed), and the DSP/greedy
parameters until the 2 called bases equal the expected duplex.  Successive
windows slide by one base, so stitching window k's first base reproduces the
read (e.g. CA,AA,AG,GT,TT -> CAAGTT).

Targets can be anchored two ways (self-correction cross-check):
  --target STR       locate STR in the M13 reference (e.g. CAAGTT), then duplex
                     k = STR[k:k+2], scans derived from the ESD<->M13 anchor map.
  --start-scan N     read-duplex targets start at the ESD base whose peak is >= N
                     (and also reported: what M13 says there).

Per duplex a differential_evolution run varies:
  DSP dims (optional, group-frozen), matrix diag, mobility shifts,
  4 greedy knobs, and 2 window-geometry dims (start offset + width).
The objective rewards exact 2-peak duplex matches, peak positions at the ESD
peak scans, and spacing consistent with the ESD trace, and takes the WORST of
the norm_window / 1.5, *1.5 calls (norm-fragile settings are rejected).

Usage:
  python3 optimize_duplex.py --well A01 --target CAAGTT --n-duplex 5 \
      --maxiter 30 --popsize 10 --workers 8
  python3 optimize_duplex.py --well A01 --start-scan 2090 --n-duplex 5 --greedy search
"""
import argparse, json, os, sys, time
import numpy as np
from scipy.optimize import differential_evolution

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, '99_archive'))
os.environ.setdefault('TF_CPP_MIN_LOG_LEVEL', '3')

import dsp
from basecall import pc_call_bases_greedy
import extract_training_data as etd
from optimize_windows_esd import (load_well, decode, x0_from,
                                  build_m13_map, _global_score, ESD_SUBDIR)

MIN_WIN_LEN, MAX_WIN_LEN = 8.0, 160.0
START_OFF = 40.0
NORM_LIST = (1.0, 1.5, 1.0 / 1.5)
# Window position fidelity: the duplex window center may stray at most MAX_DRIFT
# scans from its expected anchor (hard ceiling HARD_DRIFT).  A window that drifts
# farther is shape-fitting the WRONG part of the trace to manufacture a target
# match (it invents the reference at true variants, e.g. clone C->T at coord
# 311: M13 says C, all 96 wells read T, drifting duplex called "C").  So the
# offset is clamped and the score rejects any window farther than HARD_DRIFT.
MAX_DRIFT = 5.0
HARD_DRIFT = 8.0

_sep_cache = {}


def _sep_key(raw, p):
    m = np.asarray(p['matrix'], dtype=np.float64)
    return (p['baseline_method'], p['baseline_window'], p.get('baseline_window2'),
            p['smooth_method'], p['smooth_window'], p['smooth_order'],
            tuple(int(s) for s in p['mobility_shifts']),
            tuple(round(float(v), 6) for v in m.reshape(-1)),
            p['matrix_apply_point'])


def _separate(raw, p):
    key = _sep_key(raw, p)
    if key not in _sep_cache:
        _, _, _, _, separated, _ = dsp.dsp_full_pipeline(
            raw, list(p['mobility_shifts']), p['baseline_method'],
            p['baseline_window'], p['smooth_method'], p['smooth_window'],
            p['smooth_order'], np.asarray(p['matrix'], dtype=np.float64),
            baseline_window2=p.get('baseline_window2'),
            matrix_apply_point=p.get('matrix_apply_point', 'smoothed'))
        _sep_cache[key] = separated
    return _sep_cache[key]


def call_duplex(raw, p, region):
    """Return (positions, bases) for the window using the greedy caller."""
    sep = _separate(raw, p)
    pos, seq, _, _ = pc_call_bases_greedy(
        sep, list(p['mobility_shifts']),
        window=max(1, int(round(p.get('min_distance', 5)))),
        min_frac=p.get('prominence_frac', 0.1),
        norm_window=max(1, int(round(p.get('norm_window', 800)))),
        region=region, min_distance_floor=p.get('min_distance_floor', 1))
    seq = ''.join(b for b in seq if b in 'ACGT')
    return pos, seq


def duplex_score(seq, pos, target, exp_scans):
    """Raw score for a 2-peak duplex call vs its target + expected scans."""
    if len(target) < 2 or len(seq) == 0:
        return -60.0
    t0, t1 = target[0], target[1]
    s0, s1 = exp_scans
    L = len(seq)
    if L == 2:
        d0, d1 = abs(pos[0] - s0), abs(pos[1] - s1)
        drift = max(d0, d1)
        sc = 20.0 + 60.0 * (seq[0] == t0) + 60.0 * (seq[1] == t1)
        sc -= 1.0 * (d0 + d1)                  # ~1 pt per scan of drift (was 0.05)
        sc -= 0.02 * abs((pos[1] - pos[0]) - (s1 - s0))
        if drift > HARD_DRIFT:
            return -1.0e6                      # drifting window: reject outright
        return max(sc, 0.0)
    if L == 0:
        return -60.0
    if L == 1:
        return -30.0 + 15.0 * (seq == t0 or seq == t1)
    # too many peaks: reward if target appears consecutively, penalize excess
    bonus = 0.0
    for k in range(min(L - 1, 4)):
        if seq[k:k + 2] == target:
            bonus += 25.0
            break
    return bonus - 12.0 * (L - 2)


def refine_duplex(params, raw, region, target, exp_scans, robust=True):
    """Score a candidate, taking the worst over norm_window variations."""
    base = dict(params)
    n = max(20.0, float(params.get('norm_window', 200)))
    scores, lens = [], []
    for f in NORM_LIST:
        v = float(np.clip(n * f, 20, 4000))
        p2 = dict(base)
        p2['norm_window'] = v
        pos, seq = call_duplex(raw, p2, region)
        scores.append(duplex_score(seq, pos, target, exp_scans))
        lens.append(len(seq))
    final = min(scores)
    if robust and len(lens) >= 3:
        final -= 0.02 * (max(lens) - min(lens))
    return max(final, 0.0)


def load_m13(path):
    if path.endswith('.fa') or path.endswith('.fasta'):
        from Bio import SeqIO
        for rec in SeqIO.parse(path, 'fasta'):
            return str(rec.seq).upper()
        raise SystemExit(f'fasta empty: {path}')
    return open(path).read().strip().replace('\n', '').upper()


def target_scans(raw_len, esd_seq, esd_pp, m13_pos, start_idx):
    """Require ESD peaks for the sliding duplex window k=0.."""
    n = len(esd_pp)
    if start_idx is None:
        start_idx = 0
    return esd_pp[0]


def locate_target(m13, target, esd_seq, esd_pp, m13_pos):
    """Convert a target STR into (per-duplex targets, expected scans, m13 coords)."""
    idx = m13.find(target)
    if idx < 0:
        raise SystemExit(f'target {target} not found in M13 reference')
    dups = [target[k:k + 2] for k in range(len(target) - 1)]
    # map M13 base index -> ESD index -> scan
    scans = []
    for k in range(len(target)):
        t = idx + k
        kk = np.where(m13_pos == t)[0]
        if len(kk):
            scans.append(int(esd_pp[int(kk[0])]))
        else:
            near = int(np.argmin(np.abs(m13_pos - t)))
            scans.append(int(esd_pp[near]))
    return dups, scans, idx


def duplex_from_scan(esd_seq, esd_pp, m13_pos, s0, n):
    """Read-duplex targets starting at first ESD base with peak >= s0."""
    i0 = int(np.where(esd_pp >= s0)[0][0]) if np.any(esd_pp >= s0) else 0
    dups, scans, m13target = [], [], ''
    for k in range(n):
        i = i0 + k
        dups.append(esd_seq[i:i + 2])
        scans.append(int(esd_pp[i]))
        if m13_pos[i] >= 0:
            m13target += esd_seq[i]
    return dups, scans, i0, m13target


GLOBAL = {}


def _decode_duplex(x, init_params, dfreeze, tune_matrix, base_end, greedy):
    from optimize_windows_esd import decode as _duplex_decode
    if dfreeze:
        p = dict(init_params)
        gs = 0
    else:
        p = _duplex_decode(x[:base_end], tune_matrix, greedy)
        gs = base_end
    p['min_distance'] = max(1.0, _map1(x[gs + 0], 1.0, 12.0))
    p['prominence_frac'] = _map1(x[gs + 1], 0.01, 0.60)
    p['norm_window'] = max(20.0, _map1(x[gs + 2], 20, 4000))
    p['min_distance_floor'] = max(1.0, _map1(x[gs + 3], 2.0, 7.0))
    # mobility shifts: keep inter-channel spread <=10 scans (mean-centered), so
    # a channel can drift but no channel is more than 5 off the group mean.
    sh = np.asarray(p['mobility_shifts'], dtype=np.float64)
    sh = sh - round(float(sh.mean()))
    sh = np.clip(sh, -5, 5)
    p['mobility_shifts'] = [int(v) for v in sh]
    win_off = np.clip(_map1(x[gs + 4], -START_OFF, START_OFF),
                      -MAX_DRIFT, MAX_DRIFT)
    win_len = _map1(x[gs + 5], MIN_WIN_LEN, MAX_WIN_LEN)
    return p, win_off, win_len


def _obj_impl(x, ctx):
    raw_, tgt, exp_scans, anchor, robust, init_params, dfreeze, tune_matrix, base_end = ctx
    p, off, wl = _decode_duplex(x, init_params, dfreeze, tune_matrix, base_end, True)
    s = int(round(anchor + off))
    region = (max(0, s), min(len(raw_), s + int(round(wl))))
    return -refine_duplex(p, raw_, region, tgt, exp_scans, robust)


def _obj_worker(x):
    return _obj_impl(x, GLOBAL['ctx'])


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--well', default='A01')
    ap.add_argument('--base-dir', default=os.path.join(ROOT, 'MB1000_M13_DT'))
    ap.add_argument('--esd-subdir', default=ESD_SUBDIR)
    ap.add_argument('--ref', default=os.path.join(ROOT, 'M13.md'),
                    help='M13 reference: FASTA or raw-sequence file (default M13.md)')
    tg = ap.add_mutually_exclusive_group(required=True)
    tg.add_argument('--target', help='locate this STR in M13 (e.g. CAAGTT); duplex k = STR[k:k+2]')
    tg.add_argument('--start-scan', type=int, help='ESD read-duplex targets start at this scan')
    tg.add_argument('--m13-idx', type=int, default=None,
                    help='expected duplexes = M13 ref bases starting at this 0-based index '
                         '(polylinker/head mode, reference-anchored instead of ESD-junk-anchored)')
    ap.add_argument('--scan-anchor', type=int, default=2092,
                    help='scan of the --m13-idx first expected base (default 2092)')
    ap.add_argument('--spacing', type=float, default=5.5,
                    help='nominal scan/base spacing for --m13-idx anchors (default 5.5)')
    ap.add_argument('--n-duplex', type=int, default=None, help='number of duplexes (default: len(target)-1 or 20)')
    ap.add_argument('--init-json', default=None)
    ap.add_argument('--freeze-dsp', action='store_true', help='keep baseline/smooth/matrix/shifts pinned at init (fast)')
    ap.add_argument('--tune-matrix', choices=['diag', 'none'], default='diag')
    ap.add_argument('--no-greedy', action='store_true', help='keep greedy knobs + window dims only used by search... (dev)')
    ap.add_argument('--maxiter', type=int, default=30)
    ap.add_argument('--popsize', type=int, default=10)
    ap.add_argument('--max-drift', type=float, default=5.0,
                    help=f'max window drift from anchor in scans (hard cap {HARD_DRIFT})')
    ap.add_argument('--workers', type=int, default=1)
    ap.add_argument('--outdir', default=os.path.join(HERE, 'opt_duplex'))
    ap.add_argument('--seed', type=int, default=7)
    args = ap.parse_args()
    global MAX_DRIFT
    MAX_DRIFT = float(np.clip(args.max_drift, 1.0, HARD_DRIFT))

    raw, esd_seq, esd_pp = load_well(args.base_dir, args.well, args.esd_subdir)
    m13 = load_m13(args.ref)
    s_or, rev, m13_pos = build_m13_map(esd_seq, m13)
    print(f'{args.well}: raw {len(raw)} scans, esd {len(esd_seq)} bp peaks '
          f'{esd_pp.min()}-{esd_pp.max()}; read runs '
          f'{"reverse" if rev else "forward"} strand of M13')

    init_path = args.init_json or os.path.join(HERE, 'A01_2050_2411.json')
    if not os.path.exists(init_path):
        raise SystemExit(f'--init-json not found: {init_path}')
    init = json.load(open(init_path))
    init_params = dict(
        baseline_method=init['baseline_method'], baseline_window=init['baseline_window'],
        baseline_window2=init.get('baseline_window2'),
        smooth_method=init['smooth_method'], smooth_window=init['smooth_window'],
        smooth_order=init['smooth_order'], mobility_shifts=list(init['mobility_shifts']),
        matrix=np.array(init['matrix']),
        matrix_apply_point=init.get('matrix_apply_point', 'smoothed'),
        min_distance=init.get('min_distance', 5.0), prominence_frac=init.get('prominence_frac', 0.1),
        norm_window=init.get('norm_window', 800),
        min_distance_floor=init.get('min_distance_floor', 1))

    if args.target:
        dups, scans, m13_idx = locate_target(m13, args.target, esd_seq, esd_pp, m13_pos)
        n_dup = args.n_duplex or (len(args.target) - 1)
        print(f'target {args.target} in M13 @ base {m13_idx + 1} (0-based {m13_idx}); '
              f'scan anchors: {[s for s in scans]}')
    elif args.m13_idx is not None:
        n_dup = args.n_duplex or 12
        exp_seq = m13[args.m13_idx: args.m13_idx + n_dup + 1]
        dups = [exp_seq[k:k + 2] for k in range(n_dup)]
        scans = [args.scan_anchor + int(round(k * args.spacing))
                 for k in range(n_dup + 1)]
        n_dup = len(dups)
        print(f'M13 idx {args.m13_idx}: expected head string {exp_seq!r}; '
              f'anchors {args.scan_anchor}+{args.spacing} scan/base')
    else:
        dups, scans, i0, m13t = duplex_from_scan(esd_seq, esd_pp, m13_pos, args.start_scan,
                                                 args.n_duplex or 20)
        n_dup = len(dups)
        print(f'start scan {args.start_scan}: first ESD base idx {i0} '
              f'(scan {esd_pp[i0]}); M13-eq string so far: {m13t}')

    # param dims
    from optimize_params import BASELINE_METHODS, SMOOTH_METHODS
    from optimize_windows_esd import decode as _duplex_decode, n_dims, APPLY_POINTS
    tune_matrix = 'diag' if (args.tune_matrix == 'diag' and not args.freeze_dsp) else None
    greedy = True  # the duplex search always tunes greedy knobs in addition to the window
    dfreeze = args.freeze_dsp
    D_dsp = 11 + (4 if tune_matrix == 'diag' else 0)
    base_end = D_dsp if not dfreeze else 0
    bounds = []
    if not dfreeze:
        bounds = [(0, len(BASELINE_METHODS) - 1e-6), (0, 1), (0, 1),
                  (0, len(SMOOTH_METHODS) - 1e-6), (0, 1), (0, 1),
                  (0, 1), (0, 1), (0, 1), (0, 1),
                  (0, len(APPLY_POINTS) - 1e-6)] + [(0, 1)] * 4
    bounds += [(0, 1)] * 4   # greedy knobs
    bounds += [(0, 1), (0, 1)]  # window start offset + length

    def decode_duplex(x):
        if dfreeze:
            p = dict(init_params)
            gs = 0
        else:
            p = _duplex_decode(x[:base_end], tune_matrix, greedy)
            gs = base_end
        p['min_distance'] = max(1.0, _map1(x[gs + 0], 1.0, 12.0))
        p['prominence_frac'] = _map1(x[gs + 1], 0.01, 0.60)
        p['norm_window'] = max(20.0, _map1(x[gs + 2], 20, 4000))
        p['min_distance_floor'] = max(1.0, _map1(x[gs + 3], 2.0, 7.0))
        win_off = np.clip(_map1(x[gs + 4], -START_OFF, START_OFF),
                          -MAX_DRIFT, MAX_DRIFT)
        win_len = _map1(x[gs + 5], MIN_WIN_LEN, MAX_WIN_LEN)
        return p, win_off, win_len

    seed_x = []
    if not dfreeze:
        seed_x = list(x0_from(init_params, tune_matrix, greedy))
    gi = init_params
    seed_x += [(gi.get('min_distance', 5.0) - 1.0) / 11.0,
               (gi.get('prominence_frac', 0.1) - 0.01) / 0.59,
               (gi.get('norm_window', 800) - 20.0) / 3980.0,
               float(np.clip((gi.get('min_distance_floor', 1) - 2.0) / 5.0, 0, 1)),
               0.5, 0.5]
    seed_x = list(np.clip(seed_x, 0.0, 1.0))
    assert len(seed_x) == len(bounds), (len(seed_x), len(bounds))

    def _objective(x, ctx):
        raw_, tgt, exp_scans, anchor, robust = ctx
        p, off, wl = decode_duplex(x)
        s = int(round(anchor + off))
        region = (max(0, s), min(len(raw_), s + int(round(wl))))
        return -refine_duplex(p, raw_, region, tgt, exp_scans, robust)

    print(f'dims={len(bounds)} (freeze_dsp={dfreeze}, matrix=tune_matrix={tune_matrix})')
    os.makedirs(args.outdir, exist_ok=True)

    rows = []
    _sep_cache.clear()
    for k in range(min(n_dup, len(dups))):
        tgt = dups[k]
        exp_scans = (scans[k + 0], scans[k + 1] if k + 1 < len(scans) else scans[k] + 8)
        anchor = scans[k]
        if args.target:
            ie = np.where(m13_pos == (m13_idx + k))[0]
            esd_t = esd_seq[int(ie[0]):int(ie[0]) + 2] if len(ie) else tgt
        else:
            ie = np.where(esd_pp >= anchor)[0]
            esd_t = dups[k]
        ctx = (raw, tgt, exp_scans, anchor, True)
        GLOBAL['ctx'] = (raw, tgt, exp_scans, anchor, True, init_params,
                         dfreeze, tune_matrix, base_end)
        t0 = time.time()
        print(f'\n=== duplex {k + 1}/{min(n_dup, len(dups))}  '
              f'expected={tgt}  scans={exp_scans}  anchor={anchor} ===')
        cost_fn = _obj_worker if args.workers != 1 else _objective
        res = differential_evolution(
            cost_fn, bounds, maxiter=args.maxiter, popsize=args.popsize,
            seed=args.seed + k, workers=args.workers, polish=False, tol=0.0,
            mutation=(0.5, 1.5), recombination=0.7,
            updating='deferred' if args.workers != 1 else 'immediate',
            args=() if args.workers != 1 else (ctx,))
        p, off, wl = decode_duplex(res.x)
        s = int(round(anchor + off))
        region = (max(0, s), min(len(raw), s + int(round(wl))))
        pos, seq = call_duplex(raw, p, region)
        dt = time.time() - t0
        ok = seq == tgt
        esd_cross = esd_t
        pos13 = 'M13' if args.target else 'read'
        print(f'  called={seq!r} expected={tgt!r}  {"MATCH" if ok else "MISS"}  '
              f'ESD={esd_cross!r}  window=[{region[0]},{region[1]}] len={region[1] - region[0]}  '
              f'pos={list(int(v) for v in pos)}  {dt:.0f}s')
        print(f'  d={p["min_distance"]:.2f} prom={p["prominence_frac"]:.3f} '
              f'norm={p["norm_window"]:.0f} floor={p["min_distance_floor"]:.2f} '
              f'apply={p["matrix_apply_point"]}')
        out = {
            'well': args.well, 'duplex': k + 1, 'anchor_scan': int(anchor),
            'window_start': int(region[0]), 'window_stop': int(region[1]),
            'window_len': int(region[1] - region[0]),
            'window_center': int(round((region[0] + region[1]) / 2)),
            'drift': int(round(s - anchor)),
            'expected': tgt, 'esd_target': esd_cross,
            'called': seq, 'called_pos': [int(v) for v in pos],
            'expected_scans': list(int(v) for v in exp_scans),
            'ok': bool(ok),
            'baseline_method': p['baseline_method'], 'baseline_window': p['baseline_window'],
            'baseline_window2': p.get('baseline_window2'),
            'smooth_method': p['smooth_method'], 'smooth_window': p['smooth_window'],
            'smooth_order': p['smooth_order'], 'matrix_apply_point': p['matrix_apply_point'],
            'mobility_shifts': [int(s) for s in p['mobility_shifts']],
            'matrix': np.asarray(p['matrix']).tolist(),
            'min_distance': float(p['min_distance']),
            'prominence_frac': float(p['prominence_frac']),
            'norm_window': float(p['norm_window']),
            'min_distance_floor': float(p.get('min_distance_floor', 1)),
            'fill_gap': init.get('fill_gap', 4), 'fill_margin': init.get('fill_margin', 0.2),
            'fill_in': True, 'band_low': 0, 'band_high': 0, 'band_order': 2,
            'optimized_score': float(res.fun) if res.fun is not None else 0.0,
            'elapsed_s': round(dt, 1),
        }
        fn = os.path.join(args.outdir, f'{args.well}_duplex{k + 1:02d}.json')
        json.dump(out, open(fn, 'w'), indent=2)
        rows.append((k + 1, tgt, seq, ok, int(anchor), region, dt, fn))
        print(f'  saved {fn}')

    print('\n=== duplex summary ===')
    print(f'{"k":>3} {"exp":>3} {"call":>3} {"esd":>3} {"ok":>4} {"anchor":>6} {"window":>14} {"t/s":>5}')
    for k, t, c, ok, a, rg, dt, fn in rows:
        esd_c = json.load(open(fn)).get('esd_target', '--')
        print(f'{k:3d} {t:>3} {c:>3} {esd_c:>3} {"Y" if ok else "n":>4} {a:6d} '
              f'[{rg[0]:5d},{rg[1]:5d}] {dt:5.0f}')
    stitched = ''.join(str(rows[k][2][0]) for k in range(len(rows))
                       if len(str(rows[k][2])) > 0) if rows else ''
    print(f'\nstitched (first base per duplex): {stitched}')


def _map1(u, lo, hi):
    return lo + float(np.clip(u, 0.0, 1.0)) * (hi - lo)


if __name__ == '__main__':
    main()