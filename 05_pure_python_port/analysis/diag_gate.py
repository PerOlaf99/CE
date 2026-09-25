import sys
sys.path.insert(0, '/workspace')
import numpy as np
from megabace.rsd import RsdFile
from megabace.basecall import BaseCaller, _noise_level
from megabace import signal as sigmod

ref = open("m13mp18.fasta").read().split("\n", 1)[1].replace("\n", "").upper()
refRC = ref.translate(str.maketrans("ACGT", "TGCA"))[::-1]
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
    flat = int(H.argmax())
    i = flat // (nb + 1)
    j = flat % (nb + 1)
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


f = "MB1000_M13_DT/A01.rsd"
rsd = RsdFile(f)
tr = rsd.extract_traces()
order = rsd.metadata.channel_order
bc = BaseCaller(channel_order=order, trim=True)
call = bc.call(tr)
base = sigmod.subtract_baseline_multi(tr)
from megabace.spectral import deconvolve
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
        dele.append((i, j))
        i = j + 1
    else:
        i += 1

c_idx = {b: i for i, b in enumerate(order)}
for (a, b) in dele:
    left_ci = path[a - 1][0]
    right_ci = path[b + 1][0]
    lpos = int(call.positions[left_ci])
    rpos = int(call.positions[right_ci])
    lbase = call.bases[left_ci]
    rbase = call.bases[right_ci]
    ref_del = refc[path[a][1]:path[b + 1][1]]
    # ref base in gap: the "missing" base - use the FIRST deleted ref base
    want = ref_del[0]
    wc = c_idx[want]
    ch = sigmod.smooth(norm[wc], window=3)
    noise = _noise_level(ch)
    pk, props = sigmod.detect_peaks(ch, min_distance=2, min_prominence=max(0.001, 8.0 * noise))
    # peaks in gap window
    in_gap = pk[(pk > lpos + 1) & (pk < rpos)]
    q99 = np.percentile(ch[pk], 99.0) if pk.size else 0.0
    floor = max(0.07 * q99, 6.0 * noise) * 2.0
    desc = []
    if in_gap.size:
        for p in in_gap:
            lo = max(0, p - 2); hi = p + 3
            domc = norm[wc, lo:hi].max()
            domall = norm[:, lo:hi].max()
            reasons = []
            if ch[p] < floor:
                reasons.append(f"floor(ch={ch[p]:.2f}<{floor:.2f})")
            if domc < 1.0 * domall:
                reasons.append(f"dom({domc:.2f}<{domall:.2f})")
            desc.append(f"{order[wc]}@{p} h={ch[p]:.2f} prom={props['prominences'][list(pk).index(p)]:.2f} " + ("; ".join(reasons) if reasons else "OK"))
    else:
        # check undetected local maxima in gap
        seg = norm[wc, lpos + 1:rpos]
        pk2, pr2 = sigmod.detect_peaks(sigmod.smooth(seg, window=3), min_distance=1, min_prominence=0.001)
        if pk2.size:
            best = pk2[int(np.argmax(pr2['prominences']))] + lpos + 1
            desc.append(f"{order[wc]}@{best} prom={pr2['prominences'].max():.3f} (below gate {max(0.001,8.0*noise):.3f})")
        else:
            desc.append("no local max at all")
    print(f"del {ref_del:3s} want={want} flank {lbase}{rbase} pos {lpos}->{rpos}: " + "; ".join(desc))
