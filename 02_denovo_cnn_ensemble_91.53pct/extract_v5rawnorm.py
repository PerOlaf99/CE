#!/usr/bin/env python3
"""extract_v5rawnorm.py - v5raw book + per-channel gain normalization.

Supplementary to extract_v5raw.py. After baseline correction, EVERY channel is
divided by its own smoothly-varying per-channel 99th-percentile envelope
(running window ~ len/4) computed on the baseline-corrected signal. This makes
the per-channel volt-scale stationary over the CE, counteracting the observed
ch1/ch2 gain decay (->5-13% of dominant by the tail).

Windows/spacing/fwhm/current as in v5raw. Aux features are computed on the
RAW (pre-normalization) signal; only the input image X is gain-normalized.
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
GAIN_WIN_FRAC = 0.25       # envelope window as fraction of trace length
GAIN_PCT = 99.0


def gain_normalize(ch_raw, win=None, pct=99.0, block=512):
    """Divide each channel by its running pct-percentile envelope.

    p99 computed on strided blocks (cheap), then interpolated to a smooth
    per-scan envelope and the channel is divided by it.
    """
    n = len(ch_raw)
    nb = max(4, n // block)
    edges = np.linspace(0, n, nb + 1).astype(int)
    centers = 0.5 * (edges[:-1] + edges[1:])
    env_pts = np.stack([np.percentile(ch_raw[edges[i]:edges[i + 1]], pct, axis=0)
                        for i in range(nb)], axis=0)          # (nb, 4)
    # smooth the block percentile column-wise, edge-clamped
    sp = nb // 4 * 2 + 1
    env_sm = uniform_filter1d(env_pts, size=sp, axis=0, mode='nearest')
    env = np.empty_like(ch_raw)
    scans = np.arange(n, dtype=float)
    for c in range(ch_raw.shape[1]):
        env[:, c] = np.interp(scans, centers, env_sm[:, c],
                              left=env_sm[0, c], right=env_sm[-1, c])
    env = np.maximum(env, 1e-6)
    return ch_raw / env, env


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


def baseline_velocity(ch_raw):
    base = minimum_filter1d(ch_raw, size=401, mode='nearest')
    c = np.clip(ch_raw - base, 0, None)
    comb = uniform_filter1d(c.max(axis=1), size=2)
    pk, _ = find_peaks(comb, distance=3, prominence=comb.max() * 0.03)
    scans = pk.astype(float)
    spacing = np.diff(scans, append=scans[-1])
    sp_prof = uniform_filter1d(
        np.interp(np.arange(len(ch_raw)), scans, spacing,
                  left=spacing[0], right=spacing[-1]), size=81, mode='nearest')

    fw_raw = np.full(len(pk), np.nan)
    for i, sc in enumerate(pk):
        sl = pk[max(0, i - 1)]; sr = pk[min(len(pk) - 1, i + 1)]
        dom = int(np.argmax(c[sc]))
        lo, hi = max(0, (sl + sc) // 2), min(len(c) - 1, (sc + sr) // 2)
        if hi - lo < 2: continue
        seg = c[lo:hi + 1, dom]; pkm = c[sc, dom]
        if pkm <= 0: continue
        ab = np.where(seg >= pkm / 2)[0]
        if len(ab) == 0: continue
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
    ap.add_argument('--out', default='v5rawnorm_book.npz')
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
        ch_raw = df[CH_NAMES].values.astype(np.float64)
        cur = df['Current'].values.astype(np.float64)
        esd = parse_esd(os.path.join(GT, well + '.esd'))
        seq = esd['sequence']
        ed = np.array([i for i in range(len(seq)) if seq[i] in BASES])
        pp = esd['peak_positions'].astype(np.int64)
        n = len(ed)
        if len(pp) < n:
            print(f'  {well}: skip'); continue

        ch_norm, _env = gain_normalize(ch_raw)
        f_fwhm, f_spacing, f_cur = baseline_velocity(ch_raw)
        fw_vals = np.array([f_fwhm(int(pp[k])) for k in range(n)])
        sp_vals = np.array([f_spacing(int(pp[k])) for k in range(n)])
        med_fw = float(np.median(fw_vals)); med_sp = float(np.median(sp_vals))
        if med_fw <= 0 or med_sp <= 0:
            print(f'  {well}: skip (degenerate)'); continue
        x4w = x4key.get(well, {})
        for k in range(n):
            sc = int(pp[k])
            if not (200 < sc < len(ch_norm) - 200):
                continue
            Xw = adaptive_window(ch_norm, sc, fw_vals[k])
            fh = float(np.clip(fw_vals[k] / med_fw, 0.5, 4.0))
            sp = float(np.clip(sp_vals[k] / med_sp, 0.5, 4.0))
            cu = float(np.clip(f_cur(sc, cur) / 60.0, 0.5, 1.5))
            frac = k / max(1, n - 1)
            g = x4w.get(k)
            rows.append((
                well, sc, k,
                (0.15 if frac < 0.15 else (1 if frac < 0.65 else (2 if frac < 0.90 else 3))),
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