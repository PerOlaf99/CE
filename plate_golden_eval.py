#!/usr/bin/env python3
"""Plate-wide golden-bar evaluation of our current caller (tuned_basecaller).

Runs tuned_basecaller.call_well() (the committed "our caller") over all 96
wells and measures each read on the GOLDEN_STANDARD bar defined in
02_denovo_cnn_ensemble_91.53pct/GOLDEN_STANDARD.md:

  * matched_bp (blastn megablast best-HSP vs M13) -- THE metric
  * coverage / identity / bases_detected / bitscore
  * longest_error_free_run -- longest consecutive matching run on the SAME
    best-bitscore HSP, computed from blastn's gapped qseq/sseq columns,
    with the known template mutation column (M13 fwd 5977) treated as
    NEUTRAL (skipped: neither counts nor breaks the run).

Also reports the DLL/ESD read through the identical pipeline for the
directly-comparable standings, plus the mutation internal standard
check (96/96 -> read carries T at the CACCAG[T]GAGACGGG motif).

Usage:
  python3 plate_golden_eval.py            # all 96 wells
  python3 plate_golden_eval.py A01 B09    # specific wells
  python3 plate_golden_eval.py A          # row
"""
import os
import sys
from collections import defaultdict
from multiprocessing import Pool

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "sanger_toolkit"))

from blast_bench import blast_eval, _ref_seq

PLATE_DIR = os.path.join(
    HERE, "MB1000_M13_DT", "Analyzed Data", "MB1000_M13_DT_Cp312_MD1")

MUT_MOTIF_READ = "CACCAGTGAGACGG"  # read-strand motif carrying the T at 5977


def gapped_longest_run(seq, ref):
    """SNP-neutral longest error-free run from the best-bitscore HSP.

    cols:       blastn -outfmt "6 qseqid sstart send qstart qend bitscore qseq sseq"
    match col:  qseq[c]==sseq[c] and neither is '-'
    SNP col:    subject forward coordinate == 5977  -> skipped (no count,
                no break).  Forward coord from sstart/send orientation.
    """
    from tempfile import TemporaryDirectory
    import subprocess

    seq = ''.join(c for c in seq if c in 'ACGT')
    if len(seq) < 30:
        return None
    with TemporaryDirectory() as td:
        with open(os.path.join(td, 'ref.fa'), 'w') as f:
            f.write('>M13mp18\n' + ref + '\n')
        with open(os.path.join(td, 'q.fa'), 'w') as f:
            f.write('>q\n' + seq + '\n')
        subprocess.run(
            ['makeblastdb', '-in', os.path.join(td, 'ref.fa'),
             '-dbtype', 'nucl', '-out', os.path.join(td, 'db')],
            check=True, capture_output=True)
        out = subprocess.run(
            ['blastn', '-db', os.path.join(td, 'db'),
             '-query', os.path.join(td, 'q.fa'), '-task', 'megablast',
             '-outfmt', '6 qseqid sstart send qstart qend bitscore qseq sseq'],
            check=True, capture_output=True,
            text=True).stdout
    rows = [l.split('\t') for l in out.splitlines() if l.strip()]
    if not rows:
        return None, None
    best = max(rows, key=lambda r: float(r[5]))
    _, sstart, send, _qstart, _qend, _bs, qseq, sseq = best
    sstart, send = int(sstart), int(send)
    strand_rev = sstart > send
    longest = run = 0
    for c, (q, s) in enumerate(zip(qseq, sseq)):
        fwd = sstart - c if strand_rev else sstart + c
        if fwd == 5977:            # SNP-neutral column: skip, keep run alive
            continue
        if q == '-' or s == '-':
            run = 0
            continue
        if q == s:
            run += 1
            longest = max(longest, run)
        else:
            run = 0
    return longest, best


