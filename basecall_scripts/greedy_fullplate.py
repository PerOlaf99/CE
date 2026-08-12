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
        return ''
    thr = max(comb[start:stop].max() * min_frac, 1e-9)
    work = comb.copy(); work[:start] = -1.0; work[stop:] = -1.0
    calls = []
    while True:
        i = int(np.argmax(work))
        if work[i] < thr:
            break
        calls.append((i, gui.CHEM_MAP[int(np.argmax(normed[i]))]))
        lo, hi = max(0, i - window), min(n, i + window + 1)
        work[lo:hi] = -1.0
    calls.sort()
    return ''.join(c for _, c in calls)

def load(well):
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
    return sep, shifts, reg, ed['sequence']

import glob
files = sorted(glob.glob(os.path.join(BASE, '*.rsd')))
wells = [os.path.basename(f).replace('.rsd', '') for f in files]
print(f'{len(wells)} wells')

cur, greedy_vals = [], []
for well in wells:
    sep, shifts, reg, seq = load(well)
    _, sq, _, _ = gui.pc_call_bases_with_shifts(sep, shifts, min_distance=5,
        prominence_frac=0.075, tolerance=4, min_signal_frac=1.00, norm_window=2000, region=reg)
    cur.append(gui.pc_nw_identity(sq, seq))
    greedy_vals.append(gui.pc_nw_identity(greedy(sep, shifts, reg, 5, 0.20), seq))

cur = np.array(cur); greedy_vals = np.array(greedy_vals)
print(f'current per-channel : mean {cur.mean():.1f}%  median {np.median(cur):.1f}%  min {cur.min():.1f}%')
print(f'greedy w5 mf.20     : mean {greedy_vals.mean():.1f}%  median {np.median(greedy_vals):.1f}%  min {greedy_vals.min():.1f}%')
print(f'greedy better on {np.sum(greedy_vals > cur)}/{len(wells)} wells; worse on {np.sum(greedy_vals < cur)}')
d = greedy_vals - cur
worst = np.argsort(d)[:8]
print('worst greedy-vs-current deltas (well, cur, greedy, diff):')
for i in worst:
    print(f'  {wells[i]}  cur={cur[i]:.1f}  greedy={greedy_vals[i]:.1f}  d={d[i]:+.1f}')
