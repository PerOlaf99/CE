"""Per-well insertion/deletion structure: ours (profile) vs Cimarron DLL (esd).

Usage:
    BLAST_DIR=/path/to/ncbi-blast-*/bin python exp_perwell.py
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


def perwell(blastn, db, fasta):
    p = subprocess.run([blastn, "-task", "megablast", "-query", fasta, "-db", db,
                        "-outfmt", FMT, "-max_target_seqs", "5", "-evalue", "1e-5"],
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
            best[q] = dict(bits=bits, ins=ins, dele=dele, gaps=int(f[6]),
                           nident=int(f[4]), length=int(f[3]), readlen=int(f[7]),
                           sstart=int(f[9]), send=int(f[10]))
    return best


def main():
    blastn = be._blast_bin("blastn")
    db = os.path.join(be.WORK, "m13db")
    ours = perwell(blastn, db, os.path.join(be.WORK, "ours.fasta"))
    dll = perwell(blastn, db, os.path.join(be.WORK, "esd.fasta"))
    rows = []
    for w in sorted(set(ours) | set(dll)):
        o, d = ours.get(w, {}), dll.get(w, {})
        rows.append((o.get("ins", 0) - d.get("ins", 0), w, o, d))
    rows.sort(reverse=True)
    print("delta  well  ours(ins del gaps nident rlen)  dll(ins del gaps nident rlen)")
    for delta, w, o, d in rows[:15]:
        print("%5d  %-4s  (%3d %3d %4d %4d %4d)  (%3d %3d %4d %4d %4d)"
              % (delta, w, o.get("ins", 0), o.get("dele", 0), o.get("gaps", 0),
                 o.get("nident", 0), o.get("readlen", 0),
                 d.get("ins", 0), d.get("dele", 0), d.get("gaps", 0),
                 d.get("nident", 0), d.get("readlen", 0)))
    ti_o = sum(v["ins"] for v in ours.values())
    ti_d = sum(v["ins"] for v in dll.values())
    print("\ntotals ours ins=%d del=%d gaps=%d | dll ins=%d del=%d gaps=%d"
          % (ti_o, sum(v["dele"] for v in ours.values()),
             sum(v["gaps"] for v in ours.values()),
             ti_d, sum(v["dele"] for v in dll.values()),
             sum(v["gaps"] for v in dll.values())))


if __name__ == "__main__":
    main()
