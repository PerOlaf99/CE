#!/usr/bin/env python3
"""extract_m13_clean_training.py - build ML training data labeled by TRUE M13.

Instead of trusting the DLL/ESD base CALLS (which over-call homopolymers),
this labels every training window with the true M13 reference base at that
peak. Pipeline per well:

  1. load raw 4-channel RSD trace + ESD peak positions
  2. align the ESD (DLL) sequence to the M13 reference (read orientation =
     reverse-complement of settingsV10 reference_dna)
  3. for each aligned column with a real ESD peak:
        abase = DLL's call, rbase = true M13 base, scan = DLL peak scan
        strip_N column (ED is not a base) -> skip
        rbase == '-'              -> DLL insertion (homopolymer overcall) -> SKIP
        otherwise                 -> label = rbase  (100% correct vs M13)
  4. feature = raw 4-channel window (peak ± window) — "raw as is", no
     matrix separation, no Cimarron.

Output: npz with X (N, window*2+1, 4), y (N,) in A=0,C=1,G=2,T=3, and
metadata (wells, scans, dll_bases, true_bases, dropped_per_well).

Usage: python3 extract_m13_clean_training.py [--esd-variant Cp312] [--window 15]
"""
import argparse, json, os, sys, time
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_SUBDIR = 'MB1000_M13_DT'
CH_NAMES = ['Channel1', 'Channel2', 'Channel3', 'Channel4']
LABELS = ['A', 'C', 'G', 'T']
BASE_MAP = {b: i for i, b in enumerate(LABELS)}      # 'A':0,'C':1,'G':2,'T':3
RC_TRANS = str.maketrans('ACGT', 'TGCA')
M13_JSON = os.path.join(BASE_DIR, 'settingsV10.json')


def rc(seq):
    return seq[::-1].translate(RC_TRANS)


def load_clean_ref():
    with open(M13_JSON) as f:
        s = json.load(f)
    ref = ''.join(c for c in s['reference_dna'] if c in 'ACGT')
    return rc(ref)                                     # read orientation


