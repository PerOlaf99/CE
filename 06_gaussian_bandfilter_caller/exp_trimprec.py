"""Trim sweep on the precision configs.

With read length now expendable, cut low-quality ends to raise %ID while
checking the longest error-free run (which trimming can only reduce or keep,
never increase -- so a trim that leaves it flat is a free identity gain).

Usage:
    BLAST_DIR=/path/to/ncbi-blast-*/bin python exp_trimprec.py
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


def C(sig, reg, **over):
    d = ed.P(gaussian_recon_sigma_scale=sig, gaussian_recon_noise_reg=reg,
             use_spacing_anchor_curve=True)
    d.update(over)
    return d


CONFIGS = {}
for _p in (10, 20, 25, 30, 35, 40, 45):
    CONFIGS["hi_pct%d" % _p] = C(1.10, 0.075, trim_quality_percentile=float(_p))
for _p in (25, 35, 45):
    CONFIGS["mid_pct%d" % _p] = C(1.05, 0.09, trim_quality_percentile=float(_p))
CONFIGS["hi_mott1.0"] = C(1.10, 0.075, trim_method="mott", mott_quality_cutoff=1.0)
CONFIGS["hi_mott0.5"] = C(1.10, 0.075, trim_method="mott", mott_quality_cutoff=0.5)


def main():
    blastn = be._blast_bin("blastn")
    db = os.path.join(be.WORK, "m13db")
    wells = sorted(os.path.basename(f)[:-4] for f in glob.glob(os.path.join(ed.RSD, "*.rsd")))
    out = {}
    for name, cfg in CONFIGS.items():
        fa = os.path.join(be.WORK, "trimprec_%s.fasta" % name)
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
        out[name] = agg
        print("%-14s n=%d longN=%.1f %%ID=%.2f matched/w=%.1f bits/w=%.1f rlen=%.0f mismatch=%-5d ins=%-5d canon=%.2f"
              % (name, n, agg["mean_longest_perfect"], agg["mean_pident"], matched, bits,
                 rlen, mismatch, ins, agg["perbase_vs_ref"]), flush=True)
    json.dump({"results": out}, open(os.path.join(_HERE, "report_trimprec.json"), "w"),
              indent=2, default=str)
    print("wrote report_trimprec.json")


if __name__ == "__main__":
    main()
