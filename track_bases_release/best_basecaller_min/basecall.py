#!/usr/bin/env python3
"""De-novo MegaBACE M13 basecaller (best tuned configuration).

Reference-free: pure DSP + peak tracking. No reference sequence and no trained
model are used to call bases; the M13 genome is only used for scoring.

Given one .rsd file or a directory of .rsd files, writes one FASTA per well and
a combined FASTA of all reads.

Usage:
    python basecall.py --input /path/to/MB1000_M13_DT --out calls
    python basecall.py --input A01.rsd --out calls
    python basecall.py --input plate_dir --out calls --format fq   # FASTQ with PHRED
"""
import argparse
import glob
import os
import sys

import numpy as np

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

from cimarron_basecaller import track_bases
from cimarron_basecaller.rsd_io import read_rsd, to_acgt_trace

# Best configuration on MB1000_M13_DT.
# Retuned 2026-09-15 on A01/A02/A05 vs Cimarron ESD (SequenceMatcher):
#   original (bonus=1.6): sum_eq=2370 on 3 wells
#   retuned:              sum_eq=2427 on 3 wells (+57 matching bases)
# Main levers: lower channel_peak_bonus (fewer false insertions),
# baseline_window=201, position_adaptive_spectral=True.
WIN_CONFIG = dict(
    use_gaussian_reconstruction=True,
    gaussian_recon_segment_size=384,
    use_combined_channel_score=True,
    window_frac=(0.75, 1.25),
    local_norm_window=1800,
    channel_peak_bonus=1.1,
    pullback_weight=0.019,
    ema_alpha=0.10,
    baseline_window=201,
    position_adaptive_spectral=True,
)

PHRED_OFFSET = 33


def basecall_well(path):
    """Return (sequence, phred_quals) for one .rsd file."""
    rsd = read_rsd(path)
    trace, order = to_acgt_trace(rsd, base_order="TGCA")
    seq, quals, _bands = track_bases(trace, base_order=order, **WIN_CONFIG)
    return seq, np.asarray(quals, dtype=int)


def _write_fasta(fh, name, seq, width=60):
    fh.write(">%s len=%d\n" % (name, len(seq)))
    for i in range(0, len(seq), width):
        fh.write(seq[i:i + width] + "\n")


def _write_fastq(fh, name, seq, quals):
    fh.write("@%s len=%d\n%s\n+\n%s\n" % (
        name, len(seq), seq,
        "".join(chr(min(q, 93) + PHRED_OFFSET) for q in quals)))


def _collect(path):
    if os.path.isdir(path):
        return sorted(glob.glob(os.path.join(path, "*.rsd")))
    if path.lower().endswith(".rsd"):
        return [path]
    raise SystemExit("input must be a .rsd file or a directory of .rsd files")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--input", required=True, help=".rsd file or directory")
    ap.add_argument("--out", required=True, help="output directory")
    ap.add_argument("--format", choices=("fa", "fq"), default="fa",
                    help="fa = FASTA (default), fq = FASTQ with PHRED qualities")
    args = ap.parse_args()

    wells = _collect(args.input)
    if not wells:
        raise SystemExit("no .rsd files found in %s" % args.input)
    os.makedirs(args.out, exist_ok=True)

    ext = ".fasta" if args.format == "fa" else ".fastq"
    combined = os.path.join(args.out, "all_reads" + ext)
    total = 0
    with open(combined, "w") as cf:
        for path in wells:
            name = os.path.splitext(os.path.basename(path))[0]
            seq, quals = basecall_well(path)
            total += len(seq)
            if args.format == "fa":
                with open(os.path.join(args.out, name + ext), "w") as fh:
                    _write_fasta(fh, name, seq)
                _write_fasta(cf, name, seq)
            else:
                with open(os.path.join(args.out, name + ext), "w") as fh:
                    _write_fastq(fh, name, seq, quals)
                _write_fastq(cf, name, seq, quals)
            print("%s  %d calls" % (name, len(seq)))
    print("wrote %d wells (%d bases) to %s" % (len(wells), total, args.out))


if __name__ == "__main__":
    main()
