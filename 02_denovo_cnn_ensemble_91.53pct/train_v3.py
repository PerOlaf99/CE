#!/usr/bin/env python3
"""train_v3.py - per-region peak CNNs on M13-labeled, mutation-aware data.

* data: v3_training.npz (from extract_v3.py) - train/test WELL split 48/48
* 4 region models (begin/mid/tail/tail-tail), same CNN as train_v2
* + background class (index 4) sampled per train well, tagged by region
* val = held-out 48 wells, per region; checkpoint best val acc
Output: base_caller_model_v3_<begin|mid|tail|tailtail>.keras
"""
import os, sys, glob
import numpy as np

HERE = os.path.dirname(os.path.realpath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, ROOT)
os.environ.setdefault('TF_CPP_MIN_LOG_LEVEL', '3')

try:
    import cimarrontv as cim
except ImportError:
    import cimarrontv_shim as cim
from extract_training_data import parse_rsd

WINDOW = 15
JITTER = 3
NEG_FRAC = 0.12
EPOCHS = 16
REGIONS = ['begin', 'mid', 'tail', 'tailtail']
CH_NAMES = ['Channel1', 'Channel2', 'Channel3', 'Channel4']


def make_window(ch, s, w=WINDOW):
    n = len(ch)
    lo, hi = s - w, s + w + 1
    win = ch[max(0, lo):min(n, hi)]
    if lo < 0 or hi > n:
        win = np.pad(win, ((max(0, -lo), max(0, hi - n)), (0, 0)), mode='edge')
    return win.astype(np.float32)


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


def region_of(frac, cuts=(0.15, 0.65, 0.90)):
    if frac < cuts[0]:
        return 0
    if frac < cuts[1]:
        return 1
    if frac < cuts[2]:
        return 2
    return 3


def gen_negatives(d, rng, per_well_cap=60):
    """Background windows (label 4) for TRAIN wells only, tagged by region."""
    meta = d['meta'].item()
    nX, ny, nr = [], [], []
    uniq_tr = sorted({w for w, s in zip(d['well'], d['split']) if s})
    scan_tr = d['scan'][d['split'].astype(bool)]
    scan_lo, scan_hi = scan_tr.min(), scan_tr.max()
    for w in uniq_tr:
        rsd = os.path.join(ROOT, 'MB1000_M13_DT', w + '.rsd')
        if not os.path.isfile(rsd):
            continue
        ch = parse_rsd(rsd)[CH_NAMES].values.astype(np.float64)
        if ch.shape[0] < 400:
            continue
        pk = np.sort(d['scan'][(d['well'] == w)])
        med = np.median(np.diff(pk)) if len(pk) > 3 else 10.0
        mids = [int((a + b) // 2) for a, b in zip(pk[:-1], pk[1:])
                if b - a >= 1.3 * med]
        far = [int(s) for s in rng.integers(300, len(ch) - 300,
                                            size=per_well_cap)
               if np.min(np.abs(pk - s)) > 2 * WINDOW]
        picks = (mids + list(far))[:per_well_cap]
        if not picks:
            continue
        wlo, whi = int(pk[0]), int(pk[-1])
        for s in picks:
            nX.append(make_window(ch, s))
            nny = 4
            ny.append(nny)
            fr = (s - wlo) / max(1, whi - wlo)
            nr.append(region_of(fr))
    return nX, np.array(ny, dtype=int), np.array(nr, dtype=np.uint8)


def main():
    d = np.load(os.path.join(HERE, 'v3_training.npz'), allow_pickle=True)
    X, y = d['X'], d['y'].astype(int)
    reg = d['region'].astype(int)
    split = d['split'].astype(bool)
    wells = d['well']
    print(f'loaded {len(y)} windows; '
          f'train wells {len(set(wells[split]))} test {len(set(wells[~split]))}')

    rng = np.random.default_rng(0)
    negX, negy, negr = gen_negatives(d, rng)
    print(f'bg windows {len(negy)}: {np.bincount(negr, minlength=4)}')

    import tensorflow as tf
    results = {}
    for r in range(4):
        trm = (reg == r) & split
        va = (reg == r) & ~split
        nbg = int(NEG_FRAC * trm.sum())
        bgm = (np.asarray(negr) == r) if len(negr) else np.zeros(0, bool)
        if bgm.sum() == 0:
            print(f'region {REGIONS[r]}: no bg - copying mid'); bgm[:] = True
        sel = np.where(bgm)[0]
        sel = sel[:nbg]
        nX = np.concatenate([X[trm], np.array(negX, dtype=np.float32)[sel]])
        ny = np.concatenate([y[trm], negy[sel]])
        Xte, yte = X[va], y[va]
        print(f'REGION {REGIONS[r]} train={len(ny)} (bg {len(sel)}) '
              f'val={len(yte)}')
        if len(yte) < 100 or len(ny) < 300:
            print(f'  skip'); results[r] = 0.0; continue
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
        classes = np.bincount(ny, minlength=5)
        cw = {i: len(ny) / (5 * c) for i, c in enumerate(classes) if c > 0}
        Xte_n = zscore(Xte)
        Xtr = Xtr0 = np.concatenate([X[trm], np.array(negX)[sel]])
        ytr = np.concatenate([y[trm], negy[sel]])
        best = (0.0, -1)
        for ep in range(EPOCHS):
            p = rng.permutation(len(ytr))
            Xb = zscore(jitter_batch(Xtr[p], rng))
            model.fit(Xb, ytr[p], batch_size=64, class_weight=cw, verbose=0)
            _, acc = model.evaluate(Xte_n, yte, verbose=0)
            if acc > best[0]:
                best = (acc, ep)
                model.save(os.path.join(HERE, f'base_caller_model_v3_{REGIONS[r]}.keras'))
        print(f'  {REGIONS[r]} BEST val_acc={best[0]:.4f} @ep{best[1] + 1}')
        results[r] = best[0]
    print('DONE', ' '.join(f'{REGIONS[k]}={v:.4f}' for k, v in results.items()))


if __name__ == '__main__':
    main()