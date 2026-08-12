#!/usr/bin/env python3
"""Headless search for basecalling pipeline parameters (baseline method +
window, smoothing method + window/order, per-channel mobility shift, and
optionally the spectral-bleed matrix diagonals), scored by alignment
identity between an *independent* peak-detection basecall and MegaBACE's
own ESD-called sequence, averaged over as many wells as you give it.

This does not touch the GUI or Qt. It reuses dsp_core.full_pipeline (same
code path the GUI's sliders drive) and peak_calling.call_bases (a real
peak finder, not a lookup into ESD's own peak positions) so a result found
here reproduces exactly if you punch the same numbers into the GUI.

Usage:
    python3 optimize_params.py --wells A01 A02 A03 --maxiter 60
    python3 optimize_params.py --wells all --tune-matrix --out best.json
    python3 optimize_params.py --wells A01 --workers 4 --popsize 20

Requires extract_training_data.py (parse_rsd, parse_esd) to be importable
from the same directory / PYTHONPATH, same as sequencing_gui_V9.py does.
"""
import argparse
import json
import os
import sys
import time

import numpy as np
from scipy.optimize import differential_evolution

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dsp_core
import peak_calling

BASE_DIR = "/media/tv/78B0C7DE1FA7081C/electropherogram/MB1000_M13_DT"

BASELINE_METHODS = dsp_core.BASELINE_METHODS
SMOOTH_METHODS = dsp_core.SMOOTH_METHODS


def find_esd_subdirs(base_dir):
    dirs = {}
    for d in sorted(os.listdir(base_dir)):
        dp = os.path.join(base_dir, d)
        if os.path.isdir(dp) and d.endswith('_MD1'):
            name = d.replace('MB1000_M13_DT_', '').replace('_MD1', '')
            dirs[name] = d
    return dirs


def load_well(base_dir, well, esd_subdir):
    from extract_training_data import parse_rsd, parse_esd
    rsd_path = os.path.join(base_dir, f'{well}.rsd')
    esd_path = os.path.join(base_dir, esd_subdir, f'{well}.esd')
    df = parse_rsd(rsd_path)
    raw = df[['Channel1', 'Channel2', 'Channel3', 'Channel4']].values.astype(np.float64)
    esd_data = parse_esd(esd_path)
    seq = esd_data.get('sequence', '')
    return raw, seq


# ---------------------------------------------------------------------------
# Parameter encoding: differential_evolution only handles continuous boxes,
# so categorical choices (baseline method, smoothing method) are encoded as
# a float in [0, n) and floor-decoded. This is a standard, if slightly
# blunt, way to let one optimizer sweep a mixed discrete/continuous space;
# with a reasonable population size DE explores the categorical dimension
# fine because every candidate that lands in method i's bucket still gets
# evaluated with its own separately-optimized continuous sub-parameters.
# ---------------------------------------------------------------------------
N_BASE_DIMS = 9   # bl_method, bl_window01, sm_method, sm_window01, sm_order01,
                   # shift0, shift1, shift2, (shift3 fixed=0, it's the reference)
N_MATRIX_DIMS = 4  # diagonals, only used if tune_matrix=True

MOBILITY_MAX_SHIFT = 60


def _map01(u, lo, hi):
    return lo + float(np.clip(u, 0.0, 1.0)) * (hi - lo)


def decode(x, tune_matrix):
    bl_idx = int(np.clip(np.floor(x[0]), 0, len(BASELINE_METHODS) - 1))
    bl_method = BASELINE_METHODS[bl_idx]
    _, bl_range = dsp_core.BASELINE_PARAM_CONFIG[bl_method]
    bl_window = _map01(x[1], *bl_range)

    sm_idx = int(np.clip(np.floor(x[2]), 0, len(SMOOTH_METHODS) - 1))
    sm_method = SMOOTH_METHODS[sm_idx]
    _, r1, _, r2 = dsp_core.SMOOTH_PARAM_CONFIG[sm_method]
    sm_window = _map01(x[3], *r1)
    sm_order = _map01(x[4], *r2)
    if sm_method in ('Savitzky-Golay', 'Moving Avg', 'Median'):
        sm_window = int(round(sm_window))
        if sm_window % 2 == 0:
            sm_window += 1
    else:
        sm_window = sm_window if sm_method in ('Whittaker',) else int(round(sm_window))
    sm_order = int(round(sm_order)) if sm_method != 'Whittaker' else int(round(sm_order))

    shifts = np.zeros(4, dtype=np.int64)
    for ch in range(3):
        shifts[ch] = int(round(_map01(x[5 + ch], -MOBILITY_MAX_SHIFT, MOBILITY_MAX_SHIFT)))
    # channel 3 is the mobility reference (shift fixed at 0)

    if tune_matrix:
        diag = np.array([_map01(x[N_BASE_DIMS + i], 0.55, 0.97) for i in range(4)])
        matrix = dsp_core.make_matrix_from_diagonals(diag)
    else:
        matrix = dsp_core.DEFAULT_SPEC_MATRIX

    return dict(baseline_method=bl_method, baseline_window=bl_window,
                smooth_method=sm_method, smooth_window=sm_window,
                smooth_order=sm_order, mobility_shifts=shifts, matrix=matrix)


