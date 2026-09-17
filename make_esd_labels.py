#!/usr/bin/env python3
"""make_esd_labels.py - split-aware ground-truth (scan, base) labels.

For every well on the M13 plate this generates a *near-perfect* label row
whose positions are the PHYSICAL peak scans in the mobility-aligned separated
trace (the frame the greedy caller and the CNN operate in), and whose base
letters are the TRUE M13 reference.  Uniquely, it also emits labels for the
bases the ESD/.esd caller MISSED (deletion columns in the semiglobal
alignment to M13, i.e. the shoulders/close peaks it cannot resolve) at
interpolated-and-snapped scan positions.

This is the label generator behind this idea:

  "train a caller to recognize shoulders and peaks closer together than 5;
   correct the ESD where it makes mistakes - we know what it should be."

Pipeline per well:
  1. read_rsd -> raw 4-channel trace
  2. canonical DSP (AsyLS 50010, Butterworth 5/9, V10 SSM at 'smoothed'),
     then per-channel mobility shifts applied -> shifted frame = physical
     peak frame (record->scan offset is USED here, unlike the .esd's p+10
     bias)
  3. seed_sw_align the ESD sequence to the M13 reference (read orientation)
  4. walk the alignment:
       matched col        -> base = TRUE M13, scan = physical apex of that
                             base's channel near the ESD peak
       ref-only col (-/-) -> ESD missed it (split / shoulder): scan
                             interpolated from flanking matched peaks by
                             reference-column index, then snapped to a real
                             peak in that channel when one exists
       query-only col     -> ESD overcall vs M13: skipped (counted)
  5. save scans/bases/source/well + per-well stats to npz

Output npz fields:
  wells    (S8)  per-label well id
  scans    (i4)  physical scan of each label
  bases    (S1)  true M13 base (ACGT)
  esd_bases(S1)  ESD's call at that column ('' for split columns)
  source   (S1)  'e' = ESD-matched column, 's' = split (ESD missed)
  meta     per-well summary dict

Usage:
  python3 make_esd_labels.py [--wells A01,B02] [--out m13_split_labels.npz]
"""
import argparse
import json
import os
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import cimarrontv as cim
from extract_m13_clean_training import load_clean_ref, seed_sw_align

# Read-orientation M13 base -> separated-channel index.  Channel order is
# the instrument's BASE_OF_DYE ('T','G','C','A'); the M13 labels are the
# TRUE bases the caller must emit.
BASE_TO_CH = {'T': 0, 'G': 1, 'C': 2, 'A': 3}
LABELS = 'ACGT'
V10_SSM = np.array([[1.0, 1.00, 0.26, 0.46],
                    [0.07, 1.00, 0.075, 0.006],
                    [0.38, 0.33, 1.00, 1.52],
                    [0.27, 0.26, 0.189, 1.00]], dtype=np.float64)
MOBILITY = (5, 11, 10, 10)

# ESD peak_positions carry a fixed ~+10 scan bias relative to the physical
# separated-trace apex (record->scan = 1998 vs label->record = 2008).  The
# apex search window is therefore biased backward so a matched ESD peak
# locks onto the physical peak rather than its own biased position.
ESD_PEAK_BACK = 15
ESD_PEAK_FWD = 4
MIN_N_LABELS = 100
SPLIT_SNAP_WIN = 6


def snap_channel_apex(shifted_all, ch, p, back=2, fwd=15, n_scans=None):
    """Return the argmax scan of channel ``ch`` inside [p-back, p+fwd] on the
    shifted (mobility-aligned) separated trace.  Clipped to the trace."""
    if n_scans is None:
        n_scans = len(shifted_all[ch])
    lo = max(0, p - back)
    hi = min(n_scans, p + fwd + 1)
    if hi <= lo:
        return int(np.clip(p, 0, n_scans - 1))
    seg = shifted_all[ch][lo:hi]
    k = int(np.argmax(seg))
    if seg[k] <= 0:
        return int(np.clip(p, 0, n_scans - 1))
    return lo + k


