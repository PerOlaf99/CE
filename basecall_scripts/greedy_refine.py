import sys, os, json, numpy as np
sys.path.insert(0, '/media/per/78B0C7DE1FA7081C/electropherogram')
from PyQt5.QtWidgets import QApplication
import sequencing_gui_V15 as gui
from extract_training_data import parse_rsd, parse_esd

app = QApplication([])
w = gui.SequencingGUI()
BASE = '/media/per/78B0C7DE1FA7081C/electropherogram/MB1000_M13_DT'
esd_dir = os.path.join(BASE, 'MB1000_M13_DT_Cp312_MD1')
s = json.load(open('/media/per/78B0C7DE1FA7081C/electropherogram/settingsV8.json'))
wells = ['A01','A02','A03','A04','A06','A08','B01','B05']
data = {}
for well in wells:
    df = parse_rsd(os.path.join(BASE, f'{well}.rsd'))
    w.rsd_raw = df[['Channel1','Channel2','Channel3','Channel4']].values.astype(np.float64)
    w.x_rsd = np.arange(len(w.rsd_raw))
    ed = parse_esd(os.path.join(esd_dir, f'{well}.esd'))
    w.esd_data = ed
    w._load_esd_traces(os.path.join(esd_dir, f'{well}.esd'))
    w.x_esd = np.arange(len(w.esd_traces))
    w.load_settings_from_dict(s)
    w.esd_offset_spin.setValue(1998)
    w.mobility_spins[0].setValue(5); w.mobility_spins[1].setValue(10)
    w.mobility_spins[2].setValue(10); w.mobility_spins[3].setValue(10)
    sep = w._process()[4]; shifts = w._get_mobility_shifts(); reg = w._get_region(sep)
    data[well] = (sep, shifts, reg, ed['sequence'])

def greedy_refine(sep, shifts, reg, window=5, min_frac=0.20, refine=0,
                  norm_window=800):
    n = len(sep)
    shifted_all = [gui.dsp_shift_channel(sep[:, ch], int(shifts[ch])) for ch in range(4)]
    normed = np.empty_like(sep)
    for ch in range(4):
        sh = shifted_all[ch]
        rolled = gui.maximum_filter1d(np.clip(sh, 0, None), size=max(3, int(norm_window)), mode='nearest')
        rolled = np.where(rolled > 0, rolled, 1.0)
        normed[:, ch] = sh / rolled
    comb = normed.max(axis=1)
    start, stop = 0, n
    if reg is not None and int(reg[1]) > int(reg[0]):
        start, stop = max(0, int(reg[0])), min(n, int(reg[1]))
    else:
        start = gui.pc_signal_onset(sep, onset_frac=0.05, smooth=40)
    if start >= stop:
        return ''
    thr = max(float(comb[start:stop].max()) * min_frac, 1e-9)
    work = comb.copy(); work[:start] = -1.0; work[stop:] = -1.0
    calls = []
    while True:
        i = int(np.argmax(work))
        if work[i] < thr:
            break
        ch = int(np.argmax(normed[i]))
        j = i
        if refine > 0:
            lo, hi = max(0, i - refine), min(n - 1, i + refine + 1)
            j = lo + int(np.argmax(normed[lo:hi, ch]))
        calls.append((j, gui.CHEM_MAP[int(np.argmax(normed[j]))]))
        lo, hi = max(0, i - window), min(n, i + window + 1)
        work[lo:hi] = -1.0
    calls.sort()
    return ''.join(c for _, c in calls)

print('well   greedy   +refine r2   +refine r3   +refine r4')
res = {r: [] for r in [0, 2, 3, 4]}
for well in wells:
    sep, shifts, reg, seq = data[well]
    for r in res:
        res[r].append(gui.pc_nw_identity(
            greedy_refine(sep, shifts, reg, refine=r), seq))
for i, well in enumerate(wells):
    print(f'{well:5s}  {res[0][i]:6.1f}%   {res[2][i]:6.1f}%      {res[3][i]:6.1f}%      {res[4][i]:6.1f}%')
print(f'MEAN     {np.mean(res[0]):6.1f}%   {np.mean(res[2]):6.1f}%      {np.mean(res[3]):6.1f}%      {np.mean(res[4]):6.1f}%')
