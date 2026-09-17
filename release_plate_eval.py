#!/usr/bin/env python3
"""Release-branch plate golden-bar eval (BEST_BASECALLER_RELEASE).

Runs the tuned release caller (configs.py: pos_bonus07 / pos_profile /
hz_soften) over all 96 wells and measures EVERY emitted read on the
GOLDEN_STANDARD bar (GOLDEN_STANDARD.md): matched_bp (THE metric),
coverage, identity, bitscore and the SNP-neutral longest error-free run,
all from ONE blastn megablast invocation per read (numeric + gapped
qseq/sseq columns) so perf and metric stay consistent with plate_golden_eval.

Prints per-config plate standings + the README's ensemble strategy
(pick per well the member with max bitscore x longest_run) + DLL/ESD
reference through the identical pipeline, and the mutation-check.

Usage:
  python3 release_plate_eval.py [--release REL_DIR] [wells...]
"""
import os
import sys
import tempfile
import subprocess
import shutil
import statistics as st
from collections import Counter
from multiprocessing import Pool

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "sanger_toolkit"))

from blast_bench import _ref_seq

PLATE_DIR = os.path.join(HERE, "MB1000_M13_DT", "Analyzed Data",
                         "MB1000_M13_DT_Cp312_MD1")
REL_DIR = "/home/per/Nedlastinger/BEST_BASECALLER_RELEASE"
MUT_MOTIF_READ = "CACCAGTGAGACGG"
CONFIG_ORDER = ["pos_bonus07", "pos_profile", "hz_soften"]


class _G:
    db = None          # (dir, prefix) shared reference DB
    seq_cache = {}


def _make_db():
    td = tempfile.mkdtemp(prefix="m13db_")
    ref = os.path.join(td, "m13.fa")
    with open(ref, "w") as f:
        f.write(">M13mp18\n" + _ref_seq() + "\n")
    prefix = os.path.join(td, "db")
    subprocess.run(["makeblastdb", "-in", ref, "-dbtype", "nucl", "-out", prefix],
                   check=True, capture_output=True)
    _G.db = (td, prefix)


def eval_seq(seq):
    """One blastn per read -> metrics + SNP-neutral longest run."""
    seq = "".join(c for c in seq if c in "ACGT")
    if len(seq) < 30:
        return None
    _G.db, prefix = _G.db, _G.db[1]
    with tempfile.TemporaryDirectory() as qd:
        q = os.path.join(qd, "q.fa")
        with open(q, "w") as f:
            f.write(">q\n" + seq + "\n")
        cp = subprocess.run(
            ["blastn", "-db", prefix, "-query", q, "-task", "megablast",
             "-outfmt",
             "6 qlen qstart qend sstart send pident bitscore length mismatch "
             "gapopen qseq sseq"],
            check=False, capture_output=True, text=True)
        if cp.returncode != 0:
            raise RuntimeError(f"blastn rc={cp.returncode}: {cp.stderr}")
        out = cp.stdout
    rows = [l.split("\t") for l in out.splitlines() if l.strip()]
    if not rows:
        return None
    best = max(rows, key=lambda r: float(r[6]))
    qlen = int(best[0]); qstart = int(best[1]); qend = int(best[2])
    sstart = int(best[3]); send = int(best[4])
    pident = float(best[5]); bitscore = float(best[6])
    ln = int(best[7]); mm = int(best[8]); gaps = int(best[9])
    qseq, sseq = best[10], best[11]
    matched = ln - mm - gaps
    full = 100.0 * matched / qlen if qlen else 0.0
    rev = sstart > send
    longest = run = 0
    for c, (q, s) in enumerate(zip(qseq, sseq)):
        fwd = sstart - c if rev else sstart + c
        if fwd == 5977:
            continue
        if q == "-" or s == "-":
            run = 0
        elif q == s:
            run += 1
            longest = max(longest, run)
        else:
            run = 0
    return {
        "bases": qlen,
        "matched": matched,
        "pident": pident,
        "cov": 100.0 * (qend - qstart + 1) / qlen,
        "id": full,
        "bits": bitscore,
        "run": longest,
    }


def call_config(well, cfg_name, cfg):
    sys.path.insert(0, REL_DIR)
    from cimarron_basecaller.rsd_io import read_rsd, to_acgt_trace
    from cimarron_basecaller.spacing_caller import track_bases
    rsd = read_rsd(os.path.join(PLATE_DIR, well + ".rsd"))
    trace, order = to_acgt_trace(rsd, base_order="TGCA")
    seq, quals, bands = track_bases(trace, base_order=order, **dict(cfg))
    return seq


