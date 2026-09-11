#!/usr/bin/env python3
"""build_v9_weekend.py - v9 training set: adaptive-width windows + jitter.

Per region the window half-width W_r grows with the CE physics measured on the
calibrated lanes (head peaks ~6 scans wide -> tail peaks ~30+ scans wide), so a
single fixed W=15 window (v6) cannot see the whole tail peak.  Windows are
centered on ESD peak positions (the DLL's own calls) and jittered by d in
{-J..J} so the CNN learns to classify correctly when the de-novo candidate
sits 1-3 scans off the true apex (the measured de-novo centering error).

Output: v9_weekend_r{r}.npz  (per region: X=(N,2*W_r+1,4), y labels, split,
well, scan).  Padding = edge.  Same 48/48 well split as v6 (v3_training.npz).
"""
import os, sys, glob
import numpy as np
os.environ.setdefault('TF_CPP_MIN_LOG_LEVEL', '3')
HERE = os.path.dirname(os.path.realpath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE); sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'sanger_toolkit'))
from extract_training_data import parse_esd

GT = os.path.join(ROOT, 'ground_truth', 'MB1000_M13_DT_Cp312_MD1')
SEP = os.path.join(ROOT, 'cache_sep')
LABELS = 'ACGT'
BASE_MAP = {'A': 0, 'C': 1, 'G': 2, 'T': 3}
CUTS8 = (0.05, 0.15, 0.35, 0.50, 0.65, 0.80, 0.90)
# adaptive half-width per 8-region bin (head -> tail) based on CE physics:
# measured peak half-width ~6 scans head, ~34 tail on calibrated lanes.
W_R = (8, 10, 12, 14, 15, 18, 24, 30)
J = 3  # jitter window in scans: offsets -3..3


def region_of(f, cuts=CUTS8):
    r = 0
    for c in cuts:
        if f >= c: r += 1
        else: break
    return r


def window(lanes, s, w, n):
    lo, hi = s - w, s + w + 1
    win = lanes[max(0, lo):min(n, hi)]
    if lo < 0 or hi > n:
        win = np.pad(win, ((max(0, -lo), max(0, hi - n)), (0, 0)), mode='edge')
    return win.astype(np.float32)


def main():
    d = np.load(os.path.join(HERE, 'v3_training.npz'), allow_pickle=True)
    old_well = np.array([w.decode() if isinstance(w, bytes) else w
                         for w in d['well']])
    tr = {w for w, s in zip(old_well, d['split']) if s}
    wells = sorted({w for w, s in zip(old_well, d['split'])})
    # NOTE: v3_training split=1 means TRAINING well (0 = held-out eval well).
    # We store split identically (True=train) so train/eval are unambiguous.
    acc = {r: {'X': [], 'y': [], 'split': [], 'well': [], 'scan': []}
           for r in range(8)}

    for k, wname in enumerate(wells):
        E = parse_esd(os.path.join(GT, wname + '.esd'))
        if 'sequence' not in E or 'peak_positions' not in E:
            continue
        sep = np.load(os.path.join(SEP, wname + '.npy'))
        n = len(sep)
        pp = np.array([int(s) for s in E['peak_positions']])
        seq = np.asarray(list(E['sequence']))
        ok = (pp >= 15) & (pp < n - 15) & np.isin(seq, list(BASE_MAP))
        pp, seq = pp[ok], seq[ok]
        if len(pp) < 50:
            continue
        fr = np.arange(len(pp), dtype=float) / max(1, len(pp) - 1)
        regs = np.array([region_of(f_) for f_ in fr])
        is_tr = wname in tr
        for i, p in enumerate(pp):
            r = int(regs[i])
            W = W_R[r]
            label = BASE_MAP[seq[i]]
            for dJ in range(-J, J + 1):
                s2 = int(p) + dJ
                if 15 <= s2 < n - 15:
                    acc[r]['X'].append(window(sep, s2, W, n))
                    acc[r]['y'].append(label)
                    acc[r]['split'].append(is_tr)
                    acc[r]['well'].append(wname)
                    acc[r]['scan'].append(s2)
        if (k + 1) % 12 == 0:
            print(f'{k + 1}/{len(wells)} wells')

    for r in range(8):
        L = 2 * W_R[r] + 1
        if len(acc[r]['y']) == 0:
            print(f'region{r}: no samples'); continue
        X = np.stack(acc[r]['X'])
        y = np.array(acc[r]['y'], np.int64)
        split = np.array(acc[r]['split'], bool)
        well = np.array(acc[r]['well'], object)
        scan = np.array(acc[r]['scan'], np.int64)
        out = os.path.join(HERE, f'v9_weekend_r{r}.npz')
        np.savez_compressed(out, X=X, y=y, split=split, well=well, scan=scan)
        print(f'region{r}: X={X.shape} (2*W+1={L}) n_tr={split.sum()} '
              f'n_va={(~split).sum()}')

    print('DONE')


if __name__ == '__main__':
    main()