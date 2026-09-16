#!/usr/bin/env python3
"""patent_steps.py - stepwise Cimarron-patent pipeline vs ESD comparison.

Reframes the DLL decode as the patent's block diagram:
  1. Preprocess        (region start/stop, baseline, spectral unmix)
  2. Window            (nfeeder ~2048 step ~1900)
  3. Per-pass DSP      (band-spacing estimate, FBW filter,
                        iterative real-cepstral blind deconvolution,
                        extra-normalization)
  4. Peak detect       (envelope / zero-crossing FSM)
  5. Fuzzy post        (OmitOkN insertion filter, GapCheck gap fill)
  6. Stitch + trim     (RdrOut overlap blending, quality, L/R trim)

Each stage is a pure function returning (peak_scans, sequence).  The harness
scores EVERY stage against the ground-truth ESD record in the same way:

  POSITION MATCH (the DLL-level metric)
    recall  = |our peaks matched to an ESD peak within tol| / |ESD peaks|
    precision = |our peaks within tol of an ESD peak| / |our peaks|
  NW IDENTITY vs the ESD sequence
  PER-BASE vs M13 reference (the CNN-set metric, same seed align)

This lets us watch one stage at a time: does adding cepstral deconvolution
move position-match toward 1.00?  Currently we do NOT implement all patent
steps - stages are progressively built.  Stage 0 = current best guess; each
later stage is filled in as we go.

Usage:
  python3 patent_steps.py --stage 0 --wells A01 B05 ...
  python3 patent_steps.py --stage all
"""
import argparse
import os
import sys
import time

import numpy as np

__version__ = '1.0'
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = HERE
sys.path.insert(0, HERE)
os.environ.setdefault('TF_CPP_MIN_LOG_LEVEL', '3')

from make_esd_labels import MOBILITY, V10_SSM
from extract_m13_clean_training import load_clean_ref, seed_sw_align

try:
    import cimarrontv as cim
except ImportError:
    import cimarrontv_shim as cim

ALL_WELLS = [f'{r}{c:02d}' for r in 'ABCDEFGH' for c in range(1, 13)]


# --------------------------------------------------------------------------- #
# Stage registry
# --------------------------------------------------------------------------- #

CACHE_SEP = os.path.join('/tmp/opencode', 'patent_sep')


def _dsp(well, rsd_path):
    os.makedirs(CACHE_SEP, exist_ok=True)
    cp = os.path.join(CACHE_SEP, f'{well}.npy')
    if os.path.isfile(cp):
        return np.load(cp)
    ch_raw, _ = cim.read_rsd(rsd_path)
    if ch_raw.shape[0] == 4 and ch_raw.shape[1] >= 4:
        ch_raw = ch_raw.T
    _, _, _, sep = cim.dsp_full_pipeline(
        ch_raw, MOBILITY, baseline_method='AsyLS', baseline_window=50010,
        smooth_method='Butterworth', smooth_window=5, smooth_order=9,
        matrix=V10_SSM, matrix_apply_point='smoothed')
    np.save(cp, sep.astype(np.float32))
    return sep


def stage0_preprocess_only(well, rsd_path):
    """Baseline: preprocess + greedy peak call (before any patent filters).
    Returns (peak_scans, sequence)."""
    _dsp(well, rsd_path)  # prime the cache (used by all later stages)
    ch_raw, _ = cim.read_rsd(rsd_path)
    if ch_raw.shape[0] == 4 and ch_raw.shape[1] >= 4:
        ch_raw = ch_raw.T
    eng = cim.Cimarron312(
        variant='3.12', spec_sep_matrix=V10_SSM, mobility_shifts=MOBILITY,
        baseline_method='AsyLS', baseline_window=50010,
        smooth_method='Butterworth', smooth_window=5, smooth_order=9,
        matrix_apply_point='smoothed', caller='greedy',
        bgn_end_method='perbase', greedy_window=6)
    res = eng.call(ch_raw, None)
    peaks = np.array([int(round(pk.time)) for base, pk in zip(res.sequence, res.peaks)
                      if base in 'ACGT'], dtype=int)
    seq = ''.join(b for b in res.sequence if b in 'ACGT')
    return peaks, seq


# Patent Step 4 - FSM peak detect (envelope/zero-crossing state machine put
# on separated lanes: max envelope + rising/falling local-max FSM + width
# + bgn/end window).  This is the DLL's candidate detector port.
sys.path.insert(0, os.path.join(ROOT, '02_denovo_cnn_ensemble_91.53pct'))


def _fsm_peaks(sep):
    from dll_peakdet import dll_peaks
    pos, seq, _ = dll_peaks(sep, region=None, env_floor_frac=0.05)
    return pos, seq


def _mp_peaks(sep):
    from dll_peakdet import dll_multi_pass
    pos, seq, _, _ = dll_multi_pass(sep, passes=2, verbose=False)
    return pos, seq


def stage4_fsm(well, rsd_path):
    sep = _dsp(well, rsd_path)
    return _fsm_peaks(sep)


def stage5_multipass(well, rsd_path):
    sep = _dsp(well, rsd_path)
    return _mp_peaks(sep)


import cepstral


def stage6_cepstral(well, rsd_path):
    """Patent Steps 2-4: nfeeder window + spacing/FBW + real-cepstral blind
    deconvolution + FSM peak detect."""
    sep = _dsp(well, rsd_path)
    return cepstral.run(sep, window=2048, step=1900, iters=3,
                        env_floor_frac=0.05)


