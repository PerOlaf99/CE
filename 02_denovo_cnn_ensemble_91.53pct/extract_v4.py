#!/usr/bin/env python3
"""extract_v4.py - iterative M13-guided Viterbi labeling (signal, not ESD).

Round 0: peak->refpos0 map = v3 seed (align_cols on ESD base string).
Round N: peaks re-mapped by a semi-global Viterbi over M13 whose emission is
  the current CNN's P(base|raw window) at each DLL peak; transitions:
  match / ref-delete / peak-insert. M13 fixes WHERE, the signal picks the
  base; no M13 base-bias in the emission. Construct bands get the
  plate-consensus construct base as expected state.
  Re-train the CNN between rounds -> positions converge away from DLL
  base-string errors (EM-style).

Usage:
  extract_v4.py --round 0 --out v4_round0.npz
  extract_v4.py --round N --models 'base_caller_model_v4_r{N-1}_{region}.keras' ...
Output: npz identical in schema to v3 so train_v3/eval_v3 logic is reusable.
"""
import os, sys, argparse, glob
from collections import defaultdict
import numpy as np

ROOT = '/home/tv/electropherogram'
HERE = os.path.join(ROOT, '02_denovo_cnn_ensemble_91.53pct')
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)
os.environ.setdefault('TF_CPP_MIN_LOG_LEVEL', '3')

import extract_v3 as ex
from extract_training_data import parse_rsd, parse_esd
import tensorflow as tf

BASE_MAP = {'A': 0, 'C': 1, 'G': 2, 'T': 3}
LABELS = ['A', 'C', 'G', 'T']
REGIONS = ['begin', 'mid', 'tail', 'tailtail']
WINDOW = ex.WINDOW
CONS_FRAC = 0.90
REF_LO, REF_HI = 650, 2200
DEL = 4.0
INS = 4.0


def sw_pairs(query, ref):
    """NW with free end; returns (aligned query, aligned ref char, ref index
    within ref per column; -1 for query-insert columns)."""
    n, m = len(query), len(ref)
    H = np.zeros((n + 1, m + 1), dtype=np.int64)
    tb = np.zeros((n + 1, m + 1), dtype=np.int8)
    MATCH, MISMATCH, GAP = 2, -3, -4
    H[1:, 0] = -10 ** 9
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            diag = H[i - 1, j - 1] + (MATCH if query[i - 1] == ref[j - 1] else MISMATCH)
            up = H[i - 1, j] + GAP
            left = H[i, j - 1] + GAP
            if diag >= up and diag >= left:
                H[i, j], tb[i, j] = diag, 0
            elif up >= left:
                H[i, j], tb[i, j] = up, 1
            else:
                H[i, j], tb[i, j] = left, 2
    bj = int(np.argmax(H[n, 1:])) + 1
    i, j = n, bj
    a_, b_, r_ = [], [], []
    while i > 0:
        if tb[i, j] == 0:
            a_.append(query[i - 1]); b_.append(ref[j - 1]); r_.append(j - 1)
            i -= 1; j -= 1
        elif tb[i, j] == 1:
            a_.append(query[i - 1]); b_.append('-'); r_.append(-1); i -= 1
        else:
            a_.append('-'); b_.append(ref[j - 1]); r_.append(j - 1); j -= 1
    return (''.join(reversed(a_)), ''.join(reversed(b_)),
            np.array(list(reversed(r_)), dtype=np.int64))


def align_cols_v4(ed_q, ed_idx, peaks, ref_rc, window_pad=400):
    """ESD seq -> M13 (read orientation), rpos0 = TRUE ref index (start+winidx).

    Same anchor logic as v3 but the DP positions are taken from the actual
    window indices, not a left-flush rcount (fixes the -400 semiglobal shift).
    """
    K = 15
    if len(ed_q) < K + 45:
        return []
    qset = {ed_q[i:i + K]: i for i in range(len(ed_q) - K + 1)}
    offs = [j - qset[ref_rc[j:j + K]] for j in range(len(ref_rc) - K + 1)
            if ref_rc[j:j + K] in qset]
    if len(offs) < 3:
        return []
    med = int(np.median(offs))
    start = max(0, med - window_pad)
    win = ref_rc[start:med + 2 * len(ed_q)]
    al, bl, ridx = sw_pairs(ed_q, win)
    cols = []
    qi = 0
    for k, (a, b) in enumerate(zip(al, bl)):
        if a == '-':
            continue
        qi_this = qi
        qi += 1
        if b == '-':
            continue
        rpos0 = start + int(ridx[k])
        cols.append((ed_idx[qi_this], int(peaks[ed_idx[qi_this]]), b, a,
                     rpos0))
    return cols


