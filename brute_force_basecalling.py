#!/usr/bin/env python3
"""Brute-force ML base calling experiments: test many architectures, window sizes,
data sources, and training strategies to maximize accuracy vs M13 reference.

Approaches tested:
  1. CNN with various window sizes (15, 31, 51, 101)
  2. CNN with various depths/widths
  3. LSTM / Bidirectional LSTM
  4. Training on consensus of all 6 callers
  5. Training on M13 reference as ground truth (via alignment)
  6. Per-scan brute-force with run-length decoding
  7. Ensemble across all 6 ESD callers
  8. Spectral separation + simple peak picking baseline
"""
import os, sys, warnings, argparse, json, time
import numpy as np
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
warnings.filterwarnings('ignore')
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

BASE_DIR = os.path.dirname(__file__)
sys.path.insert(0, BASE_DIR)

from extract_training_data import parse_rsd, parse_esd
from peak_detector import PeakDetector
from m13_reference import M13_REFERENCE, align_to_reference
from basecaller import basecall_ml_scan, basecall_cimarron, basecall, _load_ml_model

VARIANTS = ['Cp312', 'Cp312_a', 'Cp312_es', 'Cp1_530', 'Cp1_530_sl_ph', 'MD']
LABELS = ['A', 'C', 'G', 'T', 'N']
CH_NAMES = ['Channel1', 'Channel2', 'Channel3', 'Channel4']

# ============================================================
# DATA LOADING
# ============================================================

def load_npz_data(path):
    """Load training data from .npz file."""
    d = np.load(path, allow_pickle=True)
    return d['X'], d['y'], d.get('quality', np.ones(len(d['y'])) * 30)

def load_well(well, base_dir):
    """Load a single well's RSD data."""
    rsd_path = os.path.join(base_dir, f"{well}.rsd")
    if not os.path.exists(rsd_path):
        return None
    return parse_rsd(rsd_path)

def load_m13_training_data(base_dir, data_subdir='MB1000_M13_DT',
                           window=15, quality_min=20,
                           use_reference=False, max_wells=None):
    """Build training set by aligning ESD calls (or M13 ref) to scan positions.
    
    When use_reference=True, uses Smith-Waterman alignment to map M13 reference
    positions to each well's trace, giving perfect ground truth labels.
    """
    wells = sorted([f.replace('.rsd', '') for f in os.listdir(os.path.join(base_dir, data_subdir))
                    if f.endswith('.rsd')])
    if max_wells:
        wells = wells[:max_wells]
    
    all_X, all_y, all_pos, all_qual = [], [], [], []
    base_map = {'A': 0, 'C': 1, 'G': 2, 'T': 3, 'N': 4}
    
    for well in wells:
        df = load_well(well, os.path.join(base_dir, data_subdir))
        if df is None:
            continue
        ch = df[CH_NAMES].values
        n_scans = len(ch)
        
        if use_reference:
            # Get ESD sequence from Cp312 (most reliable caller), align to M13
            esd_dir = f"{data_subdir}_Cp312_MD1"
            esd_path = os.path.join(base_dir, data_subdir, esd_dir, f"{well}.esd")
            if not os.path.exists(esd_path):
                continue
            try:
                esd = parse_esd(esd_path)
            except:
                continue
            seq = esd.get('sequence', '')
            positions = esd.get('peak_positions')
            if positions is None:
                positions = esd.get('bases_positions')
            quality = esd.get('quality_scores')
            if not seq or positions is None:
                continue
            
            # Align ESD sequence to M13 reference
            seq_clean = ''.join(c for c in seq if c in 'ACGT').upper()
            if len(seq_clean) < 50:
                continue
            align = align_to_reference(seq_clean)
            if align['identity'] < 0.5:
                continue
            
            # Build position mapping
            q_aligned = align['query_aligned']
            r_aligned = align['ref_aligned']
            ref_start = align['ref_start']
            
            # Walk through alignment to map ESD positions to M13 base calls
            esd_idx = 0
            for ai, (qb, rb) in enumerate(zip(q_aligned, r_aligned)):
                if qb == '-' or rb == '-':
                    continue
                # This ESD base at esd_idx maps to M13 base rb
                ref_base = rb  # From M13 reference
                # Get the scan position from ESD
                epos = positions[esd_idx]
                if epos >= window and epos < n_scans - window:
                    win = ch[epos - window:epos + window + 1]
                    all_X.append(win)
                    all_y.append(base_map.get(ref_base, 4))
                    all_pos.append(epos)
                    all_qual.append(quality[esd_idx] if quality is not None else 30)
                esd_idx += 1
        else:
            # Use ESD positions + bases directly (existing approach)
            for variant in VARIANTS:
                esd_dir = f"{data_subdir}_{variant}_MD1"
                esd_path = os.path.join(base_dir, data_subdir, esd_dir, f"{well}.esd")
                if not os.path.exists(esd_path):
                    continue
                try:
                    esd = parse_esd(esd_path)
                except:
                    continue
                seq = esd.get('sequence', '')
                positions = esd.get('peak_positions') or esd.get('bases_positions')
                quality = esd.get('quality_scores')
                if not seq or positions is None:
                    continue
                
                n_bases = min(len(seq), len(positions))
                if quality is not None:
                    n_bases = min(n_bases, len(quality))
                
                for i in range(n_bases):
                    if quality is not None and quality[i] < quality_min:
                        continue
                    pos = int(positions[i])
                    base = seq[i].upper()
                    if base not in base_map:
                        continue
                    if pos < window or pos >= n_scans - window:
                        continue
                    win = ch[pos - window:pos + window + 1]
                    all_X.append(win)
                    all_y.append(base_map[base])
                    all_pos.append(pos)
                    all_qual.append(quality[i] if quality is not None else 30)
    
    if not all_X:
        return None, None
    
    X = np.array(all_X, dtype=np.float32)
    y = np.array(all_y, dtype=np.uint8)
    print(f"  Loaded {len(X)} windows from {len(wells)} wells "
          f"({'M13 reference' if use_reference else 'ESD labels'})")
    return X, y


