#!/usr/bin/env python3
"""train_dense.py - per-scan 5-class CNN on the dense split-aware set.

Trains against dense_training.npz (built by build_dense_training.py): a
per-scan window classifier that outputs no-base / A / C / G / T at ANY scan,
including the interior of a shoulder (<5 scans apart).  The negative classes
include valley windows between close labels (teaches DO-NOT-MERGE), the exact
scans ESD falsely called (teaches where the DLL is wrong), and background
noise.  The positives include every ESD-missed split base, so the caller can
stop collapsing close peaks.

Validation is by HELD-OUT WELL (every 8th well, same protocol as the
existing v4/v5 trainers) - never same-well leakage from the shared trace.

The report also evaluates the two behaviors this caller is built for:
  * split recall  - base-class accuracy on windows whose centre is one of the
                    3695 ESD-missed shoulder bases (src='s')
  * valley spec   - no-base accuracy on the valley windows between close
                    labels (src='v'), i.e. how well it refuses to merge

Usage:
  python3 train_dense.py [--epochs 30] [--out dense_caller.keras]
"""
import argparse
import os
import sys

import numpy as np

__version__ = '1.0'
HERE = os.path.dirname(os.path.realpath(__file__))
ROOT = HERE
sys.path.insert(0, HERE)
os.environ.setdefault('TF_CPP_MIN_LOG_LEVEL', '3')

WINDOW = 15


def zscore(X):
    mu = X.mean(axis=1, keepdims=True)
    sd = X.std(axis=1, keepdims=True) + 1e-8
    return ((X - mu) / sd).astype(np.float32)


def jitter_batch(X, rng, jitter=2):
    Xj = np.empty_like(X)
    for k in range(len(X)):
        d = int(rng.integers(-jitter, jitter + 1))
        Xj[k] = np.roll(X[k], d, axis=0)
        if d > 0:
            Xj[k][:d] = X[k][0]
        elif d < 0:
            Xj[k][d:] = X[k][-1]
    return Xj


def build_model():
    import tensorflow as tf
    model = tf.keras.Sequential([
        tf.keras.layers.Input(shape=(2 * WINDOW + 1, 4)),
        tf.keras.layers.Conv1D(64, 7, padding='same', name='conv1'),
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
        tf.keras.layers.Dense(5, activation='softmax', name='base'),
    ])
    model.compile(optimizer=tf.keras.optimizers.Adam(3e-4),
                  loss='sparse_categorical_crossentropy', metrics=['accuracy'])
    return model


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--epochs', type=int, default=30)
    ap.add_argument('--data', default=os.path.join(ROOT, 'dense_training.npz'))
    ap.add_argument('--out', default=os.path.join(HERE, 'dense_caller.keras'))
    args = ap.parse_args()

    d = np.load(args.data, allow_pickle=True)
    X, y = d['X'], d['y'].astype(int)
    wells = d['well']
    src = d['src']
    all_wells = sorted(set(w.decode() for w in wells))
    test_wells = set(all_wells[::8])
    te = np.array([w.decode() in test_wells for w in wells])
    tr = ~te
    print(f'rows: {len(y)}  well-split: train {tr.sum()}  test {te.sum()} '
          f'({len(test_wells)} held-out wells: {sorted(test_wells)[:4]}...)')
    by = np.bincount(y, minlength=5)
    print('classes N/A/C/G/T:',
          dict((['N', 'A', 'C', 'G', 'T'][i], int(c))
               for i, c in enumerate(by)))

    rng = np.random.default_rng(42)
    classes = np.bincount(y[tr], minlength=5)
    cw = {i: len(y[tr]) / (5 * c) for i, c in enumerate(classes) if c > 0}
    print('class weights:', {['N', 'A', 'C', 'G', 'T'][k]: round(v, 2)
                             for k, v in cw.items()})

    Xtr, ytr = zscore(X[tr]), y[tr]
    Xte, yte = zscore(X[te]), y[te]
    src_te = src[te]
    idx = rng.permutation(len(ytr))
    Xtr, ytr, _ = Xtr[idx], ytr[idx], None

    model = build_model()
    best_acc, best_ep = 0.0, -1
    for ep in range(args.epochs):
        r = rng.permutation(len(ytr))
        model.fit(zscore(jitter_batch(Xtr[r], rng)), ytr[r],
                  batch_size=64, class_weight=cw, verbose=0)
        _, acc = model.evaluate(Xte, yte, verbose=0)
        print(f'epoch {ep + 1}: val_acc={acc:.4f}', flush=True)
        if acc > best_acc:
            best_acc, best_ep = acc, ep
            model.save(args.out)
        if ep == 1 and best_acc < 0.60:
            print('aborting: not converging')
            break
    print(f'BEST val_acc={best_acc:.4f} @epoch {best_ep + 1}')
    print(f'saved: {args.out}')

    # ---- targeted eval on the two behaviours this caller is built for ----
    import tensorflow as tf
    mdl = tf.keras.models.load_model(args.out, compile=False)
    pred = mdl.predict(Xte, verbose=0).argmax(1)

    def report(name, mask):
        if int(mask.sum()) == 0:
            print(f'{name}: no samples')
            return
        a = (yte[mask] == pred[mask]).mean()
        print(f'{name}: n={int(mask.sum())} acc={a:.4f}')
        ysel = yte[mask]
        if a < 1:
            print('   confusion:', np.bincount(
                pred[mask] * 5 + ysel, minlength=25).reshape(5, 5).tolist())

    report('ALL test', np.ones(len(yte), dtype=bool))
    for c, name in enumerate(['N', 'A', 'C', 'G', 'T']):
        report(f'class {name}', yte == c)
    report('ESD-missed SPLITS (src=s)', src_te == b's')
    report('VALLEY negatives (src=v)', src_te == b'v')
    report('ESD-OVERCALL negatives (src=o)', src_te == b'o')
    report('BACKGROUND negatives (src=b)', src_te == b'b')


if __name__ == '__main__':
    main()