"""Sweep position-profiled spacing-caller configs against the GOLDEN bar.

Golden standard: NCBI BLAST+ megablast vs M77815.1, per-read best HSP.
  matched_bp   = nident (identical bases)          <- THE acceptance metric
  bitscore     = BLAST bit score
  longest_run  = longest error-free run on the HSP, template mutation fwd 5977
                 treated as NEUTRAL (see blast_eval._longest_perfect)

The golden project records track_bases with a position-profiled pull-back
(0.008 -> 0.001 across the last 2/3 of the read, i.e. profile_fracs=(0.33,1.0))
as beating the DLL on BOTH matched_bp and bitscore. Our vendored track_bases
now supports (start,end) profiles for ema_alpha / pullback_weight /
min_prominence / channel_peak_bonus; this script sweeps them.

Usage:
    BLAST_DIR=/path/to/ncbi-blast-*/bin python exp_profile.py
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


def C(**over):
    d = dict(WIN_CONFIG)
    d.update(over)
    return d


# scalar baselines
CUR = C()
G = C(pullback_weight=0.008, ema_alpha=0.08, channel_peak_bonus=1.4)

CONFIGS = {
    "cur": CUR,
    "g_scalar": G,
    "g_prof333": {**G, "pullback_weight": (0.008, 0.001), "profile_fracs": (0.33, 1.0)},
    "g_prof25": {**G, "pullback_weight": (0.008, 0.001), "profile_fracs": (0.25, 1.0)},
    "g_prof50": {**G, "pullback_weight": (0.008, 0.001), "profile_fracs": (0.50, 1.0)},
    "g_prof333_end2": {**G, "pullback_weight": (0.008, 0.002), "profile_fracs": (0.33, 1.0)},
    "g_prof333_end0": {**G, "pullback_weight": (0.008, 0.0), "profile_fracs": (0.33, 1.0)},
    "g_prof333_pb012": {**G, "pullback_weight": (0.012, 0.001), "profile_fracs": (0.33, 1.0)},
    "cur_prof333": {**CUR, "pullback_weight": (0.019, 0.001), "profile_fracs": (0.33, 1.0)},
    "g_prof333_emaramp": {**G, "pullback_weight": (0.008, 0.001), "profile_fracs": (0.33, 1.0),
                          "ema_alpha": (0.08, 0.06)},
    "g_prof333_minprom": {**G, "pullback_weight": (0.008, 0.001), "profile_fracs": (0.33, 1.0),
                          "min_prominence": (0.05, 0.03)},
    "g_prof80": {**G, "pullback_weight": (0.008, 0.001), "profile_fracs": (0.80, 1.0)},
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
        fa = os.path.join(be.WORK, "prof_%s.fasta" % name)
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
        a["perbase_vs_ref"] = sum(v for v in pb if v is not None) / len(pb)
        a["mean_matched"] = a["identical_bases"] / a["n_wells"]
        out[name] = a
        print("%-18s matched/w=%.1f tot=%-7d bits/w=%.1f %%ID=%.2f covr=%.2f%% "
              "longN=%.1f longRAW=%.1f gaps=%-5d canon=%.2f"
              % (name, a["mean_matched"], a["identical_bases"], a["mean_bitscore"],
                 a["mean_pident"], 100 * a["mean_coverage_read"],
                 a["mean_longest_perfect"], a["mean_longest_perfect_raw"],
                 a["total_gaps"], a["perbase_vs_ref"]), flush=True)
    json.dump({"results": out}, open(os.path.join(_HERE, "report_profile.json"), "w"),
              indent=2, default=str)
    print("wrote report_profile.json")


if __name__ == "__main__":
    main()
