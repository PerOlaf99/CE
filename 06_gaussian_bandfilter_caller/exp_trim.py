"""Sweep read-trimming aggressiveness and re-score with NCBI BLAST+.

Motivation: we lead Cimarron 3.12 on total identical bases and on aligned
length, but trail on %identity / bit score / longest error-free stretch. The
degraded 3' tail of each read contributes mismatches and gaps; trimming it
should raise %ID, longest error-free stretch and (per the BLAST scoring
scheme, where a low-identity tail removes more than it adds) bit score, at the
cost of raw coverage.

We basecall every well ONCE with auto_trim=False, cache the untrimmed tracked
bases, then replay several trims offline:

  pct<p>   trim_to_quality_block(min_quality_percentile=p)
  mott<c>  trim_mott(quality_cutoff=c)
  tail<n>  hard truncate the last n% of the read

Each variant is scored with NCBI BLAST+ megablast (best HSP per read) against
M77815.1, reporting the same metric set as blast_eval.py.

Usage:
    BLAST_DIR=/path/to/ncbi-blast-*/bin python exp_trim.py [--cache trim_cache.pkl]
"""
import argparse
import glob
import json
import os
import pickle
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

from cimarron_basecaller.rsd_io import read_rsd, to_acgt_trace
from cimarron_basecaller import track_bases
from cimarron_basecaller.spacing_caller import trim_to_quality_block, trim_mott
from call_plate import WIN_CONFIG
import blast_eval as be

RSD = os.path.join(_HERE, "..", "MB1000_M13_DT")
BASE_ORDER = "ACGT"

PCTS = [10, 15, 20, 25, 30, 35, 40]
MOTTS = [0.02, 0.04, 0.06, 0.08, 0.10, 0.12, 0.15]
TAILS = [10, 20, 30]


def basecall_untripped(cache):
    if os.path.exists(cache):
        return pickle.load(open(cache, "rb"))
    wells = sorted(os.path.basename(f)[:-4] for f in glob.glob(os.path.join(RSD, "*.rsd")))
    data = {}
    for w in wells:
        rsd = read_rsd(os.path.join(RSD, w + ".rsd"))
        trace, order = to_acgt_trace(rsd, base_order="TGCA")
        _seq, _q, results = track_bases(
            trace, base_order=order, auto_trim=False, **WIN_CONFIG)
        data[w] = results
        print("basecalled %s  %d untrimmed bases" % (w, len(results)))
    pickle.dump(data, open(cache, "wb"))
    return data


def variants(data):
    """Yield (variant_name, {well: seq})."""
    for p in PCTS:
        yield "pct%d" % p, {
            w: "".join(BASE_ORDER[b.channel] for b in r[trim_to_quality_block(r, min_quality_percentile=p)[0]:
                                                        trim_to_quality_block(r, min_quality_percentile=p)[1]])
            for w, r in data.items()}
    for c in MOTTS:
        yield "mott%.2f" % c, {
            w: "".join(BASE_ORDER[b.channel] for b in r[trim_mott(r, quality_cutoff=c)[0]:
                                                        trim_mott(r, quality_cutoff=c)[1]])
            for w, r in data.items()}
    for t in TAILS:
        yield "tail%d" % t, {
            w: "".join(BASE_ORDER[b.channel] for b in r[:int(len(r) * (100 - t) / 100.0)])
            for w, r in data.items()}


def write_fasta(seqs, path):
    with open(path, "w") as fh:
        for w, s in seqs.items():
            fh.write(">%s\n%s\n" % (w, s))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache", default=os.path.join(_HERE, "trim_cache.pkl"))
    args = ap.parse_args()

    blastn, makeblastdb = be._blast_bin("blastn"), be._blast_bin("makeblastdb")
    data = basecall_untripped(args.cache)

    os.makedirs(be.WORK, exist_ok=True)
    ref = be._fetch_ref(os.path.join(be.WORK, "M77815.1.fasta"))
    ref_len = be._ref_len(ref)
    db = os.path.join(be.WORK, "m13db")
    if not os.path.exists(db + ".ndb"):
        import subprocess
        subprocess.run([makeblastdb, "-in", ref, "-dbtype", "nucl", "-out", db],
                       capture_output=True, text=True, check=True)

    results = {}
    for name, seqs in variants(data):
        fa = os.path.join(be.WORK, "variant_%s.fasta" % name)
        write_fasta(seqs, fa)
        results[name] = be._agg(be._run(blastn, db, fa), ref_len)
        a = results[name]
        print("%-9s id=%-7d len=%-7d %%ID=%.2f bits=%-9.0f refcov=%.2f%% readcov=%.2f%% "
              "longest=%.0f readlen=%.0f gaps=%d"
              % (name, a["identical_bases"], a["aligned_length"], a["mean_pident"],
                 a["total_bitscore"], 100 * a["mean_coverage_ref"],
                 100 * a["mean_coverage_read"], a["mean_longest_perfect"],
                 a["mean_read_len"], a["total_gaps"]))

    out = {"baseline_untrimmed_cfg": WIN_CONFIG, "ref_len": ref_len, "variants": results}
    json.dump(out, open(os.path.join(_HERE, "report_trim_sweep.json"), "w"), indent=2)
    print("\nwrote report_trim_sweep.json")


if __name__ == "__main__":
    main()
