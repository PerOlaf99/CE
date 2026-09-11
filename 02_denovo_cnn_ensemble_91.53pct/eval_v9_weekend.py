#!/usr/bin/env python3
"""eval_v9_weekend.py - FULL DE-NOVO with the v9 adaptive-width weekend CNN.

Pipeline: raw + Current -> signal_mask_model (true-signal region) ->
dll_peaks candidates in region -> v9 per-region CNN with adaptive window
width (W_R per region) -> (optional) v9-corr second-stage MLP -> BLAST.
Prints per-well DLL vs ours matched.  Also records the A01 identity diagnosable
stats that drive the next iteration.

Usage:  python3 eval_v9_weekend.py [--prefix base_caller_model_v9_corr]
                                     [--corr] [--wells ...]
"""
import os, sys, argparse
import numpy as np
os.environ.setdefault('TF_CPP_MIN_LOG_LEVEL', '3')
HERE = os.path.dirname(os.path.realpath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE); sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'sanger_toolkit'))
import tensorflow as tf
import dll_peakdet as dp
import bandstat as bs
from extract_training_data import parse_esd, parse_rsd
from blast_bench import blast_eval

GT = os.path.join(ROOT, 'ground_truth', 'MB1000_M13_DT_Cp312_MD1')
SEP = os.path.join(ROOT, 'cache_sep')
PLATE = os.path.join(ROOT, 'MB1000_M13_DT')
LABELS = 'ACGT'
CUTS8 = (0.05, 0.15, 0.35, 0.50, 0.65, 0.80, 0.90)
W_R = (8, 10, 12, 14, 15, 18, 24, 30)
NB = 128

_ds = np.load(os.path.join(HERE, 'signal_training.npz'))
_Xs = _ds['X'].astype(np.float32)
MU = _Xs[_ds['split'].astype(bool)].mean((0, 1), keepdims=True)
SD = _Xs[_ds['split'].astype(bool)].std((0, 1), keepdims=True) + 1e-6


def region_of(f, cuts=CUTS8):
    r = 0
    for c in cuts:
        if f >= c: r += 1
        else: break
    return r


def window(lanes, s, w, n):
    lo, hi = s - w, s + w + 1
    win = lanes[max(0, lo):min(n, hi)]
    if lo < 0 or hi > n:
        win = np.pad(win, ((max(0, -lo), max(0, hi - n)), (0, 0)), mode='edge')
    return win.astype(np.float32)


def zscore(X):
    mu = X.mean(axis=1, keepdims=True)
    sd = X.std(axis=1, keepdims=True) + 1e-8
    return ((X - mu) / sd).astype(np.float32)


def predict_region(model, raw, cur):
    edges = np.linspace(0, len(raw), NB + 1).astype(int)
    env = dp.env_max(raw)
    F = np.zeros((1, NB, 5), np.float32)
    for b in range(NB):
        lo, hi = edges[b], edges[b + 1]
        if hi <= lo:
            continue
        F[0, b, 0] = env[lo:hi].max()
        F[0, b, 1] = cur[lo:hi].mean()
        F[0, b, 2] = cur[lo:hi].std()
        F[0, b, 4] = raw[lo:hi].sum() / max(1, hi - lo)
    F[0, 1:, 3] = np.diff(F[0, :, 1])
    F[0, :, 0] /= max(1e-9, F[0, :, 0].max())
    F[0, :, 4] /= max(1e-9, F[0, :, 4].max())
    F = (F - MU) / SD
    m = model.predict(F, verbose=0)[0, :, 0]
    k = m > 0.5
    if k.sum() == 0:
        k = m > m.max() * 0.5
    b0, b1 = np.where(k)[0][0], np.where(k)[0][-1]
    step = len(raw) / NB
    return int(b0 * step), int((b1 + 1) * step)


