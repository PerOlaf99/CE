#!/usr/bin/env python3
"""build_dense_training.py - dense per-scan window training set.

Turns m13_split_labels.npz (physical (scan, true-base) labels) into a
per-scan 5-class supervision set: for INITIAL candidate windows (positive
labels + sampled alternatives) the model learns base-or-none at every scan,
so two peaks 3 scans apart both fire and the caller stops collapsing
shoulders < 5 scans apart (the ESD caller's resolution limit).

Rows:
  X  (N, 2*w+1, 4) float32 - RAW 4-channel trace window at scan s, per-window
     z-scored exactly like perfect_basecaller._build_window (mean/std over
     the whole window), so run-time inference can reproduce it.
  y  (N,) uint8 - 0=no base, 1=A, 2=C, 3=G, 4=T
  scan  (N,) int32 - the window's center scan
  well  (N,) S8
  src   (N,) S1 - 'e' esd-matched, 's' split/shoulder, 'v' valley negative,
                  'o' esd-overcall negative, 'b' background noise negative

Positives
  * every true label scan (source e or s), including the 3695 split/shoulder
    bases the .esd caller missed.
  * the split positives come pre-snapped to a real physical channel peak, so
    their windows show the shoulder structure the caller must learn.

Negatives (the interesting bit - teaches the caller WHERE NOT to call)
  * 'v' valley: midpoint of every scan-gap between consecutive labels, when
     the gap is a genuine trough (the C coin under the A, etc.).  This is
     what makes the caller stop merging close peaks into one call.
  * 'o' esd-overcall: the 1219 (scan, well) positions ESD falsely called vs
     M13 -> hard negatives at exactly the spots the DLL got wrong.
  * 'b' background: a small sample of low-signal scans (leading window and
     deep tail), to teach 'none' in the absence of any peak.

Only label windows whose center lies INSIDE the read region.  Balanced-ish:
negatives are capped per well so classes stay mostly pair-wise comparable.

Usage:
  python3 build_dense_training.py [--labels m13_split_labels.npz]
                                  [--window 15] [--max-neg-per-pos 2]
                                  [--out dense_training.npz]
"""
import argparse
import os
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import cimarrontv as cim
from make_esd_labels import MOBILITY, V10_SSM
from extract_m13_clean_training import BASE_MAP

Y_BASE = {b: i + 1 for i, b in enumerate('ACGT')}      # 1..4, 0 = none
LABEL_MAP = {b: i for i, b in enumerate('ACGT')}


def extract_features(ch, s, w):
    """RAW 4-channel window centered at scan s (mirrors perfect_basecaller
    _build_window: raw, no matrix, no shifting)."""
    n = len(ch)
    lo, hi = s - w, s + w + 1
    pad_lo, pad_hi = max(0, -lo), max(0, hi - n)
    win = ch[max(0, lo):min(n, hi)]
    if pad_lo or pad_hi:
        win = np.pad(win, ((pad_lo, pad_hi), (0, 0)), mode='edge')
    mu = win.mean()
    sd = win.std() + 1e-8
    return ((win - mu) / sd).astype(np.float32)


