#!/usr/bin/env python3
"""build_gui_lane_set.py - v10 training set from the GUI's OWN per-band DSP lanes.

The v9/v6 CNNs were trained on `cache_sep` separated lanes, but the GUI greedy
labels from ITS OWN per-band dsp_full_pipeline lane stack (after mobility
shift) -> proven input-domain mismatch (CNN 90.6% vs greedy 94.3% at the same
GUI positions).  v10 closes it: windows are extracted from the GUI's per-band
separated lanes (shifted exactly like pc_call_bases_greedy), centered on the
GUI greedy positions, labelled with the nearest ESD base (<=6 scans).

Same 48/48 well split as v6/v9 (v3_training.npz, split=1=TRAIN well).
Adaptive per-region half-width W_R identical to v9.

Output: 02_denovo_cnn_ensemble_91.53pct/gui_lane_r{r}.npz
  X (N, 2*W_R[r]+1, 4), y int, split bool, well obj, scan int.  No jitter:
  eval consumes the exact same detector positions.
"""
import os, sys, json
import numpy as np
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
os.environ.setdefault('TF_CPP_MIN_LOG_LEVEL', '3')
HERE = os.path.dirname(os.path.realpath(__file__))
ROLL = os.path.dirname(HERE)
CNN_DIR = os.path.join(ROLL, '02_denovo_cnn_ensemble_91.53pct')
sys.path.insert(0, HERE)
sys.path.insert(0, CNN_DIR)
from PyQt5.QtWidgets import QApplication

W_R = (8, 10, 12, 14, 15, 18, 24, 30)
CUTS8 = (0.05, 0.15, 0.35, 0.50, 0.65, 0.80, 0.90)
BANDS = ['A01_2050_2411.json', 'A01_2411_2761.json', 'A01_2761_3010.json',
         'A01_3000_4100.json', 'A01_4100_5000.json', 'A01_5000_5800.json',
         'A01_5800_6350.json', 'A01_6350_6700.json', 'A01_6690_7350.json',
         'A01_7320_7800.json', 'A01_7800_8600.json', 'A01_8600_9332.json']
TOL = 6
BASE_MAP = {'A': 0, 'C': 1, 'G': 2, 'T': 3}


def region_of(f, cuts=CUTS8):
    r = 0
    for c in cuts:
        if f >= c:
            r += 1
        else:
            break
    return r


def window(lanes, s, w, n):
    lo, hi = s - w, s + w + 1
    win = lanes[max(0, lo):min(n, hi)]
    if lo < 0 or hi > n:
        win = np.pad(win, ((max(0, -lo), max(0, hi - n)), (0, 0)), mode='edge')
    return win.astype(np.float32)


def main():
    import threading
    from sequencing_gui_V15 import SequencingGUI
    from extract_training_data import parse_esd

    app = QApplication(sys.argv)
    gui = SequencingGUI()
    DT_DIR = '/media/per/78B0C7DE1FA7081C/electropherogram/MB1000_M13_DT'
    if os.path.isdir(DT_DIR):
        gui.data_dir = DT_DIR
        gui._populate_wells()

    d = np.load(os.path.join(CNN_DIR, 'v3_training.npz'), allow_pickle=True)
    w_all = np.array([x.decode() if isinstance(x, bytes) else x
                      for x in d['well']])
    tr = {x for x, s in zip(w_all, d['split']) if s}
    wells = sorted({x for x in w_all})
    wells_out = [x for x in wells
                 if os.path.exists(os.path.join(gui.data_dir, x + '.rsd'))]

    acc = {r: {'X': [], 'y': [], 'split': [], 'well': [], 'scan': []}
           for r in range(8)}
    seen = set()

    for k, wname in enumerate(wells_out):
        E = parse_esd(os.path.join(
            gui.data_dir,
            (gui.esd_combo.currentData() or ''),
            wname + '.esd'))
        if 'sequence' not in E or 'peak_positions' not in E:
            continue
        pp = np.array([int(s) for s in E['peak_positions']])
        seq = np.asarray(list(E['sequence']))
        gui.well_combo.setCurrentText(wname)
        gui._load_data()
        if gui.rsd_raw is None:
            continue
        n = len(gui.rsd_raw)
        is_tr = wname in tr
        ncol = 0
        for fn in BANDS:
            r0, r1 = (int(x) for x in
                      fn.replace('A01_', '').replace('.json', '').split('_'))
            s_ = json.load(open(os.path.join(HERE, fn)))
            gui.load_settings_from_dict(s_)
            gui.region_auto_check.setChecked(False)
            gui.region_hybrid_check.setChecked(False)
            gui.region_start_spin.setValue(r0)
            gui.region_stop_spin.setValue(r1)
            gui._run_basecall()
            pos = getattr(gui, '_last_positions', None)
            if pos is None or len(pos) == 0:
                continue
            pos = np.asarray(pos, dtype=np.int64)
            sep = getattr(gui, '_last_separated', None)
            if sep is None:
                continue
            # The greedy caller labels from the SHIFTED lanes -> same as the CNN
            # should see for this band.
            from dsp import dsp_shift_channel
            shifts = gui._effective_shifts()
            sep = np.column_stack([dsp_shift_channel(sep[:, c], int(shifts[c]))
                                   for c in range(4)])
            for p in pos:
                key = (wname, int(p))
                if key in seen:
                    continue
                seen.add(key)
                dd = np.abs(pp - int(p))
                j = int(np.argmin(dd))
                if dd[j] > TOL or seq[j] not in BASE_MAP:
                    continue
                if not (15 <= int(p) < n - 15):
                    continue
                frac = float(int(p)) / 9647.0
                r = region_of(frac)
                W = W_R[int(r)]
                acc[int(r)]['X'].append(window(sep, int(p), W, n))
                acc[int(r)]['y'].append(BASE_MAP[seq[j]])
                acc[int(r)]['split'].append(is_tr)
                acc[int(r)]['well'].append(wname)
                acc[int(r)]['scan'].append(int(p))
            ncol += len(pos)
            grey = getattr(gui, '_manual_sequence', '') or ''
            print(f'  {wname} {fn}: n={len(pos)} greedy_n={len(grey)}',
                  flush=True)
        kept = sum(len(acc[r]['y']) for r in range(8))
        print(f'{k + 1}/{len(wells_out)} {wname}: cols={ncol} matched_esd={kept}',
              flush=True)

    for r in range(8):
        L = 2 * W_R[r] + 1
        if len(acc[r]['y']) == 0:
            print(f'region{r}: no samples'); continue
        X = np.stack(acc[r]['X'])
        y = np.array(acc[r]['y'], np.int64)
        split = np.array(acc[r]['split'], bool)
        well = np.array(acc[r]['well'], object)
        scan = np.array(acc[r]['scan'], np.int64)
        out = os.path.join(CNN_DIR, f'gui_lane_r{r}.npz')
        np.savez_compressed(out, X=X, y=y, split=split, well=well, scan=scan)
        print(f'region{r}: X={X.shape} (2W+1={L}) n_tr={split.sum()} '
              f'n_va={(~split).sum()}')


if __name__ == '__main__':
    main()