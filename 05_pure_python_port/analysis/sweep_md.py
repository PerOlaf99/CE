import sys, glob, statistics
sys.path.insert(0, '/workspace')
import numpy as np
from megabace.rsd import RsdFile
from megabace.basecall import BaseCaller

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


def score_one(f, **kw):
    rsd = RsdFile(f)
    tr = rsd.extract_traces()
    bc = BaseCaller(channel_order=rsd.metadata.channel_order, trim=True, **kw)
    call = bc.call(tr)
    path = sw(call.bases, refc)
    if path is None:
        return (0.0, 0, 0, len(call.bases), call.bases.count('N'))
    M = sum(1 for x in path if x[2])
    cols = len(path)
    I = sum(1 for x in path if x[0] is not None and x[1] is None)
    D = sum(1 for x in path if x[1] is not None and x[0] is None)
    return (M / cols * 100, I, D, len(call.bases), call.bases.count('N'))


wells = sorted(glob.glob("MB1000_M13_DT/*.rsd"))
for md in (1, 2, 3):
    ids = []
    rows = []
    for f in wells:
        r = score_one(f, merge_dist=md)
        rows.append(r)
        ids.append(r[0])
    print(f"merge_dist={md}: mean {statistics.mean(ids):.2f}% med {statistics.median(ids):.2f}% min {min(ids):.2f}% max {max(ids):.2f}%  I={sum(r[1] for r in rows)} D={sum(r[2] for r in rows)} N={sum(r[4] for r in rows)}")

print("\nA01 detail:")
for md in (1, 2, 3):
    r = score_one("MB1000_M13_DT/A01.rsd", merge_dist=md)
    print(f"  merge_dist={md}: id={r[0]:.2f}% I={r[1]} D={r[2]} calls={r[3]} N={r[4]}")
