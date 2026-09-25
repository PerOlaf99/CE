"""Where does the longest-error-free-run gap come from?

Compare per-well longest runs (SNP-neutral) and their reference position for
ours (profiled) vs Cimarron DLL (esd). Determines whether the DLL advantage is
broad/interior (needs a better caller) or concentrated in a few wells.

Usage:
    BLAST_DIR=/path/to/ncbi-blast-*/bin python exp_longest.py
"""
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)
if os.path.dirname(_HERE) not in sys.path:
    sys.path.insert(0, os.path.dirname(_HERE))

import blast_eval as be


def load(blastn, db, fasta):
    recs = be._run(blastn, db, fasta)
    return {q: v for q, v in recs.items()}


def main():
    blastn = be._blast_bin("blastn")
    db = os.path.join(be.WORK, "m13db")
    ours = load(blastn, db, os.path.join(be.WORK, "ours.fasta"))
    dll = load(blastn, db, os.path.join(be.WORK, "esd.fasta"))
    wells = sorted(set(ours) | set(dll))
    ol = [ours.get(w, {}).get("longest_perfect", 0) for w in wells]
    dl = [dll.get(w, {}).get("longest_perfect", 0) for w in wells]
    import statistics as st
    print("longest_perfect  ours: mean=%.1f median=%.0f min=%d max=%d"
          % (st.mean(ol), st.median(ol), min(ol), max(ol)))
    print("longest_perfect  dll : mean=%.1f median=%.0f min=%d max=%d"
          % (st.mean(dl), st.median(dl), min(dl), max(dl)))
    rows = sorted(((dll.get(w, {}).get("longest_perfect", 0) - ours.get(w, {}).get("longest_perfect", 0), w)
                   for w in wells), reverse=True)
    print("\ndelta(dll-ours)  well  ours_long  dll_long  ours_%ID  dll_%ID  ours_rlen  dll_rlen")
    for delta, w in rows[:12]:
        o, d = ours.get(w, {}), dll.get(w, {})
        print("%6d          %-4s  %5d      %5d     %.2f    %.2f    %4d      %4d"
              % (delta, w, o.get("longest_perfect", 0), d.get("longest_perfect", 0),
                 o.get("pident", 0), d.get("pident", 0), o.get("qlen", 0), d.get("qlen", 0)))
    # how many wells each side wins
    ow = sum(1 for a, b in zip(ol, dl) if a > b)
    dw = sum(1 for a, b in zip(ol, dl) if b > a)
    print("\nwells with longer run: ours=%d  dll=%d  tie=%d" % (ow, dw, len(wells) - ow - dw))


if __name__ == "__main__":
    main()
