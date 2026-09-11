#!/usr/bin/env python3
"""eval_v8_shift.py - CEILING with per-well frame alignment.

For each held-out well, sweep a small per-well scan offset d=-4..+1 for the
DLL esd peak positions (cache_sep may be mobility-shifted relative to the esd
frame).  Choose d maximizing the v6 CNN's agreement with the esd base call,
then label with v8 corrector, BLAST.  Proves the upper bound when the
esd<->calibrated-lane frame is aligned per well."""
import os, sys
import numpy as np
os.environ.setdefault('TF_CPP_MIN_LOG_LEVEL', '3')
HERE = os.path.dirname(os.path.realpath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE); sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'sanger_toolkit'))
from extract_training_data import parse_esd
from blast_bench import blast_eval
import bandstat as bs
import tensorflow as tf

GT = os.path.join(ROOT, 'ground_truth', 'MB1000_M13_DT_Cp312_MD1')
SEP = os.path.join(ROOT, 'cache_sep')
W = 15
LABELS = 'ACGT'
CUTS8 = (0.05, 0.15, 0.35, 0.50, 0.65, 0.80, 0.90)


def region_of(f, cuts=CUTS8):
    r = 0
    for c in cuts:
        if f >= c: r += 1
        else: break
    return r


def window(lanes, s, w=W):
    n = len(lanes); lo, hi = s - w, s + w + 1
    win = lanes[max(0, lo):min(n, hi)]
    if lo < 0 or hi > n:
        win = np.pad(win, ((max(0, -lo), max(0, hi - n)), (0, 0)), mode='edge')
    return win.astype(np.float32)


def zscore(X):
    mu = X.mean(1, keepdims=True); sd = X.std(1, keepdims=True) + 1e-8
    return ((X - mu) / sd).astype(np.float32)


def main():
    nreg = 8
    v6 = [tf.keras.models.load_model(f'base_caller_model_v6_cal8_r{r}.keras',
                                     compile=False) for r in range(nreg)]
    v8 = [tf.keras.models.load_model(f'base_caller_model_v8_corr_r{r}.keras',
                                     compile=False) for r in range(nreg)]
    dtr = np.load('corr_training.npz', allow_pickle=True)
    tr = dtr['X'][dtr['split']]
    mu, sd = tr.mean(0), tr.std(0) + 1e-8

    dw = np.load('v3_training.npz', allow_pickle=True)
    wells = sorted(set(w.decode() if isinstance(w, bytes) else w for w in dw['well']
                       if not bool(dw['split'][np.where(dw['well'] == w)[0][0]])))
    m8, m_dll = [], []
    best_d = []
    for well in wells:
        E = parse_esd(os.path.join(GT, well + '.esd'))
        sep = np.load(os.path.join(SEP, well + '.npy'))
        pp = np.array([int(p) for p in E['peak_positions']])
        seq = np.asarray(list(E['sequence']))
        ok = (pp >= 30) & (pp < len(sep) - 30) & np.isin(seq, list('ACGT'))
        pp, seq = pp[ok], seq[ok]
        if len(pp) < 50:
            m8.append(0); m_dll.append(0); best_d.append(0); continue
        fr = np.arange(len(pp), dtype=float) / max(1, len(pp) - 1)
        regs = np.array([region_of(f) for f in fr])
        # sweep shift to find frame alignment
        best = (-1, 0)
        for d in range(-4, 2):
            pp2 = np.clip(pp + d, 25, len(sep) - 26)
            Xc = np.array([window(sep, int(s)) for s in pp2])
            P = np.zeros((len(pp), 5))
            for r in range(nreg):
                sel = regs == r
                if sel.sum():
                    P[sel] = v6[r].predict(zscore(Xc[sel]), batch_size=256, verbose=0)
            pred = np.array([LABELS[i] for i in P[:, :4].argmax(1)])
            acc = (pred == seq).mean()
            if acc > best[0]:
                best = (acc, d)
        _, d = best
        best_d.append(d)
        pp2 = np.clip(pp + d, 25, len(sep) - 26)
        Xc = np.array([window(sep, int(s)) for s in pp2])
        P = np.zeros((len(pp), 5))
        for r in range(nreg):
            sel = regs == r
            if sel.sum():
                P[sel] = v6[r].predict(zscore(Xc[sel]), batch_size=256, verbose=0)
        F = bs.band_features(sep, pp2)
        Xall = np.concatenate([P[:, :4], F], axis=1)
        Xn = ((Xall - mu) / sd).astype(np.float32)
        p8 = np.zeros((len(pp), 4))
        for r in range(nreg):
            sel = regs == r
            if sel.sum():
                p8[sel] = v8[r].predict(Xn[sel], batch_size=512, verbose=0)
        read8 = ''.join(LABELS[i] for i in p8.argmax(1))
        b_dll = blast_eval(E['sequence'])
        b8 = blast_eval(read8)
        m_dll.append(b_dll['matched'] if b_dll else 0)
        m8.append(b8['matched'] if b8 else 0)
    print(f'wells={len(wells)}  DLL-pos+shift+v8 = {np.mean(m8):.1f}  DLL = {np.mean(m_dll):.1f}')
    print('shift distribution:', {d: best_d.count(d) for d in set(best_d)})
    print(' by-well (DLL v8shift):')
    bad = [w for w, a, b, d in zip(wells, m_dll, m8, best_d) if b < a - 20]
    print('  biggest deficits (DLL v8shift shift):',
          ' '.join(f'{w}:{a}:{b}:{d}' for w, a, b, d in zip(wells, m_dll, m8, best_d)
                   if b < a - 20))


if __name__ == '__main__':
    main()