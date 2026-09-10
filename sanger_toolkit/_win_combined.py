#!/usr/bin/env python3
import os, sys, json
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
os.environ.setdefault('TF_CPP_MIN_LOG_LEVEL', '3')
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from PyQt5.QtWidgets import QApplication

ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, '02_denovo_cnn_ensemble_91.53pct'))

WIN = {
 'A01_2050_411.json':  (2050, 2411),
 'A01_2411_761.json':  (2411, 2761),
 'A01_2761_3010.json': (2761, 3010),
 'A01_3000_4100.json': (3000, 4100),
 'A01_4100_5000.json': (4100, 5000),
}

app = QApplication(sys.argv)
from sequencing_gui_V15 import SequencingGUI

def window_calls():
    gui = SequencingGUI()
    gui.well_combo.setCurrentText('A01')
    gui._load_data()
    out = {}
    for sf,(r0,r1) in WIN.items():
        d = json.load(open(os.path.join(HERE, sf)))
        gui.load_settings_from_dict(d)
        gui.region_auto_check.setChecked(False)
        gui.region_hybrid_check.setChecked(False)
        gui.region_start_spin.setValue(r0)
        gui.region_stop_spin.setValue(r1)
        gui._run_basecall()
        seq = gui._manual_sequence or ''
        pos = list(gui._last_positions) if getattr(gui,'_last_positions',None) is not None else []
        out[sf] = (seq, pos)
    return out

def main():
    wins = window_calls()
    combined = ''.join(seq for seq,_ in wins.values())
    print('=== per-window calls ===')
    for sf,(seq,pos) in wins.items():
        print(f'{sf}: len={len(seq)} pos=({pos[0] if pos else "-"}, {pos[-1] if pos else "-"}) seq={seq[:60]!r}')
    print('\n=== combined (stitched) len=', len(combined))
    print(combined)
    with open('/tmp/opencode/combined_A01.fa','w') as f:
        f.write('>combined_A01\n'+combined+'\n')

if __name__ == '__main__':
    main()
