"""Test the position-varying spacing anchor curve (on/off) on top of the
new deconvolution winner.

Usage:
    BLAST_DIR=/path/to/ncbi-blast-*/bin python exp_anchor.py
"""
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
from call_plate import WIN_CONFIG, FALLBACK_CONFIG, QUALITY_GATE


def N(**over):
    d = dict(WIN_CONFIG)
    d.update(gaussian_recon_sigma_scale=1.05, gaussian_recon_noise_reg=0.06)
    d.update(over)
    return d


CONFIGS = {
    "base": ed.P(),
    "new": N(),
    "base_anchor": ed.P(use_spacing_anchor_curve=True),
    "new_anchor": N(use_spacing_anchor_curve=True),
    "new_anchor_pb": N(use_spacing_anchor_curve=True, pullback_weight=(0.008, 0.002)),
    "new_anchor_hi": N(use_spacing_anchor_curve=True, gaussian_recon_sigma_scale=1.10,
                       gaussian_recon_noise_reg=0.075),
}


def main():
    blastn = be._blast_bin("blastn")
    db = os.path.join(be.WORK, "m13db")
    import glob
    wells = sorted(os.path.basename(f)[:-4] for f in glob.glob(os.path.join(ed.RSD, "*.rsd")))
    out = {}
    for name, cfg in CONFIGS.items():
        fa = os.path.join(be.WORK, "anchor_%s.fasta" % name)
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
        print("%-16s n=%d matched/w=%.1f bits/w=%.1f %%ID=%.2f longN=%.1f gaps=%-5d ins=%-5d mismatch=%-5d rlen=%.0f canon=%.2f"
              % (name, n, matched, bits, agg["mean_pident"], agg["mean_longest_perfect"],
                 gaps, ins, mismatch, rlen, agg["perbase_vs_ref"]), flush=True)
    json.dump({"results": out}, open(os.path.join(_HERE, "report_anchor.json"), "w"),
              indent=2, default=str)
    print("wrote report_anchor.json")


if __name__ == "__main__":
    main()
