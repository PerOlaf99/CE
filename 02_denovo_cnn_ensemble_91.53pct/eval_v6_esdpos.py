#!/usr/bin/env python3
"""eval_v6_esdpos.py - CEILING test: label the DLL's OWN esd peak positions with
our calibrated region CNNs, build the read, BLAST it.  If this matches ~DLL,
positions (not labels) are the sole binding constraint; if not, labels still
cap us.  Uses only the DLL's *positions*, never its base calls."""
import os, sys
import numpy as np
os.environ.setdefault('TF_CPP_MIN_LOG_LEVEL', '3')
HERE = os.path.dirname(os.path.realpath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE); sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'sanger_toolkit'))
from extract_training_data import parse_esd
from blast_bench import blast_eval
import tensorflow as tf

GT = os.path.join(ROOT, 'ground_truth', 'MB1000_M13_DT_Cp312_MD1')
SEP = os.path.join(ROOT, 'cache_sep')
W = 15
LABELS = 'ACGT'
CUTS8 = (0.05, 0.15, 0.35, 0.50, 0.65, 0.80, 0.90)
CUTS4 = (0.15, 0.65, 0.90)

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
        win = np.pad(win, ((max(0,-lo), max(0,hi-n)), (0,0)), mode='edge')
    return win.astype(np.float32)

def zscore(X):
    mu = X.mean(1, keepdims=True); sd = X.std(1, keepdims=True) + 1e-8
    return ((X - mu) / sd).astype(np.float32)

def main():
    prefix = sys.argv[1] if len(sys.argv) > 1 else 'base_caller_model_v6_cal8'
    nreg = int(sys.argv[2]) if len(sys.argv) > 2 else 8
    cuts = CUTS8 if nreg == 8 else CUTS4
    do4 = '-4' in sys.argv
    v6 = [tf.keras.models.load_model(f'{prefix}_r{r}.keras', compile=False) for r in range(nreg)]
    v3 = [tf.keras.models.load_model(f'base_caller_model_v3_{nm}.keras', compile=False)
          for nm in ['begin', 'mid', 'tail', 'tailtail']] if do4 else None

    d = np.load(os.path.join(HERE, 'v3_training.npz'), allow_pickle=True)
    wells = sorted(set(w.decode() if isinstance(w, bytes) else w for w in d['well']
                       if not bool(d['split'][np.where(d['well'] == w)[0][0]])))
    m_dll, m6, m4 = [], [], []
    for well in wells:
        E = parse_esd(os.path.join(GT, well + '.esd'))
        sep = np.load(os.path.join(SEP, well + '.npy'))
        pp = np.array([int(p) for p in E['peak_positions']])
        ok = (pp >= 20) & (pp < len(sep) - 20)
        pp = pp[ok]
        fr = np.arange(len(pp), dtype=float) / max(1, len(pp) - 1)
        regs = np.array([region_of(f, cuts) for f in fr])
        Xc = np.array([window(sep, int(s)) for s in pp])
        p6 = np.zeros((len(pp), 5))
        for r in range(nreg):
            sel = regs == r
            if sel.sum(): p6[sel] = v6[r].predict(zscore(Xc[sel]), batch_size=256, verbose=0)
        read6 = ''.join(LABELS[i] for i in p6[:, :4].argmax(1))
        b6 = blast_eval(read6)
        b_dll = blast_eval(E['sequence'])
        m_dll.append(b_dll['matched'] if b_dll else 0)
        m6.append(b6['matched'] if b6 else 0)
        if v3:
            r4 = np.array([region_of(f, CUTS4) for f in fr])
            from extract_training_data import parse_rsd
            CH = ['Channel1','Channel2','Channel3','Channel4']
            raw = parse_rsd(os.path.join(ROOT, 'MB1000_M13_DT', well + '.rsd'))[CH].values.astype(np.float64)
            Xr = np.array([window(raw, int(s)) for s in pp])
            p4 = np.zeros((len(pp), 5))
            for r in range(4):
                sel = r4 == r
                if sel.sum(): p4[sel] = v3[r].predict(zscore(Xr[sel]), batch_size=256, verbose=0)
            b4 = blast_eval(''.join(LABELS[i] for i in p4[:, :4].argmax(1)))
            m4.append(b4['matched'] if b4 else 0)
    print(f'wells={len(wells)}  DLL-pos+CNN(v6_cal8) matched={np.mean(m6):.1f}  DLL matched={np.mean(m_dll):.1f}')
    if v3:
        print(f'DLL-pos + v3(raw-cnn) matched={np.mean(m4):.1f}')
    print(' per-well:', ' '.join(f'{w}:{a}->{b}' for w, a, b in
                                 zip(wells, m_dll, m6)))

if __name__ == '__main__':
    main()
