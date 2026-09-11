#!/usr/bin/env python3
"""train_v9_weekend.py - v9 adaptive-width per-region CNNs.

Each 8-region model uses its own window half-width (W_R) matching the CE peak
physics, and trains on jittered windows (±3 scans) so de-novo candidates that
sit 1-3 scans off-axis still classify correctly.  Resumable: skips regions
whose final model file already exists unless --force.  Checkpoints saved after
the best validation epoch per region.

Output: base_caller_model_v9_r{r}.keras  (compile=False-ready)
"""
import os, sys, argparse, time
import numpy as np
os.environ.setdefault('TF_CPP_MIN_LOG_LEVEL', '3')
HERE = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0, HERE)
import tensorflow as tf

W_R = (8, 10, 12, 14, 15, 18, 24, 30)
J = 3
EPOCHS = 24
PATIENCE = 6
BATCH = 256


def zscore(X):
    mu = X.mean(axis=1, keepdims=True)
    sd = X.std(axis=1, keepdims=True) + 1e-8
    return ((X - mu) / sd).astype(np.float32)


def build_model(W):
    return tf.keras.Sequential([
        tf.keras.layers.Input(shape=(2 * W + 1, 4)),
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
        tf.keras.layers.Dense(4, activation='softmax'),
    ])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--epochs', type=int, default=EPOCHS)
    ap.add_argument('--force', action='store_true',
                    help='retrain regions even if model exists')
    ap.add_argument('--log', default='weekend_train.log')
    ap.add_argument('--regions', default='0,1,2,3,4,5,6,7')
    args = ap.parse_args()
    log = open(args.log, 'a', buffering=1)

    results = {}
    for r in map(int, args.regions.split(',')):
        npz = os.path.join(HERE, f'v9_weekend_r{r}.npz')
        model_path = os.path.join(HERE, f'base_caller_model_v9_r{r}.keras')
        if not os.path.exists(npz):
            print(f'region{r}: missing {npz}, skip'); continue
        if os.path.exists(model_path) and not args.force:
            print(f'region{r}: {model_path} exists, skip (--force to retrain)')
            continue
        d = np.load(npz, allow_pickle=True)
        X, y = d['X'].astype(np.float32), d['y'].astype(int)
        split = d['split'].astype(bool)
        trm, va = split, ~split
        print(f'region{r}: X={X.shape} n_tr={trm.sum()} n_va={va.sum()} '
              f'start={time.strftime("%Y-%m-%d %H:%M")}')
        log.write(f'region{r}: start {time.strftime("%Y-%m-%d %H:%M")} '
                  f'X={X.shape}\n')
        if va.sum() < 100 or trm.sum() < 300:
            print('  skip (too few)'); continue
        Xn_tr = zscore(X[trm]); Xn_va = zscore(X[va])
        classes = np.bincount(y[trm], minlength=4)
        cw = {i: len(y[trm]) / (4 * c) for i, c in enumerate(classes) if c > 0}
        model = build_model(W_R[r])
        model.compile(tf.keras.optimizers.Adam(3e-4),
                      loss='sparse_categorical_crossentropy', metrics=['accuracy'])
        best = (0.0, -1)
        no_improve = 0
        for ep in range(args.epochs):
            model.fit(Xn_tr, y[trm], batch_size=BATCH, class_weight=cw,
                      verbose=0)
            _, acc = model.evaluate(Xn_va, y[va], verbose=0)
            msg = (f'  region{r} ep{ep + 1} val_acc={acc:.4f} '
                   f'{time.strftime("%H:%M")}')
            print(msg); log.write(msg + '\n')
            if acc > best[0]:
                best = (acc, ep)
                no_improve = 0
                model.save(model_path)
            else:
                no_improve += 1
                if no_improve >= PATIENCE:
                    print(f'  region{r}: early stop @ep{ep + 1}')
                    log.write(f'  region{r}: early stop @ep{ep + 1}\n')
                    break
        msg = f'region{r} BEST val_acc={best[0]:.4f} @ep{best[1] + 1}'
        print(msg); log.write(msg + '\n')
        results[r] = best[0]
    log.write(f'ALL DONE {time.strftime("%Y-%m-%d %H:%M")} '
              + ' '.join(f'r{k}={v:.4f}' for k, v in sorted(results.items()))
              + '\n')
    log.close()


if __name__ == '__main__':
    main()