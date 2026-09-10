import sys, glob, statistics, os
os.chdir(os.path.dirname(os.path.abspath(__file__)))
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


wells = sorted(glob.glob("MB1000_M13_DT/*.rsd"))


def evaluate(kw):
    res = []
    for f in wells:
        rsd = RsdFile(f)
        tr = rsd.extract_traces()
        bc = BaseCaller(channel_order=rsd.metadata.channel_order, **kw)
        call = bc.call(tr)
        path = sw(call.bases, refc)
        if path is None:
            res.append((0.0, 0, 0, 0, len(call.bases), call.bases.count('N'), 0, 0))
            continue
        M = sum(1 for x in path if x[2]); cols = len(path)
        I = sum(1 for x in path if x[0] is not None and x[1] is None)
        D = sum(1 for x in path if x[1] is not None and x[0] is None)
        r0 = min(x[0] for x in path if x[0] is not None); r1 = max(x[0] for x in path if x[0] is not None)
        res.append((M / cols * 100, I, D, cols, len(call.bases), call.bases.count('N'), r1 - r0, 0))
    return res


def report(label, kw):
    res = evaluate(kw)
    ids = [r[0] for r in res]
    I = sum(r[1] for r in res); D = sum(r[2] for r in res)
    cols = sum(r[3] for r in res); n = sum(r[4] for r in res); Ns = sum(r[5] for r in res)
    reads = sum(r[6] for r in res)
    print(f"{label:34s} mean {statistics.mean(ids):.2f}% med {statistics.median(ids):.2f}% min {min(ids):.2f}% "
          f"max {max(ids):.2f}% I={I} D={D} N={Ns} n_read={n} aligned_readlen_sum={reads}")


report("baseline", {})
report("pm=2,no_cull", dict(trim=True, prominence_mult=2.0, spacing_cull=False, gap_rescan=False))
report("pm=3,no_cull", dict(trim=True, prominence_mult=3.0, spacing_cull=False, gap_rescan=False))
report("pm=5,no_cull", dict(trim=True, prominence_mult=5.0, spacing_cull=False, gap_rescan=False))
report("pm=4,no_cull", dict(trim=True, prominence_mult=4.0, spacing_cull=False, gap_rescan=False))
report("pm=2,cull,no_gr", dict(trim=True, prominence_mult=2.0, spacing_cull=True, gap_rescan=False))
