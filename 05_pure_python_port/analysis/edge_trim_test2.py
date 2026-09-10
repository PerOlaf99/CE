import glob, statistics, sys
import numpy as np
sys.path.insert(0,'/workspace')
from megabace.rsd import RsdFile
from megabace.basecall import BaseCaller
ref = open('m13mp18.fasta').read().split('\n',1)[1].replace('\n','').upper()
refRC = ref.translate(str.maketrans('ACGT','TGCA'))[::-1]
refc = refRC+refRC
GAP=-5
def sw(a,b):
    na,nb=len(a),len(b); H=np.zeros((na+1,nb+1),np.int32)
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
print('loading...', flush=True)
data=[]
for f in sorted(glob.glob('MB1000_M13_DT/*.rsd')):
    rsd=RsdFile(f); tr=rsd.extract_traces()
    bc=BaseCaller(channel_order=rsd.metadata.channel_order, trim=True)
    call=bc.call(tr)
    data.append((call.bases, call.positions.astype(np.int64)))
print('loaded', len(data), flush=True)
def run(bases,pos,win,maxbad,lo_frac,hi_frac,minkeep_frac=0.55):
    n=len(pos)
    sp=np.diff(pos)
    med=float(np.median(sp))
    bad=(sp<lo_frac*med)|(sp>hi_frac*med)
    s=0
    while s < n-win:
        if bad[s:s+win].sum()<=maxbad: break
        s+=1
    e=n
    while e-win-1 >= s:
        if bad[max(0,e-win-1):e-1].sum()<=maxbad: break
        e-=1
    if (e-s) < minkeep_frac*n or (e-s)<60:
        return bases,0,0   # signal over-trim; keep none (invalid)
    return bases[s:e], s, n-e
def ev(win,maxbad,lo,hi):
    ids=[]; lens=[]
    for bases,pos in data:
        t,s,te=run(bases,pos,win,maxbad,lo,hi)
        if t==0 and s==0 and te==0:
            ids.append(float('nan')); lens.append(0); continue
        lens.append(len(t))
        p=sw(t,refc)
        if p is None: ids.append(float('nan')); continue
        M=sum(1 for x in p if x[2])
        ids.append(M/len(p)*100)
    ii=[x for x in ids if x==x]
    return (round(statistics.mean(ii),2),round(statistics.median(ii),2),round(statistics.mean(lens),0),len(ii))
print('baseline 93.9/93.82 kept~700')
for win,maxbad in ((40,3),(40,4),(40,5),(60,5),(60,6),(80,7)):
    m,md,l,nn=ev(win,maxbad,0.55,1.7)
    print('win',win,'maxbad',maxbad,'-> mean',m,'median',md,'kept',l,'ok',nn, flush=True)
