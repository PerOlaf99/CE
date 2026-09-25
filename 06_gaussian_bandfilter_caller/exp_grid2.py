"""Second-round combo search around the accuracy-favouring settings found by
exp_grid.py (lower channel_peak_bonus, wider window_frac, higher
local_norm_window). Goal: maximize total bit score / %ID / longest error-free
stretch while keeping identical bases above Cimarron 3.12 (72,286).

Usage:
    BLAST_DIR=/path/to/ncbi-blast-*/bin python exp_grid2.py
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


WIDE = (0.70, 1.30)

CONFIGS = {
    "base": BASE,
    "b1.2_w70": C(channel_peak_bonus=1.2, window_frac=WIDE),
    "b1.2_w70_nnw2400": C(channel_peak_bonus=1.2, window_frac=WIDE, local_norm_window=2400),
    "b1.2_w70_ema0.08": C(channel_peak_bonus=1.2, window_frac=WIDE, ema_alpha=0.08),
    "b1.2_w70_pb0.016": C(channel_peak_bonus=1.2, window_frac=WIDE, pullback_weight=0.016),
    "b1.35_w70": C(channel_peak_bonus=1.35, window_frac=WIDE),
    "b1.0_w70": C(channel_peak_bonus=1.0, window_frac=WIDE),
    "b1.2_w68": C(channel_peak_bonus=1.2, window_frac=(0.68, 1.32)),
    "b1.2_w72": C(channel_peak_bonus=1.2, window_frac=(0.72, 1.28)),
    "b1.2_w70_nnw2400_ema0.08": C(channel_peak_bonus=1.2, window_frac=WIDE,
                                   local_norm_window=2400, ema_alpha=0.08),
    "b1.35_w70_nnw2400": C(channel_peak_bonus=1.35, window_frac=WIDE, local_norm_window=2400),
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
        fa = os.path.join(be.WORK, "g2_%s.fasta" % name)
        with open(fa, "w") as fh:
            for w in wells:
                rsd = read_rsd(os.path.join(RSD, w + ".rsd"))
                trace, order = to_acgt_trace(rsd, base_order="TGCA")
                seq, _q, _r = track_bases(trace, base_order=order, **cfg)
                fh.write(">%s\n%s\n" % (w, seq))
        a = be._agg(be._run(blastn, db, fa), ref_len)
        out[name] = a
        print("%-27s id=%-7d len=%-7d %%ID=%.2f bits=%-9.0f refcov=%.2f%% readcov=%.2f%% "
              "longest=%.1f readlen=%.0f gaps=%d"
              % (name, a["identical_bases"], a["aligned_length"], a["mean_pident"],
                 a["total_bitscore"], 100 * a["mean_coverage_ref"],
                 100 * a["mean_coverage_read"], a["mean_longest_perfect"],
                 a["mean_read_len"], a["total_gaps"]), flush=True)
    json.dump({"results": out}, open(os.path.join(_HERE, "report_grid2.json"), "w"),
              indent=2, default=str)
    print("wrote report_grid2.json")


if __name__ == "__main__":
    main()
