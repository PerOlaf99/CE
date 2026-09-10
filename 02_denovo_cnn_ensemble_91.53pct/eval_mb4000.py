#!/usr/bin/env python3
"""eval_mb4000.py - evaluate de-novo basecaller on MB4000 data using the
correct MB4000 spectral separation matrix (different instrument/dye set
from MB1000)."""
import os
import sys

HERE = os.path.dirname(os.path.realpath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, ROOT)
os.environ.setdefault('TF_CPP_MIN_LOG_LEVEL', '3')

import json
import numpy as np
import perfect_basecaller as pb
from extract_m13_clean_training import load_clean_ref

PLATE = os.path.join(ROOT, '99_archive', 'MB4000_DEMO_DATA')
GT = os.path.join(PLATE, 'MB4000_demo_data_Cp312_MD1')
MB4K_MATRIX_PATH = os.path.join(ROOT, '99_archive', 'matrix_mb4000.json')

# load MB4000-specific matrix
with open(MB4K_MATRIX_PATH) as f:
    _d = json.load(f)
MB4K_MATRIX = np.array(_d['matrix'], dtype=np.float64)
print(f'MB4000 matrix condition: {_d.get("condition", "?")}')

# wells to eval: all with both rsd + esd
letters = 'ABCDEFGHIJKLMNOP'
cols = list(range(1, 25))
all_wells = [f'{r}{c:02d}' for r in letters for c in cols]
wells = [w for w in all_wells
         if os.path.isfile(os.path.join(PLATE, w + '.rsd'))
         and os.path.isfile(os.path.join(GT, w + '.esd'))]
print(f'{len(wells)} wells with both rsd+esd')

ref = load_clean_ref()
models = pb.load_ensemble([os.path.join(HERE, 'base_caller_model*.keras')])
print(f'ensemble: {len(models)} models')

raw_accs, pol_accs = [], []
dll_accs = []
n_ok = 0
for w in wells:
    rsd = os.path.join(PLATE, w + '.rsd')
    # our call with MB4000 matrix, no mobility shifts (None in JSON)
    try:
        r = pb.call_raw(rsd, models=models, refine=True,
                        spec_sep_matrix=MB4K_MATRIX,
                        mobility_shifts=(0, 0, 0, 0))
    except Exception as e:
        print(f'{w:5s} ERR {e}', flush=True)
        continue
    seq = r['seq']
    pol, nfix = pb.polish(seq, r['conf'], ref)
    # score raw vs M13
    raw_nw = pb.seed_sw_align(seq, ref)
    if raw_nw is None:
        print(f'{w:5s} no raw alignment', flush=True)
        continue
    q, r_al = raw_nw
    raw_acc = 100.0 * sum(1 for a, b in zip(q, r_al)
                          if a == b and a != '-') / max(1, len(q))
    pol_nw = pb.seed_sw_align(pol, ref)
    if pol_nw is None:
        pol_acc = 0.0
    else:
        q2, r2 = pol_nw
        pol_acc = 100.0 * sum(1 for a, b in zip(q2, r2)
                              if a == b and a != '-') / max(1, len(q2))
    # DLL baseline
    from extract_training_data import parse_esd
    esd_path = os.path.join(GT, f'{w}.esd')
    d = parse_esd(esd_path)
    dll_seq = ''.join(c for c in d.get('sequence', '') if c in 'ACGTN')
    dll_nw = pb.seed_sw_align(dll_seq, ref)
    if dll_nw is not None:
        qd, rd = dll_nw
        dll_acc = 100.0 * sum(1 for a, b in zip(qd, rd)
                              if a == b and a != '-') / max(1, len(qd))
        dll_accs.append(dll_acc)
    else:
        dll_acc = float('nan')
    raw_accs.append(raw_acc)
    pol_accs.append(pol_acc)
    n_ok += 1
    print(f'{w:5s} ours={raw_acc:6.2f}%  polished={pol_acc:6.2f}%  '
          f'DLL={dll_acc:6.2f}%  fixes={nfix:3d}', flush=True)

print(f'\n=== {n_ok} wells evaluated ===')
print(f'ours raw:    {np.mean(raw_accs):.2f}%  (std {np.std(raw_accs):.2f})')
print(f'ours polish: {np.mean(pol_accs):.2f}%')
if dll_accs:
    print(f'DLL:         {np.mean(dll_accs):.2f}%  (std {np.std(dll_accs):.2f})')
    print(f'margin (ours - DLL): {np.mean(raw_accs) - np.mean(dll_accs):+.2f}')
