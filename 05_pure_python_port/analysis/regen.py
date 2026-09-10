import sys, glob, os, csv, statistics
sys.path.insert(0,'/workspace')
from megabace.rsd import RsdFile
from megabace.basecall import BaseCaller

ref = open("m13mp18.fasta").read().split("\n",1)[1].replace("\n","").upper()
refRC = ref.translate(str.maketrans("ACGT","TGCA"))[::-1]
refc = refRC + refRC
GAP=-5
def sw(a, b):
    na, nb = len(a), len(b)
    H = np.zeros((na+1, nb+1), dtype=np.int32)
    ar = np.frombuffer(a.encode(), dtype=np.uint8); br = np.frombuffer(b.encode(), dtype=np.uint8)
    for i in range(1, na+1):
        sc = np.where(ar[i-1]==br, 2, -3)
        C = np.maximum(np.maximum(H[i-1,1:]+GAP, H[i-1,:-1]+sc), 0)
        run = np.maximum.accumulate(np.concatenate(([0], C - GAP*np.arange(1,nb+1))))
        H[i] = run + GAP*np.arange(nb+1)
    flat = int(H.argmax()); i = flat//(nb+1); j = flat%(nb+1)
    if H[i,j]==0: return None
    path=[]
    while i>0 and j>0 and H[i,j]>0:
        if H[i,j]==H[i-1,j-1]+(2 if a[i-1]==b[j-1] else -3): path.append((i-1,j-1,a[i-1]==b[j-1])); i-=1; j-=1
        elif H[i,j]==H[i-1,j]+GAP: path.append((i-1,None,False)); i-=1
        elif H[i,j]==H[i,j-1]+GAP: path.append((None,j-1,False)); j-=1
        else: break
    path.reverse(); return path

import numpy as np
os.makedirs("basecalls", exist_ok=True)
rows=[]; ids=[]
for f in sorted(glob.glob("MB1000_M13_DT/*.rsd")):
    w = f.split("/")[-1][:-4]
    rsd = RsdFile(f)
    tr = rsd.extract_traces()
    bc = BaseCaller(channel_order=rsd.metadata.channel_order, trim=True)
    call = bc.call(tr)
    with open(f"basecalls/{w}.fasta","w") as fh:
        fh.write(f">{w} MegaBACE M13mp18\n{call.bases}\n")
    with open(f"basecalls/{w}.fastq","w") as fh:
        fh.write(call.fastq_record(w)+"\n")
    path = sw(call.bases, refc)
    if path is None:
        rows.append((w, len(call.bases), call.bases.count('N'), 0, 0, 0, 0, 0, 0)); continue
    M=sum(1 for x in path if x[2]); cols=len(path)
    I=sum(1 for x in path if x[0] is not None and x[1] is None)
    D=sum(1 for x in path if x[1] is not None and x[0] is None)
    jv=[x[1] for x in path if x[1] is not None]
    idp=M/cols*100; ids.append(idp)
    rows.append((w, len(call.bases), call.bases.count('N'), round(idp,1), I, D, jv[0], jv[-1], cols))
with open("validation_report.csv","w",newline="") as fh:
    wr=csv.writer(fh)
    wr.writerow(["well","calls","N","pct_identity","insertions","deletions","refRC_start","refRC_end","cols"])
    wr.writerows(rows)
print(f"regenerated {len(rows)} wells; mean id {statistics.mean(ids):.1f}% median {statistics.median(ids):.1f}%")
