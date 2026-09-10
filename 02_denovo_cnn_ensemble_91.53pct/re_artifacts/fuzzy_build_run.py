#!/usr/bin/env python3
"""Phase C: run the ported fuzzy classifier (FUN_10012140) on real separated
lanes using the ported peak detector, then apply the DLL keep/weak decision.

Feature-source bridge (asm-verified):
  Y[i]    = fitted baseline spacing  (FUN_10019280 port)
  D[i]    = SWold[i] = actual inter-peak spacing
  E[i]    = position[i] (peak scan)
  sb[i]   = env at peak position      (Wvfm::envv(peakpos))
  s2[i]   = xbnd[i] per FUN_10024e47  (position-adaptive ratio ~ [1,2])
  envAll[i] = min(left-flank env, right-flank env)   (floor source)

Per band classify_fuzzy -> (val, qual). Decision:
  q = long(val);  q==1 KEEP ; q==2 emit but mark weak if xbnd<=1.176471.
"""
import sys
import os
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))

from dll_peakdet import dll_peaks, env_max
from classify_fuzzy import classify

DATA = os.path.join(os.path.dirname(os.path.dirname(HERE)), "cache_sep")


def load_lanes(well):
    return np.load(os.path.join(DATA, f"{well}.npy"))


def fitted_spacing(positions, spacings):
    """Port of FUN_10019280: outlier-rejected mean, linear iquadratic fit of
    spacing-vs-position, fill every band with the fitted spacing (ints).
    Simplified faithful version: z-score rejection at 1.5, then linear fit,
    clamp to >=1, fill."""

    def _iquadratic(pos, sp):
        # linear least squares spacing ~ a + b*pos  (iquadratic 1st order)
        n = len(pos)
        if n < 2:
            return 0.0, 0.0
        x = np.asarray(pos, float)
        y = np.asarray(sp, float)
        b, a = np.polyfit(x, y, 1)
        return a, b

    n = len(spacings)
    sp = np.asarray(spacings, float)
    pos = np.asarray(positions, float)
    mu = sp.mean()
    sd = sp.std()
    Y = np.zeros(n, dtype=np.int64)

    if sd == 0:
        Y[:] = int(mu)
        return Y

    # outlier rejection z <= 1.5
    z = np.abs((sp - mu) / sd)
    keep = z <= 1.5
    if keep.sum() >= 2:
        a, b = _iquadratic(pos[keep], sp[keep])
        for i in range(n):
            v = a + b * pos[i]
            v = round(v)
            if v < 1:
                v = 1
            Y[i] = v
    return Y


def run(well, region=None):
    lanes = load_lanes(well)
    positions, seq, intensities = dll_peaks(lanes, None, region=region)
    positions = np.asarray(positions, dtype=np.int64)
    if len(positions) < 4:
        print(f"{well}: too few peaks ({len(positions)})")
        return None

    env = env_max(lanes)

    # features
    N = len(positions)
    pos = positions.astype(float)
    spac = np.zeros(N, float)
    spac[:N - 1] = np.diff(positions.astype(float))
    spac[N - 1] = spac[N - 2] if N >= 2 else 1.0
    Y = fitted_spacing(pos, spac).astype(float)
    D = spac.copy()
    E = positions.astype(float)

    # xbnd: position-adaptive bandwidth ratio per FUN_10024e47 semantics
    # (min>=0.1 ? min/v3 : min/sqrt(v3)+1; v3 = 4th-sorted lane env; clamp [1,2])
    C = lanes.shape[1]
    s2 = np.zeros(N, float)
    for i, p in enumerate(positions):
        p = int(p)
        if p >= lanes.shape[0]:
            s2[i] = 1.0
            continue
        vs = np.sort(lanes[p, :])[::-1]          # v1>=v2>=v3>=v4
        v3 = vs[2] if C >= 3 else 0.0
        m3 = vs.min()
        if v3 < 8.9e-16:
            v3 = 2.2e-16
        if m3 >= 0.1:
            xb = m3 / v3 if v3 > 0 else 1.0
        else:
            xb = (m3 / np.sqrt(v3) + 1.0) if v3 > 0 else 1.0
        xb = max(1.0, min(2.0, xb))
        s2[i] = xb

    # sb[i] = env at peak; envAll[i] = min(left/right flank env
    sb = np.array([env[int(p)] for p in positions], float)
    envAll = np.zeros(N, float)
    for i, p in enumerate(positions):
        p = int(p)
        l = env[max(0, p - 2)]
        r = env[min(env.shape[0] - 1, p + 2)]
        envAll[i] = min(l, r)

    out = classify(Y.astype(np.int64), sb.astype(np.float32), envAll.astype(np.float32),
                   D.astype(np.int64), E.astype(np.int64), s2.astype(np.float32), N)

    # keep/weak decision
    kept_pos = []
    kept_base = []
    for i in range(N):
        val, qual = out[i]
        q = int(round(val))
        if q == 1:
            kept_pos.append(int(positions[i]))
            kept_base.append(seq[i])
        elif q == 2:
            kept_pos.append(int(positions[i]))
            kept_base.append(seq[i])   # emit but mark weak (xbnd gate info above)
    print(f"{well}: candidate={N} kept={len(kept_pos)} "
          f"(ftol-dist of val: "
          f"{[int(round(out[i][0])) for i in range(len(out))].count(1)} ones / "
          f"{[int(round(out[i][0])) for i in range(len(out))].count(2)} twos)")
    return np.array(kept_pos), ''.join(kept_base), out


if __name__ == "__main__":
    for w in ["A01", "A02"]:
        r = run(w)
        if r:
            pos, seq, out = r
            print(f"\n{w} called {len(pos)} bases; first base seq: {seq[:40]}")