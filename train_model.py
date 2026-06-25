import os, sys
import numpy as np
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers

def build_model():
    inputs = keras.Input(shape=(31, 4), name='signal')
    x = layers.Conv1D(32, 3, padding='same')(inputs)
    x = layers.BatchNormalization()(x)
    x = layers.ReLU()(x)
    x = layers.MaxPool1D(2)(x)  # 15

    x = layers.Conv1D(64, 3, padding='same')(x)
    x = layers.BatchNormalization()(x)
    x = layers.ReLU()(x)
    x = layers.MaxPool1D(2)(x)  # 7

    x = layers.Conv1D(128, 3, padding='same')(x)
    x = layers.BatchNormalization()(x)
    x = layers.ReLU()(x)
    x = layers.GlobalAveragePooling1D()(x)

    x = layers.Dense(64)(x)
    x = layers.ReLU()(x)
    x = layers.Dropout(0.5)(x)
    outputs = layers.Dense(5, activation='softmax', name='base')(x)

    model = keras.Model(inputs, outputs)
    model.compile(
        optimizer=keras.optimizers.Adam(1e-3),
        loss='sparse_categorical_crossentropy',
        metrics=['accuracy']
    )
    return model


def load_data(data_dir):
    path = os.path.join(data_dir, 'Cp312.npz')
    d = np.load(path, allow_pickle=True)
    X = d['X']
    y = d['y']
    quality = d['quality']
    return X, y, quality


def main():
    data_dir = sys.argv[1] if len(sys.argv) > 1 else \
        '/media/per/Disk 2/electropherogram/training_data'
    output_path = sys.argv[2] if len(sys.argv) > 2 else \
        '/media/per/Disk 2/electropherogram/base_caller_model.keras'

    print(f"Loading data from {data_dir}")
    X, y, quality = load_data(data_dir)
    print(f"  X: {X.shape}, y: {y.shape}")
    print(f"  Distribution: A={int((y==0).sum())} C={int((y==1).sum())} "
          f"G={int((y==2).sum())} T={int((y==3).sum())} N={int((y==4).sum())}")

    # Filter high-quality positions only
    mask = quality > 20
    X, y = X[mask], y[mask]
    print(f"  After quality > 20 filter: {len(y)} positions")

    # Remove Ns (class 4) — they're noise
    n_mask = y != 4
    X, y = X[n_mask], y[n_mask]
    print(f"  After removing Ns: {len(y)} positions")

    # Normalize per-sample (z-score per channel)
    X_mean = X.mean(axis=(1,), keepdims=True)
    X_std = X.std(axis=(1,), keepdims=True) + 1e-8
    X = (X - X_mean) / X_std

    # Manual stratified split (no sklearn dependency)
    rng = np.random.RandomState(42)
    indices = np.arange(len(y))
    train_idx, tmp_idx, val_idx, test_idx = [], [], [], []
    for cls in range(4):
        cls_idx = indices[y == cls]
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

    # Class weights
    classes = np.bincount(y_train)
    total = len(y_train)
    class_weight = {i: total / (len(classes) * c) for i, c in enumerate(classes)}
    print(f"  Class weights: {class_weight}")

    model = build_model()
    model.summary()

    callbacks = [
        keras.callbacks.EarlyStopping(
            monitor='val_accuracy', patience=10, restore_best_weights=True),
        keras.callbacks.ReduceLROnPlateau(
            monitor='val_loss', factor=0.5, patience=5, min_lr=1e-6),
    ]

    print("\nTraining...")
    history = model.fit(
        X_train, y_train,
        validation_data=(X_val, y_val),
        epochs=100,
        batch_size=128,
        class_weight=class_weight,
        callbacks=callbacks,
        verbose=1,
    )

    print("\nEvaluating...")
    test_loss, test_acc = model.evaluate(X_test, y_test, verbose=0)
    print(f"  Test accuracy: {test_acc:.4f}")

    model.save(output_path)
    print(f"\nModel saved to {output_path}")

    # Per-class accuracy
    y_pred = model.predict(X_test, verbose=0)
    y_pred_class = y_pred.argmax(axis=1)
    for cls, name in enumerate(['A', 'C', 'G', 'T']):
        mask = y_test == cls
        acc = (y_pred_class[mask] == cls).mean()
        print(f"  {name}: {acc:.3f} ({int(mask.sum())} samples)")


if __name__ == '__main__':
    main()