def process_well(well):
    sys.path.insert(0, REL_DIR)
    from configs import CONFIGS
    import extract_training_data as etd

    dll = etd.parse_esd(os.path.join(PLATE_DIR, well + ".esd"))["sequence"]
    res = {"well": well, "dll": eval_seq(dll)}
    for name in CONFIG_ORDER:
        seq = call_config(well, name, CONFIGS[name])
        res[name] = eval_seq(seq)
        res[name + "_n"] = len(seq)
        res[name + "_mut"] = MUT_MOTIF_READ in seq
        res[name + "_seq"] = seq
    scores = [res[n]["bits"] * res[n]["run"] if res[n] else -1
              for n in CONFIG_ORDER]
    pick = CONFIG_ORDER[int(np.argmax(scores))]
    res["ensemble_pick"] = pick
    res["ensemble"] = res[pick]
    res["ensemble_mut"] = res[pick + "_mut"]
    res["ensemble_seq"] = res[pick + "_seq"]
    return res


def show(label, r):
    if not r:
        print(f"  {label:22s} NO ALIGN")
        return
    print(f"  {label:22s} matched={r['matched']:5.2f}  bases={r['bases']:6.1f}  "
          f"cov={r['cov']:5.1f}  id={r['id']:5.2f}  bits={r['bits']:7.2f}  "
          f"run={r['run']:6.1f}")


def main():
    argv = sys.argv[1:]
    global REL_DIR
    rel = REL_DIR
    if argv and argv[0] == "--release":
        rel, argv = argv[1], argv[1:]
    REL_DIR = rel
    assert os.path.isdir(os.path.join(rel, "cimarron_basecaller")), rel

    if not argv:
        wells = sorted(f[:-4] for f in os.listdir(PLATE_DIR) if f.endswith(".esd"))
    elif all(len(a) <= 2 for a in argv):
        pref = []
        for a in argv:
            if len(a) == 1:
                pref += [f"{a}{c:02d}" for c in range(1, 13)]
            else:
                pref += [f"{r}{int(a[1:]):02d}" for r in "ABCDEFGH"]
        wells = sorted(f[:-4] for f in os.listdir(PLATE_DIR)
                       if f.endswith(".esd") and f[:-4] in pref)
    else:
        wells = argv

    _make_db()
    results = []
    with Pool(8) as pool:
        for r in pool.imap_unordered(process_well, wells):
            results.append(r)
            print(r["well"], {n: r[n]["matched"] for n in CONFIG_ORDER},
                  "dll=", r["dll"]["matched"], "pick=", r["ensemble_pick"],
                  flush=True)

    seq_dir = os.path.join(rel, "plate_calls")
    os.makedirs(seq_dir, exist_ok=True)
    for r in results:
        for n in CONFIG_ORDER + ["ensemble"]:
            nm = n if n != "ensemble" else f"ensemble_{r['ensemble_pick']}"
            with open(os.path.join(seq_dir, f"{r['well']}_{nm}.fasta"), "w") as f:
                f.write(f">{r['well']} {nm}\n{r[n + '_seq']}\n")

    def agg(res, key, pref=""):
        return st.mean([r[key] for r in res]) if res else 0.0

    print("\n=== PLATE STANDINGS (means over %d wells) ===" % len(results))
    dll = [r["dll"] for r in results]
    print("  %-12s %7s %7s %6s %7s %8s %7s %6s %5s" % (
        "caller", "matched", "bases", "cov", "pident", "bits", "run",
        "full-id", ">500"))
    for label, key in [("DLL/ESD", None)] + [(n, n) for n in CONFIG_ORDER] + [
            ("ensemble", "ensemble")]:
        if key is None:
            rr = dll; runs = [x["run"] for x in rr]
        else:
            rr = [r[key] for r in results if r[key]]
            runs = [r[key]["run"] for r in results if r[key]]
        if not rr:
            print(f"  {label:12s} NO ALIGN"); continue
        print("  %-12s %7.2f %7.1f %6.1f %7.2f %8.2f %7.1f %6.2f %5d" % (
            label, agg(rr, "matched"), agg(rr, "bases"), agg(rr, "cov"),
            agg(rr, "pident"), agg(rr, "bits"), agg(rr, "run"),
            agg(rr, "id"), sum(1 for x in runs if x > 500)))
    for label, key, mkey in [(n, n, n + "_mut") for n in CONFIG_ORDER] + [
            ("ensemble", "ensemble", "ensemble_mut")]:
        win = sum(1 for r in results if r[key] and r["dll"] and
                  r[key]["matched"] > r["dll"]["matched"])
        nmut = sum(1 for r in results if r.get(mkey))
        print(f"{label:10s} beats DLL matched: {win}/{len(results)}   "
              f"mutation T kept: {nmut}/{len(results)}")
    print(f"calls written to {seq_dir}/")


if __name__ == "__main__":
    main()