# ============================================================
# MODEL ARCHITECTURES
# ============================================================

def build_cnn(window=31, width=64, depth=4, dropout=0.4, use_leaky=False):
    """Vanilla 1D CNN - configurable depth and width."""
    act = layers.LeakyReLU(0.1) if use_leaky else layers.ReLU()
    inputs = keras.Input(shape=(window, 4), name='signal')
    x = inputs
    
    filter_sizes = [width * min(2**i, 8) for i in range(depth)]
    kernel_sizes = [7 if i == 0 else (5 if i == 1 else 3) for i in range(depth)]
    
    for i in range(depth):
        x = layers.Conv1D(filter_sizes[i], kernel_sizes[i], padding='same')(x)
        x = layers.BatchNormalization()(x)
        x = act.__class__.from_config(act.get_config()) if use_leaky else layers.ReLU()(x)
        if i < 2:
            x = layers.MaxPool1D(2)(x)
    
    x = layers.GlobalAveragePooling1D()(x)
    x = layers.Dense(128)(x)
    x = act.__class__.from_config(act.get_config()) if use_leaky else layers.ReLU()(x)
    x = layers.Dropout(dropout)(x)
    x = layers.Dense(64)(x)
    x = act.__class__.from_config(act.get_config()) if use_leaky else layers.ReLU()(x)
    x = layers.Dropout(max(0.2, dropout - 0.1))(x)
    outputs = layers.Dense(5, activation='softmax', name='base')(x)
    
    model = keras.Model(inputs, outputs)
    model.compile(
        optimizer=keras.optimizers.Adam(3e-4),
        loss='sparse_categorical_crossentropy',
        metrics=['accuracy']
    )
    return model


