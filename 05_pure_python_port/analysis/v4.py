import numpy as np
import scipy.signal as sps

def _noise(x):
    return np.median(np.abs(np.diff(x))) / 0.6745

def detect_candidates(sep, noise_mult=2.0, height_mult=2.0):
    cands = []
    for ch in range(4):
        x = sep[ch]
        nl = _noise(x)
        pk, props = sps.find_peaks(x, prominence=max(noise_mult*nl, 1e-3),
                                   height=height_mult*nl, distance=1, width=0.5)
        h = x[pk]
        w = props["widths"]
        for p, hh, ww in zip(pk, h, w):
            cands.append((int(p), ch, float(hh), float(ww)))
    cands.sort(key=lambda c: c[0])
    return cands

def _smooth_expected_spacing(pos):
    if pos.size < 5:
        return np.median(np.diff(pos))
    gaps = np.diff(pos)
    g = gaps.copy()
    # remove extreme outliers for a stable baseline
    for _ in range(3):
        med = np.median(g)
        mad = np.median(np.abs(g-med)) + 1e-9
        g = g[np.abs(g-med) < 3*mad]
    base = float(np.median(g))
    # moving median with window 31, clipped to [0.5*base, 2*base]
    k = 31
    sm = np.array([np.median(gaps[max(0,i-k):min(gaps.size,i+k+1)]) for i in range(gaps.size)])
    sm = np.clip(sm, 0.5*base, 2.0*base)
    return sm

def cull_spacing(cands, min_frac=0.35):
    if not cands:
        return [], np.array([], int)
    pos = np.array([c[0] for c in cands], float)
    h   = np.array([c[2] for c in cands], float)
    ch  = np.array([c[1] for c in cands], int)
    w   = np.array([c[3] for c in cands], float)
    # iterative: cluster cull
    for _ in range(20):
        p = pos; hh = h
        exp = _smooth_expected_spacing(p)
        # gaps in terms of expected spacing at each side
        gaps = np.diff(p)
        gmid = exp
        nrm = gaps / np.clip(gmid, 1.0, None)
        viol = np.flatnonzero(nrm < min_frac)
        if viol.size == 0:
            break
        # merge overlapping violations into clusters
        # build clusters of consecutive indices connected by small gaps
        removed = np.zeros(p.size, bool)
        clusters = []
        cur = []
        for vi in viol:
            if cur and vi > cur[-1]+1:
                clusters.append(cur); cur = []
            cur.append(vi)
        if cur: clusters.append(cur)
        for cl in clusters:
            # indices involved: pair i (cl) spans peaks cl and cl+1; unify all
            peak_idx = set()
            for vi in cl:
                peak_idx.add(vi); peak_idx.add(vi+1)
            peak_idx = sorted(peak_idx)
            if not peak_idx: continue
            # keep strongest
            best = max(peak_idx, key=lambda i: hh[i])
            for i in peak_idx:
                if i != best:
                    removed[i] = True
        if not removed.any():
            break
        keep = ~removed
        pos = p[keep]; h = hh[keep]
        # filter cands arrays by original indices
        oidx = np.flatnonzero(keep)
        ch = ch[oidx]; w = w[oidx]
        if pos.size < 3:
            break
    out = [(int(pos[i]), int(ch[i]), float(h[i]), float(w[i])) for i in range(pos.size)]
    return out, np.arange(pos.size)

def assign_channels(sep, cands, win=1):
    n = sep.shape[1]
    seq = []
    for (p, ch, h, w) in cands:
        lo, hi = max(0,p-win), min(n,p+win+1)
        v = sep[:, lo:hi].max(axis=1)
        dom = int(v.argmax())
        v2 = np.delete(v, dom)
        cross = v2.max()/max(v[dom],1e-9)
        seq.append((p, dom, cross, v[dom]))
    return seq
