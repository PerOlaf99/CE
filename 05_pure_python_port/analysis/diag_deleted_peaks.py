import sys
sys.path.insert(0, '/workspace')
import numpy as np
from megabace.rsd import RsdFile
from megabace.basecall import BaseCaller, _noise_level
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

f = '/tmp/opencode/rsd/MB1000_M13_DT/A01.rsd'
rsd = RsdFile(f); tr = rsd.extract_traces()
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
        dele.append((i, j)); i = j + 1
    else:
        i += 1

# Reproduce detection pre-cull: per-channel peaks (all candidates, before merge/dom)
print('=== pre-merge candidate peaks in deletion gaps ===')
for (a, b) in dele:
    lc = path[a - 1][0]; rc = path[b + 1][0]
    lpos = int(call.positions[lc]); rpos = int(call.positions[rc])
    lo = lpos + 1; hi = rpos
    if hi - lo <= 0:
        continue
    print(f'\ndel {refc[path[a][1]]} flank {call.bases[lc]}{call.bases[rc]} gap {lo}..{hi} ({hi-lo}px)')
    for c in range(4):
        ch = sigmod.smooth(norm[c], window=3)
        noise = _noise_level(ch)
        pk, props = sigmod.detect_peaks(
            ch[lo:hi],
            min_distance=bc.min_distance,
            min_prominence=max(bc.min_prominence, bc.prominence_mult * noise),
        )
        if pk.size == 0:
            continue
        for p0, prom in zip(pk, props['prominences']):
            p = int(p0) + lo
            heights = ch[pk]
            q99 = np.percentile(heights, 99.0)
            floor = max(0.07 * q99, 6.0 * noise) * bc.floor_mult
            h = ch[p]
            keep = h >= floor
            # dominance
            dr = bc.dominance_radius
            dom_c = norm[c, max(0, p - dr):p + dr + 1].max()
            dom_all = norm[:, max(0, p - dr):p + dr + 1].max()
            dom = 'D' if (dom_all > 0 and dom_c >= bc.dominance * dom_all) else '.'
            print(f'  ch{order[c]} p={p} h={h:.3f} floor={floor:.3f} prom={prom:.3f} {"keep" if keep else "cull"} dom{dom}')
