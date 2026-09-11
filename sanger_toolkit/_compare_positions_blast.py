#!/usr/bin/env python3
"""Compare DLL positions vs GUI-per-band positions on A01, then BLAST
greedy-at-GUI positions (matching the 98.09% _full_scan_esd_compare result)"""
import os, sys, json, re
import numpy as np
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
os.environ.setdefault('TF_CPP_MIN_LOG_LEVEL', '3')
HERE = os.path.dirname(os.path.realpath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, '02_denovo_cnn_ensemble_91.53pct'))
from PyQt5.QtWidgets import QApplication
app = QApplication(sys.argv)
from sequencing_gui_V15 import SequencingGUI
print('GUI module file:', __import__('sequencing_gui_V15').__file__)
from sequencing_gui_V15 import SequencingGUI
from extract_training_data import parse_esd
import dll_peakdet as dp
from blast_bench import blast_eval as blast_seq

FILES = [
 'A01_2050_2411.json', 'A01_2411_2761.json', 'A01_2761_3010.json',
 'A01_3000_4100.json', 'A01_4100_5000.json', 'A01_5000_5800.json',
 'A01_5800_6350.json', 'A01_6350_6700.json', 'A01_6690_7350.json',
 'A01_7320_7800.json', 'A01_7800_8600.json', 'A01_8600_9332.json',
]
CUTS8 = (0.05, 0.15, 0.35, 0.50, 0.65, 0.80, 0.90)
N = 9647

def region_of(sc):
    f = sc / N
    r = 0
    for c in CUTS8:
        if f >= c: r += 1
        else: break
    return r

def win_range(fn):
    m = re.search(r'A01_(\d+)_(\d+)\.json', fn)
    return int(m.group(1)), int(m.group(2))

