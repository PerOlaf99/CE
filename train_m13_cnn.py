"""Train CNN on raw RSD signals with M13 reference labels.
Uses global z-score normalization (preserves inter-channel ratios).
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
from m13_reference import align_to_reference
from scipy.signal import savgol_filter

DATA_DIR = 'MB1000_M13_DT'

def preprocess(ch):
    """Savgol smoothing + rolling min baseline correction."""
    ch_sm = np.zeros_like(ch)
    for c in range(4):
        ch_sm[:, c] = savgol_filter(ch[:, c], 5, 2)
    bl = np.zeros_like(ch_sm)
    half = 50
    for i in range(len(ch_sm)):
        lo = max(0, i - half)
        hi = min(len(ch_sm), i + half)
        bl[i] = ch_sm[lo:hi].min(axis=0)
    return np.maximum(ch_sm - bl, 0)

def extract_training(wells, window=15):
    X_list, y_list = [], []
    for well in wells:
        df = parse_rsd(os.path.join(DATA_DIR, f'{well}.rsd'))
        ch = preprocess(df[['Channel1','Channel2','Channel3','Channel4']].values.astype(np.float64))
        esd = parse_esd(os.path.join(DATA_DIR, f'{DATA_DIR}_Cp312_MD1', f'{well}.esd'))
        pp = esd.get('peak_positions')
        if pp is None: continue
        seq = ''.join(c for c in esd.get('sequence','') if c in 'ACGTNacgtn').upper()
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

def global_norm(X):
    m = X.mean(axis=(1,), keepdims=True)
    s = X.std(axis=(1,), keepdims=True) + 1e-8
    return ((X - m) / s).astype(np.float32)

all_wells = sorted([f.replace('.rsd','') for f in os.listdir(DATA_DIR) if f.endswith('.rsd')])
rng = np.random.RandomState(42); rng.shuffle(all_wells)
train_wells = all_wells[:72]; val_wells = all_wells[72:84]; test_wells = all_wells[84:96]

print("Extracting training data...")
X_train, y_train = extract_training(train_wells)
X_val, y_val = extract_training(val_wells)
X_test, y_test = extract_training(test_wells)
print(f"Train: {len(y_train)}  Val: {len(y_val)}  Test: {len(y_test)}")
for name, y in [('Train', y_train), ('Val', y_val), ('Test', y_test)]:
    dist = np.bincount(y, minlength=4)
    print(f'  {name}: A={dist[0]} C={dist[1]} G={dist[2]} T={dist[3]}')

X_train_n = global_norm(X_train)
X_val_n = global_norm(X_val)
X_test_n = global_norm(X_test)

def build_cnn(window=31):
    inputs = keras.Input(shape=(window, 4))
    x = layers.Conv1D(64, 7, padding='same')(inputs)
    x = layers.BatchNormalization()(x); x = layers.ReLU()(x); x = layers.MaxPool1D(2)(x)
    x = layers.Conv1D(128, 5, padding='same')(x)
    x = layers.BatchNormalization()(x); x = layers.ReLU()(x); x = layers.MaxPool1D(2)(x)
    x = layers.Conv1D(256, 3, padding='same')(x)
    x = layers.BatchNormalization()(x); x = layers.ReLU()(x)
    x = layers.Conv1D(256, 3, padding='same')(x)
    x = layers.BatchNormalization()(x); x = layers.ReLU()(x)
    x = layers.GlobalAveragePooling1D()(x)
    x = layers.Dense(128)(x); x = layers.ReLU()(x); x = layers.Dropout(0.4)(x)
    x = layers.Dense(64)(x); x = layers.ReLU()(x); x = layers.Dropout(0.3)(x)
    outputs = layers.Dense(4, activation='softmax')(x)
    model = keras.Model(inputs, outputs)
    model.compile(optimizer=keras.optimizers.Adam(3e-4),
                  loss='sparse_categorical_crossentropy', metrics=['accuracy'])
    return model

model = build_cnn(31)
model.summary()

classes = np.bincount(y_train, minlength=4)
total = len(y_train)
cw = {i: total/(4*c) if c>0 else 0. for i,c in enumerate(classes)}
print(f"Class weights: {cw}")

callbacks = [
    keras.callbacks.EarlyStopping(monitor='val_accuracy', patience=30, restore_best_weights=True),
    keras.callbacks.ReduceLROnPlateau(monitor='val_loss', factor=0.5, patience=10, min_lr=1e-6),
]

print("\nTraining...")
hist = model.fit(X_train_n, y_train, validation_data=(X_val_n, y_val),
                 epochs=300, batch_size=64, class_weight=cw, callbacks=callbacks, verbose=2)

test_acc = model.evaluate(X_test_n, y_test, verbose=0)[1]
print(f"\nTest accuracy: {test_acc:.4f}")

# Per-class
y_pred = model.predict(X_test_n, verbose=0)
pred_class = y_pred.argmax(axis=1)
for i, lbl in enumerate(['A','C','G','T']):
    m = y_test == i
    if m.sum() > 0:
        print(f"  {lbl}: {(pred_class[m]==i).mean():.3f} ({m.sum()})")

# Full sequence evaluation
print("\nFull sequence on test wells:")
for well in test_wells:
    df = parse_rsd(os.path.join(DATA_DIR, f'{well}.rsd'))
    ch = preprocess(df[['Channel1','Channel2','Channel3','Channel4']].values.astype(np.float64))
    esd = parse_esd(os.path.join(DATA_DIR, f'{DATA_DIR}_Cp312_MD1', f'{well}.esd'))
    pp = esd.get('peak_positions')
    X_w, valid = [], []
    for p in pp:
        p = int(p)
        if p >= 15 and p < len(ch) - 15:
            X_w.append(ch[p-15:p+16]); valid.append(p)
    if X_w:
        X_w = global_norm(np.array(X_w, dtype=np.float32))
        preds = model.predict(X_w, verbose=0)
        seq = ''.join('ACGT'[preds[i].argmax()] for i in np.argsort(valid))
        aln = align_to_reference(seq) if len(seq) >= 50 else {'identity': 0}
        esd_seq = ''.join(c for c in esd.get('sequence','') if c in 'ACGTNacgtn').upper()
        ealn = align_to_reference(esd_seq) if esd_seq else {'identity': 0}
        print(f"  {well}: CNN={aln['identity']:.4f}  ESD={ealn['identity']:.4f}")

model.save('base_caller_model_m13.keras')
print("\nSaved!")
