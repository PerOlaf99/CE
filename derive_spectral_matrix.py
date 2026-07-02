#!/usr/bin/env python3
"""Derive spectral matrix using multiple approaches:

1. Method A: Peak-of-each-dye — at each ESD position, find the local max 
   of each channel within a window, build emission profile from these peaks.
2. Method B: NMF — factorize raw trace segments to find dye profiles.
3. Method C: LDA — optimal linear discriminant for classification.
4. Method D: Gradient optimization of classification accuracy.
"""
import os, sys
import numpy as np
import warnings
warnings.filterwarnings('ignore')
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

sys.path.insert(0, os.path.dirname(__file__))
from extract_training_data import parse_rsd, parse_esd

BASE_MAP = {'A': 0, 'C': 1, 'G': 2, 'T': 3}
BASE_LABELS = ['A', 'C', 'G', 'T']
CH_NAMES = ['Channel1', 'Channel2', 'Channel3', 'Channel4']

MOBILITY = {0: -3, 1: -1, 2: 1, 3: 3}  # T, G, C, A offsets (scans)
CH_TO_DYE = {0: 'T', 1: 'G', 2: 'C', 3: 'A'}  # channel -> dye


def extract_all_data(base_dir, wells, variant='Cp312'):
    """Extract raw channel data at and around ESD positions."""
    esd_subdir = f"MB1000_M13_DT_{variant}_MD1"
    records = []
    for well in wells:
        rsd_path = os.path.join(base_dir, f"{well}.rsd")
        esd_path = os.path.join(base_dir, esd_subdir, f"{well}.esd")
        if not os.path.exists(rsd_path) or not os.path.exists(esd_path):
            continue
        try:
            df = parse_rsd(rsd_path)
            esd = parse_esd(esd_path)
        except Exception:
            continue

        seq = esd.get('sequence', '')
        pos = esd.get('peak_positions')
        if pos is None:
            pos = esd.get('bases_positions')
        qual = esd.get('quality_scores')
        if not seq or pos is None or qual is None or len(pos) == 0:
            continue

        n = min(len(seq), len(pos), len(qual))
        seq = seq[:n]
        pos = np.asarray(pos[:n]).astype(int)
        qual = np.asarray(qual[:n])

        ch = df[CH_NAMES].values.astype(np.float64)
        n_scans = len(ch)

        for i in range(n):
            if qual[i] < 10:
                continue
            b = seq[i].upper()
            if b not in BASE_MAP:
                continue
            p = pos[i]
            if p < 0 or p >= n_scans:
                continue
            records.append({
                'well': well,
                'base': BASE_MAP[b],
                'base_char': b,
                'esd_pos': p,
                'ch_raw': ch[p].copy(),
            })
    return records


def approach_peak_of_each_dye(records, window=7):
    """For each ESD position, scan ±window scans and find the peak
    position of each dye's channel. Record channel values at those positions.

    Builds emission matrix: for each base call, look at the channel values
    at the PEAK of the dye that should correspond to that base.
    """
    raise NotImplementedError("Need full trace data for peak scanning")



def approach_linear_discriminant(records):
    """Linear Discriminant Analysis for optimal classification projection.
    The projection matrix gives us the best linear separation.
    """
    X = np.array([r['ch_raw'] for r in records], dtype=np.float64)
    y = np.array([r['base'] for r in records], dtype=np.int32)

    # Center the data
    mean = X.mean(axis=0)
    Xc = X - mean

    # Compute within-class and between-class scatter
    Sw = np.zeros((4, 4), dtype=np.float64)
    Sb = np.zeros((4, 4), dtype=np.float64)

    overall_mean = Xc.mean(axis=0)

    for cls in range(4):
        X_cls = Xc[y == cls]
        if len(X_cls) < 2:
            continue
        cls_mean = X_cls.mean(axis=0)
        # Within-class scatter
        X_centered = X_cls - cls_mean
        Sw += X_centered.T @ X_centered
        # Between-class scatter
        n_cls = len(X_cls)
        mean_diff = cls_mean - overall_mean
        Sb += n_cls * np.outer(mean_diff, mean_diff)

    # Solve generalized eigenvalue problem: Sb @ v = lambda * Sw @ v
    # Note: Sw might be singular if features are correlated
    # Use pseudo-inverse
    Sw_inv = np.linalg.pinv(Sw)
    M = Sw_inv @ Sb

    eigenvalues, eigenvectors = np.linalg.eig(M)
    # Sort by eigenvalue magnitude (real part)
    idx = np.argsort(-np.real(eigenvalues))
    W = np.real(eigenvectors[:, idx[:4]])

    # W is the projection matrix (4 features -> 4 discriminants)
    # For classification we want X @ W to separate the classes
    # The LDA projection can be used directly

    return W, mean


