import sys, struct, numpy as np, csv
sys.path.insert(0,'/workspace')
from megabace.rsd import RsdFile
from megabace.basecall import BaseCaller
import megabace.signal as sigmod
from megabace.spectral import deconvolve
ref = open("m13mp18.fasta").read().split("\n",1)[1].replace("\n","").upper()
refRC = ref.translate(str.maketrans("ACGT","TGCA"))[::-1]
refc = refRC + refRC

def abif_get(fn):
    d=open(fn,'rb').read(); res={}
    for i in range(len(d)-28):
        name=d[i:i+4]
        if name not in (b'DATA',b'PLOC',b'PBAS'): continue
        num=struct.unpack('>I',d[i+4:i+8])[0]
        etype=struct.unpack('>H',d[i+8:i+10])[0]
        esize=struct.unpack('>H',d[i+10:i+12])[0]
        cnt=struct.unpack('>I',d[i+12:i+16])[0]
        off=struct.unpack('>I',d[i+20:i+24])[0]
        key=(name,num)
        if key in res: continue
        if not (0<off<len(d) and cnt<20000 and 0<esize<=4): continue
        if esize==1: arr=d[off:off+cnt]
        else: arr=np.frombuffer(d[off:off+cnt*esize],dtype='>i2')
        res[key]=arr
    return res

def swc(a,b):
    import numpy as np
    na,nb=len(a),len(b)
    H=np.zeros((na+1,nb+1),np.int32)
    ar=np.frombuffer(a.encode(),np.uint8); br=np.frombuffer(b.encode(),np.uint8)
    for i in range(1,na+1):
        sc=np.where(ar[i-1]==br,2,-3)
        C=np.maximum(np.maximum(H[i-1,1:]+GAP,H[i-1,:-1]+sc),0)
        run=np.maximum.accumulate(np.concatenate(([0],C-GAP*np.arange(1,nb+1))))
        H[i]=run+GAP*np.arange(nb+1)
    flat=int(H.argmax()); i=flat//(nb+1); j=flat%(nb+1)
    path=[]
    while i>0 and j>0 and H[i,j]>0:
        if H[i,j]==H[i-1,j-1]+(2 if a[i-1]==b[j-1] else -3): path.append((i-1,j-1)); i-=1;j-=1
        elif H[i,j]==H[i-1,j]+GAP: path.append((i-1,None)); i-=1
        elif H[i,j]==H[i,j-1]+GAP: path.append((None,j-1)); j-=1
        else: break
    path.reverse(); return path
GAP=-5

w='A01'
t=abif_get('/tmp/opencode/cimarron_gt/MB1000_M13_DT_Cp312_MD1/ABD/%s.abd'%w)
raw=np.stack([t[(b'DATA',i)] for i in (1,2,3,4)]).astype(np.float64)
proc=np.stack([t[(b'DATA',i)] for i in (9,10,11,12)]).astype(np.float64)
ploc=t[(b'PLOC',1)].astype(np.int64)
seq=t[(b'PBAS',1)]; seq=seq.decode('ascii','replace') if isinstance(seq,bytes) else seq.tobytes().decode('ascii','replace')
print('ABD raw shape',raw.shape,'proc shape',proc.shape,'ploc',ploc.shape,len(seq))
# our rsd raw compare
rsd=RsdFile('MB1000_M13_DT/%s.rsd'%w); tr=rsd.extract_traces().astype(np.float64)
print('rsd shape',tr.shape)
# compare rsd trace vs ABD raw channels
for ch in range(4):
    a=raw[ch]; b=tr[ch]
    # correlation ignoring scale
    if a.size==b.size:
        print('chan',ch,'corr rsd vs abd-raw',np.corrcoef(a,b)[0,1].round(3),'ratio max', (a.max()/b.max()).round(2))
    else:
        print('chan',ch,'length mismatch')
# raw vs processed total cross-corr (find offset & check)
tot_r=raw.sum(0); tot_p=proc.sum(0)
c=np.correlate(tot_p-np.mean(tot_p),tot_r-np.mean(tot_r),mode='full')
lag=np.argmax(c)-(len(tot_p)-1)
print('proc vs raw best lag',lag)
# PLOC scale check
print('ploc min/max',ploc.min(),ploc.max(),'proc len',proc.shape[1])
# GT seq align to refc to get template coords per base
p=swc(seq,refc)
rmap={}
for i,(rb,rc) in enumerate(p):
    if rb is not None and rc is not None: rmap[rb]=rc
print('gt aligned',len([1 for x in p if x[1] is not None]),'bases, ref span',p[0][1],p[-1][1])
# At each GT base, scan=ploc[i]; examine OUR processing at raw scan? need raw mapping
# quick: compare proc channel dominant at ploc to GT letter to validate proc
order=bc_order='TGCA'
seqb=seq
print('check GT letter vs proc-dominant at ploc:')
ok=0;tot=0
for i,b in enumerate(seq):
    s=int(ploc[i])
    if not (0<=s<proc.shape[1]): continue
    col=proc[:,s]
    dom=col.argmax(); tot+=1
    if order[dom]==b: ok+=1
print('%d/%d (%.0f%%)'%(ok,tot,100*ok/max(tot,1)))
