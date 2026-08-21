import sys, os, json, numpy as np
sys.path.insert(0, '/media/per/78B0C7DE1FA7081C/electropherogram')
from PyQt5.QtWidgets import QApplication
import sequencing_gui_V15 as gui
from extract_training_data import parse_rsd, parse_esd

app = QApplication([])
w = gui.SequencingGUI()
BASE = '/media/per/78B0C7DE1FA7081C/electropherogram/MB1000_M13_DT'
esd_dir = os.path.join(BASE, 'MB1000_M13_DT_Cp312_MD1')
WELLS = ['A01','A02','A03','A04','A06','A08','B01','B05']

def load(well, mob=[5,10,10,10], prom=0.20, norm=800):
    df = parse_rsd(os.path.join(BASE, f'{well}.rsd'))
    w.rsd_raw = df[['Channel1','Channel2','Channel3','Channel4']].values.astype(np.float64)
    w.x_rsd = np.arange(len(w.rsd_raw))
    ed = parse_esd(os.path.join(esd_dir, f'{well}.esd'))
    w.esd_data = ed
    w._load_esd_traces(os.path.join(esd_dir, f'{well}.esd'))
    w.x_esd = np.arange(len(w.esd_traces))
    w.load_settings_from_dict(json.load(open('/media/per/78B0C7DE1FA7081C/electropherogram/settingsV10.json')))
    for ch, v in enumerate(mob): w.mobility_spins[ch].setValue(v)
    w.prominence_spin.setValue(int(round(prom*1000)))
    w.norm_window_spin.setValue(norm)
    sep = w._process()[4]; shifts = w._get_mobility_shifts(); reg = w._get_region(sep)
    return sep, shifts, reg, ed['sequence']

def greedy_env(sep, shifts, reg, window=5, min_frac=0.20, norm_window=800):
    n = len(sep)
    normed = np.empty_like(sep)
    for ch in range(4):
        sh = gui.dsp_shift_channel(sep[:, ch], int(shifts[ch]))
        rolled = gui.maximum_filter1d(np.clip(sh, 0, None), size=max(3, int(norm_window)), mode='nearest')
        rolled = np.where(rolled > 0, rolled, 1.0)
        normed[:, ch] = sh / rolled
    comb = normed.max(axis=1)
    start, stop = 0, n
    if reg is not None and int(reg[1]) > int(reg[0]):
        start, stop = max(0, int(reg[0])), min(n, int(reg[1]))
    else:
        start = gui.pc_signal_onset(sep, onset_frac=0.05, smooth=40)
    thr = max(float(comb[start:stop].max()) * min_frac, 1e-9)
    work = comb.copy(); work[:start] = -1.0; work[stop:] = -1.0
    calls = []
    while True:
        i = int(np.argmax(work))
        if work[i] < thr: break
        calls.append((i, gui.CHEM_MAP[int(np.argmax(normed[i]))]))
        work[max(0, i-window):min(n, i+window+1)] = -1.0
    calls.sort()
    return calls, comb

def merge(calls, comb, ratio, dist, same_channel=False):
    if not calls: return calls
    out = [list(calls[0])]
    for i, (p, l) in enumerate(calls[1:], start=1):
        prev_p, prev_l = out[-1]
        if p - prev_p <= dist and l == prev_l:
            v = float(comb[prev_p:p+1].min())
            lower = min(comb[prev_p], comb[p])
            if v >= ratio * lower:
                if comb[p] > comb[prev_p]:
                    out[-1] = [p, l]
                continue
        out.append([p, l])
    return [(p, l) for p, l in out]

def nw(q, r):
    m, n = len(q), len(r)
    if m == 0 or n == 0: return 0.0
    dp = np.zeros((m+1, n+1), dtype=np.int32)
    dp[:,0] = np.arange(m+1)*-2; dp[0,:] = np.arange(n+1)*-2
    r_int = np.frombuffer(r.encode('ascii'), dtype=np.uint8).astype(np.int64)
    js = np.arange(1, n+1, dtype=np.int64); gapj = -2*js
    for i in range(1, m+1):
        qi = ord(q[i-1]); prev = dp[i-1]
        diag = prev[:-1] + np.where(r_int == qi, 1, -1)
        up = prev[1:] - 2
        pref = np.maximum.accumulate(np.maximum(diag, up) - gapj)
        dp[i,0] = prev[0]-2; dp[i,1:] = pref + gapj
    i, j = m, n; mt = 0; al = 0
    while i > 0 or j > 0:
        if i > 0 and j > 0 and dp[i,j] == dp[i-1,j-1] + (1 if q[i-1]==r[j-1] else -1):
            al += 1; mt += (q[i-1]==r[j-1]); i -= 1; j -= 1
        elif i > 0 and dp[i,j] == dp[i-1,j] - 2:
            al += 1; i -= 1
        else:
            al += 1; j -= 1
    return 100.0*mt/al if al else 0.0

