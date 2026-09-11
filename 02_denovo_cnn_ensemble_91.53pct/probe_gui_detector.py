#!/usr/bin/env python3
"""Compare dll_peaks vs GUI greedy detector candidate positions vs ESD peaks
vs theirs agreement, per region, for A01.  Goal: is the 82%-r2-r4 discrepancy
because dll_peaks candidates are off-center for the CNN vs greedy detector?"""
import os, sys, json
import numpy as np
os.environ.setdefault('TF_CPP_MIN_LOG_LEVEL', '3')
HERE = os.path.dirname(os.path.realpath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE); sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'sanger_toolkit'))
os.path.dirname  # noqa break recursion
import dll_peakdet as dp
import tensorflow as tf
from extract_training_data import parse_esd
from basecall import pc_call_bases, greedy
# test import of the greedy detector path used by the GUI

SEP = os.path.join(ROOT, 'cache_sep')
GT = os.path.join(ROOT, 'ground_truth', 'MB1000_M13_DT_Cp312_MD1')
CH = ['Channel1', 'Channel2', 'Channel3', 'Channel4']
LABELS = 'ACGT'
CUTS8 = (0.05, 0.15, 0.35, 0.50, 0.65, 0.80, 0.90)


def region_of(sc):
    f = sc / 9647
    r = 0
    for c in CUTS8:
        if f >= c: r += 1
        else: break
    return r


well = 'A01'
sep = np.load(os.path.join(SEP, well + '.npy'))
E = parse_esd(os.path.join(GT, well + '.esd'))
pp = np.array([int(p) for p in E['peak_positions']])
seq = np.array([b for b in E['sequence']])

# Detector 1: dll_peaks
pos1, domseq, inten = dp.dll_peaks(sep, env_floor_frac=None,
                                   region_window=False, region=None)
pos1 = np.array([int(p) for p in pos1])

# Detector 2: greedy detector used by GUI (per-channel prominence on sep)
print('greedy/pc_call_bases signatures available:', bool('pc_call_bases'))

# Try both basecalling methods on full scan space with optimal-ish settings
for name, kwargs in [
    ('pc_detect', dict(min_distance=6, prominence_frac=0.02)),
    ('pc_detect_strict', dict(min_distance=5, prominence_frac=0.10)),
]:
    try:
        from basecall import pc_detect_peaks_4ch
        cand = pc_detect_peaks_4ch(sep, **kwargs)
        print(f'{name}: {len(cand)} candidates {kwargs}')
    except Exception as e:
        print(name, 'ERR', e)

# fallback: use greedy from basecall? try import names
import basecall as bc
print('\nbasecall exports:', [n for n in dir(bc) if not n.startswith('_')][:40])