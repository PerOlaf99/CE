"""Refine the trim+precision sweet spot (mid_pct25 family).

mid = sigma 1.05 / reg 0.09 / spacing-anchor / trim_quality_percentile.
Untrimmed it sat at longest 401 with 94.8% ID; a 25th-pct quality trim lifted
BOTH to 422.9 / 97.17.  Map how the trim depth and the filter width trade off.

Usage:
    BLAST_DIR=/path/to/ncbi-blast-*/bin python exp_prectrim2.py
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
for _p in (15, 18, 20, 22, 25, 28, 30, 32):
    CONFIGS["s1.05_r0.09_p%d" % _p] = C(1.05, 0.09, _p)
for _s in (1.00, 1.02, 1.08):
    CONFIGS["s%.2f_r0.09_p25" % _s] = C(_s, 0.09, 25)
for _r in (0.085, 0.095):
    CONFIGS["s1.05_r%.3f_p25" % _r] = C(1.05, _r, 25)


def main():
    blastn = be._blast_bin("blastn")
    db = os.path.join(be.WORK, "m13db")
    wells = sorted(os.path.basename(f)[:-4] for f in glob.glob(os.path.join(ed.RSD, "*.rsd")))
    ref_len = be._ref_len(os.path.join(be.WORK, "M77815.1.fasta"))
    out = {}
    for name, cfg in CONFIGS.items():
        fa = os.path.join(be.WORK, "pctrim2_%s.fasta" % name)
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
    json.dump({"results": out}, open(os.path.join(_HERE, "report_pctrim2.json"), "w"),
              indent=2, default=str)
    print("wrote report_pctrim2.json")


if __name__ == "__main__":
    main()
