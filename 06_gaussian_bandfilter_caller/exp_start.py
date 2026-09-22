"""Per-column error profile of the first 90 query bases (start-of-read).

If our start-of-read substitutions cluster in the first few columns (leader /
primer region), a small leading trim could raise identity/longest-run at almost
no cost to matched bases. If they are spread over the first ~100, trimming is
too expensive and the caller's early-region behaviour itself needs work.

Usage:
    BLAST_DIR=/path/to/ncbi-blast-*/bin python exp_start.py
"""
import os
import subprocess
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)
if os.path.dirname(_HERE) not in sys.path:
    sys.path.insert(0, os.path.dirname(_HERE))

import blast_eval as be

FMT = ("6 qseqid sseqid pident length nident mismatch gaps qlen bitscore "
       "sstart send qseq sseq")
MAXC = 90


def tally(blastn, db, fasta):
    p = subprocess.run([blastn, "-task", "megablast", "-query", fasta, "-db", db,
                        "-outfmt", FMT, "-max_target_seqs", "5", "-evalue", "1e-5"],
                       capture_output=True, text=True)
    sub = [0] * MAXC
    mat = [0] * MAXC
    for line in p.stdout.splitlines():
        f = line.split("\t")
        if len(f) < 13 or not f[1].startswith(be.REF_ID):
            continue
        q, s = f[11], f[12]
        qi = 0
        for a, b in zip(q, s):
            if a == "-":
                continue
            if qi >= MAXC:
                break
            if b == "-":
                pass
            elif a == b:
                mat[qi] += 1
            else:
                sub[qi] += 1
            qi += 1
    return mat, sub


def main():
    blastn = be._blast_bin("blastn")
    db = os.path.join(be.WORK, "m13db")
    for label, fa in (("ours", "ours.fasta"), ("dll", "esd.fasta")):
        mat, sub = tally(blastn, db, os.path.join(be.WORK, fa))
        print("\n== %s == col: matches/substitutions (n=96)" % label)
        for start in range(0, MAXC, 10):
            line = []
            for c in range(start, start + 10):
                tot = mat[c] + sub[c]
                line.append("%d/%d" % (mat[c], sub[c]) if tot else "0/0")
            print("cols %2d-%2d: %s" % (start, start + 9, "  ".join(line)))
        print("sub total(0-89)=%d  mat total(0-89)=%d" % (sum(sub), sum(mat)))


if __name__ == "__main__":
    main()
