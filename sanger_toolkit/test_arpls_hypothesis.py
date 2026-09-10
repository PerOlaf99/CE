#!/usr/bin/env python3
import os, sys, json
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), '99_archive'))
os.environ.setdefault('TF_CPP_MIN_LOG_LEVEL', '3')
import dsp_core
from basecall import pc_call_bases_greedy
import optimize_windows_esd as owe
from Bio import Align

RAW_ROOT = os.path.dirname(HERE)

raw, esd_seq, esd_pp = owe.load_well(os.path.join(RAW_ROOT, 'MB1000_M13_DT'), 'A01', owe.ESD_SUBDIR)


def call(raw, params, region, greedy_knobs):
    _, _, _, _, separated, _ = dsp_core.full_pipeline(
        raw, [0, 0, 0, 0],
        params['baseline_method'], params['baseline_window'], params['smooth_method'],
        params['smooth_window'], params['smooth_order'], params['matrix'],
        baseline_window2=params.get('baseline_window2'),
        matrix_apply_point=params.get('matrix_apply_point', 'smoothed'))
    shifts = list(params['mobility_shifts'])
    pos, seq, _, _ = pc_call_bases_greedy(
        separated, shifts,
        window=max(1, int(round(greedy_knobs.get('min_distance', 5)))),
        min_frac=greedy_knobs.get('prominence_frac', 0.1),
        norm_window=max(1, int(round(greedy_knobs.get('norm_window', 200)))),
        region=region)
    return ''.join(b for b in seq if b in 'ACGT')


def global_score(seq, target):
    al = Align.PairwiseAligner()
    al.mode = 'global'
    al.match_score = 2
    al.mismatch_score = -1
    al.open_gap_score = -2
    al.extend_gap_score = -1
    a, b = al.align(seq, target)[0]
    matches = sum(1 for x, y in zip(a, b) if x == y and x != '-')
    non_gap = sum(1 for x, y in zip(a, b) if x != '-' and y != '-')
    return matches, non_gap


def local_sw_identity(seq, target):
    q, r = seq, target
    m, n = len(q), len(r)
    if m == 0 or n == 0:
        return 0, 0, 0.0
    match, mismatch, gap = 2, -1, -2
    dp = np.zeros((m + 1, n + 1), dtype=np.int32)
    best = 0
    for i in range(1, m + 1):
        qi = q[i - 1]
        for j in range(1, n + 1):
            diag = dp[i - 1, j - 1] + (match if qi == r[j - 1] else mismatch)
            up = dp[i - 1, j] + gap
            left = dp[i, j - 1] + gap
            v = max(0, diag, up, left)
            dp[i, j] = v
            if v > best:
                best = v
    return best, m, n


manual = json.load(open(os.path.join(HERE, 'A01_2050_2411.json')))
manual_mtx = np.array(manual['matrix'])
opt = json.load(open(os.path.join(HERE, 'opt_windows_esd/A01_[2050_2750].json')))

BASE = dict(mobility_shifts=list(manual['mobility_shifts']), matrix=manual_mtx,
            matrix_apply_point=manual.get('matrix_apply_point', 'smoothed'))
GK = dict(min_distance=5.0, prominence_frac=0.1, norm_window=200)

settings = {
    'MANUAL (RollingMedian/Butter)': dict(BASE, baseline_method='Rolling Median',
                                           baseline_window=510, baseline_window2=27,
                                           smooth_method='Butterworth', smooth_window=4, smooth_order=5),
    'HYPOTHESIS arPLS/Butter (100k:200, 9:4)': dict(BASE, baseline_method='arPLS',
                                           baseline_window=100000, baseline_window2=200,
                                           smooth_method='Butterworth', smooth_window=9, smooth_order=4),
    'OPTIMIZED w1 (RollingMedian/LOWESS)': dict(BASE, baseline_method=opt['baseline_method'],
                                           baseline_window=opt['baseline_window'],
                                           baseline_window2=opt.get('baseline_window2', 0),
                                           smooth_method=opt['smooth_method'],
                                           smooth_window=opt['smooth_window'],
                                           smooth_order=opt['smooth_order'],
                                           matrix_apply_point=opt['matrix_apply_point'],
                                           mobility_shifts=opt['mobility_shifts'],
                                           matrix=np.array(opt['matrix'])),
}

# also test HYPOTHESIS with the optimized matrix+knobs to isolate the DSP effect
opt_gk = dict(min_distance=opt['min_distance'], prominence_frac=opt['prominence_frac'],
              norm_window=opt['norm_window'])
hyp_optmat = dict(settings['HYPOTHESIS arPLS/Butter (100k:200, 9:4)'])
hyp_optmat['matrix'] = np.array(opt['matrix'])
hyp_optmat['matrix_apply_point'] = opt['matrix_apply_point']
hyp_optmat['mobility_shifts'] = opt['mobility_shifts']

regions = {
    'first 100 scans [2050,2150]': (95, 2150 - 2008),
    'full window1 [2050,2750]': (2050, 2750 - 2008),
}

for rname, (s0, e0) in regions.items():
    region = (max(0, s0 - 2008), e0 - 2008)
    esdwin = owe.esd_window(esd_seq, esd_pp, s0, e0)
    print(f'\n########## {rname}  esd_win_len={len(esdwin)} ##########')
    print(f'  esdwin: {esdwin}')
    for name, params in settings.items():
        gk = opt_gk if 'OPTIMIZED' in name else GK
        seq = call(raw, params, region, gk)
        m, ng = global_score(seq, esdwin)
        sw, sw_m, sw_n = local_sw_identity(seq, esdwin)
        ident = m / ng if ng else 0
        print(f'  {name:38s} len={len(seq):4d}  gmatch={m:4d} gng={ng:4d} gid={100*ident:5.1f}%  swscore={sw}')
    # hypothesis with optimized matrix/knobs too
    gk = opt_gk
    seq = call(raw, hyp_optmat, region, gk)
    m, ng = global_score(seq, esdwin)
    sw, _, _ = local_sw_identity(seq, esdwin)
    ident = m / ng if ng else 0
    print(f'  {"HYP + opt matrix/knobs":38s} len={len(seq):4d}  gmatch={m:4d} gng={ng:4d} gid={100*ident:5.1f}%  swscore={sw}')
