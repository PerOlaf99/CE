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
bc = BaseCaller(channel_order=order)
call = bc.call(tr)
path = sw(call.bases, refc)
print('bases:', call.bases)
print('n calls:', len(call.bases), 'cols:', len(path))
mm = [x for x in path if not x[2]]
print('\n=== all errors ===')
for x in mm:
    if x[0] is not None and x[1] is not None:
        tag = 'MISMATCH' if call.bases[x[0]] != 'N' else 'N-call'
        print(f'{tag:8s} read[{x[0]}]={call.bases[x[0]]} ref[{x[1]}]={refc[x[1]]} refRC={x[1]} fwd={7249-1-x[1]}')
    elif x[0] is None:
        print(f'DELETION   ref[{x[1]}]={refc[x[1]]} refRC={x[1]} fwd={7249-1-x[1]}')
    else:
        print(f'INSERTION  read[{x[0]}]={call.bases[x[0]]} pos={int(call.positions[x[0]])}')
