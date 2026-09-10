#!/usr/bin/env python3
"""optimize_windows.py - automate per-window DSP settings optimization along
the raw trace, the way the user does by hand with A01_2050_411.json etc.

For each overlapping scan-window of the raw chromatogram it runs the SAME
differential-evolution machinery as 99_archive/optimize_params.py, but scores
each candidate against the **M13 reference subsequence for that window** and
maximizes the number of **correctly-matched M13 bases** (not percent identity),
so a settings set that recovers many correct bases beats one that just produces
a short 100%-perfect fragment.

It writes one ready-to-load settings JSON per window (same schema the GUI's
'Load Settings' expects, with region_start/region_stop and esd_offset set),
so you can load each window in the GUI or stitch them with the same script.

Usage:
  python3 optimize_windows.py --well A01 --win-size 800 --overlap 150
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

import dsp_core
from basecall import (
    pc_call_bases_greedy, pc_call_bases_with_shifts, pc_call_bases,
    pc_signal_region, dsp_shift_channel)
from  optimize_params import (
    decode, _encode_params, BASELINE_METHODS, SMOOTH_METHODS,
    MATRIX_DIMS, N_BASE_DIMS)
import extract_training_data as etd

REF = os.path.join(HERE, 'refs', 'm13_M77815.1.fa')
ESD_SUBDIR = 'MB1000_M13_DT_Cp312_MD1'


def m13_seq():
    return ''.join(l.strip() for l in open(REF) if not l.startswith('>'))


def load_well(base_dir, well, esd_subdir):
    d = etd.parse_esd(os.path.join(base_dir, esd_subdir, well + '.esd'))
    seq = d['sequence']
    pp = np.asarray(d['peak_positions'], dtype=np.int64)
    raw = etd.parse_rsd(os.path.join(base_dir, well + '.rsd'))
    raw = raw[['Channel1', 'Channel2', 'Channel3', 'Channel4']].values.astype(np.float64)
    return raw, seq, pp


def nw_match_count(query, reference, match=1, mismatch=-1, gap=-2):
    """Needleman-Wunsch: return (# matching ref bases, aligned length, query len)."""
    q, r = query[:4000], reference[:4000]
    m, n = len(q), len(r)
    if m == 0 or n == 0:
        return 0, 0, m
    dp = np.zeros((m + 1, n + 1), dtype=np.int32)
    dp[:, 0] = np.arange(m + 1) * gap
    dp[0, :] = np.arange(n + 1) * gap
    r_int = np.frombuffer(r.encode('ascii'), dtype=np.uint8).astype(np.int64)
    js = np.arange(1, n + 1, dtype=np.int64)
    gapj = gap * js
    for i in range(1, m + 1):
        qi = ord(q[i - 1])
        prev = dp[i - 1]
        diag = prev[:-1] + np.where(r_int == qi, match, mismatch)
        up = prev[1:] + gap
        pref = np.maximum.accumulate(np.maximum(diag, up) - gapj)
        dp[i, 0] = prev[0] + gap
        dp[i, 1:] = pref + gapj
    i, j = m, n
    matches = aligned = 0
    while i > 0 or j > 0:
        if i > 0 and j > 0 and dp[i, j] == dp[i - 1, j - 1] + (match if q[i - 1] == r[j - 1] else mismatch):
            aligned += 1
            if q[i - 1] == r[j - 1]:
                matches += 1
            i -= 1; j -= 1
        elif i > 0 and dp[i, j] == dp[i - 1, j] + gap:
            aligned += 1; i -= 1
        else:
            aligned += 1; j -= 1
    return matches, aligned, m


def call_window(raw, params, region, method):
    """Run full pipeline on the FULL raw (baseline/smoothing need full-trace
    context), then call bases only within the scan region. Returns sequences,
    positions, plus the separated trace for 'ambiguous' checks if needed."""
    _, _, _, _, separated, _ = dsp_core.full_pipeline(
        raw, [0, 0, 0, 0], params['baseline_method'], params['baseline_window'],
        params['smooth_method'], params['smooth_window'], params['smooth_order'],
        params['matrix'], baseline_window2=params.get('baseline_window2'),
        matrix_apply_point=params.get('matrix_apply_point', 'smoothed'))
    shifts = list(params['mobility_shifts'])
    if method == 'greedy':
        pos, seq, _, _ = pc_call_bases_greedy(
            separated, shifts, window=max(1, int(round(params.get('min_distance', 5)))),
            min_frac=params.get('prominence_frac', 0.1),
            norm_window=max(1, int(round(params.get('norm_window', 800)))),
            region=region)
    else:
        pos, seq, _, _ = pc_call_bases_with_shifts(
            separated, shifts, min_distance=max(1, int(round(params.get('min_distance', 4)))),
            prominence_frac=params.get('prominence_frac', 0.05),
            tolerance=max(1, int(round(params.get('tolerance', 4)))),
            min_signal_frac=params.get('min_signal_frac', 0.80),
            norm_window=max(1, int(round(params.get('norm_window', 800)))),
            region=region)
    seq = ''.join(b for b in seq if b in 'ACGT')
    return seq


def _esd_to_m13_via_blast(esd_seq, ref):
    """Reliable scan->M13 anchor: blast the ESD sequence to M13, take the best
    HSP (which gives true, possibly-circular-corrected M13 coordinates), and
    map each ESD base to its M13 index by linear interpolation along the HSP.
    Returns list of M13 indices (one per ESD base) or None-on-error.
    (Global NW of a partial read onto the long circular M13 is unreliable —
    it landed the A01 read at M13~3283 instead of the true ~5957, so we use
    blast's own alignment instead.)"""
    import subprocess, tempfile
    seq = ''.join(c for c in esd_seq if c in 'ACGT')
    with tempfile.TemporaryDirectory() as td:
        open(os.path.join(td, 'm.fa'), 'w').write('>M13\n' + ref + '\n')
        open(os.path.join(td, 'q.fa'), 'w').write('>q\n' + seq + '\n')
        subprocess.run(['makeblastdb', '-in', os.path.join(td, 'm.fa'),
                        '-dbtype', 'nucl', '-out', os.path.join(td, 'db')],
                       check=True, capture_output=True)
        o = os.path.join(td, 'o.txt')
        subprocess.run(['blastn', '-db', os.path.join(td, 'db'),
                        '-query', os.path.join(td, 'q.fa'), '-task', 'megablast',
                        '-outfmt', '6 qstart qend sstart send length bitscore',
                        '-out', o], check=True, capture_output=True)
        rows = [l.split() for l in open(o) if l.strip()]
        if not rows:
            return None
        r = max(rows, key=lambda x: float(x[5]))
        qs, qe, ss, se = int(r[0]), int(r[1]), int(r[2]), int(r[3])
        # Orientation: if sstart > send the read is reverse-complemented vs the
        # linearized M13 (true here: scan order climbs while M13 drops, e.g.
        # A01 base0 scan2082 -> M13 6286, base840 scan9339 -> M13 5471).
        forward = ss <= se
        out = [None] * len(seq)
        qspan = max(1, qe - qs + 1)
        for i in range(len(seq)):
            if qs - 1 <= i <= qe - 1:
                frac = (i - (qs - 1)) / qspan
                if forward:
                    out[i] = int(round(ss + frac * (se - ss)))
                else:
                    out[i] = int(round(ss - frac * (ss - se)))
        return out


def build_scan_to_m13(esd_pp, esd_map):
    """esd_map is per-ESD-base M13 index (from _esd_to_m13_via_blast).
    Return (sorted scan array, corresponding m13 index array)."""
    pairs = [(int(esd_pp[k]), esd_map[k]) for k in range(len(esd_pp))
             if esd_map is not None and k < len(esd_map) and esd_map[k] is not None]
    if not pairs:
        return np.array([]), np.array([])
    pairs.sort()
    return (np.array([p[0] for p in pairs]),
            np.array([p[1] for p in pairs]))


def refine_windowed_objective(params, raw, region, m13win, method):
    seq = call_window(raw, params, region, method)
    if len(seq) < 10:
        return 0.0
    matches, aligned, qlen = nw_match_count(seq, m13win)
    return float(matches)


def _objective(x, ctx):
    """Module-level (picklable) DE objective. ctx =
    (raw, region, m13win, method, tune_matrix, fixed_matrix)."""
    raw, region, m13win, method, tune_matrix, fixed_matrix = ctx
    params = decode(x, tune_matrix, fixed_matrix)
    return -refine_windowed_objective(params, raw, region, m13win, method)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--well', default='A01')
    ap.add_argument('--base-dir', default=os.path.join(ROOT, 'MB1000_M13_DT'))
    ap.add_argument('--esd-subdir', default=ESD_SUBDIR)
    ap.add_argument('--win-size', type=int, default=700, help='window size in scans')
    ap.add_argument('--overlap', type=int, default=100, help='overlap between windows in scans')
    ap.add_argument('--min-win', type=int, default=None, help='start scan (default: ESD first peak)')
    ap.add_argument('--max-win', type=int, default=None, help='end scan (default: ESD last peak)')
    ap.add_argument('--method', choices=['greedy', 'shifts'], default='greedy')
    ap.add_argument('--tune-matrix', nargs='?', const='diag', choices=['diag', 'full'], default=None)
    ap.add_argument('--maxiter', type=int, default=50)
    ap.add_argument('--popsize', type=int, default=10)
    ap.add_argument('--workers', type=int, default=4)
    ap.add_argument('--outdir', default=os.path.join(HERE, 'opt_windows'))
    ap.add_argument('--esd-offset', type=int, default=2008)
    args = ap.parse_args()

    raw, esd_seq, esd_pp = load_well(args.base_dir, args.well, args.esd_subdir)
    ref = m13_seq()
    n = len(raw)
    print(f'{args.well}: raw len={n}, esd len={len(esd_seq)}, esd peaks {esd_pp.min()}-{esd_pp.max()}')

    lo = args.min_win if args.min_win is not None else int(esd_pp.min())
    hi = args.max_win if args.max_win is not None else int(esd_pp.max())
    step = args.win_size - args.overlap
    windows = []
    s = lo
    while s < hi:
        e = min(n, s + args.win_size)
        windows.append((s, e))
        s += step
        if e >= hi:
            break
    print(f'{len(windows)} windows (size={args.win_size}, overlap={args.overlap}):')
    for s, e in windows:
        print(f'  [{s}, {e}]')

    os.makedirs(args.outdir, exist_ok=True)

    # ---- build a per-window M13 reference via a blast-anchored scan->M13 map ----
    esd_map = _esd_to_m13_via_blast(esd_seq, ref)
    if esd_map is None:
        print('WARNING: could not blast ESD to M13; aborting.')
        sys.exit(1)
    scans, m13pos = build_scan_to_m13(esd_pp, esd_map)
    print(f'ESD->M13 blast anchor: first base maps to M13 idx {int(m13pos[0])}, '
          f'last to {int(m13pos[-1])}')

    def window_m13ref(s0, e0):
        m = (scans >= s0) & (scans <= e0)
        if not m.any():
            idx = int(np.argmin(np.abs(scans - int((s0 + e0) / 2))))
            return ref[max(0, int(m13pos[idx]) - 60): int(m13pos[idx]) + 120]
        a, b = int(m13pos[m].min()), int(m13pos[m].max())
        a = max(0, a - 15)
        b = min(len(ref), b + 30)
        return ref[a:b]

    # default init params (from one manual file)
    default = json.load(open(os.path.join(HERE, 'A01_2050_411.json')))
    init_params = dict(
        baseline_method=default['baseline_method'],
        baseline_window=default['baseline_window'],
        baseline_window2=default['baseline_window2'],
        smooth_method=default['smooth_method'],
        smooth_window=default['smooth_window'],
        smooth_order=default['smooth_order'],
        mobility_shifts=list(default['mobility_shifts']),
        matrix=np.array(default['matrix']),
        matrix_apply_point=default['matrix_apply_point'],
        min_distance=default['min_distance'],
        prominence_frac=default['prominence_frac'],
        norm_window=default['norm_window'],
        tolerance=default['tolerance'],
        min_signal_frac=default['min_signal_frac'],
    )

    tune_matrix = 'diag' if args.tune_matrix is True else args.tune_matrix
    n_matrix = MATRIX_DIMS.get(tune_matrix, 0)
    n_dims = N_BASE_DIMS + n_matrix
    bounds = [(0, len(BASELINE_METHODS) - 1e-6), (0, 1), (0, 1),
              (0, len(SMOOTH_METHODS) - 1e-6), (0, 1), (0, 1),
              (0, 1), (0, 1), (0, 1), (0, 1)]
    if n_matrix:
        bounds += [(0, 1)] * n_matrix
    x0 = _encode_params(init_params, tune_matrix, bounds)
    fixed_matrix = init_params['matrix'] if not tune_matrix else None

    summary = []
    for wi, (s0, e0) in enumerate(windows):
        m13win = window_m13ref(s0, e0)
        region = (s0, e0)
        ctx = (raw, region, m13win, args.method, tune_matrix, fixed_matrix)

        t0 = time.time()
        print(f'\n--- window {wi+1}/{len(windows)} [{s0},{e0}] (m13 ref {len(m13win)} bp) ---')
        res = differential_evolution(
            _objective, bounds, maxiter=args.maxiter, popsize=args.popsize,
            seed=wi, workers=args.workers, polish=False, tol=0.0,
            mutation=(0.5, 1.5), recombination=0.7, x0=x0,
            updating='deferred' if args.workers != 1 else 'immediate',
            args=(ctx,))
        best = decode(res.x, tune_matrix, fixed_matrix)
        best_seq = call_window(raw, best, region, args.method)
        matches, aligned, qlen = nw_match_count(best_seq, m13win)
        dt = time.time() - t0
        print(f'  best matched={matches} aligned={aligned}/{len(best_seq)} '
              f'in {dt:.0f}s | {best["baseline_method"]}/{best["smooth_method"]} '
              f'shifts={[int(s) for s in best["mobility_shifts"]]}')

        # write settings JSON (GUI-ready)
        out = {
            'well': args.well,
            'region_start': int(s0), 'region_stop': int(e0),
            'baseline_method': best['baseline_method'],
            'baseline_window': int(best['baseline_window']),
            'baseline_window2': int(best.get('baseline_window2') or 0),
            'smooth_method': best['smooth_method'],
            'smooth_window': int(best['smooth_window']),
            'smooth_order': int(best['smooth_order']),
            'matrix_apply_point': best.get('matrix_apply_point', 'smoothed'),
            'mobility_shifts': [int(s) for s in best['mobility_shifts']],
            'matrix': np.asarray(best['matrix']).tolist(),
            'esd_offset': args.esd_offset,
            'esd_variant': 'Cp312',
            'basecall_method': 0 if args.method == 'greedy' else 1,
            'min_distance': float(best.get('min_distance', 5)),
            'prominence_frac': float(best.get('prominence_frac', 0.1)),
            'norm_window': int(best.get('norm_window', 800)),
            'tolerance': float(best.get('tolerance', 4)),
            'min_signal_frac': float(best.get('min_signal_frac', 1.0)),
            'matched_m13': int(matches), 'aligned': int(aligned),
            'called_len': int(qlen),
            'optimized_score': float(matches),
        }
        fn = os.path.join(args.outdir, f'{args.well}_[{s0}_{e0}].json')
        with open(fn, 'w') as f:
            json.dump(out, f, indent=2)
        summary.append((s0, e0, matches, aligned, qlen, fn))
        print(f'  saved {fn}')

    print('\n=== summary ===')
    print(f'{"window":16s} {"matched":>8s} {"aligned":>8s} {"called":>7s}')
    for s0, e0, m, a, q, fn in summary:
        print(f'[{s0},{e0:5d}]: {m:8d} {a:8d} {q:7d}')
    print(f'\nTOTAL matched M13 bases across windows: {sum(x[2] for x in summary)}')




if __name__ == '__main__':
    main()