def stage0_preprocess_only(well, rsd_path):
    _dsp(well, rsd_path)  # prime the cache (used by all later stages)
    ch_raw, _ = cim.read_rsd(rsd_path)
    if ch_raw.shape[0] == 4 and ch_raw.shape[1] >= 4:
        ch_raw = ch_raw.T
    eng = cim.Cimarron312(
        variant='3.12', spec_sep_matrix=V10_SSM, mobility_shifts=MOBILITY,
        baseline_method='AsyLS', baseline_window=50010,
        smooth_method='Butterworth', smooth_window=5, smooth_order=9,
        matrix_apply_point='smoothed', caller='greedy',
        bgn_end_method='perbase', greedy_window=6)
    res = eng.call(ch_raw, None)
    peaks = np.array([int(round(pk.time)) for base, pk in zip(res.sequence, res.peaks)
                      if base in 'ACGT'], dtype=int)
    seq = ''.join(b for b in res.sequence if b in 'ACGT')
    return peaks, seq


WSTAGES = {
    4: stage4_fsm,
    5: stage5_multipass,
}
WSTAGES = {
    4: stage4_fsm,
    5: stage5_multipass,
}
STAGES = {
    0: stage0_preprocess_only,
    4: stage4_fsm,
    5: stage5_multipass,
    6: stage6_cepstral,
}


# --------------------------------------------------------------------------- #
# Scoring
# --------------------------------------------------------------------------- #

def position_match(our_peaks, esd_peaks, tol=3):
    """Recall/precision of our peak scan positions vs the ESD record list."""
    our = np.array(sorted(int(p) for p in our_peaks))
    ref = np.array(sorted(int(p) for p in esd_peaks))
    if len(ref) == 0:
        return 0.0, 1.0 if len(our) == 0 else 0.0, 0, 0
    matched = np.zeros(len(ref), dtype=bool)
    for p in our:
        d = np.abs(ref - p)
        k = int(d.argmin()) if len(d) else -1
        if len(d) and d[k] <= tol and not matched[k]:
            matched[k] = True
    recall = float(matched.mean())
    if len(our) == 0:
        precision = 1.0
    else:
        hit = 0
        for p in our:
            if len(ref) and np.abs(ref - p).min() <= tol:
                hit += 1
        precision = hit / len(our)
    return recall, precision, int(matched.sum()), len(ref)


def nw_vs_esd(seq, esd_seq):
    return cim.pc_nw_identity(seq, esd_seq)


def perbase_vs_ref(seq, ref):
    al = seed_sw_align(seq, ref)
    if al is None:
        return float('nan')
    q_al, r_al = al
    m = sum(1 for a, b in zip(q_al, r_al) if a == b)
    return 100.0 * m / max(1, len(q_al))


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #

def run(wells, stage, rsd_root, esd_root, tol=3):
    fn = STAGES[stage]
    ref = load_clean_ref()
    rows = []
    for wi, well in enumerate(wells):
        rsd = os.path.join(rsd_root, f'{well}.rsd')
        esd_p = os.path.join(esd_root, f'{well}.esd')
        if not (os.path.isfile(rsd) and os.path.isfile(esd_p)):
            continue
        esd = cim.read_esd(esd_p)
        esd_seq = esd['sequence']
        esd_pos = esd['peak_positions']
        try:
            peaks, seq = fn(well, rsd)
        except Exception as e:
            print(f'{well}: ERROR {str(e)[:120]}', flush=True)
            continue
        rec, prec, nm, nt = position_match(peaks, esd_pos, tol=tol)
        nw = nw_vs_esd(seq, esd_seq)
        pb = perbase_vs_ref(seq, ref)
        rows.append((well, rec, prec, nw, pb, len(peaks), len(esd_seq)))
        print(f'{well}  recall={rec:.3f} prec={prec:.3f}  NW={nw:.3f} '
              f'pbM13={pb:.3f}  n={len(peaks)}/{len(esd_seq)} '
              f'[{wi+1}/{len(wells)}]', flush=True)
    if not rows:
        print('no wells processed')
        return
    arr = np.array([[r[1], r[2], r[3], r[4]] for r in rows])
    print(f'\n=== STAGE {stage} — {len(rows)} wells (tol={tol}) ===')
    print(f'ESD position recall:  {arr[:, 0].mean():.4f}')
    print(f'ESD position prec:    {arr[:, 1].mean():.4f}')
    print(f'NW vs ESD:            {arr[:, 2].mean():.4f}')
    print(f'per-base vs M13:      {arr[:, 3].mean():.4f}')
    print(f'bases/well:           {np.mean([r[5] for r in rows]):.0f} ours  '
          f'{np.mean([r[6] for r in rows]):.0f} ESD')


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--stage', type=int, default=0)
    ap.add_argument('--wells', nargs='*')
    ap.add_argument('--all', action='store_true')
    ap.add_argument('--tol', type=int, default=3)
    ap.add_argument('--rsd-root', default=os.path.join(ROOT, 'MB1000_M13_DT'))
    ap.add_argument('--esd-root', default=os.path.join(
        ROOT, 'ground_truth', 'MB1000_M13_DT_Cp312_MD1'))
    args = ap.parse_args()
    wells = ALL_WELLS if args.all else (args.wells or ALL_WELLS[:12])
    t0 = time.time()
    run(wells, args.stage, args.rsd_root, args.esd_root, tol=args.tol)
    print(f'time: {time.time() - t0:.0f}s')


if __name__ == '__main__':
    main()