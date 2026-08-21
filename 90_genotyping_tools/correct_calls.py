#!/usr/bin/env python3
"""correct_calls.py - ML error-corrector on top of DLL calls.

DLL quality scores flag the error-prone positions (homopolymers, tail noise).
This replaces the DLL base ONLY at low-quality columns with the k=9 RF's call,
then scores identity vs TRUE M13 through the alignment.

Pipeline per well:
  1. separated trace (tuned engine) + mobility shift
  2. seed alignment of DLL seq to M13 -> DLL base/scan/true-base/quality columns
  3. k=9 windows at DLL peaks -> RF predictions + confidence
  4. corrector rule:
        q < qthreshold               -> keep DLL (ML not trusted on garbage)
        q >= qthreshold AND RF disagrees with DLL
            AND rf_conf > confthr     -> replace with RF call
        else                          -> keep DLL
  5. identity vs true M13

Usage: python3 correct_calls.py [--qthr 60] [--confthr <frac>] [--wells A01]
"""
import argparse, os, sys, time
import numpy as np
warnings = __import__('warnings'); warnings.filterwarnings('ignore')

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cimarrontv as cim
from sklearn.ensemble import RandomForestClassifier
from extract_training_data import parse_rsd, parse_esd
from extract_m13_clean_training import load_clean_ref, seed_sw_align
from extract_kmer_dataset import TUNED, window

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MB1K = 'MB1000_M13_DT'
ESD1K = 'MB1000_M13_DT_Cp312_MD1'
MB4K = 'MB4000_DEMO_DATA'
ESD4K = 'MB4000_DEMO_DATA/MB4000_demo_data_Cp312_MD1'
LABELS = ['A', 'C', 'G', 'T']
BASE_MAP = {b: i for i, b in enumerate(LABELS)}
BASE_CHAR = {i: c for c, i in BASE_MAP.items()}


def separate(raw):
    eng = cim.Cimarron312(variant="3.12", **TUNED)
    eng.call(raw)
    sep = np.asarray(eng.separated, dtype=np.float64)
    if sep.shape != raw.shape:
        sep = raw
    sep_shifted = np.empty_like(sep)
    for c in range(4):
        sep_shifted[:, c] = cim.dsp_shift_channel(sep[:, c], TUNED['mobility_shifts'][c])
    return sep_shifted


