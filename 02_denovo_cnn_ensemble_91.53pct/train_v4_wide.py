#!/usr/bin/env python3
"""train_v4_wide.py - train CNN with wider window (25 vs 15) + position channel.

The current 31-scan window (±15) may not capture enough context when peaks
broaden at the tail. A 51-scan window (±25) gives the model more context.

Uses reference-cleaned M13 labels from m13_clean_training.npz.
"""
import os, sys
import numpy as np

__version__ = '4.0-wide'
HERE = os.path.dirname(os.path.realpath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, ROOT)
os.environ.setdefault('TF_CPP_MIN_LOG_LEVEL', '3')

WINDOW = 25
JITTER = 4
NEG_FRAC = 0.15

try:
    import cimarrontv as cim
except ImportError:
    import cimarrontv_shim as cim


def make_window(ch, s):
    n = len(ch)
    lo, hi = s - WINDOW, s + WINDOW + 1
    pad_lo, pad_hi = max(0, -lo), max(0, hi - n)
    win = ch[max(0, lo):min(n, hi)]
    if pad_lo or pad_hi:
        win = np.pad(win, ((pad_lo, pad_hi), (0, 0)), mode='edge')
    return win


def zscore(X4):
    mu = X4.mean(axis=1, keepdims=True)
    sd = X4.std(axis=1, keepdims=True) + 1e-8
    return ((X4 - mu) / sd).astype(np.float32)


def jitter_batch(X, rng):
    Xj = np.empty_like(X)
    for k in range(len(X)):
        d = int(rng.integers(-JITTER, JITTER + 1))
        Xj[k] = np.roll(X[k], d, axis=0)
        if d > 0:
            Xj[k][:d] = X[k][0]
        elif d < 0:
            Xj[k][d:] = X[k][-1]
    return Xj


def add_position_channel(X4, scans, all_wells, well_ids):
    N = len(X4)
    X5 = np.zeros((N, 2 * WINDOW + 1, 5), dtype=np.float32)
    X5[:, :, :4] = X4
    for w in all_wells:
        mask = well_ids == w
        if mask.sum() == 0:
            continue
        w_scans = scans[mask]
        s_min, s_max = w_scans.min(), w_scans.max()
        s_range = max(1, s_max - s_min)
        pos_frac = (w_scans - s_min) / s_range
        X5[mask, :, 4] = pos_frac[:, np.newaxis]
    return X5


