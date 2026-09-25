"""Probabilistic fusion basecaller.

Fuses single-channel peak detection with four-channel (summed) detection using
different settings per pass. Candidates are scored by a peak probability
(height x purity, log-scaled). A spacing-consistent max-probability path is
selected by dynamic programming. Per-channel peak distance may differ:
same-channel candidates (homopolymer runs / shoulders) tolerate smaller
minimum separation than cross-channel ones.

Pipeline:
  1. strict_peaks():  strict per-channel skeleton (global-noise gating).
  2. candidate_pool(): primary skeleton + permissive candidates added ONLY in
     gaps where the skeleton implies a missing base.
  3. prob_path(): max-probability spacing-consistent subsequence (DP).
"""
import numpy as np
from megabace.basecall import BaseCaller, _noise_level
from megabace import signal as sigmod
from megabace import spectral

ref = open("m13mp18.fasta").read().split("\n",1)[1].replace("\n","").upper()
refRC = ref.translate(str.maketrans("ACGT","TGCA"))[::-1]
refc = refRC + refRC
GAP=-5

def sw(a, b):
    na, nb = len(a), len(b)
    H = np.zeros((na+1, nb+1), dtype=np.int32)
    ar = np.frombuffer(a.encode(), dtype=np.uint8); br = np.frombuffer(b.encode(), dtype=np.uint8)
    for i in range(1, na+1):
        sc = np.where(ar[i-1]==br, 2, -3)
        C = np.maximum(np.maximum(H[i-1,1:]+GAP, H[i-1,:-1]+sc), 0)
        run = np.maximum.accumulate(np.concatenate(([0], C - GAP*np.arange(1,nb+1))))
        H[i] = run + GAP*np.arange(nb+1)
    flat = int(H.argmax()); i = flat//(nb+1); j = flat%(nb+1)
    path=[]
    while i>0 and j>0 and H[i,j]>0:
        if H[i,j]==H[i-1,j-1]+(2 if a[i-1]==b[j-1] else -3): path.append((i-1,j-1,a[i-1]==b[j-1])); i-=1; j-=1
        elif H[i,j]==H[i-1,j]+GAP: path.append((i-1,None,False)); i-=1
        elif H[i,j]==H[i,j-1]+GAP: path.append((None,j-1,False)); j-=1
        else: break
    path.reverse(); return path

def score(peaks, chans, order):
    s = "".join(order[c] for c in chans)
    path = sw(s, refc)
    if path is None: return dict(id=0,cols=0,I=0,D=0,M=0,calls=len(s),first=0,last=0)
    M=sum(1 for x in path if x[2]); cols=len(path)
    I=sum(1 for x in path if x[0] is not None and x[1] is None)
    D=sum(1 for x in path if x[1] is not None and x[0] is None)
    jv=[x[1] for x in path if x[1] is not None]
    return dict(id=M/cols*100, cols=cols, I=I, D=D, M=M, calls=len(s), first=jv[0], last=jv[-1])

def _per_channel_peaks(norm, smooth_w, pm, fm, noise_mult=1.0):
    """Per-channel peak lists with a shared (global) noise floor."""
    noises = [_noise_level(sigmod.smooth(norm[c], window=smooth_w)) for c in range(4)]
    gnoise = float(np.median(noises))*noise_mult
    peaks_by_ch = {}
    for c in range(4):
        ch = sigmod.smooth(norm[c], window=smooth_w)
        pk,_ = sigmod.detect_peaks(ch, min_distance=2, min_prominence=max(0.001,pm*gnoise))
        if pk.size==0: continue
        heights=ch[pk]; q99=np.percentile(heights,99); floor=max(0.07*q99,6.0*gnoise)*fm
        peaks_by_ch[c] = [(int(p), float(norm[c,p]), float(norm[c,p]/max(norm[:,p].max(),1e-9)))
                          for p in pk if heights[pk==p][0]>=floor and norm[c,p]>=norm[:,p].max()]
    return peaks_by_ch

def strict_peaks(norm, order, smooth_w=5, pm=8.0, fm=2.0, noise_mult=1.0):
    """Strict per-channel skeleton (global-noise gated). Returns (pos, chan, height, purity)."""
    pb = _per_channel_peaks(norm, smooth_w, pm, fm, noise_mult)
    cands=[]
    for c, lst in pb.items():
        cands.extend((p, c, h, q) for p,h,q in lst)
    cands.sort(key=lambda x:x[0]); kept=[]; i=0
    while i<len(cands):
        j=i
        while j+1<len(cands) and cands[j+1][0]-cands[i][0]<=3: j+=1
        kept.append(max(cands[i:j+1],key=lambda x:x[2])); i=j+1
    return kept

def exp_spacing(pos, k=21):
    gaps = np.diff(pos.astype(float))
    if gaps.size==0: return np.array([])
    exp = np.array([np.median(gaps[max(0,i-k):min(gaps.size,i+k+1)]) for i in range(gaps.size)])
    med = float(np.median(gaps))
    return np.clip(exp, 0.5*med, 2.0*med)

