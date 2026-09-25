import glob, statistics, sys
import numpy as np
sys.path.insert(0, '/workspace')
from megabace.rsd import RsdFile
from megabace.basecall import BaseCaller
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

print('loading wells...', flush=True)
data = []
for f in sorted(glob.glob('MB1000_M13_DT/*.rsd')):
    rsd = RsdFile(f); tr = rsd.extract_traces()
    bc = BaseCaller(channel_order=rsd.metadata.channel_order, trim=True)
    call = bc.call(tr)
    data.append((call.bases, call.positions.astype(np.int64)))
print('loaded', len(data), flush=True)

def longest_ok_range(sp, ok, max_bad_run=2):
    """longest contiguous call-range whose internal gaps are mostly ok.
    ok has len = n-1 over calls; a call-range [i,j) is acceptable if the ok-run
    allows at most max_bad_run consecutive bad gaps."""
    n = len(sp) + 1
    # mark runs of consecutive bad gaps
    badruns = []  # (start_gap,length)
    k = 0
    while k < len(ok):
        if not ok[k]:
            e = k
            while e < len(ok) and not ok[e]:
                e += 1
            badruns.append((k, e - k)); k = e
        else:
            k += 1
    # acceptable call range must not contain any bad run longer than max_bad_run
    # pick longest contiguous call-range avoiding those
    banned = [(b, b + l) for (b, l) in badruns if l > max_bad_run]
    # banned in gap-index space; translate to call-index cut points: a banned gap-run
    # from gap a..b-1 means calls a+1..b are in the bad region center; range of calls
    # [a+1, b] is bad. forbid crossing it entirely: feasible ranges are intervals of
    # calls that do not contain [a+1, b].
    points = [0, n]
    for (a, b) in banned:
        points.append(a + 1); points.append(b)
    points = sorted(set(points))
    best = 0; br = (0, 0)
    for p1 in points:
        for p2 in points:
            if p2 <= p1:
                continue
            # interval of calls [p1,p2): gaps p1..p2-2 ; must avoid containing any banned gap-run
            okint = True
            for (a, b) in banned:
                lo_c, hi_c = a + 1, b
                if p1 < hi_c and lo_c < p2:
                    okint = False
                    break
            if okint and p2 - p1 > best:
                best = p2 - p1; br = (p1, p2)
    return br

def eval_variant(mode):
    ids = []; lens = []
    for bases, pos in data:
        sp = np.diff(pos)
        if sp.size < 10:
            continue
        med = float(np.median(sp))
        if mode == 'local':
            k = 21
            lm = np.asarray([np.median(sp[max(0, i - k):min(sp.size, i + k + 1)])
                             for i in range(sp.size)])
            lm = np.clip(lm, 0.5 * med, 2.0 * med)
            ok = (sp >= 0.6 * lm) & (sp <= 1.7 * lm)
        elif mode == 'global':
            ok = (sp >= 0.6 * med) & (sp <= 1.7 * med)
        else:
            lo, hi = mode
            ok = (sp >= lo * med) & (sp <= hi * med)
        s, e = longest_ok_range(sp, ok)
        t = bases[s:e]
        lens.append(len(t))
        p = sw(t, refc)
        if p is None:
            continue
        M = sum(1 for x in p if x[2])
        ids.append(M / len(p) * 100)
    if not ids:
        return (0, 0, 0)
    return (round(statistics.mean(ids), 2), round(statistics.median(ids), 2),
            round(statistics.mean(lens), 0))

print('no-trim baseline 93.9 / 93.82')
for mode in ('global', 'local', (0.55, 1.8), (0.6, 1.6), (0.5, 2.0)):
    m, md, ln = eval_variant(mode)
    print('mode', mode, 'mean', m, 'median', md, 'mean kept len', ln, flush=True)
