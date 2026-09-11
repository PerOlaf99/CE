#!/usr/bin/env python3
"""extract_cal.py - build calibrated-lane training set for the v5 CNN.

Center each window on the DLL's OWN called peak positions (esd peak_positions),
take the window from the DSP-calibrated lanes (cache_sep: matrix color-
separated + mobility-shifted), and label each with the esd base letter
(= the DLL's call; equals the construct base, mutation-aware).  Region split
begin/mid/tail/tail-tail by rank fraction, same train/test WELL split as
v3_training.npz.  Background windows (label 4) sampled from quiet regions of
the calibrated lanes.

This is 'train the ML to reproduce Cimarron's output on the same signal the
Cimarron reader consumes' -- positions AND signal come from the DSP layer,
labels from esd/M13.
"""
import os, sys, numpy as np

HERE = os.path.dirname(os.path.realpath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'sanger_toolkit'))

from extract_training_data import parse_esd

GT = os.path.join(ROOT, 'ground_truth', 'MB1000_M13_DT_Cp312_MD1')
SEP = os.path.join(ROOT, 'cache_sep')
WINDOW = 15
NEG_FRAC = 0.12
NEG_PER_WELL_CAP = 60
REGION_CUTS = (0.15, 0.65, 0.90)
BASE_MAP = {'A': 0, 'C': 1, 'G': 2, 'T': 3}


def region_of(frac):
    if frac < REGION_CUTS[0]:
        return 0
    if frac < REGION_CUTS[1]:
        return 1
    if frac < REGION_CUTS[2]:
        return 2
    return 3


def make_window(lanes, s, w=WINDOW):
    n = len(lanes)
    lo, hi = s - w, s + w + 1
    win = lanes[max(0, lo):min(n, hi)]
    if lo < 0 or hi > n:
        win = np.pad(win, ((max(0, -lo), max(0, hi - n)), (0, 0)), mode='edge')
    return win.astype(np.float32)


def well_peaks(sep, esd):
    pp = np.array([int(p) for p in esd['peak_positions']])
    seq = np.asarray(list(esd['sequence']))
    ok = (pp >= 20) & (pp < len(sep) - 20) & np.isin(seq, list(BASE_MAP))
    return pp[ok], seq[ok]


def gen_negatives(tr_wells, allpix, rng):
    nX, ny, nr, nw, ns = [], [], [], [], []
    for well in tr_wells:
        sep = np.load(os.path.join(SEP, well + '.npy'))
        pk = allpix[well]
        if len(pk) < 4 or len(sep) < 400:
            continue
        med = np.median(np.diff(pk)) if len(pk) > 3 else 10.0
        mids = [int((a + b) // 2) for a, b in zip(pk[:-1], pk[1:])
                if b - a >= 1.3 * med]
        far = [int(s) for s in rng.integers(300, len(sep) - 300,
                                            size=NEG_PER_WELL_CAP)
               if np.min(np.abs(pk - s)) > 2 * WINDOW]
        picks = (mids + list(far))[:NEG_PER_WELL_CAP]
        if not picks:
            continue
        wlo, whi = int(pk[0]), int(pk[-1])
        for s in picks:
            nX.append(make_window(sep, s))
            ny.append(4)
            fr = (s - wlo) / max(1, whi - wlo)
            nr.append(region_of(fr))
            nw.append(well)
            ns.append(int(s))
    return (np.array(nX, np.float32), np.array(ny, np.int64),
            np.array(nr, np.uint8), np.array(nw, object), np.array(ns, np.int64))


def main():
    old = np.load(os.path.join(HERE, 'v3_training.npz'), allow_pickle=True)
    old_well = np.array([w.decode() if isinstance(w, bytes) else w
                         for w in old['well']])
    tr_wells = sorted({w for w, s in zip(old_well, old['split']) if s})
    te_wells = sorted({w for w, s in zip(old_well, old['split']) if not s})
    wells = sorted(tr_wells + te_wells)
    is_train = {w: (w in tr_wells) for w in wells}

    X, y, region, split, well, scan = [], [], [], [], [], []
    allpix = {}
    for k, wname in enumerate(wells):
        esd = parse_esd(os.path.join(GT, wname + '.esd'))
        sep = np.load(os.path.join(SEP, wname + '.npy'))
        if not hasattr(esd, 'get') or 'sequence' not in esd:
            print(f'{wname}: skip (no esd)'); continue
        pp, seq = well_peaks(sep, esd)
        if len(pp) < 50:
            print(f'{wname}: skip (peaks {len(pp)})'); continue
        allpix[wname] = pp
        fr = np.arange(len(pp), dtype=float) / max(1, len(pp) - 1)
        for i, s in enumerate(pp):
            X.append(make_window(sep, int(s)))
            y.append(BASE_MAP[seq[i]])
            region.append(region_of(fr[i]))
            split.append(not is_train[wname])
            well.append(wname)
            scan.append(int(s))
        if (k + 1) % 12 == 0:
            print(f'{k + 1}/{len(wells)} wells ...')

    X = np.array(X, np.float32)
    y = np.array(y, np.int64)
    region = np.array(region, np.uint8)
    split = np.array(split, bool)
    well = np.array(well, object)
    scan = np.array(scan, np.int64)

    rng = np.random.default_rng(0)
    nX, ny, nr, nw, ns = gen_negatives(tr_wells, allpix, rng)
    print(f'positives {len(y)} (train wells {len(tr_wells)} test {len(te_wells)}) '
          f'bincount {np.bincount(y, minlength=5)}')
    print(f'negatives {len(ny)} {np.bincount(nr, minlength=4)}')

    np.savez_compressed(os.path.join(HERE, 'cal_training.npz'),
                        X=X, y=y, region=region, split=split,
                        well=well, scan=scan,
                        negX=nX, negy=ny, negr=nr, negw=nw, negs=ns)
    print('saved cal_training.npz')


if __name__ == '__main__':
    main()