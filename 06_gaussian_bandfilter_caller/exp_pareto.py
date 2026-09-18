"""Pareto scan: score every already-generated config fasta on the plate.

Prints matched/bit/longest/mismatch/indel structure sorted by matched bases, so
we can see whether any tried config dominates the current winner on both the
GOLDEN matched counter and the longest-error-free-run bar.

Usage:
    BLAST_DIR=/path/to/ncbi-blast-*/bin python exp_pareto.py
"""
import glob
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)
if os.path.dirname(_HERE) not in sys.path:
    sys.path.insert(0, os.path.dirname(_HERE))

import blast_eval as be


def main():
    blastn = be._blast_bin("blastn")
    db = os.path.join(be.WORK, "m13db")
    fastas = [f for f in glob.glob(os.path.join(be.WORK, "*.fasta"))
              if os.path.basename(f) not in ("M77815.1.fasta",)]
    rows = []
    for fa in fastas:
        d = be._run(blastn, db, fa)
        if not d:
            continue
        n = len(d)
        matched = sum(v["nident"] for v in d.values()) / n
        bits = sum(v["bitscore"] for v in d.values()) / n
        pident = sum(v["pident"] for v in d.values()) / n
        mismatch = sum(v["length"] - v["nident"] - v["gaps"] for v in d.values())
        gaps = sum(v["gaps"] for v in d.values())
        longest = sum(v["longest_perfect"] for v in d.values()) / n
        rlen = sum(v["qlen"] for v in d.values()) / n
        rows.append((matched, bits, longest, pident, mismatch, gaps, rlen, n,
                     os.path.basename(fa)[:-6]))
    rows.sort(reverse=True)
    print("%-32s n  matched/w bits/w longN %%ID    mismatch gaps  rlen" % "config")
    for matched, bits, longest, pident, mismatch, gaps, rlen, n, name in rows:
        print("%-32s %2d %8.1f %6.1f %5.1f %5.2f %7d %6d %6.0f"
              % (name, n, matched, bits, longest, pident, mismatch, gaps, rlen))


if __name__ == "__main__":
    main()