def interpolate_missing(scans, bases, src, misses, n_refs, shifted):
    """Fill scan=None rows (ESD missed a ref base) by linear interpolation in
    reference-column index between flanking rows that DO have a scan, then
    snap onto a physical peak in that base's channel."""
    idx = [i for i, s in enumerate(scans) if s is not None]
    if not idx:
        return scans
    # median spacing of known rows in the local region, for head/tail fills
    known = np.array([scans[i] for i in idx], dtype=np.int64)
    sp = float(np.median(np.diff(known))) if len(known) > 4 else 10.0
    for i in misses:
        base = bases[i]
        ch = BASE_TO_CH.get(base)
        if ch is None:
            continue
        prev = [j for j in idx if j < i]
        nxt = [j for j in idx if j > i]
        if prev and nxt:
            a, b = prev[-1], nxt[0]
            t = (i - a) / max(1, (b - a))
            p = int(round(scans[a] + t * (scans[b] - scans[a])))
            # stay strictly between flanking physical apexes
            lo = max(scans[a] + (i - a), p - SPLIT_SNAP_WIN)
            hi = min(scans[b] - (b - i), p + SPLIT_SNAP_WIN)
        elif prev and not nxt:                      # tail: last known + spacing
            a = prev[-1]
            p = int(round(scans[a] + sp * (i - a)))
            lo, hi = max(0, p - SPLIT_SNAP_WIN), p + SPLIT_SNAP_WIN
        elif nxt and not prev:                      # head: first known - spacing
            b = nxt[0]
            p = int(round(scans[b] - sp * (b - i)))
            lo, hi = max(0, p - SPLIT_SNAP_WIN), p + SPLIT_SNAP_WIN
        else:
            continue
        if hi <= lo:
            lo = max(0, p - 2)
            hi = lo + 4
        scans[i] = snap_channel_apex(shifted, ch, (lo + hi) // 2,
                                     back=2, fwd=hi - lo)
        src[i] = 's'
    return scans


def extract_well(well, ref_rc, raw_dir='MB1000_M13_DT',
                 gt_dir='ground_truth/MB1000_M13_DT_Cp312_MD1'):
    """Generate (scan, true-base, esd-base, source, stats) rows for one well."""
    rsd_path = os.path.join(HERE, raw_dir, f'{well}.rsd')
    esd_path = os.path.join(HERE, gt_dir, f'{well}.esd')
    if not (os.path.exists(rsd_path) and os.path.exists(esd_path)):
        return None
    ch_raw, _ = cim.read_rsd(rsd_path)
    if ch_raw.shape[0] == 4 and ch_raw.shape[1] >= 4:
        ch_raw = ch_raw.T                          # -> (N,4)
    _, _, _, separated = cim.dsp_full_pipeline(
        ch_raw, MOBILITY,
        baseline_method='AsyLS', baseline_window=50010,
        smooth_method='Butterworth', smooth_window=5, smooth_order=9,
        matrix=V10_SSM, matrix_apply_point='smoothed')

    shifted = [cim.dsp_shift_channel(separated[:, ch], int(MOBILITY[ch]))
               for ch in range(4)]
    n_scans = len(separated)

    d = cim.read_esd(esd_path)
    esd_seq = d['sequence']
    esd_peaks = np.asarray(d['peak_positions'], dtype=np.int64)
    ed_q = ''.join(c for c in esd_seq if c in 'ACGT')
    ed_idx = [i for i, c in enumerate(esd_seq) if c in 'ACGT']
    if len(ed_q) < 60:
        return None
    al, bl = seed_sw_align(ed_q, ref_rc)
    if al is None:
        return None

    scans, bases, esd_b, src = [], [], [], []
    over_scans = []
    qi = 0
    n_match = n_mism = n_over = n_split = 0
    for a, b in zip(al, bl):
        if a == '-' and b == '-':
            continue
        if a != '-' and b == '-':
            n_over += 1                             # ESD overcall vs M13
            if qi < len(ed_idx):
                over_scans.append(int(esd_peaks[ed_idx[qi]]))
            qi += 1
            continue
        if a == '-' and b != '-':
            scans.append(None)                      # ref base ESD missed
            bases.append(b)
            esd_b.append('')
            src.append('?')
            n_split += 1
            continue
        # matched column: keep TRUE base at the physical apex of its channel
        ch = BASE_TO_CH.get(b)
        p = int(esd_peaks[ed_idx[qi]]) if qi < len(ed_idx) else int(esd_peaks[-1])
        scan = snap_channel_apex(shifted, ch, p,
                                 back=ESD_PEAK_BACK, fwd=ESD_PEAK_FWD,
                                 n_scans=n_scans) if ch is not None else p
        scans.append(scan)
        bases.append(b)
        esd_b.append(a)
        src.append('e')
        n_match += 1
        if a != b:
            n_mism += 1
        qi += 1

    misses = [i for i, s in enumerate(scans) if s is None]
    if misses:
        scans = interpolate_missing(scans, bases, src, misses, bl, shifted)
    n_pending = sum(1 for s in scans if s is None)

    scans_arr = np.array([int(s) for s in scans], dtype=np.int64)
    good = (scans_arr >= 0) & (scans_arr < n_scans)
    if good.sum() < MIN_N_LABELS:
        return None

    stats = dict(n_match=n_match, n_mism=n_mism, n_over=n_over,
                 n_split=n_split, n_pending=n_pending,
                 n_esd=len(esd_seq), n_label=int(good.sum()),
                 first=int(scans_arr[good][0]), last=int(scans_arr[good][-1]))
    return dict(well=well,
                scans=scans_arr[good],
                bases=np.array([b for i, b in enumerate(bases) if good[i]],
                               dtype='S1'),
                esd_bases=np.array([eb for i, eb in enumerate(esd_b) if good[i]],
                                   dtype='S1'),
                src=np.array([s for i, s in enumerate(src) if good[i]],
                             dtype='S1'),
                over_scans=np.array(sorted(set(over_scans)), dtype=np.int64),
                stats=stats)