def s_at(x, anchor_pos, exp):
    if exp.size==0: return 9.0
    idx = np.searchsorted(anchor_pos, x)
    idx = min(max(idx-1,0), exp.size-1)
    return exp[idx]

def candidate_pool(norm, order, pm2=2.0, fm2=0.7, use_sum=True, dom_gate=0.6,
                   gap_frac=1.3, smooth_w=5):
    """Primary skeleton + permissive candidates inserted only into gaps."""
    primary = strict_peaks(norm, order, smooth_w=smooth_w)
    pos = np.array([x[0] for x in primary], int)
    ch  = np.array([x[1] for x in primary], int)
    hgt = np.array([x[2] for x in primary], float)
    pur = np.array([x[3] for x in primary], float)
    exp = exp_spacing(pos, k=21)
    cands = [(int(p), int(c), h, q, True) for (p,c,h,q) in primary]
    # permissive per-channel peaks (window 3)
    pb = _per_channel_peaks(norm, 3, pm2, fm2, noise_mult=1.0)
    perm = []
    for c, lst in pb.items():
        perm.extend((p, c, h, q) for p,h,q in lst)
    if use_sum:
        ssum = norm.sum(axis=0)
        chsum = sigmod.smooth(ssum, window=3)
        nl = _noise_level(chsum)
        pk,_ = sigmod.detect_peaks(chsum, min_distance=1, min_prominence=max(0.001,pm2*nl))
        if pk.size:
            hh=chsum[pk]; q99=np.percentile(hh,99); fl=max(0.07*q99,6.0*nl)*fm2
            for p,h in zip(pk,hh):
                if h>=fl:
                    dom = int(np.argmax(norm[:,p]))
                    perm.append((int(p), dom, float(norm[dom,p]), float(norm[dom,p]/max(norm[:,p].max(),1e-9))))
    # keep permissive candidates that fall strictly inside a skeleton gap that
    # implies >=1 missing base, and are not within 2pt of a skeleton peak
    perm = [x for x in perm if not any(abs(x[0]-pp)<=2 for pp in pos)]
    if exp.size:
        for (p,c,h,q) in perm:
            lo = np.searchsorted(pos, p) - 1
            if lo < 0 or lo+1 >= pos.size: continue
            s = exp[lo]
            gap = pos[lo+1]-pos[lo]
            if gap <= gap_frac*s: continue
            if p < pos[lo]+0.45*s or p > pos[lo+1]-0.45*s: continue
            # same-channel as one of the flanking skeleton bases preferred
            cands.append((p, c, h, q, False))
    cands.sort(key=lambda x:x[0])
    return cands, exp, pos

def prob_path(cands, anchor_pos, exp, minr_same=0.42, minr_cross=0.5,
              gap_pen=0.5, miss_pen=0.3, big_pen=5.0, max_r=2.6,
              primary_bonus=0.4, prim_w=1.0, perm_w=1.0):
    """Max-probability spacing-consistent subsequence via DP."""
    N = len(cands)
    if N == 0: return np.array([]), np.array([])
    pos = np.array([x[0] for x in cands], float)
    chan = np.array([x[1] for x in cands], int)
    isprim = np.array([x[4] for x in cands], bool)
    sc = np.array([x[2]*x[3] for x in cands], float)
    sc = np.log1p(sc)
    w = np.where(isprim, prim_w, perm_w)
    bonus = np.where(isprim, primary_bonus, 0.0)
    sc = w*sc + bonus
    dp = sc.copy()
    par = np.full(N, -1, int)
    for j in range(N):
        s_j = sc[j]; pj = pos[j]; cj = chan[j]
        best = dp[j]; best_i = -1
        for i in range(j):
            d = pj - pos[i]
            s = s_at(pos[i], anchor_pos, exp)
            if s <= 0: continue
            r = d/s
            minr = minr_same if chan[i]==cj else minr_cross
            if r < minr: continue
            if r > max_r:
                pen = big_pen
            else:
                k = max(1, int(round(r)))
                pen = gap_pen*abs(r-k) + (k-1)*miss_pen
            val = dp[i] + s_j - pen
            if val > best:
                best = val; best_i = i
        dp[j] = best; par[j] = best_i
    end = int(np.argmax(dp))
    idxs=[]
    while end >= 0:
        idxs.append(end); end = par[end]
    idxs.reverse()
    return np.array([cands[i][0] for i in idxs], int), np.array([cands[i][1] for i in idxs], int)

def prob_basecall(norm, order, pm2=2.0, fm2=0.7, smooth_w=5, minr_same=0.42,
                  minr_cross=0.5, gap_pen=0.5, miss_pen=0.3, primary_bonus=0.4,
                  gap_frac=1.3, prim_w=1.0, perm_w=1.0, use_sum=True):
    cands, exp, sp = candidate_pool(norm, order, pm2=pm2, fm2=fm2, use_sum=use_sum,
                                    gap_frac=gap_frac, smooth_w=smooth_w)
    p, c = prob_path(cands, sp, exp, minr_same=minr_same, minr_cross=minr_cross,
                     gap_pen=gap_pen, miss_pen=miss_pen, primary_bonus=primary_bonus,
                     prim_w=prim_w, perm_w=perm_w)
    return p, c
