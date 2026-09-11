#!/usr/bin/env python3
"""train_v7_feat.py - per-region CNNs on calibrated lanes + BandStat side-tower.

Same 8-region protocol as train_region but with a feature side-input: the
per-band DSP statistics (xbnd, env/floor, flank-env/floor, width, spacing
ratio, floor) concatenated after the conv GAP so the classifier can use Cimarron-
style per-band evidence in addition to the calibrated window.
Output: base_caller_model_v7_feat_r{k}.keras
"""
import os, sys, argparse
import numpy as np
os.environ.setdefault('TF_CPP_MIN_LOG_LEVEL', '3')
HERE = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0, HERE)
import tensorflow as tf

WINDOW = 15
JITTER = 3
NEG_FRAC = 0.12
EPOCHS = 24
CUTS = [0.05, 0.15, 0.35, 0.50, 0.65, 0.80, 0.90]


def zscore(X):
    mu = X.mean(axis=1, keepdims=True)
    sd = X.std(axis=1, keepdims=True) + 1e-8
    return ((X - mu) / sd).astype(np.float32)


def feat_norm(F):
    # per-feature soft-normalization: robust scale to ~[0,1] before Dense
    scale = np.array([1.6, 40.0, 30.0, 12.0, 6.0, 0.1], np.float32)
    return (np.clip(F / scale, 0, 4)).astype(np.float32)


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


def build(nf):
    img = tf.keras.layers.Input(shape=(2 * WINDOW + 1, 4))
    x = tf.keras.layers.Conv1D(64, 7, padding='same')(img)
    x = tf.keras.layers.BatchNormalization()(x); x = tf.keras.layers.ReLU()(x)
    x = tf.keras.layers.MaxPooling1D(2)(x)
    x = tf.keras.layers.Conv1D(128, 5, padding='same')(x)
    x = tf.keras.layers.BatchNormalization()(x); x = tf.keras.layers.ReLU()(x)
    x = tf.keras.layers.MaxPooling1D(2)(x)
    x = tf.keras.layers.Conv1D(256, 3, padding='same')(x)
    x = tf.keras.layers.BatchNormalization()(x); x = tf.keras.layers.ReLU()(x)
    x = tf.keras.layers.Conv1D(256, 3, padding='same')(x)
    x = tf.keras.layers.BatchNormalization()(x); x = tf.keras.layers.ReLU()(x)
    g = tf.keras.layers.GlobalAveragePooling1D()(x)
    gd = tf.keras.layers.Dense(96, activation='relu')(g)

    fi = tf.keras.layers.Input(shape=(nf,))
    fd = tf.keras.layers.Dense(32, activation='relu')(fi)
    h = tf.keras.layers.Concatenate()([gd, fd])
    h = tf.keras.layers.Dense(96, activation='relu')(h)
    h = tf.keras.layers.Dropout(0.4)(h)
    h = tf.keras.layers.Dense(48, activation='relu')(h)
    h = tf.keras.layers.Dropout(0.3)(h)
    out = tf.keras.layers.Dense(5, activation='softmax')(h)
    return tf.keras.Model(inputs=[img, fi], outputs=out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--npz', default='cal_feat.npz')
    ap.add_argument('--prefix', default='base_caller_model_v7_feat')
    args = ap.parse_args()
    d = np.load(args.npz, allow_pickle=True)
    X, y = d['X'].astype(np.float32), d['y'].astype(int)
    F = d['feat'].astype(np.float32)
    region = d['region'].astype(int)
    split = d['split'].astype(bool)
    wells = np.array([w.decode() if isinstance(w, bytes) else w for w in d['well']])
    negX = np.asarray(d['negX'], np.float32)
    negy = np.asarray(d['negy'], np.int64)
    negr = np.asarray(d['negr'], 'int')
    negF = np.asarray(d['negfeat'], np.float32)
    nreg = len(CUTS) + 1
    print(f'loaded {len(y)} windows feat={F.shape[-1]} '
          f'tr_w={len(set(wells[split]))} te_w={len(set(wells[~split]))}')
    rng = np.random.default_rng(0)
    for r in range(nreg):
        trm = (region == r) & split
        va = (region == r) & ~split
        if va.sum() < 40 or trm.sum() < 150:
            print(f'region{r}: skip'); continue
        nbg = int(NEG_FRAC * trm.sum())
        sel = np.where(negr == r)[0][:nbg]
        Xtr = np.concatenate([X[trm], negX[sel]])
        Ftr = np.concatenate([F[trm], negF[sel]])
        ytr = np.concatenate([y[trm], negy[sel]])
        Xte, Fte, yte = X[va], F[va], y[va]
        model = build(F.shape[-1])
        model.compile(tf.keras.optimizers.Adam(3e-4),
                      loss='sparse_categorical_crossentropy', metrics=['accuracy'])
        classes = np.bincount(ytr, minlength=5)
        cw = {i: len(ytr) / (5 * c) for i, c in enumerate(classes) if c > 0}
        Xte_n = zscore(Xte)
        Fte_n = feat_norm(Fte)
        best = (0.0, -1)
        for ep in range(EPOCHS):
            p = rng.permutation(len(ytr))
            Xb = zscore(jitter_batch(Xtr[p], rng))
            model.fit([Xb, feat_norm(Ftr[p])], ytr[p], batch_size=64,
                      class_weight=cw, verbose=0)
            _, acc = model.evaluate([Xte_n, Fte_n], yte, verbose=0)
            if acc > best[0]:
                best = (acc, ep)
                model.save(f'{args.prefix}_r{r}.keras')
        print(f'  region{r} BEST val={best[0]:.4f} @ep{best[1] + 1}')
    print('DONE')


if __name__ == '__main__':
    main()