import sys
sys.path.insert(0, '/workspace')
import numpy as np
from megabace.rsd import RsdFile
from megabace.basecall import BaseCaller

ref = open('/tmp/opencode/rsd/m13mp18.fasta').read().split('\n', 1)[1].replace('\n', '').upper()
refRC = ref.translate(str.maketrans('ACGT', 'TGCA'))[::-1]
refc = refRC + refRC          # RC strand, double to cover circular wrap
refF = ref + ref              # forward strand, double
R = len(ref)

f = '/tmp/opencode/rsd/MB1000_M13_DT/A01.rsd'
rsd = RsdFile(f); tr = rsd.extract_traces()
order = rsd.metadata.channel_order
bc = BaseCaller(channel_order=order, trim=False)
call = bc.call(tr)
bases = call.bases
n = len(bases)
print('untrimmed read length:', n)

W = 30
step = 5
fr = np.frombuffer(refF.encode(), dtype=np.uint8)
frc = np.frombuffer(refc.encode(), dtype=np.uint8)

def best_match(win, sb):
    # return (identity, ref_position) of best window match
    w = np.frombuffer(win.encode(), dtype=np.uint8)
    eq = (sb[np.arange(len(win))[:, None] + np.arange(sb.size - len(win) + 1)] == w[:, None])
    scores = eq.sum(axis=0)
    i = int(np.argmax(scores))
    return scores[i] / len(win), i

print('pos  len  best_strand  best_pos  id%')
rows = []
for start in range(0, n - W + 1, step):
    win = bases[start:start + W]
    idF, posF = best_match(win, fr)
    idC, posC = best_match(win, frc)
    if idC >= idF:
        strand, pos, idv = 'RC', posC, idC
    else:
        strand, pos, idv = 'F', posF, idF
    rows.append((start, strand, pos % R, idv))
    print(f'{start:5d} {W:4d} {strand:7s} {pos % R:5d} {idv*100:5.1f}%')
