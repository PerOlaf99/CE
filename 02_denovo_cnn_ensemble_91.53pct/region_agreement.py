#!/usr/bin/env python3
"""Clean per-region agreement: for each candidate, label vs nearest esd base
within +-6 scans.  Isolates where our caller is wrong vs the DLL."""
import os, sys
import numpy as np
os.environ.setdefault('TF_CPP_MIN_LOG_LEVEL', '3')
HERE = os.path.dirname(os.path.realpath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE); sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'sanger_toolkit'))
import tensorflow as tf
import dll_peakdet as dp
import bandstat as bs
from extract_training_data import parse_esd

GT = os.path.join(ROOT, 'ground_truth', 'MB1000_M13_DT_Cp312_MD1')
SEP = os.path.join(ROOT, 'cache_sep')
W = 15
LABELS = 'ACGT'
CUTS8 = (0.05, 0.15, 0.35, 0.50, 0.65, 0.80, 0.90)


def region_of(f):
    r = 0
    for c in CUTS8:
        if f >= c: r += 1
        else: break
    return r


def window(lanes, s, w=W):
    n = len(lanes)
    lo, hi = s - w, s + w + 1
    win = lanes[max(0, lo):min(n, hi)]
    if lo < 0 or hi > n:
        win = np.pad(win, ((max(0, -lo), max(0, hi - n)), (0, 0)), mode='edge')
    return win.astype(np.float32)


def zscore(X):
    mu = X.mean(axis=1, keepdims=True)
    sd = X.std(axis=1, keepdims=True) + 1e-8
    return ((X - mu) / sd).astype(np.float32)


v6 = [tf.keras.models.load_model(f'base_caller_model_v6_cal8_r{r}.keras',
                                 compile=False) for r in range(8)]
wells = ['A01', 'A03', 'B06', 'C07', 'D10', 'E05', 'F02', 'G03', 'G11', 'H08']
stat = {r: [0, 0] for r in range(8)}   # correct / total matched
conf = {r: [] for r in range(8)}
for well in wells:
    sep = np.load(os.path.join(SEP, well + '.npy'))
    pos, _, _ = dp.dll_peaks(sep, env_floor_frac=None, region_window=False,
                             region=(1800, 9650))
    E = parse_esd(os.path.join(GT, well + '.esd'))
    pp = np.array([int(p) for p in E['peak_positions']])
    seq = np.array([b for b in E['sequence']])
    fr = np.arange(len(pos), dtype=float) / max(1, len(pos) - 1)
    regs = np.array([region_of(f) for f in fr])
    X = np.array([window(sep, int(s)) for s in pos])
    P = np.zeros((len(pos), 5))
    for r in range(8):
        sel = regs == r
        if sel.sum():
            P[sel] = v6[r].predict(zscore(X[sel]), batch_size=256, verbose=0)
    pred = P[:, :4].argmax(1)
    pmax = P[:, :4].max(1)
    f = bs.band_features(sep, pos)
    # map each candidate to nearest esd peak within 6
    for i, p in enumerate(pos):
        d = np.abs(pp - p)
        j = np.argmin(d)
        if d[j] > 6 or seq[j] not in 'ACGT':
            continue
        r = regs[i]
        stat[r][1] += 1
        if LABELS[pred[i]] == seq[j]:
            stat[r][0] += 1
        conf[r].append(pmax[i])
print(f'wells={len(wells)}')
print('region  matched  agree%   conf(p50)')
for r in range(8):
    if stat[r][1]:
        print(f'  r{r}: {stat[r][1]:5d}  {100*stat[r][0]/stat[r][1]:5.1f}%   '
              f'{np.median(conf[r]):.2f}')