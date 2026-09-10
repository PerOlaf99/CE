#!/usr/bin/env python3
"""train_v3_late.py - fine-tune the v2 model on LAST-THIRD-of-read windows.

error_budget.py showed ~75% of residual errors sit in Q4 (signal-decay
tail). This reuses train_v2's data pipeline but restricts training to late
windows (+ late negatives), mixes in a global sample to limit forgetting,
and saves the checkpoint that scores best on held-out LATE windows."""
import os
import sys

HERE = os.path.dirname(os.path.realpath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, ROOT)
os.environ.setdefault('TF_CPP_MIN_LOG_LEVEL', '3')

import numpy as np
import cimarrontv as cim
from train_v2 import make_window, zscore, jitter_batch, NEG_FRAC, WINDOW

EPOCHS = 10
LATE_FRAC = 0.66
LR = 3e-5
GLOBAL_MIX = 0.5


def main():
    d = np.load(os.path.join(ROOT, 'm13_clean_training_full.npz'),
                allow_pickle=True)
    X, y, wells, scans = d['X'], d['y'].astype(int), d['wells'], d['scans']
    all_wells = sorted(set(wells))
    test_wells = set(all_wells[::8])
    te = np.array([w in test_wells for w in wells])
    tr = ~te

    hi = np.zeros(len(scans), dtype=np.int64)
    for w in all_wells:
        m = wells == w
        hi[m] = scans[m].max()
    late = scans >= (LATE_FRAC * hi)
    tr_late = tr & late
    te_late = te & late
    print(f'train windows {tr.sum()} (late {tr_late.sum()})  '
          f'held-out late windows {te_late.sum()}')

    rng = np.random.default_rng(42)

    neg_X, neg_y = [], []
    uniq_wells = sorted(set(wells[tr]))
    n_neg_target = int(NEG_FRAC * tr_late.sum())
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
        h = pk.max()
        mids = [int((a + b) // 2) for a, b in zip(pk[:-1], pk[1:])
                if b - a >= 1.3 * med and (a + b) // 2 >= LATE_FRAC * h]
        far = rng.integers(int(LATE_FRAC * h), len(chw) - 200,
                           size=per_well)
        far = [int(s) for s in far if np.min(np.abs(pk - s)) > 2 * WINDOW]
        picks = (mids[:per_well // 2] + far)[:per_well]
        for s in picks:
            neg_X.append(make_window(chw, s))
            neg_y.append(4)
    print(f'late negatives: {len(neg_y)}')

    n_glob = int(GLOBAL_MIX * tr_late.sum())
    glob_idx = rng.choice(np.where(tr)[0], size=min(n_glob, int(tr.sum())),
                          replace=False)
    Xtr = np.concatenate([X[tr_late],
                          np.array(neg_X, dtype=np.float32),
                          X[glob_idx]])
    ytr = np.concatenate([y[tr_late], np.array(neg_y), y[glob_idx]])
    idx = rng.permutation(len(ytr))
    Xtr, ytr = Xtr[idx], ytr[idx]
    print(f'fine-tune set: {len(ytr)} windows '
          f'(late real {int(tr_late.sum())} + late neg {len(neg_y)} '
          f'+ global mix {len(glob_idx)})')

    Xte = X[te]
    Xte_n = zscore(Xte)
    te_global = np.where(te)[0]
    late_local = np.isin(te_global, np.where(te_late)[0])
    Xlate_n = Xte_n[late_local]
    ylate = y[te][late_local]

    import tensorflow as tf
    model = tf.keras.models.load_model(
        os.path.join(HERE, 'base_caller_model_v2.keras'), compile=False)
    model.compile(optimizer=tf.keras.optimizers.Adam(LR),
                  loss='sparse_categorical_crossentropy', metrics=['accuracy'])

    classes = np.bincount(ytr, minlength=5)
    cw = {i: len(ytr) / (5 * c) for i, c in enumerate(classes) if c > 0}
    print('class weights:', {k: round(v, 2) for k, v in cw.items()})

    _, base_all = model.evaluate(Xte_n, y[te], verbose=0)
    _, base_late = model.evaluate(Xlate_n, ylate, verbose=0)
    print(f'v2 baseline on holdout: all={base_all:.4f} '
          f'late={base_late:.4f}', flush=True)

    best = base_late
    for ep in range(EPOCHS):
        r = rng.permutation(len(ytr))
        epochs_X = zscore(jitter_batch(Xtr[r], rng))
        model.fit(epochs_X, ytr[r], batch_size=64, class_weight=cw, verbose=0)
        _, acc_all = model.evaluate(Xte_n, y[te], verbose=0)
        _, acc_late = model.evaluate(Xlate_n, ylate, verbose=0)
        print(f'epoch {ep + 1}: val_all={acc_all:.4f} '
              f'val_LATE={acc_late:.4f}', flush=True)
        if acc_late > best:
            best = acc_late
            model.save(os.path.join(HERE, 'base_caller_model_v3_late.keras'))
            print('  saved', flush=True)
    print(f'BEST late val_acc={best:.4f}')


if __name__ == '__main__':
    main()
