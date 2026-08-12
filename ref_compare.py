#!/usr/bin/env python3
"""Compare the ESD basecall and the independent basecall against a TRUE
reference sequence, so you can see how many errors each caller really has
(not just how well the two callers agree with each other).

The ESD sequence is read from the .esd file; the independent call is
produced by the same dsp_core + peak_calling code path the GUI uses, using
the settings from a settings JSON (like A01_settings.json).

The reference is any FASTA file. M77815.1 (M13mp18, GenBank) is bundled at
refs/m13_M77815.1.fa; the read's aligned span for A01 is ref 5471..6286.

Usage:
    python3 ref_compare.py --well A01
    python3 ref_compare.py --well A01 --ref refs/m13_M77815.1.fa --start 5300 --end 6300
    python3 ref_compare.py --well A01 --settings A01_settings.json --ref refs/m13_M77815.1.fa
    python3 ref_compare.py --well A01 --local   # BLAST-style, drops noisy read ends
"""
import argparse
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dsp_core
import peak_calling
from extract_training_data import parse_esd, parse_rsd

BASE_DIR = "/media/tv/78B0C7DE1FA7081C/electropherogram/MB1000_M13_DT"
DEFAULT_REF = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           'refs', 'm13_M77815.1.fa')
DEFAULT_SETTINGS = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                'A01_settings.json')
_MATCH, _MISMATCH, _GAP = 1, -1, -2
_COMP = {'A': 'T', 'T': 'A', 'G': 'C', 'C': 'G',
         'R': 'Y', 'Y': 'R', 'S': 'S', 'W': 'W', 'K': 'M', 'M': 'K',
         'D': 'H', 'H': 'D', 'B': 'V', 'V': 'B', 'N': 'N'}


def revcomp(seq):
    return ''.join(_COMP.get(b, 'N') for b in seq[::-1])


def best_orientation(seq, ref_slice):
    """Try forward and reverse complement; return the alignment result for
    whichever matches the reference better. Returns (result, is_revcomp)."""
    fwd = semiglobal_identity(seq, ref_slice)
    rev = semiglobal_identity(revcomp(seq), ref_slice)
    if fwd[0] >= rev[0]:
        return fwd, False
    return rev, True


def local_identity(query, reference):
    """Smith-Waterman local alignment with affine gaps (BLAST-style scoring:
    match +2, mismatch -3, gap open -11, gap extend -2). Reports identity over
    the best-scoring segment only, so unreliable read ends (typical of Sanger
    runs) are dropped instead of counted as errors - this is why BLAST reports
    a higher identity than the forced whole-read semiglobal alignment above.

    Returns (identity_pct, matches, mismatches, indels, aligned_len, score,
             ref_start0, ref_end0, read_start0, read_end0, mismatch_list).
             ref_start0/ref_end0 are the reference span of the best segment
             (0-based within the reference slice); read_start0/read_end0 are
             the read span of the best segment, so the bases dropped off the
             two read ends are read_start0 and len(read)-1-read_end0.
    """
    q, r = query, reference
    m, n = len(q), len(r)
    if m == 0 or n == 0:
        return 0.0, 0, 0, 0, 0, 0, 0, 0, []
    NEG = -10**9
    match, mismatch, gopen, gext = 2, -3, 11, 2
    Mp = [0] * (n + 1)
    Xp = [NEG] * (n + 1)
    Yp = [NEG] * (n + 1)
    TB, V = [], []
    best = (0, 0, 0)
    for i in range(1, m + 1):
        qi = q[i - 1]
        Mrow = [0] * (n + 1)
        Xrow = [NEG] * (n + 1)
        Yrow = [NEG] * (n + 1)
        trow = [0] * (n + 1)
        vrow = [0] * (n + 1)
        for j in range(1, n + 1):
            base = Mp[j - 1]
            if Xp[j - 1] > base:
                base = Xp[j - 1]
            if Yp[j - 1] > base:
                base = Yp[j - 1]
            Mrow[j] = (base if base > 0 else 0) + \
                (match if qi == r[j - 1] else mismatch)
            xa = Mp[j] - gopen
            xb = Xp[j] - gext
            Xrow[j] = xa if xa > xb else xb
            ya = Mrow[j - 1] - gopen
            yb = Yrow[j - 1] - gext
            Yrow[j] = ya if ya > yb else yb
            v = Mrow[j]
            if Xrow[j] > v:
                v = Xrow[j]
            if Yrow[j] > v:
                v = Yrow[j]
            vrow[j] = v
            trow[j] = 0 if v == Mrow[j] else (1 if v == Xrow[j] else 2)
            if v > best[0]:
                best = (v, i, j)
        TB.append(trow)
        V.append(vrow)
        Mp, Xp, Yp = Mrow, Xrow, Yrow
    _, i, j = best
    matches = mismatches = indels = 0
    mism = []
    ref_hits = []
    read_hits = []
    while i > 0 and j > 0:
        v = V[i - 1][j]
        if v <= 0:
            break
        d = TB[i - 1][j]
        if d == 0:
            qb, rb = q[i - 1], r[j - 1]
            read_hits.append(i - 1)
            ref_hits.append(j - 1)
            if qb == rb:
                matches += 1
            else:
                mismatches += 1
                mism.append((i - 1, qb, rb, j - 1))
            i -= 1
            j -= 1
        elif d == 1:
            indels += 1
            read_hits.append(i - 1)
            i -= 1
        else:
            indels += 1
            ref_hits.append(j - 1)
            j -= 1
    aligned = matches + mismatches + indels
    ident = 100.0 * matches / aligned if aligned else 0.0
    rlo = min(ref_hits) if ref_hits else 0
    rhi = max(ref_hits) if ref_hits else 0
    qlo = min(read_hits) if read_hits else 0
    qhi = max(read_hits) if read_hits else len(q) - 1
    # bases dropped off each end of the read (the unreliable Sanger flanks),
    # in the aligned (possibly rev-comp'd) orientation
    return ident, matches, mismatches, indels, aligned, best[0], \
        rlo, rhi, qlo, qhi, mism


