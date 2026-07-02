"""Retrain CNN base caller on ALL 6 ESD callers' combined data + background.
Combines MB4000 and MB1000 data, adds inter-peak background windows,
and trains a single robust model.
"""
import os, sys, warnings, argparse
import numpy as np
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
warnings.filterwarnings('ignore')
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

BASE_DIR = '/media/tv/78B0C7DE1FA7081C/electropherogram'
VARIANTS = ['Cp312', 'Cp312_a', 'Cp312_es', 'Cp1_530', 'Cp1_530_sl_ph', 'MD']
LABELS = ['A', 'C', 'G', 'T', 'N']


def build_model(window=31):
    inputs = keras.Input(shape=(window, 4), name='signal')
    x = layers.Conv1D(64, 7, padding='same')(inputs)
    x = layers.BatchNormalization()(x)
    x = layers.LeakyReLU(0.1)(x)
    x = layers.MaxPool1D(2)(x)

    x = layers.Conv1D(128, 5, padding='same')(x)
    x = layers.BatchNormalization()(x)
    x = layers.LeakyReLU(0.1)(x)
    x = layers.MaxPool1D(2)(x)

    x = layers.Conv1D(256, 3, padding='same')(x)
    x = layers.BatchNormalization()(x)
    x = layers.LeakyReLU(0.1)(x)

    x = layers.Conv1D(256, 3, padding='same')(x)
    x = layers.BatchNormalization()(x)
    x = layers.LeakyReLU(0.1)(x)
    x = layers.GlobalAveragePooling1D()(x)

    x = layers.Dense(128)(x)
    x = layers.LeakyReLU(0.1)(x)
    x = layers.Dropout(0.4)(x)
    x = layers.Dense(64)(x)
    x = layers.LeakyReLU(0.1)(x)
    x = layers.Dropout(0.3)(x)
    outputs = layers.Dense(5, activation='softmax', name='base')(x)

    model = keras.Model(inputs, outputs)
    model.compile(
        optimizer=keras.optimizers.Adam(3e-4),
        loss='sparse_categorical_crossentropy',
        metrics=['accuracy']
    )
    return model


def _shift_window(window, shift):
    if shift > 0:
        return np.pad(window[shift:], ((0, shift), (0, 0)), mode='constant')
    elif shift < 0:
        s = -shift
        return np.pad(window[:-s] if s else window, ((s, 0), (0, 0)), mode='constant')
    return window.copy()


class ShiftAugment(keras.utils.Sequence):
    def __init__(self, X, y, batch_size=128, max_shift=8, shuffle=True):
        self.X = X
        self.y = y
        self.batch_size = batch_size
        self.max_shift = max_shift
        self.shuffle = shuffle
        self.indices = np.arange(len(y))
        if shuffle:
            np.random.shuffle(self.indices)

    def __len__(self):
        return int(np.ceil(len(self.y) / self.batch_size))

    def __getitem__(self, idx):
        batch_idx = self.indices[idx * self.batch_size:(idx + 1) * self.batch_size]
        X_b = self.X[batch_idx].copy()
        y_b = self.y[batch_idx]
        shifts = np.random.randint(-self.max_shift, self.max_shift + 1, size=len(batch_idx))
        for i, s in enumerate(shifts):
            if s != 0:
                X_b[i] = _shift_window(X_b[i], s)
        mean = X_b.mean(axis=(1,), keepdims=True)
        std = X_b.std(axis=(1,), keepdims=True) + 1e-8
        X_b = (X_b - mean) / std
        return X_b.astype(np.float32), y_b

    def on_epoch_end(self):
        if self.shuffle:
            np.random.shuffle(self.indices)


