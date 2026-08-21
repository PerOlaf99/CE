#!/usr/bin/env python3
"""ctc_train.py - fixed version of the DeepSeek BiLSTM+CTC basecaller.

Fixes vs the original internet code:
  * uses OUR parsers (cim.read_rsd / parse_esd) - theirs assumed a wrong RSD
    layout and text ESDs
  * feeds DSP-separated traces (AsyLS baseline, Butterworth, spectral
    separation) instead of raw crosstalk-contaminated signal
  * CTC blank collides with 'A' in the original (blank=0, A=0) -> classes
    shifted: blank=0, A=1..T=4, N=5
  * traces downsampled x2 (peak spacing ~11 scans) to fit CPU budget
  * well-level 80/16 split

Run AFTER train_v2.py finishes (needs the CPU).
"""
import os, sys
import numpy as np

__version__ = '0.3'  # WIP: loss freezes at uniform-posterior fixed point (see ctc_debug.py)
HERE = os.path.dirname(os.path.realpath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, ROOT)
os.environ.setdefault('TF_CPP_MIN_LOG_LEVEL', '3')

try:
    import cimarrontv as cim
except ImportError:
    import cimarrontv_shim as cim
import dsp_core
from extract_training_data import parse_esd

CHARS = {'A': 1, 'C': 2, 'G': 3, 'T': 4, 'N': 5}
DOWNSAMPLE = 4   # T/L ~2.2 after trim; shortens sequences -> faster epochs
MAX_SPACING = 10.5  # raw scans/base cap for the tail (median ~8.6)
V10_SSM = np.array([[1.0, 1.00, 0.26, 0.46],
                    [0.07, 1.00, 0.075, 0.006],
                    [0.38, 0.33, 1.00, 1.52],
                    [0.27, 0.26, 0.189, 1.00]])


def trim_bounds(chw):
    """Peak-region bounds (raw scan indices) from the RAW total intensity.

    Constant-voltage run -> resistance rises -> current decays slowly.
    Plate survey (all 96 wells): quiet baseline occupies scans ~0-2000
    (onset median 1995, range 1798-2167), then peaks to near trace end;
    some capillaries carry high single-channel background (A03/B03/C03
    G-channel std 60-79 vs typical 10-17). So: noise floor = median
    rolling-std INSIDE the quiet zone (first 2000 scans), onset = first
    sustained 3x crossing of the smoothed rolling-std, tail = last 2x
    crossing (trailing artifacts may stay - CTC emits blanks there).
    Post-DSP noise amplification destroys this contrast, hence RAW input.
    """
    from scipy.ndimage import uniform_filter1d
    tot = chw.sum(1)
    m = uniform_filter1d(tot, 101, mode='nearest')
    v = uniform_filter1d(tot * tot, 101, mode='nearest') - m * m
    rs = np.sqrt(np.maximum(v, 0))
    rss = uniform_filter1d(rs, 201, mode='nearest')
    floor = float(np.median(rs[:2000]))
    a = max(0, int(np.flatnonzero(rss > 3.0 * floor).min()) - 150)
    b = min(len(tot), int(np.flatnonzero(rss > 2.0 * floor).max()) + 200)
    return a, b