def run(wells, out):
    ref_rc = load_clean_ref()
    print(f'M13 reference (read orientation): {len(ref_rc)} bp')
    t0 = time.time()
    rows, meta = [], {}
    for w in wells:
        r = extract_well(w, ref_rc)
        if r is None:
            print(f'  {w}: skipped')
            continue
        rows.append(r)
        meta[w] = r['stats']
        s = r['stats']
        print(f'  {w}: {s["n_label"]} labels  match={s["n_match"]} '
              f'mism={s["n_mism"]} over={s["n_over"]} split={s["n_split"]}')
    if not rows:
        sys.exit('no wells produced labels')

    wells_arr = np.array([r['well'] for r in rows for _ in r['scans']], dtype='S8')
    scans = np.concatenate([r['scans'] for r in rows])
    bases = np.concatenate([r['bases'] for r in rows])
    esd_b = np.concatenate([r['esd_bases'] for r in rows])
    src = np.concatenate([r['src'] for r in rows])
    over_wells = np.array([r['well'] for r in rows
                           for _ in r['over_scans']], dtype='S8')
    over_scans = np.concatenate([r['over_scans'] for r in rows]) \
        if rows and any(len(r['over_scans']) for r in rows) else np.array([], dtype=np.int64)
    summ = {k: int(np.sum([meta[w][k] for w in meta])) for k in
            ('n_match', 'n_mism', 'n_over', 'n_split', 'n_pending')}
    summ['n_wells'] = len(rows)
    summ['n_labels'] = int(len(scans))
    print(f'OK {time.time()-t0:.1f}s  wells={len(rows)}  '
          f'labels={len(scans)}  split={summ["n_split"]}  '
          f'mismatches={summ["n_mism"]}')
    np.savez_compressed(out, wells=wells_arr, scans=scans, bases=bases,
                        esd_bases=esd_b, src=src, meta=meta, summary=summ,
                        over_wells=over_wells, over_scans=over_scans)
    print(f'saved {out}')
    return summ


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--wells', default=None,
                    help='comma-separated subset (default: all 96)')
    ap.add_argument('--out', default='m13_split_labels.npz')
    args = ap.parse_args()
    data_dir = os.path.join(HERE, 'MB1000_M13_DT')
    all_wells = sorted(f[:-4] for f in os.listdir(data_dir)
                       if f.endswith('.rsd'))
    if args.wells:
        want = set(args.wells.split(','))
        all_wells = [w for w in all_wells if w in want]
    run(all_wells, args.out)


if __name__ == '__main__':
    main()