def load_combined_data(data_dirs, variants, include_bg=True, quality_min=20):
    """Load and combine training data from multiple directories and variants."""
    all_X, all_y = [], []
    window = None
    total_loaded = 0
    for data_dir in data_dirs:
        for variant in variants:
            path = os.path.join(data_dir, f'{variant}.npz')
            if not os.path.exists(path):
                continue
            d = np.load(path, allow_pickle=True)
            X, y = d['X'], d['y']
            quality = d['quality']
            if window is None:
                window = X.shape[1]
            if X.shape[1] != window:
                continue
            # Filter by quality (keep N regardless)
            if include_bg:
                mask = (y == 4) | (quality > quality_min)
            else:
                mask = (quality > quality_min) & (y != 4)
            X_f = X[mask]
            y_f = y[mask]
            all_X.append(X_f)
            all_y.append(y_f)
            total_loaded += len(X_f)
            vname = os.path.basename(data_dir) + '/' + variant
            print(f"  {vname}: {len(X_f)} samples (from {len(X)} total)")

    if not all_X:
        print("No data loaded!")
        return None, None
    X_all = np.concatenate(all_X, axis=0)
    y_all = np.concatenate(all_y, axis=0)
    print(f"\nTotal: {len(X_all)} samples, window={window}, classes={np.bincount(y_all, minlength=5)}")
    return X_all, y_all


def add_background_interpeak(X, y, positions, all_data, n_extra=2):
    """Add inter-peak background windows (scan positions not near any peak).
    For each well, sample n_extra random non-peak positions per peak.
    """
    bg_X, bg_y = [], []
    for well in all_data:
        df = all_data[well]
        ch = df[['Channel1', 'Channel2', 'Channel3', 'Channel4']].values
        n_scans = len(ch)
        window = 15
        if n_scans < window * 2 + 1:
            continue
        # Find all peak positions for this well
        well_mask = positions == well
        if well_mask.sum() == 0:
            continue
        peak_set = set(positions[well_mask].astype(int))
        # Sample non-peak positions
        candidates = []
        for p in range(window, n_scans - window):
            # Check if within 5 scans of any peak
            too_close = any(abs(p - pk) <= 5 for pk in peak_set)
            if not too_close:
                candidates.append(p)
        if not candidates:
            continue
        n_sample = min(n_extra * len(peak_set), len(candidates))
        sampled = np.random.choice(candidates, n_sample, replace=False)
        for p in sampled:
            win = ch[p - window:p + window + 1]
            bg_X.append(win)
            bg_y.append(4)  # N class

    if bg_X:
        bg_X = np.array(bg_X, dtype=np.float32)
        bg_y = np.array(bg_y, dtype=np.uint8)
        X_out = np.concatenate([X, bg_X], axis=0)
        y_out = np.concatenate([y, bg_y], axis=0)
        print(f"  Added {len(bg_X)} background windows (total N class: {(y_out==4).sum()})")
        return X_out, y_out
    return X, y


