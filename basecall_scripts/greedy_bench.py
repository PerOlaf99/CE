import sys, os, json
sys.path.insert(0, '/media/per/78B0C7DE1FA7081C/electropherogram')
import numpy as np
from PyQt5.QtWidgets import QApplication
import sequencing_gui_V15 as gui
from extract_training_data import parse_rsd, parse_esd

app = QApplication([])
w = gui.SequencingGUI()
BASE = '/media/per/78B0C7DE1FA7081C/electropherogram/MB1000_M13_DT'
esd_dir = os.path.join(BASE, 'MB1000_M13_DT_Cp312_MD1')
s = json.load(open('/media/per/78B0C7DE1FA7081C/electropherogram/settingsV8.json'))

def pc_combined_call(separated, shifts, norm_window=800, min_distance=3,
                     prominence_frac=0.04, region=None):
    n = len(separated)
    shifted_all = [gui.dsp_shift_channel(separated[:, ch], int(shifts[ch])) for ch in range(4)]
    normed = np.empty_like(separated)
    for ch in range(4):
        shifted = shifted_all[ch]
        rolled = gui.maximum_filter1d(np.clip(shifted, 0, None), size=max(3, int(norm_window)), mode='nearest')
        rolled = np.where(rolled > 0, rolled, 1.0)
        normed[:, ch] = shifted / rolled
    comb = normed.max(axis=1)
    scale = np.percentile(comb, 99.5)
    prom = max(scale * prominence_frac, 1e-9)
    peaks, _ = gui.find_peaks(comb, distance=max(1, int(min_distance)), prominence=prom)
    start, stop = 0, n
    if region is not None and int(region[1]) > int(region[0]):
        start, stop = max(0, int(region[0])), min(n, int(region[1]))
    else:
        start = gui.pc_signal_onset(separated, onset_frac=0.05, smooth=40)
    peaks = [int(p) for p in peaks if start <= int(p) < stop]
    letters = [gui.CHEM_MAP[int(np.argmax(normed[p]))] for p in peaks]
    return ''.join(letters)

def greedy_call(separated, shifts, norm_window=800, window=4, min_frac=0.10, region=None):
    """Greedy maximum-intensity peak caller:
    repeatedly take the global max of the per-channel-normalized combined
    envelope, call the argmax channel there, then excise a +/-window band so
    the next iteration finds the next base. Stops when the remaining max
    falls below min_frac of the region's max."""
    n = len(separated)
    shifted_all = [gui.dsp_shift_channel(separated[:, ch], int(shifts[ch])) for ch in range(4)]
    normed = np.empty_like(separated)
    for ch in range(4):
        shifted = shifted_all[ch]
        rolled = gui.maximum_filter1d(np.clip(shifted, 0, None), size=max(3, int(norm_window)), mode='nearest')
        rolled = np.where(rolled > 0, rolled, 1.0)
        normed[:, ch] = shifted / rolled
    comb = normed.max(axis=1).copy()
    start, stop = 0, n
    if region is not None and int(region[1]) > int(region[0]):
        start, stop = max(0, int(region[0])), min(n, int(region[1]))
    else:
        start = gui.pc_signal_onset(separated, onset_frac=0.05, smooth=40)
    if start >= stop:
        return ''
    region_max = comb[start:stop].max()
    threshold = max(region_max * min_frac, 1e-9)
    work = np.where(np.arange(n) < start, -1.0, comb)
    work[stop:] = -1.0
    calls = []
    while True:
        i = int(np.argmax(work))
        if work[i] < threshold:
            break
        calls.append((i, gui.CHEM_MAP[int(np.argmax(normed[i]))]))
        lo, hi = max(0, i - int(window)), min(n, i + int(window) + 1)
        work[lo:hi] = -1.0
    calls.sort()
    return ''.join(c for _, c in calls)

wells = ['A01','A02','A03','A04','A06','A08','B01','B05']
res = {k: [] for k in ['cur', 'combined', 'greedy_sep', 'greedy_raw']}
for well in wells:
    df = parse_rsd(os.path.join(BASE, f'{well}.rsd'))
    w.rsd_raw = df[['Channel1','Channel2','Channel3','Channel4']].values.astype(np.float64)
    w.x_rsd = np.arange(len(w.rsd_raw))
    ed = parse_esd(os.path.join(esd_dir, f'{well}.esd'))
    w.esd_data = ed
    w._load_esd_traces(os.path.join(esd_dir, f'{well}.esd'))
    w.x_esd = np.arange(len(w.esd_traces))
    seq = ed['sequence']
    w.load_settings_from_dict(s)
    w.esd_offset_spin.setValue(1998)
    w.mobility_spins[0].setValue(5); w.mobility_spins[1].setValue(10)
    w.mobility_spins[2].setValue(10); w.mobility_spins[3].setValue(10)
    sep = w._process()[4]
    shifts = w._get_mobility_shifts()
    reg = w._get_region(sep)
    _, sq, _, _ = gui.pc_call_bases_with_shifts(sep, shifts, min_distance=5,
        prominence_frac=0.075, tolerance=4, min_signal_frac=1.00, norm_window=2000, region=reg)
    res['cur'].append(gui.pc_nw_identity(sq, seq))
    res['combined'].append(gui.pc_nw_identity(pc_combined_call(sep, shifts, region=reg), seq))
    res['greedy_sep'].append(gui.pc_nw_identity(
        greedy_call(sep, shifts, region=reg, window=4, min_frac=0.10), seq))
    w._set_matrix_apply_point('none')
    sep_raw = w._process()[4]
    res['greedy_raw'].append(gui.pc_nw_identity(
        greedy_call(sep_raw, shifts, region=reg, window=4, min_frac=0.10), seq))

print(f'{"well":5s} {"current":>8s} {"combined":>9s} {"greedy_sep":>11s} {"greedy_raw":>11s}')
for i, well in enumerate(wells):
    print(f'{well:5s} {res["cur"][i]:7.1f}% {res["combined"][i]:8.1f}% '
          f'{res["greedy_sep"][i]:10.1f}% {res["greedy_raw"][i]:10.1f}%')
print(f'{"MEAN":5s} {np.mean(res["cur"]):7.1f}% {np.mean(res["combined"]):8.1f}% '
      f'{np.mean(res["greedy_sep"]):10.1f}% {np.mean(res["greedy_raw"]):10.1f}%')
