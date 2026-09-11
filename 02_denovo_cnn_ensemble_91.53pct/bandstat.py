#!/usr/bin/env python3
"""bandstat.py - per-band statistical features for the CNN side-tower and the
OKN fuzzy gate, faithful to the Cimarron feature bridge (DLL_FUNCTION_MAP
SSB3-DETAIL, Phase C):

  xbnd s2   = FUN_10024e47 position-adaptive ratio (min/v3 or min/sqrt(v3)+1),
              clamp [1,2]
  sb        = cross-channel envelope at the peak (Wvfm::envv(peakpos))
  envAll    = min(left-flank env, right-flank env) near ±2 scans
  width     = dominant-channel width while value > env/2 (FUN_10024f29)
  D         = inter-peak spacing (SWold, actual)
  Y         = fitted-spacing model (FUN_10019280)
  floor     = per-well mean(envAll) clamped to 0.05 (the fuzzy floor)
  T         = 1.24*floor
  D_Y       = D/Y spacing ratio (feeds V/trapezoid in the fuzzy rule)

All computed from the DSP-calibrated lanes (cache_sep); no DLL at inference.
"""
import numpy as np


def xbnd_of(lanes, p):
    """FUN_10024e47: sorted 4 lane values v1>=v2>=v3>=v4."""
    vs = np.sort(lanes[p, :])[::-1]
    C = lanes.shape[1]
    v3 = vs[2] if C >= 3 else 0.0
    mn = vs.min()
    if v3 < 8.9e-16:
        v3 = 2.2e-16
    if mn >= 0.1:
        xb = (mn / v3) if v3 > 0 else 1.0
    else:
        xb = (mn / np.sqrt(v3) + 1.0) if v3 > 0 else 1.0
    return max(1.0, min(2.0, xb))


def peak_width(lane, p, thresh):
    """FUN_10024f29 width in scans while lane > thresh around p."""
    n = len(lane)
    if p >= n:
        return 1
    wl = 0
    while p - 1 - wl >= 0 and lane[p - 1 - wl] > thresh:
        wl += 1
    wr = 0
    while p + 1 + wr < n and lane[p + 1 + wr] > thresh:
        wr += 1
    return wl + wr + 1


def fitted_spacing(positions, spacings):
    """FUN_10019280 faithful: outlier-rejected (z<=1.5) linear spacing-vs-pos,
    fill every band with fitted value, clamp >=1, ints."""
    n = len(spacings)
    sp = np.asarray(spacings, float)
    pos = np.asarray(positions, float)
    Y = np.zeros(n, dtype=np.float64)
    if n < 2:
        return Y
    mu, sd = sp.mean(), sp.std()
    if sd == 0:
        Y[:] = int(mu)
        return Y
    z = np.abs((sp - mu) / sd)
    keep = z <= 1.5
    if keep.sum() >= 2:
        b, a = np.polyfit(pos[keep], sp[keep], 1)
        for i in range(n):
            v = round(a + b * pos[i])
            Y[i] = max(1, int(v))
    return Y


def band_features(lanes, positions):
    """Return feature dict + (N,NF) float32 matrix for the CNN side-tower.

    Features (features are raw intensity / positional units; the CNN tower
    normalizes them):
      f0 xbnd        ~[1,2]
      f1 sb_norm     envelope/floor   (floor_T zoomed)
      f2 envAll_norm flank-env/floor
      f3 width       scans (>=1)
      f4 D_Y         spacing ratio ~1
      f5 local_floor (0.05-clamped per-window floor)
    """
    positions = np.asarray(positions, dtype=np.int64)
    n = len(positions)
    N, C = lanes.shape
    env = lanes.max(axis=1)

    spac = np.zeros(n, float)
    if n >= 2:
        spac[:n - 1] = np.diff(positions.astype(float))
        spac[n - 1] = spac[n - 2]
    Y = fitted_spacing(positions, spac)

    floor = max(0.05, float(np.mean(
        [min(env[max(0, int(p) - 2)], env[min(N - 1, int(p) + 2)])
         for p in positions])))
    T = 1.24 * floor  # the fuzzy threshold scale

    feats = np.zeros((n, 6), np.float32)
    for i, p in enumerate(positions):
        p = int(p)
        if p >= N:
            feats[i, 0], feats[i, 1] = 1.0, 1.0
            feats[i, 2], feats[i, 3] = 1.0, 1.0
            feats[i, 4], feats[i, 5] = 1.0, floor
            continue
        sb = float(env[p])
        el = float(env[max(0, p - 2)])
        er = float(env[min(N - 1, p + 2)])
        ea = min(el, er)
        dom = int(lanes[p].argmax())
        wd = peak_width(lanes[:, dom], p, sb / 2.0)
        feats[i, 0] = xbnd_of(lanes, p)
        feats[i, 1] = sb / T if T > 0 else 0.0
        feats[i, 2] = ea / T if T > 0 else 0.0
        feats[i, 3] = wd
        feats[i, 4] = (spac[i] / Y[i]) if Y[i] > 0 else 1.0
        feats[i, 5] = floor
    return feats


def okn_features(lanes, positions):
    """Feature arrays for the fuzzy OKN gate (classify_fuzzy.classify):
    returns Y_int, sb, envAll, D_int, E_int, s2 as lists."""
    positions = np.asarray(positions, dtype=np.int64)
    n = len(positions)
    N, C = lanes.shape
    env = lanes.max(axis=1)
    spac = np.zeros(n, float)
    if n >= 2:
        spac[:n - 1] = np.diff(positions.astype(float))
        spac[n - 1] = spac[n - 2]
    Y = fitted_spacing(positions, spac).astype(np.int64)
    sb = np.array([float(env[int(p)]) for p in positions], np.float32)
    envAll = np.array(
        [min(float(env[max(0, int(p) - 2)]),
             float(env[min(N - 1, int(p) + 2)])) for p in positions],
        np.float32)
    D = spac.astype(np.int64)
    E = positions.astype(np.int64)
    s2 = np.array([xbnd_of(lanes, int(p)) for p in positions], np.float32)
    return Y, sb, envAll, D, E, s2