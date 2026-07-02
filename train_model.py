import os, sys, warnings, argparse
import numpy as np
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
warnings.filterwarnings('ignore')
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

def build_model(window=31):
    inputs = keras.Input(shape=(window, 4), name='signal')
    x = layers.Conv1D(64, 5, padding='same')(inputs)
    x = layers.BatchNormalization()(x)
    x = layers.ReLU()(x)
    x = layers.MaxPool1D(2)(x)

    x = layers.Conv1D(128, 5, padding='same')(x)
    x = layers.BatchNormalization()(x)
    x = layers.ReLU()(x)
    x = layers.MaxPool1D(2)(x)

    x = layers.Conv1D(256, 3, padding='same')(x)
    x = layers.BatchNormalization()(x)
    x = layers.ReLU()(x)

    x = layers.Conv1D(256, 3, padding='same')(x)
    x = layers.BatchNormalization()(x)
    x = layers.ReLU()(x)
    x = layers.GlobalAveragePooling1D()(x)

    x = layers.Dense(128)(x)
    x = layers.ReLU()(x)
    x = layers.Dropout(0.4)(x)
    x = layers.Dense(64)(x)
    x = layers.ReLU()(x)
    x = layers.Dropout(0.3)(x)
    outputs = layers.Dense(5, activation='softmax', name='base')(x)

    model = keras.Model(inputs, outputs)
    model.compile(
        optimizer=keras.optimizers.Adam(5e-4),
        loss='sparse_categorical_crossentropy',
        metrics=['accuracy']
    )
    return model


def _shift_window(window, shift):
    """Non-wrapping shift: pad zeros on one side, crop on the other."""
    if shift > 0:
        return np.pad(window[shift:], ((0, shift), (0, 0)), mode='constant')
    elif shift < 0:
        s = -shift
        return np.pad(window[:-s] if s else window, ((s, 0), (0, 0)), mode='constant')
    return window.copy()


class ShiftAugment(keras.utils.Sequence):
    def __init__(self, X, y, batch_size=128, max_shift=6, shuffle=True):
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

        # Random shift augmentation (±max_shift)
        shifts = np.random.randint(-self.max_shift, self.max_shift + 1, size=len(batch_idx))
        for i, s in enumerate(shifts):
            if s != 0:
                X_b[i] = _shift_window(X_b[i], s)

        # Per-sample z-score normalization
        mean = X_b.mean(axis=(1,), keepdims=True)
        std = X_b.std(axis=(1,), keepdims=True) + 1e-8
        X_b = (X_b - mean) / std

        return X_b.astype(np.float32), y_b

    def on_epoch_end(self):
        if self.shuffle:
            np.random.shuffle(self.indices)


def load_data(data_dir):
    path = os.path.join(data_dir, 'Cp312.npz')
    d = np.load(path, allow_pickle=True)
    X, y = d['X'], d['y']
    quality = d['quality']
    return X, y, quality


def evaluate_confidence_curve(model, X_test, y_test):
    """Evaluate accuracy at various confidence thresholds and find optimal cutoff."""
    y_pred = model.predict(X_test, verbose=0)
    y_pred_class = y_pred.argmax(axis=1)
    y_pred_prob = y_pred.max(axis=1)

    thresholds = np.arange(0.0, 1.0, 0.05)
    results = []
    for t in thresholds:
        mask = y_pred_prob >= t
        if mask.sum() == 0:
            results.append({'threshold': t, 'accuracy': 0, 'coverage': 0, 'n_calls': 0})
            continue
        acc = (y_pred_class[mask] == y_test[mask]).mean()
        results.append({
            'threshold': t,
            'accuracy': acc,
            'coverage': mask.mean(),
            'n_calls': int(mask.sum()),
        })

    # Find optimal threshold (balance accuracy vs coverage)
    # Maximize acc * sqrt(coverage) — prefers high accuracy with decent coverage
    scores = [r['accuracy'] * np.sqrt(r['coverage']) for r in results]
    best_idx = np.argmax(scores)
    best = results[best_idx]

    return results, best


def load_data(data_dir, variant='Cp312'):
    path = os.path.join(data_dir, f'{variant}.npz')
    d = np.load(path, allow_pickle=True)
    X, y = d['X'], d['y']
    quality = d['quality']
    return X, y, quality


