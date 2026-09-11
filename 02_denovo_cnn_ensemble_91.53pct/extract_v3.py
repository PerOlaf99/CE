#!/usr/bin/env python3
"""extract_v3.py - M13-labeled, construct-aware, region-tagged training data.

Design (user proposal, approved):
  * gold label per DLL peak = true M13 base (read orientation) -- EXCEPT
    "construct-truth" columns: refpos0 positions where >=90% of wells call a
    non-M13 base consistently (the single T->C mutation + the Cp312 insert
    tail). Those get the consensus construct base as label.
  * the mid-read construct column (closest to read middle) is the internal
    standard (is_mut=1): in eval the model must call the construct base,
    NOT M13.
  * beginning front: peaks "not resolved" -> masked until >=20 consecutive
    ESD==M13 agreements (peaks start to make sense).
  * no tail masking: tail/tail-tail regimes are trained on.
  * 4 region tags (begin/mid/tail/tail-tail) by rank within the usable span.
  * geometry = read_esd(ground_truth/..).peak_positions (SAME as call_guided
    inference; no engine parameters).
  * well split = checkerboard (row+col)%2 -> balanced 48 train / 48 test.

Output: v3_training.npz
"""
import os, sys, json, argparse
from collections import defaultdict
import numpy as np

_HERE = os.path.dirname(os.path.realpath(__file__))
ROOT = os.path.dirname(_HERE) if os.path.basename(_HERE) == '02_denovo_cnn_ensemble_91.53pct' else _HERE
sys.path.insert(0, ROOT)
sys.path.insert(0, _HERE)

from extract_training_data import parse_rsd, parse_esd

CH_NAMES = ['Channel1', 'Channel2', 'Channel3', 'Channel4']
LABELS = ['A', 'C', 'G', 'T']
BASE_MAP = {b: i for i, b in enumerate(LABELS)}
RC_TRANS = str.maketrans('ACGT', 'TGCA')
WINDOW = 15
CONS_FRAC = 0.90      # fraction of wells agreeing on a non-M13 base
REGION_CUT = [0.15, 0.65, 0.90]
GT = os.path.join(ROOT, 'ground_truth', 'MB1000_M13_DT_Cp312_MD1')
PLATE = os.path.join(ROOT, 'MB1000_M13_DT')


def rc(seq):
    return seq[::-1].translate(RC_TRANS)


def load_clean_ref():
    with open(os.path.join(ROOT, 'settingsV10.json')) as f:
        s = json.load(f)
    ref = ''.join(c for c in s['reference_dna'] if c in 'ACGT')
    return rc(ref)


def semi_global_sw(query, ref):
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
    a_, b_ = [], []
    while i > 0:
        if tb[i, j] == 0:
            a_.append(query[i - 1]); b_.append(ref[j - 1]); i -= 1; j -= 1
        elif tb[i, j] == 1:
            a_.append(query[i - 1]); b_.append('-'); i -= 1
        else:
            a_.append('-'); b_.append(ref[j - 1]); j -= 1
    return ''.join(reversed(a_)), ''.join(reversed(b_))


def align_cols(ed_q, ed_idx, peaks, ref_rc):
    """Align ESD ACGT seq to M13 (read orientation)."""
    K = 15
    if len(ed_q) < K + 45:
        return []
    qset = {ed_q[i:i + K]: i for i in range(len(ed_q) - K + 1)}
    offs = [j - qset[ref_rc[j:j + K]] for j in range(len(ref_rc) - K + 1)
            if ref_rc[j:j + K] in qset]
    if len(offs) < 3:
        return []
    med = int(np.median(offs))
    start = max(0, med - 400)
    win = ref_rc[start:med + 2 * len(ed_q)]
    al, bl = semi_global_sw(ed_q, win)
    cols = []
    qi = 0
    rcount = 0
    for a, b in zip(al, bl):
        if a == '-':
            if b != '-':
                rcount += 1
            continue
        qi_this = qi
        qi += 1
        if b == '-':
            continue
        rpos0 = start + rcount
        rcount += 1
        cols.append((ed_idx[qi_this], int(peaks[ed_idx[qi_this]]), b, a, rpos0))
    return cols


def region_of(rank_frac):
    if rank_frac < REGION_CUT[0]:
        return 0
    if rank_frac < REGION_CUT[1]:
        return 1
    if rank_frac < REGION_CUT[2]:
        return 2
    return 3


