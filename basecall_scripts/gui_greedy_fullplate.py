import sys, os, json, glob
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
w.method_combo.setCurrentIndex(0)  # Greedy

files = sorted(glob.glob(os.path.join(BASE, '*.rsd')))
wells = [os.path.basename(f).replace('.rsd', '') for f in files]
gw = []
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
    _, sq, _, _ = w._call_bases(sep, shifts, reg)
    gw.append(gui.pc_nw_identity(sq, ed['sequence']))

gw = np.array(gw)
print(f'GUI greedy path, {len(wells)} wells: mean {gw.mean():.1f}%  median {np.median(gw):.1f}%  min {gw.min():.1f}%')