# Diagnosis on A01: insertions and their valley depth
sep, shifts, reg, seq = load('A01')
calls, comb = greedy_env(sep, shifts, reg)
print('A01 baseline: n=%d NW=%.1f%%' % (len(calls), nw(''.join(c for _,c in calls), seq)))

# reconstruct alignment
from io import StringIO
q = ''.join(c for _, c in calls)
m, n = len(q), len(seq)
dp = np.zeros((m+1, n+1), dtype=np.int32)
dp[:,0]=np.arange(m+1)*-2; dp[0,:]=np.arange(n+1)*-2
r_int = np.frombuffer(seq.encode('ascii'), dtype=np.uint8).astype(np.int64)
js = np.arange(1, n+1, dtype=np.int64); gapj=-2*js
for i in range(1, m+1):
    qi=ord(q[i-1]); prev=dp[i-1]
    diag=prev[:-1]+np.where(r_int==qi,1,-1)
    up=prev[1:]-2
    pref=np.maximum.accumulate(np.maximum(diag,up)-gapj)
    dp[i,0]=prev[0]-2; dp[i,1:]=pref+gapj
i,j=m,n
ins_here=[]
while i>0 or j>0:
    if i>0 and j>0 and dp[i,j]==dp[i-1,j-1]+(1 if q[i-1]==seq[j-1] else -1):
        i-=1;j-=1
    elif i>0 and dp[i,j]==dp[i-1,j]-2:
        ins_here.append(i-1); i-=1
    else:
        j-=1
print('insertions in greedy call vs ESD: %d' % len(ins_here))
for k in ins_here[:12]:
    p = calls[k][0]
    lo = calls[k-1][0] if k>0 else p-8
    hi = calls[k+1][0] if k+1<len(calls) else p+8
    if hi<=lo: continue
    vmin = float(comb[lo:hi+1].min())
    vpos = lo + int(np.argmin(comb[lo:hi+1]))
    lower = min(comb[lo], comb[hi]) if (calls[k-1] if k>0 else None) and k+1<len(calls) else comb[p]
    print(f'  ins#{k} call={calls[k][1]}@{p} prev={calls[k-1][1]}@{calls[k-1][0]} next={calls[k+1][1]}@{calls[k+1][0]} valley={vmin:.2f}@scan{vpos}')

# merge sweep
# Diagnose on A01 across configs: baseline vs best same-letter merge
def run(sep, shifts, reg, seq, prom, norm):
    calls, comb = greedy_env(sep, shifts, reg, min_frac=prom, norm_window=norm)
    base = nw(''.join(c for _,c in calls), seq)
    bm = (base, None)
    for ratio in [0.5,0.6,0.7,0.8,0.9]:
        for dist in [7,8,10]:
            mc = merge(calls, comb, ratio, dist)
            v = nw(''.join(c for _,c in mc), seq)
            if v > bm[0]: bm = (v, (ratio,dist,len(mc)))
    return calls, comb, base, bm

calls, comb, base, bm = run(sep, shifts, reg, seq, 0.20, 800)
print('A01 prom=0.20 norm=800: baseline %.1f%% best-merge %.1f%% @%s' % (base, bm[0], bm[1]))
for prom, norm in [(0.135,300),(0.15,400),(0.17,400),(0.135,400)]:
    w.prominence_spin.setValue(int(round(prom*1000)))
    w.norm_window_spin.setValue(norm)
    sh2 = w._get_mobility_shifts()
    c2, cb2, b2, bm2 = run(w._process()[4], sh2, w._get_region(w._process()[4]), seq, prom, norm)
    print('A01 prom=%.3f norm=%d: baseline %.1f%% (n=%d) best-merge %.1f%% @%s' % (prom, norm, b2, len(c2), bm2[0], bm2[1]))