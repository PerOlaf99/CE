#!/usr/bin/env python3
"""q4_threshold_analysis.py - can a stricter Q4-only drop_p separate the
insertion errors from correct late calls? Uses calls_cache.npz (instant)."""
import os
import sys

HERE = os.path.dirname(os.path.realpath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, ROOT)

import numpy as np
import perfect_basecaller as pb

REF = pb.load_clean_ref()
z = np.load(os.path.join(HERE, 'calls_cache.npz'), allow_pickle=True)

rows = []
for k, w in enumerate(z['wells']):
    seq = str(z['seq'][k])
    conf = z['conf'][k]
    pm = 1 - 10 ** (-conf.astype(float) / 10.0)
    q, r = pb.seed_sw_align(seq, REF)
    qi = -1
    n_al = len(q)
    for a, b in zip(q, r):
        if a == '-':
            continue
        qi += 1
        if qi >= len(pm):
            break
        quart = min(4, 4 * qi // max(1, len(seq) - 1) + 1)
        ok = (a == b)
        rows.append((quart, ok, pm[qi]))

arr = np.array(rows, dtype=[('q', 'i4'), ('ok', '?'), ('pm', 'f4')])
print('calls per quartile:', {qq: int((arr['q'] == qq).sum())
                             for qq in range(1, 5)})
for qq in range(1, 5):
    m = arr['q'] == qq
    ok_pm = arr['pm'][m & arr['ok']]
    bad_pm = arr['pm'][m & ~arr['ok']]
    print(f'Q{qq}: n_err={len(bad_pm):3d} '
          f'err pmax med={np.median(bad_pm) if len(bad_pm) else float("nan"):.3f} '
          f'| correct pmax p10={np.percentile(ok_pm, 10):.3f} '
          f'p25={np.percentile(ok_pm, 25):.3f}')

print('\nQ4-only extra drop sweep (drop calls with pmax < T in Q4):')
m4 = arr['q'] == 4
tot_ok = int((m4 & arr['ok']).sum())
tot_bad = int((m4 & ~arr['ok']).sum())
acc_before = tot_ok / (tot_ok + tot_bad)
for t in (0.70, 0.72, 0.75, 0.78, 0.80, 0.85):
    killed_bad = int((m4 & ~arr['ok'] & (arr['pm'] < t)).sum())
    killed_ok = int((m4 & arr['ok'] & (arr['pm'] < t)).sum())
    kept_ok = tot_ok - killed_ok
    acc_after = kept_ok / max(1, kept_ok + (tot_bad - killed_bad))
    print(f'T={t:.2f}: removes {killed_bad}/{tot_bad} errors, '
          f'kills {killed_ok}/{tot_ok} correct -> '
          f'Q4 local acc {100 * acc_before:.2f}% -> {100 * acc_after:.2f}%')
