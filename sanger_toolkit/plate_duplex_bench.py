#!/usr/bin/env python3
"""PLATE-WIDE M13-anchored duplex graft benchmark (MB1000_M13_DT, 96 wells).

For each well: ESD read -> global align vs M13_bit_longer.md (900 bp truth).
Runs M13-anchored duplex DE only on the HEAD (read start..+150 bp) and TAIL
(last 150 bp) zones, where ~all ESD errors concentrate; mid is left as ESD.
Graft rule (A01-proven): duplex 2-peak call where the window matched its M13
target exactly, else the ESD base.  Reports per-well ESD-vs-ref and
GRAFT-vs-ref, both vs the full 900 bp reference.

Resumable: per-(well,idx) JSON cache in plate_duplex_out/<WELL>/<IDX>.json
Run:  python3 plate_duplex_bench.py [--wells A01 A02 ...]   (default: all 96)
"""
import argparse, glob, json, os, re, sys, time
import numpy as np
from scipy.optimize import differential_evolution
from Bio import Align

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'sanger_toolkit'))

from optimize_windows_esd import load_well
from optimize_duplex import (call_duplex, _obj_worker, GLOBAL, _sep_cache,
                             _decode_duplex, MAX_DRIFT, HARD_DRIFT)

ESD_SUB = 'MB1000_M13_DT_Cp312_MD1'
REF_FN = os.path.join(ROOT, 'M13_bit_longer.md')
OUT = os.path.join(ROOT, 'sanger_toolkit', 'plate_duplex_out')

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


def init_params(j, dsp_note='a01'):
    if dsp_note == 'default':
        from optimize_windows_esd import decode as dec
        x = dec(np.zeros(29), 'diag', True, None)
        return dict(baseline_method=x['baseline_method'], baseline_window=x['baseline_window'],
                    baseline_window2=x['baseline_window2'], smooth_method=x['smooth_method'],
                    smooth_window=x['smooth_window'], smooth_order=x['smooth_order'],
                    mobility_shifts=list(x['mobility_shifts']), matrix=np.array(x['matrix']),
                    matrix_apply_point=x.get('matrix_apply_point', 'smoothed'),
                    min_distance=x.get('min_distance', 5.0),
                    prominence_frac=x.get('prominence_frac', 0.1),
                    norm_window=x.get('norm_window', 800),
                    min_distance_floor=x.get('min_distance_floor', 1))
    return dict(baseline_method=j['baseline_method'], baseline_window=j['baseline_window'],
                baseline_window2=j.get('baseline_window2'), smooth_method=j['smooth_method'],
                smooth_window=j['smooth_window'], smooth_order=j['smooth_order'],
                mobility_shifts=list(j['mobility_shifts']), matrix=np.array(j['matrix']),
                matrix_apply_point=j.get('matrix_apply_point', 'smoothed'),
                min_distance=j.get('min_distance', 5.0),
                prominence_frac=j.get('prominence_frac', 0.1),
                norm_window=j.get('norm_window', 800),
                min_distance_floor=j.get('min_distance_floor', 1))


def align_well(raw, esd_seq, esd_pp, ref):
    al = Align.PairwiseAligner(); al.match_score = 2; al.mismatch_score = -1
    al.open_gap_score = -2; al.extend_gap_score = -1; al.mode = 'global'
    a = al.align(esd_seq, ref)[0]
    coord = np.full(len(esd_seq), -1, dtype=int)
    ei = ri = -1
    for c1, c2 in zip(a[0], a[1]):
        if c2 != '-': ri += 1
        if c1 != '-':
            ei += 1
            if c2 != '-': coord[ei] = ri
    return coord


def rec_drift(r):
    """Window offset (start - anchor scan) of a cached duplex record."""
    if 'drift' in r:
        return r['drift']
    w = r.get('window')
    if not w:
        return None
    return w[0] - r.get('scan', w[0])