def viterbi_refmap(peaks, emission, expected_idx):
    n = len(peaks)
    w = REF_HI - REF_LO
    NEG = -1e18
    prev = np.zeros(w)
    tb = np.zeros((n, w), dtype=np.int8)
    arange = np.arange(w)
    for i in range(n):
        ei = emission[i][expected_idx]
        match = np.full(w, NEG)
        match[1:] = prev[:-1] + ei[1:]
        match[0] = prev[0] + ei[0]
        insert = prev - INS
        best = np.maximum(match, insert)
        decay = best + DEL * arange
        best2 = np.maximum.accumulate(decay)
        cur = best2 - DEL * arange
        tb_match = (cur == match)
        tb_ins = (cur == insert) & ~tb_match
        tb[i] = np.where(tb_match, 0, np.where(tb_ins, 2, 1)).astype(np.int8)
        prev = cur
    j = int(np.argmax(prev))
    refpos = np.zeros(n, dtype=np.int32) - 1
    is_insert = np.zeros(n, dtype=bool)
    for i in range(n - 1, -1, -1):
        c = tb[i, j]
        if c == 0:
            refpos[i] = REF_LO + j
            j -= 1
        elif c == 1:
            j -= 1
        else:
            is_insert[i] = True
    return refpos, is_insert


def load_models(globpat):
    mm = {}
    for i, name in enumerate(REGIONS):
        p = glob.glob(globpat.replace('{region}', name))
        if not p:
            print(f'MISSING {globpat.replace("{region}", name)}')
            return None
        mm[i] = tf.keras.models.load_model(p[0], compile=False)
    return mm


def cnn_emission(ch, scans, model):
    X = np.array([ex.make_window(ch, int(s)) for s in scans], dtype=np.float32)
    mu = X.mean(axis=1, keepdims=True)
    sd = X.std(axis=1, keepdims=True) + 1e-8
    X = ((X - mu) / sd).astype(np.float32)
    p = model.predict(X, verbose=0)[:, :4]
    sums = p.sum(axis=1, keepdims=True)
    p = p / np.maximum(sums, 1e-9)
    return np.log(np.maximum(p, 1e-9))


def well_emission(ch, scans, models):
    """region per peak by scan percentile within the well (mapping-free)."""
    lo, hi = scans.min(), scans.max()
    fra = (scans - lo) / max(1, hi - lo)
    rr = np.array([ex.region_of(f) for f in fra], dtype=int)
    lp = np.zeros((len(scans), 4))
    for rg in range(4):
        sel = rr == rg
        if sel.any():
            lp[sel] = cnn_emission(ch, scans[sel], models[rg])
    return lp


