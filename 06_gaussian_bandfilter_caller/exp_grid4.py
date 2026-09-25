"""Fourth-round: push channel_peak_bonus below 1.10 (higher bit score / %ID /
longest error-free) and combine with local_norm_window, while keeping
identical bases above Cimarron 3.12 (72,286).

Usage:
    BLAST_DIR=/path/to/ncbi-blast-*/bin python exp_grid4.py
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
    "b1.10": C(channel_peak_bonus=1.10),
    "b1.00": C(channel_peak_bonus=1.00),
    "b1.05": C(channel_peak_bonus=1.05),
    "b1.08": C(channel_peak_bonus=1.08),
    "b1.12": C(channel_peak_bonus=1.12),
    "b1.10_nnw2000": C(channel_peak_bonus=1.10, local_norm_window=2000),
    "b1.10_nnw2200": C(channel_peak_bonus=1.10, local_norm_window=2200),
    "b1.05_nnw2000": C(channel_peak_bonus=1.05, local_norm_window=2000),
    "b1.08_nnw2000": C(channel_peak_bonus=1.08, local_norm_window=2000),
    "b1.10_w76": C(channel_peak_bonus=1.10, window_frac=(0.76, 1.24)),
    "b1.05_w76": C(channel_peak_bonus=1.05, window_frac=(0.76, 1.24)),
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
        fa = os.path.join(be.WORK, "g4_%s.fasta" % name)
        with open(fa, "w") as fh:
            for w in wells:
                rsd = read_rsd(os.path.join(RSD, w + ".rsd"))
                trace, order = to_acgt_trace(rsd, base_order="TGCA")
                seq, _q, _r = track_bases(trace, base_order=order, **cfg)
                fh.write(">%s\n%s\n" % (w, seq))
        a = be._agg(be._run(blastn, db, fa), ref_len)
        out[name] = a
        beat = "BEATS" if a["identical_bases"] > 72286 else "loses"
        print("%-15s id=%-7d len=%-7d %%ID=%.2f bits=%-9.0f refcov=%.2f%% readcov=%.2f%% "
              "longest=%.1f gaps=%d  [%s]"
              % (name, a["identical_bases"], a["aligned_length"], a["mean_pident"],
                 a["total_bitscore"], 100 * a["mean_coverage_ref"],
                 100 * a["mean_coverage_read"], a["mean_longest_perfect"],
                 a["total_gaps"], beat), flush=True)
    json.dump({"results": out}, open(os.path.join(_HERE, "report_grid4.json"), "w"),
              indent=2, default=str)
    print("wrote report_grid4.json")


if __name__ == "__main__":
    main()
