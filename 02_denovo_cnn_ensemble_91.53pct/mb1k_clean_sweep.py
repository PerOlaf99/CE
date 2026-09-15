#!/usr/bin/env python3
"""mb1k_clean_sweep.py - sweep for longest clean stretch (reference-anchored).

Unlike the bitscore sweep (which rewards total matched length), this sweep
maximizes the LONGEST contiguous error-free stretch, measured by aligning
rc(read) to M13 and counting columns with no gaps, no mismatches, and no
intervening errors.  Tolerated majority-variant columns (the documented
C→T at M13 5977 / ESD idx 308 plus other shared template variants) are
excluded.

Key insight from profiling: the clean block breaks because of
(a) early head errors (push the block start rightward = later in M13) and
(b) scattered tail errors (truncate the block at ~5994 instead of 6210).
Fix: tighter head params (higher pullback/min_prominence), moderate tail
(not as aggressive as the bitscore profile).

Usage:
    python3 mb1k_clean_sweep.py [--wells held|other|all]
"""
import os, sys, time, json, argparse

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(os.path.dirname(HERE), 'best_basecaller'))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), 'sanger_toolkit'))
os.environ.setdefault('TF_CPP_MIN_LOG_LEVEL', '3')

import numpy as np
from cimarron_basecaller.rsd_io import read_rsd, to_acgt_trace
from cimarron_basecaller import track_bases
from tuned_basecaller import BASE_CONFIG, QUAL_GATE
from blast_bench import blast_eval
from mb1k_posprofile_sweep import sw_align, revcomp
from clean_stretch import longest_clean, detect_snp_columns, load_ours, load_dll

PLATE = os.path.join(os.path.dirname(HERE), 'MB1000_M13_DT')
OUTDIR = os.path.join(HERE, 'clean_sweep')
os.makedirs(OUTDIR, exist_ok=True)
REF = None  # lazy init

HELD = set('A01 A03 A05 A07 A09 A11 B02 B04 B06 B08 B10 B12 '
           'C01 C03 C05 C07 C09 C11 D02 D04 D06 D08 D10 D12 '
           'E01 E03 E05 E07 E09 E11 F02 F04 F06 F08 F10 F12 '
           'G01 G03 G05 G07 G09 G11 H02 H04 H06 H08 H10 H12'.split())


def profile3(head_pb=0.019, head_mp=0.05, mid_pb=0.019, tail_pb=0.019,
              ema=0.10, bonus=1.4):
    """3-segment profile: head [0,0.33), mid [0.33,0.67), tail [0.67,1.0].
    All share ema/bonus/channel config; only pb and min_prominence vary."""
    base = dict(ema_alpha=ema, channel_peak_bonus=bonus)
    return {
        0.00: dict(base, pullback_weight=head_pb, min_prominence=head_mp),
        0.33: dict(base, pullback_weight=mid_pb,  min_prominence=0.05),
        1.00: dict(base, pullback_weight=tail_pb, min_prominence=0.05),
    }


def cfg(pb=0.019, ema=0.10, bonus=1.4):
    return dict(BASE_CONFIG, pullback_weight=pb, ema_alpha=ema,
                channel_peak_bonus=bonus)


def call_well_profile(rsd_path, config, profile):
    rsd = read_rsd(rsd_path)
    trace, order = to_acgt_trace(rsd, base_order='TGCA')
    seq, quals, bands = track_bases(trace, base_order=order, **config,
                                    pos_profile=profile)
    if np.asarray(quals, dtype=float).mean() < QUAL_GATE:
        seq, quals, bands = track_bases(trace, base_order=order, **BASE_CONFIG)
    return seq


def load_wells(which):
    wells = sorted(x[:-4] for x in os.listdir(PLATE) if x.endswith('.rsd'))
    if which == 'held':
        return [w for w in wells if w in HELD]
    elif which == 'other':
        return [w for w in wells if w not in HELD]
    return wells


