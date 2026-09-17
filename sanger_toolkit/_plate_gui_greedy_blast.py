import os, sys, json, csv, time
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

HERE = os.path.dirname(os.path.abspath(__file__))
os.chdir(HERE)
sys.path.insert(0, HERE)

BANDS = ['A01_2050_2411.json','A01_2411_2761.json','A01_2761_3010.json','A01_3000_4100.json',
         'A01_4100_5000.json','A01_5000_5800.json','A01_5800_6350.json','A01_6350_6700.json',
         'A01_6690_7350.json','A01_7320_7800.json','A01_7800_8600.json','A01_8600_9332.json']
OUT = '_plate_gui_greedy.csv'
FULLDIR = '_plate_gui_greedy_reads'
os.makedirs(FULLDIR, exist_ok=True)

def main():
    import numpy as np
    from PyQt5.QtWidgets import QApplication
    from sequencing_gui_V15 import SequencingGUI
    from plate_blast import _blast_seq

    d = np.load(os.path.join(HERE,'..','02_denovo_cnn_ensemble_91.53pct','v3_training.npz'), allow_pickle=True)
    w = np.array([x.decode() if isinstance(x,bytes) else x for x in d['well']])
    s = d['split']
    wells = sorted({x for x,si in zip(w,s) if not bool(si)})

    done = set()
    if os.path.exists(OUT):
        with open(OUT) as f:
            for row in csv.DictReader(f):
                done.add(row['well'])
    todo = [x for x in wells if x not in done]
    print(f'wells total={len(wells)} done={len(done)} todo={len(todo)}', flush=True)

    app = QApplication(sys.argv)
    gui = SequencingGUI()
    bl = _blast_seq

    t0 = time.time()
    for wi, well in enumerate(todo, 1):
        tw = time.time()
        gui.well_combo.setCurrentText(well)
        gui._load_data()
        full = []
        for jf in BANDS:
            s_ = json.load(open(jf))
            r0, r1 = map(int, jf.replace('A01_','').replace('.json','').split('_'))
            gui.load_settings_from_dict(s_)
            gui.region_auto_check.setChecked(False)
            gui.region_hybrid_check.setChecked(False)
            gui.region_start_spin.setValue(r0)
            gui.region_stop_spin.setValue(r1)
            gui._run_basecall()
            full.append(gui._manual_sequence or '')
        seq = ''.join(full).strip()
        with open(os.path.join(FULLDIR, well+'.txt'), 'w') as f:
            f.write(seq)
        rec = _blast_seq(seq)
        mb = rec['matched'] if rec is not None else -1
        best = rec['full_ident'] if rec is not None else -1
        with open(OUT, 'a', newline='') as f:
            cw = csv.writer(f)
            if wi == 1 and not done:
                cw.writerow(['well','full_len','matched_bp','best_id','secs'])
            cw.writerow([well, len(seq), mb, best, round(time.time()-tw,1)])
        print(f'{wi}/{len(todo)} {well}: len={len(seq)} matched={mb} best_id={best} ({time.time()-tw:.1f}s)', flush=True)

    print(f'done in {time.time()-t0:.0f}s')

if __name__ == '__main__':
    main()