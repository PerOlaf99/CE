#!/usr/bin/env python3
"""TRAINING-DATA GENERATOR for the region-specific (head/mid/tail) basecaller.

INPUT:  the 96-well MB1000_M13_DT plate (ESD Cp312 reads + raw RSD traces) and
        a reference (M13.md insert core).
OUTPUT: labeled per-base samples for ML:
          features  : matrix-deconvolved base-space trace window (2-peak/duplex
                      geometry, ~+/-hw scans around the aligned base) + context
                      (left/right spacing, local median spacing).
          label     : reference base, with KNOWN-VARIANT overrides applied
                      (from --override json or the internal-controls scan).
          meta      : well, coord, esd_idx, scan, region, esd_base, duplex
                      verdict (if cached), plus flags: homopolymer, weak-end,
                      low-contrast, near-start/shoulder, gap-adjacent.

KEY POINT: the label must be the *plate-verified* truth, not a blind copy of
the FASTA.  The internal-controls scan (--) finds coords where ALL wells read a
different base than M13.md (true clone variants, e.g. coord 311: ref C, plate T
96/96) and applies them, so the caller is trained to READ PEAKS, never to
invent the reference sequence.

Run:
  python3 train_data_gen.py --wells A01 B01 C01 --hw 10                 # subset
  python3 train_data_gen.py --every-mid 2 --zones head,tail             # balanced
  python3 train_data_gen.py --find-variants --min-support 0.95          # auto ref fix
"""
import argparse, glob, json, os, sys
import numpy as np
from Bio import Align
from collections import Counter
from scipy.signal import find_peaks

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from optimize_windows_esd import load_well
from optimize_duplex import MAX_DRIFT
import extract_training_data as etd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ESD_SUB = 'MB1000_M13_DT_Cp312_MD1'
OUT = os.path.join(ROOT, 'sanger_toolkit', 'train_data')

# A01 reference camera matrix (per-channel crosstalk, from A01 2090_2140.json).
DEFAULT_MATRIX = [[1.0, 0.7, 0.0, 0.05],
                  [0.0, 1.0, 0.05, 1.0],
                  [0.2, 0.3, 1.0, 1.5],
                  [0.3, 0.0, 0.0, 1.0]]


def align_esd_to_ref(esd_seq, ref):
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


def window_features(B, scan, hw, raw_win):
    """Per-base feature vector: base-space channel stats + 2-peak geometry + context.
    Base-space = raw @ inv(Matrix) (spectral deconvolution, like the GUI)."""
    s0, s1 = max(0, scan - hw), min(len(B), scan + hw + 1)
    w = B[s0:s1]
    out = []
    for c in range(4):                       # one block per base-space channel
        seg = w[:, c]
        pk, _ = find_peaks(seg, prominence=max(3, 0.05 * seg.max()), distance=3)
        H = seg[pk] if len(pk) else np.array([0.0])
        o = np.argsort(H)[::-1]
        out += [seg.max(),
                (H[o[0]] if len(pk) >= 1 else 0.0),
                (H[o[1]] if len(pk) >= 2 else 0.0),
                seg.max() / (seg.mean() + 1e-9),
                float(np.argmax(seg))]
    mx = w.max(axis=1)                       # two-peak "duplex" on the envelope
    pk, _ = find_peaks(mx, prominence=max(3, 0.05 * mx.max()), distance=3)
    H = mx[pk] if len(pk) else np.array([0.0])
    o = np.argsort(H)[::-1]
    out += [len(pk),
            (H[o[0]] if len(pk) >= 1 else 0.0),
            (H[o[1]] if len(pk) >= 2 else 0.0),
            (abs(pk[o[1]] - pk[o[0]]) if len(pk) >= 2 else 0.0),
            mx.max() / (np.median(mx) + 1e-9)]
    if raw_win is not None:
        for c in range(4):
            seg = raw_win[s0:s1, c]
            out += [seg.max(), seg.max() / (seg.sum() + 1e-9)]
    return out


def find_true_variants(wells, ref, min_support=0.95):
    """Coords where >=min_support wells agree on a base different from ref."""
    grid = {c: Counter() for c in range(len(ref))}
    for w in wells:
        p = os.path.join(ROOT, 'MB1000_M13_DT', ESD_SUB, w + '.esd')
        if not os.path.exists(p):
            continue
        seq = etd.parse_esd(p)['sequence']
        coord = align_esd_to_ref(seq, ref)
        for i in range(len(seq)):
            if 0 <= coord[i] < len(ref):
                grid[coord[i]][seq[i]] += 1
    out = {}
    for c, cnt in grid.items():
        tot = sum(cnt.values())
        if tot < 0.5 * len(wells):
            continue
        maj, n = cnt.most_common(1)[0]
        if maj != ref[c] and n >= min_support * tot:
            out[c] = maj
    return out


