"""Train CNN on raw RSD signals with M13 reference labels.
Uses per-channel normalization to preserve spectral ratios.
"""
import sys, warnings, os
import numpy as np
warnings.filterwarnings('ignore')
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
sys.path.insert(0, '.')
import tensorflow as tf
tf.get_logger().setLevel('ERROR')
from tensorflow import keras
from tensorflow.keras import layers

from extract_training_data import parse_rsd, parse_esd
from m13_reference import align_to_reference, M13_REFERENCE
from scipy.ndimage import savgol_filter

DATA_DIR = 'MB1000_M13_DT'

def preprocess(ch, window_sg=5, order_sg=2):
    """Savgol smoothing + per-channel baseline correction."""
    ch_sm = np.zeros_like(ch)
    for c in range(4):
        # Smooth
        ch_sm[:, c] = savgol_filter(ch[:, c], window_sg, order_sg)
    # Baseline: rolling min over 100 scans
    bl = np.zeros_like(ch_sm)
    half = 50
    for i in range(len(ch_sm)):
        lo = max(0, i - half)
        hi = min(len(ch_sm), i + half)
        bl[i] = ch_sm[lo:hi].min(axis=0)
    ch_bc = np.maximum(ch_sm - bl, 0)
    return ch_bc

def extract_training(wells, window=15, smooth=True, overwrite_positions=None):
    X_list, y_list = [], []
    for well in wells:
        df = parse_rsd(os.path.join(DATA_DIR, f'{well}.rsd'))
        ch = df[['Channel1','Channel2','Channel3','Channel4']].values.astype(np.float64)
        if smooth:
            ch = preprocess(ch)
        else:
            # Just baseline correction
            bl = np.percentile(ch[:300], 5, axis=0)
            ch = np.maximum(ch - bl, 0)
        esd = parse_esd(os.path.join(DATA_DIR, f'{DATA_DIR}_Cp312_MD1', f'{well}.esd'))
        seq = ''.join(c for c in esd.get('sequence','') if c in 'ACGTNacgtn').upper()
        pp = esd.get('peak_positions')
        if pp is None: continue
        aln = align_to_reference(seq)
        if aln['identity'] < 0.5: continue
        q_aln, r_aln = aln['query_aligned'], aln['ref_aligned']
        esd_idx = 0
        n_scans = len(ch)
        for qb, rb in zip(q_aln, r_aln):
            if qb == '-' or rb == '-':
                if qb == '-': esd_idx += 1
                continue
            if esd_idx >= len(pp): break
            if rb in 'ACGT':
                p = int(pp[esd_idx])
                if p >= window and p < n_scans - window:
                    X_list.append(ch[p-window:p+window+1])
                    y_list.append('ACGT'.index(rb))
            esd_idx += 1
    if not X_list: return None, None
    return np.array(X_list, dtype=np.float32), np.array(y_list, dtype=np.uint8)

# Load all wells and split
all_wells = sorted([f.replace('.rsd','') for f in os.listdir(DATA_DIR) if f.endswith('.rsd')])
rng = np.random.RandomState(42)
rng.shuffle(all_wells)
train_wells = all_wells[:72]
val_wells = all_wells[72:84]
test_wells = all_wells[84:96]

print("Extracting training data (baseline-corrected, smoothed)...")
X_train, y_train = extract_training(train_wells, window=15, smooth=True)
X_val, y_val = extract_training(val_wells, window=15, smooth=True)
X_test, y_test = extract_training(test_wells, window=15, smooth=True)
print(f"Train: {len(y_train)}  Val: {len(y_val)}  Test: {len(y_test)}")

# Per-channel normalization: each channel z-scored independently
def per_channel_norm(X):
    Xn = X.copy().astype(np.float32)
    for i in range(len(Xn)):
        for c in range(4):
            mu = Xn[i, :, c].mean()
            s = Xn[i, :, c].std() + 1e-8
            Xn[i, :, c] = (Xn[i, :, c] - mu) / s
    return Xn

X_train_n = per_channel_norm(X_train)
X_val_n = per_channel_norm(X_val)
X_test_n = per_channel_norm(X_test)

# Also add raw (non-normalized) version for comparison
# Standard global z-score
def global_norm(X):
    m = X.mean(axis=(1,), keepdims=True)
    s = X.std(axis=(1,), keepdims=True) + 1e-8
    return ((X - m) / s).astype(np.float32)

X_val_g = global_norm(X_val)
X_test_g = global_norm(X_test)

# Build 4-output CNN (A/C/G/T only)
def build_cnn(window=31):
    inputs = keras.Input(shape=(window, 4))
    x = layers.Conv1D(64, 7, padding='same')(inputs)
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
    outputs = layers.Dense(4, activation='softmax')(x)
    model = keras.Model(inputs, outputs)
    model.compile(optimizer=keras.optimizers.Adam(3e-4),
                  loss='sparse_categorical_crossentropy',
                  metrics=['accuracy'])
    return model

model = build_cnn(31)
model.summary()

# Class weights
classes = np.bincount(y_train, minlength=4)
total = len(y_train)
cw = {i: total/(4*c) if c>0 else 0. for i,c in enumerate(classes)}
print(f"Class weights: {cw}")

callbacks = [
    keras.callbacks.EarlyStopping(monitor='val_accuracy', patience=25, restore_best_weights=True),
    keras.callbacks.ReduceLROnPlateau(monitor='val_loss', factor=0.5, patience=8, min_lr=1e-6),
]

print("\nTraining (per-channel norm)...")
hist = model.fit(X_train_n, y_train, validation_data=(X_val_n, y_val),
                 epochs=200, batch_size=64, class_weight=cw, callbacks=callbacks, verbose=1)

# Evaluate
test_acc = model.evaluate(X_test_n, y_test, verbose=0)[1]
print(f"\nTest accuracy (per-channel norm): {test_acc:.4f}")

# Full sequence evaluation
print("\nFull sequence identity on test wells:")
ML_LABELS = ['A', 'C', 'G', 'T']
for well in test_wells:
    df = parse_rsd(os.path.join(DATA_DIR, f'{well}.rsd'))
    ch = df[['Channel1','Channel2','Channel3','Channel4']].values.astype(np.float64)
    ch_p = preprocess(ch)
    esd = parse_esd(os.path.join(DATA_DIR, f'{DATA_DIR}_Cp312_MD1', f'{well}.esd'))
    pp = esd.get('peak_positions')
    X_w, valid = [], []
    for p in pp:
        p = int(p)
        if p >= 15 and p < len(ch_p) - 15:
            X_w.append(ch_p[p-15:p+16])
            valid.append(p)
    if X_w:
        X_w = np.array(X_w, dtype=np.float32)
        X_w_n = per_channel_norm(X_w)
        preds = model.predict(X_w_n, verbose=0)
        seq = ''.join(ML_LABELS[preds[i].argmax()] for i in np.argsort(valid))
        aln = align_to_reference(seq) if len(seq) >= 50 else {'identity': 0}
        esd_seq = ''.join(c for c in esd.get('sequence','') if c in 'ACGTNacgtn').upper()
        esd_aln = align_to_reference(esd_seq) if esd_seq else {'identity': 0}
        print(f"  {well}: CNN={aln['identity']:.4f}  ESD={esd_aln['identity']:.4f}")

model.save('base_caller_model_m13.keras')
print("\nSaved to base_caller_model_m13.keras")
