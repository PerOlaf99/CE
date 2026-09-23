"""Seventh sweep: last push on longest at the trim peak.

The (longest, %ID) frontier now peaks at reg 0.13 / trim pct 38: longest 471.8
at 98.19% ID (vs DLL 490.7 / 96.76 -- we win identity by a mile, trail longest
by ~19 bp).  Fine-grid reg/sigma at that trim depth and test whether
expected-spacing insertion pruning extends the runs further.

Usage:
    BLAST_DIR=/path/to/ncbi-blast-*/bin python exp_prectrim7.py
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


def C(sig, reg, pct, **over):
    d = ed.P(gaussian_recon_sigma_scale=sig, gaussian_recon_noise_reg=reg,
             use_spacing_anchor_curve=True, trim_quality_percentile=float(pct))
    d.update(over)
    return d


CONFIGS = {}
for _r in (0.124, 0.128, 0.132):
    CONFIGS["s1.05_r%.3f_p38" % _r] = C(1.05, _r, 38)
for _s in (1.00, 1.02, 1.08):
    CONFIGS["s%.2f_r0.130_p38" % _s] = C(_s, 0.130, 38)
CONFIGS["s1.05_r0.130_p36"] = C(1.05, 0.130, 36)
CONFIGS["s1.05_r0.130_p40"] = C(1.05, 0.130, 40)
for _m in (1.25, 1.45):
    CONFIGS["prune_m%.2f_p38" % _m] = C(1.05, 0.130, 38, prune_insertions=True,
                                        prune_expected_spacing=True,
                                        prune_merge_frac=_m, prune_height_frac=0.95)


def main():
    blastn = be._blast_bin("blastn")
    db = os.path.join(be.WORK, "m13db")
    wells = sorted(os.path.basename(f)[:-4] for f in glob.glob(os.path.join(ed.RSD, "*.rsd")))
    ref_len = be._ref_len(os.path.join(be.WORK, "M77815.1.fasta"))
    out = {}
    for name, cfg in CONFIGS.items():
        fa = os.path.join(be.WORK, "pctrim7_%s.fasta" % name)
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
    json.dump({"results": out}, open(os.path.join(_HERE, "report_pctrim7.json"), "w"),
              indent=2, default=str)
    print("wrote report_pctrim7.json")


if __name__ == "__main__":
    main()
