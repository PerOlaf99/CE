import sys, struct, numpy as np, itertools
sys.path.insert(0,'/workspace')
from megabace.rsd import RsdFile
from megabace.basecall import BaseCaller
import megabace.signal as sigmod
from megabace.spectral import deconvolve
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
        if H[i,j]==H[i-1,j-1]+(2 if a[i-1]==b[j-1] else -3): path.append((i-1,j-1)); i-=1;j-=1
        elif H[i,j]==H[i-1,j]+GAP: path.append((i-1,None)); i-=1
        elif H[i,j]==H[i,j-1]+GAP: path.append((None,j-1)); j-=1
        else: break
    path.reverse(); return path
def abif_get(fn):
    d=open(fn,'rb').read(); res={}
    for i in range(len(d)-28):
        name=d[i:i+4]
        if name not in (b'DATA',b'PLOC',b'PBAS'): continue
        num=struct.unpack('>I',d[i+4:i+8])[0]
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

def win_dom(mat,s,half):
    lo=max(0,int(s-half)); hi=min(mat.shape[1],int(s+half)+1)
    return int(mat[:,lo:hi].max(axis=1).argmax())

for w in ['A01','B02','D06']:
    t=abif_get('/tmp/opencode/cimarron_gt/MB1000_M13_DT_Cp312_MD1/ABD/%s.abd'%w)
    ploc=t[(b'PLOC',1)].astype(np.int64)
    gseq=t[(b'PBAS',1)]; gseq=gseq.decode('ascii','replace') if isinstance(gseq,bytes) else gseq.tobytes().decode()
    proc=np.stack([t[(b'DATA',i)] for i in (9,10,11,12)]).astype(np.float64)
    # channel permutation for proc: which perm maps proc channels to ACGT letters
    best=None
    for perm in itertools.permutations(range(4)):
        ok=0
        for i,b in enumerate(gseq):
            s=int(ploc[i])
            if not (0<=s<proc.shape[1]): continue
            if perm[int(proc[:,s].argmax())]==b: ok+=1
        if best is None or ok>best[0]: best=(ok,perm)
    print('== %s proc-dominant vs GT best %d/%d perm(letter<-[channel]) %s'%(w,best[0],len(gseq),'ACGT'))
    _,(perm)=best
    rsd=RsdFile('MB1000_M13_DT/%s.rsd'%w); tr=rsd.extract_traces().astype(np.float64)
    order=rsd.metadata.channel_order.upper()
    bc=BaseCaller(channel_order=order, trim=False)
    c=bc.call(tr)
    p=sw(c.bases,refc)
    our={}
    for i,(rb,rc) in enumerate(p):
        if rb is not None and rc is not None: our[rc]=i
    gp=sw(gseq,refc)
    gtmap={}
    for i,(rb,rc) in enumerate(gp):
        if rb is not None and rc is not None: gtmap[rc]=(i,gseq[rb])
    anchors=[]
    for rc in sorted(set(our)&set(gtmap)):
        oi=our[rc]; gi,_=gtmap[rc]
        anchors.append((int(c.positions[oi]),int(ploc[gi]),rc))
    anchors.sort(key=lambda x:x[1])
    arr_raw=np.asarray([a[0] for a in anchors]); arr_ps=np.asarray([a[1] for a in anchors]); arr_rc=np.asarray([a[2] for a in anchors])
    # piecewise interp proc->raw; extrapolate beyond using last local slope
    def raw_of(ps):
        if ps<arr_ps[0]: return arr_raw[0]
        if ps>arr_ps[-1]:
            i=min(len(arr_ps)-1, len(arr_ps)-2) if len(arr_ps)>=2 else 0
            i=max(i,0)
            # robust local slope from last 40 anchors
            a=arr_ps[-40:]; b=arr_raw[-40:]
            slope=np.polyfit(a,b,1)[0]
            return arr_raw[-1]+(ps-arr_ps[-1])*slope
        return np.interp(ps,arr_ps,arr_raw)
    base=sigmod.subtract_baseline_multi(tr)
    sep=deconvolve(base, bc.matrix, bc.estimate_matrix)
    norm=sigmod.normalize_channels(sep)
    spacing=float(np.median(np.diff(ploc)))
    half=max(1,int(0.4*spacing))
    def eval_rc(rcs,label):
        ok=0;A=0;tot=0
        for rc in rcs:
            if rc not in gtmap: continue
            gi,b=gtmap[rc]; s=raw_of(int(ploc[gi]))
            if not (0<=s<norm.shape[1]): continue
            d=win_dom(norm,s,half); tot+=1
            if order[d]==b: ok+=1
            if order[d]=='A': A+=1
        print('   %-9s win==GT %d/%d (%.0f%%) A-arg %d (%.0f%%)'%(label,ok,tot,100*ok/max(tot,1),A,100*A/max(tot,1)))
    our_ref_max=max(our.keys())
    interior=[rc for rc in arr_rc if rc>our_ref_max-300 and rc<=our_ref_max]
    tail=[rc for rc in sorted(gtmap) if rc>our_ref_max]
    eval_rc(interior,'interior'); eval_rc(tail,'TAIL')
