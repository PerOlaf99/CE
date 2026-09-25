import numpy as np
import scipy.signal as sps
from megabace.basecall import _noise_level
from megabace import signal as sigmod

def peak_area(S, ch, p, aw):
    lo, hi = max(0,p-aw), min(S.shape[1],p+aw+1)
    if hi <= lo: return 0.0
    x = S[ch, lo:hi]
    b = min(x[0], x[-1])
    return float(np.trapezoid(np.maximum(x-b, 0)))

def detect_height(norm, pm, fm, md, dom):
    candidates = []
    for c in range(4):
        ch = sigmod.smooth(norm[c], window=3)
        noise = _noise_level(ch)
        pk, _ = sigmod.detect_peaks(ch, min_distance=md, min_prominence=max(0.001, pm*noise))
        if pk.size == 0: continue
        heights = ch[pk]
        q99 = np.percentile(heights, 99.0)
        floor = max(0.07*q99, 6.0*noise) * fm
        keep = heights >= floor
        for p in pk[keep]:
            if norm[c, p] >= dom * norm[:, p].max():
                candidates.append((int(p), c))
    if not candidates: return np.zeros(0,int), np.zeros(0,int)
    candidates.sort(key=lambda pc: pc[0])
    kept=[]; i=0; n=len(candidates)
    while i < n:
        j = i
        while j+1 < n and candidates[j+1][0]-candidates[i][0] <= 3:
            j += 1
        best = max(candidates[i:j+1], key=lambda pc: norm[pc[1], pc[0]])
        kept.append(best); i = j+1
    peaks = np.array([p for p,_ in kept]); chans = np.array([c for _,c in kept])
    return peaks, chans

def spacing_cull(peaks, chans, norm, min_frac=0.35, iters=15):
    if peaks.size < 4: return peaks, chans
    pos = peaks.astype(float); ch = chans.copy()
    for _ in range(iters):
        gaps = np.diff(pos)
        if gaps.size==0: break
        med = float(np.median(gaps))
        g = gaps[(gaps > 0.4*med) & (gaps < 2.2*med)]
        base = float(np.median(g)) if g.size else med
        k = 21
        exp = np.array([np.median(gaps[max(0,i-k):min(gaps.size,i+k+1)]) for i in range(gaps.size)])
        exp = np.clip(exp, 0.5*base, 2.0*base)
        nrm = gaps / exp
        viol = np.flatnonzero(nrm < min_frac)
        if viol.size==0: break
        removed = np.zeros(pos.size, bool)
        i = 0
        while i < viol.size:
            j = i
            while j+1 < viol.size and viol[j+1] == viol[j]+1:
                j += 1
            pidx = list(range(int(viol[i]), int(viol[j])+2))
            pidx = [p for p in pidx if p < pos.size]
            best = max(pidx, key=lambda p: norm[ch[p], int(pos[p])])
            for p in pidx:
                if p != best: removed[p] = True
            i = j+1
        keep = ~removed
        pos = pos[keep]; ch = ch[keep]
        if pos.size < 4: break
    return pos.astype(int), ch

def area_gate(norm, peaks, chans, dom=0.7, af=0.5, fl_frac=0.04):
    """Reassign channels by peak AREA and gate weak ones."""
    if peaks.size < 2: return peaks, chans
    spacing = float(np.median(np.diff(peaks)))
    aw = max(2, int(round(af*spacing)))
    areas = np.zeros((4, peaks.size))
    for j,p in enumerate(peaks):
        for c in range(4):
            areas[c,j] = peak_area(norm, c, p, aw)
    newch = np.argmax(areas, axis=0)
    maxa = areas.max(axis=0)
    domok = areas[newch, np.arange(peaks.size)] >= dom * np.maximum(maxa, 1e-9)
    q99c = np.array([np.percentile(areas[c], 99) for c in range(4)])
    floork = np.array([areas[c, np.arange(peaks.size)] >= max(fl_frac*q99c[c], 0.5) for c in range(4)])
    keep = domok & floork.any(axis=0)
    return peaks[keep], newch[keep]
