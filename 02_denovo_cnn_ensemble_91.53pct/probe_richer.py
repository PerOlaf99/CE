#!/usr/bin/env python3
"""Test: does keeping 1 candidate per esd band (strongest) fix r2-r5?
The 70-82% agreement may be inflated-false because dll_peaks over-detects
(2 candidates in many r2 bands + 239 candidates in r0-r1 which have NO esd
peaks at all).  Only rich candidate -> CNN might recover what GUI_V15's
tuned settings reached."""
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
CUT = 6


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
# A01-only per-region detail (GUI reached high on A01)
for well in wells:
    sep = np.load(os.path.join(SEP, well + '.npy'))
    env = dp.env_max(sep)
    pos, _, inten = dp.dll_peaks(sep, env_floor_frac=None, region_window=False,
                                 region=None)
    pos = np.array([int(p) for p in pos])
    E = parse_esd(os.path.join(GT, well + '.esd'))
    pp = np.array([int(p) for p in E['peak_positions']])
    seq = np.array([b for b in E['sequence']])
    fr = np.arange(len(pos), dtype=float) / max(1, len(pos) - 1)
    regs = np.array([region_of(f) for f in fr])
    score = P = None

    # greedy: each esd peak keeps its strongest candidate within CUT
    keep = np.zeros(len(pos), bool)
    for j, p in enumerate(pp):
        m = np.flatnonzero(np.abs(pos - p) <= CUT)
        if len(m) == 0:
            continue
        keep[m[np.argmax([inten[i] for i in m])]] = True
    ks = np.flatnonzero(keep)
    ok = 0
    for i in ks:
        j = int(np.argmin(np.abs(pp - pos[i])))
        if seq[j] in 'ACGT':
            ok += 0  # count later; we need CNN labels
    print(f'{well}: esd={len(pp)} cand={len(pos)} 1-per-band={len(ks)} '
          f'(kept {len(ks)/max(1,len(pp)):.2f}/esd)')