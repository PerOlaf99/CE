#!/usr/bin/env python3
"""mb1k_window_sweep.py - fine-finetune stage 1 for the MB1000_M13_DT plate.

Objective change vs best_web_sweep.py: score BLAST *bitscore* (length AND
identity together) and mean identity, not matched_bp alone.  The tuned
caller already wins matched (792.6 vs DLL 753.3) but trails bitscore
(1262 vs DLL 1278) purely on identity (94.4% vs 96.8%).  This sweep hunts
the global-knob combo that raises identity while keeping the tail length.

Configs are expressed relative to the shipped TUNED_CONFIG
(pullback 0.012, ema 0.10, channel_peak_bonus 1.6, window_frac (0.75,1.25)).
Every config keeps the quality gate: if the aggressive read's mean base
qual < QUAL_GATE it falls back to BASE_CONFIG (so no config can destroy a
well).  All calls are pure de-novo (rsd only, no reference/ESD).

If stage-1 global tuning plateaus, stage-2 (mb1k_window_stage2.py) will
re-call the head/tail windows separately - head/middle/tail error rates on
the tuned read are 1.9%/0.4%/3.9%, so 93% of the errors are in the outer
windows.

Usage:
    python3 mb1k_window_sweep.py [--wells held|other|all]
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(os.path.dirname(HERE), 'best_basecaller'))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), 'sanger_toolkit'))
os.environ.setdefault('TF_CPP_MIN_LOG_LEVEL', '3')

import json
import itertools
import numpy as np

from cimarron_basecaller.rsd_io import read_rsd, to_acgt_trace
from cimarron_basecaller import track_bases
from tuned_basecaller import BASE_CONFIG, QUAL_GATE

PLATE = os.path.join(os.path.dirname(HERE), 'MB1000_M13_DT')
OUTDIR = os.path.join(HERE, 'window_sweep')
os.makedirs(OUTDIR, exist_ok=True)

HELD = set('A01 A03 A05 A07 A09 A11 B02 B04 B06 B08 B10 B12 '
           'C01 C03 C05 C07 C09 C11 D02 D04 D06 D08 D10 D12 '
           'E01 E03 E05 E07 E09 E11 F02 F04 F06 F08 F10 F12 '
           'G01 G03 G05 G07 G09 G11 H02 H04 H06 H08 H10 H12'.split())


def load_wells(which):
    wells = sorted(x[:-4] for x in os.listdir(PLATE) if x.endswith('.rsd'))
    if which == 'held':
        wells = [w for w in wells if w in HELD]
    elif which == 'other':
        wells = [w for w in wells if w not in HELD]
    return wells


def call_one(rsd_path, config):
    rsd = read_rsd(rsd_path)
    trace, order = to_acgt_trace(rsd, base_order='TGCA')
    seq, quals, bands = track_bases(trace, base_order=order, **config)
    if np.asarray(quals, dtype=float).mean() < QUAL_GATE:
        seq, quals, bands = track_bases(trace, base_order=order, **BASE_CONFIG)
    return seq


def main():
    import argparse
    import time

    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--wells', default='held', choices=['held', 'other', 'all'])
    args = ap.parse_args()

    from blast_bench import blast_eval
    wells = load_wells(args.wells)
    print(f'{len(wells)} wells ({args.wells}), plate {PLATE}', flush=True)

    base = 'pullback_weight:0.012,ema_alpha:0.10,channel_peak_bonus:1.6,window_frac:(0.75,1.25)'

    def cfg(pb=0.012, ema=0.10, bonus=1.6, wfrac=(0.75, 1.25)):
        return dict(BASE_CONFIG, pullback_weight=pb, ema_alpha=ema,
                    channel_peak_bonus=bonus, window_frac=wfrac)

    # Curated stage-1 grid around the shipped tuned optimum.
    configs = [
        ('baseline tuned', cfg()),
        ('pb 0.008', cfg(pb=0.008)),
        ('pb 0.016', cfg(pb=0.016)),
        ('pb 0.020', cfg(pb=0.020)),
        ('ema 0.06', cfg(ema=0.06)),
        ('ema 0.14', cfg(ema=0.14)),
        ('bonus 1.2', cfg(bonus=1.2)),
        ('bonus 2.0', cfg(bonus=2.0)),
        ('pb.008 ema.06', cfg(pb=0.008, ema=0.06)),
        ('pb.010 ema.08', cfg(pb=0.010, ema=0.08)),
        ('pb.014 ema.12', cfg(pb=0.014, ema=0.12)),
        ('pb.008 bonus1.8', cfg(pb=0.008, bonus=1.8)),
        ('wfrac1.2 pb.008', cfg(pb=0.008, wfrac=(0.8, 1.2))),
        ('wfrac1.2', cfg(wfrac=(0.8, 1.2))),
        ('pb.006', cfg(pb=0.006)),
        ('pb.004', cfg(pb=0.004)),
    ]

    rows = []
    for name, conf in configs:
        t0 = time.time()
        tot_bits = tot_match = tot_id = 0.0
        n = 0
        per_well = []
        for w in wells:
            seq = call_one(os.path.join(PLATE, f'{w}.rsd'), conf)
            r = blast_eval(seq)
            if r is None:
                per_well.append((w, None))
                continue
            tot_bits += r['bitscore']; tot_match += r['matched']; tot_id += r['identity']
            per_well.append((w, {k: r[k] for k in
                                 ('qlen', 'matched', 'aligned', 'identity',
                                  'coverage', 'bitscore')}))
            n += 1
        dt = time.time() - t0
        row = dict(name=name, n=n,
                   bits=round(tot_bits / n, 2), matched=round(tot_match / n, 2),
                   ident=round(tot_id / n, 2), sec=round(dt, 1))
        rows.append(row)
        with open(os.path.join(OUTDIR, f'wells_{name.replace(" ", "_").replace(".", "p").replace(",", "")}.json'), 'w') as f:
            json.dump(dict(config=conf, per_well=per_well), f)
        print(f'{name:22s} bits={row["bits"]:7.1f}  matched={row["matched"]:7.1f}  '
              f'id={row["ident"]:5.2f}%  ({n} wells in {dt:.1f}s)', flush=True)

    rows.sort(key=lambda r: -r['bits'])
    print(f'\n=== best by bitscore ({args.wells}) ===')
    for r in rows:
        print(f'{r["name"]:22s} bits={r["bits"]:7.1f} matched={r["matched"]:7.1f} id={r["ident"]:5.2f}%')
    with open(os.path.join(OUTDIR, f'summary_{args.wells}.json'), 'w') as f:
        json.dump(rows, f, indent=1)


if __name__ == '__main__':
    main()