def approach_gradient_optimization(records, n_iter=5000, lr=0.001):
    """Gradient descent to find spectral matrix maximizing classification accuracy.
    
    We want to find separation matrix S (4×4) such that:
    argmax(raw @ S) = correct base
    
    Using softmax cross-entropy loss.
    """
    import tensorflow as tf
    import tensorflow.keras.backend as K

    X = np.array([r['ch_raw'] for r in records], dtype=np.float64)
    y = np.array([r['base'] for r in records], dtype=np.int32)

    # Normalize
    X_mean = X.mean(axis=0)
    X_std = X.std(axis=0) + 1e-8
    Xn = (X - X_mean) / X_std

    # Convert to tensors
    X_t = tf.constant(Xn, dtype=tf.float64)
    y_t = tf.constant(y, dtype=tf.int32)

    # Initialize separation matrix close to identity (with some noise)
    S = tf.Variable(
        np.eye(4, dtype=np.float64) + np.random.randn(4, 4).astype(np.float64) * 0.1,
        dtype=tf.float64
    )

    optimizer = tf.optimizers.Adam(learning_rate=lr)

    best_loss = float('inf')
    best_S = None
    history = []

    for step in range(n_iter):
        with tf.GradientTape() as tape:
            unmixed = X_t @ S
            unmixed = tf.maximum(unmixed, 0.0)
            # Softmax cross-entropy with 4 classes
            logits = unmixed
            loss = tf.reduce_mean(
                tf.nn.sparse_softmax_cross_entropy_with_logits(
                    labels=y_t, logits=logits
                )
            )
            # Regularize: encourage diagonal dominance
            diag = tf.linalg.diag_part(S)
            off_diag = S - tf.linalg.diag(diag)
            reg = 0.01 * (tf.reduce_sum(tf.square(off_diag)))
            loss = loss + reg

        grads = tape.gradient(loss, [S])
        optimizer.apply_gradients(zip(grads, [S]))

        if step % 500 == 0:
            # Compute accuracy
            unmixed_np = unmixed.numpy()
            preds = np.argmax(unmixed_np, axis=1)
            acc = (preds == y).mean()
            history.append((step, float(loss), acc))
            if step % 1000 == 0:
                print(f"  Step {step}: loss={float(loss):.4f}, acc={acc:.4f}")

            if float(loss) < best_loss:
                best_loss = float(loss)
                best_S = S.numpy().copy()

    best_S = S.numpy()

    # Scale back to original data range
    best_S = best_S / X_std[:, None]  # Adjust for the normalization
    offset = -X_mean @ best_S  # Bias term

    print(f"\n  Final loss: {float(loss):.4f}, best loss: {best_loss:.4f}")

    return best_S, offset


def evaluate_matrix(records, sep_matrix, label="Matrix"):
    """Evaluate a separation matrix on the test data."""
    X = np.array([r['ch_raw'] for r in records], dtype=np.float64)
    y = np.array([r['base'] for r in records], dtype=np.int32)
    y_str = np.array([r['base_char'] for r in records])

    # Apply separation
    unmixed = X @ sep_matrix.T
    unmixed = np.maximum(unmixed, 0)

    # Classify by dominant channel
    dominant = np.argmax(unmixed, axis=1)
    preds = np.array([BASE_LABELS[d] for d in dominant])
    true = y_str

    acc = (preds == true).mean()
    print(f"\n  {label}: overall acc = {acc:.4f} ({int(acc * len(true))}/{len(true)})")

    # Per-base
    for b in BASE_LABELS:
        mask = true == b
        if mask.sum() == 0:
            continue
        ba = (preds[mask] == b).mean()
        print(f"    {b}: {ba:.4f} ({mask.sum():>4} samples)")

    # Confusion matrix
    cm = np.zeros((4, 4), dtype=int)
    for i, b in enumerate(BASE_LABELS):
        mask = true == b
        for j, p_b in enumerate(BASE_LABELS):
            cm[i, j] = int((preds[mask] == p_b).sum())

    # Find most confused pairs
    print(f"    Confusion matrix (rows=true):")
    for i, b in enumerate(BASE_LABELS):
        row = " ".join(f"{cm[i,j]:5d}" for j in range(4))
        print(f"      {b}: {row}")

    return acc, sep_matrix, dominant


