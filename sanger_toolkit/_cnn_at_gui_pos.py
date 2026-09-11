#!/usr/bin/env python3
"""Decisive test: are r2-r5 non-100% due to POSITIONS or LABELS?

Run the GUI's 12 per-band greedy settings on A01 (98.09% identity known).
For each band: get greedy positions + greedy sequence.  Then re-label those
positions with the v6 CNN (per-region) and with the ESD truth, and compare
per region + overall.  This isolates whether the CNN or the detector is the
bottleneck at GUI-detected positions."""
import os, sys, json, re
import numpy as np
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
os.environ.setdefault('TF_CPP_MIN_LOG_LEVEL', '3')
HERE = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0, HERE)
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, '02_denovo_cnn_ensemble_91.53pct'))
sys.path.insert(0, os.path.join(ROOT, 'sanger_toolkit'))
from PyQt5.QtWidgets import QApplication
import tensorflow as tf

app = QApplication(sys.argv)
from sequencing_gui_V15 import SequencingGUI
import extract_training_data as etd
from extract_training_data import parse_esd
import numpy as np

CH = ['Channel1', 'Channel2', 'Channel3', 'Channel4']
LABELS = 'ACGT'
W = 15
CUTS8 = (0.05, 0.15, 0.35, 0.50, 0.65, 0.80, 0.90)

FILES = [
 'A01_2050_2411.json', 'A01_2411_2761.json', 'A01_2761_3010.json',
 'A01_3000_4100.json', 'A01_4100_5000.json', 'A01_5000_5800.json',
 'A01_5800_6350.json', 'A01_6350_6700.json', 'A01_6690_7350.json',
 'A01_7320_7800.json', 'A01_7800_8600.json', 'A01_8600_9332.json',
]


def region_of(sc):
    f = sc / 9647
    r = 0
    for c in CUTS8:
        if f >= c: r += 1
        else: break
    return r


def window(lanes, s, w=W):
    n = len(lanes)
    lo, hi = s - w, s + w + 1
    win = lanes[max(0, lo):min(n, hi)]
    if lo < 0 or hi > n:
        win = np.pad(win, ((max(0, -lo), max(0, hi - n)), (0, 0)), mode='edge')
    return win.astype(np.float32)


def zscore(X):
    mu = X.mean(axis=1, keepdims=True)
    sd = X.std(axis=1, keepdims=True) + 1e-8
    return ((X - mu) / sd).astype(np.float32)


def win_range(fn):
    return tuple(int(x) for x in re.search(r'(\d+)_(\d+)\.json', fn).groups())


def main():
    d = np.load('/media/per/78B0C7DE1FA7081C/electropherogram/02_denovo_cnn_ensemble_91.53pct/signal_training.npz', allow_pickle=True)
    wells = sorted(set(w.decode() if isinstance(w, bytes) else w for w in d['well']))
    # v6 CNN
    v6 = [tf.keras.models.load_model(
        f'/media/per/78B0C7DE1FA7081C/electropherogram/02_denovo_cnn_ensemble_91.53pct/base_caller_model_v6_cal8_r{r}.keras',
        compile=False) for r in range(8)]
    sep = np.load('/media/per/78B0C7DE1FA7081C/electropherogram/cache_sep/A01.npy')

    gui = SequencingGUI()
    gui.well_combo.setCurrentText('A01')
    gui._load_data()
    all_pos = []
    all_greedy = []
    for fn in FILES:
        r0, r1 = win_range(fn)
        dk = json.load(open(os.path.join(HERE, fn)))
        gui.load_settings_from_dict(dk)
        gui.region_auto_check.setChecked(False)
        gui.region_hybrid_check.setChecked(False)
        gui.region_start_spin.setValue(r0)
        gui.region_stop_spin.setValue(r1)
        gui._run_basecall()
        pos = np.array(gui._last_positions, dtype=np.int64)
        seq = (gui._manual_sequence or '')
        # keep only ACGT, align to positions 1:1
        keep = np.array([c in 'ACGT' for c in seq])
        if len(pos) != len(keep):
            print(f'{fn}: pos {len(pos)} != seq {len(seq)}')
        all_pos.append(pos[keep])
        all_greedy.append(''.join(np.array(list(seq))[keep]))
        print(f'{fn} [{r0},{r1}]: n={len(pos)} greedy-acgt={keep.sum()}')
    pos = np.concatenate(all_pos)
    greedy = ''.join(all_greedy)
    # BUT the GUI's separated is computed inside gui; the CNN should be fed the
    # same DSP that produced positions -> use cache_sep lanes (frame-consistent).
    # (Note: GUI computed its own separated via _process; using cache_sep is the
    # same data our v6 CNN was trained on.)
    fr = np.arange(len(pos), dtype=float) / max(1, len(pos) - 1)
    regs = np.array([region_of(s) for s in pos])
    X = np.array([window(sep, int(s)) for s in pos])
    P = np.zeros((len(pos), 5))
    for r in range(8):
        sel = regs == r
        if sel.sum():
            P[sel] = v6[r].predict(zscore(X[sel]), batch_size=256, verbose=0)
    cnn = ''.join(LABELS[i] for i in P[:, :4].argmax(1))

    E = parse_esd('/media/per/78B0C7DE1FA7081C/electropherogram/ground_truth/MB1000_M13_DT_Cp312_MD1/A01.esd')
    pp = np.array([int(p) for p in E['peak_positions']])
    eseq = np.array(list(E['sequence']))
    # per-region agreement of greedy and cnn, via nearest esd within 6
    stat = {r: [0, 0, 0, 0] for r in range(8)}  # greedy-ok,greedy-n,cnn-ok,cnn-n
    for i, p in enumerate(pos):
        d = np.abs(pp - p)
        j = int(np.argmin(d))
        if d[j] > 6 or eseq[j] not in 'ACGT':
            continue
        r = regs[i]
        if r < 8:
            stat[r][1] += 1
            stat[r][3] += 1
            if greedy[i] == eseq[j]: stat[r][0] += 1
            if cnn[i] == eseq[j]: stat[r][2] += 1
    print('\nregion  greedy  cnn     (matched / n)')
    for r in range(8):
        g, gn, c, cn = stat[r]
        if gn:
            print(f'  r{r}: {100*g/gn:5.1f}%   {100*c/cn:5.1f}%   ({gn} matched)')
    # overall
    g = sum(s[0] for s in stat.values()); gn = sum(s[1] for s in stat.values())
    c = sum(s[2] for s in stat.values()); cn = sum(s[3] for s in stat.values())
    print(f'\nOVERALL: greedy {100*g/gn:.1f}%  cnn {100*c/cn:.1f}%  (n={gn})')


if __name__ == '__main__':
    main()