import glob, statistics, sys
import numpy as np
sys.path.insert(0,'/workspace')
from megabace.rsd import RsdFile
from megabace.basecall import BaseCaller
from megabace import signal as sigmod
from megabace.spectral import deconvolve
ref = open('/tmp/opencode/rsd/m13mp18.fasta').read().split('\n',1)[1].replace('\n','').upper()
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
wells=sorted(glob.glob('MB1000_M13_DT/*.rsd'))
data=[]
for f in wells:
    rsd=RsdFile(f)
    tr=rsd.extract_traces()
    base=sigmod.subtract_baseline_multi(tr)
    sep=sigmod.normalize_channels(deconvolve(base,None,True))
    bc=BaseCaller(channel_order=rsd.metadata.channel_order, trim=True)
    call=bc.call(tr)
    amp=np.max(sep,axis=0)
    p=call.positions.astype(int)
    av=np.array([amp[min(len(amp)-1,max(0,x))] for x in p])
    data.append((call.bases, av, call.qualities))
def ev(frac, run=12):
    ids=[]
    for bases,av,q in data:
        mx=np.percentile(av,99.5)
        thr=frac*mx
        n=len(bases)
        # left boundary: first index where av>=thr sustained for run bases
        i=0
        while i<n:
            if av[i]>=thr and i+run<n and np.all(av[i:i+run]>=thr*0.8): break
            i+=1
        j=n
        while j>i:
            if av[j-1]>=thr and j-run>=i and np.all(av[max(i,j-run):j]>=thr*0.8): break
            j-=1
        if j-i<40: continue
        t=bases[i:j]
        pth=sw(t,refc)
        if pth is None: continue
        M=sum(1 for x in pth if x[2])
        ids.append(M/len(pth)*100)
    return round(statistics.mean(ids),2), round(statistics.median(ids),2), len(ids)
print('no-trim baseline was 93.9/93.82')
for fr in (0.02,0.05,0.08,0.12,0.18,0.25):
    m,med,nn=ev(fr)
    print('frac',fr,'mean',m,'median',med,'n',nn)
