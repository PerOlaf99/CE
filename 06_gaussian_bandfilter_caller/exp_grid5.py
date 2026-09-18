"""Fifth-round: probe channel_peak_bonus below 1.0 and its interaction with
local_norm_window / window_frac, scoring with BLAST+ and the repo canonical
perbase metric. Keeps only configs with identical bases above Cimarron
(72,286).

Usage:
    BLAST_DIR=/path/to/ncbi-blast-*/bin python exp_grid5.py
"""
import glob
import json
import os
import subprocess
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)
if os.path.dirname(_HERE) not in sys.path:
    sys.path.insert(0, os.path.dirname(_HERE))

from cimarron_basecaller.rsd_io import read_rsd, to_acgt_trace
from cimarron_basecaller import track_bases
from call_plate import WIN_CONFIG
import blast_eval as be
import canon_metric as cm

RSD = os.path.join(_HERE, "..", "MB1000_M13_DT")
BASE = dict(WIN_CONFIG)


def C(**over):
    d = dict(BASE)
    d.update(over)
    return d


CONFIGS = {
    "b1.00": C(channel_peak_bonus=1.00),
    "b0.95": C(channel_peak_bonus=0.95),
    "b0.90": C(channel_peak_bonus=0.90),
    "b1.02": C(channel_peak_bonus=1.02),
    "b0.95_nnw2200": C(channel_peak_bonus=0.95, local_norm_window=2200),
    "b0.90_nnw2200": C(channel_peak_bonus=0.90, local_norm_window=2200),
    "b1.00_nnw2200": C(channel_peak_bonus=1.00, local_norm_window=2200),
    "b1.00_w74": C(channel_peak_bonus=1.00, window_frac=(0.74, 1.26)),
    "b0.95_w74": C(channel_peak_bonus=0.95, window_frac=(0.74, 1.26)),
    "b0.95_nnw2200_w74": C(channel_peak_bonus=0.95, local_norm_window=2200,
                            window_frac=(0.74, 1.26)),
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
        fa = os.path.join(be.WORK, "g5_%s.fasta" % name)
        seqs = {}
        for w in wells:
            rsd = read_rsd(os.path.join(RSD, w + ".rsd"))
            trace, order = to_acgt_trace(rsd, base_order="TGCA")
            seq, _q, _r = track_bases(trace, base_order=order, **cfg)
            seqs[w] = seq
        with open(fa, "w") as fh:
            for w, s in seqs.items():
                fh.write(">%s\n%s\n" % (w, s))
        a = be._agg(be._run(blastn, db, fa), ref_len)
        pb = [cm.perbase_vs_ref(s) for s in seqs.values()]
        pb = sum(v for v in pb if v is not None) / len(pb)
        a["perbase_vs_ref"] = pb
        out[name] = a
        beat = "BEATS" if a["identical_bases"] > 72286 else "loses"
        print("%-20s id=%-7d %%ID=%.2f bits=%-9.0f longest=%.1f gaps=%-5d canon=%.2f  [%s]"
              % (name, a["identical_bases"], a["mean_pident"], a["total_bitscore"],
                 a["mean_longest_perfect"], a["total_gaps"], pb, beat), flush=True)
    json.dump({"results": out}, open(os.path.join(_HERE, "report_grid5.json"), "w"),
              indent=2, default=str)
    print("wrote report_grid5.json")


if __name__ == "__main__":
    main()
