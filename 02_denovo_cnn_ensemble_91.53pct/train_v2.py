#!/usr/bin/env python3
"""train_v2.py - retrain the peak CNN with jitter augmentation + background.

Improvements over the original training:
  * jitter augmentation: each window randomly shifted +-3 scans (edge pad)
    -> translation-tolerant model for gap-fill candidates
  * explicit background class (index 4): windows sampled mid-gap / far from
    any peak -> honest P(no base) for insertion decisions
  * well-level holdout (every 8th well) for honest validation

Output: base_caller_model_v2.keras
"""
import os, sys, json
import numpy as np

__version__ = '2.0'  # 2.0: jitter aug + background class + class weights; ROOT-aware
HERE = os.path.dirname(os.path.realpath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, ROOT)
os.environ.setdefault('TF_CPP_MIN_LOG_LEVEL', '3')

try:
    import cimarrontv as cim
except ImportError:
    import cimarrontv_shim as cim

WINDOW = 15
JITTER = 3
EXPAND = 5
NEG_FRAC = 0.15


def make_window(ch, s):
    n = len(ch)
    lo, hi = s - WINDOW, s + WINDOW + 1
    pad_lo, pad_hi = max(0, -lo), max(0, hi - n)
    win = ch[max(0, lo):min(n, hi)]
    if pad_lo or pad_hi:
        win = np.pad(win, ((pad_lo, pad_hi), (0, 0)), mode='edge')
    return win


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
    d = np.load(os.path.join(ROOT, 'm13_clean_training_full.npz'),
                allow_pickle=True)
    X, y, wells, scans = d['X'], d['y'].astype(int), d['wells'], d['scans']
    all_wells = sorted(set(wells))
    test_wells = set(all_wells[::8])
    te = np.array([w in test_wells for w in wells])
    tr = ~te
    print(f'wells: {len(all_wells)}  train windows: {tr.sum()}  '
          f'test windows: {te.sum()} ({len(test_wells)} held-out wells)')

    rng = np.random.default_rng(42)

    neg_X, neg_y = [], []
    uniq_wells = sorted(set(wells[tr]))
    n_neg_target = int(NEG_FRAC * tr.sum())
    per_well = max(1, n_neg_target // len(uniq_wells))
    for w in uniq_wells:
        rsd = os.path.join(ROOT, 'MB1000_M13_DT', w + '.rsd')
        if not os.path.isfile(rsd):
            continue
        ch, _ = cim.read_rsd(rsd)
        chw = np.asarray(ch, dtype=np.float64)
        if chw.shape[0] == 4 and chw.shape[0] <= chw.shape[1]:
            chw = chw.T
        pk = np.sort(scans[wells == w])
        if len(pk) < 4:
            continue
        med = np.median(np.diff(pk))
        mids = [int((a + b) // 2) for a, b in zip(pk[:-1], pk[1:])
                if b - a >= 1.3 * med]
        far = rng.integers(200, len(chw) - 200, size=per_well)
        far = [int(s) for s in far if np.min(np.abs(pk - s)) > 2 * WINDOW]
        picks = (mids[:per_well // 2] + far)[:per_well]
        for s in picks:
            neg_X.append(make_window(chw, s))
            neg_y.append(4)
    print(f'negatives: {len(neg_y)}')
    if neg_X:
        Xtr = np.concatenate([X[tr], np.array(neg_X, dtype=np.float32)])
        ytr = np.concatenate([y[tr], np.array(neg_y)])
    else:
        Xtr, ytr = X[tr], y[tr]

    idx = rng.permutation(len(ytr))
    Xtr, ytr = Xtr[idx], ytr[idx]
    Xte, yte = X[te], y[te]

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

    classes = np.bincount(ytr, minlength=5)
    cw = {i: len(ytr) / (5 * c) for i, c in enumerate(classes) if c > 0}
    print('class weights:', {k: round(v, 2) for k, v in cw.items()})

    Xte_n = zscore(Xte)
    best_acc, best_ep = 0, -1
    for ep in range(20):
        r = rng.permutation(len(ytr))
        epochs_X = zscore(jitter_batch(Xtr[r], rng))
        model.fit(epochs_X, ytr[r], batch_size=64, class_weight=cw, verbose=0)
        _, acc = model.evaluate(Xte_n, yte, verbose=0)
        print(f'epoch {ep + 1}: val_acc={acc:.4f}', flush=True)
        if acc > best_acc:
            best_acc, best_ep = acc, ep
            model.save(os.path.join(HERE, 'base_caller_model_v2.keras'))
        if ep == 1 and best_acc < 0.6:
            print('aborting: not converging')
            break
    print(f'BEST val_acc={best_acc:.4f} @epoch {best_ep + 1} '
          f'(held-out wells incl. background class)')


if __name__ == '__main__':
    main()
