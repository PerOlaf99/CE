import struct, numpy as np, glob, csv, statistics, sys, os
ref = open("/tmp/opencode/rsd/m13mp18.fasta").read().split("\n",1)[1].replace("\n","").upper()
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

def read_pbas(fn):
    d=open(fn,'rb').read()
    cand=[]
    for i in range(len(d)-28):
        name=d[i:i+4]
        if name!=b'PBAS': continue
        num=struct.unpack('>I',d[i+4:i+8])[0]
        cnt=struct.unpack('>I',d[i+12:i+16])[0]
        off=struct.unpack('>I',d[i+20:i+24])[0]
        if num==1 and 0<off<len(d) and cnt<10000:
            return d[off:off+cnt].decode('ascii','replace')
    return None

rows=[]; ids=[]
os.makedirs("cimarron_calls", exist_ok=True)
for f in sorted(glob.glob("/tmp/opencode/cimarron_gt/MB1000_M13_DT_Cp312_MD1/ABD/*.abd")):
    w = os.path.basename(f)[:-4]
    s = read_pbas(f)
    if s is None:
        rows.append((w, 0, 0, 0, 0, 0, 0, 0, 0, 'NOPBAS')); continue
    with open(f"cimarron_calls/{w}.fasta","w") as fh:
        fh.write(f">{w}\n{s}\n")
    p = sw(s, refc)
    if p is None:
        rows.append((w, len(s), s.count('N'), 0, 0, 0, 0, 0, 0, 'NOALIGN')); continue
    M=sum(1 for x in p if x[2]); cols=len(p)
    I=sum(1 for x in p if x[0] is not None and x[1] is None)
    D=sum(1 for x in p if x[1] is not None and x[0] is None)
    jv=[x[1] for x in p if x[1] is not None]
    idp=M/cols*100; ids.append(idp)
    rows.append((w, len(s), s.count('N'), round(idp,1), I, D, jv[0], jv[-1], cols, 'ok'))
with open("cimarron_gt_report.csv","w",newline="") as fh:
    wr=csv.writer(fh)
    wr.writerow(["well","readlen","N","pct_identity","insertions","deletions","refRC_start","refRC_end","cols","status"])
    wr.writerows(rows)
if ids:
    print(f"GT: {len(rows)} wells (ok {len(ids)}); mean id {statistics.mean(ids):.2f}% median {statistics.median(ids):.2f}%  mean readlen {statistics.mean([r[1] for r in rows if r[9]=='ok']):.0f}")