def main():
    from blast_bench import _ref_seq
    global REF
    REF = _ref_seq()

    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--wells', default='held', choices=['held', 'other', 'all'])
    args = ap.parse_args()
    wells = load_wells(args.wells)
    print(f'{len(wells)} wells ({args.wells})', flush=True)

    # detect tolerated majority-variant columns from current tuned_calls
    print('detecting tolerated variant columns from tuned_calls...', flush=True)
    tuned_dir = os.path.join(HERE, 'tuned_calls')
    current_reads = []
    for w in wells:
        with open(os.path.join(tuned_dir, f'{w}.fasta')) as f:
            seq = ''.join(l.strip() for l in f if not l.startswith('>'))
        if len(seq) >= 30:
            current_reads.append(seq)
    tolerated = detect_snp_columns(current_reads)
    print(f'  tolerated: {len(tolerated)} column(s): {sorted(tolerated)}', flush=True)

    configs = [
        # --- controls ---
        ('flat base pb.019',  cfg(pb=0.019),                           None),
        ('flat tuned pb.008', cfg(pb=0.008, ema=0.08, bonus=1.4),     None),
        ('bitscore profile',  cfg(pb=0.008, ema=0.08, bonus=1.4),
                              {0.00: dict(ema_alpha=0.08, pullback_weight=0.008,
                                          min_prominence=0.05, channel_peak_bonus=1.4),
                               0.33: dict(ema_alpha=0.08, pullback_weight=0.008,
                                          min_prominence=0.05, channel_peak_bonus=1.4),
                               1.00: dict(ema_alpha=0.08, pullback_weight=0.001,
                                          min_prominence=0.05, channel_peak_bonus=1.4)}),
        # --- head-tight sweep (moderate tail) ---
        ('head pb.012 tail.008',  cfg(pb=0.019), profile3(head_pb=0.012, tail_pb=0.008)),
        ('head pb.019 tail.008',  cfg(pb=0.019), profile3(head_pb=0.019, tail_pb=0.008)),
        ('head pb.025 tail.008',  cfg(pb=0.019), profile3(head_pb=0.025, tail_pb=0.008)),
        ('head pb.030 tail.008',  cfg(pb=0.019), profile3(head_pb=0.030, tail_pb=0.008)),
        ('head pb.040 tail.008',  cfg(pb=0.019), profile3(head_pb=0.040, tail_pb=0.008)),
        ('head pb.050 tail.008',  cfg(pb=0.019), profile3(head_pb=0.050, tail_pb=0.008)),
        # --- best head + tail sweep ---
        ('head pb.030 tail.005',  cfg(pb=0.019), profile3(head_pb=0.030, tail_pb=0.005)),
        ('head pb.030 tail.012',  cfg(pb=0.019), profile3(head_pb=0.030, tail_pb=0.012)),
        ('head pb.030 tail.019',  cfg(pb=0.019), profile3(head_pb=0.030, tail_pb=0.019)),
        # --- head mp sweep ---
        ('head pb.030 mp.08',     cfg(pb=0.019), profile3(head_pb=0.030, head_mp=0.08)),
        ('head pb.030 mp.12',     cfg(pb=0.019), profile3(head_pb=0.030, head_mp=0.12)),
        ('head pb.030 mp.15',     cfg(pb=0.019), profile3(head_pb=0.030, head_mp=0.15)),
        # --- combined tight head+moderate tail+higher mp ---
        ('head pb.030 mp.10 tail.008',  cfg(pb=0.019),
         profile3(head_pb=0.030, head_mp=0.10, tail_pb=0.008)),
    ]

    rows = []
    for name, config, profile in configs:
        t0 = time.time()
        tot_clean = tot_bits = tot_match = 0
        n = 0
        details = []
        for w in wells:
            seq = call_well_profile(os.path.join(PLATE, f'{w}.rsd'), config, profile)
            r = blast_eval(seq)
            a, b, rs = sw_align(revcomp(seq), REF)
            lc, s1, e1 = longest_clean(a, b, rs, tolerated)
            bits = r['bitscore'] if r else 0
            match = r['matched'] if r else 0
            tot_clean += lc; tot_bits += bits; tot_match += match; n += 1
            details.append(dict(well=w, clean=lc, start=s1, end=e1,
                                bits=bits, matched=match))
        dt = time.time() - t0
        avg = tot_clean / n if n else 0
        row = dict(name=name, n=n, clean=round(avg, 1),
                   bits=round(tot_bits / n, 1), matched=round(tot_match / n, 1),
                   sec=round(dt, 1))
        rows.append(row)
        with open(os.path.join(OUTDIR,
                               f'wells_{name.replace(" ","_").replace(".","p")}.json'),
                  'w') as f:
            json.dump(dict(config=config,
                           profile={str(k): v for k, v in (profile or {}).items()},
                           per_well=details), f)
        print(f'{name:30s} clean={avg:6.1f}  bits={row["bits"]:7.1f}  matched={row["matched"]:6.1f}'
              f'  ({row["sec"]:.0f}s)', flush=True)

    rows.sort(key=lambda r: -r['clean'])
    print(f'\n=== best by longest clean ({args.wells}) ===')
    for r in rows:
        print(f'{r["name"]:30s} clean={r["clean"]:6.1f}  bits={r["bits"]:7.1f}  matched={r["matched"]:6.1f}')
    with open(os.path.join(OUTDIR, f'summary_{args.wells}.json'), 'w') as f:
        json.dump(rows, f, indent=1)


if __name__ == '__main__':
    main()
