#!/usr/bin/env python3
"""Clean per-region agreement, SCAN-based regions.

For each candidate: label vs nearest esd base within +-6 scans.  Regions are
assigned by the candidate's SCAN fraction of the 9647 frame (0-1), matching
the CNN training cuts.  Also reports how many candidates fall in r0/r1 where
the esd has NO peaks (background = the front our ML region should exclude)."""
import os, sys
import numpy as np
os.environ.setdefault('TF_CPP_MIN_LOG_LEVEL', '3')
HERE = os.path.dirname(os.path.realpath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE); sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'sanger_toolkit'))
import tensorflow as tf
import dll_peakdet as dp
from extract_training_data import parse_esd

GT = os.path.join(ROOT, 'ground_truth', 'MB1000_M13_DT_Cp312_MD1')
SEP = os.path.join(ROOT, 'cache_sep')
W = 15
LABELS = 'ACGT'
CUTS8 = (0.05, 0.15, 0.35, 0.50, 0.65, 0.80, 0.90)
NFRAME = 9647


def region_of(sc):
    f = sc / NFRAME
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
stat = {r: [0, 0] for r in range(8)}        # correct/matched (per-band kept)
bg = {r: [0, 0] for r in range(8)}          # candidates w/ no esd within 6
for well in wells:
    sep = np.load(os.path.join(SEP, well + '.npy'))
    pos, _, _ = dp.dll_peaks(sep, env_floor_frac=None, region_window=False,
                             region=None)
    pos = np.array([int(p) for p in pos])
    E = parse_esd(os.path.join(GT, well + '.esd'))
    pp = np.array([int(p) for p in E['peak_positions']])
    seq = np.array([b for b in E['sequence']])
    # keep only candidates that lie INSIDE the true-signal region:
    # [first_esd - 150, last_esd + 150]  (mirrors the ML region model)
    s0, s1 = pp[0] - 150, pp[-1] + 150
    inside = (pos >= s0) & (pos <= s1)
    pos = pos[inside]
    if len(pos) < 30:
        continue
    X = np.array([window(sep, int(s)) for s in pos])
    P = np.zeros((len(pos), 5))
    regs = np.array([region_of(s) for s in pos])
    for r in range(8):
        sel = regs == r
        if sel.sum():
            P[sel] = v6[r].predict(zscore(X[sel]), batch_size=256, verbose=0)
    pred = P[:, :4].argmax(1)
    pmax = P[:, :4].max(1)
    for i, p in enumerate(pos):
        d = np.abs(pp - p)
        j = int(np.argmin(d))
        r = regs[i]
        if d[j] > 6:
            bg[r][1] += 1          # candidate with no esd band nearby
            if pmax[i] < 0.5:
                bg[r][0] += 1
            continue
        if seq[j] not in 'ACGT':
            bg[r][1] += 1
            continue
        stat[r][1] += 1
        if LABELS[pred[i]] == seq[j]:
            stat[r][0] += 1
print(f'wells={len(wells)}  (candidates kept only inside true-signal '''
      f'region [{s0}-{s1}]-style)')
print('region  matched  agree%   no-esd-bg')
for r in range(8):
    if stat[r][1]:
        noesd = bg[r][1]
        print(f'  r{r}: {stat[r][1]:5d}  {100*stat[r][0]/stat[r][1]:5.1f}%   {noesd}')