"""Sweep the *tail aggressiveness* of the position profile.

The profiled pull-back (0.008 -> 0.001) is what recovers the degraded 3' tail,
but the loose tail also over-calls (ours 1,301 insertions vs DLL 501), which
lowers identity and breaks the longest error-free run. Sweep the tail end
values of pullback / window / min_prominence to find a config that keeps
matched bases (~816/well) while cutting insertions and lifting the longest run.

Usage:
    BLAST_DIR=/path/to/ncbi-blast-*/bin python exp_profile3.py
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
    "base": P(),
    "pb_0.002": P(pullback_weight=(0.008, 0.002)),
    "pb_0.003": P(pullback_weight=(0.008, 0.003)),
    "pb_0.004": P(pullback_weight=(0.008, 0.004)),
    "pb_0.005": P(pullback_weight=(0.008, 0.005)),
    "pb_0.006": P(pullback_weight=(0.008, 0.006)),
    "win_1.00": P(window_frac=(0.75, 1.00)),
    "win_1.10": P(window_frac=(0.75, 1.10)),
    "win_1.15": P(window_frac=(0.75, 1.15)),
    "mp_0.08": P(min_prominence=(0.05, 0.08)),
    "mp_0.12": P(min_prominence=(0.05, 0.12)),
    "pb_0.003_mp0.08": P(pullback_weight=(0.008, 0.003), min_prominence=(0.05, 0.08)),
    "pb_0.004_mp0.08": P(pullback_weight=(0.008, 0.004), min_prominence=(0.05, 0.08)),
    "pb_0.004_win1.1": P(pullback_weight=(0.008, 0.004), window_frac=(0.75, 1.10)),
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
        ins = sum(1 for a, b in zip(f[11], f[12]) if b == "-" and a != "-")
        recs.append((f[0], float(f[8]), int(f[4]), int(f[6]), ins, int(f[7])))
    return recs


def main():
    blastn = be._blast_bin("blastn")
    db = os.path.join(be.WORK, "m13db")
    wells = sorted(os.path.basename(f)[:-4] for f in glob.glob(os.path.join(RSD, "*.rsd")))
    out = {}
    for name, cfg in CONFIGS.items():
        fa = os.path.join(be.WORK, "prof3_%s.fasta" % name)
        seqs = {w: call_well(os.path.join(RSD, w + ".rsd"), cfg) for w in wells}
        with open(fa, "w") as fh:
            for w, s in seqs.items():
                fh.write(">%s\n%s\n" % (w, s))
        recs = run_records(blastn, db, fa)
        n = len(recs)
        matched = sum(r[2] for r in recs) / n
        bits = sum(r[1] for r in recs) / n
        gaps = sum(r[3] for r in recs)
        ins = sum(r[4] for r in recs)
        rlen = sum(r[5] for r in recs) / n
        agg = be._agg(be._run(blastn, db, fa), be._ref_len(os.path.join(be.WORK, "M77815.1.fasta")))
        pb = [cm.perbase_vs_ref(s) for s in seqs.values()]
        agg["perbase_vs_ref"] = sum(v for v in pb if v is not None) / len(pb)
        agg["mean_matched"] = matched
        agg["total_insertions"] = ins
        agg["mean_read_len_precise"] = rlen
        out[name] = agg
        print("%-18s matched/w=%.1f bits/w=%.1f %%ID=%.2f covr=%.2f%% longN=%.1f longmed=%.0f gaps=%-5d ins=%-5d rlen=%.0f canon=%.2f"
              % (name, matched, bits, agg["mean_pident"], 100 * agg["mean_coverage_read"],
                 agg["mean_longest_perfect"], agg["median_longest_perfect"], gaps, ins,
                 rlen, agg["perbase_vs_ref"]), flush=True)
    json.dump({"results": out}, open(os.path.join(_HERE, "report_profile3.json"), "w"),
              indent=2, default=str)
    print("wrote report_profile3.json")


if __name__ == "__main__":
    main()
