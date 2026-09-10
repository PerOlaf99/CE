import sys, glob, os
sys.path.insert(0, '/workspace')
import numpy as np
from megabace.rsd import RsdFile
from megabace.basecall import BaseCaller
from megabace import signal as sigmod
from megabace.spectral import deconvolve

ref = open('/tmp/opencode/rsd/m13mp18.fasta').read().split('\n', 1)[1].replace('\n', '').upper()
refRC = ref.translate(str.maketrans('ACGT', 'TGCA'))[::-1]
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

# collect insertions: read bases that are inserted (read idx present, no ref)
ins = []       # (well, read_idx, base, pos, flank heights, my height)
realA = []     # (well, read_idx, pos, height, flank heights) for A calls that are matches
wells = sorted(glob.glob('MB1000_M13_DT/*.rsd'))
for f in wells:
    name = os.path.basename(f).replace('.rsd', '')
    rsd = RsdFile(f); tr = rsd.extract_traces()
    order = rsd.metadata.channel_order
    bc = BaseCaller(channel_order=order)
    call = bc.call(tr)
    if len(call.bases) < 50:
        continue
    base = sigmod.subtract_baseline_multi(tr)
    sep = deconvolve(base, None, True)
    norm = sigmod.normalize_channels(sep)
    sm = np.vstack([sigmod.smooth(norm[c], window=3) for c in range(4)])
    path = sw(call.bases, refc)
    if path is None:
        continue
    # read index -> matched?
    matched = {}
    refpos = {}
    for x in path:
        if x[0] is not None and x[1] is not None:
            matched[x[0]] = x[2]
            refpos[x[0]] = x[1]
    pos = call.positions.astype(int)
    for k in range(len(call.bases)):
        b = call.bases[k]
        if b not in order:
            continue
        c = order.index(b)
        p = pos[k]
        h = sm[c, p]
        # neighbor heights: previous and next called band heights
        def _h(j):
            bj = call.bases[j]
            if bj not in order:
                return 0.0
            return sm[order.index(bj), pos[j]]
        prev_h = _h(k - 1) if k > 0 else 0.0
        next_h = _h(k + 1) if k + 1 < len(call.bases) else 0.0
        maxn = max(prev_h, next_h)
        if k in matched:
            if matched[k]:
                if b == 'A':
                    realA.append((name, k, p, h, maxn, refpos[k]))
        else:
            # insertion (read base not aligned to any ref)
            ins.append((name, k, b, p, h, maxn))

print('=== INSERTIONS (unmatched read bases) ===')
print(f'total insertions: {len(ins)}')
ach = [(b, h, mx, p) for (n, k, b, p, h, mx) in ins if b == 'A']
nonA = [(b, h, mx, p) for (n, k, b, p, h, mx) in ins if b != 'A']
print(f'A insertions: {len(ach)}  non-A insertions: {len(nonA)}')
if ach:
    print('A ins: height min/max = %.2f/%.2f, ratio-to-maxneighbor min/median/max = %.2f/%.2f/%.2f' % (
        min(h for _,h,_,_ in ach), max(h for _,h,_,_ in ach),
        min(h/mx for _,h,mx,_ in ach if mx>0), np.median([h/mx for _,h,mx,_ in ach if mx>0]),
        max(h/mx for _,h,mx,_ in ach if mx>0)))
if nonA:
    print('nonA ins: channels', [b for b,_,_,_ in nonA])
print()
print('=== REAL A CALLS (matched) ===')
if realA:
    print(f'count={len(realA)} height min/med/max = {min(h for _,_,_,h,_,_ in realA):.2f}/{np.median([h for _,_,_,h,_,_ in realA]):.2f}/{max(h for _,_,_,h,_,_ in realA):.2f}')
    rr = [h/mx for _,_,_,h,mx,_ in realA if mx > 0]
    print(f'ratio-to-maxneighbor min/med/max = {min(rr):.2f}/{np.median(rr):.2f}/{max(rr):.2f}')
    # how many real A have ratio < various thresholds
    for t in (0.3, 0.4, 0.5, 0.6):
        print(f'  real A with ratio < {t}: {sum(1 for r in rr if r < t)} / {len(rr)}')
    for t in (0.3, 0.4, 0.5, 0.6):
        print(f'  A-ins with ratio < {t}: {sum(1 for h,mx in [(h,mx) for _,h,mx,_ in ach] if mx>0 and h/mx < t)} / {len(ach)}')
