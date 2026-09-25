"""Sweep Richardson-Lucy iterative deconvolution vs the Wiener band filter.

Goal: reduce per-position substitutions (the longest-run bottleneck) without
losing matched bases, by replacing the fixed Wiener deconvolution with the
non-negative iterative RL form (overshoot attenuated by construction).

Usage:
    BLAST_DIR=/path/to/ncbi-blast-*/bin python exp_deconv.py
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
from call_plate import WIN_CONFIG, FALLBACK_CONFIG, QUALITY_GATE
import blast_eval as be
import canon_metric as cm

RSD = os.path.join(_HERE, "..", "MB1000_M13_DT")
FMT = ("6 qseqid sseqid pident length nident mismatch gaps qlen bitscore "
       "sstart send qseq sseq")


def P(**over):
    d = dict(WIN_CONFIG)
    d.update(over)
    return d


CONFIGS = {
    "w_s1.00_r0.05": P(),
    "w_s0.70_r0.05": P(gaussian_recon_sigma_scale=0.70),
    "w_s0.80_r0.05": P(gaussian_recon_sigma_scale=0.80),
    "w_s0.90_r0.05": P(gaussian_recon_sigma_scale=0.90),
    "w_s1.10_r0.05": P(gaussian_recon_sigma_scale=1.10),
    "w_s1.20_r0.05": P(gaussian_recon_sigma_scale=1.20),
    "w_s0.80_r0.10": P(gaussian_recon_sigma_scale=0.80, gaussian_recon_noise_reg=0.10),
    "w_s0.70_r0.20": P(gaussian_recon_sigma_scale=0.70, gaussian_recon_noise_reg=0.20),
    "w_s1.00_r0.10": P(gaussian_recon_noise_reg=0.10),
    "w_s1.00_r0.20": P(gaussian_recon_noise_reg=0.20),
    "w_s0.85_r0.10": P(gaussian_recon_sigma_scale=0.85, gaussian_recon_noise_reg=0.10),
    "w_s1.00_r0.02": P(gaussian_recon_noise_reg=0.02),
}


def call_well(path, cfg):
    rsd = read_rsd(path)
    trace, order = to_acgt_trace(rsd, base_order="TGCA")
    seq, q, _ = track_bases(trace, base_order=order, **cfg)
    if len(q) == 0 or float(sum(q) / len(q)) < QUALITY_GATE:
        seq, q, _ = track_bases(trace, base_order=order, **FALLBACK_CONFIG)
    return seq


def run_records(blastn, db, fasta):
    p = subprocess.run([blastn, "-task", "megablast", "-query", fasta, "-db", db,
                        "-outfmt", FMT, "-max_target_seqs", "5", "-evalue", "1e-5"],
                       capture_output=True, text=True)
    recs = []
    for line in p.stdout.splitlines():
        f = line.split("\t")
        if len(f) < 13 or not f[1].startswith(be.REF_ID):
            continue
        recs.append((f[0], float(f[8]), int(f[4]), int(f[6]), int(f[3]),
                     sum(1 for a, b in zip(f[11], f[12]) if b == "-" and a != "-"),
                     int(f[7])))
    return recs


def main():
    blastn = be._blast_bin("blastn")
    db = os.path.join(be.WORK, "m13db")
    wells = sorted(os.path.basename(f)[:-4] for f in glob.glob(os.path.join(RSD, "*.rsd")))
    out = {}
    for name, cfg in CONFIGS.items():
        fa = os.path.join(be.WORK, "deconv_%s.fasta" % name)
        seqs = {w: call_well(os.path.join(RSD, w + ".rsd"), cfg) for w in wells}
        with open(fa, "w") as fh:
            for w, s in seqs.items():
                fh.write(">%s\n%s\n" % (w, s))
        recs = run_records(blastn, db, fa)
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
        print("%-16s n=%d matched/w=%.1f bits/w=%.1f %%ID=%.2f longN=%.1f gaps=%-5d ins=%-5d mismatch=%-5d rlen=%.0f canon=%.2f"
              % (name, n, matched, bits, agg["mean_pident"], agg["mean_longest_perfect"],
                 gaps, ins, mismatch, rlen, agg["perbase_vs_ref"]), flush=True)
    json.dump({"results": out}, open(os.path.join(_HERE, "report_deconv.json"), "w"),
              indent=2, default=str)
    print("wrote report_deconv.json")


if __name__ == "__main__":
    main()
