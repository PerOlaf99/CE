import sys, os, json, numpy as np
sys.path.insert(0, '/media/per/78B0C7DE1FA7081C/electropherogram')
from PyQt5.QtWidgets import QApplication
import sequencing_gui_V15 as gui
from extract_training_data import parse_rsd, parse_esd
from scipy.ndimage import maximum_filter1d

app = QApplication([])
w = gui.SequencingGUI()
BASE = '/media/per/78B0C7DE1FA7081C/electropherogram/MB1000_M13_DT'
esd_dir = os.path.join(BASE, 'MB1000_M13_DT_Cp312_MD1')
WELLS = ['A01','A02','A03','A04','A06','A08','B01','B05']

def load(well):
    df = parse_rsd(os.path.join(BASE, f'{well}.rsd'))
    w.rsd_raw = df[['Channel1','Channel2','Channel3','Channel4']].values.astype(np.float64)
    w.x_rsd = np.arange(len(w.rsd_raw))
    ed = parse_esd(os.path.join(esd_dir, f'{well}.esd'))
    w.esd_data = ed
    w._load_esd_traces(os.path.join(esd_dir, f'{well}.esd'))
    w.x_esd = np.arange(len(w.esd_traces))
    w.load_settings_from_dict(json.load(open('/media/per/78B0C7DE1FA7081C/electropherogram/settingsV10.json')))
    for ch, v in enumerate([5,11,10,10]): w.mobility_spins[ch].setValue(v)
    w.prominence_spin.setValue(200); w.norm_window_spin.setValue(800)
    sep = w._process()[4]; shifts = w._get_mobility_shifts(); reg = w._get_region(sep)
    return sep, shifts, reg, ed['sequence']

def greedy(sep, shifts, reg, window=5, min_frac=0.20, norm_window=800, fwhm_adaptive=False,
           cap=12):
    n = len(sep)
    normed = np.empty_like(sep)
    for ch in range(4):
        sh = gui.dsp_shift_channel(sep[:, ch], int(shifts[ch]))
        rolled = maximum_filter1d(np.clip(sh, 0, None), size=max(3, int(norm_window)), mode='nearest')
        rolled = np.where(rolled > 0, rolled, 1.0)
        normed[:, ch] = sh / rolled
    comb = normed.max(axis=1)
    dv = normed.argmax(axis=1)
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
        letters = gui.CHEM_MAP[int(np.argmax(normed[i]))]
        w_here = window
        if fwhm_adaptive:
            ch = dv[i]
            half = 0.5 * normed[i, ch]
            lo, hi = i, i
            while lo > start and normed[lo-1, ch] >= half and i - lo < cap: lo -= 1
            while hi < stop-1 and normed[hi+1, ch] >= half and hi - i < cap: hi += 1
            w_here = int(max(window, (i - lo), (hi - i)))
        calls.append((i, letters))
        work[max(0, i-w_here):min(n, i+w_here+1)] = -1.0
    calls.sort()
    return ''.join(c for _, c in calls)

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

data = {well: load(well) for well in WELLS}
res = {k: [] for k in ['w4','w5','w6','fwhm_cap10','fwhm_cap12','fwhm_cap16']}
for well in WELLS:
    sep, shifts, reg, seq = data[well]
    res['w4'].append(nw(greedy(sep,shifts,reg,window=4), seq))
    res['w5'].append(nw(greedy(sep,shifts,reg,window=5), seq))
    res['w6'].append(nw(greedy(sep,shifts,reg,window=6), seq))
    res['fwhm_cap10'].append(nw(greedy(sep,shifts,reg,fwhm_adaptive=True,cap=10), seq))
    res['fwhm_cap12'].append(nw(greedy(sep,shifts,reg,fwhm_adaptive=True,cap=12), seq))
    res['fwhm_cap16'].append(nw(greedy(sep,shifts,reg,fwhm_adaptive=True,cap=16), seq))
for k, v in res.items():
    print(f'{k:14s} mean={np.mean(v):5.1f}%  median={np.median(v):5.1f}%   ' +
          '  '.join(f'{x:.1f}' for x in v))