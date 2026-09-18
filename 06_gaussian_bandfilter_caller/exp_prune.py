"""Sweep insertion-pruning thresholds (OmitOkN) on the profiled config.

Goal: remove the ~800 spurious inserted bases the loose tail introduces
(ours 1,301 vs DLL 501) so identity and longest error-free run rise without
losing matched bases. Every run keeps the mean-quality gate + scalar fallback.

Usage:
    BLAST_DIR=/path/to/ncbi-blast-*/bin python exp_prune.py
"""
import glob
import json
import os
import subprocess
import statistics
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)
if os.path.dirname(_HERE) not in sys.path:
    sys.path.insert(0, os.path.dirname(_HERE))

from cimarron_basecaller.rsd_io import read_rsd, to_acgt_trace
from cimarron_basecaller import track_bases
from call_plate import WIN_CONFIG, FALLBACK_CONFIG, QUALITY_GATE
import blast_eval as be
import canon_metric as cm

RSD = os.path.join(_HERE, "..", "MB1000_M13_DT")


def P(**over):
    d = dict(WIN_CONFIG)
    d.update(over)
    return d


CONFIGS = {
    "prof": P(),
    "pr_m1.2_h0.9": P(prune_insertions=True, prune_merge_frac=1.2, prune_height_frac=0.9),
    "pr_m1.3_h0.9": P(prune_insertions=True, prune_merge_frac=1.3, prune_height_frac=0.9),
    "pr_m1.4_h0.9": P(prune_insertions=True, prune_merge_frac=1.4, prune_height_frac=0.9),
    "pr_m1.6_h0.9": P(prune_insertions=True, prune_merge_frac=1.6, prune_height_frac=0.9),
    "pr_m1.4_h0.8": P(prune_insertions=True, prune_merge_frac=1.4, prune_height_frac=0.8),
    "pr_m1.4_h1.0": P(prune_insertions=True, prune_merge_frac=1.4, prune_height_frac=1.0),
    "pr_m1.3_h0.8": P(prune_insertions=True, prune_merge_frac=1.3, prune_height_frac=0.8),
    "pr_m1.5_h0.85": P(prune_insertions=True, prune_merge_frac=1.5, prune_height_frac=0.85),
    "pr_m1.35_h0.95": P(prune_insertions=True, prune_merge_frac=1.35, prune_height_frac=0.95),
}


def call_well(path, cfg):
    rsd = read_rsd(path)
    trace, order = to_acgt_trace(rsd, base_order="TGCA")
    seq, q, _ = track_bases(trace, base_order=order, **cfg)
    if len(q) == 0 or float(sum(q) / len(q)) < QUALITY_GATE:
        seq, q, _ = track_bases(trace, base_order=order, **FALLBACK_CONFIG)
    return seq


def main():
    blastn, makeblastdb = be._blast_bin("blastn"), be._blast_bin("makeblastdb")
    os.makedirs(be.WORK, exist_ok=True)
    ref = be._fetch_ref(os.path.join(be.WORK, "M77815.1.fasta"))
    ref_len = be._ref_len(ref)
    db = os.path.join(be.WORK, "m13db")
    if not os.path.exists(db + ".ndb"):
        subprocess.run([makeblastdb, "-in", ref, "-dbtype", "nucl", "-out", db],
                       capture_output=True, text=True, check=True)

    wells = sorted(os.path.basename(f)[:-4] for f in glob.glob(os.path.join(RSD, "*.rsd")))
    out = {}
    for name, cfg in CONFIGS.items():
        fa = os.path.join(be.WORK, "prune_%s.fasta" % name)
        seqs = {}
        for w in wells:
            seqs[w] = call_well(os.path.join(RSD, w + ".rsd"), cfg)
        with open(fa, "w") as fh:
            for w, s in seqs.items():
                fh.write(">%s\n%s\n" % (w, s))
        a = be._agg(be._run(blastn, db, fa), ref_len)
        pb = [cm.perbase_vs_ref(s) for s in seqs.values()]
        a["perbase_vs_ref"] = sum(v for v in pb if v is not None) / len(pb)
        a["mean_matched"] = a["identical_bases"] / a["n_wells"]
        out[name] = a
        print("%-16s matched/w=%.1f bits/w=%.1f %%ID=%.2f covr=%.2f%% longN=%.1f longmed=%.0f gaps=%-5d readlen=%.0f canon=%.2f"
              % (name, a["mean_matched"], a["mean_bitscore"], a["mean_pident"],
                 100 * a["mean_coverage_read"], a["mean_longest_perfect"],
                 a["median_longest_perfect"], a["total_gaps"], a["mean_read_len"],
                 a["perbase_vs_ref"]), flush=True)
    json.dump({"results": out}, open(os.path.join(_HERE, "report_prune.json"), "w"),
              indent=2, default=str)
    print("wrote report_prune.json")


if __name__ == "__main__":
    main()
