import sys
sys.path.insert(0, '/workspace')
import numpy as np
from megabace.rsd import RsdFile
from megabace.basecall import BaseCaller

ref = open('/tmp/opencode/rsd/m13mp18.fasta').read().split('\n', 1)[1].replace('\n', '').upper()
refRC = ref.translate(str.maketrans('ACGT', 'TGCA'))[::-1]
R = len(ref)
refs = {'RC': refRC + refRC, 'F': ref + ref}

def sw_blast(q, db, match=2, mismatch=-3, gopen=-5, gext=-5):
    nq = len(q); nd = len(db)
    H = np.zeros((nq + 1, nd + 1), dtype=np.int32)
    qb = np.frombuffer(q.encode(), dtype=np.uint8)
    dbb = np.frombuffer(db.encode(), dtype=np.uint8)
    best = 0; besti = 0; bestj = 0
    for i in range(1, nq + 1):
        sc = np.where(dbb == qb[i - 1], match, mismatch).astype(np.int32)
        C = np.maximum(np.maximum(H[i - 1, 1:] + gopen, H[i - 1, :-1] + sc), 0)
        run = np.maximum.accumulate(np.concatenate(([0], C - gopen * np.arange(1, nd + 1))))
        H[i] = run + gopen * np.arange(nd + 1)
        m = int(H[i].max())
        if m > best:
            best = m; besti = i; bestj = int(H[i].argmax())
    i, j = besti, bestj
    # traceback
    pairs = []
    while i > 0 and j > 0 and H[i, j] > 0:
        qc = chr(qb[i - 1]); dc = chr(dbb[j - 1])
        pairs.append((i - 1, j - 1, qc == dc))
        if H[i, j] == H[i - 1, j - 1] + (match if qc == dc else mismatch):
            i -= 1; j -= 1
        elif H[i, j] == H[i - 1, j] + gopen:
            i -= 1
        elif H[i, j] == H[i, j - 1] + gopen:
            j -= 1
        else:
            break
    pairs.reverse()
    M = sum(1 for p in pairs if p[2])
    qs = min(p[0] for p in pairs); qe = max(p[0] for p in pairs)
    rs = min(p[1] for p in pairs); re = max(p[1] for p in pairs)
    return M, len(pairs), qs, qe, rs, re

f = '/tmp/opencode/rsd/MB1000_M13_DT/A01.rsd'
rsd = RsdFile(f); tr = rsd.extract_traces()
order = rsd.metadata.channel_order
for kw, label in [
    (dict(trim=False), 'baseline'),
    (dict(trim=False, prominence_mult=2.0, spacing_cull=False, gap_rescan=False), 'permissive pm2'),
]:
    bc = BaseCaller(channel_order=order, **kw)
    call = bc.call(tr)
    q = call.bases
    print(f'--- {label}: read length {len(q)} ---')
    for strand, db in refs.items():
        M, cols, qs, qe, rs, re = sw_blast(q, db)
        print(f'  {strand}: BLAST-HSP len={cols} id={M/cols*100:.1f}% read[{qs}:{qe}] ref[{rs%R}:{re%R}]')
