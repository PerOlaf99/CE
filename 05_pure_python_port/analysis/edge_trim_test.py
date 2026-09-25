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
def run(bases,pos,win,maxbad,lo_frac,hi_frac):
    n=len(pos)
    sp=np.diff(pos)
    med=float(np.median(sp))
    a_lo=lo_frac*med; a_hi=hi_frac*med
    # anomaly mask on gaps
    bad=(sp<a_lo)|(sp>a_hi)
    # drop first call while window of first `win` gaps has >maxbad bad
    s=0
    while True:
        endg=min(len(bad), s+win)
        if endg-s<3: break
        if bad[s:endg].sum()<=maxbad: break
        s+=1
    e=n
    # from tail: bad gap index before dropping call e-1 is e-2
    while True:
        # consider last `win` gaps before call e
        lo_g=max(0,(e-1)-win)
        hi_g=e-1
        if hi_g-lo_g<3 or hi_g>len(bad): 
            break
        seg=bad[lo_g:hi_g]
        if seg.sum()<=maxbad: break
        e-=1
    if e-s<40: s,e=0,n
    return bases[s:e]
def ev(win,maxbad,lo_frac,hi_frac):
    ids=[]; lens=[]
    for bases,pos in data:
        t=run(bases,pos,win,maxbad,lo_frac,hi_frac)
        lens.append(len(t))
        p=sw(t,refc)
        if p is None: continue
        M=sum(1 for x in p if x[2])
        ids.append(M/len(p)*100)
    return (round(statistics.mean(ids),2),round(statistics.median(ids),2),round(statistics.mean(lens),0))
print('baseline 93.9 mean, median kept ~700')
for maxbad in (3,5,8):
    for lo,hi in ((0.5,1.8),(0.55,1.7)):
        m,md,l=ev(20,maxbad,lo,hi)
        print('win20 maxbad',maxbad,'bounds',lo,hi,'-> mean',m,'median',md,'kept',l, flush=True)
