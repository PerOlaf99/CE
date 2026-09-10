import sys
sys.path.insert(0, '/workspace')
import numpy as np
from megabace.rsd import RsdFile
from megabace.basecall import BaseCaller, _noise_level
from megabace import signal as sigmod
from megabace.spectral import deconvolve

ref = open('/tmp/opencode/rsd/m13mp18.fasta').read().split('\n', 1)[1].replace('\n', '').upper()
refRC = ref.translate(str.maketrans('ACGT', 'TGCA'))[::-1]
refc = refRC + refRC
GAP = -5

def sw(a, b):
    na, nb = len(a), len(b)
    H = np.zeros((na + 1, nb + 1), dtype=np.int32)
    ar = np.frombuffer(a.encode(), dtype=np.uint8)
    br = np.frombuffer(b.encode(), dtype=np.uint8)
    for i in range(1, na + 1):
        sc = np.where(ar[i - 1] == br, 2, -3)
        C = np.maximum(np.maximum(H[i - 1, 1:] + GAP, H[i - 1, :-1] + sc), 0)
        run = np.maximum.accumulate(np.concatenate(([0], C - GAP * np.arange(1, nb + 1))))
        H[i] = run + GAP * np.arange(nb + 1)
    flat = int(H.argmax()); i = flat // (nb + 1); j = flat % (nb + 1)
    if H[i, j] == 0:
        return None
    path = []
    while i > 0 and j > 0 and H[i, j] > 0:
        if H[i, j] == H[i - 1, j - 1] + (2 if a[i - 1] == b[j - 1] else -3):
            path.append((i - 1, j - 1, a[i - 1] == b[j - 1])); i -= 1; j -= 1
        elif H[i, j] == H[i - 1, j] + GAP:
            path.append((i - 1, None, False)); i -= 1
        elif H[i, j] == H[i, j - 1] + GAP:
            path.append((None, j - 1, False)); j -= 1
        else:
            break
    path.reverse()
    return path

f = '/tmp/opencode/rsd/MB1000_M13_DT/A01.rsd'
rsd = RsdFile(f); tr = rsd.extract_traces()
order = rsd.metadata.channel_order
bc = BaseCaller(channel_order=order, trim=True)
call = bc.call(tr)
base = sigmod.subtract_baseline_multi(tr)
sep = deconvolve(base, None, True)
norm = sigmod.normalize_channels(sep)
path = sw(call.bases, refc)

dele = []
i = 0
while i < len(path):
    if path[i][0] is None and path[i][1] is not None:
        j = i
        while j + 1 < len(path) and path[j + 1][0] is None and path[j + 1][1] is not None:
            j += 1
        dele.append((i, j)); i = j + 1
    else:
        i += 1

# Rebuild the peak pipeline stage by stage
def stage_peaks():
    n_dyes = norm.shape[0]
    candidates = []
    for c in range(n_dyes):
        ch = sigmod.smooth(norm[c], window=3)
        noise = _noise_level(ch)
        pk, _ = sigmod.detect_peaks(
            ch, min_distance=bc.min_distance,
            min_prominence=max(bc.min_prominence, bc.prominence_mult * noise))
        if pk.size == 0:
            continue
        heights = ch[pk]
        q99 = np.percentile(heights, 99.0)
        floor = max(0.07 * q99, 6.0 * noise) * bc.floor_mult
        keep = heights >= floor
        for p in pk[keep]:
            candidates.append((int(p), c))
    candidates.sort(key=lambda pc: pc[0])
    return candidates

def merge(candidates):
    kept = []
    i = 0
    n = len(candidates)
    while i < n:
        j = i
        while j + 1 < n and candidates[j + 1][0] - candidates[i][0] <= bc.merge_dist:
            j += 1
        best = max(candidates[i:j + 1], key=lambda pc: norm[pc[1], pc[0]])
        kept.append(best)
        i = j + 1
    return kept

def dominance(candidates):
    out = []
    for (p, c) in candidates:
        dr = bc.dominance_radius
        dom_c = norm[c, max(0, p - dr):p + dr + 1].max()
        dom_all = norm[:, max(0, p - dr):p + dr + 1].max()
        if dom_all > 0 and dom_c >= bc.dominance * dom_all:
            out.append((p, c))
    return out

raw = stage_peaks()
dom = dominance(raw)
merged = merge(dom)

# apply spacing cull like the class does
def cull(pos, ch):
    pos = np.asarray(pos, dtype=np.float64)
    ch = np.asarray(ch, dtype=np.int64)
    for _ in range(20):
        gaps = np.diff(pos)
        if gaps.size == 0:
            break
        med = float(np.median(gaps))
        trim = gaps[(gaps > 0.4 * med) & (gaps < 2.2 * med)]
        base = float(np.median(trim)) if trim.size else med
        k = 21
        exp = np.asarray([np.median(gaps[max(0, i - k):min(gaps.size, i + k + 1)]) for i in range(gaps.size)])
        exp = np.clip(exp, 0.5 * base, 2.0 * base)
        nrm = gaps / exp
        viol = np.flatnonzero(nrm < bc.spacing_min_frac)
        if viol.size == 0:
            break
        removed = np.zeros(pos.size, dtype=bool)
        i = 0
        nv = viol.size
        while i < nv:
            j = i
            while j + 1 < nv and viol[j + 1] == viol[j] + 1:
                j += 1
            seg = pos[i:j + 2]
            w = np.argmin([norm[ch[t], int(pos[t])] for t in range(i, j + 2)])
            removed[i + w] = True
            i = j + 1
        keep = ~removed
        pos = pos[keep]; ch = ch[keep]
    return pos, ch

mp = np.asarray([p for p, _ in merged], dtype=np.float64)
mc = np.asarray([c for _, c in merged], dtype=np.int64)
cp, cc = cull(mp, mc)

print('=== pipeline trace for deletion gaps ===')
for (a, b) in dele:
    lc = path[a - 1][0]; rc = path[b + 1][0]
    lpos = int(call.positions[lc]); rpos = int(call.positions[rc])
    lo = lpos + 1; hi = rpos
    if hi - lo <= 0:
        continue
    exp_gap = float(np.median(np.diff(call.positions.astype(float))))
    print(f'\ndel {refc[path[a][1]]} flank {call.bases[lc]}{call.bases[rc]} gap {lo}..{hi}')
    print(f'  raw cands in gap: {[(p, order[c]) for (p, c) in raw if lo <= p < hi]}')
    print(f'  after dominance:  {[(p, order[c]) for (p, c) in dom if lo <= p < hi]}')
    print(f'  after merge:      {[(int(p), order[int(c)]) for (p, c) in zip(mp, mc) if lo <= p < hi]}')
    print(f'  after cull:       {[(int(p), order[int(c)]) for (p, c) in zip(cp, cc) if lo <= p < hi]}')
    print(f'  in final call:    {[(int(call.positions[k]), call.bases[k]) for k in range(len(call.bases)) if lo <= int(call.positions[k]) < hi]}')
