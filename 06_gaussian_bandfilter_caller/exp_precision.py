"""Precision frontier sweep: maximise longest error-free run / %ID, giving up
read length (and matched bases).

Triggered by the operator decision to prioritise the longest-run and identity
bars over raw matched bases. Explores the regularization x sigma x
spacing-anchor space toward the high-precision end.

Usage:
    BLAST_DIR=/path/to/ncbi-blast-*/bin python exp_precision.py
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


def C(sig, reg, anchor=True, **over):
    d = ed.P(gaussian_recon_sigma_scale=sig, gaussian_recon_noise_reg=reg,
             use_spacing_anchor_curve=anchor)
    d.update(over)
    return d


CONFIGS = {
    "winner_s1.05_r0.06": ed.P(),
    "a_s1.00_r0.09": C(1.00, 0.09),
    "a_s1.05_r0.09": C(1.05, 0.09),
    "a_s1.10_r0.09": C(1.10, 0.09),
    "a_s1.15_r0.09": C(1.15, 0.09),
    "a_s1.10_r0.10": C(1.10, 0.10),
    "a_s1.10_r0.12": C(1.10, 0.12),
    "a_s1.15_r0.11": C(1.15, 0.11),
    "a_s1.20_r0.10": C(1.20, 0.10),
    "a_s1.00_r0.11": C(1.00, 0.11),
    "a_s1.10_r0.075": C(1.10, 0.075),
    "a_s1.05_r0.08": C(1.05, 0.08),
    "n_s1.00_r0.09": C(1.00, 0.09, anchor=False),
    "a_s1.20_r0.13": C(1.20, 0.13),
}


def main():
    blastn = be._blast_bin("blastn")
    db = os.path.join(be.WORK, "m13db")
    wells = sorted(os.path.basename(f)[:-4] for f in glob.glob(os.path.join(ed.RSD, "*.rsd")))
    out = {}
    for name, cfg in CONFIGS.items():
        fa = os.path.join(be.WORK, "prec_%s.fasta" % name)
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
        print("%-20s n=%d longN=%.1f longmed=%.0f %%ID=%.2f matched/w=%.1f bits/w=%.1f rlen=%.0f mismatch=%-5d ins=%-5d canon=%.2f"
              % (name, n, agg["mean_longest_perfect"], agg["median_longest_perfect"],
                 agg["mean_pident"], matched, bits, rlen, mismatch, ins,
                 agg["perbase_vs_ref"]), flush=True)
    rank = sorted(out.items(), key=lambda kv: kv[1]["mean_longest_perfect"], reverse=True)
    print("\nranked by longest error-free run:")
    for name, agg in rank[:6]:
        print("  %-20s longN=%.1f %%ID=%.2f matched/w=%.1f bits/w=%.1f rlen=%.0f"
              % (name, agg["mean_longest_perfect"], agg["mean_pident"],
                 agg["mean_matched"], agg["mean_bitscore"], agg["mean_read_len"]))
    json.dump({"results": out}, open(os.path.join(_HERE, "report_precision.json"), "w"),
              indent=2, default=str)
    print("wrote report_precision.json")


if __name__ == "__main__":
    main()
