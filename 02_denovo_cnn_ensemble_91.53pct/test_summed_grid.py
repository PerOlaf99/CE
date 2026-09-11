#!/usr/bin/env python3
"""User idea v1: summed-channel 'peak position channel' grid -> CNN labels -> fill-in.
Runs entirely on cache_sep (no GUI), matching what our ML models were trained on.

Stage A (grid): combined normalized envelope from the 4 channels (sum of channel
   maxima, rolling-local-max normalized with a scan-dependent window so the tail
   is still visible) -> local maxima above a baseline-floored threshold.
Stage B (labels): v6 region CNN windows at grid positions.
Stage C (fill): insert missing bases where the grid deviates from expected
   spacing (median of recent inter-peak gaps).
Per-band grid via per-region norm_window tuning mimics the GUI JSONs without
hand-tuning each well."""
import os, sys, io, json
import numpy as np
os.environ.setdefault('TF_CPP_MIN_LOG_LEVEL', '3')
HERE = os.path.dirname(os.path.realpath(__file__))
ROOT = os.path.dirname(HERE)
PJ = os.path.join(ROOT, '02_denovo_cnn_ensemble_91.53pct')
sys.path.insert(0, HERE)
sys.path.insert(0, PJ)
sys.path.insert(0, os.path.join(ROOT, 'sanger_toolkit'))
import tensorflow as tf
import basecall as bc
from scipy import signal as scisig
from blast_bench import blast_eval

LABELS = 'ACGT'
W = 15
CUTS8 = (0.05, 0.15, 0.35, 0.50, 0.65, 0.80, 0.90)


def region_of(sc, n):
    f = sc / n
    r = 0
    for c in CUTS8:
        if f >= c: r += 1
        else: break
    return r


def norm_window_for(sc, n, base=180, k=0.35):
    # grow window with scan (tail peaks are ~5x wider + weaker)
    return max(base, int(norm_window_for._min) )  # placeholder not used
norm_window_for._min = 180


def combined_grid(sep, start, stop, w0=150, w1=420, thr_floor=0.02):
    """Summed-channel grid: rolling-local-max normalized envelope, local maxima
    above floor.  window grows linearly from w0 (head) to w1 (tail)."""
    n = sep.shape[0]
    env = np.maximum(sep, 0).sum(axis=1)  # summed 'peak position channel'
    # rolling local max with per-position window
    nrm = np.zeros(n)
    for i in range(start, stop):
        fr = i / n
        win = int(round(w0 + (w1 - w0) * fr))
        a, b = max(0, i - win), min(n, i + win + 1)
        locmax = env[max(0, i):min(n, i + 1)]
        nrm[i] = env[i] / (np.max(env[a:b]) + 1e-12)
    logi = nrm > 1e-9
    picks = []
    d = np.abs(scisig.find_peaks(nrm, prominence=thr_floor)[0])
    return np.array(d, dtype=np.int64)


def grid_tophat(sep, start, stop, gradient=0.5):
    """Grid via log-domain prominence: peak position channel = log(sum channels).
    Baseline = rolling minimum; peaks where signal > baseline*thr with min sep."""
    n = sep.shape[0]
    pkchan = np.log1p(np.maximum(sep, 0).sum(axis=1) * 1.0)
    # block-median baseline with block size growing for the tail
    pk = scisig.find_peaks(pkchan, prominence=0.15, width=1)[0]
    pk = pk[(pk >= start) & (pk < stop)]
    return np.array(pk, dtype=np.int64)


def win(lanes, s, n, w=W):
    lo, hi = s - w, s + w + 1
    ww = lanes[max(0, lo):min(n, hi)]
    if lo < 0 or hi > n:
        ww = np.pad(ww, ((max(0, -lo), max(0, hi - n)), (0, 0)), mode='edge')
    return ww.astype(np.float32)


def zs(X):
    mu = X.mean(1, keepdims=True); sd = X.std(1, keepdims=True) + 1e-8
    return ((X - mu) / sd).astype(np.float32)


def fill_in_pipeline(v6, sep, pos, seq, regs, n, max_gap=8, min_gap=1):
    """Fill gaps/shooulders: walk grid, if inter-peak scan gap > max_gap, scan for a
    shoulder sub-peak in the gap and CNN-label it."""
    pos = np.array(pos, dtype=np.int64)
    seq = list(seq)
    labels = list('ACGT')
    i = 0
    out_pos = []
    out_seq = []
    while i < len(pos):
        out_pos.append(int(pos[i]))
        out_seq.append(seq[i])
        if i + 1 < len(pos):
            gap = pos[i+1] - pos[i]
            if gap > max_gap:
                lo, hi = int(pos[i]) + min_gap, int(pos[i+1]) - min_gap
                if hi > lo:
                    env = np.maximum(sep, 0).sum(axis=1)
                    cand = int(np.argmax(env[lo:hi])) + lo
                    X = zs(win(sep, cand, n)[None])
                    r = region_of(cand, n)
                    P = v6[r].predict(X, verbose=0)[0]
                    lab = LABELS[int(np.argmax(P[:4]))]
                    out_pos.append(cand)
                    out_seq.append(lab)
        i += 1
    return np.array(out_pos, dtype=np.int64), ''.join(out_seq)


def main():
    well = 'A01'
    sep = np.load(os.path.join(ROOT, 'cache_sep', f'{well}.npy'))
    n = sep.shape[0]
    v6 = [tf.keras.models.load_model(os.path.join(PJ, f'base_caller_model_v6_cal8_r{r}.keras'),
                                     compile=False) for r in range(8)]

    # Stage A: summed-channel greedy grid (the GUI's "call the peak you see"),
    # on cache_sep lanes, no per-band DSP.  Try a couple of norm windows.
    for norm_win in (180, 260, 400, 800):
        shifts = (0, 0, 0, 0)
        start, stop = 0, n
        pos, gseq, groups, ints = bc.pc_call_bases_greedy(
            sep, shifts, window=3, min_frac=0.10,
            norm_window=norm_win, region=(start, stop))
        if len(pos) == 0:
            print(f'[greedy nw={norm_win}] no peaks')
            continue
        regs = np.array([region_of(int(s), n) for s in pos])
        X = np.array([win(sep, int(s), n) for s in pos])
        P = np.zeros((len(pos), 5))
        for r in range(8):
            sel = regs == r
            if sel.sum():
                P[sel] = v6[r].predict(zs(X[sel]), batch_size=256, verbose=0)
        seq = ''.join(LABELS[i] for i in np.argmax(P[:, :4], axis=1))
        res = blast_eval(seq)
        res_g = blast_eval(gseq)
        print(f'[greedy nw={norm_win}] n={len(pos)}  greedy_grid_blast={res_g}')
        print(f'[greedy nw={norm_win}] n={len(pos)}  cnn_labels_blast={res}')


if __name__ == '__main__':
    main()