def score_params(params, wells_data, max_align_len=2500):
    """Mean NW-alignment identity (%) of the independent basecall vs ESD
    sequence, across all loaded wells. Any exception (singular matrix,
    degenerate smoothing window, etc.) scores as 0 for that well rather
    than crashing the whole search."""
    scores = []
    for raw, esd_seq in wells_data:
        try:
            _, _, _, _, separated, _ = dsp_core.full_pipeline(
                raw, params['mobility_shifts'], params['baseline_method'],
                params['baseline_window'], params['smooth_method'],
                params['smooth_window'], params['smooth_order'], params['matrix'])
            _, called_seq, _ = peak_calling.call_bases(separated)
            ident = peak_calling.nw_identity(called_seq, esd_seq, max_len=max_align_len)
        except Exception:
            ident = 0.0
        scores.append(ident)
    return float(np.mean(scores)) if scores else 0.0


def run_optimization(wells_data, tune_matrix=False, maxiter=60, popsize=15,
                      workers=1, seed=0, progress_cb=None):
    """wells_data: list of (raw_array, esd_sequence_str). Returns
    (best_params_dict, best_score, decoded_matrix_as_list)."""
    n_dims = N_BASE_DIMS + (N_MATRIX_DIMS if tune_matrix else 0)
    bounds = [(0, len(BASELINE_METHODS) - 1e-6), (0, 1),
              (0, len(SMOOTH_METHODS) - 1e-6), (0, 1), (0, 1),
              (0, 1), (0, 1), (0, 1)]
    if tune_matrix:
        bounds += [(0, 1)] * N_MATRIX_DIMS

    eval_count = [0]

    def objective(x):
        eval_count[0] += 1
        params = decode(x, tune_matrix)
        ident = score_params(params, wells_data)
        if progress_cb is not None:
            progress_cb(eval_count[0], ident, params)
        return -ident  # minimize

    result = differential_evolution(
        objective, bounds, maxiter=maxiter, popsize=popsize, seed=seed,
        workers=workers, updating='deferred' if workers != 1 else 'immediate',
        polish=False, mutation=(0.5, 1.5), recombination=0.7)

    best_params = decode(result.x, tune_matrix)
    best_score = -result.fun
    return best_params, best_score


def params_to_json(best_params, best_score, wells):
    mat = best_params['matrix']
    return {
        'wells_used': wells,
        'best_identity_pct': best_score,
        'baseline_method': best_params['baseline_method'],
        'baseline_window': best_params['baseline_window'],
        'smooth_method': best_params['smooth_method'],
        'smooth_window': best_params['smooth_window'],
        'smooth_order': best_params['smooth_order'],
        'mobility_shifts': [int(s) for s in best_params['mobility_shifts']],
        'matrix': np.asarray(mat).tolist(),
        'diagonals': np.diag(np.asarray(mat)).tolist(),
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                  formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--base-dir', default=BASE_DIR)
    ap.add_argument('--esd-subdir', default=None,
                     help='ESD variant subdir name (defaults to first found)')
    ap.add_argument('--wells', nargs='+', default=['all'],
                     help="well names, or 'all' to use every .rsd in base-dir")
    ap.add_argument('--tune-matrix', action='store_true',
                     help='also search the spectral-bleed matrix diagonals '
                          '(off by default: the matrix is a property of the '
                          'dye set/instrument, not really a per-read knob, '
                          'and adding it quadruples the search dimensions)')
    ap.add_argument('--maxiter', type=int, default=60)
    ap.add_argument('--popsize', type=int, default=15)
    ap.add_argument('--workers', type=int, default=1,
                     help='parallel workers for differential_evolution '
                          '(-1 = all cores). Each worker re-runs the full '
                          'DSP pipeline per candidate, so this helps a lot '
                          'once you have more than a couple of wells.')
    ap.add_argument('--seed', type=int, default=0)
    ap.add_argument('--out', default='best_params.json')
    args = ap.parse_args()

    subdirs = find_esd_subdirs(args.base_dir)
    if not subdirs:
        print(f'No *_MD1 ESD subdirectories found under {args.base_dir}')
        sys.exit(1)
    esd_subdir = subdirs.get(args.esd_subdir) if args.esd_subdir else next(iter(subdirs.values()))

    if args.wells == ['all']:
        wells = sorted(f[:-4] for f in os.listdir(args.base_dir) if f.endswith('.rsd'))
    else:
        wells = args.wells

    print(f'Loading {len(wells)} well(s) from {args.base_dir} (ESD: {esd_subdir}) ...')
    wells_data, used = [], []
    for w in wells:
        try:
            raw, seq = load_well(args.base_dir, w, esd_subdir)
            if not seq:
                print(f'  {w}: no ESD sequence, skipping')
                continue
            wells_data.append((raw, seq))
            used.append(w)
        except Exception as e:
            print(f'  {w}: failed to load ({e}), skipping')
    if not wells_data:
        print('No usable wells loaded, aborting.')
        sys.exit(1)
    print(f'Using {len(used)} well(s): {used}')

    t0 = time.time()

    def progress_cb(n, ident, params):
        if n % 10 == 0:
            print(f'  eval {n}: identity={ident:.2f}%  '
                  f'{params["baseline_method"]}/{params["smooth_method"]}')

    best_params, best_score = run_optimization(
        wells_data, tune_matrix=args.tune_matrix, maxiter=args.maxiter,
        popsize=args.popsize, workers=args.workers, seed=args.seed,
        progress_cb=progress_cb)

    dt = time.time() - t0
    print(f'\nDone in {dt:.1f}s. Best mean identity vs ESD: {best_score:.2f}%')
    print(json.dumps({k: (v.tolist() if isinstance(v, np.ndarray) else v)
                       for k, v in best_params.items() if k != 'matrix'}, indent=2))

    out = params_to_json(best_params, best_score, used)
    with open(args.out, 'w') as f:
        json.dump(out, f, indent=2)
    print(f'Saved to {args.out}')


if __name__ == '__main__':
    main()
