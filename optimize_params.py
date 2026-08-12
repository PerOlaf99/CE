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
    peak_positions = esd_data.get('peak_positions')
    if peak_positions is None:
        peak_positions = esd_data.get('bases_positions')
    return raw, seq, peak_positions


# ---------------------------------------------------------------------------
# Parameter encoding: differential_evolution only handles continuous boxes,
# so categorical choices (baseline method, smoothing method) are encoded as
# a float in [0, n) and floor-decoded. This is a standard, if slightly
# blunt, way to let one optimizer sweep a mixed discrete/continuous space;
# with a reasonable population size DE explores the categorical dimension
# fine because every candidate that lands in method i's bucket still gets
# evaluated with its own separately-optimized continuous sub-parameters.
# ---------------------------------------------------------------------------
N_BASE_DIMS = 10  # bl_method, bl_window01, bl_window2_01, sm_method,
                    # sm_window01, sm_order01, shift0, shift1, shift2, shift3
                    # (the GUI exposes all 4 shift spinners, so none is
                    # pinned to a mobility reference)

# Matrix tuning modes: 'diag' searches the 4 diagonal entries only
# (off-diagonals follow the DEFAULT bleed pattern), 'full' searches all 16
# entries so matrices like the user's (strong instrument-specific bleed)
# are reachable. None means the matrix is fixed (default or from init JSON).
MATRIX_DIMS = {'diag': 4, 'full': 16}
MATRIX_ENTRY_MAX = 5.0  # upper bound for full-matrix entries (bleed can exceed 1)

MOBILITY_MAX_SHIFT = 60


def _map01(u, lo, hi):
    return lo + float(np.clip(u, 0.0, 1.0)) * (hi - lo)


def decode(x, tune_matrix, fixed_matrix=None):
    tune_matrix = 'diag' if tune_matrix is True else tune_matrix
    bl_idx = int(np.clip(np.floor(x[0]), 0, len(BASELINE_METHODS) - 1))
    bl_method = BASELINE_METHODS[bl_idx]
    _, bl_range, _, bl2_range = dsp_core.BASELINE_PARAM_CONFIG[bl_method]
    bl_window = _map01(x[1], *bl_range)
    bl_window2 = None
    if bl2_range is not None:
        bl_window2 = _map01(x[2], *bl2_range)

    sm_idx = int(np.clip(np.floor(x[3]), 0, len(SMOOTH_METHODS) - 1))
    sm_method = SMOOTH_METHODS[sm_idx]
    _, r1, _, r2 = dsp_core.SMOOTH_PARAM_CONFIG[sm_method]
    sm_window = _map01(x[4], *r1)
    sm_order = _map01(x[5], *r2)
    if sm_method in ('Savitzky-Golay', 'Moving Avg', 'Median'):
        sm_window = int(round(sm_window))
        if sm_window % 2 == 0:
            sm_window += 1
    else:
        sm_window = sm_window if sm_method in ('Whittaker',) else int(round(sm_window))
    sm_order = int(round(sm_order)) if sm_method != 'Whittaker' else int(round(sm_order))

    shifts = np.zeros(4, dtype=np.int64)
    for ch in range(4):
        shifts[ch] = int(round(_map01(x[6 + ch], -MOBILITY_MAX_SHIFT, MOBILITY_MAX_SHIFT)))

    if tune_matrix == 'full':
        mat = np.array([_map01(v, 0.0, MATRIX_ENTRY_MAX)
                        for v in x[N_BASE_DIMS:N_BASE_DIMS + 16]])
        matrix = mat.reshape(4, 4)
    elif tune_matrix == 'diag':
        diag = np.array([_map01(x[N_BASE_DIMS + i], 0.20, 0.99) for i in range(4)])
        matrix = dsp_core.make_matrix_from_diagonals(diag)
    elif fixed_matrix is not None:
        # keep the bleed matrix from the init JSON / GUI fixed while the
        # optimizer sweeps baseline/smoothing/shifts only
        matrix = np.asarray(fixed_matrix, dtype=np.float64)
    else:
        matrix = dsp_core.DEFAULT_SPEC_MATRIX

    return dict(baseline_method=bl_method, baseline_window=bl_window,
                baseline_window2=bl_window2,
                smooth_method=sm_method, smooth_window=sm_window,
                smooth_order=sm_order, mobility_shifts=shifts, matrix=matrix)


