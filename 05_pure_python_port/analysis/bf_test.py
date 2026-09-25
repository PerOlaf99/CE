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
        return (0.0, 0, 0, len(call.bases), call.bases.count('N'), call.bases)
    M = sum(1 for x in path if x[2])
    cols = len(path)
    I = sum(1 for x in path if x[0] is not None and x[1] is None)
    D = sum(1 for x in path if x[1] is not None and x[0] is None)
    return (M / cols * 100, I, D, len(call.bases), call.bases.count('N'), call.bases)


def main():
    argv = sys.argv[1:]
    bf = "--bf" in argv
    dr = 0
    if "--dr" in argv:
        dr = int(argv[argv.index("--dr") + 1])
        argv.pop(argv.index("--dr") + 1)
        argv.pop(argv.index("--dr"))
    adr = None
    if "--adr" in argv:
        adr = int(argv[argv.index("--adr") + 1])
        argv.pop(argv.index("--adr") + 1)
        argv.pop(argv.index("--adr"))
    tdr = None
    if "--tdr" in argv:
        tdr = int(argv[argv.index("--tdr") + 1])
        argv.pop(argv.index("--tdr") + 1)
        argv.pop(argv.index("--tdr"))
    ar = 0
    if "--ar" in argv:
        ar = int(argv[argv.index("--ar") + 1])
        argv.pop(argv.index("--ar") + 1)
        argv.pop(argv.index("--ar"))
    raw = "--raw" in argv
    argv = [a for a in argv if a != "--raw"]
    wells = [a for a in argv if a != "--bf"] or ["MB1000_M13_DT/A01.rsd"]
    kw = {}
    rows = []
    for f in wells:
        kw = dict(band_filter=bf, dominance_radius=dr, assign_radius=ar, a_bleed_smooth=not raw)
        if adr is not None:
            kw["a_dominance_radius"] = adr
        if tdr is not None:
            kw["t_dominance_radius"] = tdr
        r = score_one(f, **kw)
        rows.append((f.split("/")[-1], r[0], r[1], r[2], r[3], r[4]))
        print(f"{f.split('/')[-1]:8s} id={r[0]:6.2f}% I={r[1]} D={r[2]} calls={r[3]} N={r[4]}")
    ids = [r[1] for r in rows if r[1] > 0]
    if len(ids) > 1:
        print(f"mean {statistics.mean(ids):.2f}%  median {statistics.median(ids):.2f}%  (band_filter={bf} dr={dr} adr={adr} tdr={tdr})")


if __name__ == "__main__":
    main()
