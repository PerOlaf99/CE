#!/usr/bin/env python3
"""eval_v7_esdpos.py - CEILING test for v7 (calibrated lanes + BandStat side-tower):
label the DLL's OWN esd peak positions, build the read, BLAST it.  Compares
v7(feat) vs v6(cal-only) at the same positions to isolate what the DSP features
add on top of the CNN on Cimarron's own call sites."""
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


def region_of(f, cuts):
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


def feat_norm(F):
    scale = np.array([1.6, 40.0, 30.0, 12.0, 6.0, 0.1], np.float32)
    return (np.clip(F / scale, 0, 4)).astype(np.float32)


def main():
    prefix = sys.argv[1] if len(sys.argv) > 1 else 'base_caller_model_v7_feat'
    nreg = 8
    v7 = [tf.keras.models.load_model(f'{prefix}_r{r}.keras', compile=False) for r in range(nreg)]

    d = np.load(os.path.join(HERE, 'v3_training.npz'), allow_pickle=True)
    wells = sorted(set(w.decode() if isinstance(w, bytes) else w for w in d['well']
                       if not bool(d['split'][np.where(d['well'] == w)[0][0]])))
    m7, m6, m_dll = [], [], []
    for well in wells:
        E = parse_esd(os.path.join(GT, well + '.esd'))
        sep = np.load(os.path.join(SEP, well + '.npy'))
        pp = np.array([int(p) for p in E['peak_positions']])
        ok = (pp >= 20) & (pp < len(sep) - 20)
        pp = pp[ok]
        fr = np.arange(len(pp), dtype=float) / max(1, len(pp) - 1)
        regs = np.array([region_of(f, CUTS8) for f in fr])
        Xc = np.array([window(sep, int(s)) for s in pp])
        Ff = feat_norm(bs.band_features(sep, pp))
        p7 = np.zeros((len(pp), 5))
        for r in range(nreg):
            sel = regs == r
            if sel.sum():
                p7[sel] = v7[r].predict([zscore(Xc[sel]), Ff[sel]], batch_size=256, verbose=0)
        read7 = ''.join(LABELS[i] for i in p7[:, :4].argmax(1))
        b7 = blast_eval(read7)
        b_dll = blast_eval(E['sequence'])
        m_dll.append(b_dll['matched'] if b_dll else 0)
        m7.append(b7['matched'] if b7 else 0)
    print(f'wells={len(wells)}  DLL-pos+v7(feat) matched={np.mean(m7):.1f}  DLL matched={np.mean(m_dll):.1f}')
    print(' per-well:', ' '.join(f'{w}:{a}->{b}' for w, a, b in zip(wells, m_dll, m7)))


if __name__ == '__main__':
    main()