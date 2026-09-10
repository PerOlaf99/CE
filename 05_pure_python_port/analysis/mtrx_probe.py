import struct, numpy as np, itertools, sys

def abif_get(fn):
    d = open(fn, 'rb').read(); res = {}
    for i in range(len(d) - 28):
        name = d[i:i + 4]
        if not all((c >= 65 and c <= 90) or (c >= 48 and c <= 57) for c in name):
            continue
        num = struct.unpack('>I', d[i + 4:i + 8])[0]
        esize = struct.unpack('>H', d[i + 10:i + 12])[0]
        cnt = struct.unpack('>I', d[i + 12:i + 16])[0]
        off = struct.unpack('>I', d[i + 20:i + 24])[0]
        key = (name, num)
        if key in res or esize not in (1, 2, 4) or not (0 < off < len(d)) or cnt * esize + off > len(d):
            continue
        res[key] = d[off:off + cnt * esize]
    return res

t = abif_get('/tmp/opencode/cimarron_gt/MB1000_M13_DT_Cp312_MD1/ABD/A01.abd')
M = np.frombuffer(t[(b'MTRX', 1)], dtype='>i2').reshape(4, 4).astype(np.float64)
ploc = np.frombuffer(t[(b'PLOC', 1)], dtype='>i2').astype(int)
gseq = t[(b'PBAS', 1)].decode()
R = np.stack([np.frombuffer(t[(b'DATA', n)], dtype='>i2').astype(np.float64)
              for n in (9, 10, 11, 12)])
idx = list(range(150, 600))
print('R shape', R.shape, 'nan?', np.isnan(R).any(), 'ploc range', ploc.min(), ploc.max(), file=sys.stderr)

def eval_tr(S, perm):
    hits = 0; nn = 0
    for i in idx:
        p = int(ploc[i]); lo = max(0, p - 2); hi = min(S.shape[1], p + 3)
        if hi <= lo:
            continue
        nn += 1
        mx = S[:, lo:hi].max(axis=1)
        row = int(np.argmax(mx))
        if perm[row] == gseq[i]:
            hits += 1
    return hits / max(nn, 1)

for name, S in [('M', M), ('invM', np.linalg.inv(M))]:
    best_sc = -1.0; best_p = None
    for p in itertools.permutations('ACGT'):
        perm = ''.join(p)
        sc = eval_tr(S, perm)
        if sc > best_sc:
            best_sc = sc; best_p = perm
    print('%s best %.3f perm %s' % (name, best_sc, best_p))
