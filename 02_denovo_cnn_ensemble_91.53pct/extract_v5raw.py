#!/usr/bin/env python3
"""extract_v5raw.py - v5 book with velocity features measured from RAW data.

Fixes to extract_v5.py:
  * spacing   : measured from RAW peak cadence (baseline-corrected max-comb
                peak detector), NOT the Cimarron ESD peak positions.
  * fwhm      : measured on the RAW trace at each DLL peak (half-max width in
                the dominant channel), NOT esd['fwhm_values'].
  * current   : added feature (12-row aux) - the run current at each peak.
  * window    : adaptive +/-1.5*RAW fwhm, resampled to 31x4.

Labels stay ESD bases (extract_v5 convention).  All geometry/velocity
quantities are RAW-derived.  No region split, no M13 features.
"""
import os, sys
import numpy as np
from scipy.ndimage import minimum_filter1d, uniform_filter1d
from scipy.signal import find_peaks

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
CH_NAMES = ex.CH_NAMES
PLATE = ex.PLATE
GT = ex.GT


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


def raw_velocity(ch_raw):
    """Return (fwhm_func, spacing_func, current_func) closures computed from
    the RAW baseline-corrected signal + peak cadence."""
    base = minimum_filter1d(ch_raw, size=401, mode='nearest')
    c = np.clip(ch_raw - base, 0, None)
    comb = uniform_filter1d(c.max(axis=1), size=2)
    pk, _ = find_peaks(comb, distance=3, prominence=comb.max() * 0.03)
    scans = pk.astype(float)
    spacing = np.diff(scans, append=scans[-1])
    sp_prof = uniform_filter1d(
        np.interp(np.arange(len(ch_raw)), scans, spacing,
                  left=spacing[0], right=spacing[-1]),
        size=81, mode='nearest')
    # fwhm per raw peak (half-max width on dominant channel, bounded by neighbors)
    fw_raw = np.full(len(pk), np.nan)
    for i, sc in enumerate(pk):
        sl = pk[max(0, i - 1)]
        sr = pk[min(len(pk) - 1, i + 1)]
        dom = int(np.argmax(c[sc]))
        lo, hi = max(0, (sl + sc) // 2), min(len(c) - 1, (sc + sr) // 2)
        if hi - lo < 2:
            continue
        seg = c[lo:hi + 1, dom]
        pkm = c[sc, dom]
        if pkm <= 0:
            continue
        ab = np.where(seg >= pkm / 2)[0]
        if len(ab) == 0:
            continue
        fw_raw[i] = ab.max() - ab.min() + 1
    fw_prof = np.interp(np.arange(len(ch_raw)), scans,
                        np.where(np.isfinite(fw_raw), fw_raw, np.nanmedian(fw_raw)),
                        left=np.nanmedian(fw_raw), right=np.nanmedian(fw_raw))
    fw_prof = uniform_filter1d(fw_prof, size=21, mode='nearest')

    def f_fwhm(sc):
        return float(np.clip(fw_prof[min(max(int(sc), 0), len(fw_prof) - 1)], 2.0, 40.0))

    def f_spacing(sc):
        return float(np.clip(sp_prof[min(max(int(sc), 0), len(sp_prof) - 1)], 2.0, 40.0))

    def f_current(sc, cur_arr):
        return float(cur_arr[min(max(int(sc), 0), len(cur_arr) - 1)])

    return f_fwhm, f_spacing, f_current


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', default='v5raw_book.npz')
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

    wells = sorted(f[:-4] for f in os.listdir(PLATE) if f.endswith('.rsd'))
    if args.wells:
        wells = [w.strip() for w in args.wells.split(',') if w.strip()]

    rows = []
    for well in wells:
        df = parse_rsd(os.path.join(PLATE, well + '.rsd'))
        ch = df[CH_NAMES].values.astype(np.float64)
        cur = df['Current'].values.astype(np.float64)
        esd = parse_esd(os.path.join(GT, well + '.esd'))
        seq = esd['sequence']
        ed = np.array([i for i in range(len(seq)) if seq[i] in BASES])
        pp = esd['peak_positions'].astype(np.int64)
        n = len(ed)
        if len(pp) < n:
            print(f'  {well}: skip'); continue
        f_fwhm, f_spacing, f_cur = raw_velocity(ch)
        fw_vals = np.array([f_fwhm(int(pp[k])) for k in range(n)])
        sp_vals = np.array([f_spacing(int(pp[k])) for k in range(n)])
        med_fw = float(np.median(fw_vals))
        med_sp = float(np.median(sp_vals))
        if med_fw <= 0 or med_sp <= 0:
            print(f'  {well}: skip (degenerate)'); continue
        x4w = x4key.get(well, {})
        for k in range(n):
            sc = int(pp[k])
            if not (200 < sc < len(ch) - 200):
                continue
            Xw = adaptive_window(ch, sc, fw_vals[k])
            fh = float(np.clip(fw_vals[k] / med_fw, 0.5, 4.0))
            sp = float(np.clip(sp_vals[k] / med_sp, 0.5, 4.0))
            cu0 = f_cur(sc, cur)
            cu = float(np.clip(cu0 / 60.0, 0.5, 1.5))
            frac = k / max(1, n - 1)
            g = x4w.get(k)
            rows.append((
                well, sc, k, (0.15 if frac < 0.15 else (1 if frac < 0.65 else (2 if frac < 0.90 else 3))),
                fh, sp, frac, cu, Xw,
                BASES.index(seq[ed[k]]),
                BASES.index(g[1]) if g else -1,
                g[0] if g else -1,
                fw_vals[k], sp_vals[k],
            ))
    print(f'windows: {len(rows)}')

    np.savez_compressed(
        args.out,
        X=np.stack([r[8] for r in rows]).astype(np.float32),
        aux=np.array([[r[4], r[5], r[6], r[7]] for r in rows], dtype=np.float32),
        y_esd=np.array([r[9] for r in rows], dtype=np.int8),
        y_ref=np.array([r[10] for r in rows], dtype=np.int16),
        refpos0=np.array([r[11] for r in rows], dtype=np.int32),
        region=np.array([r[3] for r in rows], dtype=np.uint8),
        scan=np.array([r[1] for r in rows], dtype=np.int32),
        esd_idx=np.array([r[2] for r in rows], dtype=np.int32),
        fwhm=np.array([r[12] for r in rows], dtype=np.float32),
        spacing=np.array([r[13] for r in rows], dtype=np.float32),
        well=np.array([r[0] for r in rows], dtype=object),
    )
    print(f'saved {args.out}: {len(rows)} windows over {len(wells)} wells')


if __name__ == '__main__':
    main()