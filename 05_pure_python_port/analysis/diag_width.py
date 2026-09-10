import sys
sys.path.insert(0, '/workspace')
import numpy as np
from megabace.rsd import RsdFile
from megabace.basecall import BaseCaller
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


def half_width(ch, p):
    """width at half max on smoothed channel"""
    h = ch[p]
    if h <= 0:
        return 0
    half = h / 2
    lo = p
    while lo > 0 and ch[lo] > half:
        lo -= 1
    hi = p
    n = len(ch)
    while hi < n - 1 and ch[hi] > half:
        hi += 1
    return hi - lo


sm = np.vstack([sigmod.smooth(norm[c], window=3) for c in range(4)])
# compute widths for all calls
widths = []
for j in range(len(call.bases)):
    p = int(call.positions[j])
    c = order.index(call.bases[j]) if call.bases[j] in order else -1
    if c < 0:
        widths.append(0)
    else:
        widths.append(half_width(sm[c], p))
widths = np.asarray(widths)

print("all call half-widths: median", np.median(widths[widths > 0]), "mean", widths[widths > 0].mean())
# deletion-adjacent calls (left and right flanks)
print("\ndeletion flank widths:")
for (a, b) in dele:
    lc = path[a - 1][0]
    rc = path[b + 1][0]
    wl = widths[lc]
    wr = widths[rc]
    lb = call.bases[lc]
    rb = call.bases[rc]
    lpos = int(call.positions[lc])
    rpos = int(call.positions[rc])
    # width of the flanking band in ITS OWN channel
    print(f"  del ref={refc[path[a][1]]} flank {lb}{rb} pos {lpos}->{rpos} width_L={wl} width_R={wr}")

# compare widths around deletions vs elsewhere (is the merged band wider?)
print("\nwidth histogram of calls within 10 of a deletion vs all calls:")
near = np.zeros(len(call.bases), dtype=bool)
for (a, b) in dele:
    lc = path[a - 1][0]
    rc = path[b + 1][0]
    near[max(0, lc - 2):min(len(call.bases), rc + 3)] = True
w_near = widths[near]
w_other = widths[~near]
print("  near deletions: median", np.median(w_near[w_near > 0]), "mean", w_near[w_near > 0].mean())
print("  elsewhere:      median", np.median(w_other[w_other > 0]), "mean", w_other[w_other > 0].mean())
