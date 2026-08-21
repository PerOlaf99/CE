#!/usr/bin/env python3
"""error_budget.py - decompose de-novo residual errors: mismatch/ins/del."""
import os, sys
HERE = os.path.dirname(os.path.realpath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, ROOT)
os.environ.setdefault('TF_CPP_MIN_LOG_LEVEL', '3')
import numpy as np
import perfect_basecaller as pb
from extract_training_data import parse_esd

WELLS = ['A01', 'B02', 'C03', 'D04', 'E05', 'F06', 'G07', 'H08', 'A09', 'B12']
PLATE = os.path.join(ROOT, 'MB1000_M13_DT')


def decompose(query, ref):
    al = pb.seed_sw_align(query, ref)
    if al is None:
        return None
    q, r = al
    mm = sum(1 for a, b in zip(q, r) if a != '-' and b != '-' and a != b)
    ins = sum(1 for a in q if a == '-')       # extra base in ours (over-call)
    dele = sum(1 for b in r if b == '-')      # missed base (under-call)
    # error position along the read (quartile of aligned query index)
    n = len(q)
    pos = {'Q1': 0, 'Q2': 0, 'Q3': 0, 'Q4': 0}
    qi = 0
    for a, b in zip(q, r):
        if a != '-':
            err = (b == '-') or (a != b and b != '-')
            if err:
                pos[f'Q{min(4, 4 * qi // max(1, n - 1) + 1)}'] += 1
            qi += 1
    acc = 100.0 * sum(1 for a, b in zip(q, r)
                      if a == b and a != '-') / max(1, len(q))
    return dict(acc=acc, mismatch=mm, ins=ins, dele=dele, pos=pos,
                read_len=len(q))


def main():
    models = pb.load_ensemble([os.path.join(
        HERE, 'base_caller_model*.keras')])
    ref = pb.load_clean_ref()
    rows = []
    tot = {k: 0 for k in ('mm', 'ins', 'del')}
    dtot = dict(tot)
    print(f"{'well':5s} | {'ours acc':8s} mm ins del | Q1-Q4 | "
          f"{'DLL acc':8s} mm ins del")
    for w in WELLS:
        try:
            ours = pb.call_raw(os.path.join(PLATE, f'{w}.rsd'),
                               models=models, refine=True)
            d = parse_esd(os.path.join(
                PLATE, 'MB1000_M13_DT_Cp312_MD1', f'{w}.esd'))
            dll_seq = ''.join(c for c in d.get('sequence', '')
                              if c in 'ACGTN')[:len(ref)]
            ro = decompose(ours['seq'], ref)
            rd = decompose(dll_seq, ref)
        except Exception as e:
            print(w, 'ERR', e)
            continue
        if not ro or not rd:
            print(w, 'no alignment')
            continue
        rows.append((w, ro, rd))
        tot['mm'] += ro['mismatch']; tot['ins'] += ro['ins']; tot['del'] += ro['dele']
        dtot['mm'] += rd['mismatch']; dtot['ins'] += rd['ins']; dtot['del'] += rd['dele']
        p = ro['pos']
        print(f"{w:5s} | {ro['acc']:7.2f}% {ro['mismatch']:3d} {ro['ins']:3d} "
              f"{ro['dele']:3d} | {p['Q1']:3d}{p['Q2']:3d}{p['Q3']:3d}{p['Q4']:3d} | "
              f"{rd['acc']:7.2f}% {rd['mismatch']:3d} {rd['ins']:3d} {rd['dele']:3d}",
              flush=True)
    n = len(rows)
    if n:
        print(f"\nours totals/well: mismatch {tot['mm']/n:.1f}  "
              f"ins {tot['ins']/n:.1f}  del {tot['del']/n:.1f}")
        print(f"DLL totals/well:  mismatch {dtot['mm']/n:.1f}  "
              f"ins {dtot['ins']/n:.1f}  del {dtot['del']/n:.1f}")


if __name__ == '__main__':
    main()
