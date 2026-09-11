#!/usr/bin/env python3
"""extract_v5.py - portable "book" of DLL peak windows + mobility features.

Per well: every DLL/ESD base call (start -> tail-tail) becomes one row with
  - ADAPTIVE window: +/- 1.5*fwhm scans around the DLL peak, resampled to 31
    scans x 4 channels, per-window z-scored  (fix 3)
  - mobility context features (fix 1): fwhm_norm, spacing_norm, scan_frac
  - label: the ESD base call at that peak (raw trace, no coordinates)
  - side-car: v4 M13-gold reference (refpos0 + M13/construct base) where the
    row exists in v4_round3.npz - used only for *evaluation*, never as features.

Feature design has NO region split, NO plate reference, NO M13 input.
"""
import os, sys
import numpy as np

HERE = os.path.dirname(os.path.realpath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, ROOT)
os.environ.setdefault('TF_CPP_MIN_LOG_LEVEL', '3')

import extract_v3 as ex
from extract_training_data import parse_rsd, parse_esd

WIN = 31
MAX_HALF = 48
MIN_HALF = 8
BASES = 'ACGT'


def region_of(frac, cuts=(0.15, 0.65, 0.90)):
    if frac < cuts[0]:
        return 0
    if frac < cuts[1]:
        return 1
    if frac < cuts[2]:
        return 2
    return 3


def adaptive_window(ch, sc, fwhm):
    half = int(round(1.5 * fwhm))
    half = max(MIN_HALF, min(MAX_HALF, half))
    n = len(ch)
    lo, hi = sc - half, sc + half + 1
    sl, sh = int(np.clip(lo, 0, n - 1)), int(np.clip(hi, lo + 1, n))
    seg = ch[sl:sh]
    if lo < 0:
        seg = np.pad(seg, ((-lo, 0), (0, 0)), mode='edge')
    if hi > n:
        seg = np.pad(seg, ((0, hi - n), (0, 0)), mode='edge')
    if len(seg) < 2:
        seg = np.pad(seg, ((0, 2 - len(seg)), (0, 0)), mode='edge')
    grid = np.linspace(0, len(seg) - 1, WIN)
    out = np.empty((WIN, ch.shape[1]), dtype=np.float32)
    for c in range(ch.shape[1]):
        out[:, c] = np.interp(grid, np.arange(len(seg)), seg[:, c])
    mu = out.mean(); sd = out.std() + 1e-8
    return ((out - mu) / sd).astype(np.float32)


def nearest_fwhm(esd, sc):
    bpos = esd['bases_positions'].astype(np.int64)
    fw = esd['fwhm_values']
    d = np.abs(bpos - sc)
    j = int(np.argmin(d))
    if d[j] > 6:
        return float(np.median(fw))
    return float(fw[j])


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', default='v5_book.npz')
    ap.add_argument('--wells', default=None)
    args = ap.parse_args()

    v4 = np.load(os.path.join(HERE, 'v4_round3.npz'), allow_pickle=True)
    x4key = {}
    for w in np.unique(v4['well']):
        m = v4['well'] == w
        x4key[w] = {int(e): (int(rp), BASES[int(yv)])
                    for e, rp, yv in zip(v4['esd_idx'][m], v4['refpos0'][m], v4['y'][m])
                    if int(e) >= 0}
    print('v4 side-car ready')

    wells = sorted(f[:-4] for f in os.listdir(ex.PLATE) if f.endswith('.rsd'))
    if args.wells:
        wells = [w.strip() for w in args.wells.split(',') if w.strip()]
    print(f'building book for {len(wells)} wells')

    rows = []
    for well in wells:
        ch = parse_rsd(os.path.join(ex.PLATE, well + '.rsd'))[ex.CH_NAMES].values.astype(np.float64)
        esd = parse_esd(os.path.join(ex.GT, well + '.esd'))
        seq = esd['sequence']
        ed = np.array([i for i in range(len(seq)) if seq[i] in BASES])
        pp = esd['peak_positions'].astype(np.int64)
        n = len(ed)
        if len(pp) < n:
            print(f'  {well}: skip'); continue
        spk = np.zeros(n, dtype=np.float64)
        fwk = np.zeros(n, dtype=np.float64)
        for k in range(n):
            sc = int(pp[k])
            s_prev = (sc - int(pp[k - 1])) if k > 0 else 0.0
            s_next = (int(pp[k + 1]) - sc) if k < n - 1 else 0.0
            s = (s_prev + s_next) / 2.0 if (s_prev > 0 and s_next > 0) else max(s_prev, s_next)
            spk[k] = float(np.clip(s if s > 0 else 10.0, 2.0, 30.0))
            fwk[k] = nearest_fwhm(esd, sc)
        med_fw = float(np.median(fwk))
        med_sp = float(np.median(spk[n // 3: 2 * n // 3])) if n > 9 else float(np.median(spk))
        if med_sp <= 0 or med_fw <= 0:
            print(f'  {well}: skip (degenerate)'); continue
        x4w = x4key.get(well, {})
        for k in range(n):
            sc = int(pp[k])
            if not (200 < sc < len(ch) - 200):
                continue
            Xw = adaptive_window(ch, sc, fwk[k])
            fh = float(np.clip(fwk[k] / med_fw, 0.5, 4.0))
            sp = float(np.clip(spk[k] / med_sp, 0.5, 4.0))
            frac = k / max(1, n - 1)
            g = x4w.get(k)
            rows.append((
                well, sc, k, region_of(frac),
                fh, sp, frac, Xw,
                BASES.index(seq[ed[k]]),
                BASES.index(g[1]) if g else -1,
                g[0] if g else -1,
                fwk[k], spk[k],
            ))
    print(f'windows: {len(rows)}')

    np.savez_compressed(
        args.out,
        X=np.stack([r[7] for r in rows]).astype(np.float32),
        aux=np.array([[r[4], r[5], r[6]] for r in rows], dtype=np.float32),
        y_esd=np.array([r[8] for r in rows], dtype=np.int8),
        y_ref=np.array([r[9] for r in rows], dtype=np.int16),
        refpos0=np.array([r[10] for r in rows], dtype=np.int32),
        region=np.array([r[3] for r in rows], dtype=np.uint8),
        scan=np.array([r[1] for r in rows], dtype=np.int32),
        esd_idx=np.array([r[2] for r in rows], dtype=np.int32),
        fwhm=np.array([r[11] for r in rows], dtype=np.float32),
        spacing=np.array([r[12] for r in rows], dtype=np.float32),
        well=np.array([r[0] for r in rows], dtype=object),
    )
    print(f'saved {args.out}: {len(rows)} windows over {len(wells)} wells')


if __name__ == '__main__':
    main()