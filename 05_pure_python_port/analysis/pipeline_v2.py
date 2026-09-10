import numpy as np
from megabace.basecall import BaseCaller, _noise_level
from megabace import signal as sigmod
from megabace import spectral
from megabace.rsd import RsdFile

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
    path=[]
    while i>0 and j>0 and H[i,j]>0:
        if H[i,j]==H[i-1,j-1]+(2 if a[i-1]==b[j-1] else -3): path.append((i-1,j-1,a[i-1]==b[j-1])); i-=1; j-=1
        elif H[i,j]==H[i-1,j]+GAP: path.append((i-1,None,False)); i-=1
        elif H[i,j]==H[i,j-1]+GAP: path.append((None,j-1,False)); j-=1
        else: break
    path.reverse(); return path

def score(peaks, chans, order):
    s = "".join(order[c] for c in chans)
    path = sw(s, refc)
    if path is None: return dict(id=0,cols=0,I=0,D=0,M=0,calls=len(s),first=0,last=0)
    M=sum(1 for x in path if x[2]); cols=len(path)
    I=sum(1 for x in path if x[0] is not None and x[1] is None)
    D=sum(1 for x in path if x[1] is not None and x[0] is None)
    jv=[x[1] for x in path if x[1] is not None]
    return dict(id=M/cols*100, cols=cols, I=I, D=D, M=M, calls=len(s), first=jv[0], last=jv[-1])

def primary_detect(norm, order, smooth_w=5, pm=8.0, fm=2.0):
    cands=[]
    for c in range(4):
        ch = sigmod.smooth(norm[c], window=smooth_w)
        noise = _noise_level(ch)
        pk,_ = sigmod.detect_peaks(ch, min_distance=2, min_prominence=max(0.001,pm*noise))
        if pk.size==0: continue
        heights=ch[pk]; q99=np.percentile(heights,99); floor=max(0.07*q99,6.0*noise)*fm
        for p in pk[heights>=floor]:
            if norm[c,p]>=norm[:,p].max(): cands.append((int(p),c))
    cands.sort(key=lambda x:x[0]); kept=[]; i=0
    while i<len(cands):
        j=i
        while j+1<len(cands) and cands[j+1][0]-cands[i][0]<=3: j+=1
        kept.append(max(cands[i:j+1],key=lambda pc:norm[pc[1],pc[0]])); i=j+1
    return np.array([p for p,_ in kept],int), np.array([c for _,c in kept],int)

def exp_spacing(peaks, k=41):
    gaps = np.diff(peaks.astype(float))
    if gaps.size==0: return np.array([])
    exp = np.array([np.median(gaps[max(0,i-k):min(gaps.size,i+k+1)]) for i in range(gaps.size)])
    med = np.median(gaps)
    return np.clip(exp, 0.5*med, 2.0*med)

def gap_fill(norm, peaks, chans, bc, gap_frac=1.3, purity=0.5, min_sep_frac=0.4):
    gaps = np.diff(peaks.astype(float))
    exp = exp_spacing(peaks)
    if exp.size==0: return peaks, chans
    med = np.median(gaps)
    added=[]
    for i in range(peaks.size-1):
        g=gaps[i]; se=exp[min(i,exp.size-1)]
        if not (g>gap_frac*se and g<8*se): continue
        nmiss=int(round(g/se))-1
        if nmiss<1: continue
        lo,hi=int(peaks[i]),int(peaks[i+1])
        found=[]
        for c in range(4):
            ch = sigmod.smooth(norm[c], window=3)
            nl = _noise_level(ch)
            pk,_ = sigmod.detect_peaks(ch, min_distance=1, min_prominence=max(0.001,2.0*nl))
            if pk.size==0: continue
            hh=ch[pk]; q99=np.percentile(hh,99); fl=max(0.07*q99,6.0*nl)*0.7
            for p,h in zip(pk,hh):
                if lo<p<hi and h>=fl:
                    v=norm[:,max(0,p-1):p+2].max(axis=1)
                    if v[c]>=purity*v.max(): found.append((int(p),c,norm[c,int(p)]))
        found.sort(key=lambda x:x[2],reverse=True)
        chosen=[]
        for (p,c,h) in found:
            if len(chosen)>=nmiss: break
            if all(abs(p-q)>=max(2,int(min_sep_frac*med)) for q,_ in chosen): chosen.append((p,c))
        added.extend(chosen)
    if not added: return peaks, chans
    allp=np.concatenate([peaks,np.array([x[0] for x in added],int)])
    allc=np.concatenate([chans,np.array([x[1] for x in added],int)])
    o=np.argsort(allp); mp=[]; mc=[]; i=0
    while i<len(o):
        j=i
        while j+1<len(o) and allp[o[j+1]]-allp[o[i]]<=3: j+=1
        best=max(o[i:j+1],key=lambda idx: norm[allc[idx],allp[idx]])
        mp.append(allp[best]); mc.append(allc[best]); i=j+1
    return bc._cull_by_spacing(norm, np.array(mp,int), np.array(mc,int))