def build_bands(all_wells, ref_rc):
    hist = defaultdict(int)
    cons = defaultdict(lambda: defaultdict(int))
    for well in all_wells:
        esdf = os.path.join(ex.GT, well + '.esd')
        if not os.path.exists(esdf):
            continue
        esd = parse_esd(esdf)
        seq = ''.join(c for c in esd.get('sequence', '') if c in 'ACGT')
        pe = esd.get('peak_positions', None)
        if pe is None or len(pe) < len(seq) or len(seq) < 60:
            continue
        ei = [i for i, c in enumerate(esd['sequence']) if c in 'ACGT']
        cols = align_cols_v4(seq, ei, pe, ref_rc)
        if len(cols) < 200:
            continue
        for qi, (_, _, rb, eb, rp0) in enumerate(cols):
            if qi / max(1, len(cols) - 1) < 0.10:
                continue
            if eb in BASE_MAP and rb in BASE_MAP and eb != rb:
                hist[int(rp0)] += 1
                cons[int(rp0)][eb] += 1
    total = len(all_wells)
    cands = sorted(rp for rp, c in hist.items() if c >= 2)
    bands = []
    for rp in cands:
        if bands and rp - bands[-1][1] <= 8:
            bands[-1][1] = rp
        else:
            bands.append([rp, rp])
    out = []
    for lo, hi in bands:
        t = sum(hist[rp] for rp in range(lo, hi + 1))
        if t >= CONS_FRAC * total:
            cnt = defaultdict(int)
            for rp in range(lo, hi + 1):
                for b, c in cons[rp].items():
                    cnt[b] += c
            maj = max(cnt.items(), key=lambda kv: kv[1])[0]
            center = int(round(np.median([rp for rp in range(lo, hi + 1)
                                          if hist[rp]])))
            out.append((lo, hi, center, maj, t))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--round', type=int, default=0)
    ap.add_argument('--models', default=None,
                    help='glob with {region} for per-region models (req r>0)')
    ap.add_argument('--wells', default=None)
    ap.add_argument('--out', default=os.path.join(HERE, 'v4_training.npz'))
    args = ap.parse_args()

    ref_rc = ex.load_clean_ref()
    all_wells = sorted(f[:-4] for f in os.listdir(ex.PLATE) if f.endswith('.rsd'))
    if args.wells:
        want = set(args.wells.split(','))
        all_wells = [w for w in all_wells if w in want]

    bands = build_bands(all_wells, ref_rc)
    print('construct bands: ' + ' '.join(
        f'{lo}-{hi}~{ctr}({maj})' for lo, hi, ctr, maj, _ in bands))
    if not bands:
        print('ERROR: no construct bands'); return
    MUT_BAND = min(bands, key=lambda b: abs(b[2] - 1400))
    mut_lo, mut_hi, MUT_RP = MUT_BAND[0], MUT_BAND[1], MUT_BAND[2]
    print(f'internal standard (mutation) band {mut_lo}-{mut_hi} center={MUT_RP}')

    band_exp = np.empty(REF_HI - REF_LO, dtype=np.int8)
    for j in range(REF_HI - REF_LO):
        rp0 = REF_LO + j
        inb = next((b for b in bands if b[0] <= rp0 <= b[1]), None)
        band_exp[j] = (BASE_MAP[inb[3]] if inb is not None
                       else (BASE_MAP[ref_rc[rp0]] if ref_rc[rp0] in BASE_MAP
                             else 0))

    models = None
    if args.models:
        models = load_models(args.models)
        if models is None:
            print('abort: models missing'); return

    # load per-well channels, scans, esd sequence for agreement
    wells_data = {}
    for well in all_wells:
        rsd = os.path.join(ex.PLATE, well + '.rsd')
        esdf = os.path.join(ex.GT, well + '.esd')
        if not (os.path.exists(rsd) and os.path.exists(esdf)):
            continue
        ch = parse_rsd(rsd)[ex.CH_NAMES].values.astype(np.float64)
        esd = parse_esd(esdf)
        seq = esd.get('sequence', '')
        pe = esd.get('peak_positions', None)
        if pe is None or len(pe) == 0 or len(seq) < 60 or len(pe) < len(seq):
            continue
        ed_idx = np.array([i for i, c in enumerate(seq) if c in 'ACGT'],
                          dtype=np.int32)
        if len(ed_idx) < 100:
            continue
        ed_str = ''.join(seq[i] for i in ed_idx)
        scans = np.array([float(pe[i]) for i in ed_idx])
        wells_data[well] = (ch, ed_idx, ed_str, scans, pe)
    print(f'loaded {len(wells_data)} wells')

    # per-peak mapping + agreement base
    maps = {}
    nskip = defaultdict(int)
    if args.round == 0:
        for well, (ch, ed_idx, ed_str, scans, pe) in wells_data.items():
            cols = align_cols_v4(ed_str, [int(i) for i in ed_idx], pe, ref_rc)
            if len(cols) < 200:
                nskip['align-fail'] += 1
                continue
            rp_full = np.full(len(ed_idx), -1, dtype=np.int32)
            agree_b = np.full(len(ed_idx), '?', dtype='<U1')
            dmap = {}
            for (esdidx, _, rb, eb, rp0) in cols:
                dmap[int(esdidx)] = (int(rp0), eb)
            for k, esdidx in enumerate(ed_idx):
                if int(esdidx) in dmap:
                    rp_full[k], agree_b[k] = dmap[int(esdidx)]
            maps[well] = (rp_full, agree_b)
    else:
        for well, (ch, ed_idx, ed_str, scans, pe) in wells_data.items():
            lp = well_emission(ch, scans, models)
            rp_full, is_insert = viterbi_refmap(scans, lp, band_exp)
            agree_b = np.array([LABELS[int(np.argmax(r))] for r in lp],
                               dtype='<U1')
            maps[well] = (rp_full, agree_b)

    print(f'mapped wells: {len(maps)}  skip: {dict(nskip)}')

    X, y, reg, ismut, sc, rp, esd_idx, wells_l, tr = ([] for _ in range(9))
    meta = {}
    tot_ins = 0
    for well, (rp_full, agree_b) in maps.items():
        ch, ed_idx, ed_str, scans, pe = wells_data[well]
        n_scan = len(ch)
        rletter, c = well[0], int(well[1:])
        is_train = int(((ord(rletter) - ord('A')) + c) % 2 == 0)
        n0 = len(ed_idx)
        # agreement vs expected for front-mask rule
        agree = np.zeros(n0, dtype=np.int8)
        for k in range(n0):
            rp0 = int(rp_full[k])
            if rp0 < REF_LO or rp0 >= REF_HI:
                continue
            # expected base index at this refpos
            b = LABELS[int(band_exp[rp0 - REF_LO])]
            agree[k] = 1 if agree_b[k] == b else 0
        us = 0
        for f in range(n0 - 20):
            if agree[f:f + 20].all():
                us = f
                break
        lab = np.zeros(n0, dtype=int)
        mut = np.zeros(n0, dtype=np.uint8)
        for k in range(n0):
            rp0 = int(rp_full[k])
            if rp0 < REF_LO or rp0 >= REF_HI:
                lab[k] = -1
                continue
            inb = next((b for b in bands if b[0] <= rp0 <= b[1]), None)
            if inb is not None:
                if ed_str[k] in BASE_MAP:
                    lab[k] = BASE_MAP[ed_str[k]]
                else:
                    lab[k] = int(band_exp[rp0 - REF_LO])
            else:
                lab[k] = int(band_exp[rp0 - REF_LO])
            if mut_lo <= rp0 <= mut_hi:
                mut[k] = 1
        keep = [k for k in range(n0)
                if lab[k] >= 0 and k >= us
                and WINDOW <= scans[k] < n_scan - WINDOW]
        if len(keep) < 150:
            nskip['too-few-usable'] += 1
            print(f'{well}: skim too-few-usable (n={len(keep)})')
            continue
        rank = np.arange(len(keep), dtype=float) / max(1, len(keep) - 1)
        region = np.array([ex.region_of(x) for x in rank], dtype=np.uint8)
        meta[well] = dict(n=len(keep), usable_start=int(us),
                          is_train=bool(is_train),
                          scan_lo=int(scans[keep].min()),
                          scan_hi=int(scans[keep].max()))
        for j, k in enumerate(keep):
            X.append(ex.make_window(ch, int(scans[k])))
            y.append(int(lab[k]))
            reg.append(int(region[j]))
            ismut.append(int(mut[k]))
            sc.append(int(scans[k]))
            rp.append(int(rp_full[k]))
            esd_idx.append(int(ed_idx[k]))
            wells_l.append(well)
            tr.append(int(is_train))

    X = np.asarray(X, dtype=np.float32)
    y = np.asarray(y, dtype=np.int32)
    reg = np.asarray(reg, dtype=np.uint8)
    ismut = np.asarray(ismut, dtype=np.uint8)
    sc = np.asarray(sc, dtype=np.int32)
    rp = np.asarray(rp, dtype=np.int32)
    esd_idx = np.asarray(esd_idx, dtype=np.int32)
    wells_l = np.asarray(wells_l)
    tr = np.asarray(tr, dtype=np.uint8)
    print(f'total {len(y)} tr={int(tr.sum())} te={int((~tr.astype(bool)).sum())} '
          f'mut cols={int(ismut.sum())}')
    print('per region (tr/te): ' + ' '.join(
        f'r{k}:{int(((reg==k)&tr.astype(bool)).sum())}/'
        f'{int(((reg==k)&~tr.astype(bool)).sum())}' for k in range(4)))
    np.savez_compressed(args.out, X=X, y=y, region=reg, is_mut=ismut,
                        scan=sc, refpos0=rp, esd_idx=esd_idx, well=wells_l,
                        split=tr, meta=meta, labels=np.array(LABELS),
                        window=np.int32(WINDOW), mut_ref0=np.int32(MUT_RP),
                        mut_lo=np.int32(mut_lo), mut_hi=np.int32(mut_hi),
                        cband_lo=np.array([b[0] for b in bands]),
                        cband_hi=np.array([b[1] for b in bands]),
                        cons_base=np.array([b[3] for b in bands]))
    print(f'saved {args.out}')


if __name__ == '__main__':
    main()