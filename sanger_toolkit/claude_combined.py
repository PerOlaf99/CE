#!/usr/bin/env python3
"""claude_combined.py - evaluate the Claude cimarron_basecaller package
combined with our project's BLAST-vs-M13 benchmark and SCF ground truth.

The Claude package (from /home/per/Nedlastinger/Claude/cimarron_basecaller)
provides an independent spacing-tracking base caller that with gaussian
reconstruction + Mott quality trimming beats Cimarron 3.12's DLL on BOTH
real-BLAST metrics (identity AND coverage) on the high-confidence core.

Usage:
    python3 sanger_toolkit/claude_combined.py [--wells A01,A02,...] [--config balanced|gauss|gauss_mott]

Defaults: all 12 A-row wells, config=gauss_mott (cut 0.93).
"""
import argparse
import sys
import os

sys.path.insert(0, '/home/per/Nedlastinger/Claude/cimarron_basecaller')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np

from cimarron_basecaller.rsd_io import read_rsd, to_acgt_trace
from cimarron_basecaller import track_bases
from cimarron_basecaller.scf_io import read_scf
from cimarron_basecaller.scoring import score_against_truth
from blast_check import blast_eval

BASE_ORDER = 'TGCA'
WELLS = ['A01', 'A02', 'A03', 'A04', 'A05', 'A06',
         'A07', 'A08', 'A09', 'A10', 'A11', 'A12']

CONFIGS = {
    'balanced':   {},
    'gauss':      dict(use_gaussian_reconstruction=True, window_frac=(0.8, 1.2)),
    'gauss_mott': dict(use_gaussian_reconstruction=True, window_frac=(0.8, 1.2),
                       trim_method='mott', mott_quality_cutoff=0.93),
}


def eval_well(well, rsd_dir, scf_dir, kw):
    rsd = read_rsd(os.path.join(rsd_dir, f'{well}.rsd'))
    trace, order = to_acgt_trace(rsd, base_order=BASE_ORDER)
    seq, quals, bands = track_bases(trace, base_order=order,
                                    mobility_shifts='default', **kw)
    bl = blast_eval(seq, 'megablast')
    out = {'n': len(seq)}
    out.update({k: (bl[k] if bl else float('nan')) for k in ('pident', 'coverage')})
    scf_path = os.path.join(scf_dir, f'{well}.scf')
    if os.path.exists(scf_path):
        truth = read_scf(scf_path).bases
        s = score_against_truth(seq, truth)
        out['vsSCF'] = s['identity_pct']
        mq = blast_eval(truth, 'megablast')
        out['DLLid'] = mq['pident'] if mq else float('nan')
        out['DLLcov'] = mq['coverage'] if mq else float('nan')
    else:
        out['vsSCF'] = float('nan')
        out['DLLid'] = float('nan')
        out['DLLcov'] = float('nan')
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--wells', default=','.join(WELLS))
    ap.add_argument('--config', default='gauss_mott', choices=list(CONFIGS))
    ap.add_argument('--rsd-dir', default=None)
    ap.add_argument('--scf-dir', default='99_archive/Data/MB1000_M13_DT_Cp312_MD1/SCF')
    args = ap.parse_args()

    rsd_dir = args.rsd_dir or 'MB1000_M13_DT'
    wells = [w for w in args.wells.split(',') if w]
    kw = CONFIGS[args.config]

    rows = []
    for well in wells:
        rows.append((well, eval_well(well, rsd_dir, args.scf_dir, kw)))

    print(f"config={args.config}  (id/cov = real megablast vs M13; vsSCF = per-base vs ground truth)")
    print(f"{'well':5s} {'n':>4s} {'id':>7s} {'cov':>7s} {'vsSCF':>7s} {'DLLid':>7s} {'DLLcov':>7s}")
    for well, r in rows:
        print(f"{well:5s} {r['n']:4d} {r['pident']:7.2f} {r['coverage']:7.2f} "
              f"{r['vsSCF']:7.2f} {r['DLLid']:7.2f} {r['DLLcov']:7.2f}")
    ids = [r['pident'] for _, r in rows]
    covs = [r['coverage'] for _, r in rows]
    dids = [r['DLLid'] for _, r in rows]
    dcovs = [r['DLLcov'] for _, r in rows]
    print(f"mean  id={np.nanmean(ids):.2f} cov={np.nanmean(covs):.2f} | DLL id={np.nanmean(dids):.2f} cov={np.nanmean(dcovs):.2f}")
    print(f"wins: id>DLL {sum(id > d and not np.isnan(d) for id, d in zip(ids, dids))}/{len(ids)}, "
          f"cov>DLL {sum(c > d and not np.isnan(d) for c, d in zip(covs, dcovs))}/{len(covs)}")


if __name__ == '__main__':
    main()