"""Third-round: tune channel_peak_bonus (and a slightly narrower window) to
maximize %ID and longest error-free stretch WHILE keeping identical bases
above Cimarron 3.12 (72,286). exp_grid2 showed wider windows push %ID up but
drop total correct bases below Cimarron, so here we only nudge the window.

Usage:
    BLAST_DIR=/path/to/ncbi-blast-*/bin python exp_grid3.py
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
    "b1.10": C(channel_peak_bonus=1.10),
    "b1.15": C(channel_peak_bonus=1.15),
    "b1.20": C(channel_peak_bonus=1.20),
    "b1.25": C(channel_peak_bonus=1.25),
    "b1.30": C(channel_peak_bonus=1.30),
    "b1.20_w73": C(channel_peak_bonus=1.20, window_frac=(0.73, 1.27)),
    "b1.25_w73": C(channel_peak_bonus=1.25, window_frac=(0.73, 1.27)),
    "b1.30_w73": C(channel_peak_bonus=1.30, window_frac=(0.73, 1.27)),
    "b1.25_w74": C(channel_peak_bonus=1.25, window_frac=(0.74, 1.26)),
    "b1.30_w74": C(channel_peak_bonus=1.30, window_frac=(0.74, 1.26)),
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
        fa = os.path.join(be.WORK, "g3_%s.fasta" % name)
        with open(fa, "w") as fh:
            for w in wells:
                rsd = read_rsd(os.path.join(RSD, w + ".rsd"))
                trace, order = to_acgt_trace(rsd, base_order="TGCA")
                seq, _q, _r = track_bases(trace, base_order=order, **cfg)
                fh.write(">%s\n%s\n" % (w, seq))
        a = be._agg(be._run(blastn, db, fa), ref_len)
        out[name] = a
        beat = "BEATS" if a["identical_bases"] > 72286 else "loses"
        print("%-12s id=%-7d len=%-7d %%ID=%.2f bits=%-9.0f refcov=%.2f%% readcov=%.2f%% "
              "longest=%.1f readlen=%.0f gaps=%d  [%s cmr id]"
              % (name, a["identical_bases"], a["aligned_length"], a["mean_pident"],
                 a["total_bitscore"], 100 * a["mean_coverage_ref"],
                 100 * a["mean_coverage_read"], a["mean_longest_perfect"],
                 a["mean_read_len"], a["total_gaps"], beat), flush=True)
    json.dump({"results": out}, open(os.path.join(_HERE, "report_grid3.json"), "w"),
              indent=2, default=str)
    print("wrote report_grid3.json")


if __name__ == "__main__":
    main()
