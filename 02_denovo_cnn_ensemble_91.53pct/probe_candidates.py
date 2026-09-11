#!/usr/bin/env python3
"""Compare candidate sets vs esd peaks per region for A01.

Q: our r2-r5 agreement (~70-82%) vs GUI_V15 reaching ~100% for A01 with
some settings.  Hypothesis: it's the DETECTOR, not the CNN.  If dll_peaks
over-detects within r2-r5 (multiple candidates per real band), the extra
candidates are mislabeled by the CNN (2nd-best dye peak of homopolymer, side
lobe) dragging agreement down, whereas GUI/perfect_basecaller walker makes
exactly one candidate per band at the right place -> 100%."""
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


well = 'A01'
sep = np.load(os.path.join(SEP, well + '.npy'))
E = parse_esd(os.path.join(GT, well + '.esd'))
pp = np.array([int(p) for p in E['peak_positions']])
seq = np.array([b for b in E['sequence']])
n = len(sep)

# ---- detector 1: dll_peaks
for rgn_name, region in [('full', None), ('mid', (3350, 7750))]:
    pos, _, _ = dp.dll_peaks(sep, env_floor_frac=None, region_window=False,
                             region=region)
    print(f'\ndll_peaks region={rgn_name}: {len(pos)} candidates')

# ---- detector 2: walker2-like local maxima (candidate_peaks)
sys.path.insert(0, HERE)
try:
    import walker2
    ch, env = walker2.preprocess(sep, smooth=5)
    bgn, end = walker2.read_extent(env)
    scans = walker2.candidate_peaks(env, min_distance=5.0, prominence_frac=0.2)
    scans = scans[(scans >= bgn) & (scans <= end)]
    print(f'\nwalker2 candidate_peaks: {len(scans)} peaks (bgn={bgn} end={end})')
except Exception as e:
    print('walker2 import failed:', e)
    scans = None

# match analysis for dll_peaks full set: for each esd peak count how many
# candidates within +-6
pos, _, _ = dp.dll_peaks(sep, env_floor_frac=None, region_window=False,
                         region=None)
u = np.unique(np.searchsorted(pos, pp, side='right') - np.searchsorted(pos, pp, side='left'))
multi = (u > 1).sum()
empty = (u == 0).sum()
single = (u == 1).sum()
print(f'\nesd peaks={len(pp)}  dll candidates={len(pos)}')
print(f'  esd peaks w/ 0 cand in +-6: {empty}, 1 cand: {single}, >=2 cand: {multi}')

# count per region: candidates vs esd peaks
for r in range(8):
    fr0, fr1 = (0.0 if r == 0 else CUTS8[r - 1]), (CUTS8[r] if r < 7 else 1.0)
    s0, s1 = int(fr0 * n), int(fr1 * n)
    np_r = np.sum((pp >= s0) & (pp < s1))
    nc_r = np.sum((pos >= s0) & (pos < s1))
    print(f'  r{r} [{fr0:.2f}-{fr1:.2f}] esd={np_r:3d} dll_cand={nc_r:3d} '
          f'ratio={nc_r/max(1,np_r):.2f}')