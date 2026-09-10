import sys, csv, numpy as np, statistics
sys.path.insert(0,'/workspace')
from megabace.rsd import RsdFile
from megabace.basecall import BaseCaller
ref = open("m13mp18.fasta").read().split("\n",1)[1].replace("\n","").upper()
refRC = ref.translate(str.maketrans("ACGT","TGCA"))[::-1]
refc = refRC + refRC
GAP=-5
def sw(a,b):
    na,nb=len(a),len(b)
    H=np.zeros((na+1,nb+1),np.int32)
    ar=np.frombuffer(a.encode(),np.uint8); br=np.frombuffer(b.encode(),np.uint8)
    for i in range(1,na+1):
        sc=np.where(ar[i-1]==br,2,-3)
        C=np.maximum(np.maximum(H[i-1,1:]+GAP,H[i-1,:-1]+sc),0)
        run=np.maximum.accumulate(np.concatenate(([0],C-GAP*np.arange(1,nb+1))))
        H[i]=run+GAP*np.arange(nb+1)
    flat=int(H.argmax()); i=flat//(nb+1); j=flat%(nb+1)
    if H[i,j]==0: return None
    path=[]
    while i>0 and j>0 and H[i,j]>0:
        if H[i,j]==H[i-1,j-1]+(2 if a[i-1]==b[j-1] else -3): path.append((i-1,j-1,a[i-1]==b[j-1])); i-=1;j-=1
        elif H[i,j]==H[i-1,j]+GAP: path.append((i-1,None,False)); i-=1
        elif H[i,j]==H[i,j-1]+GAP: path.append((None,j-1,False)); j-=1
        else: break
    path.reverse(); return path
def metrics(bases):
    p=sw(bases,refc)
    if p is None: return None
    M=sum(1 for x in p if x[2]); cols=len(p)
    I=sum(1 for x in p if x[0] is not None and x[1] is None)
    D=sum(1 for x in p if x[1] is not None and x[0] is None)
    jv=[x[1] for x in p if x[1] is not None]
    return (len(bases), M/cols*100, I, D, jv[0], jv[-1], cols)
gt={r['well']:r for r in csv.DictReader(open('cimarron_gt_report.csv')) if r['status']=='ok'}
wells=['A01','B02','B06','D06','C04','A08','D05']
variants={
 'base':       dict(),
 'tailExt':    dict(tail_extension=True),
 'tailExt+hd': dict(tail_extension=True, tail_extension_prom=1.2),
}
print('well      variant        readlen  id%     endRef startRef  cols  gt(end/len)')
res={v:[] for v in variants}
for w in wells:
    rsd=RsdFile('MB1000_M13_DT/%s.rsd'%w); tr=rsd.extract_traces()
    for v,cfg in variants.items():
        bc=BaseCaller(channel_order=rsd.metadata.channel_order, trim=True, **cfg)
        c=bc.call(tr)
        m=metrics(c.bases)
        if m is None:
            print(w,v,'NOALIGN'); continue
        rl,idp,I,D,rs,re,cols=m
        g=gt[w]
        print(f'{w:5}  {v:14} {rl:7d} {idp:6.2f}  {re:6d} {rs:6d} {cols:5d}   gt end={g["refRC_end"]} len={g["readlen"]}')