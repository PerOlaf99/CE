#!/usr/bin/env python3
"""build_mixed8.py - build fine-8-region cal set + raw+cal stacked 8-channel set
from cal_training.npz (windows already centered on esd peaks, esd labels)."""
import os, sys, numpy as np
sys.path.insert(0, '.')
sys.path.insert(0, '/media/per/78B0C7DE1FA7081C/electropherogram/sanger_toolkit')
from extract_training_data import parse_rsd
ROOT = '/media/per/78B0C7DE1FA7081C/electropherogram'
CH = ['Channel1', 'Channel2', 'Channel3', 'Channel4']
W = 15
CUTS8 = [0.05, 0.15, 0.35, 0.50, 0.65, 0.80, 0.90]

def region_of(f, cuts):
    r = 0
    for c in cuts:
        if f >= c: r += 1
        else: break
    return r

def window(ch, s, w=W):
    n = len(ch); lo, hi = s-w, s+w+1
    win = ch[max(0, lo):min(n, hi)]
    if lo < 0 or hi > n:
        win = np.pad(win, ((max(0,-lo), max(0,hi-n)), (0,0)), mode='edge')
    return win.astype(np.float32)

d = np.load('cal_training.npz', allow_pickle=True)
well = np.array([w.decode() if isinstance(w, bytes) else w for w in d['well']])
scan = d['scan'].astype(np.int64)
y = d['y'].astype(int); split = d['split'].astype(bool)

raw_cache = {}
raw_win = np.empty((len(well), 2*W+1, 4), np.float32)  # per-row buffer
Xcal = d['X']
region8 = np.empty(len(well), np.uint8)
for k, wname in enumerate(sorted(set(well))):
    m = wname == well
    if wname not in raw_cache:
        raw_cache[wname] = parse_rsd(os.path.join(ROOT, 'MB1000_M13_DT', wname + '.rsd'))[CH].values.astype(np.float64)
    raw = raw_cache[wname]
    pp = scan[m]
    fr_idx = np.argsort(pp)
    n = len(pp)
    fr = np.empty(n, float)
    fr[fr_idx] = np.arange(n, dtype=float) / max(1, n-1)
    region8[m] = np.array([region_of(f, CUTS8) for f in fr], np.uint8)
    raw_win[m] = np.array([window(raw, int(s)) for s in pp])

Xmixed = np.concatenate([raw_win[:, :, :4], Xcal], axis=2)
negw = np.array([w.decode() if isinstance(w, bytes) else w for w in d['negw']])
negs = d['negs'].astype(np.int64)
negRaw = np.empty((len(negw), 2*W+1, 4), np.float32)
for k, wname in enumerate(sorted(set(negw))):
    m = negw == wname
    if wname not in raw_cache:
        raw_cache[wname] = parse_rsd(os.path.join(ROOT, 'MB1000_M13_DT', wname + '.rsd'))[CH].values.astype(np.float64)
    raw = raw_cache[wname]
    negRaw[m] = np.array([window(raw, int(s)) for s in negs[m]])
negX8 = np.concatenate([negRaw, np.asarray(d['negX'], np.float32)], axis=2)
np.savez_compressed('mixed8.npz', X=Xmixed, y=y, region=region8, split=split,
                    well=well, scan=scan,
                    negX=negX8, negy=d['negy'], negr=d['negr'])
np.savez_compressed('cal8.npz', X=Xcal, y=y, region=region8, split=split,
                    well=well, scan=scan,
                    negX=d['negX'], negy=d['negy'], negr=d['negr'])
print('built mixed8.npz C=8  cal8.npz region8 bins=%d' % len(np.unique(region8)))
print('region8 counts', np.bincount(region8, minlength=8))