def trim_dead_time(sep, bounds, n_labels):
    """Apply bounds; cap the tail (post-peak junk: unresolved blobs then
    background - Cimarron auto-stops for the same reason) and keep T>L."""
    a, b = bounds
    a //= DOWNSAMPLE
    b = min(b // DOWNSAMPLE, a + int(MAX_SPACING * n_labels / DOWNSAMPLE))
    return sep[a:max(a + 1, min(b, sep.shape[0]))]


def load_well(well):
    rsd = os.path.join(ROOT, 'MB1000_M13_DT', well + '.rsd')
    esd = os.path.join(ROOT, 'MB1000_M13_DT', 'MB1000_M13_DT_Cp312_MD1',
                       well + '.esd')
    if not (os.path.isfile(rsd) and os.path.isfile(esd)):
        return None
    ch, _ = cim.read_rsd(rsd)
    chw = np.asarray(ch, dtype=np.float64)
    if chw.shape[0] == 4 and chw.shape[0] <= chw.shape[1]:
        chw = chw.T
    _, _, _, _, sep, _ = dsp_core.full_pipeline(
        chw, (5, 11, 10, 10), 'AsyLS', 50010, 'Butterworth', 5, 9,
        V10_SSM, matrix_apply_point='smoothed')
    mu, sd = sep.mean(0, keepdims=True), sep.std(0, keepdims=True) + 1e-8
    sep = ((sep - mu) / sd)[::DOWNSAMPLE].astype(np.float32)
    d = parse_esd(esd)
    seq = ''.join(c for c in d.get('sequence', '') if c in CHARS)
    if len(seq) < 100:
        return None
    lab = np.array([CHARS[c] for c in seq], dtype=np.int32)
    return trim_dead_time(sep, trim_bounds(chw), len(lab)), lab


def make_model():
    import tensorflow as tf
    inp = tf.keras.layers.Input(shape=(None, 4))
    x = tf.keras.layers.Bidirectional(
        tf.keras.layers.LSTM(128, return_sequences=True))(inp)
    x = tf.keras.layers.Bidirectional(
        tf.keras.layers.LSTM(128, return_sequences=True))(x)
    out = tf.keras.layers.Dense(6, activation='softmax')(x)
    m = tf.keras.models.Model(inp, out)

    def ctc_loss(y_true, y_pred):
        # y_true: (B, L) ints 1..5 (A..N), padded with 0. Blank class = 0.
        y = tf.cast(y_true, tf.int32)
        lens = tf.reduce_sum(tf.cast(y > 0, tf.int32), axis=1)
        mask = tf.sequence_mask(lens, tf.shape(y)[1])
        idx = tf.where(mask)
        sparse = tf.SparseTensor(idx, tf.gather_nd(y, idx),
                                 tf.shape(y, out_type=tf.int64))
        seq_lens = tf.fill([tf.shape(y_pred)[0]], tf.shape(y_pred)[1])
        return tf.nn.ctc_loss(
            labels=tf.sparse.reorder(sparse),
            logits=y_pred,
            label_length=lens,
            logit_length=seq_lens,
            logits_time_major=False,
            blank_index=0)

    m.compile(optimizer=tf.keras.optimizers.Adam(1e-3, clipnorm=1.0),
              loss=ctc_loss)
    return m


def pad_batch(items):
    max_t = max(x.shape[0] for x, _ in items)
    max_l = max(len(l) for _, l in items)
    X = np.zeros((len(items), max_t, 4), dtype=np.float32)
    Y = np.zeros((len(items), max_l), dtype=np.int32)
    for i, (x, l) in enumerate(items):
        X[i, :x.shape[0]] = x
        Y[i, :len(l)] = l
    return X, Y


def main():
    wells = sorted(f[:-4] for f in os.listdir(os.path.join(ROOT, 'MB1000_M13_DT'))
                   if f.endswith('.rsd'))
    rng = np.random.default_rng(42)
    rng.shuffle(wells)
    train_w, val_w = wells[:80], wells[80:]
    print(f'train {len(train_w)} wells, val {len(val_w)} wells', flush=True)

    train = [r for w in train_w if (r := load_well(w))]
    val = [r for w in val_w if (r := load_well(w))]
    print(f'loaded {len(train)}/{len(train_w)} train, '
          f'{len(val)}/{len(val_w)} val', flush=True)

    model = make_model()
    best = np.inf
    for ep in range(120):
        rng.shuffle(train)
        losses = []
        for i in range(0, len(train), 2):
            X, Y = pad_batch(train[i:i + 2])
            losses.append(float(model.train_on_batch(X, Y)))
        vloss = []
        for i in range(0, len(val), 2):
            X, Y = pad_batch(val[i:i + 2])
            vloss.append(float(model.test_on_batch(X, Y)))
        vl = float(np.mean(vloss))
        print(f'epoch {ep + 1}: train={np.mean(losses):8.2f} val={vl:8.2f}',
              flush=True)
        if vl < best:
            best = vl
            model.save(os.path.join(HERE, 'ctc_basecaller_v1.keras'))
    print('saved ctc_basecaller_v1.keras')


if __name__ == '__main__':
    main()