def load_duplex_cache(well):
    """idx -> cached duplex rec (window drift-filtered), from the bench/full caches."""
    out = {}
    for d in (os.path.join(ROOT, 'sanger_toolkit', 'od_whole_m13'),
              os.path.join(ROOT, 'sanger_toolkit', 'train_data', 'duplex', well),
              os.path.join(ROOT, 'sanger_toolkit', 'plate_duplex_out', well)):
        if not os.path.isdir(d):
            continue
        for fn in glob.glob(os.path.join(d, '*.json')):
            try:
                r = json.load(open(fn))
            except Exception:
                continue
            i = r.get('idx', int(os.path.basename(fn)[: os.path.basename(fn).find('.')]))
            out[i] = r
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--wells', nargs='*', default=None)
    ap.add_argument('--ref', default=os.path.join(ROOT, 'M13.md'))
    ap.add_argument('--hw', type=int, default=10, help='window half-width in scans')
    ap.add_argument('--zones', default='head,mid,tail', help='head,mid,tail[,tail2]')
    ap.add_argument('--every-mid', type=int, default=1, help='stride in mid zone')
    ap.add_argument('--with-raw-channels', action='store_true')
    ap.add_argument('--override', default=None,
                    help='json {coord: base} of known true variants to apply')
    ap.add_argument('--find-variants', action='store_true',
                    help='auto-detect plate-consistent deviations and apply them')
    ap.add_argument('--min-support', type=float, default=0.95)
    ap.add_argument('--duplex-cache', action='store_true',
                    help='attach cached duplex verdicts (ok/called) to meta')
    args = ap.parse_args()

    ref = open(args.ref).read().strip().upper()
    wells = args.wells or sorted(os.path.basename(f)[:-4]
                                 for f in glob.glob(os.path.join(ROOT, 'MB1000_M13_DT', '*.rsd')))

    override = dict()
    if args.find_variants:
        override = find_true_variants(wells, ref, args.min_support)
        print(f'[auto] true variants found & applied: '
              + (' '.join(f'{c}:{ref[c]}->{b}' for c, b in override.items()) or 'none'))
    if args.override:
        override.update({int(k): v for k, v in json.load(open(args.override)).items()})

    M = np.array(DEFAULT_MATRIX)
    Minv = np.linalg.inv(M).T

    zones = set(args.zones.split(','))
    region_by_coord = lambda c: ('head' if c < 60 else 'tail2' if c >= 800 else
                                 'tail' if c >= 770 else 'mid')

    os.makedirs(OUT, exist_ok=True)
    X, y, meta = [], [], []
    for w in wells:
        p = os.path.join(ROOT, 'MB1000_M13_DT', ESD_SUB, w + '.esd')
        if not os.path.exists(p):
            continue
        raw, esd_seq, esd_pp = load_well(os.path.join(ROOT, 'MB1000_M13_DT'), w, ESD_SUB)
        B = (raw @ Minv).clip(0, None)
        coord = align_esd_to_ref(esd_seq, ref)
        dcache = load_duplex_cache(w) if args.duplex_cache else {}
        for i in range(len(esd_seq)):
            c = coord[i]
            if not (0 <= c < len(ref)):
                continue
            reg = region_by_coord(c)
            if reg not in zones:
                continue
            if reg == 'mid':
                cc = int(np.min(coord[coord >= 0]))          # first core coord
                if (c - cc) % max(1, args.every_mid) != 0:
                    continue
            label = override.get(c, ref[c])
            scan = int(esd_pp[i])
            s0, s1 = max(0, scan - args.hw), min(len(raw), scan + args.hw + 1)
            rawwin = raw[s0:s1] if args.with_raw_channels else None
            f = window_features(B, scan, args.hw, rawwin)
            dL = float(scan - esd_pp[i - 1]) if i > 0 else float('nan')
            dR = float(esd_pp[i + 1] - scan) if i + 1 < len(esd_pp) else float('nan')
            local = float(np.median(np.diff(esd_pp[max(0, i - 6):min(len(esd_pp), i + 7)])))
            X.append(np.concatenate([f, [dL if dL == dL else 0, dR if dR == dR else 0,
                                         local if local == local else 0]]))
            y.append(label)
            dc = dcache.get(i, {})
            dw = dc.get('window')
            drift_val = round(dw[0] - dc.get('scan', 0), 1) if dw else None
            trusted = bool(dc.get('ok') and drift_val is not None and abs(drift_val) <= MAX_DRIFT)
            meta.append(dict(well=w, coord=int(c), esd_idx=int(i), scan=scan,
                             region=reg, esd=esd_seq[i],
                             homopolymer=bool(c > 0 and c + 1 < len(ref) and
                                              ref[c - 1] == ref[c] == ref[c + 1]),
                             weak_end=bool(scan > 9000),
                             near_start=bool(scan < 2150),
                             variant=bool(override.get(c) is not None),
                             duplex_ok=bool(dc.get('ok')),
                             duplex_called=dc.get('called', ''),
                             duplex_drift=drift_val,
                             duplex_trusted=trusted))
        if w in {'A01', 'B01', 'C01', 'D01'} or wells[0] == w:
            print(f'  {w}: {len(raw)}scans, {len(coord)} esd, core bases sampled', flush=True)
    X = np.array(X); y = np.array(y)
    out = os.path.join(OUT, 'batch')
    np.savez_compressed(out + '.npz', X=X, y=y,
                        meta=np.array([json.dumps(m) for m in meta], dtype=object))
    json.dump(meta, open(out + '_meta.json', 'w'))
    ov = os.path.join(OUT, 'true_variants.json')
    json.dump({str(c): b for c, b in override.items()}, open(ov, 'w'), indent=1)
    print(f'\nWROTE {out}.npz : X{X.shape}  samples={len(y)}')
    print('  override(s):', override)
    from collections import Counter as C
    print('  region counts:', dict(C(m['region'] for m in meta)))
    print('  label counts:', dict(C(y)))


if __name__ == '__main__':
    main()