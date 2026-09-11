#!/usr/bin/env python3
"""Diagnose A01 r2-r4 failures in detail.  For each candidate in regions
framed by scan, compare v6 label to esd base + show if the CNN-discriminated
5-class output, or partial window overlap, is the cause.

Also tests: for each esd peak what does the v6 CNN predict at the ESD
peak position (ground-truth centered) vs our candidate position.  If the two
disagree, the DETECTOR is off (candidate not centered on the true peak)."""
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
well = 'A01'
sep = np.load(os.path.join(SEP, well + '.npy'))
E = parse_esd(os.path.join(GT, well + '.esd'))
pp = np.array([int(p) for p in E['peak_positions']])
seq = np.array([b for b in E['sequence']])
n = len(sep)

pos, _, _ = dp.dll_peaks(sep, env_floor_frac=None, region_window=False,
                         region=None)
pos = np.array([int(p) for p in pos])

# esd-position-centered prediction (the 100% baseline)
fcn = np.zeros((len(pp), 5))
Xe = np.array([window(sep, int(s)) for s in pp])
for r in range(8):
    sel = np.array([region_of(s) == r for s in pp])
    if sel.sum():
        fcn[sel] = v6[r].predict(zscore(Xe[sel]), batch_size=256, verbose=0)
pred_e = fcn[:, :4].argmax(1)
match_e = (pred_e == np.array([ 'ACGT'.index(b) if b in 'ACGT' else -1 for b in seq]))
acc_e = np.array([region_of(s) for s in pp])
for r in range(8):
    sel = acc_e == r
    if sel.sum():
        print(f'ESD-pos r{r}: {sel.sum():4d} acc={match_e[sel].mean()*100:5.1f}%')

# per-esd-peak: candidate predicted vs esd predicted
cand_match = np.zeros(len(pp), int)   # 0=none,1=both agree,2=only esd,3=only cand
for j, p in enumerate(pp):
    m = np.flatnonzero(np.abs(pos - p) <= 6)
    if len(m) == 0:
        cand_match[j] = 0
        continue
    i = m[np.argmin(np.abs(pos[m] - p))]
    X1 = window(sep, int(pos[i]))[None]
    r = region_of(p)
    P1 = v6[r].predict(zscore(X1), batch_size=1, verbose=0)[0]
    c1 = P1[:4].argmax()
    e1 = pred_e[j]
    if seq[j] not in 'ACGT':
        cand_match[j] = 0
        continue
    okc = c1 == 'ACGT'.index(seq[j])
    oke = e1 == 'ACGT'.index(seq[j])
    cand_match[j] = (1 if okc else 0) + (2 if oke else 0)

print('\ncand/esd match per esd peak (1=cand ok, 2=esd-pos ok, 3=both):')
for r in range(8):
    sel = acc_e == r
    if sel.sum() == 0:
        continue
    cm = cand_match[sel]
    both = (cm == 3).sum(); none = (cm == 0).sum(); eo = (cm == 2).sum()
    print(f'  r{r}: both={both:4d} esd-only={eo:4d} none={none:4d} '
          f'total={sel.sum():4d}')