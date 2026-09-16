#!/usr/bin/env python3
"""build_cal_set.py - regenerate the calibrated (separated) 4-dye lanes and a
training set identical to v3_training.npz except feature windows come from
the DSP color-whitened lanes instead of the raw channels.

cache_sep used by the older v6_cal8 / v9 work is gone, so this rebuilds:
  ROOT/cache_sep/{well}.npy         separated lanes (n,4) float64
  cal_training.npz                   same y/region/split/scans as v3 but X=sep

The separated lanes are de-novo (settingsV10 crosstalk matrix applied to our
own baseline-corrected/smoothed trace), identical to perfect_basecaller's
`eng.separated`.
"""
import os, sys
import numpy as np

HERE = os.path.dirname(os.path.realpath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, ROOT)
os.environ.setdefault('TF_CPP_MIN_LOG_LEVEL', '3')

import extract_v3 as ex
import walker2 as w2

SEP_DIR = os.path.join(ROOT, 'cache_sep')


def build_lanes():
    d = np.load(os.path.join(HERE, 'v3_training.npz'), allow_pickle=True)
    wells = sorted({w for w in d['well']})
    os.makedirs(SEP_DIR, exist_ok=True)
    made = 0
    for i, well in enumerate(wells, 1):
        p = os.path.join(SEP_DIR, well + '.npy')
        if os.path.exists(p):
            continue
        sep, _ = w2.sep_lanes(well)
        np.save(p, sep)
        made += 1
        print(f'{well} sep saved ({i}/{len(wells)})', flush=True)
    print(f'done: {made} wells regenerated into {SEP_DIR}')
    return wells


def build_set(wells):
    d = np.load(os.path.join(HERE, 'v3_training.npz'), allow_pickle=True)
    X = np.zeros_like(np.asarray(d['X'], dtype=np.float32))
    scan = np.asarray(d['scan']).astype(int)
    wells_arr = np.asarray(d['well'])
    uniq = sorted(set(wells_arr))
    for well in uniq:
        sep = np.load(os.path.join(SEP_DIR, well + '.npy'))
        idx = np.where(wells_arr == well)[0]
        for k in idx:
            s = int(scan[k])
            X[k] = ex.make_window(sep, s)
    out = dict(d)
    out['X'] = X
    np.savez_compressed(os.path.join(HERE, 'cal_training.npz'), **out)
    print(f'saved cal_training.npz (X from separated lanes, n={len(X)})')
    # sanity: compare a window
    k = 0
    print('sample raw window', np.asarray(d['X'])[k][14, :2])
    print('sample cal window', X[k][14, :2])


if __name__ == '__main__':
    wells = build_lanes()
    build_set(wells)