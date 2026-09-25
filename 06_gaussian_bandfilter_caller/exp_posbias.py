"""Position-of-error analysis: are substitutions concentrated in the 3' tail?

For each alignment column, map it to the query coordinate and tally
substitutions and insertions into deciles of the read. If our excess
substitutions live in the tail (the region only WE read, because the DLL
trims earlier), then improving the caller's tail accuracy is the target;
if they are spread evenly, the core detector itself needs work.

Usage:
    BLAST_DIR=/path/to/ncbi-blast-*/bin python exp_posbias.py
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
N = 10


def tally(blastn, db, fasta):
    p = subprocess.run([blastn, "-task", "megablast", "-query", fasta, "-db", db,
                        "-outfmt", FMT, "-max_target_seqs", "5", "-evalue", "1e-5"],
                       capture_output=True, text=True)
    sub = [0] * N
    ins = [0] * N
    tot = [0] * N
    n_reads = 0
    for line in p.stdout.splitlines():
        f = line.split("\t")
        if len(f) < 13 or not f[1].startswith(be.REF_ID):
            continue
        q, s, qlen = f[11], f[12], int(f[7])
        n_reads += 1
        qi = 0
        for a, b in zip(q, s):
            d = min(N - 1, (qi * N) // max(qlen, 1))
            if a != "-":
                qi += 1
                tot[d] += 1
                if b == "-":
                    ins[d] += 1
                elif a != b:
                    sub[d] += 1
    return sub, ins, tot, n_reads


def main():
    blastn = be._blast_bin("blastn")
    db = os.path.join(be.WORK, "m13db")
    for label, fa in (("ours", "ours.fasta"), ("dll", "esd.fasta")):
        sub, ins, tot, nr = tally(blastn, db, os.path.join(be.WORK, fa))
        print("\n== %s (%d reads) ==" % (label, nr))
        print("decile  aligned  subst  sub%%   ins   sub+/1kb")
        for d in range(N):
            if tot[d] == 0:
                continue
            print("%3d%%    %6d  %5d  %5.2f  %4d   %6.1f"
                  % (d * 100 // N, tot[d], sub[d], 100.0 * sub[d] / tot[d], ins[d],
                     1000.0 * (sub[d] + ins[d]) / tot[d]))


if __name__ == "__main__":
    main()