def best_orientation_local(seq, ref_slice):
    """Local-alignment orientation auto-detect: pick the strand with the
    higher Smith-Waterman score (BLAST picks the best bit score). Returns
    (result, is_revcomp)."""
    fwd = local_identity(seq, ref_slice)
    rev = local_identity(revcomp(seq), ref_slice)
    if fwd[5] >= rev[5]:
        return fwd, False
    return rev, True


def read_fasta(path):
    with open(path) as f:
        lines = f.read().splitlines()
    hdr = lines[0].lstrip('>').split()[0] if lines else '?'
    seq = ''.join(l.strip() for l in lines[1:] if l.strip())
    return hdr, seq.upper()


def semiglobal_identity(query, reference):
    """Free-end-gap Needleman-Wunsch (semiglobal): terminal overhangs of the
    reference (and of a longer-than-reference read) are free and do NOT count
    as errors. Returns
    (identity_pct, matches, mismatches, indels, mismatch_list)
    where mismatch_list is [(query_idx, query_base, ref_base, ref_idx), ...]
    indexed from the left end of the read / reference slice.
    Errors = mismatches + indels; identity = matches / (matches + errors).
    """
    q, r = query, reference
    m, n = len(q), len(r)
    if m == 0 or n == 0:
        return 0.0, 0, 0, 0, []
    dp = np.zeros((m + 1, n + 1), dtype=np.int32)
    tb = np.zeros((m + 1, n + 1), dtype=np.int8)  # 0=diag 1=up 2=left
    for i in range(1, m + 1):
        qi = q[i - 1]
        prev = dp[i - 1]
        row = dp[i]
        tbrow = tb[i]
        row[0] = 0
        for j in range(1, n + 1):
            diag = prev[j - 1] + (_MATCH if qi == r[j - 1] else _MISMATCH)
            up = prev[j] + _GAP
            left = row[j - 1] + _GAP
            if diag >= up and diag >= left:
                row[j], tbrow[j] = diag, 0
            elif up >= left:
                row[j], tbrow[j] = up, 1
            else:
                row[j], tbrow[j] = left, 2

    # best end point: free skip of trailing ref (last row) or trailing query
    i, j = m, int(np.argmax(dp[m, :]))
    if dp[i, j] < dp[int(np.argmax(dp[:, n])), n]:
        i, j = int(np.argmax(dp[:, n])), n

    matches = mismatches = indels = 0
    mism = []
    while i > 0 and j > 0:
        d = tb[i, j]
        if d == 0:
            qb, rb = q[i - 1], r[j - 1]
            if qb == rb:
                matches += 1
            else:
                mismatches += 1
                mism.append((i - 1, qb, rb, j - 1))
            i -= 1
            j -= 1
        elif d == 1:  # query base consumed, ref gapped -> read insertion
            indels += 1
            i -= 1
        else:         # ref base consumed, query gapped -> read deletion
            indels += 1
            j -= 1
    # reaching row 0 or column 0 is a free flank, not an error
    total = matches + mismatches + indels
    ident = 100.0 * matches / total if total else 0.0
    return ident, matches, mismatches, indels, mism


