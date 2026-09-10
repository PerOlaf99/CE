import sys
sys.path.insert(0, '/workspace')
import numpy as np
from megabace.rsd import RsdFile
from megabace.basecall import BaseCaller

ref = open('/tmp/opencode/rsd/m13mp18.fasta').read().split('\n', 1)[1].replace('\n', '').upper()
refRC = ref.translate(str.maketrans('ACGT', 'TGCA'))[::-1]
R = len(ref)
# both strands, doubled for circularity
refs = {'RC': refRC + refRC, 'F': ref + ref}

def sw_blast(q, db, match=1, mismatch=-1, gopen=-2, gext=-1):
    """BLAST-like gapped local alignment. Returns (score, matches, cols, refstart)."""
    nq = len(q); nd = len(db)
    H = np.zeros((nq + 1, nd + 1), dtype=np.int32)
    E = np.zeros((nq + 1, nd + 1), dtype=np.int32)  # gap in db
    F = np.zeros((nq + 1, nd + 1), dtype=np.int32)  # gap in query
    H[0, :] = gext * np.arange(nd + 1)
    for i in range(1, nq + 1):
        sc = np.where(np.frombuffer(db.encode(), dtype=np.uint8) == np.frombuffer(q.encode(), dtype=np.uint8)[i - 1],
                      match, mismatch).astype(np.int32)
        H[i, 0] = gext * i
        E[i, :] = np.maximum(H[i, :-1] + gopen, E[i, :-1] + gext)
        F[i, :] = np.maximum(H[i - 1, :] + gopen, F[i - 1, :] + gext)
        H[i, 1:] = np.maximum.reduce([H[i - 1, :-1] + sc, E[i, 1:], F[i, :-1]])
        H[i] = np.maximum(H[i], 0)
    j = int(np.argmax(H[nq]))
    score = H[nq, j]
    # traceback
    i = nq
    matches = 0; cols = 0
    while i > 0 and H[i, j] > 0:
        qi = i - 1
        qc = q[qi]
        if j > 0 and db[j - 1] == qc:
            matches += 1
        cols += 1
        # move: diagonal if H[i,j]==H[i-1,j-1]+sc else up/left
        if j > 0 and H[i, j] == H[i - 1, j - 1] + (match if db[j - 1] == qc else mismatch):
            i -= 1; j -= 1
        elif H[i, j] == H[i - 1, j] + gopen or H[i, j] == H[i - 1, j] + gext:
            i -= 1
        elif H[i, j] == H[i, j - 1] + gopen or H[i, j] == H[i, j - 1] + gext:
            j -= 1
        else:
            i -= 1
        if H[i, j] <= 0:
            break
    return score, matches, cols, j

f = '/tmp/opencode/rsd/MB1000_M13_DT/A01.rsd'
rsd = RsdFile(f); tr = rsd.extract_traces()
order = rsd.metadata.channel_order
bc = BaseCaller(channel_order=order, trim=False)
call = bc.call(tr)
bases = call.bases
n = len(bases)

# find main body alignment bounds
def sw_strict(q, db):
    na, nb = len(q), len(db)
    H = np.zeros((na + 1, nb + 1), dtype=np.int32)
    for i in range(1, na + 1):
        sc = np.where(np.frombuffer(db.encode(), dtype=np.uint8) == np.frombuffer(q.encode(), dtype=np.uint8)[i - 1], 2, -3)
        C = np.maximum(np.maximum(H[i - 1, 1:] - 5, H[i - 1, :-1] + sc), 0)
        run = np.maximum.accumulate(np.concatenate(([0], C + 5 * np.arange(1, nb + 1))))
        H[i] = run - 5 * np.arange(nb + 1)
    flat = int(H.argmax()); i = flat // (nb + 1); j = flat % (nb + 1)
    return i, j

# head/tail boundaries via the strict alignment to refRC
i_end, j_end = sw_strict(bases, refs['RC'])
# reconstruct: r0 = first aligned read index. simpler: reuse window profile knowledge
r0 = 115
r1 = 585

head = bases[:r0]
tail = bases[r1:]
print(f'head len={len(head)}  tail len={len(tail)}')
for name, q in (('HEAD', head), ('TAIL', tail)):
    print(f'\n=== {name} ({len(q)} bases) ===')
    for strand, db in refs.items():
        score, M, cols, j = sw_blast(q, db)
        if cols == 0:
            print(f'  {strand}: no match')
            continue
        refstart = j - cols
        print(f'  {strand}: score={score} matches={M}/{cols} id={M/cols*100:.1f}% ref[{refstart}:{j}] (mod {R} = {refstart % R})')