def main():
    d = np.load(os.path.join(ROOT, 'm13_clean_training.npz'), allow_pickle=True)
    X, y, wells = d['X'], d['y'].astype(int), d['wells']
    scans = d['scans'] if 'scans' in d.files else np.zeros(len(y), dtype=np.int32)

    # Re-extract features with wider window (can't use the cached 31-wide windows)
    print(f'Need to re-extract with WINDOW={WINDOW} (cached data uses WINDOW=15)')
    print(f'Re-extracting features...')

    import time
    from extract_training_data import parse_rsd, parse_esd

    BASE_DIR = os.path.join(ROOT, 'MB1000_M13_DT')
    ESD_DIR = os.path.join(BASE_DIR, 'MB1000_M13_DT_Cp312_MD1')
    CH_NAMES = ['Channel1', 'Channel2', 'Channel3', 'Channel4']
    LABELS = ['A', 'C', 'G', 'T']
    BASE_MAP = {b: i for i, b in enumerate(LABELS)}

    all_wells = sorted(set(wells))
    X_parts, y_parts, scans_parts, wells_parts = [], [], [], []

    t0 = time.time()
    for w in all_wells:
        rsd = os.path.join(BASE_DIR, f"{w}.rsd")
        esd_path = os.path.join(ESD_DIR, f"{w}.esd")
        if not os.path.exists(rsd) or not os.path.exists(esd_path):
            continue
        try:
            df = parse_rsd(rsd)
            esd = parse_esd(esd_path)
        except Exception:
            continue
        ch = df[CH_NAMES].values.astype(np.float64)
        n_scans = len(ch)
        seq = esd.get('sequence', '')
        peaks = esd.get('peak_positions')
        if peaks is None or seq is None:
            continue

        # Get the reference-cleaned labels
        from extract_m13_clean_training import load_clean_ref, seed_sw_align
        ref_rc = load_clean_ref()
        ed_q = ''.join(c for c in seq if c in 'ACGT')
        ed_idx = [i for i, c in enumerate(seq) if c in 'ACGT']
        al, bl = seed_sw_align(ed_q, ref_rc)
        if al is None:
            continue

        X_w, y_w, sc_w = [], [], []
        qi = 0
        for a, b in zip(al, bl):
            if a == '-':
                continue
            if b == '-':
                qi += 1
                continue
            try:
                scan = int(peaks[ed_idx[qi]])
            except IndexError:
                break
            if WINDOW <= scan < n_scans - WINDOW:
                X_w.append(make_window(ch, scan))
                y_w.append(BASE_MAP.get(b, 4))
                sc_w.append(scan)
            qi += 1

        if len(X_w) >= 100:
            X_parts.append(np.array(X_w, dtype=np.float32))
            y_parts.append(np.array(y_w, dtype=np.uint8))
            scans_parts.append(np.array(sc_w, dtype=np.int32))
            wells_parts.append(np.full(len(y_w), w))

    X = np.concatenate(X_parts)
    y = np.concatenate(y_parts)
    scans_arr = np.concatenate(scans_parts)
    wells_arr = np.concatenate(wells_parts)
    print(f'Extracted {len(y)} windows in {time.time()-t0:.1f}s')

    test_wells = set(all_wells[::8])
    te = np.array([w in test_wells for w in wells_arr])
    tr = ~te
    print(f'train: {tr.sum()}  test: {te.sum()}')

    rng = np.random.default_rng(42)
    neg_X, neg_y, neg_scans = [], [], []
    uniq_wells = sorted(set(wells_arr[tr]))
    n_neg_target = int(NEG_FRAC * tr.sum())
    per_well = max(1, n_neg_target // len(uniq_wells))
    for w in uniq_wells:
        rsd = os.path.join(BASE_DIR, f'{w}.rsd')
        if not os.path.isfile(rsd):
            continue
        ch_raw, _ = cim.read_rsd(rsd)
        chw = np.asarray(ch_raw, dtype=np.float64)
        if chw.shape[0] == 4 and chw.shape[0] <= chw.shape[1]:
            chw = chw.T
        pk = np.sort(scans_arr[wells_arr == w])
        if len(pk) < 4:
            continue
        med = np.median(np.diff(pk))
        mids = [int((a + b) // 2) for a, b in zip(pk[:-1], pk[1:])
                if b - a >= 1.3 * med]
        far = rng.integers(200, len(chw) - 200, size=per_well)
        far = [int(s) for s in far if np.min(np.abs(pk - s)) > 2 * WINDOW]
        picks = (mids[:per_well // 2] + far)[:per_well]
        for s in picks:
            neg_X.append(make_window(chw, s))
            neg_y.append(4)
            neg_scans.append(s)
    print(f'negatives: {len(neg_y)}')

    if neg_X:
        X_all = np.concatenate([X[tr], np.array(neg_X, dtype=np.float32)])
        y_all = np.concatenate([y[tr], np.array(neg_y)])
        scans_all = np.concatenate([scans_arr[tr], np.array(neg_scans, dtype=np.int32)])
        wells_all = np.concatenate([wells_arr[tr], np.array(['NEG'] * len(neg_y))])
    else:
        X_all, y_all, scans_all, wells_all = X[tr], y[tr], scans_arr[tr], wells_arr[tr]

    idx = rng.permutation(len(y_all))
    X_all, y_all = X_all[idx], y_all[idx]
    scans_all, wells_all = scans_all[idx], wells_all[idx]

    unique_wells_all = sorted(set(wells_all))
    Xtr5 = add_position_channel(X_all, scans_all, unique_wells_all, wells_all)

    Xte, yte, scans_te = X[te], y[te], scans_arr[te]
    wells_te = wells_arr[te]
    unique_wells_te = sorted(set(wells_te))
    Xte5 = add_position_channel(Xte, scans_te, unique_wells_te, wells_te)

    Xtr5[:, :, :4] = zscore(Xtr5[:, :, :4])
    Xte5[:, :, :4] = zscore(Xte5[:, :, :4])

    import tensorflow as tf
    model = tf.keras.Sequential([
        tf.keras.layers.Input(shape=(2 * WINDOW + 1, 5)),
        tf.keras.layers.Conv1D(64, 7, padding='same', name='conv1'),
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
        tf.keras.layers.Dense(5, activation='softmax', name='base'),
    ])
    model.compile(optimizer=tf.keras.optimizers.Adam(3e-4),
                  loss='sparse_categorical_crossentropy', metrics=['accuracy'])

    classes = np.bincount(y_all, minlength=5)
    cw = {i: len(y_all) / (5 * c) for i, c in enumerate(classes) if c > 0}
    print('class weights:', {k: round(v, 2) for k, v in cw.items()})

    best_acc, best_ep = 0, -1
    for ep in range(25):
        r = rng.permutation(len(y_all))
        epochs_X = Xtr5[r].copy()
        epochs_X[:, :, :4] = jitter_batch(epochs_X[:, :, :4], rng)
        model.fit(epochs_X, y_all[r], batch_size=64, class_weight=cw, verbose=0)
        _, acc = model.evaluate(Xte5, yte, verbose=0)
        print(f'epoch {ep + 1}: val_acc={acc:.4f}', flush=True)
        if acc > best_acc:
            best_acc, best_ep = acc, ep
            model.save(os.path.join(HERE, 'base_caller_model_v4_wide.keras'))
        if ep == 1 and best_acc < 0.6:
            print('aborting: not converging')
            break
    print(f'BEST val_acc={best_acc:.4f} @epoch {best_ep + 1}')


if __name__ == '__main__':
    main()
