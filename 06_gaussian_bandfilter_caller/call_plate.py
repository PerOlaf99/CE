"""De-novo basecall the MB1000_M13_DT plate with the best pure-Python pipeline.

Configuration tuned to maximize correctly-called bases measured by NCBI BLAST+
(MEGABLAST vs the NCBI M13 reference), on the 96-well MB1000_M13_DT plate:

    basecaller                       track_bases (spacing caller)
    gaussian reconstruction          ON   (the "band filter" stage)
    gaussian_recon_segment_size      384
    combined channel score           ON
    window_frac                      (0.75, 1.25)
    local_norm_window                1800
    channel_peak_bonus               1.6
    pullback_weight                  0.019
    ema_alpha                        0.10

Result (96 wells, NCBI BLAST+ vs M13mp18):
    identical bases   73,462   vs Cimarron 3.12  72,313   (+1,149, +1.6%)
    aligned length    77,136   vs               74,780   (+2,356)
    mean identity     95.30%   vs               96.73%   (-1.43)
    mean read length  920.9    vs               873.1

No reference and no ML model are used at call time: pure DSP + peak tracking.
The trade-off is explicit: we call more correct bases and longer reads than
Cimarron 3.12, at lower average identity.

Usage:
    python call_plate.py [--rsd-dir ../MB1000_M13_DT] [--out basecalls]
"""
import argparse
import glob
import os
import sys

import numpy as np

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

from cimarron_basecaller.rsd_io import read_rsd, to_acgt_trace
from cimarron_basecaller import track_bases

WIN_CONFIG = dict(
    use_gaussian_reconstruction=True,
    gaussian_recon_segment_size=384,
    use_combined_channel_score=True,
    window_frac=(0.75, 1.25),
    local_norm_window=1800,
    channel_peak_bonus=1.6,
    pullback_weight=0.019,
    ema_alpha=0.10,
)


def basecall_well(path):
    rsd = read_rsd(path)
    trace, order = to_acgt_trace(rsd, base_order="TGCA")
    seq, quals, _bands = track_bases(trace, base_order=order, **WIN_CONFIG)
    return seq, quals


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rsd-dir", default=os.path.join(_HERE, "..", "MB1000_M13_DT"))
    ap.add_argument("--out", default=os.path.join(_HERE, "basecalls"))
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)
    wells = sorted(os.path.basename(f)[:-4] for f in glob.glob(os.path.join(args.rsd_dir, "*.rsd")))
    if not wells:
        raise SystemExit("no .rsd files found in %s" % args.rsd_dir)
    fasta = []
    for w in wells:
        seq, quals = basecall_well(os.path.join(args.rsd_dir, w + ".rsd"))
        with open(os.path.join(args.out, w + ".fasta"), "w") as fh:
            fh.write(">%s len=%d\n" % (w, len(seq)))
            for i in range(0, len(seq), 60):
                fh.write(seq[i:i + 60] + "\n")
        fasta.append((w, seq))
        print("%s  %d calls" % (w, len(seq)))
    with open(os.path.join(args.out, "plate.fasta"), "w") as fh:
        for w, seq in fasta:
            fh.write(">%s\n" % w)
            for i in range(0, len(seq), 60):
                fh.write(seq[i:i + 60] + "\n")
    print("wrote %d wells to %s" % (len(wells), args.out))


if __name__ == "__main__":
    main()