def semi_global_sw(query, ref):
    """Align the FULL query against ref (free ref overhang at both ends) using
    a linear-gap dynamic program. Returns (q_al, r_al) with '-' gaps.
    Unlike a local alignment this never drops query bases, so the caller can
    index query positions 1:1 from q_al (unshifted)."""
    n, m = len(query), len(ref)
    H = np.zeros((n + 1, m + 1), dtype=np.int64)
    tb = np.zeros((n + 1, m + 1), dtype=np.int8)   # 0 diag / 1 up / 2 left
    MATCH, MISMATCH, GAP = 2, -3, -4
    inf = -10 ** 9
    H[1:, 0] = inf                     # query cannot float over ref's left edge
    for i in range(1, n + 1):
        qi = i - 1
        ri0 = max(0, i - 1 - n // 1)   # unrestricted (linear gap, no banding)
        for j in range(1, m + 1):
            rj = j - 1
            diag = H[i - 1, j - 1] + (MATCH if query[qi] == ref[rj] else MISMATCH)
            up = H[i - 1, j] + GAP
            left = H[i, j - 1] + GAP
            if diag >= up and diag >= left:
                H[i, j], tb[i, j] = diag, 0
            elif up >= left:
                H[i, j], tb[i, j] = up, 1
            else:
                H[i, j], tb[i, j] = left, 2
    bj = int(np.argmax(H[n, 1:])) + 1          # best end column on last row
    i, j = n, bj
    a_, b_ = [], []
    while i > 0:
        if tb[i, j] == 0:
            a_.append(query[i - 1]); b_.append(ref[j - 1]); i -= 1; j -= 1
        elif tb[i, j] == 1:
            a_.append(query[i - 1]); b_.append('-'); i -= 1
        else:
            a_.append('-'); b_.append(ref[j - 1]); j -= 1
    al = ''.join(reversed(a_))
    bl = ''.join(reversed(b_))
    i0 = len(bl) - len(bl.lstrip('-'))          # trim ref-only overhang cols
    return al[i0:], bl[i0:]


def seed_sw_align(query, ref_rc):
    """15-mer seeded alignment (same seed logic as eval_ground_truth) but the
    window is aligned semi-globally so the FULL query survives: the returned
    (q_al, r_al) keep every query base, hence q_al's non-gap count indexes the
    query 1:1 with no head/tail clipping. Returns None if seeding fails."""
    if len(query) < 60:
        return None
    K = 15
    qset = {query[i:i + K]: i for i in range(len(query) - K + 1)}
    offs = [j - qset[ref_rc[j:j + K]] for j in range(len(ref_rc) - K + 1)
            if ref_rc[j:j + K] in qset]
    if len(offs) < 3:
        return None
    med = int(np.median(offs))
    start = max(0, med - 400)
    win = ref_rc[start:med + 2 * len(query)]
    al, bl = semi_global_sw(query, win)
    return al, bl


def extract_features(ch, peak_idx, window=15):
    n = len(ch)
    start = max(0, peak_idx - window)
    end = min(n, peak_idx + window + 1)
    win = ch[start:end]
    if len(win) < window * 2 + 1:
        pad_before = max(0, window - peak_idx)
        pad_after = max(0, (peak_idx + window + 1) - n)
        win = np.pad(win, ((pad_before, pad_after), (0, 0)), mode='edge')
    return win.astype(np.float32)


def extract_well(well, esd_variant, window, ref_rc, raw_dir=DATA_SUBDIR):
    from extract_training_data import parse_rsd, parse_esd
    rsd_path = os.path.join(BASE_DIR, raw_dir, f"{well}.rsd")
    esd_path = os.path.join(BASE_DIR, raw_dir,
                            f"{raw_dir}_{esd_variant}_MD1", f"{well}.esd")
    if not os.path.exists(rsd_path) or not os.path.exists(esd_path):
        return None
    df = parse_rsd(rsd_path)
    ch = df[CH_NAMES].values.astype(np.float64)
    d = parse_esd(esd_path)
    seq = d.get('sequence', '')
    peaks = d.get('peak_positions')
    if peaks is None or len(peaks) == 0 or seq is None or len(seq) < 60:
        return None

    ed_q = ''.join(c for c in seq if c in 'ACGT')
    ed_idx = [i for i, c in enumerate(seq) if c in 'ACGT']
    al, bl = seed_sw_align(ed_q, ref_rc)
    if al is None:
        return None

    X = []
    y = []
    scans = []
    dll = []
    true_b = []
    dropped = 0
    mism = 0
    qi = 0
    for a, b in zip(al, bl):
        if a == '-':
            if b != '-':
                dropped += 1             # DLL deletion vs M13 (no peak exists)
            continue
        # real DLL peak here
        if b == '-':
            dropped += 1                 # DLL insertion (homopolymer overcall)
            qi += 1
            continue
        try:
            scan = int(peaks[ed_idx[qi]])
        except IndexError:
            break
        if 0 <= scan < len(ch):
            X.append(extract_features(ch, scan, window))
            y.append(BASE_MAP[b])
            scans.append(scan)
            dll.append(a)
            true_b.append(b)
            if a != b:
                mism += 1
        qi += 1
    if len(X) < 100:
        return None
    return dict(X=np.asarray(X, dtype=np.float32),
                y=np.asarray(y, dtype=np.uint8),
                scans=np.asarray(scans, dtype=np.int32),
                dll=b''.join(s.encode() for s in dll),
                true_b=b''.join(s.encode() for s in true_b),
                dropped=dropped, mism=mism, well=well)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--esd-variant', default='Cp312')
    ap.add_argument('--window', type=int, default=15)
    ap.add_argument('--wells', default=None,
                    help='comma-separated subset (default: all 96)')
    ap.add_argument('--out', default='m13_clean_training.npz')
    ap.add_argument('--verbose', action='store_true')
    args = ap.parse_args()

    ref_rc = load_clean_ref()
    data_dir = os.path.join(BASE_DIR, DATA_SUBDIR)
    all_wells = sorted(f[:-4] for f in os.listdir(data_dir) if f.endswith('.rsd'))
    if args.wells:
        want = set(args.wells.split(','))
        all_wells = [w for w in all_wells if w in want]
    print(f"M13 reference (read orientation): {len(ref_rc)} bp "
          f"({ref_rc[:12]}...{ref_rc[-12:]})")
    print(f"Extracting {len(all_wells)} wells (variant={args.esd_variant}, "
          f"window={args.window}, feature dim={(args.window*2+1)*4})")

    X_parts, y_parts = [], []
    wells_parts, scans_parts = [], []
    meta = {}
    ndrop = 0
    nmis = 0
    nclean = 0
    t0 = time.time()
    for w in all_wells:
        r = extract_well(w, args.esd_variant, args.window, ref_rc)
        if r is None:
            if args.verbose:
                print(f"  {w}: skipped")
            continue
        X_parts.append(r['X'])
        y_parts.append(r['y'])
        wells_parts.append(np.full(len(r['y']), r['well']))
        scans_parts.append(r['scans'])
        meta[w] = dict(n=len(r['y']), dropped=r['dropped'],
                       mism=r['mism'], scans=(int(r['scans'][0]),
                                               int(r['scans'][-1])),
                       dll=r['dll'].decode(), true=r['true_b'].decode())
        ndrop += r['dropped']
        nmis += r['mism']
        nclean += r['mism'] if r['mism'] else 0
        if args.verbose:
            print(f"  {w}: {len(r['y'])} labeled, {r['dropped']} dropped, "
                  f"{r['mism']} mismatches-turned-correct")
    X = np.concatenate(X_parts)
    y = np.concatenate(y_parts)
    wells_arr = np.concatenate(wells_parts)
    scans_arr = np.concatenate(scans_parts)
    print(f"OK {time.time()-t0:.1f}s  total samples={len(y)}  "
          f"classes={np.bincount(y, minlength=4).tolist()}")
    print(f"DLL errors excluded from labels: {ndrop} insertion/del columns, "
          f"{nmis} mismatches relabeled to true M13")

    out = os.path.join(BASE_DIR, args.out)
    np.savez_compressed(out, X=X, y=y, window=np.int32(args.window),
                        labels=np.array(LABELS), meta=meta,
                        wells=wells_arr, scans=scans_arr)
    print(f"saved {out}")


if __name__ == '__main__':
    main()