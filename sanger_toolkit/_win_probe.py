#!/usr/bin/env python3
import os, sys, json
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
os.environ.setdefault('TF_CPP_MIN_LOG_LEVEL', '3')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PyQt5.QtWidgets import QApplication
app = QApplication(sys.argv)
from sequencing_gui_V15 import SequencingGUI

WIN = {
 'A01_2050_411.json':  (2050,2411),
 'A01_2411_761.json':  (2411,2761),
 'A01_2761_3010.json': (2761,3010),
 'A01_3000_4100.json': (3000,4100),
 'A01_4100_5000.json': (4100,5000),
}

gui = SequencingGUI()
gui.well_combo.setCurrentText('A01')
gui._load_data()
print('well', gui.current_well, 'rsd', gui.rsd_raw.shape)

for sf,(r0,r1) in WIN.items():
    d=json.load(open(sf))
    gui.load_settings_from_dict(d)
    # force region (manual mode overrides spins)
    gui.region_auto_check.setChecked(False)
    gui.region_hybrid_check.setChecked(False)
    gui.region_start_spin.setValue(r0)
    gui.region_stop_spin.setValue(r1)
    gui._run_basecall()
    seq = gui._manual_sequence or ''
    pos = list(gui._last_positions) if getattr(gui,'_last_positions',None) is not None else []
    print(f'{sf}: region=({r0},{r1}) len={len(seq)} npos={len(pos)} '
          f'posrange={ (min(pos),max(pos)) if pos else None }')
    print(f'   seq={seq!r}')
