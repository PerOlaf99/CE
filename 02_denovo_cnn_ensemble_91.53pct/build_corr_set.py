#!/usr/bin/env python3
"""build_corr_set.py - training set for the second-stage per-column corrector.

Feature vector per esd position (the DLL's own called peaks):
  p[0:4]  v6 8-region CNN class probabilities (calibrated lanes)
  f[0:6]  bandstat.band_features (xbnd, sb/T, envAll/T, width, D_Y, floor)
Input  = concat(p, f)  -> 10 floats
Label  = esd base letter (0-3), 'N' rows dropped
Region = 8-region rank bin (same CUTS8 as v6)
Split  = well-level (v3_training.npz)

Output: corr_training.npz {X,p,f,y,region,split,well,scan}
"""
import os, sys, numpy as np
os.environ.setdefault('TF_CPP_MIN_LOG_LEVEL', '3')
HERE = os.path.dirname(os.path.realpath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE); sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'sanger_toolkit'))
import tensorflow as tf
from extract_training_data import parse_esd
import bandstat as bs

GT = os.path.join(ROOT, 'ground_truth', 'MB1000_M13_DT_Cp312_MD1')
SEP = os.path.join(ROOT, 'cache_sep')
W = 15
LABELS = 'ACGT'
BASE_MAP = {'A': 0, 'C': 1, 'G': 2, 'T': 3}
CUTS8 = (0.05, 0.15, 0.35, 0.50, 0.65, 0.80, 0.90)


def region_of(f, cuts=CUTS8):
    r = 0
    for c in cuts:
        if f >= c: r += 1
        else: break
    return r


def window(lanes, s, w=W):
    n = len(lanes); lo, hi = s - w, s + w + 1
    win = lanes[max(0, lo):min(n, hi)]
    if lo < 0 or hi > n:
        win = np.pad(win, ((max(0, -lo), max(0, hi - n)), (0, 0)), mode='edge')
    return win.astype(np.float32)


def zscore(X):
    mu = X.mean(1, keepdims=True); sd = X.std(1, keepdims=True) + 1e-8
    return ((X - mu) / sd).astype(np.float32)


def main():
    d = np.load(os.path.join(HERE, 'v3_training.npz'), allow_pickle=True)
    old_well = np.array([w.decode() if isinstance(w, bytes) else w for w in d['well']])
    tr = {w for w, s in zip(old_well, d['split']) if s}
    wells = sorted({w for w, s in zip(old_well, d['split'])})

    v6 = [tf.keras.models.load_model(f'base_caller_model_v6_cal8_r{r}.keras',
                                     compile=False) for r in range(8)]
    X, p, f, y, region, split, well, scan = ([] for _ in range(8))
    for k, wname in enumerate(wells):
        E = parse_esd(os.path.join(GT, wname + '.esd'))
        if 'sequence' not in E:
            continue
        sep = np.load(os.path.join(SEP, wname + '.npy'))
        pp = np.array([int(s) for s in E['peak_positions']])
        seq = np.asarray(list(E['sequence']))
        ok = (pp >= 20) & (pp < len(sep) - 20) & np.isin(seq, list(BASE_MAP))
        pp, seq = pp[ok], seq[ok]
        if len(pp) < 50:
            continue
        fr = np.arange(len(pp), dtype=float) / max(1, len(pp) - 1)
        regs = np.array([region_of(f_) for f_ in fr])
        Xc = np.array([window(sep, int(s)) for s in pp])
        P = np.zeros((len(pp), 5))
        for r in range(8):
            sel = regs == r
            if sel.sum():
                P[sel] = v6[r].predict(zscore(Xc[sel]), batch_size=256, verbose=0)
        F = bs.band_features(sep, pp)
        P4 = P[:, :4].astype(np.float32)
        X.append(np.concatenate([P4, F], axis=1).astype(np.float32))
        p.append(P4); f.append(F)
        y.append(np.array([BASE_MAP[c] for c in seq], np.int64))
        region.append(regs)
        split.append(np.full(len(pp), wname not in tr, bool))
        well.append(np.full(len(pp), wname, object))
        scan.append(pp)
        if (k + 1) % 12 == 0:
            print(f'{k + 1}/{len(wells)} wells')
    X = np.concatenate(X); p = np.concatenate(p); f = np.concatenate(f)
    y = np.concatenate(y); region = np.concatenate(region)
    split = np.concatenate(split); well = np.concatenate(well); scan = np.concatenate(scan)
    np.savez_compressed(os.path.join(HERE, 'corr_training.npz'),
                        X=X, p=p, f=f, y=y, region=region, split=split,
                        well=well, scan=scan)
    print(f'saved corr_training.npz: X={X.shape} acc-train={split.mean():.3f} '
          f'regions={np.bincount(region, minlength=8)}')


if __name__ == '__main__':
    main()