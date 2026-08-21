import os
import numpy as np
import tensorflow as tf
from tensorflow.keras import layers, models, backend as K
from tensorflow.keras.optimizers import Adam
from sklearn.model_selection import train_test_split
from utils import read_rsd, read_esd, preprocess_traces
import pickle

# ---------------------------
# 1. Load all data
# ---------------------------
raw_dir = "data/raw/"
called_dir = "data/called/"

file_list = [f for f in os.listdir(raw_dir) if f.endswith('.rsd')]
X = []  # list of trace arrays (variable length)
y = []  # list of sequences (strings)

for fname in file_list:
    base = fname.replace('.rsd', '')
    rsd_path = os.path.join(raw_dir, fname)
    esd_path = os.path.join(called_dir, base + '.esd')
    if not os.path.exists(esd_path):
        print(f"Warning: {esd_path} not found, skipping {fname}")
        continue
    # Load traces
    traces = read_rsd(rsd_path)
    # Preprocess
    trace_data = preprocess_traces(traces)  # shape (T, 4)
    # Load sequence from .esd
    seq, _ = read_esd(esd_path)
    X.append(trace_data)
    y.append(seq)

print(f"Loaded {len(X)} samples.")

# ---------------------------
# 2. Encode sequences to integer indices
# ---------------------------
char_to_idx = {'A': 0, 'C': 1, 'G': 2, 'T': 3, 'N': 4}  # N as unknown
def encode_seq(seq):
    return np.array([char_to_idx.get(ch, 4) for ch in seq], dtype=np.int32)

y_encoded = [encode_seq(seq) for seq in y]

# Train/validation split
X_train, X_val, y_train, y_val = train_test_split(X, y_encoded, test_size=0.2, random_state=42)

# ---------------------------
# 3. Build the model (BiLSTM + CTC)
# ---------------------------
def build_model(input_dim=4, num_classes=5):  # 4 bases + blank (CTC uses blank as index 0)
    # Input: (batch, time, features)
    inputs = layers.Input(shape=(None, input_dim), name='the_input')
    # BiLSTM layers
    x = layers.Bidirectional(layers.LSTM(128, return_sequences=True, dropout=0.2))(inputs)
    x = layers.Bidirectional(layers.LSTM(128, return_sequences=True, dropout=0.2))(x)
    # Dense layer for softmax output
    x = layers.Dense(num_classes + 1, activation='softmax', name='softmax')(x)  # +1 for blank
    model = models.Model(inputs=inputs, outputs=x)
    return model

model = build_model()
model.summary()

# ---------------------------
# 4. CTC loss and training
# ---------------------------
def ctc_loss(y_true, y_pred):
    # y_true: (batch, max_label_len) – padded with -1
    # y_pred: (batch, time, num_classes)
    label_length = K.sum(K.cast(y_true != -1, dtype='int32'), axis=1)
    input_length = K.sum(K.ones_like(y_pred[:, :, 0], dtype='int32'), axis=1)
    return K.ctc_batch_cost(y_true, y_pred, input_length, label_length)

model.compile(optimizer=Adam(learning_rate=0.001), loss=ctc_loss)

# ---------------------------
# 5. Data generator for variable-length sequences
# ---------------------------
def generator(X, y, batch_size=8):
    while True:
        # Shuffle indices
        idx = np.random.permutation(len(X))
        for start in range(0, len(X), batch_size):
            end = min(start+batch_size, len(X))
            batch_X = X[start:end]
            batch_y = y[start:end]
            # Pad sequences to same length (for batching)
            max_len = max([len(seq) for seq in batch_y])
            y_pad = -1 * np.ones((len(batch_X), max_len), dtype=np.int32)
            for i, seq in enumerate(batch_y):
                y_pad[i, :len(seq)] = seq
            # Pad traces? Not needed because we use variable time dimension; but we need to pad to same time for batching.
            # Actually, we can use ragged tensors or pad with zeros. For simplicity, we'll pad traces to the same length.
            max_t = max([arr.shape[0] for arr in batch_X])
            X_pad = np.zeros((len(batch_X), max_t, batch_X[0].shape[1]), dtype=np.float32)
            for i, arr in enumerate(batch_X):
                X_pad[i, :arr.shape[0], :] = arr
            yield (X_pad, y_pad)

batch_size = 8
train_gen = generator(X_train, y_train, batch_size)
val_gen = generator(X_val, y_val, batch_size)

steps_per_epoch = max(1, len(X_train) // batch_size)
validation_steps = max(1, len(X_val) // batch_size)

# ---------------------------
# 6. Train the model
# ---------------------------
history = model.fit(
    train_gen,
    steps_per_epoch=steps_per_epoch,
    epochs=50,
    validation_data=val_gen,
    validation_steps=validation_steps,
    callbacks=[
        tf.keras.callbacks.ModelCheckpoint('best_model.h5', save_best_only=True),
        tf.keras.callbacks.EarlyStopping(patience=5, restore_best_weights=True)
    ]
)

# Save the final model
model.save('final_basecaller_model.h5')

# Save the char mapping for later use
with open('char_map.pkl', 'wb') as f:
    pickle.dump(char_to_idx, f)

print("Training complete. Model saved.")