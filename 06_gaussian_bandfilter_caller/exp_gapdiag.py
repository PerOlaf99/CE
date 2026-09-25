"""Diagnose the gap structure of an alignment: are the excess gap columns
query INSERTIONS (extra called bases, sseq=='-') or query DELETIONS (missing
bases, qseq=='-')? This decides whether the patent's OmitOkN insertion-prune or
GapCheck/GAP_SPLIT gap-fill is the right lever.

Usage:
    BLAST_DIR=... python exp_gapdiag.py
"""
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

import blast_eval as be


def diagnose(fasta, blastn, db):
    fmt = ("6 qseqid sseqid pident length nident mismatch gaps qlen bitscore "
           "sstart send qseq sseq")
    import subprocess
    p = subprocess.run([blastn, "-task", "megablast", "-query", fasta, "-db", db,
                        "-outfmt", fmt, "-max_target_seqs", "5", "-evalue", "1e-5"],
                       capture_output=True, text=True)
    best = {}
    for line in p.stdout.splitlines():
        f = line.split("\t")
        if len(f) < 13 or not f[1].startswith(be.REF_ID):
            continue
        q, bits = f[0], float(f[8])
        if q not in best or bits > best[q][0]:
            ins = sum(1 for a, b in zip(f[11], f[12]) if b == "-" and a != "-")
            dele = sum(1 for a, b in zip(f[11], f[12]) if a == "-" and b != "-")
            best[q] = (bits, ins, dele, int(f[6]))
    n = len(best)
    if n == 0:
        print("%-40s no hits" % os.path.basename(fasta))
        return
    ins = sum(v[1] for v in best.values())
    dele = sum(v[2] for v in best.values())
    gaps = sum(v[3] for v in best.values())
    print("%-40s n=%d  insertions=%d  deletions=%d  gaps_field=%d  ins/read=%.2f del/read=%.2f"
          % (os.path.basename(fasta), n, ins, dele, gaps, ins / n, dele / n))


def main():
    blastn = be._blast_bin("blastn")
    os.makedirs(be.WORK, exist_ok=True)
    ref = be._fetch_ref(os.path.join(be.WORK, "M77815.1.fasta"))
    db = os.path.join(be.WORK, "m13db")
    if not os.path.exists(db + ".ndb"):
        import subprocess
        subprocess.run([be._blast_bin("makeblastdb"), "-in", ref, "-dbtype", "nucl", "-out", db],
                       capture_output=True, text=True, check=True)
    for name in ("ours", "esd",
                 "prof2_g_prof333_b1.2", "prof_g_scalar", "grid_base"):
        fa = os.path.join(be.WORK, name + ".fasta")
        if os.path.exists(fa):
            diagnose(fa, blastn, db)


if __name__ == "__main__":
    main()
