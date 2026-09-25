"""Fourth sweep: chase the regularization monotonicity.

Longest error-free run rose straight through reg 0.09 -> 0.12 (434 -> 459)
while identity stayed flat ~97.1%, because the quality trim discards the
broader/degraded ends that regularization smears.  Keep pushing reg and
re-check sigma (1.10 looked slightly better at reg 0.11).

Usage:
    BLAST_DIR=/path/to/ncbi-blast-*/bin python exp_prectrim4.py
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


def C(sig, reg, pct):
    return ed.P(gaussian_recon_sigma_scale=sig, gaussian_recon_noise_reg=reg,
                use_spacing_anchor_curve=True, trim_quality_percentile=float(pct))


CONFIGS = {}
for _r in (0.13, 0.14, 0.15, 0.16, 0.18, 0.20):
    CONFIGS["s1.05_r%.2f_p25" % _r] = C(1.05, _r, 25)
for _r in (0.13, 0.15, 0.18):
    CONFIGS["s1.10_r%.2f_p25" % _r] = C(1.10, _r, 25)
CONFIGS["s1.05_r0.15_p20"] = C(1.05, 0.15, 20)
CONFIGS["s1.05_r0.15_p30"] = C(1.05, 0.15, 30)


def main():
    blastn = be._blast_bin("blastn")
    db = os.path.join(be.WORK, "m13db")
    wells = sorted(os.path.basename(f)[:-4] for f in glob.glob(os.path.join(ed.RSD, "*.rsd")))
    ref_len = be._ref_len(os.path.join(be.WORK, "M77815.1.fasta"))
    out = {}
    for name, cfg in CONFIGS.items():
        fa = os.path.join(be.WORK, "pctrim4_%s.fasta" % name)
        seqs = {w: ed.call_well(os.path.join(ed.RSD, w + ".rsd"), cfg) for w in wells}
        with open(fa, "w") as fh:
            for w, s in seqs.items():
                fh.write(">%s\n%s\n" % (w, s))
        agg = be._agg(be._run(blastn, db, fa), ref_len)
        recs = ed.run_records(blastn, db, fa)
        agg["mean_matched"] = sum(r[2] for r in recs) / len(recs)
        pb = [cm.perbase_vs_ref(s) for s in seqs.values()]
        agg["perbase_vs_ref"] = sum(v for v in pb if v is not None) / len(pb)
        out[name] = agg
        print("%-20s longN=%.1f longmed=%.0f %%ID=%.2f matched/w=%.1f bits/w=%.1f rlen=%.0f canon=%.2f"
              % (name, agg["mean_longest_perfect"], agg["median_longest_perfect"],
                 agg["mean_pident"], agg["mean_matched"], agg["mean_bitscore"],
                 agg["mean_read_len"], agg["perbase_vs_ref"]), flush=True)
    json.dump({"results": out}, open(os.path.join(_HERE, "report_pctrim4.json"), "w"),
              indent=2, default=str)
    print("wrote report_pctrim4.json")


if __name__ == "__main__":
    main()