def extract_well(well, ch, esd, ref_rc):
    """Returns usable (front-masked, window-in-trace) columns + agree array."""
    seq = esd.get('sequence', '')
    peaks = esd.get('peak_positions', None)
    n_scan = len(ch)
    if peaks is None or len(peaks) == 0 or len(seq) < 60:
        return None, 'no-peaks'
    if len(peaks) < len(seq):
        return None, 'short-peaks'
    ed_q = ''.join(c for c in seq if c in 'ACGT')
    ed_idx = [i for i, c in enumerate(seq) if c in 'ACGT']
    cols = align_cols(ed_q, ed_idx, peaks, ref_rc)
    if len(cols) < 200:
        return None, 'align-fail'
    agree = np.array([1.0 if (a == b and b in 'ACGT') else 0.0
                      for (_, _, b, a, _) in cols], dtype=np.int8)
    us = 0
    for f in range(len(cols) - 20):
        if agree[f:f + 20].all():
            us = f
            break
    keep = [(ei, sc, rb, eb, rp, qi) for qi, (ei, sc, rb, eb, rp)
            in enumerate(cols)
            if qi >= us and WINDOW <= sc < n_scan - WINDOW]
    if len(keep) < 150:
        return None, 'too-few-usable'
    return dict(
        esd_idx=np.array([k[0] for k in keep], dtype=np.int32),
        scan=np.array([k[1] for k in keep], dtype=np.int32),
        rbase=np.array([k[2] for k in keep], dtype='<U1'),
        esd_base=np.array([k[3] for k in keep], dtype='<U1'),
        refpos0=np.array([k[4] for k in keep], dtype=np.int32),
        order=np.array([k[5] for k in keep], dtype=np.int32),
        n_usable=len(keep), usable_start=us,
    ), 'ok'


