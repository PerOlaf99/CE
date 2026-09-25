import sys, glob
sys.path.insert(0, '/workspace')
import numpy as np
from collections import Counter
from megabace.rsd import RsdFile
from megabace.basecall import BaseCaller
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


def window_max(traces, p, r):
    n = traces.shape[1]
    lo = max(0, p - r)
    hi = min(n, p + r + 1)
    return traces[:, lo:hi].max(axis=1)


stats = Counter()
correct_by_base = Counter()
flip_stats = {}
for f in sorted(glob.glob("MB1000_M13_DT/*.rsd")):
    w = f.split("/")[-1][:-4]
    rsd = RsdFile(f)
    tr = rsd.extract_traces()
    order = rsd.metadata.channel_order
    bc = BaseCaller(channel_order=order, trim=True)
    call = bc.call(tr)
    path = sw(call.bases, refc)
    if path is None:
        continue
    for (ci, ri, match) in path:
        if ci is None or ri is None:
            continue
        if call.bases[ci] != 'N':
            continue
        corr = refc[ri]
        correct_by_base[corr] += 1
        p = int(call.positions[ci])
        wm_raw = window_max(tr, p, 2)   # raw traces, radius 2
        wm_sm = window_max(sigmod.normalize_channels(tr), p, 2)  # not used; placeholder
        order_idx = {b: i for i, b in enumerate(order)}
        cidx = order_idx[corr]
        top = int(np.argmax(wm_raw))
        second = float(np.sort(wm_raw)[-2])
        topv = float(wm_raw.max())
        margin = topv / max(second, 1e-9) if second > 0 else 99.0
        # candidate rules
        rules = {
            "raw_top_is_correct": top == cidx,
            "raw_top_strict": top == cidx and second < topv,
            "raw_margin1.05": top == cidx and margin >= 1.05,
            "raw_margin1.10": top == cidx and margin >= 1.10,
            "raw_margin1.15": top == cidx and margin >= 1.15,
        }
        for rn, hit in rules.items():
            flip_stats.setdefault(rn, Counter())[corr if hit else "MISS"] += 1
        stats["total_N"] += 1

print("correct base distribution for N calls:", dict(correct_by_base))
print()
for rn, cnt in flip_stats.items():
    hits = cnt.get("MISS", 0)
    tot = sum(cnt.values())
    ok = tot - hits
    if tot:
        print(f"{rn:18s} hits={ok:4d} miss={hits:4d}  ({ok/tot*100:5.1f}% of {tot})")
