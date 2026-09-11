#!/usr/bin/env python3
"""train_signal_mask.py - per-bin TRUE-SIGNAL mask classifier.

Task: for each of 128 time-bins over the 9647-scan frame, decide whether the
bin bears a TRUE band (label 1 = any esd called peak falls in the bin) vs
background (0: primer front, dye blob, dead tail).  A band-density mask is the
signal region; start/stop derive as the first/last bin with mask>thresh.

This turns the 96-well regression into a 12k-sample segmentation task and
explicitly implements "we don't basecall the background"."""
import os, sys
import numpy as np
os.environ.setdefault('TF_CPP_MIN_LOG_LEVEL', '3')
sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
import tensorflow as tf

EPOCHS = 200
NB = 128
FRAME = 9647


def build():
    inp = tf.keras.layers.Input(shape=(NB, 5))
    x = tf.keras.layers.Conv1D(32, 7, padding='same', activation='relu')(inp)
    x = tf.keras.layers.Conv1D(64, 5, padding='same', activation='relu')(x)
    x = tf.keras.layers.MaxPooling1D(2)(x)
    x = tf.keras.layers.Conv1D(64, 5, padding='same', activation='relu')(x)
    x = tf.keras.layers.Conv1D(64, 3, padding='same', activation='relu')(x)
    x = tf.keras.layers.Conv1D(128, 3, padding='same', activation='relu')(x)
    x = tf.keras.layers.UpSampling1D(2)(x)
    x = tf.keras.layers.Conv1D(1, 3, padding='same')(x)
    out = tf.keras.layers.Activation('sigmoid', name='mask')(x)
    return tf.keras.Model(inp, out)


def main():
    d = np.load('signal_training.npz', allow_pickle=True)
    X = d['X'].astype(np.float32)
    split = d['split'].astype(bool)
    # rebuild per-bin labels from esd peaks (span array only gives endpoints)
    wells = [w.decode() if isinstance(w, bytes) else w for w in d['well']]
    sys.path.insert(0, '../sanger_toolkit')
    from extract_training_data import parse_esd
    GT = '../ground_truth/MB1000_M13_DT_Cp312_MD1'
    Y = np.zeros((len(X), NB), np.float32)
    for i, w in enumerate(wells):
        E = parse_esd(f'{GT}/{w}.esd')
        pp = np.array([int(p) for p in E['peak_positions']])
        edges = np.linspace(0, 9647, NB + 1).astype(int)
        for p in pp:
            b = int(np.searchsorted(edges, p, side='right') - 1)
            b = max(0, min(NB - 1, b))
            Y[i, b] = 1.0
    # dilate labels by 1 bin (real bands are wide)
    Yd = np.maximum.reduce([np.roll(Y, k, axis=1) for k in [-1, 0, 1]])
    mu = X[split].mean((0, 1), keepdims=True)
    sd = X[split].std((0, 1), keepdims=True) + 1e-6
    Xn = ((X - mu) / sd).astype(np.float32)

    model = build()
    model.compile(tf.keras.optimizers.Adam(1e-3), loss='binary_crossentropy')
    Xtr, Ytr, Xte, Yte = Xn[split], Yd[split], Xn[~split], Yd[~split]
    best = (1e9, -1)
    for ep in range(EPOCHS):
        model.fit(Xtr, Ytr, batch_size=16, verbose=0)
        L = model.evaluate(Xte, Yte, verbose=0)
        if L < best[0]:
            best = (L, ep)
            model.save('signal_mask_model.keras')
    # evaluate
    yp = model.predict(Xte, verbose=0)[..., 0]
    # derive start/stop: first/last bin with prob>0.5, expand to scans
    gt = Yte > 0.5
    errs = []
    for i in range(len(yp)):
        # ground-truth start/stop via span fraction
        g0, g1 = (np.where(gt[i])[0].min(), np.where(gt[i])[0].max())
        m = yp[i] > 0.5
        if m.sum() == 0:
            errs.append((1e9, 1e9))
            continue
        p0, p1 = np.where(m)[0][0], np.where(m)[0][-1]
        errs.append(((p0 - g0) * (FRAME / NB), (p1 - g1) * (FRAME / NB)))
    e = np.array(errs, float)
    print(f'BEST bce={best[0]:.4f} @ep{best[1] + 1}')
    print(f'  test start bin err mean={np.abs(e[:,0]).mean():.0f} scans '
          f'(std {e[:,0].std():.0f})  stop err mean={np.abs(e[:,1]).mean():.0f}')
    print(f'  start within 150 scans: {(np.abs(e[:,0])<150).mean():.2f}  '
          f'stop within 150: {(np.abs(e[:,1])<150).mean():.2f}')
    # quality rows per well
    print('  per-well (pred_start pred_stop, gt_start gt_stop):')
    te_wells = [wells[k] for k in np.flatnonzero(~split)]
    for i in range(len(yp)):
        g0, g1 = np.where(gt[i])[0].min(), np.where(gt[i])[0].max()
        m = yp[i] > 0.5
        if m.sum():
            p0, p1 = np.where(m)[0][0], np.where(m)[0][-1]
        else:
            p0 = p1 = -1
        print(f'    {te_wells[i]}: {p0*(FRAME//NB):5d} {p1*(FRAME//NB):5d} | '
              f'{g0*(FRAME//NB):5d} {g1*(FRAME//NB):5d}')


if __name__ == '__main__':
    main()