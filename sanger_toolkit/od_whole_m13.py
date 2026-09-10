#!/usr/bin/env python3
"""Whole-read duplex sweep, M13-ANCHORED targets (reference truth, not ESD).
Expected pair at read base i = m13[coord[i]:coord[i]+2] via global alignment.
Reports self-match, stitched-vs-M13 and divergence vs ESD per band."""
import glob, json, os, re, sys, time
import numpy as np
from scipy.optimize import differential_evolution
from Bio import Align

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'sanger_toolkit'))
sys.path.insert(0, ROOT)

from optimize_windows_esd import load_well
from optimize_duplex import (call_duplex, _obj_worker, GLOBAL, _sep_cache,
                             _decode_duplex)

raw, esd_seq, esd_pp = load_well(os.path.join(ROOT, 'MB1000_M13_DT'), 'A01',
                                 'MB1000_M13_DT_Cp312_MD1')
m13 = open(os.path.join(ROOT, 'M13.md')).read().strip().upper()

al = Align.PairwiseAligner(); al.match_score = 2; al.mismatch_score = -1
al.open_gap_score = -2; al.extend_gap_score = -1; al.mode = 'global'
a = al.align(esd_seq, m13)[0]
coord = np.full(len(esd_seq), -1, dtype=int)
ei = mi = -1
for c1, c2 in zip(a[0], a[1]):
    if c2 != '-': mi += 1
    if c1 != '-':
        ei += 1
        if c2 != '-': coord[ei] = mi
print(f'global align: esd {len(esd_seq)}bp vs m13 {len(m13)}bp; coords assigned '
      f'{int((coord>=0).sum())}')

jsons = []
for fn in glob.glob(os.path.join(ROOT, 'sanger_toolkit', 'A01*_*.json')):
    nums = [int(x) for x in re.findall(r'\d+', os.path.basename(fn))]
    if len(nums) >= 2:
        jsons.append((nums[0], nums[1], fn))
jsons.sort()


def window_init(scan):
    best = None
    for a, b, fn in jsons:
        if a <= scan <= b:
            span = b - a
            if best is None or span < best[0]:
                best = (span, fn)
    if best is None:
        best = (1e9, min(jsons, key=lambda t: abs(t[0] - scan))[2])
    return json.load(open(best[1]))


def init_params(j):
    return dict(baseline_method=j['baseline_method'], baseline_window=j['baseline_window'],
                baseline_window2=j.get('baseline_window2'), smooth_method=j['smooth_method'],
                smooth_window=j['smooth_window'], smooth_order=j['smooth_order'],
                mobility_shifts=list(j['mobility_shifts']), matrix=np.array(j['matrix']),
                matrix_apply_point=j.get('matrix_apply_point', 'smoothed'),
                min_distance=j.get('min_distance', 5.0),
                prominence_frac=j.get('prominence_frac', 0.1),
                norm_window=j.get('norm_window', 800),
                min_distance_floor=j.get('min_distance_floor', 1))

outdir = os.path.join(ROOT, 'sanger_toolkit', 'od_whole_m13')
os.makedirs(outdir, exist_ok=True)
BOUNDS6 = [(0, 1)] * 6
t0 = time.time()
rows = []
_sep_cache.clear()
for i in range(len(esd_seq) - 1):
    outfn = os.path.join(outdir, f'{i:04d}.json')
    if os.path.exists(outfn):
        rows.append(json.load(open(outfn)))
        continue
    if coord[i] < 0 or coord[i] + 1 >= len(m13):
        rows.append(dict(idx=i, scan=int(esd_pp[i]), expected='--', called='', ok=False,
                         note='no m13 coord', el=0))
        json.dump(rows[-1], open(outfn, 'w'))
        continue
    tgt = m13[coord[i]:coord[i] + 2]
    anchor = int(esd_pp[i])
    exp = (int(esd_pp[i]), int(esd_pp[i + 1]))
    init = init_params(window_init(anchor))
    GLOBAL['ctx'] = (raw, tgt, exp, anchor, True, init, True, None, 0)
    ts = time.time()
    res = differential_evolution(_obj_worker, BOUNDS6, maxiter=18, popsize=6,
                                 seed=7 + i, workers=8, polish=False, tol=0.0,
                                 mutation=(0.5, 1.5), recombination=0.7,
                                 updating='deferred')
    p, off, wl = _decode_duplex(res.x, init, True, None, 0, True)
    s = int(round(anchor + off))
    region = (max(0, s), min(len(raw), s + int(round(wl))))
    pos, gseq = call_duplex(raw, p, region)
    rec = dict(idx=i, scan=anchor, m13_idx=int(coord[i]), expected=tgt, called=gseq,
               ok=gseq == tgt, window=list(region), pos=list(map(int, pos)),
               el=round(time.time() - ts, 1))
    json.dump(rec, open(outfn, 'w'), indent=2)
    rows.append(rec)
    if (i + 1) % 60 == 0 or i == len(esd_seq) - 2:
        print(f'... {i+1}/{len(esd_seq)-1} '
              f'{sum(1 for r in rows if r["ok"])} ok  {(time.time()-t0)/60:.1f} min', flush=True)

nOK = sum(1 for r in rows if r['ok'] and r['expected'] != '--')
print(f'\nM13-anchored MATCH rate: {nOK}/{len(rows)- sum(1 for r in rows if r["expected"]=="--")} '
      f'= {100*nOK/(len(rows)- sum(1 for r in rows if r["expected"]=="--")):.1f}%')

print('\nband       dup-ok   stch-vs-M13   ESD-vs-M13   stch-vs-ESD   (n)')
bands = [(2082, 2400), (2400, 3000), (3000, 4000), (4000, 5000), (5000, 6000),
         (6000, 7000), (7000, 8000), (8000, 8600), (8600, 9400)]
for b0, b1 in bands:
    sel = [r for r in rows if b0 <= r['scan'] <= b1]
    if not sel: continue
    ns = sum(1 for r in sel if r['ok'] and r['expected'] != '--')
    sv = ev = se = cov = 0
    for r in sel:
        i = r['idx']; c = r['called']
        if r['expected'] == '--' or coord[i] < 0: continue
        cov += 1
        if r['ok'] and c and c[0] == m13[coord[i]]: sv += 1
        if esd_seq[i] == m13[coord[i]]: ev += 1
        if r['ok'] and c and c[0] == esd_seq[i]: se += 1
    print(f'{b0}-{b1:<5d}   {100*ns/len(sel):5.1f}%   {100*sv/cov if cov else 0:5.1f}%     '
          f'{100*ev/cov if cov else 0:5.1f}%      {100*se/cov if cov else 0:5.1f}%    ({cov})')
print(f'\n({time.time()-t0:.0f}s)')