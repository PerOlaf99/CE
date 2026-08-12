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
    sep = w._process()[4]
    shifts = w._get_mobility_shifts()
    reg = w._get_region(sep)
    data[well] = (sep, shifts, reg, ed['sequence'])

def greedy_np(sep, shifts, reg, window, min_frac, norm_window=800):
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
        return []
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
    return calls

print('mean NW over 8 wells (window x min_frac):')
print('       mf.10   mf.15   mf.20   mf.25   mf.30')
grid = {}
for win in (4, 5, 6, 7, 8):
    row = []
    for mf in (0.10, 0.15, 0.20, 0.25, 0.30):
        vs = []
        for sep, shifts, reg, seq in data.values():
            sseq = ''.join(c for _, c in greedy_np(sep, shifts, reg, win, mf))
            vs.append(gui.pc_nw_identity(sseq, seq))
        grid[(win, mf)] = np.mean(vs)
        row.append(f'{np.mean(vs):6.1f}')
    print(f'win={win}  ' + ' '.join(row))

best = max(grid, key=grid.get)
print('\nbest config:', best, f'{grid[best]:.1f}% mean')
for win, mf in [(best[0], best[1]), (6, 0.20), (5, 0.20)]:
    seq_all = [data[k][3] for k in wells]
    calls_all = [greedy_np(*data[k][:3], win, mf) for k in wells]
    nws = [gui.pc_nw_identity(''.join(c for _, c in calls), seq)
           for calls, seq in zip(calls_all, seq_all)]
    ns = [len(c) for c in calls_all]
    print(f'win={win} mf={mf}: mean {np.mean(nws):.1f}%  n={np.mean(ns):.0f}  per-well {[round(x,1) for x in nws]}')
