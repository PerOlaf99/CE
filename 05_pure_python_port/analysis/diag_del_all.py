import sys, glob, os
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, '/workspace')
import numpy as np
from collections import Counter
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


cat = Counter()
total_del = 0
recoverable_2noise = 0
recoverable_4noise = 0
for f in sorted(glob.glob("MB1000_M13_DT/*.rsd")):
    rsd = RsdFile(f)
    tr = rsd.extract_traces()
    order = rsd.metadata.channel_order
    bc = BaseCaller(channel_order=order, trim=True)
    call = bc.call(tr)
    path = sw(call.bases, refc)
    if path is None:
        continue
    c_idx = {b: i for i, b in enumerate(order)}
    i = 0
    npts = tr.shape[1]
    while i < len(path):
        if path[i][0] is None and path[i][1] is not None:
            j = i
            while j + 1 < len(path) and path[j + 1][0] is None and path[j + 1][1] is not None:
                j += 1
            # flanking calls
            left_ci = path[i - 1][0] if i > 0 else None
            right_ci = path[j + 1][0] if j + 1 < len(path) else None
            lpos = int(call.positions[left_ci]) if left_ci is not None else 0
            rpos = int(call.positions[right_ci]) if right_ci is not None else npts - 1
            want = refc[path[i][1]]
            wc = c_idx[want]
            total_del += 1
            # does the correct channel have a local max in the gap?
            seg = tr[wc, lpos + 1:rpos]
            pk2, pr2 = sigmod.detect_peaks(sigmod.smooth(seg, window=3), min_distance=1, min_prominence=0.001)
            noise = _noise_level(sigmod.smooth(tr[wc], window=3))
            found = False
            dom_ok = False
            if pk2.size:
                pmax = pr2['prominences'].max()
                k2 = int(np.argmax(pr2['prominences']))
                p = int(pk2[k2]) + lpos + 1
                dom_c = tr[wc, max(0, p - 1):min(npts, p + 2)].max()
                dom_all = tr[:, max(0, p - 1):min(npts, p + 2)].max()
                if pmax > 2.0 * noise:
                    recoverable_2noise += 1
                    found = True
                if pmax > 4.0 * noise:
                    recoverable_4noise += 1
                if dom_all > 0 and dom_c >= 0.9 * dom_all:
                    dom_ok = True
            if found:
                cat["has_localmax"] += 1
            else:
                cat["no_localmax"] += 1
            cat["dom_ok"] += 1 if dom_ok else 0
            i = j + 1
        else:
            i += 1

print("total deletions:", total_del)
print("recoverable at 2*noise:", recoverable_2noise)
print("recoverable at 4*noise:", recoverable_4noise)
print(dict(cat))
