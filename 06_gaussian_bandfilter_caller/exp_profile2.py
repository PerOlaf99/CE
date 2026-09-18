"""Refinement around the position-profiled config, aiming to raise matched_bp
and cut the gap count the loose tail introduces (gaps 1969 -> ~2500).

Reference (exp_profile.py): g_prof333 = pb(0.008->0.001) from frac 0.33,
matched/w 817.8, bits/w 1290.9, gaps 2538.

Usage:
    BLAST_DIR=/path/to/ncbi-blast-*/bin python exp_profile2.py
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


G = C(pullback_weight=0.008, ema_alpha=0.08, channel_peak_bonus=1.4)
P = (0.008, 0.001)


def Gp(**over):
    d = dict(G)
    d.update(pullback_weight=P, profile_fracs=(0.33, 1.0))
    d.update(over)
    return d


CONFIGS = {
    "g_prof333": Gp(),
    "g_prof333_b1.2": Gp(channel_peak_bonus=1.2),
    "g_prof333_b1.6": Gp(channel_peak_bonus=1.6),
    "g_prof333_mp04": Gp(min_prominence=(0.05, 0.04)),
    "g_prof333_mp045": Gp(min_prominence=(0.05, 0.045)),
    "g_prof333_end5e-4": Gp(pullback_weight=(0.008, 0.0005)),
    "g_prof333_nnw2200": Gp(local_norm_window=2200),
    "g_prof333_win72": Gp(window_frac=(0.72, 1.28)),
    "g_prof333_ema08flat_bonus1.2": Gp(ema_alpha=0.08, channel_peak_bonus=1.2),
    "g_prof333_pbstart012": Gp(pullback_weight=(0.012, 0.001)),
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
        fa = os.path.join(be.WORK, "prof2_%s.fasta" % name)
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
        print("%-26s matched/w=%.1f bits/w=%.1f %%ID=%.2f covr=%.2f%% longN=%.1f "
              "gaps=%-5d canon=%.2f"
              % (name, a["mean_matched"], a["mean_bitscore"], a["mean_pident"],
                 100 * a["mean_coverage_read"], a["mean_longest_perfect"],
                 a["total_gaps"], a["perbase_vs_ref"]), flush=True)
    json.dump({"results": out}, open(os.path.join(_HERE, "report_profile2.json"), "w"),
              indent=2, default=str)
    print("wrote report_profile2.json")


if __name__ == "__main__":
    main()
