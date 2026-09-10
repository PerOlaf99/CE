#!/usr/bin/env python3
"""End-to-end duplex sweep of A01: for every ESD base, a 2-peak duplex window is
optimized against the ESD/read target (self-consistent), beginning at the read
start (scan 2082) through the read end.  Stitched first-base calls are then
compared to M13 reference per band."""
import glob, json, os, re, sys, time
import numpy as np
from scipy.optimize import differential_evolution

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'sanger_toolkit'))
sys.path.insert(0, ROOT)

from optimize_windows_esd import load_well, build_m13_map
import optimize_duplex as OD
from optimize_duplex import (call_duplex, _obj_worker, GLOBAL, _sep_cache,
                             _decode_duplex)

well = 'A01'
raw, esd_seq, esd_pp = load_well(os.path.join(ROOT, 'MB1000_M13_DT'), well,
                                 'MB1000_M13_DT_Cp312_MD1')
m13new = OD.load_m13(os.path.join(ROOT, 'M13_bit_longer.md'))
m13old = OD.load_m13(os.path.join(ROOT, 'M13.md'))
_, _, mp_new = build_m13_map(esd_seq, m13new)
_, _, mp_old = build_m13_map(esd_seq, m13old)
print('esd', len(esd_seq), 'bp; scans', esd_pp.min(), '-', esd_pp.max())

# per-window settings grid: map anchor scan -> json
jsons = []
for fn in glob.glob(os.path.join(ROOT, 'sanger_toolkit', 'A01*_*.json')):
    nums = [int(x) for x in re.findall(r'\d+', os.path.basename(fn))]
    if len(nums) >= 2:
        jsons.append((nums[0], nums[1], fn))
jsons.sort()
print('window json grid:', [(a, b) for a, b, _ in jsons])


def window_init(scan):
    """most specific json covering scan (fallback: nearest start)."""
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
    return dict(
        baseline_method=j['baseline_method'], baseline_window=j['baseline_window'],
        baseline_window2=j.get('baseline_window2'),
        smooth_method=j['smooth_method'], smooth_window=j['smooth_window'],
        smooth_order=j['smooth_order'], mobility_shifts=list(j['mobility_shifts']),
        matrix=np.array(j['matrix']),
        matrix_apply_point=j.get('matrix_apply_point', 'smoothed'),
        min_distance=j.get('min_distance', 5.0), prominence_frac=j.get('prominence_frac', 0.1),
        norm_window=j.get('norm_window', 800), min_distance_floor=j.get('min_distance_floor', 1))

MAXITER, POPSIZE = 18, 6
BOUNDS6 = [(0, 1)] * 6
outdir = os.path.join(ROOT, 'sanger_toolkit', 'od_whole')
os.makedirs(outdir, exist_ok=True)

t0 = time.time()
rows = []
_sep_cache.clear()
for i in range(len(esd_seq) - 1):
    outfn = os.path.join(outdir, f'{well}_{i:04d}.json')
    if os.path.exists(outfn):
        rows.append(json.load(open(outfn)))
        continue
    tgt = esd_seq[i:i + 2]
    anchor = int(esd_pp[i])
    exp = (int(esd_pp[i]), int(esd_pp[i + 1]))
    init = init_params(window_init(anchor))
    GLOBAL['ctx'] = (raw, tgt, exp, anchor, True, init, True, None, 0)
    ts = time.time()
    res = differential_evolution(_obj_worker, BOUNDS6, maxiter=MAXITER,
                                 popsize=POPSIZE, seed=7 + i, workers=8,
                                 polish=False, tol=0.0, mutation=(0.5, 1.5),
                                 recombination=0.7, updating='deferred')
    p, off, wl = _decode_duplex(res.x, init, True, None, 0, True)
    s = int(round(anchor + off))
    region = (max(0, s), min(len(raw), s + int(round(wl))))
    pos, gseq = call_duplex(raw, p, region)
    rec = dict(idx=i, scan=anchor, expected=tgt, called=gseq,
               ok=gseq == tgt, window=list(region), pos=list(map(int, pos)),
               el=round(time.time() - ts, 1),
               min_distance=p['min_distance'], prom=p['prominence_frac'],
               norm=p['norm_window'], floor=p['min_distance_floor'],
               baseline=p['baseline_method'], smooth=p['smooth_method'],
               apply_pt=p['matrix_apply_point'], shifts=list(p['mobility_shifts']))
    json.dump(rec, open(outfn, 'w'), indent=2)
    rows.append(rec)
    if (i + 1) % 40 == 0 or i == len(esd_seq) - 2:
        el = time.time() - t0
        nOK = sum(1 for r in rows if r['ok'])
        print(f'... {i+1}/{len(esd_seq)-1} dup  {nOK} ok  '
              f'{el/60:.1f} min  ({(i+1)/max(el,1e-9):.1f} dup/s)  ETA {(len(esd_seq)-1-i)/max(el/(i+1),1e-9)/60:.0f} min', flush=True)