def main():
    sep = np.load(os.path.join(ROOT, 'cache_sep/A01.npy'))
    E = parse_esd(os.path.join(ROOT, 'MB1000_M13_DT/MB1000_M13_DT_Cp312_MD1/A01.esd'))
    pp = np.array([int(p) for p in E['peak_positions']])
    eseq = ''.join(c for c in E['sequence'] if c in 'ACGTN')

    # --- DLL positions ---
    dll_p = np.array(dp.dll_peaks(sep, env_floor_frac=None)[0], dtype=np.int64)

    # --- GUI greedy positions + sequence ---
    gui = SequencingGUI()
    gui.well_combo.setCurrentText('A01')
    gui._load_data()
    gui_pos_all = []
    gui_seqs = []
    for fn in FILES:
        r0, r1 = win_range(fn)
        dk = json.load(open(os.path.join(HERE, fn)))
        gui.load_settings_from_dict(dk)
        gui.region_auto_check.setChecked(False)
        gui.region_hybrid_check.setChecked(False)
        gui.region_start_spin.setValue(r0)
        gui.region_stop_spin.setValue(r1)
        gui._run_basecall()
        lp = getattr(gui, '_last_positions', None)
        pos = np.array([] if lp is None else lp, dtype=np.int64)
        seq = gui._manual_sequence or ''
        if len(pos) == 0:
            print(f'  WARN: {fn} produced no positions; status="{gui.status.text()}"')
        keep = np.array([c in 'ACGT' for c in seq])
        n_keep = int(keep.sum())
        if len(pos) != len(keep):
            print(f'  WARN: {fn} pos {len(pos)} != seq {len(seq)}, trimming to {min(len(pos),len(keep))}')
            n_keep = min(len(pos), len(keep), int(keep[:min(len(pos),len(keep))].sum()))
            pos = pos[:n_keep]
            keep = keep[:n_keep]
            seq = seq[:n_keep]
        gui_pos_all.append(pos[keep])
        gui_seqs.append(''.join(np.array(list(seq))[keep]))
    gui_pos = np.concatenate(gui_pos_all)
    gui_seq = ''.join(gui_seqs)

    # --- Position centering comparison ---
    print('=== Position centering: nearest-ESD peak distance (scans) ===\n')
    print('Region | N_esd | N_gui | N_dll | GUI_med | GUI>3% | DLL_med | DLL>3% | DLL>6%')
    for r in range(8):
        sc0 = 0 if r == 0 else int(CUTS8[r-1] * N)
        sc1 = int(CUTS8[r] * N) if r < len(CUTS8) else N
        esd_r = pp[(pp >= sc0) & (pp < sc1)]
        gp = gui_pos[(gui_pos >= sc0) & (gui_pos < sc1)]
        dp_r = dll_p[(dll_p >= sc0) & (dll_p < sc1)]
        if len(esd_r) == 0:
            print(f'  r{r}:  esd={len(esd_r):3d}  SKIP')
            continue
        gui_d = np.min(np.abs(gp[:, None] - esd_r[None, :]), axis=1) if len(gp) else np.array([])
        dll_d = np.min(np.abs(dp_r[:, None] - esd_r[None, :]), axis=1) if len(dp_r) else np.array([])
        gm = np.median(gui_d) if len(gui_d) else -1
        dm = np.median(dll_d) if len(dll_d) else -1
        g3 = 100 * (gui_d > 3).mean() if len(gui_d) else -1
        d3 = 100 * (dll_d > 3).mean() if len(dll_d) else -1
        d6 = 100 * (dll_d > 6).mean() if len(dll_d) else -1
        print(f'  r{r}:  esd={len(esd_r):3d}  gui={len(gp):3d}  dll={len(dp_r):3d}  '
              f'GUI_med={gm:4.1f} GUI>3={g3:4.1f}%  DLL_med={dm:4.1f} DLL>3={d3:4.1f}% DLL>6={d6:4.1f}%')

    # --- BLAST: greedy at GUI positions vs ESD ---
    print('\n=== BLAST: greedy-at-GUI-positions vs ESD ===')
    res = blast_seq(gui_seq)
    print(res)

    # --- BLAST: v6-CNN at DLL-positions vs ESD ---
    from tensorflow import keras
    LABELS = 'ACGT'
    def zs(X):
        mu = X.mean(1, keepdims=True); sd = X.std(1, keepdims=True) + 1e-8
        return ((X - mu) / sd).astype(np.float32)
    v6 = [keras.models.load_model(
        os.path.join(os.path.dirname(HERE), '02_denovo_cnn_ensemble_91.53pct',
                     f'base_caller_model_v6_cal8_r{r}.keras'), compile=False)
        for r in range(8)]
    CUTS = (0.05, 0.15, 0.35, 0.50, 0.65, 0.80, 0.90)

    def region_of_v6(sc):
        f = sc / N
        r = 0
        for c in CUTS:
            if f >= c: r += 1
            else: break
        return r

    fr = np.arange(len(dll_p), dtype=float) / max(1, len(dll_p) - 1)
    v6_regs = np.array([region_of_v6(s) for s in dll_p])
    W = 15
    def win(lanes, s):
        lo, hi = s - W, s + W + 1
        w = lanes[max(0, lo):min(N, hi)]
        if lo < 0 or hi > N:
            w = np.pad(w, ((max(0, -lo), max(0, hi - N)), (0, 0)), mode='edge')
        return w.astype(np.float32)
    X = np.array([win(sep, int(s)) for s in dll_p])
    P = np.zeros((len(dll_p), 5))
    for r in range(8):
        sel = v6_regs == r
        if sel.sum():
            P[sel] = v6[r].predict(zs(X[sel]), batch_size=256, verbose=0)
    v6_seq = ''.join(LABELS[i] for i in P[:, :4].argmax(1))
    v6_seq = ''.join(c for c in v6_seq if c in 'ACGT')

    print('\n=== BLAST: v6-CNN at DLL-positions vs ESD ===')
    res2 = blast_seq(v6_seq)
    print(res2)

if __name__ == '__main__':
    main()
