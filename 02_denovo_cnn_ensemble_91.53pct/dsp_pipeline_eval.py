#!/usr/bin/env python3
"""dsp_pipeline_eval.py - held-48 evaluation of the Cimarron DSP-pipeline
preprocessing path (dsp_full_pipeline with _TUNED_SSM) feeding track_bases,
compared against current production (TUNED_PROFILE) and the DLL target, on
longest clean stretch, bitscore, and matched bp.
"""
import os, sys, time, json, argparse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'best_basecaller'))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'sanger_toolkit'))
os.environ.setdefault('TF_CPP_MIN_LOG_LEVEL', '3')

import numpy as np
from cimarron_basecaller.rsd_io import read_rsd, to_acgt_trace
from cimarron_basecaller import track_bases
from tuned_basecaller import TUNED_CONFIG, BASE_CONFIG, QUAL_GATE
from blast_bench import blast_eval, _ref_seq
from mb1k_posprofile_sweep import sw_align, revcomp
from clean_stretch import load_ours, load_dll, longest_clean, detect_snp_columns

PLATE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'MB1000_M13_DT')
HELD = set('A01 A03 A05 A07 A09 A11 B02 B04 B06 B08 B10 B12 '
           'C01 C03 C05 C07 C09 C11 D02 D04 D06 D08 D10 D12 '
           'E01 E03 E05 E07 E09 E11 F02 F04 F06 F08 F10 F12 '
           'G01 G03 G05 G07 G09 G11 H02 H04 H06 H08 H10 H12'.split())

from constants import _TUNED_SSM
from cimarrontv import dsp_full_pipeline

TGCA2ACGT = [3, 2, 1, 0]


def call_dsp(rsd_path, mob=(5, 11, 10, 10), ssm=_TUNED_SSM, smooth_win=1, smooth_samples=2,
             pb=0.008, ema=0.08, bonus=1.4, baseline_win=151):
    rsd = read_rsd(rsd_path)
    raw = rsd.trace.astype(np.float64)
    _, _, _, sep = dsp_full_pipeline(
        raw, list(mob), 'AsyLS', 50010, 'Butterworth', 5, 9, ssm,
        baseline_window2=1, matrix_apply_point='smoothed')
    sep_acgt = sep[:, TGCA2ACGT]
    seq, quals, bands = track_bases(
        sep_acgt, base_order='ACGT', spectral_separation_matrix=None,
        smoothing_window=smooth_samples, baseline_window=baseline_win,
        pullback_weight=pb, ema_alpha=ema, channel_peak_bonus=bonus,
    )
    return seq


def call_prod(rsd_path):
    rsd = read_rsd(rsd_path)
    trace, order = to_acgt_trace(rsd, base_order='TGCA')
    seq, quals, bands = track_bases(trace, base_order=order, **TUNED_CONFIG)
    if np.asarray(quals, dtype=float).mean() < QUAL_GATE:
        seq, quals, bands = track_bases(trace, base_order=order, **BASE_CONFIG)
    return seq


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--wells', default='held', choices=['held', 'other', 'all'])
    ap.add_argument('--use-quality-gate', action='store_true')
    args = ap.parse_args()
    REF = _ref_seq()

    wells = sorted(x[:-4] for x in os.listdir(PLATE) if x.endswith('.rsd'))
    if args.wells == 'held':
        wells = [w for w in wells if w in HELD]
    elif args.wells == 'other':
        wells = [w for w in wells if w not in HELD]

    print(f'building tolerated SNP set from tuned_calls ({len(wells)} wells)...', flush=True)
    reads = [load_ours(w) for w in wells]
    tolerated = detect_snp_columns(reads)
    print(f'  {len(tolerated)} tolerated columns: {sorted(tolerated)}', flush=True)

    rows = []
    for w in wells:
        r = {}
        r['dll'] = load_dll(w)
        r['prod'] = load_ours(w)
        t0 = time.time()
        r['dsp'] = call_dsp(os.path.join(PLATE, f'{w}.rsd'))
        r['dsp_ms'] = (time.time() - t0) * 1000
        row = {'well': w, 'len_dll': len(r['dll']), 'len_prod': len(r['prod']), 'len_dsp': len(r['dsp'])}
        for key in ('dll', 'prod', 'dsp'):
            seq = r[key]
            if len(seq) < 30:
                row[f'{key}_clean'] = 0; row[f'{key}_bits'] = 0
                row[f'{key}_match'] = 0; continue
            evalr = blast_eval(seq)
            a, b, rs = sw_align(revcomp(seq), REF)
            lc, s1, e1 = longest_clean(a, b, rs, tolerated)
            row[f'{key}_clean'] = lc
            row[f'{key}_bits'] = evalr['bitscore'] if evalr else 0
            row[f'{key}_match'] = evalr['matched'] if evalr else 0
        rows.append(row)

    print(f'\n=== {args.wells} ({len(wells)} wells) ===')
    print(f'{"caller":<8s} {"longest clean":>14s} {"bitscore":>10s} {"matched":>9s}')
    for key in ('dsp', 'prod', 'dll'):
        n = sum(1 for r in rows if r.get(f'{key}_clean') is not None)
        avg_clean = sum(r[f'{key}_clean'] for r in rows) / n
        avg_bits = sum(r[f'{key}_bits'] for r in rows) / n
        avg_match = sum(r[f'{key}_match'] for r in rows) / n
        print(f'{key:<8s} {avg_clean:>14.1f} {avg_bits:>10.1f} {avg_match:>9.1f}')

    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dsp_pipeline_eval',
                       f'wells_{args.wells}.json')
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, 'w') as f:
        json.dump(rows, f, indent=1)
    print(f'\nwrote {out}')


if __name__ == '__main__':
    main()