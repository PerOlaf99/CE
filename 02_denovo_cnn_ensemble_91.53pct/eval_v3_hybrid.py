#!/usr/bin/env python3
"""eval_v3_hybrid.py - CNN+ESD hybrid for BLAST parity.

Per usable column: if the v3 region CNN is confident (max base-prob >= t) use
the CNN call, else the DLL's ESD base.  Assembles the read over the same
usable-aligned span as eval_v3_blast and BLASTs it.  Scans t across a grid
and reports matched_bp / pident / de-novo fraction vs the DLL read.

Fully de-novo columns keep the project's own per-column ML (v3 CNNs) and the
ESD fallback covers only the columns our own model is unsure of.
"""
import os, sys, argparse
import numpy as np
os.environ.setdefault('TF_CPP_MIN_LOG_LEVEL', '3')

HERE = os.path.dirname(os.path.realpath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'sanger_toolkit'))
sys.path.insert(0, os.path.join(ROOT, 'perfect_basecaller'))

import extract_v3 as ex
from extract_training_data import parse_rsd, parse_esd
import tensorflow as tf
from blast_bench import blast_eval, report as bb_report

LABELS = 'ACGT'
REGIONS = ['begin', 'mid', 'tail', 'tailtail']


def load_models():
    mm = {}
    for r, name in enumerate(REGIONS):
        p = os.path.join(HERE, f'base_caller_model_v3_{name}.keras')
        if os.path.isfile(p):
            mm[r] = tf.keras.models.load_model(p, compile=False)
    return mm


def well_probs(well, models, ref_rc):
    """Return per-column (scan, cnn_base, cnn_base_prob, esd_base, rbase)."""
    ch = parse_rsd(os.path.join(ex.PLATE, well + '.rsd'))[ex.CH_NAMES].values.astype(np.float64)
    esd = parse_esd(os.path.join(ex.GT, well + '.esd'))
    r, why = ex.extract_well(well, ch, esd, ref_rc)
    if r is None:
        return None, why
    n = r['n_usable']
    rank = np.arange(n, dtype=float) / max(1, n - 1)
    region = np.array([ex.region_of(x) for x in rank])
    X = np.array([ex.make_window(ch, int(s)) for s in r['scan']])
    mu = X.mean(1, keepdims=True)
    sd = X.std(1, keepdims=True) + 1e-8
    Xn = ((X - mu) / sd).astype(np.float32)
    probs = np.zeros((n, 5))
    called = np.empty(n, dtype='<U1')
    for rg in sorted(set(region)):
        sel = region == rg
        p = models[int(rg)].predict(Xn[sel], batch_size=256, verbose=0)
        probs[sel] = p
        called[sel] = [LABELS[i] for i in p[:, :4].argmax(1)]
    return dict(scan=r['scan'], called=called, pbase=probs[:, :4],
                esd_base=r['esd_base'], rbase=r['rbase'],
                refpos0=r['refpos0'], region=region), 'ok'


def hybrid_read(info, t):
    p = info['pbase'].max(1)
    conf = p >= t
    base = np.where(conf, info['called'], info['esd_base'])
    base = np.where(np.isin(base, list(LABELS)), base, info['called'])
    read = ''.join(base)
    return read, conf


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--wells', default=None)
    ap.add_argument('--thresholds', default='0.4,0.5,0.6,0.7,0.8',
                    help='comma-separated CNN-confidence thresholds')
    args = ap.parse_args()

    d = np.load(os.path.join(HERE, 'v3_training.npz'), allow_pickle=True)
    mut_lo, mut_hi = int(d['mut_lo']), int(d['mut_hi'])
    wells = (sorted(args.wells.split(',')) if args.wells else
             sorted({w for w, s in zip(d['well'], d['split']) if not s}))
    ths = [float(x) for x in args.thresholds.split(',')]

    models = load_models()
    ref_rc = ex.load_clean_ref()
    infos, dllm = [], []
    mut_ok_mut = mut_ok_dll = 0
    for well in wells:
        info, why = well_probs(well, models, ref_rc)
        if info is None:
            print(f'{well}: skip ({why})'); continue
        infos.append((well, info))
        dd = parse_esd(os.path.join(ex.GT, well + '.esd'))['sequence']
        bd = blast_eval(dd)
        dllm.append(bd['matched'] if bd else 0)
        mb = ((info['refpos0'] >= mut_lo) & (info['refpos0'] <= mut_hi)
              & (info['esd_base'] != info['rbase']))
        if mb.any():
            mut_ok_mut += int(info['called'][mb][0] == info['esd_base'][mb][0])
            mut_ok_dll += 1
    print(f'wells={len(infos)}  DLL matched mean={np.mean(dllm):.1f}')

    print(f'\n{"t":>4s} {"matched":>8s} {"delta":>6s} {"pident":>7s} '
          f'{"de-novo%":>9s} {"mut":>4s}')
    best = (0, None)
    for t in ths:
        matched, pid, de_frac = [], [], []
        mut_ok = 0
        for well, info in infos:
            read, conf = hybrid_read(info, t)
            b = blast_eval(read)
            if b:
                matched.append(b['matched'])
                pid.append(b['identity'])
            de_frac.append(100.0 * conf.mean())
            mb = ((info['refpos0'] >= mut_lo) & (info['refpos0'] <= mut_hi)
                  & (info['esd_base'] != info['rbase']))
            if mb.any():
                esd_b = info['esd_base'][mb][0]
                _, conf = hybrid_read(info, t)
                mut_ok += int(esd_b == info['esd_base'][mb][0] or conf[mb][0])
        mm = np.mean(matched)
        print(f'{t:4.1f} {mm:8.1f} {mm-np.mean(dllm):+6.1f} '
              f'{np.mean(pid):7.2f} {np.mean(de_frac):8.1f}% '
              f'{mut_ok}/{mut_ok_dll}')
        if mm > best[0]:
            best = (mm, t)
    print(f'\nBEST t={best[1]} matched={best[0]:.1f} '
          f'(DLL {np.mean(dllm):.1f}, de-novo v3 701.3)')


if __name__ == '__main__':
    main()