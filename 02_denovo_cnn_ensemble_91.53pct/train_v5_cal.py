#!/usr/bin/env python3
"""train_v5_cal.py - per-region CNNs on the DSP-CALIBRATED lanes.

Same architecture/regions/labels protocol as train_v3, but the input windows
are taken from the matrix-separated + mobility-shifted lanes (cache_sep)
centered on the DLL's OWN called peak positions, labels = esd bases.
Region models: begin/mid/tail/tail-tail.  Output: base_caller_model_v5_<r>.keras
"""
import os, sys
import numpy as np

HERE = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0, HERE)
os.environ.setdefault('TF_CPP_MIN_LOG_LEVEL', '3')

WINDOW = 15
JITTER = 3
NEG_FRAC = 0.12
EPOCHS = 16
REGIONS = ['begin', 'mid', 'tail', 'tailtail']
REGION_CUTS = (0.15, 0.65, 0.90)


def region_of(frac):
    if frac < REGION_CUTS[0]:
        return 0
    if frac < REGION_CUTS[1]:
        return 1
    if frac < REGION_CUTS[2]:
        return 2
    return 3


def zscore(X):
    mu = X.mean(axis=1, keepdims=True)
    sd = X.std(axis=1, keepdims=True) + 1e-8
    return ((X - mu) / sd).astype(np.float32)


def jitter_batch(X, rng):
    Xj = np.empty_like(X)
    for k in range(len(X)):
        d = int(rng.integers(-JITTER, JITTER + 1))
        Xj[k] = np.roll(X[k], d, axis=0)
        if d > 0:
            Xj[k][:d] = X[k][0]
        elif d < 0:
            Xj[k][d:] = X[k][-1]
    return Xj


def main():
    d = np.load(os.path.join(HERE, 'cal_training.npz'), allow_pickle=True)
    X, y = d['X'], d['y'].astype(int)
    reg = d['region'].astype(int)
    split = d['split'].astype(bool)
    wells = np.array([w.decode() if isinstance(w, bytes) else w for w in d['well']])
    print(f'loaded {len(y)} calibrated windows; '
          f'train wells {len(set(wells[split]))} test {len(set(wells[~split]))}')

    negX = np.asarray(d['negX'], np.float32)
    negy = np.asarray(d['negy'], np.int64)
    negr = np.asarray(d['negr'], np.uint8)

    rng = np.random.default_rng(0)
    import tensorflow as tf
    results = {}
    for r in range(4):
        trm = (reg == r) & split
        va = (reg == r) & ~split
        nbg = int(NEG_FRAC * trm.sum())
        bgm = np.asarray(negr) == r
        sel = np.where(bgm)[0][:nbg]
        nXtr = np.concatenate([X[trm], negX[sel]])
        nytr = np.concatenate([y[trm], negy[sel]])
        Xte, yte = X[va], y[va]
        print(f'REGION {REGIONS[r]} train={len(nytr)} (bg {len(sel)}) val={len(yte)}')
        if len(yte) < 100 or len(nytr) < 300:
            print('  skip'); results[r] = 0.0; continue
        model = tf.keras.Sequential([
            tf.keras.layers.Input(shape=(2 * WINDOW + 1, 4)),
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
        cw = {i: len(nytr) / (5 * c) for i, c in enumerate(classes) if c > 0}
        Xte_n = zscore(Xte)
        best = (0.0, -1)
        for ep in range(EPOCHS):
            p = rng.permutation(len(nytr))
            Xb = zscore(jitter_batch(nXtr[p], rng))
            model.fit(Xb, nytr[p], batch_size=64, class_weight=cw, verbose=0)
            _, acc = model.evaluate(Xte_n, yte, verbose=0)
            if acc > best[0]:
                best = (acc, ep)
                model.save(os.path.join(HERE, f'base_caller_model_v5_{REGIONS[r]}.keras'))
        print(f'  {REGIONS[r]} BEST val_acc={best[0]:.4f} @ep{best[1] + 1}')
        results[r] = best[0]
    print('DONE', ' '.join(f'{REGIONS[k]}={v:.4f}' for k, v in results.items()))


if __name__ == '__main__':
    main()