def esd_match_score(separated, shifts, seq, peak_positions):
    """Replicate the GUI's 'ESD match %' metric: sample the mobility-corrected
    separated trace at ESD's *own* peak positions and count how often the
    strongest dye channel matches the ESD base. Return percent.

    This only tests colour separation at positions ESD already decided were
    peaks (it can't catch peak-count drift), but reporting it alongside the
    aligned identity lets the optimizer chase 'fit between the two boxes'."""
    if seq is None or peak_positions is None or len(peak_positions) == 0:
        return 0.0
    sep = separated.copy()
    for ch in range(4):
        s = int(shifts[ch])
        if s != 0:
            sep[:, ch] = dsp_core.shift_channel(sep[:, ch], s)
    n = min(len(seq), len(peak_positions))
    if n == 0:
        return 0.0
    matches = 0
    for i in range(n):
        p = int(peak_positions[i])
        if 0 <= p < len(sep):
            ch = int(np.argmax(sep[p]))
            if peak_calling.BASE_LETTERS[ch] == seq[i].upper():
                matches += 1
    return 100.0 * matches / n


def score_params(params, wells_data, min_distance=4, prominence_frac=0.05,
                 min_signal_frac=0.80, tolerance=4, onset_frac=0.05,
                 signal_onset_smooth=40, max_align_len=2500):
    """Score a params dict the same way the GUI does.

    Returns (base_ident_pct, esd_match_pct) averaged across wells:
      base_ident_pct - mean NW-alignment identity (%) of the GUI's own
        independent caller (``peak_calling.pc_call_bases_with_shifts``,
        the exact routine the GUI's 'Independent bases' box shows) vs the
        ESD sequence.
      esd_match_pct  - mean of the GUI's circular 'ESD match %'.

    Mobility shifts are handed to the caller (it applies them internally,
    exactly like the GUI, so we never double-shift)."""
    base_idents, esd_matches = [], []
    for raw, esd_seq, esd_positions in wells_data:
        try:
            _, _, _, _, separated, _ = dsp_core.full_pipeline(
                raw, [0, 0, 0, 0], params['baseline_method'],
                params['baseline_window'], params['smooth_method'],
                params['smooth_window'], params['smooth_order'], params['matrix'],
                baseline_window2=params.get('baseline_window2'))
            _, called_seq, _, _ = peak_calling.pc_call_bases_with_shifts(
                separated, params['mobility_shifts'],
                min_distance=min_distance, prominence_frac=prominence_frac,
                tolerance=tolerance, min_signal_frac=min_signal_frac,
                onset_frac=onset_frac, signal_onset_smooth=signal_onset_smooth)
            base_ident = peak_calling.nw_identity(called_seq, esd_seq,
                                                  max_len=max_align_len)
            esd_match = esd_match_score(separated, params['mobility_shifts'],
                                        esd_seq, esd_positions)
        except Exception:
            base_ident, esd_match = 0.0, 0.0
        base_idents.append(base_ident)
        esd_matches.append(esd_match)
    return (float(np.mean(base_idents)) if base_idents else 0.0,
            float(np.mean(esd_matches)) if esd_matches else 0.0)


