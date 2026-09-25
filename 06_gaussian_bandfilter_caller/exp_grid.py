"""Grid-search spacing-caller configs for a lower per-base error rate.

Our current config maximizes total identical bases, but trails Cimarron on
%ID / bit score / longest error-free stretch because it carries more
mismatches+gaps (4.76% error vs 3.27%). This script basecalls the plate under
several nearby configs and scores each with NCBI BLAST+ megablast, printing
identical bases, aligned length, %ID, total bit score, ref/read coverage and
mean longest error-free stretch, so we can look for a config that dominates
(more correct bases AND higher bit score).

Usage:
    BLAST_DIR=/path/to/ncbi-blast-*/bin python exp_grid.py
"""
import glob
import json
import os
import subprocess
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

from cimarron_basecaller.rsd_io import read_rsd, to_acgt_trace
from cimarron_basecaller import track_bases
from call_plate import WIN_CONFIG
import blast_eval as be

RSD = os.path.join(_HERE, "..", "MB1000_M13_DT")

BASE = dict(WIN_CONFIG)


def C(**over):
    d = dict(BASE)
    d.update(over)
    return d


CONFIGS = {
    "base": BASE,
    "ema0.06": C(ema_alpha=0.06),
    "ema0.08": C(ema_alpha=0.08),
    "ema0.14": C(ema_alpha=0.14),
    "pb0.012": C(pullback_weight=0.012),
    "pb0.030": C(pullback_weight=0.030),
    "pb0.045": C(pullback_weight=0.045),
    "bonus1.2": C(channel_peak_bonus=1.2),
    "bonus2.1": C(channel_peak_bonus=2.1),
    "win0.70_1.30": C(window_frac=(0.70, 1.30)),
    "win0.82_1.18": C(window_frac=(0.82, 1.18)),
    "nnw1200": C(local_norm_window=1200),
    "nnw2400": C(local_norm_window=2400),
    "no_comb": C(use_combined_channel_score=False),
}


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
        fa = os.path.join(be.WORK, "grid_%s.fasta" % name)
        with open(fa, "w") as fh:
            for w in wells:
                rsd = read_rsd(os.path.join(RSD, w + ".rsd"))
                trace, order = to_acgt_trace(rsd, base_order="TGCA")
                seq, _q, _r = track_bases(trace, base_order=order, **cfg)
                fh.write(">%s\n%s\n" % (w, seq))
        a = be._agg(be._run(blastn, db, fa), ref_len)
        out[name] = a
        print("%-13s id=%-7d len=%-7d %%ID=%.2f bits=%-9.0f refcov=%.2f%% readcov=%.2f%% "
              "longest=%.1f readlen=%.0f gaps=%d"
              % (name, a["identical_bases"], a["aligned_length"], a["mean_pident"],
                 a["total_bitscore"], 100 * a["mean_coverage_ref"],
                 100 * a["mean_coverage_read"], a["mean_longest_perfect"],
                 a["mean_read_len"], a["total_gaps"]), flush=True)
    json.dump({"configs": {k: v for k, v in CONFIGS.items()}, "results": out},
              open(os.path.join(_HERE, "report_grid.json"), "w"), indent=2, default=str)
    print("wrote report_grid.json")


if __name__ == "__main__":
    main()
