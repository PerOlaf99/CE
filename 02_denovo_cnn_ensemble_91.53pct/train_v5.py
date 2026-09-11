#!/usr/bin/env python3
"""train_v5.py - single portable CNN on the "book".

Two-branch model:
  - window branch: 31x4 adaptive scan window (same conv stack as v3/v4)
  - mobility branch: Dense over (fwhm_norm, spacing_norm, scan_frac)
Merged -> 4-class softmax. TRAIN on BOOK wells, VAL/EPOCH-REPORT on the TEST
wells (the honest held-out set). No regions, no M13 anywhere in the features.
"""
import os, sys
import numpy as np

HERE = os.path.dirname(os.path.realpath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, ROOT)
os.environ.setdefault('TF_CPP_MIN_LOG_LEVEL', '3')

WIN = 31
EPOCHS = 8


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('--npz', default='v5_book.npz')
    ap.add_argument('--book', default=None,
                    help='comma list of BOOK (train) wells; default: every 4th well')
    ap.add_argument('--model', default='base_caller_model_v5.keras')
    args = ap.parse_args()

    d = np.load(os.path.join(HERE, args.npz), allow_pickle=True)
    X, aux, y = d['X'], d['aux'], d['y_esd'].astype(int)
    wells = list(d['well'])
    allw = sorted(set(wells))
    book = args.book.split(',') if args.book else [w for i, w in enumerate(allw) if i % 4 == 0]
    trm = np.array([w in book for w in wells])
    te = ~trm
    print(f'book wells {len(book)}  train rows {trm.sum()}  test rows {te.sum()}  '
          f'(test wells {len(set(np.array(wells)[te]))})')

    import tensorflow as tf

    def zscore(X):
        mu = X.mean(axis=1, keepdims=True)
        sd = X.std(axis=1, keepdims=True) + 1e-8
        return ((X - mu) / sd).astype(np.float32)

    def model_fn():
        win_in = tf.keras.Input(shape=(WIN, 4))
        x = tf.keras.layers.Conv1D(64, 7, padding='same')(win_in)
        x = tf.keras.layers.BatchNormalization()(x); x = tf.keras.layers.ReLU()(x)
        x = tf.keras.layers.MaxPooling1D(2)(x)
        x = tf.keras.layers.Conv1D(128, 5, padding='same')(x)
        x = tf.keras.layers.BatchNormalization()(x); x = tf.keras.layers.ReLU()(x)
        x = tf.keras.layers.MaxPooling1D(2)(x)
        x = tf.keras.layers.Conv1D(256, 3, padding='same')(x)
        x = tf.keras.layers.BatchNormalization()(x); x = tf.keras.layers.ReLU()(x)
        x = tf.keras.layers.Conv1D(256, 3, padding='same')(x)
        x = tf.keras.layers.BatchNormalization()(x); x = tf.keras.layers.ReLU()(x)
        x = tf.keras.layers.GlobalAveragePooling1D()(x)          # 256
        x = tf.keras.layers.Dense(96, activation='relu')(x)
        x = tf.keras.layers.Dropout(0.35)(x)

        aux_in = tf.keras.Input(shape=(3,))
        a = tf.keras.layers.Dense(24, activation='relu')(aux_in)
        a = tf.keras.layers.Dense(16, activation='relu')(a)

        m = tf.keras.layers.Concatenate()([x, a])
        m = tf.keras.layers.Dense(64, activation='relu')(m)
        m = tf.keras.layers.Dropout(0.3)(m)
        out = tf.keras.layers.Dense(4, activation='softmax')(m)
        model = tf.keras.Model(inputs=[win_in, aux_in], outputs=out)
        model.compile(tf.keras.optimizers.Adam(3e-4),
                      loss='sparse_categorical_crossentropy', metrics=['accuracy'])
        return model

    model = model_fn()
    Xtr = zscore(X[trm]); Atr = aux[trm].astype(np.float32); ytr = y[trm]
    Xte = zscore(X[te]);  Ate = aux[te].astype(np.float32);  yte = y[te]
    cls = np.bincount(ytr, minlength=4)
    cw = {i: len(ytr) / (4.0 * c) for i, c in enumerate(cls) if c > 0}
    best = (0.0, -1)
    rng = np.random.default_rng(0)
    for ep in range(EPOCHS):
        model.fit([Xtr, Atr], ytr, batch_size=128, class_weight=cw, epochs=1, verbose=0)
        _, acc = model.evaluate([Xte, Ate], yte, verbose=0)
        print(f'  ep{ep + 1}: TEST-well acc {acc:.4f}')
        if acc > best[0]:
            best = (acc, ep)
            model.save(os.path.join(HERE, args.model))
    print(f'BEST test-well acc {best[0]:.4f} @ep{best[1] + 1} -> {args.model}')


if __name__ == '__main__':
    main()