def call_well(well, sig, models, corr=None):
    raw = parse_rsd(os.path.join(PLATE, well + '.rsd'))[
        ['Channel1', 'Channel2', 'Channel3', 'Channel4']].values.astype(np.float64)
    cur = parse_rsd(os.path.join(PLATE, well + '.rsd'))['Current'].values.astype(float)
    s0, s1 = predict_region(sig, raw, cur)
    sep = np.load(os.path.join(SEP, well + '.npy'))
    n = len(sep)
    pos, domseq, inten = dp.dll_peaks(sep, env_floor_frac=None,
                                      region_window=False, region=(s0, s1))
    if len(pos) < 30:
        return None
    pos = np.array(pos, dtype=np.int64)
    fr = np.arange(len(pos), dtype=float) / max(1, len(pos) - 1)
    regs = np.array([region_of(f_) for f_ in fr])
    # adaptive width windows, grouped by region for batched predict.
    # Regions without a trained model are dropped (do NOT emit arbitrary bases).
    keep = np.ones(len(pos), bool)
    P = np.zeros((len(pos), 4), np.float32)
    for r in range(8):
        sel = regs == r
        if sel.sum():
            if models[r] is None:
                keep[sel] = False
                continue
            Xc = np.array([window(sep, int(s), W_R[r], n) for s in pos[sel]])
            P[sel] = models[r].predict(zscore(Xc), batch_size=256, verbose=0)
    if corr is not None:
        F = bs.band_features(sep, pos)
        Xall = np.concatenate([P, F], axis=1)
        Xn = ((Xall - _cmu) / _csd).astype(np.float32)
        P2 = np.zeros((len(pos), 4), np.float32)
        for r in range(8):
            sel = (regs == r) & keep
            if sel.sum():
                if corr[r] is None:
                    keep[sel] = False
                    continue
                P2[sel] = corr[r].predict(Xn[sel], batch_size=512, verbose=0)
        P = P2
    pos = pos[keep]
    P = P[keep]
    base = P.argmax(1)
    keepb = np.array([i in range(len(LABELS)) for i in base])
    bases = np.array([LABELS[i] for i in base])[keepb]
    posf = pos[keepb]
    if len(bases) < 30:
        return None
    order = np.argsort(posf)
    return ''.join(bases[order])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--corr', action='store_true',
                    help='use v9 second-stage corrector too')
    ap.add_argument('--prefix', default='base_caller_model_v9')
    ap.add_argument('--wells', default=None)
    args = ap.parse_args()

    d = np.load(os.path.join(HERE, 'v3_training.npz'), allow_pickle=True)
    wells = sorted(set(w.decode() if isinstance(w, bytes) else w
                       for w in d['well']
                       if not bool(d['split'][np.where(d['well'] == w)[0][0]])))
    if args.wells:
        wells = [w for w in args.wells.split(',') if w in wells]

    models = [tf.keras.models.load_model(f'{args.prefix}_r{r}.keras',
                                         compile=False) for r in range(8)]
    corr = None
    if args.corr:
        _dc = np.load(os.path.join(HERE, 'corr_training_v9.npz'), allow_pickle=True)
        global _cmu, _csd
        _cmu = _dc['X'][_dc['split']].mean(0)
        _csd = _dc['X'][_dc['split']].std(0) + 1e-8
        corr = [tf.keras.models.load_model(f'{args.prefix}_corr_r{r}.keras',
                                           compile=False) for r in range(8)]
    sig = tf.keras.models.load_model('signal_mask_model.keras', compile=False)

    rows = []
    for well in wells:
        esd = parse_esd(os.path.join(GT, well + '.esd'))
        dllr = blast_eval(esd['sequence'])
        read = call_well(well, sig, models, corr)
        matched, ident, n = 0, 0.0, 0
        if read is not None:
            b = blast_eval(read)
            matched = b['matched'] if b else 0
            ident = b['identity'] if b else 0.0
            n = len(read)
        rows.append((well, dllr['matched'] if dllr else 0, matched, n, ident))
    m = np.array([r[1] for r in rows]); o = np.array([r[2] for r in rows])
    n = np.array([r[3] for r in rows]); i = np.array([r[4] for r in rows])
    print(f'wells={len(rows)}  DLL matched={m.mean():.1f}  '
          f'OURS(v9{"+corr" if args.corr else ""})={o.mean():.1f} '
          f'(delta {o.mean() - m.mean():+.1f})  bases={n.mean():.0f} '
          f'pident={i.mean():.1f}')
    for (w, dm, om, nb, idn) in rows:
        print(f'  {w} DLL {dm:4d} ours {om:4d} ({om - dm:+d}) nb {nb}')


if __name__ == '__main__':
    main()