def evaluate_max_channel(records):
    """Simple max-channel classifier as baseline."""
    X = np.array([r['ch_raw'] for r in records], dtype=np.float64)
    y_str = np.array([r['base_char'] for r in records])
    max_ch = np.argmax(X, axis=1)
    preds = np.array([CH_TO_DYE[c] for c in max_ch])
    acc = (preds == y_str).mean()

    print(f"\n  Raw max-channel baseline:")
    print(f"    overall acc = {acc:.4f} ({int(acc * len(y_str))}/{len(y_str)})")
    for b in BASE_LABELS:
        mask = y_str == b
        if mask.sum() == 0:
            continue
        ba = (preds[mask] == b).mean()
        print(f"    {b}: {ba:.4f} ({mask.sum():>4} samples)")
    return acc


def main():
    base_dir = '/media/per/Disk 2/electropherogram/MB1000_M13_DT'
    wells = [f"{r}{c:02d}" for r in 'ABCDEFGH' for c in range(1, 13)]

    print("Loading data...")
    records = extract_all_data(base_dir, wells, 'Cp312')
    print(f"  {len(records)} records from 96 wells")

    # Split into train/test
    rng = np.random.RandomState(42)
    wells_unique = sorted(set(r['well'] for r in records))
    rng.shuffle(wells_unique)
    n_train = int(len(wells_unique) * 0.8)
    train_wells = set(wells_unique[:n_train])
    test_wells = set(wells_unique[n_train:])

    train_records = [r for r in records if r['well'] in train_wells]
    test_records = [r for r in records if r['well'] in test_wells]
    print(f"  Train: {len(train_records)}, Test: {len(test_records)}")

    # Baseline
    print("\n=== BASELINE: Raw max-channel ===")
    evaluate_max_channel(train_records)
    evaluate_max_channel(test_records)

    # Approach: LDA
    print("\n=== APPROACH 1: Linear Discriminant Analysis ===")
    W, mean = approach_linear_discriminant(train_records)
    print(f"  LDA projection matrix:")
    for i in range(4):
        print(f"    [{W[i][0]:8.4f} {W[i][1]:8.4f} {W[i][2]:8.4f} {W[i][3]:8.4f}]")

    W, _ = approach_linear_discriminant(train_records)
    # W from eigendecomposition is eigenvectors, we want to use it as projection
    evaluate_matrix(train_records, W.T, "LDA (train)")
    evaluate_matrix(test_records, W.T, "LDA (test)")

    # Approach: Gradient optimization
    print("\n=== APPROACH 2: Gradient-optimized separation matrix ===")
    print("  Training...")
    sep_matrix, offset = approach_gradient_optimization(train_records, n_iter=5000, lr=0.001)

    print(f"\n  Optimized separation matrix:")
    for i in range(4):
        print(f"    [{sep_matrix[i][0]:8.4f} {sep_matrix[i][1]:8.4f} {sep_matrix[i][2]:8.4f} {sep_matrix[i][3]:8.4f}]")

    evaluate_matrix(train_records, sep_matrix, "Gradient-opt (train)")
    evaluate_matrix(test_records, sep_matrix, "Gradient-opt (test)")

    # Also evaluate the old default matrix
    print("\n=== OLD: Default matrix (current) ===")
    DEFAULT_SPEC_MATRIX = np.array([
        [0.85, 0.03, 0.05, 0.07],
        [0.02, 0.88, 0.04, 0.06],
        [0.06, 0.04, 0.86, 0.04],
        [0.07, 0.05, 0.05, 0.83],
    ], dtype=np.float64)
    # This is the emission matrix, invert for separation
    sep_old = np.linalg.inv(DEFAULT_SPEC_MATRIX)
    evaluate_matrix(train_records, sep_old, "Old matrix (train)")
    evaluate_matrix(test_records, sep_old, "Old matrix (test)")

    # Print best result
    print("\n\n=== SAVE MATRIX ===")
    print("# Optimized separation matrix (use as-is, no inversion needed):")
    print("SPEC_SEPARATION_MATRIX = np.array([")
    for i in range(4):
        row = ", ".join(f"{sep_matrix[i,j]:8.4f}" for j in range(4))
        print(f"    [{row}],  # {CH_NAMES[i]}")
    print("], dtype=np.float64)")


if __name__ == '__main__':
    main()
