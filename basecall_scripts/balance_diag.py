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
    raw, bl, corr, sm, sep, mix = w._process()
    return raw, sep, ed['sequence'], np.array(ed['peak_positions'], dtype=int)

raw, sep, seq, esdpos = load('A01')

# ESD trace positions: need the ESD raw trace to compare amplitudes. Use the
# loaded esd traces from the GUI (aligned coordinates).
esdtr = w.esd_traces  # shape (n_esd, 4)? check

# For each ESD base position, examine:
#   raw   : the 4 raw channel values at that scan
#   sep   : the 4 separated channel values at that scan
#   esdtr : the ESD trace value (channel amplitudes as ESD knows them)
print('esd_traces shape:', np.asarray(esdtr).shape)
print('sep shape:', sep.shape, 'raw shape:', raw.shape)

def channel_letter(idx):
    return {0:'T',1:'G',2:'C',3:'A'}[idx] if False else gui.CHEM_MAP[idx]

# Compare per-base: separated argmax letter vs ESD letter, in first vs last half.
esdtr = np.asarray(esdtr)
def esd_argmax(p):
    # ESD trace index -> scan: assume esd_traces aligned to same x as sep
    if p < len(esdtr):
        return gui.CHEM_MAP[int(np.argmax(esdtr[p]))]
    return None

from collections import Counter
conf = Counter()
raw_amp = {'A': [], 'G': [], 'C': [], 'T': []}
sep_amp = {'A': [], 'G': [], 'C': [], 'T': []}
esd_amp = {'A': [], 'G': [], 'C': [], 'T': []}
halves = {'early': 0, 'late': 0}
for k, p in enumerate(esdpos):
    if k >= len(seq) or not (0 <= p < len(sep)):
        continue
    letter = seq[k]
    sepvals = sep[p]
    sepdom = gui.CHEM_MAP[int(np.argmax(sepvals))]
    half = 'late' if k > len(seq)*0.5 else 'early'
    if sepdom != letter:
        conf[(half, letter, sepdom)] += 1
    # amplitude of the TRUE channel at this position
    ch = {0:'T',1:'G',2:'C',3:'A'}  # need CHEM_MAP index of letter
    chidx = None
    for ci in range(4):
        if gui.CHEM_MAP[ci] == letter:
            chidx = ci
    if chidx is None:
        continue
    raw_amp[letter].append(raw[p, chidx])
    sep_amp[letter].append(sep[p, chidx])
    if p < len(esdtr):
        esd_amp[letter].append(esdtr[p, chidx])

print('\nConfusion (half, true_letter, our_call):')
for key, cnt in sorted(conf.items()):
    print(f'  {key}: {cnt}')

print('\nMedian amplitude of the TRUE channel at ESD positions (raw / separated / esd):')
for letter in 'ACGT':
    if raw_amp[letter]:
        r = np.median(raw_amp[letter]); sp = np.median(sep_amp[letter]); es = np.median(esd_amp[letter]) if esd_amp[letter] else float('nan')
        print(f'  {letter}: raw={r:.2f}  separated={sp:.3f}  esd_trace={es:.3f}')

# late-read only imbalance: for the last 150 bases
print('\nLast 150 bases confusion (true_letter, our_call):')
conf2 = Counter()
for k, p in enumerate(esdpos[-150:]):
    idx = len(seq) - 150 + k
    if idx >= len(seq) or not (0 <= p < len(sep)):
        continue
    letter = seq[idx]
    sepdom = gui.CHEM_MAP[int(np.argmax(sep[p]))]
    if sepdom != letter:
        conf2[(letter, sepdom)] += 1
for key, cnt in sorted(conf2.items()):
    print(f'  {key}: {cnt}')
