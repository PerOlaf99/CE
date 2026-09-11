#!/usr/bin/env python3
"""cov_experiment.py - where do the DLL's extra BLAST-matched bases come from?

Builds three read variants per held-out well with the v3 CNNs and BLASTs them:
  V0 baseline  : current eval_v3 read (masked usable aligned columns)
  V1 +insert   : also include ESD-insertion columns (b=='-') in alignment order
  V2 +head     : V1 plus the front-masked head columns
Compares matched_bp mean vs the DLL read (parse_esd).

The DLL read is ~870 chars, ours ~850; this isolates whether the 20 extra
bases are alignment-dropped insertions (should be BLAST-matchable).
"""
import os, sys
import numpy as np
os.environ.setdefault('TF_CPP_MIN_LOG_LEVEL', '3')
sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
import extract_v3 as ex
import train_v3 as tv
from extract_training_data import parse_rsd, parse_esd
import tensorflow as tf
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(
    os.path.realpath(__file__))), 'sanger_toolkit'))
from blast_bench import blast_eval

HERE = os.path.dirname(os.path.realpath(__file__))
LABELS = 'ACGT'


def align_all(ed_q, ed_idx, peaks, ref_rc):
    """Like ex.align_cols but returns EVERY ESD-consuming column in alignment
    order with a running ref counter (e.g. 10.5 = between ref cols 10 and 11)."""
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
    al, bl = ex.semi_global_sw(ed_q, win)
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
        rpos0 = start + rcount if b != '-' else -1
        is_ins = (b == '-')
        if not is_ins:
            rcount += 1
        cols.append((ed_idx[qi_this], int(peaks[ed_idx[qi_this]]),
                     b, a, rpos0, qi_this, bool(is_ins)))
    return cols


def build_read(well, models, ref_rc, d, include_head):
    ch = parse_rsd(os.path.join(ex.PLATE, well + '.rsd'))[ex.CH_NAMES].values.astype(np.float64)
    esd = parse_esd(os.path.join(ex.GT, well + '.esd'))
    seq = esd.get('sequence', '')
    peaks = esd.get('peak_positions', None)
    if peaks is None or len(seq) < 60:
        return None
    ed_q = ''.join(c for c in seq if c in 'ACGT')
    ed_idx = [i for i, c in enumerate(seq) if c in 'ACGT']
    cols = align_all(ed_q, ed_idx, peaks, ref_rc)
    if len(cols) < 100:
        return None
    # usable_start (mask) from stock extract
    room, _ = ex.extract_well(well, ch, esd, ref_rc)
    us = room['usable_start'] if room else 0
    n = len(ch)
    keep = [c for c in cols if ex.WINDOW <= c[1] < n - ex.WINDOW]
    # order columns by alignment order (col[5])
    keep.sort(key=lambda c: c[5])
    scans = np.array([c[1] for c in keep], np.int32)
    rpos = np.array([c[4] for c in keep], np.int32)
    ins = np.array([c[6] for c in keep], bool)
    qidx = np.array([c[5] for c in keep], np.int32)
    region = np.zeros(len(keep), int)
    # rank only over ref-consumed (non-ins) columns in alignment order -> mimic usable span
    nonins_q = qidx[~ins]
    rank_denom = max(1, len(nonins_q) - 1) if len(nonins_q) else 1
    pos_of = {q: i for i, q in enumerate(nonins_q)}
    for k in range(len(keep)):
        if ins[k]:
            region[k] = 2  # tail-ish default for insertions
        else:
            region[k] = ex.region_of(pos_of[qidx[k]] / rank_denom)
    X = np.array([ex.make_window(ch, int(s)) for s in scans])
    mu = X.mean(1, keepdims=True)
    sd = X.std(1, keepdims=True) + 1e-8
    Xn = ((X - mu) / sd).astype(np.float32)
    called = np.empty(len(keep), '<U1')
    for rg in sorted(set(region)):
        sel = region == rg
        p = models[int(rg)].predict(Xn[sel], verbose=0)[:, :4]
        called[sel] = [LABELS[i] for i in p.argmax(1)]
    if include_head:
        mask_ok = (nonins_pos := np.array([pos_of[q] if not ins[k] else -1
                                            for k, q in enumerate(qidx)])) >= 0
        mask = np.array([pos_of[qidx[k]] if not ins[k] else 0 for k in range(len(keep))])
    else:
        # drop columns before the usable start (mimic eval_v3)
        nq = nonins_q
        okq = np.array([pos_of[q] for q in qidx if not ins[k]]
                       for k in range(len(keep)))
        ok = np.array([not ins[k] and pos_of[qidx[k]] >= us for k in range(len(keep))])
    # assemble
    if include_head:
        keep_all = np.arange(len(keep))
    else:
        keep_all = np.array([k for k in range(len(keep))
                             if not ins[k] and pos_of[qidx[k]] >= us])
    read = ''.join(called[keep_all])
    return read, dict(rpos=rpos[keep_all], ins=ins[keep_all],
                      called=called[keep_all], n=len(keep_all))


def main():
    d = np.load(os.path.join(HERE, "v3_training.npz"), allow_pickle=True)
    wells = sorted({w for w, s in zip(d['well'], d['split']) if not s})
    models = {r: tf.keras.models.load_model(
        os.path.join(HERE, f"base_caller_model_v3_{tv.REGIONS[r]}.keras"),
        compile=False) for r in range(4)}
    ref_rc = ex.load_clean_ref()
    from collections import defaultdict
    sums = defaultdict(lambda: [0.0, 0, 0.0])
    print('build reads + blast (48 wells x3 variants)...', flush=True)
    per = []
    for well in wells:
        res = build_read(well, models, ref_rc, d, include_head=True)
        dll = blast_eval(parse_esd(os.path.join(ex.GT, well + '.esd'))['sequence'])
        if res is None:
            print(well, 'no-read'); continue
        readH, info = res
        # V0: emulate without head/ins by using info subsets is complex;
        # instead build the three reads separately with the flag
        res0 = build_read(well, models, ref_rc, d, include_head=False)
        reads = {'V0_mask': res0[0] if res0 else None,
                 'V1_all': readH}
        per.append((well, readH, dll, info, res0))
    # to keep runtime bounded: blast V0 and V1-all per well
    tot = defaultdict(list)
    for well, readH, dll, info, res0 in per:
        dllm = dll['matched'] if dll else 0
        tot['dll'].append(dllm)
        if res0 and res0[0]:
            b0 = blast_eval(res0[0])
            tot['V0'].append(b0['matched'] if b0 else 0)
        else:
            tot['V0'].append(None)
        b1 = blast_eval(readH)
        tot['V1'].append(b1['matched'] if b1 else 0)
    dm = np.mean([x for x in tot['dll']])
    v0 = [x for x in tot['V0'] if x is not None]
    v1 = np.mean([x for x in tot['V1']])
    print(f'\nDLL matched mean      : {dm:.1f}')
    print(f'V0 (masked)  matched  : {np.mean(v0):.1f}  n={len(v0)}  gap={dm-np.mean(v0):+.1f}')
    print(f'V1 (+ins, +head) matched: {v1:.2f}')
    print(f'V1 vs V0 net change     : {v1-np.mean(v0):+.2f}')
    for well, readH, dll, info, res0 in per[:6]:
        l0 = len(res0[0]) if res0 else -1
        print(f'  {well} V0len={l0} V1len={len(readH)} ins={int(info["ins"].sum())} dllmatched={dll["matched"] if dll else -1}')


if __name__ == '__main__':
    main()