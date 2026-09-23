"""Reference-free per-well config selection: can a quality proxy pick the
config that yields the longer error-free run?

The golden (sharp, untrimmed) and precision (blurred, trimmed) calls disagree
well-by-well: golden wins G01/D06/H10, precision wins most others, and the
per-well oracle mean longest is 486.9 vs DLL 490.7.  At call time we cannot
see the true run, so we need a proxy.  Candidate proxies (all scale-free):

  P_med   longest run of bases whose quality >= the read's own median quality
  P_frac  longest run of bases whose quality >= `frac` * max quality
  P_rank  longest run above the `pct`-th quality percentile

For each well we call BOTH configs, then pick the one with the larger proxy and
score the assembled plate.  A proxy that recovers most of the oracle gain is a
legitimate (reference-free) improvement; otherwise it is documented as a
negative result.
"""
import glob
import json
import os
import sys
import subprocess

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

import numpy as np
import call_plate as cp
import blast_eval as be
from cimarron_basecaller.rsd_io import read_rsd, to_acgt_trace
from cimarron_basecaller import track_bases

RSD = os.path.join(_HERE, "..", "MB1000_M13_DT")


def longest_run(mask):
    best = cur = 0
    for v in mask:
        cur = cur + 1 if v else 0
        if cur > best:
            best = cur
    return best


def proxies(quals):
    q = np.asarray(quals, dtype=float)
    if q.size == 0:
        return {}
    out = {"P_med": longest_run(q >= float(np.median(q)))}
    for frac in (0.6, 0.75):
        out["P_frac%.2f" % frac] = longest_run(q >= frac * float(q.max()))
    for pct in (50, 65):
        out["P_rank%d" % pct] = longest_run(q >= float(np.percentile(q, pct)))
    return out


def main():
    blastn = be._blast_bin("blastn")
    db = os.path.join(be.WORK, "m13db")
    ref_len = be._ref_len(os.path.join(be.WORK, "M77815.1.fasta"))
    wells = sorted(os.path.basename(f)[:-4] for f in glob.glob(os.path.join(RSD, "*.rsd")))

    calls = {"gold": {}, "prec": {}}
    prox = {"gold": {}, "prec": {}}
    for w in wells:
        rsd = read_rsd(os.path.join(RSD, w + ".rsd"))
        trace, order = to_acgt_trace(rsd, base_order="TGCA")
        for tag, cfg in (("gold", cp.WIN_CONFIG), ("prec", cp.WIN_CONFIG_PRECISION)):
            seq, q, _ = track_bases(trace, base_order=order, **cfg)
            calls[tag][w] = seq
            prox[tag][w] = proxies(q)

    # truth
    truth = {}
    for tag in ("gold", "prec"):
        fa = os.path.join(be.WORK, "select_%s.fasta" % tag)
        with open(fa, "w") as fh:
            for w in wells:
                fh.write(">%s\n%s\n" % (w, calls[tag][w]))
        truth[tag] = be._run(blastn, db, fa)

    keys = sorted(prox["gold"][wells[0]].keys())
    results = {}
    for k in keys:
        chosen = {w: ("gold" if prox["gold"][w][k] > prox["prec"][w][k] else "prec") for w in wells}
        fa = os.path.join(be.WORK, "select_%s.fasta" % k)
        with open(fa, "w") as fh:
            for w in wells:
                fh.write(">%s\n%s\n" % (w, calls[chosen[w]][w]))
        r = be._run(blastn, db, fa)
        agg = be._agg(r, ref_len)
        n_gold = sum(1 for v in chosen.values() if v == "gold")
        oracle = np.mean([max(truth["gold"][w]["longest_perfect"],
                              truth["prec"][w]["longest_perfect"]) for w in wells])
        results[k] = {"mean_longest": agg["mean_longest_perfect"],
                      "mean_pident": agg["mean_pident"],
                      "mean_bitscore": agg["mean_bitscore"],
                      "n_gold_chosen": n_gold, "oracle_mean_longest": oracle}
        print("%-10s longN=%.1f %%ID=%.2f bits/w=%.1f gold_chosen=%d/96 (oracle %.1f)"
              % (k, agg["mean_longest_perfect"], agg["mean_pident"],
                 agg["mean_bitscore"], n_gold, oracle), flush=True)

    json.dump(results, open(os.path.join(_HERE, "report_select.json"), "w"),
              indent=2, default=str)
    print("wrote report_select.json")


if __name__ == "__main__":
    main()