nOK = sum(1 for r in rows if r['ok'])
print(f'\n=== MATCH rate: {nOK}/{len(rows)} = {100*nOK/len(rows):.1f}% ===')

# stitched read from matched duplexes (first base of each)
stitch = []
for r in rows:
    c = r['called']
    stitch.append(c[0] if (r['ok'] and c) else ('-' if not c else None))
stitch = [('' if (s is None) else s) for s in stitch]
s_read = ''.join(stitch)
print('stitched(len)=', len(s_read))

# per-band accuracy vs M13 old (known-good mid identity)
print('\nband         dup  ok%   stitched-vs-M13old  stitched-vs-M13new')
bands = [(2082, 2400), (2400, 3000), (3000, 4000), (4000, 5000), (5000, 6000),
         (6000, 7000), (7000, 8000), (8000, 8600), (8600, 9400)]
tot_ok = tot_v_old = tot_v_new = tot_cov = 0
for b0, b1 in bands:
    sel = [r for r in rows if b0 <= r['scan'] <= b1]
    if not sel:
        continue
    ok = sum(1 for r in sel if r['ok'])
    v_old = v_new = cov = 0
    for r in sel:
        i = r['idx']
        if r['ok'] and r['called']:
            if 0 <= mp_old[i] < len(m13old):
                cov += 1
                v_old += (r['called'][0] == m13old[mp_old[i]])
            if 0 <= mp_new[i] < len(m13new):
                v_new += (r['called'][0] == m13new[mp_new[i]])
    print(f'{b0}-{b1:<5d} {len(sel):5d}  {100*ok/len(sel):5.1f}%    '
          f'{100*v_old/cov if cov else 0:5.1f}% (n={cov})    '
          f'{100*v_new/len(sel) if sel else 0:5.1f}%')
    tot_ok += ok; tot_v_old += v_old; tot_cov += cov; tot_v_new += v_new
    tot_cov_new = sum(1 for r in rows if r['ok'] and r['called'] and 0 <= mp_new[r['idx']] < len(m13new))
print(f'\nTOTAL  match {100*tot_ok/len(rows):.1f}%  vs-M13old {100*tot_v_old/tot_cov:.1f}%  '
      f'vs-M13new {100*tot_v_new/ tot_cov_new:.1f}%  ({time.time()-t0:.0f}s)')
print('baseline refs: esd-vs-M13old =', round(100*sum(esd_seq[i]==m13old[m] for i,m in enumerate(mp_old) if 0<=m<len(m13old))/sum(1 for m in mp_old if 0<=m<len(m13old)),1),
      '%  esd-vs-M13new =', round(100*sum(esd_seq[i]==m13new[m] for i,m in enumerate(mp_new) if 0<=m<len(m13new))/sum(1 for m in mp_new if 0<=m<len(m13new)),1), '%')