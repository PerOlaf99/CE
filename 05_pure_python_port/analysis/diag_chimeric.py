import sys
sys.path.insert(0, '/workspace')
import numpy as np
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

f = '/tmp/opencode/rsd/MB1000_M13_DT/A01.rsd'
rsd = RsdFile(f); tr = rsd.extract_traces()
order = rsd.metadata.channel_order
bc = BaseCaller(channel_order=order, trim=False)
call = bc.call(tr)
bases = call.bases
n = len(bases)
print('untrimmed read length:', n)

# Full local alignment
path = sw(bases, refc)
aligned_read = [x[0] for x in path]
aligned_ref = [x[1] for x in path]
r0 = min(x for x in aligned_read if x is not None)
r1 = max(x for x in aligned_read if x is not None)
print(f'main alignment: read [{r0}:{r1}] (len {r1-r0})')

# Which read positions are NOT covered by the main alignment?
covered = np.zeros(n, dtype=bool)
for x in path:
    if x[0] is not None:
        covered[x[0]] = True
uncov = np.flatnonzero(~covered)
if uncov.size:
    print('uncovered read positions:', uncov.min(), 'to', uncov.max(), 'count', uncov.size)
    # head = before r0, tail = after r1
    head = bases[:r0]
    tail = bases[r1:]
    print('head len:', len(head))
    print('tail len:', len(tail))
    # align tail against full refc (and forward strand too)
    ptail = sw(tail, refc)
    if ptail:
        M = sum(1 for x in ptail if x[2])
        print(f'tail SW vs refc: matches {M}/{len(ptail)} = {M/len(ptail)*100:.1f}%')
        if M:
            rf = min(x[1] for x in ptail if x[1] is not None)
            rr = max(x[1] for x in ptail if x[1] is not None)
            print(f'tail aligns to refRC [{rf}:{rr}] (mod 7249 = {rf % 7249}, {rr % 7249})')
    # also forward strand
    ptail2 = sw(tail, ref + ref)
    if ptail2:
        M2 = sum(1 for x in ptail2 if x[2])
        print(f'tail SW vs forward ref: matches {M2}/{len(ptail2)} = {M2/len(ptail2)*100:.1f}%')
        if M2:
            rf = min(x[1] for x in ptail2 if x[1] is not None)
            rr = max(x[1] for x in ptail2 if x[1] is not None)
            print(f'tail aligns to fwd [{rf}:{rr}] (mod 7249 = {rf % 7249}, {rr % 7249})')
    # head vs refc
    phead = sw(head, refc)
    if phead:
        Mh = sum(1 for x in phead if x[2])
        print(f'head SW vs refc: matches {Mh}/{len(phead)} = {Mh/len(phead)*100:.1f}%')
        if Mh:
            rf = min(x[1] for x in phead if x[1] is not None)
            rr = max(x[1] for x in phead if x[1] is not None)
            print(f'head aligns to refRC [{rf}:{rr}] (mod 7249 = {rf % 7249}, {rr % 7249})')