def _encode_params(params, tune_matrix, bounds):
    """Encode a params dict (from JSON/settings) into the 0-1 normalized
    vector space used by differential_evolution, as an x0 starting point."""
    tune_matrix = 'diag' if tune_matrix is True else tune_matrix
    try:
        bl_idx = BASELINE_METHODS.index(params['baseline_method'])
    except (ValueError, KeyError):
        bl_idx = 0
    x = [float(bl_idx) + 0.5]

    _, bl_range, _, bl2_range = dsp_core.BASELINE_PARAM_CONFIG.get(
        params['baseline_method'], ('Window:', (20, 1000), None, None))
    bl_w = float(params.get('baseline_window', 200))
    x.append((bl_w - bl_range[0]) / (bl_range[1] - bl_range[0]))
    if bl2_range is not None:
        bl2_w = float(params.get('baseline_window2', bl2_range[0]))
        x.append((bl2_w - bl2_range[0]) / (bl2_range[1] - bl2_range[0]))
    else:
        x.append(0.0)  # placeholder, ignored by decode

    try:
        sm_idx = SMOOTH_METHODS.index(params['smooth_method'])
    except (ValueError, KeyError):
        sm_idx = 0
    x.append(float(sm_idx) + 0.5)

    _, r1, _, r2 = dsp_core.SMOOTH_PARAM_CONFIG.get(
        params['smooth_method'], ('Window:', (3, 51), 'Order:', (1, 20)))
    x.append((float(params.get('smooth_window', 7)) - r1[0]) / (r1[1] - r1[0]))
    x.append((float(params.get('smooth_order', 2)) - r2[0]) / (r2[1] - r2[0]))

    shifts = params.get('mobility_shifts', [0, 0, 0, 0])
    for ch in range(4):
        x.append((float(shifts[ch]) + MOBILITY_MAX_SHIFT) / (2 * MOBILITY_MAX_SHIFT))

    if tune_matrix == 'full':
        mat = np.array(params.get('matrix', dsp_core.DEFAULT_SPEC_MATRIX))
        for i in range(16):
            x.append(float(np.clip(mat.reshape(-1)[i] / MATRIX_ENTRY_MAX, 0.0, 1.0)))
    elif tune_matrix == 'diag':
        mat = np.array(params.get('matrix', dsp_core.DEFAULT_SPEC_MATRIX))
        diag = np.diag(mat)
        for i in range(4):
            lo, hi = 0.20, 0.99
            x.append((diag[i] - lo) / (hi - lo))

    n_bl = len(BASELINE_METHODS)
    n_sm = len(SMOOTH_METHODS)
    x[0] = float(np.clip(x[0], 0, n_bl - 1e-6))
    x[3] = float(np.clip(x[3], 0, n_sm - 1e-6))
    for i in range(1, len(x)):
        if i not in (0, 3):
            x[i] = float(np.clip(x[i], 0.0, 1.0))
    return x


def _objective_value(base_ident, esd_match, objective):
    if objective == 'base':
        return base_ident
    if objective == 'esd':
        return esd_match
    # balanced: mean of the two metric boxes
    return 0.5 * base_ident + 0.5 * esd_match


def _objective(x, tune_matrix, fixed_matrix, wells_data, score_kwargs, objective):
    """Module-level DE objective (picklable so ``workers>1`` works).
    Returns the negative objective value; DE minimizes."""
    params = decode(x, tune_matrix, fixed_matrix)
    base_ident, esd_match = score_params(params, wells_data, **score_kwargs)
    return -_objective_value(base_ident, esd_match, objective)


