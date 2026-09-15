"""Experiment: does trace upsampling (DLL-style spline vs Fourier) improve the
NCBI BLAST identical-base count for the track_bases caller?

The Cimarron DLL's rate conversion is cubic-spline based (NR spline/splint,
rawRateCnvrt@Wvfm); its FFT (dfour1 -> NR four1) is used for spectral filters,
not for interpolation. Here we test both a spline upsample and an ideal
Fourier (sinc) upsample at 2x and 4x, with sample-rate-dependent windows scaled.
"""
import glob
import os
import subprocess
import statistics
import sys

import numpy as np
from scipy.signal import resample_poly
from scipy.interpolate import CubicSpline

sys.path.insert(0, "/tmp/opencode/ce_repo/06_gaussian_bandfilter_caller")
from cimarron_basecaller import track_bases
from cimarron_basecaller.rsd_io import read_rsd, to_acgt_trace

RSD = "/tmp/opencode/ce_repo/MB1000_M13_DT"
BLASTN = "/tmp/opencode/ncbi-blast-2.17.0+/bin/blastn"
DB = "/tmp/opencode/rsd/m13db"
WORK = "/tmp/opencode/rsd/exp_up"

BASE = dict(
    use_gaussian_reconstruction=True, gaussian_recon_segment_size=384,
    use_combined_channel_score=True, window_frac=(0.75, 1.25),
    local_norm_window=1800, channel_peak_bonus=1.6,
    pullback_weight=0.019, ema_alpha=0.10,
)


def upsample_fourier(trace, f):
    return resample_poly(trace, f, 1, axis=0)


def upsample_spline(trace, f):
    n = trace.shape[0]
    x = np.arange(n)
    xs = np.linspace(0, n - 1, n * f)
    out = np.empty((len(xs), trace.shape[1]))
    for c in range(trace.shape[1]):
        out[:, c] = CubicSpline(x, trace[:, c])(xs)
    return out


def scaled(base, f):
    cfg = dict(base)
    cfg["baseline_window"] = int(151 * f)
    cfg["local_norm_window"] = int(base["local_norm_window"] * f)
    cfg["gaussian_recon_segment_size"] = int(base["gaussian_recon_segment_size"] * f)
    cfg["smoothing_window"] = max(2, int(2 * f))
    return cfg


def basecall(path, f, method):
    rsd = read_rsd(path)
    trace, order = to_acgt_trace(rsd, base_order="TGCA")
    if f > 1:
        trace = upsample_fourier(trace, f) if method == "four" else upsample_spline(trace, f)
    seq, _q, _b = track_bases(trace, base_order=order, **scaled(BASE, f))
    return seq


def blast_identical(fasta):
    fmt = "6 qseqid sseqid pident length nident"
    p = subprocess.run([BLASTN, "-task", "megablast", "-query", fasta, "-db", DB,
                        "-outfmt", fmt, "-max_target_seqs", "5", "-evalue", "1e-5"],
                       capture_output=True, text=True)
    best = {}
    plen = {}
    for line in p.stdout.splitlines():
        f = line.split("\t")
        if len(f) < 5 or "M77815.1" not in f[1]:
            continue
        q = f[0]
        if q not in best or int(f[4]) > best[q]:
            best[q] = int(f[4])
    return best, sum(best.values()), statistics.mean(best.values())


def run(tag, f, method):
    os.makedirs(WORK, exist_ok=True)
    fasta = os.path.join(WORK, tag + ".fasta")
    wells = sorted(os.path.basename(x)[:-4] for x in glob.glob(os.path.join(RSD, "*.rsd")))
    with open(fasta, "w") as fh:
        for w in wells:
            try:
                s = basecall(os.path.join(RSD, w + ".rsd"), f, method)
            except Exception as e:
                print("  %s failed: %s" % (w, e))
                continue
            fh.write(">%s\n%s\n" % (w, s))
    best, total, mean = blast_identical(fasta)
    print("%-22s f=%d method=%-6s wells=%d identical=%d mean=%.1f" %
          (tag, f, method, len(best), total, mean), flush=True)
    return total


if __name__ == "__main__":
    cfgs = [("ctrl", 1, "none"), ("sp2", 2, "spline"), ("fo2", 2, "four"),
            ("sp4", 4, "spline"), ("fo4", 4, "four")]
    res = {}
    for tag, f, m in cfgs:
        res[tag] = run(tag, f, m)
    print("--- summary identical bases ---")
    for k, v in res.items():
        print("%-6s %d" % (k, v))
