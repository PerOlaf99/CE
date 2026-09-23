"""Official precision-mode scoreboard.

Calls the plate with call_plate.WIN_CONFIG_PRECISION, writes
basecalls_precision/, and scores it with real BLAST+ megablast vs M77815.1
(full metric set) plus the canonical per-base identity, so the precision
(longest-run/%ID) mode has the same auditable artifacts as the golden mode.
"""
import glob
import json
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

import call_plate as cp
import blast_eval as be
import canon_metric as cm


def main():
    rsd = os.path.join(_HERE, "..", "MB1000_M13_DT")
    out = os.path.join(_HERE, "basecalls_precision")
    os.makedirs(out, exist_ok=True)
    wells = sorted(os.path.basename(f)[:-4] for f in glob.glob(os.path.join(rsd, "*.rsd")))
    fa = os.path.join(be.WORK, "precision_mode.fasta")
    seqs = {}
    for w in wells:
        seq, _q = cp.basecall_well(os.path.join(rsd, w + ".rsd"), cp.WIN_CONFIG_PRECISION)
        seqs[w] = seq
        with open(os.path.join(out, w + ".fasta"), "w") as fh:
            fh.write(">%s len=%d\n" % (w, len(seq)))
            for i in range(0, len(seq), 60):
                fh.write(seq[i:i + 60] + "\n")
    with open(fa, "w") as fh:
        for w in wells:
            fh.write(">%s\n%s\n" % (w, seqs[w]))

    blastn = be._blast_bin("blastn")
    db = os.path.join(be.WORK, "m13db")
    ref_len = be._ref_len(os.path.join(be.WORK, "M77815.1.fasta"))
    agg = be._agg(be._run(blastn, db, fa), ref_len)
    recs = list(_records(blastn, db, fa))
    agg["mean_matched"] = sum(r[1] for r in recs) / len(recs)
    pb = [cm.perbase_vs_ref(s) for s in seqs.values()]
    agg["perbase_vs_ref"] = sum(v for v in pb if v is not None) / len(pb)
    agg["mode"] = "precision"
    agg["config"] = {k: v for k, v in cp.WIN_CONFIG_PRECISION.items()}
    print(json.dumps({k: v for k, v in agg.items() if k != "config"}, indent=2, default=str))
    json.dump(agg, open(os.path.join(_HERE, "report_precision_mode.json"), "w"),
              indent=2, default=str)
    print("wrote report_precision_mode.json")


def _records(blastn, db, fa):
    import subprocess
    fmt = ("6 qseqid sseqid pident length nident mismatch gaps qlen bitscore "
           "sstart send qseq sseq")
    p = subprocess.run([blastn, "-task", "megablast", "-query", fa, "-db", db,
                        "-outfmt", fmt, "-max_target_seqs", "5", "-evalue", "1e-5"],
                       capture_output=True, text=True)
    for line in p.stdout.splitlines():
        f = line.split("\t")
        if len(f) < 13 or not f[1].startswith(be.REF_ID):
            continue
        yield (f[0], int(f[4]), int(f[3]))


if __name__ == "__main__":
    main()
