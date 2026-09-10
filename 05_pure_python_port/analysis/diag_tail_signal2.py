import sys, numpy as np, csv
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
        if H[i,j]==H[i-1,j-1]+(2 if a[i-1]==b[j-1] else -3): path.append((i-1,j-1,a[i-1]==b[j-1])); i-=1;j-=1
        elif H[i,j]==H[i-1,j]+GAP: path.append((i-1,None,False)); i-=1
        elif H[i,j]==H[i,j-1]+GAP: path.append((None,j-1,False)); j-=1
        else: break
    path.reverse(); return path

w='A01'
rsd=RsdFile('MB1000_M13_DT/%s.rsd'%w); tr=rsd.extract_traces().astype(np.float64)
bc=BaseCaller(channel_order=rsd.metadata.channel_order, trim=False)
c=bc.call(tr)
print('trace npts',tr.shape[1],'caller channels order',bc.channel_order,'total calls(no trim)',len(c.bases))
p=sw(c.bases,refc)
matched=[(x[0],x[1]) for x in p if x[0] is not None and x[1] is not None]
print('aligned cols',len(p),'matched',len(matched),'id',sum(1 for x in p if x[2])/len(p)*100)
# our scan position for read base idx
readpos={i:c.positions[i] for i in range(len(c.bases))}
pairs=[(readpos[i],rc) for i,rc in matched]
# fit scan~ref in last 80 matched
P=np.asarray([(rc,sp) for sp,rc in pairs])
P=P[P[:,0].argsort()]
tail=P[-80:]
A=np.polyfit(tail[:,0],tail[:,1],1)
print('tail model scan=%.2f*ref%.0f+%.1f'%(A[0],0,A[1]) if False else 'tail model slope %.3f intercept %.1f (per-ref-base scan %.2f)'%(A[0],A[1],A[0]))
gref_end=1779; gref_start=964
s_end=A[0]*gref_end+A[1]; s_start=A[0]*gref_start+A[1]
print('predicted scan range for GT span (%d..%d): %.0f..%.0f  (our calls span %d..%d)'%(gref_start,gref_end,s_start,s_end,c.positions[0],c.positions[-1]))
# examine our norm channels in predicted window
base=sigmod.subtract_baseline_multi(tr)
sep=deconvolve(base, bc.matrix, bc.estimate_matrix)
norm=sigmod.normalize_channels(sep)
lo=max(0,int(s_start)); hi=min(norm.shape[1],int(s_end))
print('window scans %d..%d len %d'%(lo,hi,hi-lo))
seg=norm[:,lo:hi]
tot=seg.sum(axis=0)
# peak detection at very low prominence on sum
from scipy.signal import find_peaks
# use module's detect_peaks if it accepts 1d
try:
    pk,_=sigmod.detect_peaks(tot,min_distance=2,min_prominence=0.005)
except Exception as e:
    from scipy.signal import find_peaks
    pk,_=find_peaks(tot,distance=2,prominence=0.005)
print('peaks found in GT-window by sum: %d'%pk.size)
# letters our caller actually called inside window (trim=False bases whose position in window)
wbase=[(b,c.positions[i]) for i,b in enumerate(c.bases) if lo<=c.positions[i]<hi]
print('our calls inside predicted GT window: %d'%len(wbase))
print('first 10:',wbase[:10])
# per-base: GT read for those template coords
gts=open('cimarron_calls/%s.fasta'%w).read().split('\n',1)[1].replace('\n','')
gpath=sw(gts,refc)
cmap={}
for x in gpath:
    if x[0] is not None and x[1] is not None: cmap[x[1]]=gts[x[0]]
tgt=[(rc,cmap.get(rc)) for rc in range(gref_start,gref_end+1)]
known=[(rc,b) for rc,b in tgt if b]
print('GT bases known in window:',len(known))
# dominant norm channel at predicted scan for each GT base, compare letters
order=bc.channel_order
def scan_for(rc):
    return int(A[0]*rc+A[1])
match=0; totc=0
for rc,b in known:
    s=scan_for(rc)
    if not (0<=s<norm.shape[1]): continue
    col=norm[:,s]
    dom=col.argmax()
    totc+=1
    if order[dom]==b: match+=1
print('at predicted scans, norm-dominant channel == GT letter: %d/%d (%.0f%%)'%(match,totc,100*match/max(totc,1)))
