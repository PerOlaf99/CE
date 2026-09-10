#!/usr/bin/env python3
"""eval_v3.py - evaluate per-region v3 CNNs on the 48 held-out wells vs M13.

* columns = identical usable span (front-masked, window-in-trace) used in
  training; gold label = true M13 base.
* construct-truth bands (mutation T->C + Cp312 insert region) are excluded
  from identity (their gold is the construct, not M13).
* internal standard: at the mutation column the model must call the ESD
  (construct) base - i.e. we verify it reads the mutation T->C, not M13.
* reports OURS vs ESD over the SAME columns; context bar = Cimarron 3.12
  90.72% whole-read.
"""
import os, sys
import numpy as np
os.environ.setdefault('TF_CPP_MIN_LOG_LEVEL', '3')

HERE = os.path.dirname(os.path.realpath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, ROOT)

import extract_v3 as ex
from extract_training_data import parse_rsd, parse_esd
import tensorflow as tf

LABELS = 'ACGT'
REGIONS = ['begin', 'mid', 'tail', 'tailtail']


def load_models():
    mm = {}
    for r, name in enumerate(REGIONS):
        p = os.path.join(HERE, f'base_caller_model_v3_{name}.keras')
        if not os.path.isfile(p):
            print(f'MISSING {p}')
            continue
        mm[r] = tf.keras.models.load_model(p, compile=False)
    return mm


def main():
    ref_rc = ex.load_clean_ref()
    models = load_models()
    if len(models) != 4:
        print(f'ABORT only {len(models)}/4 region models present'); return

    d = np.load(os.path.join(HERE, 'v3_training.npz'), allow_pickle=True)
    test_wells = sorted({w for w, s in zip(d['well'], d['split']) if not s})
    mut_lo, mut_hi = int(d['mut_lo']), int(d['mut_hi'])
    meta = d['meta'].item()
    print(f'held-out wells: {len(test_wells)}  mutation band {mut_lo}-{mut_hi}')

    agg = {r: [0, 0, 0] for r in range(4)}   # ours_correct, esd_correct, n
    t_cor = t_e_cor = t_n = 0
    mut_ok = mut_n = 0
    rows = []
    for well in test_wells:
        rsd = os.path.join(ex.PLATE, well + '.rsd')
        esdf = os.path.join(ex.GT, well + '.esd')
        ch = parse_rsd(rsd)[ex.CH_NAMES].values.astype(np.float64)
        esd = parse_esd(esdf)
        r, why = ex.extract_well(well, ch, esd, ref_rc)
        if r is None:
            print(f'{well}: skip {why}'); continue
        n = r['n_usable']
        rank = np.arange(n, dtype=float) / max(1, n - 1)
        region = np.array([ex.region_of(x) for x in rank])
        X = np.array([ex.make_window(ch, int(s)) for s in r['scan']])
        mu = X.mean(axis=1, keepdims=True)
        sd = X.std(axis=1, keepdims=True) + 1e-8
        X = ((X - mu) / sd).astype(np.float32)
        called = np.empty(n, dtype='<U1')
        for rg in sorted(set(region)):
            sel = region == rg
            probs = models[int(rg)].predict(X[sel], verbose=0)[:, :4]
            called[sel] = [LABELS[i] for i in probs.argmax(1)]
        mutcol = ((r['refpos0'] >= mut_lo) & (r['refpos0'] <= mut_hi)
                  & (r['esd_base'] != r['rbase']))
        cl = d['cband_lo']; ch2 = d['cband_hi']
        band_ok = np.zeros(n, bool)
        for k, rp in enumerate(r['refpos0']):
            rp = int(rp)
            for blo, bhi in zip(cl, ch2):
                if int(blo) <= rp <= int(bhi):
                    band_ok[k] = True
        exclude = band_ok          # construct-truth columns: gold is not M13
        evalcols = ~exclude
        ok = (called == r['rbase']) & evalcols
        eok = (r['esd_base'] == r['rbase']) & evalcols
        nn = int(evalcols.sum())
        ident = 100.0 * ok.sum() / nn
        eident = 100.0 * eok.sum() / nn
        t_cor += int(ok.sum()); t_e_cor += int(eok.sum()); t_n += nn
        for rg in range(4):
            sel = (region == rg) & evalcols
            agg[rg][0] += int((called[sel] == r['rbase'][sel]).sum())
            agg[rg][1] += int((r['esd_base'][sel] == r['rbase'][sel]).sum())
            agg[rg][2] += int(sel.sum())
        if mutcol.any():
            mut_n += 1
            mut_ok += int(called[mutcol][0] == r['esd_base'][mutcol][0])
            mstmt = (f" mut: called {called[mutcol][0]} esd "
                     f"{r['esd_base'][mutcol][0]} m13 {r['rbase'][mutcol][0]}")
        else:
            mstmt = ' mut?: none'
        rows.append((well, nn, ident, eident))
        print(f"{well} n={nn:4d} ours={ident:6.2f}% esd={eident:6.2f}% "
              f"d={ident - eident:+6.2f}{mstmt}")

    us = 100.0 * t_cor / t_n
    them = 100.0 * t_e_cor / t_n
    print(f'\n== held-out ({len(rows)} wells, {t_n} non-construct columns) ==')
    print(f'OURS identity {us:.2f}%   ESD identity {them:.2f}%')
    print('(same span; Cimarron 3.12 whole-read bar = 90.72%)')
    print(f'internal standard: called construct at mutation in '
          f'{mut_ok}/{mut_n} wells')
    print('per region: ours%  esd%  n')
    for rg in range(4):
        wo = 100.0 * agg[rg][0] / max(1, agg[rg][2])
        we = 100.0 * agg[rg][1] / max(1, agg[rg][2])
        print(f'  {REGIONS[rg]:8s} {wo:6.2f}   {we:6.2f}   {agg[rg][2]}')
    nwin = sum(1 for w in rows if w[2] > w[3])
    print(f'OURS beats ESD on {nwin}/{len(rows)} wells')


if __name__ == '__main__':
    main()