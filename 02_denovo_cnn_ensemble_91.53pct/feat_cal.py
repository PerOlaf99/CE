#!/usr/bin/env python3
"""feat_cal.py - append per-band BandStat features to cal_training.npz ->
cal_feat.npz.  Feature rows aligned 1:1 with d['X'] (same esd peak positions).
"""
import os, sys, numpy as np
sys.path.insert(0, '.')
sys.path.insert(0, '/media/per/78B0C7DE1FA7081C/electropherogram/sanger_toolkit')
import bandstat as bs

SEP = '/media/per/78B0C7DE1FA7081C/electropherogram/cache_sep'
d = np.load('cal_training.npz', allow_pickle=True)
well = np.array([w.decode() if isinstance(w, bytes) else w for w in d['well']])
scan = d['scan'].astype(np.int64)
n = len(well)
feat = np.zeros((n, 6), np.float32)
byn = {}
for wname in sorted(set(well)):
    byn[wname] = np.load(os.path.join(SEP, wname + '.npy'))
for k, wname in enumerate(sorted(set(well))):
    m = well == wname
    lanes = byn[wname]
    ff = bs.band_features(lanes, scan[m])
    feat[m] = ff
    if (k + 1) % 12 == 0:
        print(k + 1, 'wells')
negw = np.array([x.decode() if isinstance(x, bytes) else x for x in d['negw']])
negs = d['negs'].astype(np.int64)
negfeat = np.zeros((len(negw), 6), np.float32)
for k, wname in enumerate(sorted(set(negw))):
    m = negw == wname
    lanes = byn[wname]
    ff = bs.band_features(lanes, negs[m])
    negfeat[m] = ff
np.savez_compressed('cal_feat.npz', X=d['X'], y=d['y'], region=d['region'],
                    split=d['split'], well=d['well'], scan=d['scan'],
                    feat=feat, negX=d['negX'], negy=d['negy'], negr=d['negr'],
                    negfeat=negfeat)
print('saved cal_feat.npz feat', feat.shape, 'range', feat.min(0), feat.max(0))
