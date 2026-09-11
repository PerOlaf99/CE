#!/usr/bin/env python3
"""eval_v6_blast.py - BLAST-matched over the 48 held-out wells.

Positions: ported DLL envelope detector (FUN_1002511d+...) on the DSP-
calibrated lanes (cache_sep), frame-consistent with the CNN training.
Labels: per-region v5/v6 CNNs (calibrated or raw+calibrated input).
Read: bases in ascending position order, optional CNN-background gate.
Metric: blastn/megablast vs M13 -> matched_bp (fair metric); compare vs
DLL-ESD (754.8) and the pure de-novo v3 read (701.3).
"""
import os, sys, argparse
import numpy as np
os.environ.setdefault('TF_CPP_MIN_LOG_LEVEL', '3')
HERE = os.path.dirname(os.path.realpath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE); sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'sanger_toolkit'))
import dll_peakdet as dp
from extract_training_data import parse_esd
from blast_bench import blast_eval

GT = os.path.join(ROOT, 'ground_truth', 'MB1000_M13_DT_Cp312_MD1')
SEP = os.path.join(ROOT, 'cache_sep')
PLATE = os.path.join(ROOT, 'MB1000_M13_DT')
CH = ['Channel1', 'Channel2', 'Channel3', 'Channel4']
W = 15
LABELS = 'ACGT'
CUTS4 = (0.15, 0.65, 0.90)
CUTS8 = (0.05, 0.15, 0.35, 0.50, 0.65, 0.80, 0.90)


def region_of(f, cuts):
    r = 0
    for c in cuts:
        if f >= c:
            r += 1
        else:
            break
    return r


def window(lanes, s, w=W):
    n = len(lanes)
    lo, hi = s - w, s + w + 1
    win = lanes[max(0, lo):min(n, hi)]
    if lo < 0 or hi > n:
        win = np.pad(win, ((max(0, -lo), max(0, hi - n)), (0, 0)), mode='edge')
    return win.astype(np.float32)


def zscore(X):
    mu = X.mean(axis=1, keepdims=True)
    sd = X.std(axis=1, keepdims=True) + 1e-8
    return ((X - mu) / sd).astype(np.float32)


def load_models(prefix, nreg):
    import tensorflow as tf
    return [tf.keras.models.load_model(f'{prefix}_r{r}.keras', compile=False)
            for r in range(nreg)]


def call_well(well, models, cuts, use_raw, env_floor, bg_gate, region_window):
    sep = np.load(os.path.join(SEP, well + '.npy'))
    pos, domseq, inten = dp.dll_peaks(sep, env_floor_frac=None,
                                      region_window=False)
    if len(pos) == 0:
        return None
    inten = np.array(inten)
    if region_window:
        above = env_floor * inten.max()
        keep = inten >= above
        keep &= dp._longest_signal_region(inten, np.full(len(inten), above))
        pos = pos[keep]
        inten = inten[keep]
    if env_floor and not region_window:
        thr = env_floor * inten.max()
        keep = inten >= thr
        pos = pos[keep]
        inten = inten[keep]
    if len(pos) < 30:
        return None
    fr = np.arange(len(pos), dtype=float) / max(1, len(pos) - 1)
    regs = np.array([region_of(f, cuts) for f in fr])
    Xc = np.array([window(sep, int(s)) for s in pos])
    if use_raw:
        from extract_training_data import parse_rsd
        raw = parse_rsd(os.path.join(PLATE, well + '.rsd'))[CH].values.astype(np.float64)
        Xr = np.array([window(raw, int(s)) for s in pos])
        X = np.concatenate([Xr, Xc], axis=2)
    else:
        X = Xc
    probs = np.zeros((len(pos), 5))
    for r in range(len(models)):
        sel = regs == r
        if sel.sum() == 0:
            continue
        probs[sel] = models[r].predict(zscore(X[sel]), batch_size=256, verbose=0)
    pb_ = probs[:, :4]
    base = pb_.argmax(1)
    keepb = np.ones(len(pos), bool)
    if bg_gate:
        keepb = probs.argmax(1) != 4
    keepb &= np.array([i in range(len(LABELS)) for i in base])
    bases = np.array([LABELS[i] for i in base])[keepb]
    posf = pos[keepb]
    if len(bases) < 30:
        return None
    order = np.argsort(posf)
    read = ''.join(bases[order])
    return dict(read=read, n=len(read), npos=len(pos))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--prefix', required=True, help='model prefix')
    ap.add_argument('--nreg', type=int, required=True, choices=[4, 8])
    ap.add_argument('--use-raw', action='store_true')
    ap.add_argument('--env-floor', type=float, default=0.02)
    ap.add_argument('--region-window', action='store_true')
    ap.add_argument('--bg-gate', action='store_true')
    ap.add_argument('--wells', default=None)
    args = ap.parse_args()

    d = np.load(os.path.join(HERE, 'v3_training.npz'), allow_pickle=True)
    wells = sorted(set(w.decode() if isinstance(w, bytes) else w
                       for w in d['well'] if not bool(d['split'][np.where(d['well'] == w)[0][0]])))
    if args.wells:
        wells = [w for w in args.wells.split(',') if w in wells]
    cuts = CUTS8 if args.nreg == 8 else CUTS4
    models = load_models(args.prefix, args.nreg)
    from extract_training_data import parse_esd
    rows = []
    for well in wells:
        esd = parse_esd(os.path.join(GT, well + '.esd'))
        dllr = blast_eval(esd['sequence'])
        res = call_well(well, models, cuts, args.use_raw, args.env_floor, args.bg_gate, args.region_window)
        if res is None:
            rows.append((well, dllr['matched'] if dllr else 0, 0, 0, 0.0))
            continue
        b = blast_eval(res['read'])
        matched = b['matched'] if b else 0
        ident = b['identity'] if b else 0.0
        rows.append((well, dllr['matched'] if dllr else 0, matched, res['n'], ident))
    m = np.array([r[1] for r in rows]); o = np.array([r[2] for r in rows])
    n = np.array([r[3] for r in rows]); i = np.array([r[4] for r in rows])
    print(f'wells={len(rows)}  DLL matched={m.mean():.1f}  OURS={o.mean():.1f} '
          f'(delta {o.mean()-m.mean():+.1f})  bases={n.mean():.0f} pident={i.mean():.1f}')
    print(' per-well matched:')
    for (w, dm, om, nb, idn) in rows:
        print(f'  {w} DLL {dm:4d} ours {om:4d} ({om-dm:+d}) nbases {nb}')


if __name__ == '__main__':
    main()