def aligned_columns(esd_path, ref_rc):
    """Return dict of per-column arrays (DLL base, scan, q, true base)."""
    d = parse_esd(esd_path)
    seq = d.get('sequence', '')
    peaks = d.get('peak_positions')
    q = d.get('quality_scores')
    if not seq or peaks is None or len(peaks) == 0:
        return None
    ed_q = ''.join(c for c in seq if c in 'ACGT')
    ed_idx = [i for i, c in enumerate(seq) if c in 'ACGT']
    res = seed_sw_align(ed_q, ref_rc)
    if res is None:
        return None
    al, bl = res
    cols = dict(dbase=[], scan=[], q=[], true=[], dllidx=[])
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
        cols['dbase'].append(BASE_MAP[a.upper()])
        cols['scan'].append(scan)
        cols['q'].append(float(q[ed_idx[qi]]) if q is not None else 99.0)
        cols['true'].append(BASE_MAP[b])
        cols['dllidx'].append(ed_idx[qi])
        qi += 1
    for k in cols:
        cols[k] = np.array(cols[k])
    return cols


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--qthr', type=float, default=70,
                    help='DLL quality below which ML may override')
    ap.add_argument('--confthr', type=float, default=0.0,
                    help='RF confidence (max prob) required to override; '
                         '0 = override on any disagreement in low-q zone')
    ap.add_argument('--on', default='mb1000',
                    choices=['mb1000', 'mb4000'],
                    help='which instrument to run on')
    ap.add_argument('--wells', default=None, help='comma-separated subset')
    ap.add_argument('--train-wells', default=None,
                    help='wells to TRAIN the RF on (from kmer_dataset.npz). '
                         'Default: all wells in the npz')
    args = ap.parse_args()

    ref_rc = load_clean_ref()
    # ---- train RF on MB1000 k9 (subset to --train-wells if given)
    d = np.load(os.path.join(BASE_DIR, 'kmer_dataset.npz'), allow_pickle=True)
    if args.train_wells and args.on == 'mb1000':
        train_set = set(args.train_wells.split(','))
        sel = np.array([w in train_set for w in d['wells']])
        print(f'holdout: training RF on {sel.sum()} windows from '
              f'{len(np.unique(d["wells"][sel]))} wells of {np.unique(d["wells"]).shape[0]}',
              flush=True)
    else:
        sel = np.ones(len(d['wells']), dtype=bool)
    X = d['X_sep'][sel].reshape(d['X_sep'][sel].shape[0], -1)
    m = X.max(1, keepdims=True); m[m < 1e-9] = 1e-9
    X = X / m
    rf = RandomForestClassifier(n_estimators=200, max_depth=30,
                                min_samples_leaf=2, class_weight='balanced',
                                n_jobs=4, random_state=42)
    t0 = time.time()
    rf.fit(X, d['y_base'][sel])
    print(f'trained k9 RF ({len(X)} windows) {time.time()-t0:.0f}s', flush=True)

    if args.on == 'mb1000':
        root, esd = MB1K, os.path.join(MB1K, ESD1K)
        wells = sorted(f[:-4] for f in os.listdir(os.path.join(BASE_DIR, root))
                       if f.endswith('.rsd'))
    else:
        root, esd = MB4K, ESD4K
        wells = sorted(f[:-4] for f in os.listdir(os.path.join(BASE_DIR, root))
                       if f.endswith('.rsd'))
    if args.wells:
        wells = [w for w in wells if w in set(args.wells.split(','))]
    print(f'evaluating {len(wells)} wells (on={args.on}, qthr={args.qthr}, '
          f'confthr={args.confthr})', flush=True)

    tot = {k: 0 for k in ['all', 'dll', 'corr']}
    tp_dll = tp_ml = tp_corr = 0
    n_override = 0
    per = []
    disag = dict()
    t1 = time.time()
    for well in wells:
        esd_path = os.path.join(BASE_DIR, esd, well + '.esd')
        rsd_path = os.path.join(BASE_DIR, root, well + '.rsd')
        if not os.path.exists(esd_path) or not os.path.exists(rsd_path):
            continue
        cols = aligned_columns(esd_path, ref_rc)
        if cols is None:
            continue
        if len(cols['scan']) < 9:
            continue
        try:
            df = parse_rsd(rsd_path)
            raw = df[['Channel1', 'Channel2', 'Channel3', 'Channel4']].values.astype(np.float64)
            sep = separate(raw)
        except Exception:
            continue
        # windows at every interior DLL peak
        half = 4
        scans = cols['scan']
        W = np.stack([np.stack([window(sep, int(scans[j]), 15)
                                for j in range(i - half, i + half + 1)])
                      for i in range(half, len(scans) - half)])
        Wf = W.reshape(W.shape[0], -1)
        mx = Wf.max(1, keepdims=True); mx[mx < 1e-9] = 1e-9
        Wf = Wf / mx
        P = rf.predict_proba(Wf)
        pred = rf.classes_[P.argmax(1)]
        conf = P.max(1)
        # indices i correspond to cols rows [half : len-half]
        for j, i in enumerate(range(half, len(scans) - half)):
            t = cols['true'][i]
            dll = cols['dbase'][i]
            q = cols['q'][i]
            ml = pred[j]
            # corrector rule
            if q >= args.qthr or ml == dll or conf[j] < args.confthr:
                final = dll
            else:
                final = ml
                n_override += 1
            tot['all'] += 1
            tp_dll += int(dll == t)
            tp_ml += int(ml == t)
            tp_corr += int(final == t)
            if ml != dll:
                bucket = int(np.clip(conf[j] * 10, 0, 9))
                disag[('n', bucket)] = disag.get(('n', bucket), 0) + 1
                disag[('mlr', bucket)] = disag.get(('mlr', bucket), 0) + (1 if ml == t else 0)
                disag[('dllr', bucket)] = disag.get(('dllr', bucket), 0) + (1 if dll == t else 0)
        print(f'  {well}: done ({len(cols["scan"])} cols)', flush=True)
    if tot['all']:
        print(f'\nidentity vs true M13 (on={args.on}, {tot["all"]} cols):')
        print(f'  DLL          : {tp_dll/tot["all"]:.4f}')
        print(f'  ML alone     : {tp_ml/tot["all"]:.4f}')
        print(f'  CORRECTOR    : {tp_corr/tot["all"]:.4f}  (overrode {n_override} cols, '
              f'{100*n_override/tot["all"]:.1f}%)')
        print('\ndisagreement columns (ML!=DLL): ML-right vs DLL-right by confidence bucket')
        print('  conf-bin   n     ML-right  DLL-right  ML-wins%')
        for b in range(10):
            n = disag.get(('n', b), 0)
            if n:
                mlr = disag.get(('mlr', b), 0)
                dllr = disag.get(('dllr', b), 0)
                print(f'  {b/10:.1f}-{b/10+0.1:.1f}  {n:6d}   {mlr:6d}   {dllr:8d}   '
                      f'{100*mlr/(mlr+dllr):.1f}')
        print(f'elapsed {time.time()-t1:.0f}s')


if __name__ == '__main__':
    main()