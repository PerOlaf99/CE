import sys, os, json, numpy as np
sys.path.insert(0, '/media/per/78B0C7DE1FA7081C/electropherogram')
from PyQt5.QtWidgets import QApplication
import sequencing_gui_V15 as gui
from extract_training_data import parse_rsd, parse_esd

app = QApplication([])
w = gui.SequencingGUI()
BASE = '/media/per/78B0C7DE1FA7081C/electropherogram/MB1000_M13_DT'
esd_dir = os.path.join(BASE, 'MB1000_M13_DT_Cp312_MD1')
s = json.load(open('/media/per/78B0C7DE1FA7081C/electropherogram/settingsV10.json'))

wells = []
for r in 'ABCDEFGH':
    for c in range(1, 13):
        wells.append(f'{r}{c:02d}')

def greedy(sep, shifts, reg, window=5, min_frac=0.20, norm_window=800):
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
    return ''.join(c for _, c in calls)

CONFIGS = [
    ('V10-stored  m5,11,10,10 p0.135 n300', [5,11,10,10], 0.135, 300),
    ('bestA       m5,10,10,10 p0.200 n800', [5,10,10,10], 0.200, 800),
    ('bestB       m5,11,10,10 p0.200 n800', [5,11,10,10], 0.200, 800),
]
res = {c[0]: [] for c in CONFIGS}
missing = []
for well in wells:
    try:
        df = parse_rsd(os.path.join(BASE, f'{well}.rsd'))
        w.rsd_raw = df[['Channel1','Channel2','Channel3','Channel4']].values.astype(np.float64)
        w.x_rsd = np.arange(len(w.rsd_raw))
        ed = parse_esd(os.path.join(esd_dir, f'{well}.esd'))
        w.esd_data = ed
        w._load_esd_traces(os.path.join(esd_dir, f'{well}.esd'))
        w.x_esd = np.arange(len(w.esd_traces))
        w.load_settings_from_dict(s)
        sep = w._process()[4]
        for name, mob, prom, norm in CONFIGS:
            for ch, v in enumerate(mob): w.mobility_spins[ch].setValue(v)
            w.prominence_spin.setValue(int(round(prom*1000)))
            w.norm_window_spin.setValue(norm)
            shifts = w._get_mobility_shifts(); reg = w._get_region(sep)
            sq = greedy(sep, shifts, reg, min_frac=prom, norm_window=norm)
            res[name].append(gui.pc_nw_identity(sq, ed['sequence']))
    except Exception as e:
        missing.append((well, str(e)))

for name, *_ in CONFIGS:
    v = np.array(res[name])
    if len(v):
        print(f'{name}: n={len(v)}  mean={v.mean():.1f}%  median={np.median(v):.1f}%  min={v.min():.1f}%')
print('missing wells:', missing if missing else 'none')