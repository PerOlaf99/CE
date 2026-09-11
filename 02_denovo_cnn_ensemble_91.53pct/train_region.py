#!/usr/bin/env python3
"""train_region.py - parametrized per-region CNN training.

npz must have keys X (N,31,C), y, region, split, negX, negy, negr.
Regions defined by cut list on per-row rank fraction -> supply as --cuts.
Trains one model per region; saves base_caller_model_<prefix>_r<k>.keras
"""
import os, sys, argparse
import numpy as np
os.environ.setdefault('TF_CPP_MIN_LOG_LEVEL', '3')

WINDOW = 15
JITTER = 3
NEG_FRAC = 0.12
EPOCHS = 20


def zscore(X):
    mu = X.mean(axis=1, keepdims=True)
    sd = X.std(axis=1, keepdims=True) + 1e-8
    return ((X - mu) / sd).astype(np.float32)


def jitter_batch(X, rng, C):
    Xj = np.empty_like(X)
    for k in range(len(X)):
        d = int(rng.integers(-JITTER, JITTER + 1))
        # jitter only the trace channels, keep static channels aligned
        Xj[k] = np.roll(X[k], d, axis=0)
        if d > 0:
            Xj[k][:d] = X[k][0]
        elif d < 0:
            Xj[k][d:] = X[k][-1]
    return Xj


def run(X, y, region, split, negX, negy, negr, cuts, prefix):
    import tensorflow as tf
    nreg = len(cuts) + 1
    results = {}
    for r in range(nreg):
        trm = (region == r) & split
        va = (region == r) & ~split
        if va.sum() < 40 or trm.sum() < 150:
            print(f'region{r}: skip (tr {trm.sum()} va {va.sum()})'); results[r]=0.0; continue
        nbg = int(NEG_FRAC * trm.sum())
        sel = np.where(negr == r)[0][:nbg]
        nXtr = np.concatenate([X[trm], negX[sel]])
        nytr = np.concatenate([y[trm], negy[sel]])
        Xte, yte = X[va], y[va]
        print(f'region{r}: train={len(nytr)} (bg {len(sel)}) val={len(yte)}')
        C = X.shape[-1]
        model = tf.keras.Sequential([
            tf.keras.layers.Input(shape=(2*WINDOW+1, C)),
            tf.keras.layers.Conv1D(64, 7, padding='same'),
            tf.keras.layers.BatchNormalization(), tf.keras.layers.ReLU(),
            tf.keras.layers.MaxPooling1D(2),
            tf.keras.layers.Conv1D(128, 5, padding='same'),
            tf.keras.layers.BatchNormalization(), tf.keras.layers.ReLU(),
            tf.keras.layers.MaxPooling1D(2),
            tf.keras.layers.Conv1D(256, 3, padding='same'),
            tf.keras.layers.BatchNormalization(), tf.keras.layers.ReLU(),
            tf.keras.layers.Conv1D(256, 3, padding='same'),
            tf.keras.layers.BatchNormalization(), tf.keras.layers.ReLU(),
            tf.keras.layers.GlobalAveragePooling1D(),
            tf.keras.layers.Dense(128, activation='relu'),
            tf.keras.layers.Dropout(0.4),
            tf.keras.layers.Dense(64, activation='relu'),
            tf.keras.layers.Dropout(0.3),
            tf.keras.layers.Dense(5, activation='softmax'),
        ])
        model.compile(tf.keras.optimizers.Adam(3e-4),
                      loss='sparse_categorical_crossentropy', metrics=['accuracy'])
        classes = np.bincount(nytr, minlength=5)
        cw = {i: len(nytr)/(5*c) for i, c in enumerate(classes) if c > 0}
        Xte_n = zscore(Xte)
        rng = np.random.default_rng(0)
        best = (0.0, -1)
        for ep in range(EPOCHS):
            p = rng.permutation(len(nytr))
            Xb = zscore(jitter_batch(nXtr[p], rng, C))
            model.fit(Xb, nytr[p], batch_size=64, class_weight=cw, verbose=0)
            _, acc = model.evaluate(Xte_n, yte, verbose=0)
            if acc > best[0]:
                best = (acc, ep)
                model.save(f'{prefix}_r{r}.keras')
        print(f'  region{r} BEST val={best[0]:.4f} @ep{best[1]+1}')
        results[r] = best[0]
    print('DONE', ' '.join(f'r{k}={v:.4f}' for k, v in results.items()))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--npz', required=True)
    ap.add_argument('--cuts', default='0.05,0.15,0.35,0.50,0.65,0.80,0.90',
                    help='region cut fractions (descending ok)')
    ap.add_argument('--prefix', required=True)
    args = ap.parse_args()
    cuts = [float(x) for x in args.cuts.split(',')]
    d = np.load(args.npz, allow_pickle=True)
    X, y = d['X'].astype(np.float32), d['y'].astype(int)
    region = d['region'].astype(int)
    split = d['split'].astype(bool)
    wells = np.array([w.decode() if isinstance(w, bytes) else w
                      for w in d['well']])
    print(f'loaded {len(y)} windows C={X.shape[-1]} '
          f'tr_w={len(set(wells[split]))} te_w={len(set(wells[~split]))}')
    # retag region from scans-rank if npz has scan+well? region already set by builder.
    negX = np.asarray(d['negX'], np.float32)
    negy = np.asarray(d['negy'], np.int64)
    negr = np.asarray(d['negr'], 'int')
    print('neg_counts', np.bincount(negr, minlength=max(len(cuts)+1, 5)))
    run(X, y, region, split, negX, negy, negr, cuts, args.prefix)


if __name__ == '__main__':
    main()
