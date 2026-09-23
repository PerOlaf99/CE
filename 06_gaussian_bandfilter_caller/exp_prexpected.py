"""Insertion-pruning sweep with LOCAL-EXPECTED spacing.

The original prune used the tracker's adaptive spacing, which collapses onto
the overcalls themselves, so it never triggered.  Here `prune_expected_spacing`
feeds the spacing-anchor curve (true local band spacing) as the yardstick, so
three called bases squeezed into less than `merge_frac` real bands are flagged.

Dropping a false insertion removes a gap column, merging two matching runs --
the one mechanism that can RAISE the longest error-free run rather than just
identity.  Sweep how aggressive the squeeze test is.

Usage:
    BLAST_DIR=/path/to/ncbi-blast-*/bin python exp_prexpected.py
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


def C(sig, reg, merge, height):
    return ed.P(gaussian_recon_sigma_scale=sig, gaussian_recon_noise_reg=reg,
                use_spacing_anchor_curve=True, prune_insertions=True,
                prune_expected_spacing=True, prune_merge_frac=merge,
                prune_height_frac=height)


CONFIGS = {}
BASE = (1.10, 0.075)
for _merge in (1.25, 1.40, 1.60):
    for _h in (0.75, 0.95):
        CONFIGS["hi_m%.2f_h%.2f" % (_merge, _h)] = C(1.10, 0.075, _merge, _h)
for _merge in (1.25, 1.40):
    CONFIGS["mid_m%.2f_h0.95" % _merge] = C(1.05, 0.09, _merge, 0.95)


def main():
    blastn = be._blast_bin("blastn")
    db = os.path.join(be.WORK, "m13db")
    wells = sorted(os.path.basename(f)[:-4] for f in glob.glob(os.path.join(ed.RSD, "*.rsd")))
    ref_len = be._ref_len(os.path.join(be.WORK, "M77815.1.fasta"))
    out = {}
    for name, cfg in CONFIGS.items():
        fa = os.path.join(be.WORK, "prexp_%s.fasta" % name)
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
        print("%-15s longN=%.1f longmed=%.0f %%ID=%.2f matched/w=%.1f bits/w=%.1f rlen=%.0f canon=%.2f"
              % (name, agg["mean_longest_perfect"], agg["median_longest_perfect"],
                 agg["mean_pident"], agg["mean_matched"], agg["mean_bitscore"],
                 agg["mean_read_len"], agg["perbase_vs_ref"]), flush=True)
    json.dump({"results": out}, open(os.path.join(_HERE, "report_prexpected.json"), "w"),
              indent=2, default=str)
    print("wrote report_prexpected.json")


if __name__ == "__main__":
    main()