def build_well(well, labels, ref_rc, w, max_neg_per_pos, rand):
    """Return X/y/scan/src rows for one well. ``labels`` is one row of the
    split-labels npz (well, scans, bases, src, over_scans)."""
    rsd_path = os.path.join(HERE, 'MB1000_M13_DT', f'{well}.rsd')
    if not os.path.exists(rsd_path):
        return None
    ch_raw, _ = cim.read_rsd(rsd_path)
    if ch_raw.shape[0] == 4 and ch_raw.shape[1] >= 4:
        ch_raw = ch_raw.T
    n_scans = len(ch_raw)
    scans = labels['scans']
    base_s = np.array([b.decode() for b in labels['bases']])

    # read region: [lead onset, tail trimming] so windows stay in signal
    _, _, _, separated = cim.dsp_full_pipeline(
        ch_raw, MOBILITY, baseline_method='AsyLS', baseline_window=50010,
        smooth_method='Butterworth', smooth_window=5, smooth_order=9,
        matrix=V10_SSM, matrix_apply_point='smoothed')
    start = int(cim.pc_signal_onset(separated, onset_frac=0.02, smooth=40))
    end = int(np.clip(int(scans[-1]) + 800, 0, n_scans - 1))
    region = (max(0, start - 20), min(n_scans, end))

    X, y, ss, src = [], [], [], []
    pos_idx = []

    def add(s, yi, sname, allow_pad=False):
        if not (region[0] + w <= s <= region[1] - 1 - w) and not allow_pad:
            return False
        X.append(extract_features(ch_raw, s, w))
        y.append(yi)
        ss.append(int(s))
        src.append(sname)
        return True

    # positives: every true label
    for i, s in enumerate(scans):
        sc = int(s)
        if region[0] <= sc <= region[1]:
            if add(sc, Y_BASE[base_s[i]], labels['src'][i].decode(),
                   allow_pad=True):
                pos_idx.append(len(y) - 1)

    # valley negatives: midpoint of each intra-label gap when it is a real
    # trough in the separated combined trace (teaches not-to-merge).
    comb = separated.max(axis=1)
    for a, b in zip(scans[:-1], scans[1:]):
        g = int(b) - int(a)
        if g < 3:
            continue
        m = (int(a) + int(b)) // 2
        if m <= region[0] or m >= region[1]:
            continue
        flank = max(float(comb[max(region[0], int(a) - 2)]),
                    float(comb[max(region[0], int(b) - 2)]))
        trough = float(comb[m])
        if flank > 0 and trough / flank < 0.80:
            add(m, 0, 'v')

    # esd-overcall negatives
    ov = labels.get('over_scans', np.array([], dtype=np.int64))
    for s in ov:
        if region[0] <= int(s) <= region[1]:
            add(int(s), 0, 'o')

    # background negatives: sample low-signal scans in the lead-in and tail
    n_bg = max_neg_per_pos * max(1, len(pos_idx)) // 6
    lead = np.where(comb[:max(1, region[0])] <
                    max(float(comb[:max(1, region[0])].max()) * 0.1, float(comb.max()) * 0.02))[0]
    tail = np.where(comb[region[1]:] <
                    max(float(comb[region[1]:].max()) * 0.1, float(comb.max()) * 0.02))[0]
    tail = tail + region[1]
    cand = np.concatenate([lead, tail])
    if len(cand) > n_bg:
        cand = np.sort(rand.choice(cand, n_bg, replace=False))
    for s in cand:
        add(int(s), 0, 'b', allow_pad=True)

    # cap negatives per well to keep class balance sane
    n_pos = len(pos_idx)
    neg_idx = [i for i, yi in enumerate(y) if yi == 0]
    if len(neg_idx) > max_neg_per_pos * max(1, n_pos):
        keep = set(np.sort(rand.choice(neg_idx,
                                       max_neg_per_pos * max(1, n_pos),
                                       replace=False)))
        keep.update(pos_idx)
        ii = sorted(keep)
        X = [X[i] for i in ii]
        y = [y[i] for i in ii]
        ss = [ss[i] for i in ii]
        src = [src[i] for i in ii]
    if len(y) < 200:
        return None
    return dict(X=np.asarray(X, dtype=np.float32),
                y=np.asarray(y, dtype=np.uint8),
                scan=np.asarray(ss, dtype=np.int32),
                src=np.array(src, dtype='S1'),
                n_pos=n_pos, n_neg=len(y) - n_pos)


def run(labels_path, out, window, max_neg_per_pos, seed):
    rand = np.random.default_rng(seed)
    lab = np.load(labels_path, allow_pickle=True)
    wells = np.unique(lab['wells'])
    # unique (well, scan) positive labels -> dict per well
    by_well = {}
    for w in wells:
        m = lab['wells'] == w
        by_well[w] = dict(scans=lab['scans'][m], bases=lab['bases'][m],
                          src=lab['src'][m])
    # overcalls: map well -> scans
    ow = lab['over_wells']
    for w in wells:
        mo = ow == w
        by_well[w]['over_scans'] = lab['over_scans'][mo]

    ref_rc = _load_ref()
    parts = []
    part_wells = []
    t0 = time.time()
    for wi, w in enumerate(wells):
        r = build_well(w.decode(), by_well[w], ref_rc, window,
                       max_neg_per_pos, rand)
        if r is None:
            print(f'  {w.decode()}: skipped')
            continue
        parts.append(r)
        part_wells.append(w.decode())
        by = np.bincount(r['y'], minlength=5)
        print(f'  {w.decode()}: pos={r["n_pos"]} neg={r["n_neg"]} '
              f'(A {by[1]},C {by[2]},G {by[3]},T {by[4]},N {by[0]})')
    if not parts:
        sys.exit('no wells produced rows')

    X = np.concatenate([p['X'] for p in parts])
    y = np.concatenate([p['y'] for p in parts])
    scan = np.concatenate([p['scan'] for p in parts])
    wells_arr = np.concatenate([np.full(len(p['y']), well, dtype='S8')
                                for well, p in zip(part_wells, parts)])
    src = np.concatenate([p['src'] for p in parts])
    by = np.bincount(y, minlength=5)
    print(f'OK {time.time()-t0:.1f}s  wells={len(parts)}  rows={len(y)}  '
          f'A {by[1]} C {by[2]} G {by[3]} T {by[4]} N {by[0]}')
    np.savez_compressed(out, X=X, y=y, scan=scan, well=wells_arr, src=src,
                        window=np.int32(window),
                        labels=np.array(list('ACGT')))
    print(f'saved {out}  ({os.path.getsize(out)/1e6:.1f} MB)')


def _load_ref():
    from extract_m13_clean_training import load_clean_ref
    return load_clean_ref()


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--labels', default='m13_split_labels.npz')
    ap.add_argument('--window', type=int, default=15)
    ap.add_argument('--max-neg-per-pos', type=int, default=2)
    ap.add_argument('--seed', type=int, default=7)
    ap.add_argument('--out', default='dense_training.npz')
    args = ap.parse_args()
    run(args.labels, args.out, args.window, args.max_neg_per_pos, args.seed)


if __name__ == '__main__':
    main()