def run_optimization(wells_data, tune_matrix=False, maxiter=60, popsize=15,
                     workers=1, seed=0, progress_cb=None, init_json=None,
                     objective='balanced', min_distance=4, prominence_frac=0.05,
                     min_signal_frac=0.80, tolerance=4, onset_frac=0.05,
                     signal_onset_smooth=40):
    """wells_data: list of (raw_array, esd_sequence_str, esd_peak_positions).
    Returns (best_params_dict, best_score, best_metrics_dict).

    ``tune_matrix``: None/False keeps the matrix fixed (from ``init_json`` or
    DEFAULT), 'diag' searches the 4 diagonal entries only, 'full' searches all
    16 entries so instrument-specific bleed matrices (like the one you entered
    by hand) are reachable.

    ``objective`` selects what is maximized:
      'balanced' - the mean of ESD match % and aligned base identity %,
                   i.e. the optimizer actively improves the fit between the
                   GUI's two metric boxes (the easy ~95% colour-separation
                   metric stays high while the honest alignment metric is
                   pulled up towards it).
      'base'     - only the aligned base identity % (the honest metric).
      'esd'      - only the circular ESD match %.

    If init_json is a JSON file path or dict, its values are used as the
    starting point for differential_evolution (via x0), so the search
    converges faster from a known-good configuration."""
    tune_matrix = 'diag' if tune_matrix is True else tune_matrix
    n_matrix = MATRIX_DIMS.get(tune_matrix, 0)
    n_dims = N_BASE_DIMS + n_matrix
    bounds = [(0, len(BASELINE_METHODS) - 1e-6), (0, 1), (0, 1),
              (0, len(SMOOTH_METHODS) - 1e-6), (0, 1), (0, 1),
              (0, 1), (0, 1), (0, 1), (0, 1)]
    if n_matrix:
        bounds += [(0, 1)] * n_matrix

    score_kwargs = dict(min_distance=min_distance, prominence_frac=prominence_frac,
                        min_signal_frac=min_signal_frac, tolerance=tolerance,
                        onset_frac=onset_frac, signal_onset_smooth=signal_onset_smooth)

    x0 = None
    fixed_matrix = None
    if init_json is not None:
        if isinstance(init_json, str):
            if os.path.exists(init_json):
                with open(init_json) as f:
                    init_json = json.load(f)
        if isinstance(init_json, dict):
            if not tune_matrix and init_json.get('matrix') is not None:
                fixed_matrix = init_json['matrix']
            x0 = _encode_params(init_json, tune_matrix, bounds)
            if x0 is not None:
                base_ident, esd_match = score_params(
                    decode(x0, tune_matrix, fixed_matrix), wells_data,
                    **score_kwargs)
                print(f'Starting from init_json: base={base_ident:.1f}% '
                      f'esd={esd_match:.1f}% '
                      f'obj={_objective_value(base_ident, esd_match, objective):.1f}%')

    gen_count = [0]

    def gen_cb(xk, convergence=None):
        # called once per generation in the main process (never pickled);
        # scipy passes the current best vector plus the convergence value.
        gen_count[0] += 1
        params = decode(np.asarray(xk), tune_matrix, fixed_matrix)
        base_ident, esd_match = score_params(params, wells_data, **score_kwargs)
        val = _objective_value(base_ident, esd_match, objective)
        if progress_cb is not None:
            progress_cb(gen_count[0], val, base_ident, esd_match, params)

    result = differential_evolution(
        _objective, bounds, maxiter=maxiter, popsize=popsize, seed=seed,
        workers=workers, updating='deferred' if workers != 1 else 'immediate',
        polish=False, tol=0.0, mutation=(0.5, 1.5), recombination=0.7, x0=x0,
        args=(tune_matrix, fixed_matrix, wells_data, score_kwargs, objective),
        callback=gen_cb)

    best_params = decode(result.x, tune_matrix, fixed_matrix)
    best_base, best_esd = score_params(best_params, wells_data, **score_kwargs)
    best_score = -result.fun
    best_metrics = {'base_identity_pct': best_base, 'esd_match_pct': best_esd}
    return best_params, best_score, best_metrics


