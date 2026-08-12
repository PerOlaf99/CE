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

def greedy(sep, shifts, reg, window, min_frac, norm_window=800):
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
        return np.array([], dtype=int), np.array([]), np.array([])
    thr = max(float(comb[start:stop].max()) * min_frac, 1e-9)
    work = comb.copy(); work[:start] = -1.0; work[stop:] = -1.0
    picks = []
    while True:
        i = int(np.argmax(work))
        if work[i] < thr:
            break
        picks.append(i)
        lo, hi = max(0, i - window), min(n, i + window + 1)
        work[lo:hi] = -1.0
    picks = np.array(sorted(picks), dtype=int)
    return picks, normed, comb

def greedy_fill(sep, shifts, reg, window=5, min_frac=0.20, fill_gap=3, fill_margin=0.20,
                prom_frac=0.04, norm_window=800):
    picks, normed, comb = greedy(sep, shifts, reg, window, min_frac, norm_window)
    letters = [gui.CHEM_MAP[int(np.argmax(normed[p]))] for p in picks]
    adds = gui.pc_fill_in_combined_peaks(
        sep, shifts, positions=[int(p) for p in picks],
        min_distance=1, prominence_frac=prom_frac, norm_window=norm_window,
        fill_gap=fill_gap, fill_margin=fill_margin, region=reg)
    if adds:
        merged = sorted([(int(p), l) for p, l in zip(picks, letters)] + list(adds), key=lambda t: t[0])
        picks = np.array([t[0] for t in merged], dtype=int)
        letters = [t[1] for t in merged]
    return ''.join(letters), len(picks)

print('well   greedy     +fill g3 m.20   +fill g2 m.15   +fill g2 m.25')
res = {}
for tag in ['base', 'g3m20', 'g2m15', 'g2m25']:
    res[tag] = []
for well in wells:
    sep, shifts, reg, seq = data[well]
    sq0, _ = greedy_fill(sep, shifts, reg)
    res['base'].append(gui.pc_nw_identity(sq0, seq))
    sq, _ = greedy_fill(sep, shifts, reg, fill_gap=3, fill_margin=0.20)
    res['g3m20'].append(gui.pc_nw_identity(sq, seq))
    sq, _ = greedy_fill(sep, shifts, reg, fill_gap=2, fill_margin=0.15)
    res['g2m15'].append(gui.pc_nw_identity(sq, seq))
    sq, _ = greedy_fill(sep, shifts, reg, fill_gap=2, fill_margin=0.25)
    res['g2m25'].append(gui.pc_nw_identity(sq, seq))
for i, well in enumerate(wells):
    print(f'{well:5s}   {res["base"][i]:6.1f}%     {res["g3m20"][i]:6.1f}%       {res["g2m15"][i]:6.1f}%       {res["g2m25"][i]:6.1f}%')
print(f'MEAN     {np.mean(res["base"]):6.1f}%     {np.mean(res["g3m20"]):6.1f}%       {np.mean(res["g2m15"]):6.1f}%       {np.mean(res["g2m25"]):6.1f}%')
