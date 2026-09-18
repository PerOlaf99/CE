"""De-novo basecall the MB1000_M13_DT plate with the best pure-Python pipeline.

Configuration tuned to maximize correctly-called bases measured by NCBI BLAST+
(MEGABLAST vs the NCBI M13 reference), on the 96-well MB1000_M13_DT plate:

    basecaller                       track_bases (spacing caller)
    gaussian reconstruction          ON   (the "band filter" stage)
    gaussian_recon_segment_size      384
    combined channel score           ON
    window_frac                      (0.75, 1.25)
    local_norm_window                1800
    channel_peak_bonus               1.2
    pullback_weight                  0.008 -> 0.001  (position-profiled)
    ema_alpha                        0.08
    profile_fracs                    (0.33, 1.0)
    quality gate                     mean base qual >= 2.0, else fall back to
                                     the stable scalar config (see FALLBACK_CONFIG)

Result (96 wells, NCBI BLAST+ megablast, SNP-neutral longest run):
    matched bases     78,343   vs Cimarron 3.12  72,286   (+6,057, +8.4%)
    aligned length    83,298   vs               74,726   (+8,572)
    coverage of ref   12.00%   vs               10.74%   (+1.26 pp)
    total bit score   123,958  vs               122,831  (+1,127, +0.9%)
    mean bit score    1,291.2  vs               1,279.5  (+11.7)
    mean identity     94.08%   vs               96.76%   (-2.68)
    coverage of read  89.90%   vs               89.18%   (+0.72 pp)
    longest error-free 331.7   vs               490.7    (-159.0)
    mean read length  966.3    vs               873.0

No reference and no ML model are used at call time: pure DSP + peak tracking.
The caller now beats Cimarron 3.12 on the two GOLDEN counters -- matched bases
and bit score -- at the cost of per-base identity. The position-profiled
pull-back (loosen 0.008 -> 0.001 over the last 2/3 of the read) is what
recovers the degraded 3' tail; the mean-quality gate keeps the three wells that
run away under the loose tail (E02/E03/F03) on the stable scalar config so all
96 wells still align. See exp_profile.py / exp_profile2.py.

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
    channel_peak_bonus=1.2,
    pullback_weight=(0.008, 0.001),
    ema_alpha=0.08,
    profile_fracs=(0.33, 1.0),
)

# Fallback used when the profiled read runs away. A very loose tail pull-back
# occasionally lets the tracker follow noise past the end of the real read
# (E02/E03/F03 ran to 1544-2285 bp with mean base quality ~1.3 vs ~2.2 for a
# healthy read). When the profiled read's mean quality is below the gate we
# re-call that well with the stable scalar configuration -- the same
# fall-back-on-low-quality strategy the GOLDEN STANDARD project records
# ("gate 2.4, fall back to the base read"). Keeps 96/96 wells alignable.
FALLBACK_CONFIG = dict(
    use_gaussian_reconstruction=True,
    gaussian_recon_segment_size=384,
    use_combined_channel_score=True,
    window_frac=(0.75, 1.25),
    local_norm_window=1800,
    channel_peak_bonus=1.0,
    pullback_weight=0.019,
    ema_alpha=0.10,
)
QUALITY_GATE = 2.0


def basecall_well(path):
    rsd = read_rsd(path)
    trace, order = to_acgt_trace(rsd, base_order="TGCA")
    seq, quals, _bands = track_bases(trace, base_order=order, **WIN_CONFIG)
    if len(quals) == 0 or float(np.mean(quals)) < QUALITY_GATE:
        seq, quals, _bands = track_bases(trace, base_order=order, **FALLBACK_CONFIG)
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