def independent_basecall(well, settings, esd_variant):
    rsd = parse_rsd(os.path.join(BASE_DIR, f'{well}.rsd'))
    raw = rsd[['Channel1', 'Channel2', 'Channel3', 'Channel4']].values.astype(np.float64)
    _, _, _, _, separated, _ = dsp_core.full_pipeline(
        raw, [0, 0, 0, 0],
        settings.get('baseline_method', 'Rolling Median'),
        settings.get('baseline_window', 510),
        settings.get('smooth_method', 'FFT Lowpass'),
        settings.get('smooth_window', 4),
        settings.get('smooth_order', 12),
        np.array(settings.get('matrix', dsp_core.DEFAULT_SPEC_MATRIX)),
        baseline_window2=settings.get('baseline_window2'),
        matrix_apply_point=settings.get('matrix_apply_point', 'smoothed'))
    pos, called_seq, _, _ = peak_calling.pc_call_bases_with_shifts(
        separated, settings.get('mobility_shifts', [0, 0, 0, 0]),
        min_distance=settings.get('min_distance', 5),
        prominence_frac=settings.get('prominence_frac', 0.006),
        min_signal_frac=settings.get('min_signal_frac', 1.0),
        tolerance=settings.get('tolerance', 4),
        norm_window=settings.get('norm_window', 800),
        onset_frac=settings.get('onset_frac', 0.05),
        signal_onset_smooth=settings.get('signal_onset_smooth', 40))
    if settings.get('fill_in'):
        shifts = settings.get('mobility_shifts', [0, 0, 0, 0])
        added = peak_calling.pc_fill_in_combined_peaks(
            separated, shifts, positions=[int(p) for p in pos],
            min_distance=settings.get('min_distance', 1),
            prominence_frac=settings.get('prominence_frac', 0.02),
            norm_window=settings.get('norm_window', 800),
            fill_gap=settings.get('fill_gap', 3),
            fill_margin=settings.get('fill_margin', 0.2))
        if added:
            merged = sorted([(int(p), b) for p, b in zip(pos, called_seq)]
                            + list(added), key=lambda t: t[0])
            pos = np.array([t[0] for t in merged], dtype=np.int64)
            called_seq = ''.join(t[1] for t in merged)
    return called_seq


def find_esd_subdirs(base_dir):
    return {d.replace('MB1000_M13_DT_', '').replace('_MD1', ''): d
            for d in os.listdir(base_dir)
            if os.path.isdir(os.path.join(base_dir, d)) and d.endswith('_MD1')}


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--well', default='A01')
    ap.add_argument('--esd-variant', default='Cp312')
    ap.add_argument('--ref', default=DEFAULT_REF, help='reference FASTA')
    ap.add_argument('--start', type=int, default=5300, help='ref start (1-based)')
    ap.add_argument('--end', type=int, default=6300, help='ref end (1-based, inclusive)')
    ap.add_argument('--settings', default=DEFAULT_SETTINGS,
                    help='settings JSON for the independent caller')
    ap.add_argument('--mismatches', type=int, default=10,
                    help='how many mismatches to print (0 = none)')
    ap.add_argument('--local', action='store_true',
                    help='BLAST-style local alignment (Smith-Waterman, affine '
                         'gaps): report identity over the best-scoring '
                         'segment, dropping unreliable Sanger read ends, '
                         'instead of forcing the whole read to align')
    args = ap.parse_args()

    subdirs = find_esd_subdirs(BASE_DIR)
    if args.esd_variant not in subdirs:
        print(f'ESD variant {args.esd_variant} not found; have: {sorted(subdirs)}')
        sys.exit(1)
    esd_path = os.path.join(BASE_DIR, subdirs[args.esd_variant], f'{args.well}.esd')
    esd_data = parse_esd(esd_path)
    esd_seq = esd_data.get('sequence', '')

    ref_hdr, ref = read_fasta(args.ref)
    ref_slice = ref[args.start - 1:args.end]
    print(f'Reference: {ref_hdr}  slice {args.start}..{args.end} '
          f'({len(ref_slice)} nt)')

    settings = json.load(open(args.settings)) if os.path.exists(args.settings) else {}
    ind_seq = independent_basecall(args.well, settings, args.esd_variant)

    print(f'\n{"caller":<14}{"identity":>9}{"matches":>9}{"mismatch":>10}'
          f'{"indel":>7}{"errors":>8}{"bases":>7}')
    print('-' * 64)
    for label, seq in (('ESD', esd_seq), ('Independent', ind_seq)):
        if args.local:
            (ident, m, mm, ind, aligned, score, rlo, rhi, qlo, qhi, mism), is_rev = \
                best_orientation_local(seq, ref_slice)
            aligned_len = aligned
            drop_start = qlo
            drop_end = max(0, len(seq) - 1 - qhi)
            span = (f'local: ref {args.start + rlo}..{args.start + rhi}, '
                    f'read {qlo}..{qhi} of {len(seq)}, '
                    f'{drop_start} bp dropped at read start, '
                    f'{drop_end} at read end')
        else:
            (ident, m, mm, ind, mism), is_rev = best_orientation(seq, ref_slice)
            aligned_len = len(seq)
            span = ''
        print(f'{label:<14}{ident:>8.1f}%{m:>9}{mm:>10}{ind:>7}'
              f'{mm + ind:>8}{aligned_len:>7}'
              f'  ({("rev-comp" if is_rev else "forward")} read'
              f'{(", " + span) if span else ""})')
        if args.mismatches and mm:
            print(f'  first {min(args.mismatches, mm)} mismatches:')
            for qi, qb, rb, ri in mism[:args.mismatches]:
                print(f'    base #{qi + 1} ({qb}) -> ref {qb}!={rb} at ref {args.start + ri}')
    print()


if __name__ == '__main__':
    main()
