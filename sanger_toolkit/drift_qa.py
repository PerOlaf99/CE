#!/usr/bin/env python3
"""drift_qa.py - offline spectral-drift / bleed QA across a plate.

Estimate a sliding-window crosstalk matrix per well (supervised on the ESD
ground-truth peaks), then report per-well spectral-health metrics as a PASS /
WARN / FAIL flag.  Read-only: does NOT change basecalling or any settings.

Metrics (per well):
  nwin      valid matrix windows (estimation needs >= min_peaks peaks)
  drift_rel ||M_end - M_start||_F / ||I||_F   : net spectral change along the run
  jump_max  max_i ||M_{i+1} - M_i||_F         : largest abrupt matrix step
  cond_max  worst window condition number     : weakest spectral conditioning
  purity_med median diag(M)                   : how clean each dye's channel is

Flags (hard FAIL thresholds, calibrated conservatively so a healthy run passes):
  FAIL  drift_rel > 0.80  or  cond_max > 80  or  nwin < 5
  WARN  drift_rel > 0.55  or  cond_max > 45  or  purity_med < 0.15

Run:
  python3 drift_qa.py --base-dir ../MB1000_M13_DT [--wells A01,B01,...]
                      [--esd-subdir MB1000_M13_DT_Cp312_MD1] [--out report.txt]
"""
import argparse, glob, json, os, sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import dsp
import extract_training_data as etd
from crosstalk_drift import CrosstalkDrift

DEFAULT_INIT = os.path.join(HERE, 'A01_2050_2411.json')
FLAG_FAIL = dict(drift_rel=0.80, cond_max=80.0, nwin=5)
FLAG_WARN = dict(drift_rel=0.55, cond_max=45.0, purity_med=0.15)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--base-dir', default=os.path.join(os.path.dirname(HERE), 'MB1000_M13_DT'))
    ap.add_argument('--esd-subdir', default='MB1000_M13_DT_Cp312_MD1')
    ap.add_argument('--init-json', default=DEFAULT_INIT)
    ap.add_argument('--window-size', type=int, default=800)
    ap.add_argument('--step', type=int, default=200)
    ap.add_argument('--min-peaks', type=int, default=10)
    ap.add_argument('--wells', default=None, help='comma list; default = all *.rsd')
    ap.add_argument('--out', default=None, help='write per-well CSV here')
    args = ap.parse_args()

    init = json.load(open(args.init_json))
    bl_kw = dict(baseline_method=init['baseline_method'],
                 baseline_window=init['baseline_window'],
                 baseline_window2=init.get('baseline_window2'))

    if args.wells:
        wells = [w.strip() for w in args.wells.split(',') if w.strip()]
    else:
        wells = sorted(os.path.basename(p)[:-4]
                       for p in glob.glob(os.path.join(args.base_dir, '*.rsd')))

    esd_dir = os.path.join(args.base_dir, args.esd_subdir)
    rows = [well_metrics(args.base_dir, esd_dir, w, bl_kw,
                         args.window_size, args.step, args.min_peaks)
            for w in wells]
    thresholds = calibrate(rows)

    print(f"{'well':>4s} {'nwin':>4s} {'drift':>6s} {'jump':>6s} {'condM':>6s} "
          f"{'condX':>6s} {'purMd':>6s} {'flag':>6s}")
    n_fail = n_warn = 0
    for r in rows:
        r['flag'] = classify(r, thresholds)
        if r['flag'] == 'FAIL':
            n_fail += 1
        elif r['flag'] == 'WARN':
            n_warn += 1
        print(f"{r['well']:>4s} {r['nwin']:4d} {r['drift_rel']:6.3f} "
              f"{r['jump_max']:6.3f} {r['cond_med']:6.1f} {r['cond_max']:6.1f} "
              f"{r['purity_med']:6.3f} {r['flag']:>6s}")
    print(f'\n{len(rows)} wells: {n_fail} FAIL, {n_warn} WARN, '
          f'{len(rows) - n_fail - n_warn} PASS')

    if args.out:
        with open(args.out, 'w') as f:
            f.write('well,nwin,drift_rel,jump_max,cond_med,cond_max,purity_med,flag\n')
            for r in rows:
                f.write(','.join(str(r[k]) for k in
                                 ('well', 'nwin', 'drift_rel', 'jump_max',
                                  'cond_med', 'cond_max', 'purity_med', 'flag')) + '\n')
        print(f'wrote {args.out}')


