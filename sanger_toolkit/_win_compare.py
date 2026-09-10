#!/usr/bin/env python3
import os, sys, json
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
os.environ.setdefault('TF_CPP_MIN_LOG_LEVEL', '3')
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, '02_denovo_cnn_ensemble_91.53pct'))
from PyQt5.QtWidgets import QApplication

WIN = {
 'A01_2050_411.json':  (2050, 2411),
 'A01_2411_761.json':  (2411, 2761),
 'A01_2761_3010.json': (2761, 3010),
 'A01_3000_4100.json': (3000, 4100),
 'A01_4100_5000.json': (4100, 5000),
}

def window_calls():
    app = QApplication(sys.argv)
    from sequencing_gui_V15 import SequencingGUI
    gui = SequencingGUI()
    gui.well_combo.setCurrentText('A01')
    gui._load_data()
    out = []
    for sf,(r0,r1) in WIN.items():
        d = json.load(open(os.path.join(HERE, sf)))
        gui.load_settings_from_dict(d)
        gui.region_auto_check.setChecked(False)
        gui.region_hybrid_check.setChecked(False)
        gui.region_start_spin.setValue(r0)
        gui.region_stop_spin.setValue(r1)
        gui._run_basecall()
        seq = gui._manual_sequence or ''
        out.append(seq)
    return ''.join(out)

def dll_seq():
    import extract_training_data as etd
    d = etd.parse_esd(os.path.join(ROOT,'MB1000_M13_DT','MB1000_M13_DT_Cp312_MD1','A01.esd'))
    return d['sequence']

def cnn_seq():
    import tensorflow as tf
    import perfect_basecaller as pb
    import numpy as np
    pat = os.path.join(ROOT,'02_denovo_cnn_ensemble_91.53pct')
    models = [tf.keras.models.load_model(os.path.join(pat,f),compile=False)
              for f in ['base_caller_model_v4_clean.keras',
                        'base_caller_model_v4_pos.keras',
                        'base_caller_model_v4_pos_b.keras']]
    r = pb.call_raw(os.path.join(ROOT,'MB1000_M13_DT','A01.rsd'), models=models,
                    bgn_end_method='perbase')
    return r['seq']

def main():
    combined = window_calls()
    dll = dll_seq()
    cnn = cnn_seq()
    print('combined len', len(combined))
    print('dll len    ', len(dll))
    print('cnn len    ', len(cnn))
    json.dump({'combined':combined,'dll':dll,'cnn':cnn}, open('/tmp/opencode/a01_seqs.json','w'))
    for name, seq in [('combined',combined),('dllesd',dll),('cnn',cnn)]:
        with open(f'/tmp/opencode/{name}.fa','w') as f:
            f.write(f'>{name}\n{seq}\n')
    print('done')

if __name__=='__main__':
    main()
