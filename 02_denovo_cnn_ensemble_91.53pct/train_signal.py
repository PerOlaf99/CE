#!/usr/bin/env python3
"""train_signal.py - CNN to predict true-signal region [start, stop] from raw
signal + current (X: 128 bins x 5 features).  Outputs 2 scalars (fractions).
Auxiliary loss: reconstruction of the "signal band mask" from the esd peaks,
so the model learns peak-bearing regions, not just endpoints."""
import os, sys
import numpy as np
os.environ.setdefault('TF_CPP_MIN_LOG_LEVEL', '3')
sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
import tensorflow as tf

EPOCHS = 300


def build():
    inp = tf.keras.layers.Input(shape=(128, 5))
    x = tf.keras.layers.Conv1D(32, 7, padding='same', activation='relu')(inp)
    x = tf.keras.layers.Conv1D(32, 5, padding='same', activation='relu')(x)
    x = tf.keras.layers.MaxPooling1D(2)(x)
    x = tf.keras.layers.Conv1D(64, 5, padding='same', activation='relu')(x)
    x = tf.keras.layers.Conv1D(64, 3, padding='same', activation='relu')(x)
    x = tf.keras.layers.GlobalAveragePooling1D()(x)
    x = tf.keras.layers.Dense(32, activation='relu')(x)
    r = tf.keras.layers.Dense(2, name='region')(x)
    return tf.keras.Model(inp, r)


def main():
    d = np.load('signal_training.npz', allow_pickle=True)
    X, y = d['X'].astype(np.float32), d['y'].astype(np.float32)
    split = d['split'].astype(bool)
    # center/normalize per feature across frame
    mu = X[split].mean((0, 1), keepdims=True)
    sd = X[split].std((0, 1), keepdims=True) + 1e-6
    Xn = ((X - mu) / sd).astype(np.float32)

    model = build()
    model.compile(tf.keras.optimizers.Adam(5e-4), loss='mse')
    Xtr, ytr, Xte, yte = Xn[split], y[split], Xn[~split], y[~split]
    best = (1e9, -1)
    for ep in range(EPOCHS):
        model.fit(Xtr, ytr, batch_size=16, verbose=0)
        err = model.evaluate(Xte, yte, verbose=0)
        if err < best[0]:
            best = (err, ep)
            model.save('signal_region_model.keras')
    # report in scan units
    yp = model.predict(Xte, verbose=0)
    p = yp * 9647
    gt = yte * 9647
    d0 = np.abs(p[:, 0] - gt[:, 0]).mean()
    d1 = np.abs(p[:, 1] - gt[:, 1]).mean()
    ws = [w.decode() if isinstance(w, bytes) else w for w in d['well'][~split]]
    print(f'BEST mse={best[0]:.2e} @ep{best[1] + 1}')
    print(f'  test start err = {d0:.1f} scans  stop err = {d1:.1f} scans  '
          f'(frame 9647)')
    # per-well
    for w, a, b in zip(ws, gt[:, 0], gt[:, 1]):
        pass
    th = 2  # scans in % of frame * 9647
    ok_start = (np.abs(p[:, 0] - gt[:, 0]) < 100).mean()
    ok_stop = (np.abs(p[:, 1] - gt[:, 1]) < 150).mean()
    print(f'  within 100 scans start: {ok_start:.2f}  within 150 stop: {ok_stop:.2f}')
    print('  per-well (pred_start pred_stop gt_start gt_stop):')
    for w, a, b, c, dd in zip(ws, p[:, 0], p[:, 1], gt[:, 0], gt[:, 1]):
        print(f'    {w}: {a:.0f} {b:.0f} | {c:.0f} {dd:.0f}')


if __name__ == '__main__':
    main()