def window_reassign(norm, peaks, chans, order, win=5, min_gain=1.2):
    # for each peak, check window dominance; if a different channel dominates by min_gain and has a local max within win, reassign
    out_p=[]; out_c=[]
    for p, c in zip(peaks, chans):
        lo=max(0,p-win); hi=min(norm.shape[1],p+win+1)
        amps = norm[:,lo:hi].max(axis=1)
        dom = int(np.argmax(amps))
        if dom!=c and amps[dom] > min_gain*amps[c] + 1e-9:
            # find dom channel local max near p
            seg = norm[dom, lo:hi]
            pos = lo + int(np.argmax(seg))
            out_p.append(pos); out_c.append(dom)
        else:
            out_p.append(p); out_c.append(c)
    # re-sort
    o=np.argsort(out_p)
    return np.array([out_p[i] for i in o],int), np.array([out_c[i] for i in o],int)

def gap_fill_samech(norm, peaks, chans, bc, gap_frac=1.3, purity=0.5, min_sep_frac=0.4, require_same_channel=True):
    gaps = np.diff(peaks.astype(float))
    exp = exp_spacing(peaks)
    if exp.size==0: return peaks, chans
    med = np.median(gaps)
    added=[]
    for i in range(peaks.size-1):
        g=gaps[i]; se=exp[min(i,exp.size-1)]
        if not (g>gap_frac*se and g<8*se): continue
        nmiss=int(round(g/se))-1
        if nmiss<1: continue
        lo,hi=int(peaks[i]),int(peaks[i+1])
        ca, cb = chans[i], chans[i+1]
        found=[]
        for c in range(4):
            # same-channel constraint: candidate must be in a flanking channel
            if require_same_channel and c not in (ca, cb): continue
            ch = sigmod.smooth(norm[c], window=3)
            nl = _noise_level(ch)
            pk,_ = sigmod.detect_peaks(ch, min_distance=1, min_prominence=max(0.001,2.0*nl))
            if pk.size==0: continue
            hh=ch[pk]; q99=np.percentile(hh,99); fl=max(0.07*q99,6.0*nl)*0.7
            for p,h in zip(pk,hh):
                if lo<p<hi and h>=fl:
                    v=norm[:,max(0,p-1):p+2].max(axis=1)
                    if v[c]>=purity*v.max(): found.append((int(p),c,norm[c,int(p)]))
        found.sort(key=lambda x:x[2],reverse=True)
        chosen=[]
        for (p,c,h) in found:
            if len(chosen)>=nmiss: break
            if all(abs(p-q)>=max(2,int(min_sep_frac*med)) for q,_ in chosen): chosen.append((p,c))
        added.extend(chosen)
    if not added: return peaks, chans
    allp=np.concatenate([peaks,np.array([x[0] for x in added],int)])
    allc=np.concatenate([chans,np.array([x[1] for x in added],int)])
    o=np.argsort(allp); mp=[]; mc=[]; i=0
    while i<len(o):
        j=i
        while j+1<len(o) and allp[o[j+1]]-allp[o[i]]<=3: j+=1
        best=max(o[i:j+1],key=lambda idx: norm[allc[idx],allp[idx]])
        mp.append(allp[best]); mc.append(allc[best]); i=j+1
    return bc._cull_by_spacing(norm, np.array(mp,int), np.array(mc,int))
