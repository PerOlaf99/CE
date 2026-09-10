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
path = sw(call.bases, refc)

# gap ratio at each deletion
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

gaps = np.diff(call.positions)
k = 21
exp = np.asarray([np.median(gaps[max(0, m - k):min(gaps.size, m + k + 1)]) for m in range(gaps.size)])
base = float(np.median(gaps))
exp = np.clip(exp, 0.5 * base, 2.0 * base)

print(f"A01 deletions: {len(dele)}")
below = 0
for (a, b) in dele:
    left_ci = path[a - 1][0]
    right_ci = path[b + 1][0]
    lpos = int(call.positions[left_ci])
    rpos = int(call.positions[right_ci])
    # find the gap index (between flanking calls in the positions array)
    li = np.searchsorted(call.positions, lpos)
    gi = li  # gap between call li and li+1
    if gi < len(gaps):
        ratio = (rpos - lpos) / max(exp[gi], 1e-9)
    else:
        ratio = 99
    want = refc[path[a][1]]
    flag = ""
    if ratio < 1.8:
        flag = "  <== BELOW RATIO GATE"
        below += 1
    print(f"del {want} flank {call.bases[left_ci]}{call.bases[right_ci]} pos {lpos}->{rpos} spacing={rpos-lpos} exp={exp[gi]:.0f} ratio={ratio:.2f}{flag}")
print("below 1.8 gate:", below)
