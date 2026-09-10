#!/usr/bin/env python3
"""test_refine_cleanup.py - refine_denovo leaves added peaks at add_p=0.68,
below the drop_p=0.70 threshold. Re-score survivors, drop any pmax < drop_p.
Does this fix insertions without killing recall?"""
import os
import sys

HERE = os.path.dirname(os.path.realpath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, ROOT)
os.environ.setdefault('TF_CPP_MIN_LOG_LEVEL', '3')

import numpy as np
import perfect_basecaller as pb
from error_budget import WELLS, PLATE, decompose

REF = pb.load_clean_ref()


def call_with_cleanup(rsd_path, models, drop_p=0.70, add_p=0.68,
                      gap_frac=1.25, iters=3, jitter=2):
    """Reproduce call_raw but with a final cleanup: re-score survivors,
    drop any with pmax < drop_p.  Returns (seq_cleaned, scans_cleaned)."""
    import cimarrontv as cim
    ch, scans = cim.read_rsd(rsd_path)
    eng = pb.build_engine()
    res = eng.call(ch, scans)
    LABELS = 'ACGT'
    seq_raw, ps = [], []
    for base, pk in zip(res.sequence, res.peaks):
        if base in LABELS:
            seq_raw.append(base)
            ps.append(int(round(pk.time)))
    chw = np.asarray(ch, dtype=np.float64)
    if chw.ndim == 2 and chw.shape[0] == 4 and chw.shape[0] <= chw.shape[1]:
        chw = chw.T
    probs = pb.cnn_probs(models, chw, ps)
    pred = probs.argmax(1)
    seq = [LABELS[i] for i in pred]
    conf = np.array([pb.phred(probs[k, i]) for k, i in enumerate(pred)],
                    dtype=np.int32)
    # standard refine
    seq_r, _, scans_r = pb.refine_denovo(models, chw, seq, list(conf),
                                          np.asarray(ps), drop_p=drop_p,
                                          add_p=add_p, gap_frac=gap_frac,
                                          iters=iters, jitter=jitter)
    # NEW: re-score survivors, drop any pmax < drop_p
    scans_r = [int(s) for s in scans_r]
    if scans_r:
        final_probs = pb.cnn_probs(models, chw, scans_r)
        final_pmax = final_probs.max(1)
        keep = final_pmax >= drop_p
        seq_c = ''.join(b for b, k in zip(seq_r, keep) if k)
        scans_c = np.array([s for s, k in zip(scans_r, keep) if k],
                           dtype=np.int64)
    else:
        seq_c, scans_c = seq_r, np.array([], dtype=np.int64)
    # standard refine without cleanup
    return seq_r, seq_c


def main():
    models = pb.load_ensemble([os.path.join(HERE, 'base_caller_model*.keras')])
    print(f'{"well":5s} {"base%":7s}  {"ins":3s} {"mm":3s} {"del":3s}'
          f'  ->  {"base%":7s}  {"ins":3s} {"mm":3s} {"del":3s}  d_acc',
          flush=True)
    a_before, a_after = [], []
    mm_i, mm_f = [], []
    ins_i, ins_f = [], []
    del_i, del_f = [], []
    for w in WELLS:
        rsd = os.path.join(PLATE, f'{w}.rsd')
        seq_std = pb.call_raw(rsd, models=models, refine=True)['seq']
        seq_cln = call_with_cleanup(rsd, models)[0]
        ro = decompose(seq_std, REF)
        rc = decompose(seq_cln, REF)
        if ro is None or rc is None:
            print(w, 'no alignment'); continue
        a_before.append(ro['acc']); a_after.append(rc['acc'])
        mm_i.append(ro['mismatch']); mm_f.append(rc['mismatch'])
        ins_i.append(ro['ins']); ins_f.append(rc['ins'])
        del_i.append(ro['dele']); del_f.append(rc['dele'])
        d = rc['acc'] - ro['acc']
        print(f'{w:5s} {ro["acc"]:6.2f}% {ro["ins"]:3d} {ro["mismatch"]:3d} '
              f'{ro["dele"]:3d}  ->  {rc["acc"]:6.2f}% {rc["ins"]:3d} '
              f'{rc["mismatch"]:3d} {rc["dele"]:3d}  {d:+.2f}', flush=True)
    n = len(a_before)
    print(f'\nmean before: {np.mean(a_before):.3f}% '
          f'ins={np.mean(ins_i):.1f} mm={np.mean(mm_i):.1f} '
          f'del={np.mean(del_i):.1f}')
    print(f'mean after:  {np.mean(a_after):.3f}% '
          f'ins={np.mean(ins_f):.1f} mm={np.mean(mm_f):.1f} '
          f'del={np.mean(del_f):.1f}')
    print(f'delta: ins={np.mean(ins_f)-np.mean(ins_i):+.2f} '
          f'mm={np.mean(mm_f)-np.mean(mm_i):+.2f} '
          f'del={np.mean(del_f)-np.mean(del_i):+.2f}')


if __name__ == '__main__':
    main()