def main():
    parser = argparse.ArgumentParser(description='Train CNN base caller model')
    parser.add_argument('--data-dir', default='/media/per/Disk 2/electropherogram/training_data',
                        help='Training data directory')
    parser.add_argument('--output', default=None,
                        help='Output model path (default: auto-named)')
    parser.add_argument('--variant', default='Cp312',
                        help='Variant name to train on (default Cp312)')
    parser.add_argument('--epochs', type=int, default=200,
                        help='Maximum training epochs')
    parser.add_argument('--batch-size', type=int, default=128,
                        help='Batch size for training')
    parser.add_argument('--max-shift', type=int, default=6,
                        help='Maximum shift augmentation')
    parser.add_argument('--quality-min', type=float, default=20,
                        help='Minimum quality score filter')
    parser.add_argument('--lr', type=float, default=5e-4,
                        help='Initial learning rate')
    parser.add_argument('--include-background', action='store_true', default=False,
                        help='Include N/background class from training data')
    args = parser.parse_args()

    data_dir = args.data_dir
    output_path = args.output
    if output_path is None:
        suffix = '_with_bg' if args.include_background else ''
        output_path = f'/media/per/Disk 2/electropherogram/base_caller_model{suffix}.keras'

    print(f"Loading data from {data_dir}")
    X, y, quality = load_data(data_dir, args.variant)
    n_tot = len(y)
    print(f"  X: {X.shape}, y: {y.shape}")

    # Filter high quality, optionally remove Ns
    if args.include_background:
        # Keep N/background regardless of quality, filter others by quality
        mask = (y == 4) | (quality > args.quality_min)
        X, y = X[mask], y[mask]
        n_after = len(y)
        n_n = int((y == 4).sum())
        print(f"  After quality filter: {n_after}/{n_tot} kept ({n_n} background/N)")
    else:
        mask = (quality > args.quality_min) & (y != 4)
        X, y = X[mask], y[mask]
        n_after = len(y)
        print(f"  After quality>{args.quality_min} & no-N filter: {n_after}/{n_tot} kept")

    # Distribution
    label_names = ['A', 'C', 'G', 'T']
    if args.include_background:
        label_names.append('N')
    for cls, name in enumerate(label_names):
        print(f"    {name}: {int((y==cls).sum())}")

    # Stratified split
    n_classes = 5 if args.include_background else 4
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

    print(f"  Train: {len(y_train)}, Val: {len(y_val)}, Test: {len(y_test)}")

    # Class weights (handles up to 5 classes including N)
    classes = np.bincount(y_train, minlength=5)
    total = len(y_train)
    n_cls = max(1, (classes > 0).sum())
    class_weight = {i: total / (n_cls * c) if c > 0 else 0.0 for i, c in enumerate(classes)}
    print(f"  Class weights: {class_weight}")

    # Build model
    model = build_model(window=X.shape[1])
    model.summary()

    # Data generators with augmentation
    train_gen = ShiftAugment(X_train, y_train, batch_size=args.batch_size,
                             max_shift=args.max_shift, shuffle=True)

    # For validation, apply z-score normalization (no augmentation)
    def _normalize(X):
        m = X.mean(axis=(1,), keepdims=True)
        s = X.std(axis=(1,), keepdims=True) + 1e-8
        return ((X - m) / s).astype(np.float32)

    X_val_norm = _normalize(X_val)
    X_test_norm = _normalize(X_test)
    # Also create shifted test sets to evaluate robustness
    X_test_shifted = {}
    for s in [-4, -2, 2, 4]:
        X_s = np.array([_shift_window(x, s) for x in X_test])
        X_test_shifted[s] = _normalize(X_s)

    callbacks = [
        keras.callbacks.EarlyStopping(
            monitor='val_accuracy', patience=20, restore_best_weights=True),
        keras.callbacks.ReduceLROnPlateau(
            monitor='val_loss', factor=0.5, patience=5, min_lr=1e-6),
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

    print("\nEvaluating...")
    test_loss, test_acc = model.evaluate(X_test_norm, y_test, verbose=0)
    print(f"  Test (centered): accuracy = {test_acc:.4f}")

    for s, X_s in X_test_shifted.items():
        loss_s, acc_s = model.evaluate(X_s, y_test, verbose=0)
        print(f"  Test (shift={s:+d}): accuracy = {acc_s:.4f}")

    # Confidence evaluation curve
    print("\nConfidence threshold analysis:")
    curve, best = evaluate_confidence_curve(model, X_test_norm, y_test)
    for r in curve:
        cov_pct = r['coverage'] * 100
        if r['n_calls'] > 0:
            print(f"  p>={r['threshold']:.2f}: acc={r['accuracy']:.4f}  "
                  f"cov={cov_pct:.0f}%  n={r['n_calls']}")
    print(f"\n  Optimal threshold: p>={best['threshold']:.2f} "
          f"(acc={best['accuracy']:.4f}, cov={best['coverage']*100:.0f}%)")

    # Save confidence curve data alongside model
    curve_path = output_path.replace('.keras', '_confidence.csv')
    with open(curve_path, 'w') as f:
        f.write('threshold,accuracy,coverage,n_calls\n')
        for r in curve:
            f.write(f"{r['threshold']:.2f},{r['accuracy']:.4f},{r['coverage']:.4f},{r['n_calls']}\n")
    print(f"  Confidence curve saved to {curve_path}")

    model.save(output_path)
    print(f"\nModel saved to {output_path}")

    # Per-class accuracy
    y_pred = model.predict(X_test_norm, verbose=0)
    y_pred_class = y_pred.argmax(axis=1)
    label_names = ['A', 'C', 'G', 'T', 'N'] if args.include_background else ['A', 'C', 'G', 'T']
    for cls, name in enumerate(label_names):
        mask = y_test == cls
        if mask.sum() == 0:
            continue
        acc = (y_pred_class[mask] == cls).mean()
        print(f"  {name}: {acc:.3f} ({int(mask.sum())} samples)")


if __name__ == '__main__':
    main()
