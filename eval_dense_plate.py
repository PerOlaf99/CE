#!/usr/bin/env python3
"""eval_dense_plate.py - decode + full-plate eval of dense_caller.keras.

Runs the dense 5-class CNN over every scan in the callable region, decodes
peaks (collapse consecutive same-letter runs), and scores:
  1. NW identity vs ESD (de-novo quality)
  2. Per-base accuracy vs M13 reference (the headline metric)
  3. Split recovery: how many of the ESD-missed shoulder bases get called
  4. Base count: vs greedy baseline

Compares side-by-side with the greedy caller baseline so both metrics land
in the same table.

Usage:
  python3 eval_dense_plate.py [--model dense_caller.keras]
                               [--wells A01 B05 ...] [--all]
                               [--min-height 0.5] [--min-dist 3]
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


def zscore(X):
    mu = X.mean(axis=1, keepdims=True)
    sd = X.std(axis=1, keepdims=True) + 1e-8
    return ((X - mu) / sd).astype(np.float32)


def extract_features(ch, s, w):
    n = len(ch)
    lo, hi = s - w, s + w + 1
    pad_lo, pad_hi = max(0, -lo), max(0, hi - n)
    win = ch[max(0, lo):min(n, hi)]
    if pad_lo or pad_hi:
        win = np.pad(win, ((pad_lo, pad_hi), (0, 0)), mode='edge')
    mu = win.mean()
    sd = win.std() + 1e-8
    return ((win - mu) / sd).astype(np.float32)


def decode_dense(ch_raw, region, model, w=15, min_height=0.5, min_dist=3):
    """Score every scan in region, decode to (peaks_scans, letters, confs)."""
    n = len(ch_raw)
    start, stop = int(region[0]), int(region[1])
    lo = max(w, start)
    hi = min(n - w - 1, stop)
    if hi <= lo:
        return np.array([], dtype=int), '', np.array([], dtype=float)
    scans = np.arange(lo, hi + 1, dtype=np.int32)
    X = np.array([extract_features(ch_raw, int(s), w) for s in scans],
                 dtype=np.float32)
    probs = model.predict(zscore(X), verbose=0)
    p_base = 1.0 - probs[:, 0]
    letters_map = 'NACGT'
    arg = probs.argmax(1)

    on = p_base >= min_height
    peaks_s, peaks_l, peaks_p = [], [], []
    i = 0
    while i < len(scans):
        if not on[i]:
            i += 1
            continue
        j = i
        while j < len(scans) and on[j]:
            j += 1
        seg = slice(i, j)
        best = int(p_base[seg].argmax()) + i
        letter = letters_map[arg[best]]
        if letter == 'N':
            i = j
            continue
        peaks_s.append(int(scans[best]))
        peaks_l.append(letter)
        peaks_p.append(float(p_base[best]))
        i = j
    # merge same-letter runs closer than min_dist
    if not peaks_s:
        return np.array([], dtype=int), '', np.array([], dtype=float)
    ms, ml, mp = [peaks_s[0]], [peaks_l[0]], [peaks_p[0]]
    for k in range(1, len(peaks_s)):
        if peaks_s[k] - ms[-1] < min_dist and peaks_l[k] == ml[-1]:
            if peaks_p[k] > mp[-1]:
                ms[-1] = peaks_s[k]
                mp[-1] = peaks_p[k]
        else:
            ms.append(peaks_s[k])
            ml.append(peaks_l[k])
            mp.append(peaks_p[k])
    return np.array(ms, dtype=int), ''.join(ml), np.array(mp, dtype=float)


def greedy_baseline(rsd_path):
    """Run greedy caller via Cimarron engine; return (seq, scans, n_bases)."""
    eng = cim.Cimarron312(
        variant='3.12',
        spec_sep_matrix=V10_SSM, mobility_shifts=MOBILITY,
        baseline_method='AsyLS', baseline_window=50010,
        smooth_method='Butterworth', smooth_window=5, smooth_order=9,
        matrix_apply_point='smoothed', caller='greedy',
        bgn_end_method='perbase', greedy_window=6)
    ch, scans_rsd = cim.read_rsd(rsd_path)
    res = eng.call(ch, scans_rsd)
    seq = ''.join(b for b in res.sequence if b in 'ACGT')
    peaks = np.array([int(round(pk.time)) for base, pk
                      in zip(res.sequence, res.peaks) if base in 'ACGT'],
                     dtype=int)
    return seq, peaks, len(seq)


def perbase_vs_ref(seq, ref):
    al = seed_sw_align(seq, ref)
    if al is None:
        return float('nan')
    q_al, r_al = al
    m = sum(1 for a, b in zip(q_al, r_al) if a == b)
    return 100.0 * m / max(1, len(q_al))


def nw_vs_esd(seq, esd_seq):
    return cim.pc_nw_identity(seq, esd_seq)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--model', default=os.path.join(HERE, 'dense_caller.keras'))
    ap.add_argument('--wells', nargs='*')
    ap.add_argument('--all', action='store_true', help='all 96 wells')
    ap.add_argument('--plate', default=os.path.join(ROOT, 'MB1000_M13_DT'))
    ap.add_argument('--gt', default=os.path.join(ROOT, 'ground_truth',
                                                  'MB1000_M13_DT_Cp312_MD1'))
    ap.add_argument('--min-height', type=float, default=0.50)
    ap.add_argument('--min-dist', type=int, default=3)
    args = ap.parse_args()

    os.environ.setdefault('TF_CPP_MIN_LOG_LEVEL', '3')
    import tensorflow as tf
    print(f'loading model: {args.model}', flush=True)
    model = tf.keras.models.load_model(args.model, compile=False)
    w = int(model.input_shape[1] // 2)
    print(f'  window half-width = {w}, input shape = {model.input_shape}')

    ref = load_clean_ref()
    all_wells = [f'{r}{c:02d}' for r in 'ABCDEFGH' for c in range(1, 13)]
    if args.all:
        wells = all_wells
    elif args.wells:
        wells = args.wells
    else:
        wells = all_wells[:12]

    labels_npz = os.path.join(HERE, 'm13_split_labels.npz')
    has_labels = os.path.isfile(labels_npz)
    if has_labels:
        lab = np.load(labels_npz, allow_pickle=True)

    results = []
    t0 = time.time()
    for wi, well in enumerate(wells):
        rsd_path = os.path.join(args.plate, f'{well}.rsd')
        esd_path = os.path.join(args.gt, f'{well}.esd')
        if not os.path.isfile(rsd_path):
            continue
        esd_seq = cim.read_esd(esd_path)['sequence'] if os.path.isfile(esd_path) else ''

        ch_raw, _ = cim.read_rsd(rsd_path)
        if ch_raw.shape[0] == 4 and ch_raw.shape[1] >= 4:
            ch_raw = ch_raw.T
        _, _, _, separated = cim.dsp_full_pipeline(
            ch_raw, MOBILITY, baseline_method='AsyLS', baseline_window=50010,
            smooth_method='Butterworth', smooth_window=5, smooth_order=9,
            matrix=V10_SSM, matrix_apply_point='smoothed')
        start = int(cim.pc_signal_onset(separated, onset_frac=0.02, smooth=40))
        # tail: use last scan with >10% of max total
        tot = separated.sum(axis=1)
        mx = float(tot[start:].max()) if start < len(tot) else 1.0
        tail = np.where(tot[start:] > mx * 0.10)[0]
        stop = int(start + tail[-1]) + 20 if len(tail) > 0 else len(ch_raw) - 1
        region = (start, min(len(ch_raw), stop))

        # dense decode
        dense_peaks, dense_seq, dense_p = decode_dense(
            ch_raw, region, model, w=w,
            min_height=args.min_height, min_dist=args.min_dist)

        # greedy baseline
        g_seq, g_peaks, g_len = greedy_baseline(rsd_path)

        nw_d = nw_vs_esd(dense_seq, esd_seq) if esd_seq else float('nan')
        nw_g = nw_vs_esd(g_seq, esd_seq) if esd_seq else float('nan')
        pb_d = perbase_vs_ref(dense_seq, ref) if dense_seq else float('nan')
        pb_g = perbase_vs_ref(g_seq, ref) if g_seq else float('nan')
        pb_esd = perbase_vs_ref(esd_seq, ref) if esd_seq else float('nan')

        # split recovery: how many ESD-missed labels does dense caller hit?
        split_hits = 0
        split_total = 0
        if has_labels:
            wl = lab['wells']
            m = np.array([w.decode() == well for w in wl])
            wl_scans = lab['scans'][m]
            wl_bases = lab['bases'][m]
            wl_src = lab['src'][m]
            sm = np.array([s.decode() == 's' for s in wl_src])
            for sc, ba in zip(wl_scans[sm], wl_bases[sm]):
                split_total += 1
                sc = int(sc)
                dists = np.abs(dense_peaks - sc)
                if len(dists) == 0:
                    continue
                k = dists.argmin()
                if dists[k] <= 4 and dense_seq[k] == ba.decode():
                    split_hits += 1

        results.append(dict(
            well=well, nw_d=nw_d, nw_g=nw_g, pb_d=pb_d, pb_g=pb_g,
            pb_esd=pb_esd, n_dense=len(dense_seq), n_greedy=g_len,
            split_hits=split_hits, split_total=split_total))
        elapsed = time.time() - t0
        print(f'{well}  NW_d={nw_d:.3f} NW_g={nw_g:.3f}  '
              f'pb_d={pb_d:.3f} pb_g={pb_g:.3f} ESD={pb_esd:.3f}  '
              f'n={len(dense_seq)}/{g_len}  splits={split_hits}/{split_total}  '
              f'[{wi+1}/{len(wells)} {elapsed:.0f}s]', flush=True)

    if not results:
        sys.exit('no wells processed')

    arr = {k: np.array([r[k] for r in results]) for k in
           ['nw_d', 'nw_g', 'pb_d', 'pb_g', 'pb_esd',
            'n_dense', 'n_greedy', 'split_hits', 'split_total']}

    print('\n=== PLATE SUMMARY ===')
    print(f'wells:          {len(results)}')
    print(f'NW vs ESD:      dense={np.nanmean(arr["nw_d"]):.4f}  '
          f'greedy={np.nanmean(arr["nw_g"]):.4f}  '
          f'delta={np.nanmean(arr["nw_d"]) - np.nanmean(arr["nw_g"]):+.4f}')
    print(f'per-base vs M13: dense={np.nanmean(arr["pb_d"]):.4f}  '
          f'greedy={np.nanmean(arr["pb_g"]):.4f}  '
          f'ESD={np.nanmean(arr["pb_esd"]):.4f}  '
          f'delta={np.nanmean(arr["pb_d"]) - np.nanmean(arr["pb_g"]):+.4f}')
    print(f'bases/call:     dense={np.mean(arr["n_dense"]):.0f}  '
          f'greedy={np.mean(arr["n_greedy"]):.0f}')
    st = arr['split_total'].sum()
    sh = arr['split_hits'].sum()
    print(f'split recovery: {sh}/{st}  '
          f'({100.0*sh/max(1,st):.1f}%)')
    print(f'time: {time.time()-t0:.0f}s')


if __name__ == '__main__':
    main()