def build_lstm(window=31, lstm_units=64, bidirectional=True):
    """LSTM / BiLSTM base caller."""
    inputs = keras.Input(shape=(window, 4), name='signal')
    x = layers.Conv1D(32, 5, padding='same')(inputs)
    x = layers.BatchNormalization()(x)
    x = layers.LeakyReLU(0.1)(x)
    
    if bidirectional:
        x = layers.Bidirectional(layers.LSTM(lstm_units, return_sequences=True))(x)
        x = layers.Bidirectional(layers.LSTM(lstm_units // 2))(x)
    else:
        x = layers.LSTM(lstm_units, return_sequences=True)(x)
        x = layers.LSTM(lstm_units // 2)(x)
    
    x = layers.Dropout(0.3)(x)
    x = layers.Dense(64, activation='relu')(x)
    x = layers.Dropout(0.2)(x)
    outputs = layers.Dense(5, activation='softmax', name='base')(x)
    
    model = keras.Model(inputs, outputs)
    model.compile(
        optimizer=keras.optimizers.Adam(3e-4),
        loss='sparse_categorical_crossentropy',
        metrics=['accuracy']
    )
    return model


def build_resnet(window=31):
    """ResNet-style 1D CNN with residual connections."""
    inputs = keras.Input(shape=(window, 4), name='signal')
    
    def conv_bn_relu(x, filters, kernel, stride=1):
        x = layers.Conv1D(filters, kernel, strides=stride, padding='same')(x)
        x = layers.BatchNormalization()(x)
        return layers.ReLU()(x)
    
    def residual_block(x, filters, kernel=3):
        shortcut = x
        y = conv_bn_relu(x, filters, kernel)
        y = conv_bn_relu(y, filters, kernel)
        if shortcut.shape[-1] != filters:
            shortcut = layers.Conv1D(filters, 1, padding='same')(shortcut)
        return layers.Add()([shortcut, y])
    
    x = conv_bn_relu(inputs, 64, 7)
    x = layers.MaxPool1D(2)(x)
    x = residual_block(x, 64)
    x = residual_block(x, 64)
    x = residual_block(x, 128)
    x = layers.MaxPool1D(2)(x)
    x = residual_block(x, 128)
    x = residual_block(x, 256)
    x = layers.GlobalAveragePooling1D()(x)
    x = layers.Dense(128, activation='relu')(x)
    x = layers.Dropout(0.4)(x)
    outputs = layers.Dense(5, activation='softmax')(x)
    
    model = keras.Model(inputs, outputs)
    model.compile(
        optimizer=keras.optimizers.Adam(3e-4),
        loss='sparse_categorical_crossentropy',
        metrics=['accuracy']
    )
    return model


def build_tiny_transformer(window=31, d_model=32, nhead=4, num_layers=2):
    """Minimal transformer encoder for base calling."""
    inputs = keras.Input(shape=(window, 4), name='signal')
    x = layers.Dense(d_model)(inputs)
    x = layers.PositionalEncoding()(x) if hasattr(layers, 'PositionalEncoding') else x
    x = layers.Add()([x, layers.Dense(d_model)(inputs)])
    
    for _ in range(num_layers):
        attn = layers.MultiHeadAttention(num_heads=nhead, key_dim=d_model // nhead)(x, x)
        x = layers.Add()([x, attn])
        x = layers.LayerNormalization()(x)
        ffn = layers.Dense(d_model * 2, activation='relu')(x)
        ffn = layers.Dense(d_model)(ffn)
        x = layers.Add()([x, ffn])
        x = layers.LayerNormalization()(x)
    
    x = layers.GlobalAveragePooling1D()(x)
    x = layers.Dense(64, activation='relu')(x)
    x = layers.Dropout(0.3)(x)
    outputs = layers.Dense(5, activation='softmax')(x)
    
    model = keras.Model(inputs, outputs)
    model.compile(
        optimizer=keras.optimizers.Adam(3e-4),
        loss='sparse_categorical_crossentropy',
        metrics=['accuracy']
    )
    return model


# ============================================================
# TRAINING HELPERS
# ============================================================

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


def normalize(X):
    m = X.mean(axis=(1,), keepdims=True)
    s = X.std(axis=(1,), keepdims=True) + 1e-8
    return ((X - m) / s).astype(np.float32)


def stratified_split(y, test_pct=0.1, val_pct=0.1, seed=42):
    n_classes = int(y.max()) + 1
    rng = np.random.RandomState(seed)
    indices = np.arange(len(y))
    train_idx, val_idx, test_idx = [], [], []
    for cls in range(n_classes):
        cls_idx = indices[y == cls]
        if len(cls_idx) == 0:
            continue
        rng.shuffle(cls_idx)
        n = len(cls_idx)
        n_val = int(n * val_pct)
        n_test = int(n * test_pct)
        n_train = n - n_val - n_test
        train_idx.append(cls_idx[:n_train])
        val_idx.append(cls_idx[n_train:n_train + n_val])
        test_idx.append(cls_idx[n_train + n_val:])
    return (np.concatenate(train_idx), np.concatenate(val_idx),
            np.concatenate(test_idx))


def train_model(model, X_train, y_train, X_val, y_val,
                batch_size=128, epochs=200, max_shift=8, class_weight=None):
    train_gen = ShiftAugment(X_train, y_train, batch_size=batch_size, max_shift=max_shift)
    X_val_norm = normalize(X_val)
    
    callbacks = [
        keras.callbacks.EarlyStopping(
            monitor='val_accuracy', patience=25, restore_best_weights=True),
        keras.callbacks.ReduceLROnPlateau(
            monitor='val_loss', factor=0.5, patience=5, min_lr=1e-6),
    ]
    
    history = model.fit(
        train_gen,
        validation_data=(X_val_norm, y_val),
        epochs=epochs,
        class_weight=class_weight,
        callbacks=callbacks,
        verbose=0,
    )
    return history


def compute_confidence_curve(model, X_test, y_test):
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
            'threshold': t, 'accuracy': acc,
            'coverage': mask.mean(), 'n_calls': int(mask.sum()),
        })
    
    scores = [r['accuracy'] * np.sqrt(r['coverage']) for r in results]
    best_idx = np.argmax(scores)
    best = results[best_idx]
    return results, best


# ============================================================
# EVALUATION AGAINST M13 REFERENCE
# ============================================================

def evaluate_model_on_well(model, df, use_scan=False, min_confidence=0.5,
                           min_spacing=3, window=15):
    """Evaluate model on a single well, returning sequence + alignment info."""
    ch = df[CH_NAMES].values
    n_scans = len(ch)
    
    if use_scan:
        # Per-scan brute force
        if n_scans < window * 2 + 1:
            return None
        valid_positions = np.arange(window, n_scans - window)
        X = np.array([ch[p - window:p + window + 1] for p in valid_positions], dtype=np.float32)
        X = normalize(X)
        preds = model.predict(X, verbose=0)
        classes = preds.argmax(axis=1)
        confs = preds.max(axis=1)
        
        is_base = (classes < 4) & (confs >= min_confidence)
        bases, positions = [], []
        i = 0
        while i < len(valid_positions):
            if not is_base[i]:
                i += 1
                continue
            base_cls = classes[i]
            run_start = i
            j = i
            while j < len(valid_positions) and is_base[j] and classes[j] == base_cls:
                j += 1
            run_end = j - 1
            run_confs = confs[run_start:run_end + 1]
            best_idx = run_start + run_confs.argmax()
            best_pos = valid_positions[best_idx]
            bases.append(LABELS[base_cls])
            positions.append(float(best_pos))
            next_scan = best_pos + min_spacing
            i = np.searchsorted(valid_positions, next_scan)
    else:
        # Peak-based: detect peaks first, then classify each
        detector = PeakDetector()
        peaks, peak_channels = detector.detect(df[CH_NAMES].values)
        if len(peaks) == 0:
            return None
        
        sorted_idx = np.argsort(peaks)
        peaks_sorted = peaks[sorted_idx]
        
        bases, positions = [], []
        for peak_idx in peaks_sorted:
            if peak_idx < window or peak_idx >= n_scans - window:
                continue
            win = ch[peak_idx - window:peak_idx + window + 1]
            win_norm = normalize(win[np.newaxis, ...])
            pred = model.predict(win_norm, verbose=0)
            cls = pred.argmax(axis=1)[0]
            conf = pred.max(axis=1)[0]
            base = LABELS[cls] if cls < 4 and conf >= min_confidence else 'N'
            if base != 'N':
                bases.append(base)
                positions.append(float(peak_idx))
    
    if len(bases) < 10:
        return None
    
    seq = ''.join(bases)
    align = align_to_reference(seq)
    return {'sequence': seq, 'alignment': align, 'n_bases': len(bases)}


def evaluate_on_plate(model, wells, base_dir, data_subdir,
                      use_scan=False, min_confidence=0.5,
                      min_spacing=3, window=15, max_wells=None):
    """Evaluate model on all wells in a plate."""
    if max_wells:
        wells = wells[:max_wells]
    
    results = []
    for well in wells:
        df = load_well(well, os.path.join(base_dir, data_subdir))
        if df is None:
            continue
        r = evaluate_model_on_well(model, df, use_scan, min_confidence, min_spacing, window)
        if r and r['alignment'] and r['alignment']['identity'] > 0:
            results.append({
                'well': well,
                'identity': r['alignment']['identity'],
                'matches': r['alignment']['matches'],
                'aligned': r['alignment']['aligned_length'],
                'n_bases': r['n_bases'],
            })
    
    if not results:
        return {'n_wells': 0, 'mean_identity': 0, 'wells': []}
    
    identities = [r['identity'] for r in results]
    return {
        'n_wells': len(results),
        'mean_identity': float(np.mean(identities)),
        'median_identity': float(np.median(identities)),
        'min_identity': float(np.min(identities)),
        'max_identity': float(np.max(identities)),
        'std_identity': float(np.std(identities)),
        'wells': results,
    }


# ============================================================
# BASELINE COMPARISON METHODS
# ============================================================

def evaluate_esd_baseline(wells, base_dir, data_subdir, variant='Cp312'):
    """Evaluate an existing ESD caller against M13 reference."""
    results = []
    for well in wells:
        esd_dir = f"{data_subdir}_{variant}_MD1"
        esd_path = os.path.join(base_dir, data_subdir, esd_dir, f"{well}.esd")
        if not os.path.exists(esd_path):
            continue
        try:
            esd = parse_esd(esd_path)
        except:
            continue
        seq = esd.get('sequence', '')
        seq_clean = ''.join(c for c in seq if c in 'ACGTN').upper()
        if len(seq_clean) < 50:
            continue
        align = align_to_reference(seq_clean)
        if align['identity'] > 0:
            results.append({
                'well': well,
                'identity': align['identity'],
                'matches': align['matches'],
                'aligned': align['aligned_length'],
                'n_bases': len(seq_clean),
            })
    
    if not results:
        return {'n_wells': 0, 'mean_identity': 0}
    
    identities = [r['identity'] for r in results]
    return {
        'n_wells': len(results),
        'mean_identity': float(np.mean(identities)),
        'median_identity': float(np.median(identities)),
        'std_identity': float(np.std(identities)),
        'wells': results,
    }


# ============================================================
# MAIN EXPERIMENT
# ============================================================

def run_experiment(config, X_train, y_train, X_val, y_val, wells, base_dir, data_subdir):
    """Run a single experiment configuration and return results."""
    print(f"\n{'='*60}")
    print(f"  Experiment: {config['name']}")
    print(f"{'='*60}")
    
    # Build model
    arch = config.get('architecture', 'cnn')
    window = config.get('window', 31)
    
    if arch == 'cnn':
        model = build_cnn(window=window, width=config.get('width', 64),
                          depth=config.get('depth', 4),
                          dropout=config.get('dropout', 0.4),
                          use_leaky=config.get('use_leaky', False))
    elif arch == 'lstm':
        model = build_lstm(window=window, lstm_units=config.get('lstm_units', 64),
                           bidirectional=config.get('bidirectional', True))
    elif arch == 'resnet':
        model = build_resnet(window=window)
    elif arch == 'transformer':
        model = build_tiny_transformer(window=window)
    else:
        print(f"  Unknown architecture: {arch}")
        return None
    
    # Class weights
    classes = np.bincount(y_train, minlength=5)
    total = len(y_train)
    n_cls = max(1, (classes > 0).sum())
    class_weight = {i: total / (n_cls * c) if c > 0 else 0.0 for i, c in enumerate(classes)}
    
    # Train
    t0 = time.time()
    train_model(model, X_train, y_train, X_val, y_val,
                batch_size=config.get('batch_size', 128),
                epochs=config.get('epochs', 150),
                max_shift=config.get('max_shift', 8),
                class_weight=class_weight)
    train_time = time.time() - t0
    
    # Evaluate on test set
    if X_val is not None and len(X_val) > 0:
        X_val_norm = normalize(X_val)
        val_loss, val_acc = model.evaluate(X_val_norm, y_val, verbose=0)
    else:
        val_acc = 0
    
    # Confidence curve
    if X_val is not None and len(X_val) > 0:
        curve, best = compute_confidence_curve(model, X_val, y_val)
        opt_threshold = best['threshold']
        opt_acc = best['accuracy']
    else:
        opt_threshold = 0.5
        opt_acc = 0
    
    # Evaluate on real wells vs M13 reference
    eval_results = evaluate_on_plate(
        model, wells, base_dir, data_subdir,
        use_scan=config.get('use_scan', False),
        min_confidence=config.get('min_confidence', 0.5),
        min_spacing=config.get('min_spacing', 3),
        window=window,
        max_wells=config.get('eval_wells', None),
    )
    
    result = {
        'config': config,
        'val_accuracy': float(val_acc),
        'opt_threshold': float(opt_threshold),
        'opt_accuracy': float(opt_acc),
        'train_time': round(train_time, 1),
        'eval': eval_results,
    }
    
    print(f"  Val accuracy: {val_acc:.4f}")
    print(f"  Opt threshold: {opt_threshold:.2f} (acc={opt_acc:.4f})")
    print(f"  Plate eval: {eval_results['n_wells']} wells, "
          f"mean identity={eval_results['mean_identity']:.4f}")
    print(f"  Train time: {train_time:.1f}s")
    
    return result


def main():
    parser = argparse.ArgumentParser(description='Brute-force ML base calling experiments')
    parser.add_argument('--base-dir', default=BASE_DIR,
                        help='Base directory (default: script dir)')
    parser.add_argument('--data-dir', default=None,
                        help='Data subdirectory (default: MB1000_M13_DT)')
    parser.add_argument('--output', default='experiment_results.json',
                        help='Output JSON file for results')
    parser.add_argument('--max-wells', type=int, default=24,
                        help='Max wells for training (default 24)')
    parser.add_argument('--eval-wells', type=int, default=12,
                        help='Max wells for evaluation (default 12)')
    parser.add_argument('--quick', action='store_true',
                        help='Quick mode: fewer epochs, fewer experiments')
    args = parser.parse_args()
    
    data_subdir = args.data_dir or 'MB1000_M13_DT'
    base_dir = args.base_dir
    data_dir = os.path.join(base_dir, data_subdir)
    
    if not os.path.exists(data_dir):
        print(f"Data directory not found: {data_dir}")
        # Try the USB path
        alt = '/media/tv/78B0C7DE1FA7081C/electropherogram'
        alt_data = os.path.join(alt, data_subdir)
        if os.path.exists(alt_data):
            base_dir = alt
            data_dir = alt_data
            print(f"Using alternative path: {base_dir}")
        else:
            print(f"Also not found: {alt_data}")
            sys.exit(1)
    
    # Get wells
    wells = sorted([f.replace('.rsd', '') for f in os.listdir(data_dir)
                    if f.endswith('.rsd')])
    print(f"Found {len(wells)} wells in {data_dir}")
    
    # Load training data (combined ESD labels)
    print("\nLoading training data (combined ESD labels)...")
    X, y = load_m13_training_data(base_dir, data_subdir, window=15,
                                  use_reference=False, max_wells=args.max_wells)
    
    if X is None:
        print("Failed to load training data!")
        sys.exit(1)
    
    # Also load M13-reference-based training data
    print("\nLoading training data (M13 reference labels)...")
    X_ref, y_ref = load_m13_training_data(base_dir, data_subdir, window=15,
                                          use_reference=True, max_wells=args.max_wells)
    
    # Split
    _, val_idx, test_idx = stratified_split(y, test_pct=0.1, val_pct=0.1)
    X_val, y_val = X[val_idx], y[val_idx]
    X_test, y_test = X[test_idx], y[test_idx]
    
    if X_ref is not None:
        _, val_idx_r, _ = stratified_split(y_ref, test_pct=0.1, val_pct=0.1)
        X_val_r, y_val_r = y_ref[val_idx_r], y_ref[val_idx_r]  # Note: bug, but val only
        X_val_r, y_val_r = X_ref[val_idx_r], y_ref[val_idx_r]
    
    # 1. Evaluate ESd baselines first
    print(f"\n{'='*60}")
    print("  ESD BASELINES")
    print(f"{'='*60}")
    baselines = {}
    for variant in VARIANTS:
        r = evaluate_esd_baseline(wells, base_dir, data_subdir, variant)
        baselines[variant] = r
        print(f"  {variant}: {r['n_wells']} wells, mean id={r['mean_identity']:.4f}")
    
    # Define experiments
    experiments = []
    
    # Current standard CNN (window=31, similar to existing base_caller_model.keras)
    experiments.append({
        'name': 'CNN_win31_std',
        'architecture': 'cnn',
        'window': 31,
        'width': 64,
        'depth': 4,
        'dropout': 0.4,
        'use_leaky': False,
        'use_scan': False,
        'min_confidence': 0.5,
    })
    
    # CNN with LeakyReLU (like retrain_model.py)
    experiments.append({
        'name': 'CNN_win31_leaky',
        'architecture': 'cnn',
        'window': 31,
        'width': 64,
        'depth': 4,
        'dropout': 0.4,
        'use_leaky': True,
        'use_scan': False,
        'min_confidence': 0.5,
    })
    
    # Wider CNN
    experiments.append({
        'name': 'CNN_win31_wide',
        'architecture': 'cnn',
        'window': 31,
        'width': 128,
        'depth': 4,
        'dropout': 0.4,
        'use_leaky': True,
        'use_scan': False,
        'min_confidence': 0.5,
    })
    
    # Deeper CNN
    experiments.append({
        'name': 'CNN_win31_deep',
        'architecture': 'cnn',
        'window': 31,
        'width': 64,
        'depth': 6,
        'dropout': 0.5,
        'use_leaky': True,
        'use_scan': False,
        'min_confidence': 0.5,
    })
    
    # Different window sizes
    for win in [15, 51, 101]:
        experiments.append({
            'name': f'CNN_win{win}_leaky',
            'architecture': 'cnn',
            'window': win,
            'width': 64,
            'depth': 4,
            'dropout': 0.4,
            'use_leaky': True,
            'use_scan': False,
            'min_confidence': 0.5,
        })
    
    # LSTM
    experiments.append({
        'name': 'BiLSTM_win31',
        'architecture': 'lstm',
        'window': 31,
        'lstm_units': 64,
        'bidirectional': True,
        'use_scan': False,
        'min_confidence': 0.5,
    })
    
    experiments.append({
        'name': 'LSTM_win31',
        'architecture': 'lstm',
        'window': 31,
        'lstm_units': 64,
        'bidirectional': False,
        'use_scan': False,
        'min_confidence': 0.5,
    })
    
    # ResNet
    experiments.append({
        'name': 'ResNet_win31',
        'architecture': 'resnet',
        'window': 31,
        'use_scan': False,
        'min_confidence': 0.5,
    })
    
    # Per-scan brute force with run-length decoding (best model)
    experiments.append({
        'name': 'CNN_win31_scan',
        'architecture': 'cnn',
        'window': 31,
        'width': 64,
        'depth': 4,
        'dropout': 0.4,
        'use_leaky': True,
        'use_scan': True,
        'min_confidence': 0.3,
        'min_spacing': 3,
    })
    
    # Per-scan with higher confidence
    experiments.append({
        'name': 'CNN_win31_scan_highconf',
        'architecture': 'cnn',
        'window': 31,
        'width': 64,
        'depth': 4,
        'dropout': 0.4,
        'use_leaky': True,
        'use_scan': True,
        'min_confidence': 0.6,
        'min_spacing': 3,
    })
    
    # Train on M13 reference instead of ESD labels
    if X_ref is not None:
        _, val_idx_r, test_idx_r = stratified_split(y_ref, test_pct=0.1, val_pct=0.1)
        X_train_r = np.delete(X_ref, np.concatenate([val_idx_r, test_idx_r]), axis=0)
        y_train_r = np.delete(y_ref, np.concatenate([val_idx_r, test_idx_r]), axis=0)
        X_val_r, y_val_r = X_ref[val_idx_r], y_ref[val_idx_r]
        
        experiments.append({
            'name': 'CNN_win31_M13ref',
            'architecture': 'cnn',
            'window': 31,
            'width': 64,
            'depth': 4,
            'dropout': 0.4,
            'use_leaky': True,
            'use_scan': False,
            'min_confidence': 0.5,
            '_X_train': X_train_r,
            '_y_train': y_train_r,
            '_X_val': X_val_r,
            '_y_val': y_val_r,
        })
    
    # Quick mode: fewer experiments
    if args.quick:
        experiments = [e for e in experiments if 'win31' in e['name']][:4]
        for e in experiments:
            e['epochs'] = 50
    
    # Run all experiments
    results = {'baselines': baselines, 'experiments': []}
    
    for config in experiments:
        # Use specific train/val data if provided, otherwise use default
        if '_X_train' in config:
            X_tr, y_tr = config.pop('_X_train'), config.pop('_y_train')
            X_va, y_va = config.pop('_X_val'), config.pop('_y_val')
        else:
            train_idx = np.setdiff1d(np.arange(len(y)), np.concatenate([val_idx, test_idx]))
            X_tr, y_tr = X[train_idx], y[train_idx]
            X_va, y_va = X_val, y_val
        
        # Need to reload data with correct window size if different
        window = config.get('window', 31)
        if window != 15 and '_X_train' not in config:
            print(f"\n  Reloading data for window={window}...")
            X_w, y_w = load_m13_training_data(base_dir, data_subdir, window=window // 2,
                                              use_reference=False, max_wells=args.max_wells)
            if X_w is not None:
                _, val_idx_w, test_idx_w = stratified_split(y_w, test_pct=0.1, val_pct=0.1)
                train_idx_w = np.setdiff1d(np.arange(len(y_w)),
                                           np.concatenate([val_idx_w, test_idx_w]))
                X_tr, y_tr = X_w[train_idx_w], y_w[train_idx_w]
                X_va, y_va = X_w[val_idx_w], y_w[val_idx_w]
        
        result = run_experiment(config, X_tr, y_tr, X_va, y_va,
                                wells, base_dir, data_subdir)
        if result:
            results['experiments'].append(result)
        
        # Save intermediate results
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2, default=str)
    
    # Print summary
    print(f"\n{'='*60}")
    print("  SUMMARY")
    print(f"{'='*60}")
    
    print("\n  Baselines (ESD callers vs M13 reference):")
    for name, r in sorted(baselines.items(), key=lambda x: -x[1]['mean_identity']):
        print(f"    {name:20s}: id={r['mean_identity']:.4f} ({r['n_wells']} wells)")
    
    print("\n  ML Experiments (vs M13 reference):")
    sorted_exp = sorted(results['experiments'],
                        key=lambda x: x['eval']['mean_identity'], reverse=True)
    for r in sorted_exp:
        name = r['config']['name']
        eid = r['eval']['mean_identity']
        nw = r['eval']['n_wells']
        va = r['val_accuracy']
        print(f"    {name:30s}: plate_id={eid:.4f} ({nw} wells) val_acc={va:.4f}")
    
    print(f"\nResults saved to {args.output}")


if __name__ == '__main__':
    main()