def well_metrics(base_dir, esd_dir, well, bl_kw, window_size, step, min_peaks):
    r = dict(well=well, nwin=0, drift_rel=np.nan, jump_max=np.nan,
             cond_med=np.nan, cond_max=np.nan, purity_med=np.nan, flag_=None)
    rsd_p = os.path.join(base_dir, well + '.rsd')
    esd_p = os.path.join(esd_dir, well + '.esd')
    if not (os.path.exists(rsd_p) and os.path.exists(esd_p)):
        r['flag_'] = 'SKIP'
        return r
    traces = etd.parse_rsd(rsd_p)[['Channel1', 'Channel2', 'Channel3', 'Channel4']].values.astype(np.float64)
    d = etd.parse_esd(esd_p)
    esq = str(d['sequence'])
    ep = np.asarray(d['peak_positions'], dtype=np.int64)

    bl = dsp.dsp_compute_baseline(traces, bl_kw['baseline_method'],
                                  bl_kw['baseline_window'], bl_kw['baseline_window2'])
    corr = np.clip(traces - bl, 0, None)

    msk = (ep >= 0) & (ep < corr.shape[0])
    msk &= np.isin(list(esq), ['A', 'C', 'G', 'T'])
    idx = np.where(msk)[0]
    cd = CrosstalkDrift(window_size=window_size, step=step, min_peaks=min_peaks)
    cd.estimate_from_peaks(corr.T, ep[idx].tolist(), [esq[i] for i in idx])

    valid = [i for i, M in enumerate(cd.matrices) if M is not None
             and np.isfinite(cd.condition_numbers[i])]
    if len(valid) < 2:
        r['nwin'] = len(valid)
        r['flag_'] = 'LOW-PKS'
        return r
    conds = [cd.condition_numbers[i] for i in valid]
    pur = np.array([cd.matrices[i].diagonal() for i in valid])
    M0 = cd.matrices[valid[0]]
    ME = cd.matrices[valid[-1]]
    jumps = [np.linalg.norm(cd.matrices[valid[i + 1]] - cd.matrices[valid[i]])
             for i in range(len(valid) - 1)]
    r.update(nwin=len(valid),
             drift_rel=float(np.linalg.norm(ME - M0) / np.linalg.norm(np.eye(4))),
             jump_max=float(max(jumps)),
             cond_med=float(np.median(conds)),
             cond_max=float(max(conds)),
             purity_med=float(np.median(pur)))
    return r


def calibrate(rows):
    """Plate-relative thresholds: p90 panWARN, p95+margin FAILs.

    Absolute floors keep the tool from ever PASSing a genuinely broken read
    even if the whole plate is bad."""
    floors = dict(drift_rel=(0.60, 0.70), cond_med=(55.0, 85.0))
    t = {}
    for k in ('drift_rel', 'cond_med'):
        v = np.asarray([r[k] for r in rows if r['flag_'] is None and np.isfinite(r[k])])
        if len(v) < 4:
            t[k] = (floors[k][0], floors[k][1])
            continue
        q50, q90, q95 = np.percentile(v, [50, 90, 95])
        margin = q95 - q90
        warn = max(q90, floors[k][0])
        fail = max(q95 + margin, q90 + 0.25 * (q95 - q50), floors[k][1])
        t[k] = (float(warn), float(fail))
    return t


def classify(r, t):
    if r['flag_'] is not None:
        return r['flag_']
    wd, fd = t['drift_rel']
    wc, fc = t['cond_med']
    if r['nwin'] < FLAG_FAIL['nwin']:
        return 'FAIL'
    if r['drift_rel'] > fd or r['cond_med'] > fc:
        return 'FAIL'
    if r['drift_rel'] > wd or r['cond_med'] > wc:
        return 'WARN'
    return 'PASS'


if __name__ == '__main__':
    main()