def make_window(ch, s, w=WINDOW):
    n = len(ch)
    lo, hi = s - w, s + w + 1
    win = ch[max(0, lo):min(n, hi)]
    if lo < 0 or hi > n:
        win = np.pad(win, ((max(0, -lo), max(0, hi - n)), (0, 0)), mode='edge')
    return win.astype(np.float32)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--wells', default=None)
    ap.add_argument('--out', default=os.path.join(
        os.path.dirname(os.path.abspath(__file__)), 'v3_training.npz'))
    args = ap.parse_args()

    ref_rc = load_clean_ref()
    print(f'M13 ref (read orientation) len={len(ref_rc)}')

    all_wells = sorted(f[:-4] for f in os.listdir(PLATE) if f.endswith('.rsd'))
    if args.wells:
        want = set(args.wells.split(','))
        all_wells = [w for w in all_wells if w in want]

    recs = {}
    nskip = defaultdict(int)
    for well in all_wells:
        rsd = os.path.join(PLATE, well + '.rsd')
        esdf = os.path.join(GT, well + '.esd')
        if not (os.path.exists(rsd) and os.path.exists(esdf)):
            nskip['no-file'] += 1
            continue
        ch = parse_rsd(rsd)[CH_NAMES].values.astype(np.float64)
        esd = parse_esd(esdf)
        r, why = extract_well(well, ch, esd, ref_rc)
        if r is None:
            nskip[why] += 1
            continue
        recs[well] = (r, ch)

    print(f'usable wells: {len(recs)}  skipped: {dict(nskip)}')

    # PASS 1: per-refpos0 histogram of esd-vs-M13 mismatches -> construct bands
    # (mutation locus wobbles +-5 positions between wells, so use cluster bands)
    hist = defaultdict(int)
    for well, (r, _) in recs.items():
        n = r['n_usable']
        for k in range(n):
            if k / max(1, n - 1) < 0.10:
                continue
            if r['esd_base'][k] != r['rbase'][k]:
                hist[int(r['refpos0'][k])] += 1
    cands = sorted(rp for rp, c in hist.items() if c >= 2)
    bands = []
    for rp in cands:
        if bands and rp - bands[-1][1] <= 8:
            bands[-1][1] = rp
        else:
            bands.append([rp, rp])
    construct_bands = []
    for lo, hi in bands:
        total = sum(hist[rp] for rp in range(lo, hi + 1))
        if total >= CONS_FRAC * len(recs):
            center = int(round(np.median([rp for rp in range(lo, hi + 1)
                                          if hist[rp]])))
            construct_bands.append((lo, hi, center, total))
    print(f'construct bands (consistent non-M13, >=90% wells):')
    for lo, hi, center, total in construct_bands:
        print(f'   refpos0 {lo}-{hi} center~{center} hit-count {total}')

    if not construct_bands:
        print('ERROR: no construct bands found'); return

    # internal standard = construct band closest to the median read middle
    mids = [float(r['refpos0'][len(r['refpos0']) // 2])
            for well, (r, _) in recs.items()]
    med_mid = float(np.median(mids))
    MUT_BAND = min(construct_bands, key=lambda b: abs(b[2] - med_mid))
    MUT_RP = MUT_BAND[2]
    mut_lo, mut_hi = MUT_BAND[0], MUT_BAND[1]
    print(f'internal standard (mutation) band {mut_lo}-{mut_hi} '
          f'center={MUT_RP}  (read middle ~{int(med_mid)})')

    # PASS 2: labels + features
    X, y, reg, ismut, sc, rp, esd_idx, wells, tr = ([] for _ in range(9))
    meta = {}
    for well, (r, ch) in recs.items():
        rletter, c = well[0], int(well[1:])
        is_train = int(((ord(rletter) - ord('A')) + c) % 2 == 0)
        n = r['n_usable']
        rank = np.arange(n, dtype=float) / max(1, n - 1)
        region = np.array([region_of(x) for x in rank], dtype=np.uint8)
        yl = np.empty(n, dtype=int)
        mut_arr = np.zeros(n, dtype=np.uint8)
        for k in range(n):
            rp0 = int(r['refpos0'][k])
            in_band = next((b for b in construct_bands if b[0] <= rp0 <= b[1]), None)
            if in_band is not None:
                yl[k] = BASE_MAP[r['esd_base'][k]] if r['esd_base'][k] in BASE_MAP \
                    else BASE_MAP[r['rbase'][k]]
                if mut_lo <= rp0 <= mut_hi and r['esd_base'][k] != r['rbase'][k]:
                    mut_arr[k] = 1
            else:
                yl[k] = BASE_MAP[r['rbase'][k]]
        meta[well] = dict(n=n, usable_start=int(r['usable_start']),
                          is_train=bool(is_train),
                          scan_lo=int(r['scan'].min()),
                          scan_hi=int(r['scan'].max()))
        for k in range(n):
            X.append(make_window(ch, int(r['scan'][k])))
            y.append(int(yl[k])); reg.append(int(region[k]))
            ismut.append(int(mut_arr[k])); sc.append(int(r['scan'][k]))
            rp.append(int(r['refpos0'][k]))
            esd_idx.append(int(r['esd_idx'][k]))
            wells.append(well); tr.append(int(is_train))

    X = np.asarray(X, dtype=np.float32)
    y = np.asarray(y, dtype=np.int32)
    reg = np.asarray(reg, dtype=np.uint8)
    ismut = np.asarray(ismut, dtype=np.uint8)
    sc = np.asarray(sc, dtype=np.int32)
    rp = np.asarray(rp, dtype=np.int32)
    esd_idx = np.asarray(esd_idx, dtype=np.int32)
    wells = np.asarray(wells)
    tr = np.asarray(tr, dtype=np.uint8)
    print(f'total samples {len(y)}  tr={int(tr.sum())} te={int((~tr.astype(bool)).sum())}')
    print('per region (tr/te): ' + ' '.join(
        f'r{k}:{int(((reg==k)&tr.astype(bool)).sum())}/'
        f'{int(((reg==k)&~tr.astype(bool)).sum())}' for k in range(4)))
    print(f'mutation (internal standard) columns: {int(ismut.sum())}')
    np.savez_compressed(args.out, X=X, y=y, region=reg, is_mut=ismut,
                        scan=sc, refpos0=rp, esd_idx=esd_idx, well=wells,
                        split=tr, meta=meta, labels=np.array(LABELS),
                        window=np.int32(WINDOW), mut_ref0=np.int32(MUT_RP),
                        mut_lo=np.int32(mut_lo), mut_hi=np.int32(mut_hi),
                        cband_lo=np.array([b[0] for b in construct_bands]),
                        cband_hi=np.array([b[1] for b in construct_bands]))
    print(f'saved {args.out}')


if __name__ == '__main__':
    main()