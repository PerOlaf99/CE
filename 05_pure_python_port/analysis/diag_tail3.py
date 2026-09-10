import sys, struct, numpy as np, csv
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

for w in ['A01','B02']:
    t=abif_get('/tmp/opencode/cimarron_gt/MB1000_M13_DT_Cp312_MD1/ABD/%s.abd'%w)
    ploc=t[(b'PLOC',1)].astype(np.int64)
    gseq=t[(b'PBAS',1)]; gseq=gseq.decode('ascii','replace') if isinstance(gseq,bytes) else gseq.tobytes().decode()
    rsd=RsdFile('MB1000_M13_DT/%s.rsd'%w); tr=rsd.extract_traces().astype(np.float64)
    order=rsd.metadata.channel_order.upper()
    bc=BaseCaller(channel_order=order, trim=False)
    c=bc.call(tr)
    p=sw(c.bases,refc)
    # our matched: readIdx -> refCoord
    our={}
    for i,(rb,rc) in enumerate(p):
        if rb is not None and rc is not None: our[rc]=i
    gp=sw(gseq,refc)
    gtmap={}
    for i,(rb,rc) in enumerate(gp):
        if rb is not None and rc is not None: gtmap[rc]=(i, gseq[rb])
    # anchor pairs rawScan(our position of ref) vs procScan(ploc[gt idx])
    pairs=[]
    for rc in sorted(set(our)&set(gtmap)):
        oi=our[rc]; gi,_=gtmap[rc]
        pairs.append((int(c.positions[oi]), int(ploc[gi]), rc))
    pairs=np.asarray(pairs)
    # fit rawScan ~ f(procScan) via poly1 over anchors (should be monotonic across read)
    A=np.polyfit(pairs[:,1], pairs[:,0], 2)
    pred=lambda ps:int(np.polyval(A,ps))
    # sanity: r2
    fitv=np.polyval(A,pairs[:,1])
    r2=1-np.sum((fitv-pairs[:,0])**2)/np.sum((pairs[:,0]-pairs[:,0].mean())**2)
    print(f'== {w}: anchors {len(pairs)} poly2 r2 {r2:.4f} our order {order} len(calls no-trim) {len(c.bases)}')
    # norm channels in rsd coords
    base=sigmod.subtract_baseline_multi(tr)
    sep=deconvolve(base, bc.matrix, bc.estimate_matrix)
    norm=sigmod.normalize_channels(sep)
    # GT bases in tail beyond our aligned end
    our_ref_max=max(our.keys())
    tail=[rc for rc in sorted(gtmap) if rc>our_ref_max]
    print('  our aligned ref end',our_ref_max,'GT tail bases beyond:',len(tail),'(e.g. to',max(tail) if tail else 0,')')
    # per tail GT base: predicted raw scan; check our norm dominant & letter
    def win_dom(col_norm, s, half):
        lo=max(0,s-half); hi=min(col_norm.shape[1],s+half+1)
        mx=col_norm[:,lo:hi].max(axis=1)
        return int(mx.argmax())
    def eval_span(rcs, label, half_frac):
        matched=0; tot=0; afrac=0; other_ok=0
        for rc in rcs:
            if rc not in gtmap: continue
            gi,gbase=gtmap[rc]
            ps=int(ploc[gi]); s=pred(ps)
            if s<0 or s>=norm.shape[1]: continue
            col=norm[:,s]
            half=max(1,int(half_frac*int(np.median(np.diff(ploc)))))
            dom=win_dom(norm,s,half); tot+=1
            if order[dom]=='A': afrac+=1
            if order[dom]==gbase: matched+=1
            elif order[dom]!='A' and gbase!='A': other_ok+=1
        print('  %-8s norm-win==GT %d/%d (%.0f%%) A-dominant %d (%.0f%%)'%(
            label,matched,tot,100*matched/max(tot,1),afrac,100*afrac/max(tot,1)))
    interior=[rc for rc in sorted(gtmap) if our_ref_max-300<rc<=our_ref_max]
    eval_span(interior,'interior',0.5)
    tail=[rc for rc in sorted(gtmap) if rc>our_ref_max]
    eval_span(tail,'TAIL',0.5)
    if tail:
        matched=0; mism=[]; tot=0; none=0
        for rc in tail:
            gi,gbase=gtmap[rc]
            ps=int(ploc[gi]); s=pred(ps)
            if s<0 or s>=norm.shape[1]: none+=1; continue
            col=norm[:,s]
            half=max(1,int(0.5*np.median(np.diff(ploc))))
            dom=win_dom(norm,s,half); tot+=1
            if order[dom]==gbase: matched+=1
            else: mism.append((rc,gbase,order[dom],ps,s))
        print('  TAIL(win): %d/%d'%(matched,tot))
        for m in mism[:6]:
            print('    refRC',m[0],'GT',m[1],'our',m[2],'proc',m[3],'raw',m[4])
