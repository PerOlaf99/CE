#!/usr/bin/env python3
"""train_corr.py - second-stage per-column corrector (v8).

Per-region MLP: input = v6 CNN class probs (4) + bandstat features (6).
Learns to correct the CNN's confident-but-wrong columns using per-band DSP
evidence the local window cannot see (width, D_Y spacing ratio).
Output: base_caller_model_v8_corr_r{k}.keras (4-class, softmax).
"""
import os, sys, argparse
import numpy as np
os.environ.setdefault('TF_CPP_MIN_LOG_LEVEL', '3')
sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
import tensorflow as tf

EPOCHS = 30
CUTS = [0.05, 0.15, 0.35, 0.50, 0.65, 0.80, 0.90]


def build_mlp():
    inp = tf.keras.layers.Input(shape=(10,))
    x = tf.keras.layers.Dense(64, activation='relu')(inp)
    x = tf.keras.layers.Dropout(0.3)(x)
    x = tf.keras.layers.Dense(64, activation='relu')(x)
    x = tf.keras.layers.Dropout(0.2)(x)
    out = tf.keras.layers.Dense(4, activation='softmax', name='call')(x)
    return tf.keras.Model(inp, out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--npz', default='corr_training.npz')
    ap.add_argument('--prefix', default='base_caller_model_v8_corr')
    args = ap.parse_args()
    d = np.load(args.npz, allow_pickle=True)
    X, y = d['X'].astype(np.float32), d['y'].astype(int)
    region = d['region'].astype(int)
    split = d['split'].astype(bool)
    nreg = len(CUTS) + 1
    # feature normalization statistics from TRAIN only
    tr = X[split]
    mu, sd = tr.mean(0), tr.std(0) + 1e-8
    Xn = ((X - mu) / sd).astype(np.float32)
    print(f'X={X.shape} train_samp={split.sum()} test_samp={(~split).sum()}')
    base_acc = []
    for r in range(nreg):
        trm = (region == r) & split
        va = (region == r) & ~split
        if va.sum() < 40 or trm.sum() < 150:
            print(f'region{r}: skip'); continue
        model = build_mlp()
        model.compile(tf.keras.optimizers.Adam(2e-3),
                      loss='sparse_categorical_crossentropy', metrics=['accuracy'])
        cls = np.bincount(y[trm], minlength=4)
        cw = {i: len(y[trm]) / (4 * c) for i, c in enumerate(cls) if c > 0}
        best = (0.0, -1)
        for ep in range(EPOCHS):
            model.fit(Xn[trm], y[trm], batch_size=256, class_weight=cw, verbose=0)
            _, acc = model.evaluate(Xn[va], y[va], verbose=0)
            if acc > best[0]:
                best = (acc, ep)
                model.save(f'{args.prefix}_r{r}.keras')
        print(f'  region{r} BEST val={best[0]:.4f} @ep{best[1] + 1}')
        base_acc.append(best[0])
    print('DONE')


if __name__ == '__main__':
    main()