def process_well(well):
    sys.path.insert(0, os.path.join(HERE, "02_denovo_cnn_ensemble_91.53pct"))
    from tuned_basecaller import call_well
    import extract_training_data as etd

    esd = etd.parse_esd(os.path.join(PLATE_DIR, well + ".esd"))
    dll = esd["sequence"]

    seq, quals, bands, cfg = call_well(os.path.join(PLATE_DIR, well + ".rsd"))
    used_cfg = cfg.get("pullback_weight", 0.0)

    ours = blast_eval(seq)
    dl = blast_eval(dll)

    our_run, _ = gapped_longest_run(seq, _ref_seq())
    dll_run, _ = gapped_longest_run(dll, _ref_seq())

    mut = MUT_MOTIF_READ in seq
    res = {
        "well": well,
        "ours_bases": ours["bases_detected"] if ours else 0,
        "ours_matched": ours["matched"] if ours else 0,
        "ours_cov": round(ours["coverage"], 1) if ours else 0.0,
        "ours_id": round(ours["identity"], 2) if ours else 0.0,
        "ours_bits": ours["bitscore"] if ours else 0,
        "ours_run": our_run if our_run else 0,
        "dll_bases": dl["bases_detected"] if dl else 0,
        "dll_matched": dl["matched"] if dl else 0,
        "dll_cov": round(dl["coverage"], 1) if dl else 0.0,
        "dll_id": round(dl["identity"], 2) if dl else 0.0,
        "dll_run": dll_run if dll_run else 0,
        "cfg": used_cfg,
        "mut_T": mut,
    }
    if ours is None:
        res["ours_note"] = "NO_ALIGN"
    if dl is None:
        res["dll_note"] = "NO_ALIGN"
    return res


def main():
    args = sys.argv[1:]
    if not args:
        wells = sorted(f[:-4] for f in os.listdir(PLATE_DIR) if f.endswith(".esd"))
    elif all(len(a) <= 2 for a in args):
        pref = []
        for a in args:
            if len(a) == 1:
                pref += [f"{a}{c:02d}" for c in range(1, 13)]
            else:
                pref += [f"{r}{int(a[1:]):02d}" for r in "ABCDEFGH"]
        wells = sorted(f[:-4] for f in os.listdir(PLATE_DIR)
                       if f.endswith(".esd") and f[:-4] in pref)
    else:
        wells = args

    if not wells:
        print("no wells matched", file=sys.stderr)
        sys.exit(1)

    print("well,ours_bases,ours_matched,ours_cov,ours_id,ours_bits,ours_run,"
          "dll_bases,dll_matched,dll_cov,dll_id,dll_run,mut_T,cfg")
    results = []
    with Pool(8) as pool:
        for r in pool.imap_unordered(process_well, wells):
            results.append(r)
            print(','.join(str(r.get(k, '')) for k in (
                "well", "ours_bases", "ours_matched", "ours_cov", "ours_id",
                "ours_bits", "ours_run", "dll_bases", "dll_matched", "dll_cov",
                "dll_id", "dll_run", "mut_T", "cfg")), flush=True)

    means = defaultdict(float)
    for r in results:
        for k in ("matched", "bases", "run"):
            means[(r["well"], k)] = 0
    def agg(prefix, key):
        vals = [r[f"{prefix}_{key}"] for r in results]
        return sum(vals) / len(vals)
    print("\n=== PLATE STANDINGS (mean over %d wells) ===" % len(results))
    for label, prefix in (("OURS", "ours"), ("DLL ", "dll")):
        print(f"{label}  matched={agg(prefix,'matched'):6.2f}  "
              f"bases={agg(prefix,'bases'):6.1f}  cov={agg(prefix,'cov'):5.1f}  "
              f"id={agg(prefix,'id'):5.2f}  run={agg(prefix,'run'):6.1f}")
    win = sum(1 for r in results if r["ours_matched"] > r["dll_matched"])
    print(f"wells beating DLL: {win}/{len(results)}")
    print(f"mutation T called: {sum(r['mut_T'] for r in results)}/{len(results)}")


if __name__ == "__main__":
    main()