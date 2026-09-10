import sys
sys.path.insert(0, '/workspace')
import numpy as np
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


f = "MB1000_M13_DT/A01.rsd"
rsd = RsdFile(f)
tr = rsd.extract_traces()
order = rsd.metadata.channel_order
bc = BaseCaller(channel_order=order, trim=True)
call = bc.call(tr)
path = sw(call.bases, refc)

# collect deletions: consecutive ref-only steps with the flanking calls
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

print(f"A01 deletions: {len(dele)}")
for (a, b) in dele:
    # flanking called peaks
    left_ci = path[a - 1][0] if a > 0 else None
    right_ci = path[b + 1][0] if b + 1 < len(path) else None
    lpos = int(call.positions[left_ci]) if left_ci is not None else None
    rpos = int(call.positions[right_ci]) if right_ci is not None else None
    lbase = call.bases[left_ci] if left_ci is not None else "?"
    rbase = call.bases[right_ci] if right_ci is not None else "?"
    ref_del = refc[path[a][1]:path[b + 1][1]]
    n = tr.shape[1]
    # look for undetected local maxima (shoulders) in the gap region
    lo = lpos + 1 if lpos is not None else 0
    hi = rpos if rpos is not None else n - 1
    if hi - lo < 2 or hi <= lo:
        print(f"gap {ref_del:4s} pos {lpos}-{rpos} flank {lbase}{rbase} no window")
        continue
    seg = tr[:, lo:hi]
    local = []
    for c in range(4):
        ch = sigmod.smooth(seg[c], window=3)
        pk, props = sigmod.detect_peaks(ch, min_distance=1, min_prominence=0.001)
        for k, p in enumerate(pk):
            if props['prominences'][k] > 1e-4:
                local.append((int(p) + lo, c, float(ch[p]), float(props['prominences'][k])))
    local.sort(key=lambda x: -x[2])
    desc = ",".join(f"{order[c]}@{p}:{h:.2f}" for p, c, h, _ in local[:3]) if local else "none"
    print(f"gap {ref_del:4s} flank {lbase}{rbase} pos {lpos}->{rpos} (spacing {rpos - lpos}) local: {desc}")