def run_zone(well, raw, esd_seq, esd_pp, coord, ref, idxs, dsp_note):
    outw = os.path.join(OUT, well)
    os.makedirs(outw, exist_ok=True)
    GLOBAL['ctx'] = (raw, '', (0, 0), 0, True, None, True, None, 0)
    rows = []
    for i in idxs:
        outfn = os.path.join(outw, f'{i:04d}.json')
        if os.path.exists(outfn):
            cached = json.load(open(outfn))
            dr = rec_drift(cached)
            # self-heal: stale/unclamped caches (pre-MAX_DRIFT) are recomputed
            if dr is not None and abs(dr) > MAX_DRIFT and cached.get('called'):
                os.remove(outfn)
            else:
                rows.append(cached)
                continue
        if coord[i] < 0 or coord[i] + 1 >= len(ref):
            rows.append(dict(idx=i, scan=int(esd_pp[i]), expected='--', called='', ok=False,
                             note='no ref coord', el=0))
            json.dump(rows[-1], open(outfn, 'w'))
            continue
        tgt = ref[coord[i]:coord[i] + 2]
        anchor = int(esd_pp[i])
        init = init_params(window_init(anchor), dsp_note)
        GLOBAL['ctx'] = (raw, tgt,
                         (int(esd_pp[i]), int(esd_pp[i + 1]) if i + 1 < len(esd_pp)
                          else int(esd_pp[i]) + 8),
                         anchor, True, init, True, None, 0)
        ts = time.time()
        res = differential_evolution(_obj_worker, [(0, 1)] * 6, maxiter=18, popsize=6,
                                     seed=7 + i, workers=8, polish=False, tol=0.0,
                                     mutation=(0.5, 1.5), recombination=0.7,
                                     updating='deferred')
        p, off, wl = _decode_duplex(res.x, init, True, None, 0, True)
        s = int(round(anchor + off))
        region = (max(0, s), min(len(raw), s + int(round(wl))))
        pos, gseq = call_duplex(raw, p, region)
        rec = dict(idx=i, scan=anchor, ref_idx=int(coord[i]), expected=tgt, called=gseq,
                   ok=gseq == tgt, window=list(region), pos=list(map(int, pos)),
                   drift=round(s - anchor, 1), el=round(time.time() - ts, 1))
        json.dump(rec, open(outfn, 'w'), indent=2)
        rows.append(rec)
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--wells', nargs='*', default=None,
                    help='subset of well ids; default = all 96 via glob')
    ap.add_argument('--dsp', choices=['a01', 'default'], default='a01')
    ap.add_argument('--zones', default='head,tail',
                    help='comma list of head/tail/mid/all (by ESD idx)')
    ap.add_argument('--max-drift', type=float, default=5.0,
                    help=f'max duplex window drift from anchor (hard cap {HARD_DRIFT})')
    args = ap.parse_args()
    global MAX_DRIFT
    MAX_DRIFT = float(np.clip(args.max_drift, 1.0, HARD_DRIFT))

    ref = open(REF_FN).read().strip().upper()
    if args.wells:
        wells = args.wells
    else:
        wells = sorted(os.path.basename(f)[:-4]
                       for f in glob.glob(os.path.join(ROOT, 'MB1000_M13_DT', '*.rsd')))
    zones = set(args.zones.split(','))

    t0 = time.time()
    print(f'plate duplex graft bench: {len(wells)} wells, zones={sorted(zones)}, '
          f'dsp_init={args.dsp}', flush=True)
    for w in wells:
        ew = os.path.join(ROOT, 'MB1000_M13_DT', ESD_SUB, w + '.esd')
        if not os.path.exists(ew):
            print(f'{w}: no esd, skip', flush=True)
            continue
        raw, esd_seq, esd_pp = load_well(os.path.join(ROOT, 'MB1000_M13_DT'), w, ESD_SUB)
        coord = align_well(raw, esd_seq, esd_pp, ref)
        n = len(esd_seq)
        head = list(range(0, min(150, n)))
        tail = list(range(max(0, n - 150), n))
        mid = list(range(150, n - 150))
        _sep_cache.clear()
        rows = []
        if 'all' in zones:
            rows += run_zone(w, raw, esd_seq, esd_pp, coord, ref, range(n), args.dsp)
        else:
            if 'head' in zones:
                rows += run_zone(w, raw, esd_seq, esd_pp, coord, ref, head, args.dsp)
            if 'tail' in zones:
                rows += run_zone(w, raw, esd_seq, esd_pp, coord, ref, tail, args.dsp)
        byidx = {r['idx']: r for r in rows}
        ed = co = cv = gd = 0   # esd errors, graft errors, insertions, graft div
        for i in range(n):
            ri, base = coord[i], esd_seq[i]
            if ri < 0:
                co += 1
                ed += 1          # esd insertion base counts as an error on both sides
                gd += 1
                continue
            cv += 1
            is_err = base != ref[ri]
            r = byidx.get(i)
            g = base
            if r is not None and r.get('called'):
                dr = rec_drift(r)
                if r['ok'] and dr is not None and abs(dr) <= MAX_DRIFT:
                    g = r['called'][0]
            if is_err: ed += 1
            if g != ref[ri]: gd += 1
        print(f'{w}: esd={100*(n-ed)/n:.1f}% (ed={ed})  '
              f'graft={100*(n-gd)/n:.1f}% (gd={gd})  n={n} ins={co}  '
              f'duplex_ok={sum(1 for r in rows if r["ok"])}/{len(rows)}  '
              f'{(time.time()-t0)/60:.1f}min', flush=True)
    print(f'\nPLATE DONE ({time.time()-t0:.0f}s)')


if __name__ == '__main__':
    main()