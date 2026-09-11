#!/usr/bin/env python3
"""okn_gate.py - Port 1: the OKN called-peak gate.

Applies Cimarron's fuzzy band-classifier (FUN_10012140, see re_artifacts/
classify_fuzzy.py) on top of OUR detector candidates (dll_peakdet.dll_peaks)
using faithful BandStat features (bandstat.okn_features) to reproduce the DLL's
called-peak SET decision:

  q = ftol(centroid(combined sets))     # defuzzified classifier value
  q==1 -> KEEP (emit base)
  q==2 -> weak (emit base, mark posflag 5)
  else -> DROP

So the gate EMITS iff q in {1,2}.  In the DLL this sits AFTER the bandwidth /
env-floor gates in FUN_10019ef2; here it is applied as a post-filter on the
candidate positions that the CNN then labels.

`classify()` takes (Y, sb, envAll, D, E, s2, N) and returns list[(val,qual)].
"""
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
from re_artifacts import classify_fuzzy as cf
import bandstat as bs


def okn_q(lanes, positions):
    """Apply the fuzzy classifier to a candidate set; return int q per band."""
    Y, sb, envAll, D, E, s2 = bs.okn_features(lanes, positions)
    out = cf.classify(list(map(int, Y)), list(map(float, sb)),
                      list(map(float, envAll)), list(map(int, D)),
                      list(map(int, E)), list(map(float, s2)), len(Y))
    q = np.array([int(o[0]) for o in out], np.int64)  # ftol(centroid)
    return q


def okn_gate(lanes, positions, mark_weak=True):
    """Emit mask: True iff q in {1(keep),2(weak)}.  xbnd<=1.176471 marks weak
    (posflag 5) but does NOT affect emission, matching FUN_10012140 caller."""
    q = okn_q(lanes, positions)
    emit = (q == 1) | (q == 2)
    return emit, q


def confus(detected, ground, tol=4):
    """detected/ground int arrays; matching within tol (any-direction)."""
    det = np.sort(detected)
    n = len(det)
    if n == 0 or len(ground) == 0:
        return 0, n, 0
    gi, hi = 0, 0
    tp = 0
    for p in det:
        while gi < len(ground) and ground[gi] < p - tol:
            gi += 1
        if gi < len(ground) and ground[gi] <= p + tol:
            tp += 1
        hi += 1
    return tp, hi, len(ground)  # hits, hits_candidates, ground_total


if __name__ == '__main__':
    # diagnostic mode: verify the gate separates esd-called from non-called
    HERE = os.path.dirname(os.path.realpath(__file__))
    ROOT = os.path.join(HERE, '..')
    sys.path.insert(0, ROOT); sys.path.insert(0, os.path.join(ROOT, 'sanger_toolkit'))
    from extract_training_data import parse_esd
    from dll_peakdet import dll_peaks
    import tensorflow as tf

    GT = os.path.join(ROOT, 'ground_truth', 'MB1000_M13_DT_Cp312_MD1')
    SEP = os.path.join(ROOT, 'cache_sep')
    wells = sys.argv[1:] if len(sys.argv) > 1 else ['A01', 'A02', 'B02']
    from concurrent.futures import ThreadPoolExecutor

    def one(well):
        E = parse_esd(os.path.join(GT, well + '.esd'))
        ground = np.array([int(p) for p in E['peak_positions']])
        sep = np.load(os.path.join(SEP, well + '.npy'))
        det, seq, _ = dll_peaks(sep, env_floor_frac=None, region_window=False)
        # probe gate on raw detector set (over-detected by design)
        emit, q = okn_gate(sep, det)
        tp_a, n_a, g = confus(det[emit], ground)
        tp_b, n_b, _ = confus(det[~emit], ground)
        return well, len(ground), len(det), int(emit.sum()), int((~emit).sum()), \
            tp_a, n_a, tp_b, n_b, q

    with ThreadPoolExecutor(max_workers=3) as ex:
        for res in ex.map(one, wells):
            well, g, c, e, d, tpa, na, tpb, nb, q = res
            rec_e, prec_e = tpa / g, tpa / na
            print(f'{well}: ground={g} cand={c} emit={e} drop={d}')
            print(f'   q dist emit:', {qi: int((q[((q == 1) | (q == 2))] == qi).sum()) for qi in range(5)})
            print(f'   EMIT   recall={rec_e:.3f} precision={prec_e:.3f} ({tpa}/{na})')
            print(f'   DROP   recall={tpb / g:.3f}  (dropped-but-real={tpb})')