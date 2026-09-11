#!/usr/bin/env python3
"""build_signal_set.py - dataset for the true-signal-region detector.

Labels: the DLL's own called-peak region [first, last] esd peak, expanded by a
margin proportional to local spacing (start margin = 1.5x median head spacing,
stop margin = 1.5x median tail spacing).  The 'true signal' is defined as the
band-containing interval; everything outside is background the caller should
not try to basecall.

Features (raw signal + current, frame-normalized to 128 bins):
  for each of 128 time-bins over the 9647-scan frame:
    f0 max cross-channel env in bin (raw, not calibrated)
    f1 mean current in bin
    f2 std current in bin
    f3 current derivative (bin i - bin i-1)
    f4 4ch sum / bin-norm (local brightness)
  => X shape (N, 128, 5).  y = (start_norm, stop_norm) floats in [0,1],
  where start_norm = start_scan/9647.
"""
import os, sys, numpy as np
HERE = os.path.dirname(os.path.realpath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE); sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'sanger_toolkit'))
from extract_training_data import parse_esd, parse_rsd
from dll_peakdet import env_max

GT = os.path.join(ROOT, 'ground_truth', 'MB1000_M13_DT_Cp312_MD1')
RAW = os.path.join(ROOT, 'MB1000_M13_DT')
NB = 128
FRAME = 9647
CH = ['Channel1', 'Channel2', 'Channel3', 'Channel4']


def bin_features(raw, cur, nb=NB):
    n = len(raw)
    edges = np.linspace(0, n, nb + 1).astype(int)
    env = env_max(raw)
    F = np.zeros((nb, 5), np.float32)
    for b in range(nb):
        lo, hi = edges[b], edges[b + 1]
        if hi <= lo:
            continue
        F[b, 0] = env[lo:hi].max()
        F[b, 1] = cur[lo:hi].mean()
        F[b, 2] = cur[lo:hi].std()
        F[b, 4] = raw[lo:hi].sum() / max(1, hi - lo)
    F[1:, 3] = F[1:, 1] - F[:-1, 1]
    # normalize env & brightness to [0,1] per well
    F[:, 0] /= max(1e-9, F[:, 0].max())
    F[:, 4] /= max(1e-9, F[:, 4].max())
    return F


def main():
    d = np.load(os.path.join(HERE, 'v3_training.npz'), allow_pickle=True)
    old_well = np.array([w.decode() if isinstance(w, bytes) else w for w in d['well']])
    tr = {w for w, s in zip(old_well, d['split']) if s}
    wells = sorted({w for w, s in zip(old_well, d['split'])})

    X, y, spi, split, well = [], [], [], [], []
    for k, wname in enumerate(wells):
        try:
            E = parse_esd(os.path.join(GT, wname + '.esd'))
            df = parse_rsd(os.path.join(RAW, wname + '.rsd'))
        except Exception as e:
            print(wname, 'ERR', e); continue
        raw = df[CH].values.astype(np.float64)
        cur = df['Current'].values.astype(float)
        pp = np.array([int(p) for p in E['peak_positions']])
        if len(pp) < 50 or len(raw) < 8000:
            continue
        # margins from local spacing
        sp0 = np.median(np.diff(pp[:8])) if len(pp) > 8 else 8.0
        sp1 = np.median(np.diff(pp[-8:])) if len(pp) > 8 else 8.0
        start = max(0, pp[0] - int(1.5 * sp0))
        stop = min(len(raw), pp[-1] + int(1.5 * sp1))
        F = bin_features(raw, cur)
        X.append(F)
        y.append((start / len(raw), stop / len(raw)))
        spi.append((start, stop))
        split.append(wname not in tr)
        well.append(wname)
        if (k + 1) % 24 == 0:
            print(k + 1, 'wells')
    X = np.array(X, np.float32)
    y = np.array(y, np.float32)
    spi = np.array(spi)
    split = np.array(split, bool)
    well = np.array(well, object)
    np.savez_compressed(os.path.join(HERE, 'signal_training.npz'),
                        X=X, y=y, span=spi, split=split, well=well)
    print(f'saved signal_training.npz X={X.shape} tr={split.sum()} te={(~split).sum()}')


if __name__ == '__main__':
    main()