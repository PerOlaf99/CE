import sys
sys.path.insert(0, '/workspace')
import numpy as np
from megabace.rsd import RsdFile
from megabace.basecall import BaseCaller, _noise_level
from megabace import signal as sigmod
from megabace.spectral import deconvolve

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
sep = deconvolve(base, None, True)
norm = sigmod.normalize_channels(sep)
path = sw(call.bases, refc)

# replicate candidate detection
candidates = []
for c in range(4):
    ch = sigmod.smooth(norm[c], window=3)
    noise = _noise_level(ch)
    pk, _ = sigmod.detect_peaks(ch, min_distance=2, min_prominence=max(0.001, 8.0 * noise))
    if pk.size == 0:
        continue
    heights = ch[pk]
    q99 = np.percentile(heights, 99.0)
    floor = max(0.07 * q99, 6.0 * noise) * 2.0
    keep = heights >= floor
    for p in pk[keep]:
        lo = max(0, p - 2); hi = p + 3
        dom_c = norm[c, lo:hi].max()
        dom_all = norm[:, lo:hi].max()
        if dom_c >= 1.0 * dom_all:
            candidates.append((int(p), c))

candidates.sort()
print(f"total candidates: {len(candidates)}")
# show candidates in the neighborhood of the 3 OK deletions
for target in (3141, 6260, 7217):
    print(f"\ncandidates within 20 of {target}:")
    for p, c in candidates:
        if abs(p - target) <= 20:
            print(f"  {order[c]}@{p}")

# simulate merge
merged = []
i = 0
n = len(candidates)
while i < n:
    j = i
    while j + 1 < n and candidates[j + 1][0] - candidates[i][0] <= 3:
        j += 1
    best = max(candidates[i:j + 1], key=lambda pc: norm[pc[1], pc[0]])
    merged.append(best)
    i = j + 1
print(f"\nafter merge: {len(merged)} peaks")
for target in (3141, 6260, 7217):
    print(f"merged peaks within 20 of {target}:")
    for p, c in merged:
        if abs(p - target) <= 20:
            print(f"  {order[c]}@{p}")

# compare to actual called positions
print("\nactual called positions within 20 of targets:")
for target in (3141, 6260, 7217):
    for p, b in zip(call.positions, call.bases):
        if abs(int(p) - target) <= 20:
            print(f"  {b}@{int(p)}")
