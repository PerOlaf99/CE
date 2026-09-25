"""Sweep position-profiled Wiener regularization (sharp early, smooth tail).

Rationale: global regularization trades matched bases for longest run. Most
matched bases are early/mid read, most substitutions are at both ends. A
noise_reg that ramps up over the read keeps the early matches sharp while
smoothing the noisy 3' tail.

Usage:
    BLAST_DIR=/path/to/ncbi-blast-*/bin python exp_regprofile.py
"""
import glob
import json
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)
if os.path.dirname(_HERE) not in sys.path:
    sys.path.insert(0, os.path.dirname(_HERE))

import exp_deconv2 as ed
import blast_eval as be
import canon_metric as cm


def R(reg, **over):
    d = ed.P(gaussian_recon_noise_reg=reg)
    d.update(over)
    return d


CONFIGS = {
    "scalar0.06": ed.P(),
    "r06_10": R((0.06, 0.10)),
    "r06_12": R((0.06, 0.12)),
    "r06_13": R((0.06, 0.13)),
    "r06_15": R((0.06, 0.15)),
    "r06_16": R((0.06, 0.16)),
    "r06_20": R((0.06, 0.20)),
    "r05_09": R((0.05, 0.09)),
    "r07_13": R((0.07, 0.13)),
    "r06_13_pf40": R((0.06, 0.13), profile_fracs=(0.40, 1.0)),
    "r06_13_pf25": R((0.06, 0.13), profile_fracs=(0.25, 1.0)),
    "r06_16_pf25": R((0.06, 0.16), profile_fracs=(0.25, 1.0)),
}


def main():
    blastn = be._blast_bin("blastn")
    db = os.path.join(be.WORK, "m13db")
    wells = sorted(os.path.basename(f)[:-4] for f in glob.glob(os.path.join(ed.RSD, "*.rsd")))
    out = {}
    for name, cfg in CONFIGS.items():
        fa = os.path.join(be.WORK, "regprof_%s.fasta" % name)
        seqs = {w: ed.call_well(os.path.join(ed.RSD, w + ".rsd"), cfg) for w in wells}
        with open(fa, "w") as fh:
            for w, s in seqs.items():
                fh.write(">%s\n%s\n" % (w, s))
        recs = ed.run_records(blastn, db, fa)
        n = len(recs)
        matched = sum(r[2] for r in recs) / n
        bits = sum(r[1] for r in recs) / n
        gaps = sum(r[3] for r in recs)
        alen = sum(r[4] for r in recs)
        ins = sum(r[5] for r in recs)
        rlen = sum(r[6] for r in recs) / n
        mismatch = alen - sum(r[2] for r in recs) - gaps
        agg = be._agg(be._run(blastn, db, fa), be._ref_len(os.path.join(be.WORK, "M77815.1.fasta")))
        pb = [cm.perbase_vs_ref(s) for s in seqs.values()]
        agg["perbase_vs_ref"] = sum(v for v in pb if v is not None) / len(pb)
        agg["mean_matched"] = matched
        agg["total_insertions"] = ins
        out[name] = agg
        print("%-14s n=%d matched/w=%.1f bits/w=%.1f %%ID=%.2f longN=%.1f gaps=%-5d ins=%-5d mismatch=%-5d rlen=%.0f canon=%.2f"
              % (name, n, matched, bits, agg["mean_pident"], agg["mean_longest_perfect"],
                 gaps, ins, mismatch, rlen, agg["perbase_vs_ref"]), flush=True)
    json.dump({"results": out}, open(os.path.join(_HERE, "report_regprofile.json"), "w"),
              indent=2, default=str)
    print("wrote report_regprofile.json")


if __name__ == "__main__":
    main()
