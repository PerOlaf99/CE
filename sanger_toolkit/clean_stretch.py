#!/usr/bin/env python3
"""clean_stretch.py - longest error-free (clean) stretch metric.

Are the extended tail bases real sequence, or caller guesswork?  The best
single number for that is the LONGEST contiguous stretch of aligned columns
with no gaps and no errors -- where a systematic, reproducible variant
(observed shared "C->T SNP" in these reads at one M13 coordinate) is
excluded as a *caller-inderiv dependent* column, since both callers see the
same template.

The SNP columns are detected empirically from the majority of OURS reads:
a mismatch at the same reference coordinate with the same substituted base,
present in >= half the reads, is treated as real template, not error.  That
same tolerated set is then applied unchanged to the DLL calls (fair).

Usage:
    python3 clean_stretch.py [--wells held|other|all]  (reads tuned_calls/)
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, '02_denovo_cnn_ensemble_91.53pct'))
sys.path.insert(0, os.path.join(ROOT, 'best_basecaller'))
sys.path.insert(0, HERE)
os.environ.setdefault('TF_CPP_MIN_LOG_LEVEL', '3')

import json
import argparse
import time

from mb1k_posprofile_sweep import sw_align, revcomp, REF, errors_by_third
from blast_bench import _ref_seq as _dummy  # noqa: F401 (keeps blast path hot)
import extract_training_data as etd

GT_DIR = os.path.join(ROOT, 'MB1000_M13_DT', 'MB1000_M13_DT_Cp312_MD1')
TUNED_DIR = os.path.join(ROOT, '02_denovo_cnn_ensemble_91.53pct', 'tuned_calls')

HELD = set('A01 A03 A05 A07 A09 A11 B02 B04 B06 B08 B10 B12 '
           'C01 C03 C05 C07 C09 C11 D02 D04 D06 D08 D10 D12 '
           'E01 E03 E05 E07 E09 E11 F02 F04 F06 F08 F10 F12 '
           'G01 G03 G05 G07 G09 G11 H02 H04 H06 H08 H10 H12'.split())


def load_ours(w):
    with open(os.path.join(TUNED_DIR, f'{w}.fasta')) as f:
        return ''.join(l.strip() for l in f if not l.startswith('>'))


def load_dll(w):
    seq = etd.parse_esd(os.path.join(GT_DIR, f'{w}.esd'))['sequence']
    return ''.join(c for c in seq if c in 'ACGT')


def align(seq):
    """Align rc(read) to plus-strand M13; return (aligned_q, aligned_r,
    ref_start) where ref_start is the absolute 0-based FASTA coord of the
    first aligned reference base."""
    return sw_align(revcomp(seq), REF)


def mismatch_columns(q, r, ref_start):
    """List of (ref_coord_abs, ref_base, read_base) for mismatch columns."""
    cols = []
    rc = ref_start
    for a, b in zip(q, r):
        if b != '-':
            if a != '-' and a != b:
                cols.append((rc, b, a))
            rc += 1
    return cols


def detect_snp_columns(reads, min_frac=0.5):
    """Ref coords where >=min_frac of reads share the same substitution."""
    from collections import Counter
    cnt = Counter()
    reads = [read for read in reads if len(read) >= 30]
    for seq in reads:
        a, b, rs = align(seq)
        for rc, ref, base in mismatch_columns(a, b, rs):
            cnt[(rc, ref, base)] += 1
    thr = max(1, int(len(reads) * min_frac))
    return {(rc, ref, base) for (rc, ref, base), n in cnt.items() if n >= thr}


def longest_clean(q, r, ref_start, tolerated):
    """Longest run of aligned columns with no gap and no (non-tolerated)
    error.  A column counts clean if it matches OR its ref coord+base is a
    tolerated SNP.  Returns (stretch_len, start_ref_coord, end_ref_coord)
    in ABSOLUTE 0-based FASTA coordinates."""
    best = cur = 0
    best_rc = cur_rc = rc = ref_start
    for a, b in zip(q, r):
        if b != '-':
            if a != '-' and (a == b or (rc, b, a) in tolerated):
                if cur == 0:
                    cur_rc = rc
                cur += 1
            else:
                cur = 0
            if cur > best:
                best = cur
                best_rc = cur_rc
            rc += 1
    return best, best_rc, best_rc + best - 1


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--wells', default='all', choices=['held', 'other', 'all'])
    args = ap.parse_args()

    wells = sorted(x[:-6] for x in os.listdir(TUNED_DIR)
                   if x.endswith('.fasta') and x != 'all_reads.fasta')
    if args.wells == 'held':
        wells = [w for w in wells if w in HELD]
    elif args.wells == 'other':
        wells = [w for w in wells if w not in HELD]
    print(f'{len(wells)} wells ({args.wells})', flush=True)

    t0 = time.time()
    ours = {w: load_ours(w) for w in wells}
    dll = {w: load_dll(w) for w in wells}

    print('detecting shared SNP columns from OURS reads...', flush=True)
    tolerated = detect_snp_columns(list(ours.values()))
    print(f'  tolerated majority variant columns: {len(tolerated)}', flush=True)
    for rc, ref, base in sorted(tolerated):
        print(f'    ref coord {rc}: ref={ref} reads-share {base}', flush=True)

    rows = {'wells': [], 'ours': [], 'dll': []}
    own = dln = 0
    snp = {'ours': 0, 'dll': 0}
    for w in wells:
        a, b, rs = align(ours[w])
        lpass, s1, e1 = longest_clean(a, b, rs, tolerated)
        for rc, ref, base in mismatch_columns(a, b, rs):
            if (rc, ref, base) in tolerated:
                snp['ours'] += 1
        a, b, rs = align(dll[w])
        lpdl, s2, e2 = longest_clean(a, b, rs, tolerated)
        for rc, ref, base in mismatch_columns(a, b, rs):
            if (rc, ref, base) in tolerated:
                snp['dll'] += 1
        own += lpass
        dln += lpdl
        rows['wells'].append(w)
        rows['ours'].append(lpass)
        rows['dll'].append(lpdl)
        print(f'{w}  ours_clean={lpass:4d} (M13 {s1}-{e1})   '
              f'dll_clean={lpdl:4d} (M13 {s2}-{e2})', flush=True)

    n = len(wells)
    print(f'\n=== clean stretch by well ({args.wells}) ===')
    print(f'mean longest clean stretch: OURS {own/n:.1f} bp, DLL {dln/n:.1f} bp '
          f'({own/n - dln/n:+.1f} bp)')
    print(f'tolerated-variant columns seen: ours {snp["ours"]}, dll {snp["dll"]}')
    with open(os.path.join(HERE, 'clean_stretch.json'), 'w') as f:
        json.dump(dict(wells=rows['wells'], tuned_calls_clean=rows['ours'],
                       dll_clean=rows['dll'], tolerated=list(sorted(tolerated)),
                       mean_ours=round(own / n, 2), mean_dll=round(dln / n, 2)),
                  f, indent=1)
    print(f'wrote {os.path.join(HERE, "clean_stretch.json")} ({time.time()-t0:.0f}s)')


if __name__ == '__main__':
    main()