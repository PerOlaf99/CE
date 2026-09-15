#!/usr/bin/env python3
"""train_region_split.py - train one CNN per region for ARBITRARY splits.

Same recipe as train_v3.py (5-layer CNN, win +-15, jitter-3, bg class 4,
checkpoint best held-out val acc) but the region assignment uses the rank
fraction cuts of the requested split, so we can sweep region COUNT.

Splits are read from region_common.SPLITS.  Models saved as
region_split<N>_r<r>.keras (N>=3).  The v3 4-region models remain untouched
(SPLIT_TAGS['4'] == 'v3' keeps the eval default on the original set).

Usage:  python3 train_region_split.py [--splits 3,5,6] [--epochs 14]
"""
import os, sys, argparse
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

import region_common as rc
from region_common import region_of, model_path

CH_NAMES = ['Channel1', 'Channel2', 'Channel3', 'Channel4']
JITTER = 3
NEG_FRAC = 0.12
WINDOW = 15


def make_window(ch, s, w=WINDOW):
    n = len(ch)
    lo, hi = s - w, s + w + 1
    win = ch[max(0, lo):min(n, hi)]
    if lo < 0 or hi > n:
        win = np.pad(win, ((max(0, -lo), max(0, hi - n)), (0, 0)),
                     mode='edge')
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


def gen_negatives(d, cuts, rng, per_well_cap=60, cal=False):
    """Background windows (label 4) for TRAIN wells, region-tagged by cuts."""
    n_regions = len(cuts) + 1
    nX, ny, nr = [], [], []
    uniq_tr = sorted({w for w, s in zip(d['well'], d['split']) if s})
    for w in uniq_tr:
        if cal:
            p = os.path.join(ROOT, 'cache_sep', w + '.npy')
            if not os.path.isfile(p):
                continue
            ch = np.load(p).astype(np.float64)
        else:
            p = os.path.join(ROOT, 'MB1000_M13_DT', w + '.rsd')
            if not os.path.isfile(p):
                continue
            ch = parse_rsd(p)[CH_NAMES].values.astype(np.float64)
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
            ny.append(4)
            fr = (s - wlo) / max(1, whi - wlo)
            nr.append(region_of(fr, cuts))
    return nX, np.array(ny, dtype=int), np.array(nr, dtype=np.uint8)


def build_cnn():
    import tensorflow as tf
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
    return model


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--splits', default='4,3,5,6,8',
                    help='comma list of region counts to train')
    ap.add_argument('--epochs', type=int, default=14)
    ap.add_argument('--data', default=os.path.join(HERE, 'v3_training.npz'),
                    help='training npz (cal_training.npz for calibrated lanes)')
    ap.add_argument('--tag', default='s',
                    help="model name tag ('s' raw, 'cal' calibrated lanes)")
    args = ap.parse_args()

    d = np.load(args.data, allow_pickle=True)
    cal = args.data != os.path.join(HERE, 'v3_training.npz')
    X, y = d['X'], d['y'].astype(int)
    split = d['split'].astype(bool)
    wells = d['well']
    well_names = sorted(set(wells))
    order = {w: np.where(wells == w)[0] for w in well_names}

    # reconstruct per-sample rank fraction (matches extract_v3: usable cols in
    # order, masked to >= usable_start)
    rank = np.zeros(len(y), dtype=np.float64)
    for w in well_names:
        idx = order[w]
        rank[idx] = np.arange(len(idx), dtype=float) / max(1, len(idx) - 1)
    print(f'loaded {len(y)} windows; rank fractions reconstructed per well')

    import tensorflow as tf
    tf.keras.utils.set_random_seed(7)
    want = [int(x) for x in args.splits.split(',') if int(x) in rc.SPLITS]
    summary = {}
    for n in want:
        cuts = rc.SPLITS[n]['cuts']
        print(f'\n===== SPLIT {n} regions, cuts {cuts} '
              f'(data={"cal" if cal else "raw"}, tag={args.tag}) =====')
        reg = np.array([region_of(f, cuts) for f in rank], dtype=np.uint8)
        rng = np.random.default_rng(0)
        negX, negy, negr = gen_negatives(d, cuts, rng, cal=cal)
        print(f'bg windows {len(negy)}: {dict(zip(*np.unique(negr, return_counts=True)))}')
        bests = {}
        for r in range(n):
            trm = (reg == r) & split
            va = (reg == r) & ~split
            nbg = int(NEG_FRAC * trm.sum())
            bgm = (np.asarray(negr) == r) if len(negr) else np.zeros(0, bool)
            if bgm.sum() == 0:
                print(f'  region {r}: no bg - copying mid'); bgm[:] = True
            sel = np.where(bgm)[0][:nbg]
            nX = np.concatenate([X[trm], np.array(negX, dtype=np.float32)[sel]])
            ny = np.concatenate([y[trm], negy[sel]])
            yte = y[va]
            print(f'  r{r}: train={len(ny)} (bg {len(sel)}) val={len(yte)}')
            if len(yte) < 80 or len(ny) < 300:
                print('    skip (too few)'); bests[r] = 0.0; continue
            model = build_cnn()
            classes = np.bincount(ny, minlength=5)
            cw = {i: len(ny) / (5 * c) for i, c in enumerate(classes) if c > 0}
            Xte_n = zscore(X[va])
            Xtr0 = nX
            best = (0.0, -1)
            for ep in range(args.epochs):
                p = rng.permutation(len(ny))
                Xb = zscore(jitter_batch(Xtr0[p], rng))
                model.fit(Xb, ny[p], batch_size=64, class_weight=cw, verbose=0)
                _, acc = model.evaluate(Xte_n, yte, verbose=0)
                if acc > best[0]:
                    best = (acc, ep)
                    model.save(model_path(n, r, args.tag))
            print(f'    r{r} BEST val_acc={best[0]:.4f} @ep{best[1] + 1}')
            bests[r] = best[0]
        summary[n] = bests
        print('  -> ' + '  '.join(f'{n}:r{r}={bests[r]:.4f}' for r in bests))
    print('\n== SPLIT SUMMARY (per-region val acc) ==')
    for n, b in summary.items():
        v = [b[r] for r in sorted(b)]
        print(f'  n={n}: ' + ' '.join(f'{x:.4f}' for x in v) +
              f'  mean={np.mean(v):.4f} min={np.min(v):.4f}')


if __name__ == '__main__':
    main()