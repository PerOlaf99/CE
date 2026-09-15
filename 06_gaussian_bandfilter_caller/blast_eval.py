"""Measure correctly-called bases with NCBI BLAST+ against the M13 reference.

This is the authoritative comparison metric for this folder: it uses the real
NCBI BLAST+ megablast engine (the same algorithm as the NCBI web BLAST URL
API) against the NCBI M13mp18 reference (M77815.1), rather than a local
aligner. It reports, per well and aggregated, for our calls and for the
Cimarron 3.12 ESD calls:

  identical bases        total matching bases in the best HSP
  aligned length         HSP length
  mean % identity        pident of the best HSP
  bit score              BLAST bit score of the best HSP
  % coverage (ref)       HSP length / reference length
  % coverage (read)      HSP length / called read length
  longest error-free     longest run of consecutive matches along the HSP
  mean read length       called length
  total gaps             gaps in the HSP

Requires the NCBI BLAST+ binaries (blastn, makeblastdb) on PATH or pointed to
by the BLAST_DIR environment variable, e.g.:
    BLAST_DIR=/path/to/ncbi-blast-2.17.0+/bin python blast_eval.py

Usage:
    python blast_eval.py [--out report_blast.json]
"""
import glob
import json
import os
import re
import shutil
import statistics
import subprocess
import urllib.request

_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO = os.path.dirname(_HERE)
CALLS = os.path.join(_HERE, "basecalls")
ESD = os.path.join(_REPO, "ground_truth", "MB1000_M13_DT_Cp312_MD1")
RSD = os.path.join(_REPO, "MB1000_M13_DT")
WORK = os.path.join(_HERE, "blast_work")
REF_ID = "M77815.1"


def _blast_bin(name):
    d = os.environ.get("BLAST_DIR")
    if d and os.path.exists(os.path.join(d, name)):
        return os.path.join(d, name)
    p = shutil.which(name)
    if p:
        return p
    for pat in ("/tmp/opencode/ncbi-blast-*/bin/" + name,
                os.path.expanduser("~/ncbi-blast-*/bin/" + name)):
        hit = sorted(glob.glob(pat))
        if hit:
            return hit[-1]
    raise SystemExit("BLAST+ %s not found; set BLAST_DIR" % name)


def _fetch_ref(path):
    if os.path.exists(path):
        return path
    url = ("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
           "?db=nuccore&id=%s&rettype=fasta&retmode=text" % REF_ID)
    txt = urllib.request.urlopen(url, timeout=60).read().decode()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, "w").write(txt)
    return path


def _ref_len(path):
    return sum(len(l.strip()) for l in open(path) if not l.startswith(">"))


def _esd_seq(path):
    raw = open(path, "rb").read()
    idx = -1
    while True:
        idx = raw.find(b"SEQUENCE", idx + 1)
        if idx < 0:
            return None
        np_ = idx + 8
        if np_ + 3 >= len(raw) or raw[np_] != 0:
            continue
        tb, lo, hi = raw[np_ + 1], raw[np_ + 2], raw[np_ + 3]
        if tb == 0x06 and 100 < (lo + (hi << 8)) < 5000:
            length, ds = lo + (hi << 8), np_ + 4
        elif tb == 0x05 and 100 < lo < 1000:
            length, ds = lo, np_ + 3
        else:
            continue
        return "".join(c for c in raw[ds:ds + length].decode("ascii", "replace")
                       if c in "ACGTNacgtn").upper()


def _longest_perfect(qseq, sseq):
    """Longest run of consecutive identical columns (gaps break the run)."""
    best = run = 0
    for a, b in zip(qseq, sseq):
        if a != "-" and a == b:
            run += 1
            best = max(best, run)
        else:
            run = 0
    return best


def _run(blastn, db, fasta):
    fmt = "6 qseqid sseqid pident length nident mismatch gaps qlen bitscore qseq sseq"
    p = subprocess.run([blastn, "-task", "megablast", "-query", fasta, "-db", db,
                        "-outfmt", fmt, "-max_target_seqs", "5", "-evalue", "1e-5"],
                       capture_output=True, text=True)
    best = {}
    for line in p.stdout.splitlines():
        f = line.split("\t")
        if len(f) < 11 or not f[1].startswith(REF_ID):
            continue
        q, bits = f[0], float(f[8])
        if q not in best or bits > best[q]["bitscore"]:
            best[q] = {
                "pident": float(f[2]), "length": int(f[3]), "nident": int(f[4]),
                "mismatch": int(f[5]), "gaps": int(f[6]), "qlen": int(f[7]),
                "bitscore": bits, "longest_perfect": _longest_perfect(f[9], f[10]),
            }
    return best


def _agg(d, ref_len):
    return {
        "n_wells": len(d),
        "identical_bases": sum(v["nident"] for v in d.values()),
        "aligned_length": sum(v["length"] for v in d.values()),
        "total_bitscore": sum(v["bitscore"] for v in d.values()),
        "mean_pident": statistics.mean(v["pident"] for v in d.values()),
        "mean_bitscore": statistics.mean(v["bitscore"] for v in d.values()),
        "mean_coverage_ref": statistics.mean(v["length"] / ref_len for v in d.values()),
        "mean_coverage_read": statistics.mean(v["length"] / v["qlen"] for v in d.values()),
        "mean_longest_perfect": statistics.mean(v["longest_perfect"] for v in d.values()),
        "median_longest_perfect": statistics.median(v["longest_perfect"] for v in d.values()),
        "mean_read_len": statistics.mean(v["qlen"] for v in d.values()),
        "total_gaps": sum(v["gaps"] for v in d.values()),
    }


def main():
    blastn = _blast_bin("blastn")
    makeblastdb = _blast_bin("makeblastdb")
    os.makedirs(WORK, exist_ok=True)
    ref = _fetch_ref(os.path.join(WORK, "M77815.1.fasta"))
    ref_len = _ref_len(ref)
    db = os.path.join(WORK, "m13db")
    subprocess.run([makeblastdb, "-in", ref, "-dbtype", "nucl", "-out", db],
                   capture_output=True, text=True, check=True)
    wells = sorted(os.path.basename(f)[:-4] for f in glob.glob(os.path.join(RSD, "*.rsd")))
    our_fa = os.path.join(WORK, "ours.fasta")
    esd_fa = os.path.join(WORK, "esd.fasta")
    with open(our_fa, "w") as fh:
        for w in wells:
            p = os.path.join(CALLS, w + ".fasta")
            if os.path.exists(p):
                s = "".join(l for l in open(p).read().split("\n") if not l.startswith(">")).strip()
                fh.write(">%s\n%s\n" % (w, s))
    with open(esd_fa, "w") as fh:
        for w in wells:
            s = _esd_seq(os.path.join(ESD, w + ".esd"))
            if s:
                fh.write(">%s\n%s\n" % (w, s))
    o = _agg(_run(blastn, db, our_fa), ref_len)
    e = _agg(_run(blastn, db, esd_fa), ref_len)
    out = {"metric": "NCBI BLAST+ megablast vs %s (M13mp18)" % REF_ID,
           "reference_length": ref_len,
           "ours": o, "cimarron312_esd": e,
           "delta": {k: o[k] - e[k] for k in
                     ("identical_bases", "aligned_length", "total_bitscore",
                      "mean_pident", "mean_bitscore", "mean_coverage_ref",
                      "mean_coverage_read", "mean_longest_perfect",
                      "mean_read_len", "total_gaps")}}
    json.dump(out, open(os.path.join(_HERE, "report_blast.json"), "w"), indent=2)
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