def params_to_json(best_params, best_score, best_metrics, wells):
    mat = best_params['matrix']
    out = {
        'wells_used': wells,
        'best_score_pct': best_score,
        'base_identity_pct': best_metrics.get('base_identity_pct'),
        'esd_match_pct': best_metrics.get('esd_match_pct'),
        'baseline_method': best_params['baseline_method'],
        'baseline_window': best_params['baseline_window'],
        'baseline_window2': best_params.get('baseline_window2'),
        'smooth_method': best_params['smooth_method'],
        'smooth_window': best_params['smooth_window'],
        'smooth_order': best_params['smooth_order'],
        'mobility_shifts': [int(s) for s in best_params['mobility_shifts']],
        'matrix': np.asarray(mat).tolist(),
        'diagonals': np.diag(np.asarray(mat)).tolist(),
    }
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                  formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--base-dir', default=BASE_DIR)
    ap.add_argument('--esd-subdir', default=None,
                     help='ESD variant subdir name (defaults to first found)')
    ap.add_argument('--wells', nargs='+', default=['all'],
                     help="well names, or 'all' to use every .rsd in base-dir")
    ap.add_argument('--tune-matrix', nargs='?', const='diag',
                    choices=['diag', 'full'], default=None,
                    help='also search the spectral-bleed matrix together with '
                         'baseline/smoothing/shifts: "diag" tunes only the 4 '
                         'diagonal entries (off-diagonals follow the default '
                         'bleed pattern); "full" tunes all 16 entries so '
                         'instrument-specific bleed matrices are reachable. '
                         'Off by default (matrix stays fixed).')
    ap.add_argument('--maxiter', type=int, default=60)
    ap.add_argument('--popsize', type=int, default=15)
    ap.add_argument('--workers', type=int, default=1,
                     help='parallel workers for differential_evolution '
                          '(-1 = all cores). Each worker re-runs the full '
                          'DSP pipeline per candidate, so this helps a lot '
                          'once you have more than a couple of wells.')
    ap.add_argument('--seed', type=int, default=0)
    ap.add_argument('--objective', default='balanced',
                    choices=['balanced', 'base', 'esd'],
                    help="'balanced' maximizes the mean of the ESD match %% "
                         "and aligned base identity %% (best 'fit between the "
                         "two boxes'); 'base' only the aligned identity; "
                         "'esd' only the circular ESD match")
    ap.add_argument('--min-distance', type=int, default=4,
                    help='min base spacing for the independent caller '
                         '(GUI Distance spin, default 4)')
    ap.add_argument('--prominence-frac', type=float, default=0.05,
                    help='peak prominence threshold as a fraction of the '
                         'channel scale (GUI Prom spin / 1000, default 0.05)')
    ap.add_argument('--ambig-frac', type=float, default=0.80,
                    help='minimum fraction of the tallest peak signal for a '
                         'channel to contribute to an ambiguous call '
                         '(GUI Ambig spin / 100, default 0.80)')
    ap.add_argument('--init-json', default=None,
                    help='Starting point JSON (from a previous run or from the '
                         'GUI "Copy settings" button). Differential evolution '
                         'will seed its initial population around these values '
                         'instead of random init, converging faster from a '
                         'good starting point.')
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
            raw, seq, peak_positions = load_well(args.base_dir, w, esd_subdir)
            if not seq:
                print(f'  {w}: no ESD sequence, skipping')
                continue
            wells_data.append((raw, seq, peak_positions))
            used.append(w)
        except Exception as e:
            print(f'  {w}: failed to load ({e}), skipping')
    if not wells_data:
        print('No usable wells loaded, aborting.')
        sys.exit(1)
    print(f'Using {len(used)} well(s): {used}')

    t0 = time.time()

    def progress_cb(gen, obj_val, base_ident, esd_match, params):
        print(f'  gen {gen}: obj={obj_val:.2f}%  base={base_ident:.2f}%  '
              f'esd={esd_match:.2f}%  '
              f'{params["baseline_method"]}/{params["smooth_method"]}')

    best_params, best_score, best_metrics = run_optimization(
        wells_data, tune_matrix=args.tune_matrix, maxiter=args.maxiter,
        popsize=args.popsize, workers=args.workers, seed=args.seed,
        progress_cb=progress_cb, init_json=args.init_json,
        objective=args.objective, min_distance=args.min_distance,
        prominence_frac=args.prominence_frac, min_signal_frac=args.ambig_frac)

    dt = time.time() - t0
    print(f'\nDone in {dt:.1f}s. '
          f'Best: base identity={best_metrics["base_identity_pct"]:.2f}%, '
          f'ESD match={best_metrics["esd_match_pct"]:.2f}%, '
          f'objective={best_score:.2f}%')
    print(json.dumps({k: (v.tolist() if isinstance(v, np.ndarray) else v)
                       for k, v in best_params.items() if k != 'matrix'}, indent=2))

    out = params_to_json(best_params, best_score, best_metrics, used)
    with open(args.out, 'w') as f:
        json.dump(out, f, indent=2)
    print(f'Saved to {args.out}')


if __name__ == '__main__':
    main()