def main():
    parser = argparse.ArgumentParser(description='Retrain base caller model on ALL callers')
    parser.add_argument('--data-dirs', nargs='*', default=[
        os.path.join(BASE_DIR, 'training_data_mb4000_v3'),
        os.path.join(BASE_DIR, 'training_data'),
        os.path.join(BASE_DIR, 'training_data_matched_full'),
    ], help='Training data directories')
    parser.add_argument('--output', default=os.path.join(BASE_DIR, 'base_caller_model_combined.keras'),
                        help='Output model path')
    parser.add_argument('--epochs', type=int, default=300, help='Max epochs')
    parser.add_argument('--batch-size', type=int, default=256, help='Batch size')
    parser.add_argument('--quality-min', type=float, default=20, help='Min quality')
    parser.add_argument('--no-bg', action='store_true', help='Exclude N class')
    parser.add_argument('--lr', type=float, default=3e-4, help='Learning rate')
    args = parser.parse_args()

    print("Loading combined training data from:")
    for d in args.data_dirs:
        print(f"  {d}")
    X, y = load_combined_data(
        args.data_dirs, VARIANTS,
        include_bg=not args.no_bg,
        quality_min=args.quality_min,
    )
    if X is None:
        return

    # Stratified split
    n_classes = 5 if not args.no_bg else 4
    rng = np.random.RandomState(42)
    indices = np.arange(len(y))
    train_idx, val_idx, test_idx = [], [], []
    for cls in range(n_classes):
        cls_idx = indices[y == cls]
        if len(cls_idx) == 0:
            continue
        rng.shuffle(cls_idx)
        n = len(cls_idx)
        n_train = int(n * 0.8)
        n_val = int(n * 0.1)
        train_idx.append(cls_idx[:n_train])
        val_idx.append(cls_idx[n_train:n_train + n_val])
        test_idx.append(cls_idx[n_train + n_val:])
    train_idx = np.concatenate(train_idx)
    val_idx = np.concatenate(val_idx)
    test_idx = np.concatenate(test_idx)
    X_train, y_train = X[train_idx], y[train_idx]
    X_val, y_val = X[val_idx], y[val_idx]
    X_test, y_test = X[test_idx], y[test_idx]
    print(f"\nSplit: train={len(y_train)}, val={len(y_val)}, test={len(y_test)}")

    # Class weights
    classes = np.bincount(y_train, minlength=5)
    total = len(y_train)
    n_cls = max(1, (classes > 0).sum())
    class_weight = {i: total / (n_cls * c) if c > 0 else 0.0 for i, c in enumerate(classes)}
    print(f"Class weights: {class_weight}")

    # Build and train model
    model = build_model(window=X.shape[1])
    model.summary()

    train_gen = ShiftAugment(
        X_train, y_train, batch_size=args.batch_size,
        max_shift=8, shuffle=True,
    )

    def _normalize(X):
        m = X.mean(axis=(1,), keepdims=True)
        s = X.std(axis=(1,), keepdims=True) + 1e-8
        return ((X - m) / s).astype(np.float32)

    X_val_norm = _normalize(X_val)
    X_test_norm = _normalize(X_test)

    callbacks = [
        keras.callbacks.EarlyStopping(
            monitor='val_accuracy', patience=30, restore_best_weights=True),
        keras.callbacks.ReduceLROnPlateau(
            monitor='val_loss', factor=0.5, patience=8, min_lr=1e-6),
        keras.callbacks.ModelCheckpoint(
            args.output.replace('.keras', '_checkpoint.keras'),
            monitor='val_accuracy', save_best_only=True),
    ]

    print("\nTraining...")
    history = model.fit(
        train_gen,
        validation_data=(X_val_norm, y_val),
        epochs=args.epochs,
        class_weight=class_weight,
        callbacks=callbacks,
        verbose=1,
    )

    # Evaluate
    print("\n=== Evaluation ===")
    test_loss, test_acc = model.evaluate(X_test_norm, y_test, verbose=0)
    print(f"  Test accuracy: {test_acc:.4f}")

    # Per-class
    y_pred = model.predict(X_test_norm, verbose=0)
    y_pred_class = y_pred.argmax(axis=1)
    label_names = LABELS if not args.no_bg else LABELS[:4]
    for cls, name in enumerate(label_names):
        mask = y_test == cls
        if mask.sum() == 0:
            continue
        acc = (y_pred_class[mask] == cls).mean()
        print(f"  {name}: {acc:.3f} ({int(mask.sum())} samples)")

    # Confidence curve
    from train_model import evaluate_confidence_curve
    curve, best = evaluate_confidence_curve(model, X_test_norm, y_test)
    curve_path = args.output.replace('.keras', '_confidence.csv')
    with open(curve_path, 'w') as f:
        f.write('threshold,accuracy,coverage,n_calls\n')
        for r in curve:
            f.write(f"{r['threshold']:.2f},{r['accuracy']:.4f},{r['coverage']:.4f},{r['n_calls']}\n")
    print(f"\nOptimal threshold: p>={best['threshold']:.2f} "
          f"(acc={best['accuracy']:.4f}, cov={best['coverage']*100:.0f}%)")
    print(f"Confidence curve saved to {curve_path}")

    model.save(args.output)
    print(f"\nModel saved to {args.output}")


if __name__ == '__main__':
    main()
