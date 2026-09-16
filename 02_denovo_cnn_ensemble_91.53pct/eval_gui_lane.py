#!/usr/bin/env python3
"""eval_gui_lane.py - v10 de-novo read: GUI per-band greedy POSITIONS relabelled
by the v10 per-region CNNs (trained on GUI DSP lanes, same domain).

For each held-out well: run the GUI 12-band greedy settings, grab positions
per band, relabel each with the v10 region model feeding the SAME shifted-lane
windows used in training, BLAST vs M13 (golden standard matched_bp).
Inline greedy read (695-713 on A01) reproduced from the same positions so the
delta is pure label gain.

Usage:
  python3 eval_gui_lane.py            # all 48 held-out wells
  python3 eval_gui_lane.py --wells A03
"""
import os, sys, json, time
import numpy as np
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
os.environ.setdefault('TF_CPP_MIN_LOG_LEVEL', '3')
HERE = os.path.dirname(os.path.realpath(__file__))
ROLL = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROLL, 'sanger_toolkit'))
from PyQt5.QtWidgets import QApplication
import tensorflow as tf

LABELS = 'ACGT'
W_R = (8, 10, 12, 14, 15, 18, 24, 30)
CUTS8 = (0.05, 0.15, 0.35, 0.50, 0.65, 0.80, 0.90)
GUI_DIR = os.path.join(ROLL, 'sanger_toolkit')
BANDS = ['A01_2050_2411.json', 'A01_2411_2761.json', 'A01_2761_3010.json',
         'A01_3000_4100.json', 'A01_4100_5000.json', 'A01_5000_5800.json',
         'A01_5800_6350.json', 'A01_6350_6700.json', 'A01_6690_7350.json',
         'A01_7320_7800.json', 'A01_7800_8600.json', 'A01_8600_9332.json']
FRAME = 9647


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


def zscore(X):
    mu = X.mean(axis=1, keepdims=True)
    sd = X.std(axis=1, keepdims=True) + 1e-8
    return ((X - mu) / sd).astype(np.float32)


def load_models():
    models = {}
    for r in range(8):
        p = os.path.join(HERE, f'base_caller_model_v10_r{r}.keras')
        if os.path.exists(p):
            models[r] = tf.keras.models.load_model(p, compile=False)
    return models


def call_well(gui, well, models):
    gui.well_combo.setCurrentText(well)
    gui._load_data()
    if gui.rsd_raw is None:
        return None, None
    n = len(gui.rsd_raw)
    from dsp import dsp_shift_channel
    positions = []
    regs = []
    wX = {r: [] for r in models}
    widx = {r: [] for r in models}
    for fn in BANDS:
        r0, r1 = (int(x) for x in
                  fn.replace('A01_', '').replace('.json', '').split('_'))
        s_ = json.load(open(os.path.join(GUI_DIR, fn)))
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
        shifts = gui._effective_shifts()
        sep = np.column_stack([dsp_shift_channel(sep[:, c], int(shifts[c]))
                               for c in range(4)])
        for p in pos:
            if not (15 <= int(p) < n - 15):
                continue
            frac = float(int(p)) / FRAME
            r = region_of(frac)
            if r not in models:
                continue
            i = len(positions)
            positions.append(int(p))
            regs.append(r)
            wX[r].append(window(sep, int(p), W_R[r], n))
            widx[r].append(i)
    P = np.empty((len(positions), 4), dtype=np.float32)
    for r in models:
        if not wX[r]:
            continue
        X = zscore(np.stack(wX[r]))
        Pv = models[r].predict(X, batch_size=512, verbose=0)
        for k, i in enumerate(widx[r]):
            P[i] = Pv[k]
    labels = np.array([LABELS[P[i].argmax()] for i in range(len(positions))])
    order = np.argsort(np.array(positions))
    seq = ''.join(labels[order])
    return seq, np.array(positions)[order], np.array(regs)[order]


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('--wells', nargs='*', default=None)
    args = ap.parse_args()

    from sequencing_gui_V15 import SequencingGUI
    from plate_blast import _blast_seq
    DT = '/media/per/78B0C7DE1FA7081C/electropherogram/MB1000_M13_DT'
    app = QApplication(sys.argv)
    gui = SequencingGUI()
    if os.path.isdir(DT):
        gui.data_dir = DT
        gui._populate_wells()

    d = np.load(os.path.join(HERE, 'v3_training.npz'), allow_pickle=True)
    w_all = np.array([x.decode() if isinstance(x, bytes) else x
                      for x in d['well']])
    held = sorted({x for x, s in zip(w_all, d['split']) if not s})
    if args.wells:
        held = [w.upper() for w in args.wells if w.upper() in held]
    models = load_models()
    print('models:', {r: True for r in models}, flush=True)

    t0 = time.time()
    for wi, well in enumerate(held, 1):
        tw = time.time()
        seq, pos, regs = call_well(gui, well, models)
        if seq is None:
            print(f'{well}: no data'); continue
        rec = _blast_seq(seq)
        mb = rec['matched'] if rec else -1
        fi = rec['full_ident'] if rec else -1
        print(f'{wi}/{len(held)} {well}: len={len(seq)} matched={mb} '
              f'fullid={fi:.1f} ({time.time()-tw:.1f}s)', flush=True)
    print(f'done {time.time()-t0:.0f}s')


if __name__ == '__main__':
    main()