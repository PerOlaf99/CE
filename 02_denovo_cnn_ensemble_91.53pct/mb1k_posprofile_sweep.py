#!/usr/bin/env python3
"""mb1k_posprofile_sweep.py - position-profile (time-varying parameter) sweep.

Stage-2 honest form of the abandoned windowed tail splice: instead of
re-calling the tail on a mid-trace slice (track_bases stalls there), the
parameters themselves become a function of read position via the new
`pos_profile` kwarg on track_bases (ema_alpha / pullback_weight /
min_prominence / channel_peak_bonus, linearly interpolated across the
read).  The tail third carries ~63% of residual errors (3.9% error-rate vs
0.4% in the middle), so the sweep asks which tail shape actually lowers
that rate without giving up bitscore.

Profiles are defined as {read_fraction: {param: value}} breakpoints that
must span 0.0 -> 1.0.  A flat profile reproduces the current TUNED_CONFIG
byte-for-byte (regression-gated), and it scores as the control.

Metrics per config: BLAST bitscore (authoritative), matched bp, identity,
plus a read-third error decomposition (head/mid/tail error counts and
rates from a needleman-wunsch alignment to M13mp18).

Usage:
    python3 mb1k_posprofile_sweep.py [--wells held|other|all]
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(os.path.dirname(HERE), 'best_basecaller'))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), 'sanger_toolkit'))
os.environ.setdefault('TF_CPP_MIN_LOG_LEVEL', '3')

import json
import argparse
import time

import numpy as np

from cimarron_basecaller.rsd_io import read_rsd, to_acgt_trace
from cimarron_basecaller import track_bases
from mb1k_window_sweep import cfg, load_wells, HELD
from tuned_basecaller import BASE_CONFIG, QUAL_GATE
from blast_bench import blast_eval, _ref_seq

PLATE = os.path.join(os.path.dirname(HERE), 'MB1000_M13_DT')
OUTDIR = os.path.join(HERE, 'posprofile_sweep')
os.makedirs(OUTDIR, exist_ok=True)

BASE_KW = cfg(pb=0.008, ema=0.08, bonus=1.4)  # current tuned scalars


def ramp(start, mid, end, end_frac=1.0):
    """3-breakpoint profile: start at 0.0, flat [0,0.5] to `mid`, then ramp
    to `end` by `end_frac`.  Constant params stay flat everywhere."""
    return {0.0: start, 0.5: mid, end_frac: end}


def tail_profile(**tail):
    """Profile with the mid-read scalars (BASE_KW) until frac 0.5, ramping
    only the given params toward their tail value by end of read."""
    d0 = dict(ema_alpha=0.08, pullback_weight=0.008, min_prominence=0.05,
              channel_peak_bonus=1.4)
    dm = dict(d0)
    dt = dict(d0)
    for k, v in tail.items():
        d0[k], dm[k], dt[k] = d0[k], dm[k], v
    return {0.0: d0, 0.5: dm, 1.0: dt}


# ---- smith-waterman (local, linear gap) + read-third error split -------
# Read is a ~1kb substring of the 7249bp M13 ref, so GLOBAL alignment
# mis-scores (entire-read matches outweigh the correct offset's leading
# gap).  Local alignment skips the ref prefix for free and clips only the
# read's own unaligned ends (which auto_trim mostly removes anyway).
_MATCH, _MIS, _GAP = 2, -1, -2


def sw_align(q, r):
    """Local SW of q vs r.  Returns (aligned_q, aligned_r, ref_start) where
    ref_start is the 0-based index in `r` of the first aligned ref base
    (absolute FASTA coordinate, since the local alignment doesn't start at
    ref position 0)."""
    n, m = len(q), len(r)
    if n == 0 or m == 0:
        return '', '', 0
    dp = np.zeros((n + 1, m + 1), np.int16)
    for i in range(1, n + 1):
        same = np.frombuffer(q[i - 1].encode(), np.uint8) == np.frombuffer(r.encode(), np.uint8)
        diag = dp[i - 1, :-1] + np.where(same, _MATCH, _MIS)
        up = dp[i - 1, 1:] + _GAP
        left = dp[i, :-1] + _GAP
        dp[i, 1:] = np.maximum.reduce([diag, up, left, np.zeros_like(diag)])
    i, j = (int(x) for x in np.unravel_index(dp.argmax(), dp.shape))
    score = dp[i, j]
    if score < _MATCH * 3:
        return '', '', 0
    aq, ar = [], []
    while i > 0 and j > 0 and dp[i, j] > 0:
        if q[i - 1] == r[j - 1] and dp[i, j] == dp[i - 1, j - 1] + _MATCH:
            aq.append(q[i - 1]); ar.append(r[j - 1]); i -= 1; j -= 1
        elif i > 0 and j > 0 and dp[i, j] == dp[i - 1, j - 1] + _MIS and q[i - 1] != r[j - 1]:
            aq.append(q[i - 1]); ar.append(r[j - 1]); i -= 1; j -= 1
        elif i > 0 and dp[i, j] == dp[i - 1, j] + _GAP:
            aq.append(q[i - 1]); ar.append('-'); i -= 1
        else:
            aq.append('-'); ar.append(r[j - 1]); j -= 1
    return ''.join(reversed(aq)), ''.join(reversed(ar)), j


def errors_by_third(q, r):
    """Count errors in each third of the aligned READ (query) position."""
    counts = [0, 0, 0]
    qi = 0
    nq = sum(1 for a in q if a != '-')
    for a, b in zip(q, r):
        if a != '-':
            if b == '-' or (a != b and b != '-'):
                counts[min(2, 3 * qi // max(1, nq))] += 1
            qi += 1
    return counts, nq


REF = _ref_seq()
_RC = str.maketrans('ACGTN', 'TGCAN')


def revcomp(s):
    return s.translate(_RC)[::-1]


def call_one(rsd_path, config, profile):
    rsd = read_rsd(rsd_path)
    trace, order = to_acgt_trace(rsd, base_order='TGCA')
    seq, quals, bands = track_bases(trace, base_order=order, **config,
                                    pos_profile=profile)
    if np.asarray(quals, dtype=float).mean() < QUAL_GATE:
        seq, quals, bands = track_bases(trace, base_order=order, **BASE_CONFIG)
    return seq


def ramp_profile(pb_tail=0.001, ramp_from=0.5, ema_tail=0.08):
    """Looser pullback (and optionally faster EMA) in the read tail, starting
    the ramp at `ramp_from` fraction of the read."""
    d0 = dict(ema_alpha=0.08, pullback_weight=0.008, min_prominence=0.05,
              channel_peak_bonus=1.4)
    dm = dict(d0)
    dt = dict(d0, pullback_weight=pb_tail, ema_alpha=ema_tail)
    return {0.0: d0, ramp_from: dm, 1.0: dt}


def profile_table():
    """Profiles: flat control + directional tail ramps on the current tuned
    scalar base (BASE_KW), plus a couple of combined regimes."""
    f0 = dict(ema_alpha=0.08, pullback_weight=0.008, min_prominence=0.05,
              channel_peak_bonus=1.4)
    return [
        ('flat (control)', dict(BASE_KW), {0.0: dict(f0), 1.0: dict(f0)}),
        # ---------------- round 2: around the pb->0.001 winner --------------
        ('pb .001 rampf.33', dict(BASE_KW), ramp_profile(pb_tail=0.001, ramp_from=0.33)),
        ('pb .001 rampf.50', dict(BASE_KW), ramp_profile(pb_tail=0.001, ramp_from=0.5)),
        ('pb .001 rampf.67', dict(BASE_KW), ramp_profile(pb_tail=0.001, ramp_from=0.67)),
        ('pb .0005 rampf.50', dict(BASE_KW), ramp_profile(pb_tail=0.0005, ramp_from=0.5)),
        ('pb .001 ema.25 rampf.50', dict(BASE_KW), ramp_profile(pb_tail=0.001, ramp_from=0.5, ema_tail=0.25)),
        ('pb .002 rampf.50', dict(BASE_KW), ramp_profile(pb_tail=0.002, ramp_from=0.5)),
    ]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--wells', default='held', choices=['held', 'other', 'all'])
    args = ap.parse_args()

    wells = load_wells(args.wells)
    print(f'{len(wells)} wells ({args.wells})', flush=True)

    rows = []
    for name, config, profile in profile_table():
        t0 = time.time()
        tot_bits = tot_match = tot_id = 0.0
        errs = [0, 0, 0]
        tot_third = [0, 0, 0]
        n = per_well = 0
        details = []
        for w in wells:
            seq = call_one(os.path.join(PLATE, f'{w}.rsd'), config, profile)
            r = blast_eval(seq)
            if r is None:
                details.append((w, None))
                continue
            tot_bits += r['bitscore']; tot_match += r['matched']; tot_id += r['identity']
            n += 1
            q, s, _ = sw_align(revcomp(seq), REF)
            cnt, nq = errors_by_third(q, s)
            for i in range(3):
                errs[i] += cnt[i]
                tot_third[i] += max(1, nq // 3)
            details.append((w, cnt, nq))
            per_well += nq
        dt = time.time() - t0
        row = dict(name=name, n=n,
                   bits=round(tot_bits / n, 2), matched=round(tot_match / n, 2),
                   ident=round(tot_id / n, 2), sec=round(dt, 1),
                   err_rate=round(100.0 * sum(errs) / per_well, 2),
                   tail_rate=round(100.0 * errs[2] / tot_third[2], 2),
                   mid_rate=round(100.0 * errs[1] / tot_third[1], 2),
                   head_rate=round(100.0 * errs[0] / tot_third[0], 2),
                   tail_err=errs[2], mid_err=errs[1], head_err=errs[0])
        rows.append(row)
        with open(os.path.join(OUTDIR, f'wells_{name.replace(" ", "_").replace("->", "to").replace(".", "p")}.json'), 'w') as f:
            json.dump(dict(config=config, profile={str(k): v for k, v in profile.items()},
                           per_well=details), f)
        print(f'{name:26s} bits={row["bits"]:7.1f}  matched={row["matched"]:6.1f}  '
              f'id={row["ident"]:5.2f}%  | err h/m/t {row["head_rate"]:4.1f}/'
              f'{row["mid_rate"]:4.1f}/{row["tail_rate"]:4.1f}%  ({row["sec"]:.0f}s)',
              flush=True)

    rows.sort(key=lambda r: -r['bits'])
    print(f'\n=== best by bitscore ({args.wells}); control = flat ===')
    for r in rows:
        print(f'{r["name"]:26s} bits={r["bits"]:7.1f} matched={r["matched"]:6.1f} '
              f'id={r["ident"]:5.2f}%  tail_err_rate={r["tail_rate"]:4.1f}%')
    with open(os.path.join(OUTDIR, f'summary_{args.wells}.json'), 'w') as f:
        json.dump(rows, f, indent=1)


if __name__ == '__main__':
    main()