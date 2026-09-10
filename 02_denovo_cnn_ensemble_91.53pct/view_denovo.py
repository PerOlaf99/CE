#!/usr/bin/env python3
"""view_denovo.py - run the de-novo caller and SHOW peaks + called bases.

Plots the 4 separated channels with every final base letter drawn on its
peak (A green, C blue, G black, T red; low-confidence letters are faded).
Top panel = whole trace with the zoom window marked; bottom panel = zoom.

Usage:
  python3 view_denovo.py MB1000_M13_DT/A01.rsd                    # first 800 peak-region scans
  python3 view_denovo.py MB1000_M13_DT/A01.rsd --start 2000 --end 2800
  python3 view_denovo.py MB1000_M13_DT/A01.rsd --out A01.png      # save instead of showing
  python3 view_denovo.py ... --no-refine                          # raw CNN calls only
"""
import argparse, os, sys
__version__ = '1.0'
HERE = os.path.dirname(os.path.realpath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, ROOT)
os.environ.setdefault('TF_CPP_MIN_LOG_LEVEL', '3')

import numpy as np
import matplotlib
import matplotlib.pyplot as plt

try:
    import cimarrontv as cim
except ImportError:
    import cimarrontv_shim as cim
import dsp_core
import perfect_basecaller as pb

V10_SSM = np.array([[1.0, 1.00, 0.26, 0.46],
                    [0.07, 1.00, 0.075, 0.006],
                    [0.38, 0.33, 1.00, 1.52],
                    [0.27, 0.26, 0.189, 1.00]])
BASE_COLOR = {'A': 'green', 'C': 'blue', 'G': 'black', 'T': 'red'}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('rsd')
    ap.add_argument('--start', type=int, default=None)
    ap.add_argument('--end', type=int, default=None)
    ap.add_argument('--span', type=int, default=800,
                    help='zoom width when --start not given')
    ap.add_argument('--out')
    ap.add_argument('--no-refine', action='store_true')
    a = ap.parse_args()

    models = pb.load_ensemble([os.path.join(HERE, 'base_caller_model*.keras')])
    ch, _ = cim.read_rsd(a.rsd)
    chw = np.asarray(ch, dtype=np.float64)
    if chw.shape[0] == 4 and chw.shape[0] <= chw.shape[1]:
        chw = chw.T
    _, _, _, _, sep, _ = dsp_core.full_pipeline(
        chw, (5, 11, 10, 10), 'AsyLS', 50010, 'Butterworth', 5, 9,
        V10_SSM, matrix_apply_point='smoothed')

    eng = pb.build_engine()
    res = eng.call(chw, np.arange(chw.shape[1]))
    seq, conf, ps = [], [], []
    for base, pk in zip(res.sequence, res.peaks):
        if base in pb.LABELS:
            seq.append(base)
            ps.append(int(round(pk.time)))
            conf.append(30)
    probs = pb.cnn_probs(models, chw, ps)
    pred = probs.argmax(1)
    seq = [pb.LABELS[i] for i in pred]
    conf = [pb.phred(probs[k, i]) for k, i in enumerate(pred)]
    scans = np.asarray(ps)
    tag = 'raw CNN'
    if not a.no_refine:
        seq_s, conf_s, scans = pb.refine_denovo(models, chw, seq, conf, scans)
        seq, conf = list(seq_s), list(conf_s)
        tag = 'refined de-novo'

    lo = a.start if a.start is not None else int(scans.min())
    hi = a.end if a.end is not None else lo + a.span

    fig, (ax1, ax2) = plt.subplots(
        2, 1, figsize=(14, 8), height_ratios=[1, 2], sharex=False)
    shades = ['#999999', '#bbbbbb', '#888888', '#aaaaaa']
    for c in range(4):
        ax1.plot(sep[:, c], lw=.5, color=shades[c])
        ax2.plot(sep[:, c], lw=1.0, color=shades[c])
    off = 0.08 * float(sep.max())
    for s, b, q in zip(scans, seq, conf):
        y = float(sep[s].max()) + off * (1.6 if b in BASE_COLOR else 1.0)
        for ax in (ax1, ax2):
            ax.text(s, y, b, fontsize=9, ha='center',
                    color=BASE_COLOR.get(b, 'magenta'),
                    alpha=min(1.0, 0.35 + q / 40.0))
    ax1.axvspan(lo, hi, color='orange', alpha=.15)
    ax1.set_title(f'{os.path.basename(a.rsd)} - {tag} - {len(seq)} bases '
                  f'(orange band = zoom)')
    ax2.set_xlim(lo, hi)
    ax2.set_xlabel('scan')
    fig.tight_layout()
    if a.out:
        fig.savefig(a.out, dpi=130)
        print('saved', a.out)
    else:
        plt.show()


if __name__ == '__main__':
    main()
