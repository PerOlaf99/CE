#!/usr/bin/env python3
"""warp_tail_experiment.py - does spacing-normalized (warped) windows help the
tail region model?  Controlled: train tail model twice from same RNG seed,
once on raw windows (npz), once on warped windows (band resampled to fixed
length between neighbor-peak midpoints).  Report paired val accuracy.

Dogma: tight tail spacing (6-7.5 scans/col) shrinks the band the CNN must
read; resampling each band onto a fixed grid removes the spacing variability
the tail model otherwise must learn.
"""
import os, sys
import numpy as np

HERE = os.path.dirname(os.path.realpath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, ROOT)
os.environ.setdefault('TF_CPP_MIN_LOG_LEVEL', '3')
import tensorflow as tf
import train_v3 as tv
from extract_training_data import parse_rsd

WARP_N = 25          # samples across the warped band


def warp_window(ch, s_prev, s_cur, s_next, n=WARP_N):
    """Resample channels between the two band boundaries around s_cur."""
    if s_prev is None:
        left = s_cur - 10.0
    else:
        left = (s_prev + s_cur) / 2.0
    if s_next is None:
        right = s_cur + 10.0
    else:
        right = (s_cur + s_next) / 2.0
    if right - left < 1.0:
        right = left + 1.0
    x = np.linspace(left, right, n)
    xq = np.clip(x, 0, ch.shape[0] - 1)
    xi = np.floor(xq).astype(int)
    frac = xq - xi
    xi1 = np.minimum(xi + 1, ch.shape[0] - 1)
    out = ch[xi] * (1 - frac)[:, None] + ch[xi1] * frac[:, None]
    return out.astype(np.float32)


def make_model():
    return tf.keras.Sequential([
        tf.keras.layers.Input(shape=(None, 4)),
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


def main():
    d = np.load(os.path.join(HERE, 'v3_training.npz'), allow_pickle=True)
    scan = d['scan'].astype(int)
    well = d['well']
    split = d['split'].astype(bool)
    reg = d['region'].astype(int)
    y = d['y'].astype(int)

    # neighbor scans per window (windows grouped per well in read order)
    prev_s = np.full(len(well), -1)
    next_s = np.full(len(well), -1)
    start = 0
    while start < len(well):
        w = well[start]
        end = start
        while end < len(well) and well[end] == w:
            end += 1
        sc = scan[start:end]
        for k in range(start, end):
            j = k - start
            prev_s[k] = sc[j - 1] if j > 0 else -1
            next_s[k] = sc[j + 1] if j < end - start - 1 else -1
        start = end

    sel = reg >= 2
    idx = np.flatnonzero(sel)
    print(f'windows in tail/tailtail: {int(sel.sum())} '
          f'(train {int((sel & split).sum())} val {int((sel & ~split).sum())})')

    Xw = np.zeros((int(sel.sum()), WARP_N, 4), dtype=np.float32)
    cache = {}
    for k, gi in enumerate(idx):
        w = well[gi]
        if w not in cache:
            cache[w] = parse_rsd(os.path.join(ROOT, 'MB1000_M13_DT', w + '.rsd'))
        ch = cache[w][tv.CH_NAMES].values.astype(np.float64)
        p = prev_s[gi] if prev_s[gi] >= 0 else None
        n = next_s[gi] if next_s[gi] >= 0 else None
        Xw[k] = warp_window(ch, p, scan[gi], n)

    yr = y[sel]
    rg = reg[sel]
    sp = split[sel]
    keep = (rg == 2) & sp
    vk = (rg == 2) & ~sp
    print(f'tail train {int(keep.sum())} val {int(vk.sum())}')

    def run(Xtr, ytr, Xva, yva, tag):
        rng = np.random.default_rng(0)
        model = make_model()
        model.compile(tf.keras.optimizers.Adam(3e-4),
                      loss='sparse_categorical_crossentropy', metrics=['accuracy'])
        classes = np.bincount(ytr, minlength=5)
        cw = {i: len(ytr) / (5 * c) for i, c in enumerate(classes) if c > 0}
        Xva_n = tv.zscore(Xva)
        best = (0.0, -1)
        for ep in range(16):
            p = rng.permutation(len(ytr))
            Xb = tv.zscore(tv.jitter_batch(Xtr[p], rng))
            model.fit(Xb, ytr[p], batch_size=64, class_weight=cw, verbose=0)
            acc = model.evaluate(Xva_n, yva, verbose=0)[1]
            if acc > best[0]:
                best = (acc, ep)
        acc = model.evaluate(Xva_n, yva, verbose=0)[1]
        print(f'[{tag}] tail val acc final {acc*100:.2f}%  best {best[0]*100:.2f}% @ep{best[1]+1}')
        return model

    Xt = d['X'][sel]
    km = keep & (rg == 2)
    vm = vk & (rg == 2)
    Xtr_raw = Xt[km]
    ytr_raw = yr[km]
    Xva_raw = Xt[vm]
    yva_raw = yr[vm]
    Xtr_w = Xw[km]
    ytr_w = yr[km]
    Xva_w = Xw[vm]
    yva_w = yr[vm]
    print(f'controlled sets: raw n={len(ytr_raw)}/{len(yva_raw)}  '
          f'warped n={len(ytr_w)}/{len(yva_w)}')
    run(Xtr_raw, ytr_raw, Xva_raw, yva_raw, 'RAW  ')
    run(Xtr_w, ytr_w, Xva_w, yva_w, 'WARP ')


if __name__ == '__main__':
    main()