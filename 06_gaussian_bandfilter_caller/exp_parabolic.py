"""Experiment: sub-sample (parabolic/quadratic) peak localization, as the
Cimarron DLL does via BandStat::squad/gquad + iquadratic/dquadratic.

track_bases updates its spacing EMA from the integer argmax position. Here we
refine the peak position with a 3-point parabolic fit (the standard quadratic
peak estimator) and feed the sub-sample position into the spacing update.
"""
import glob
import os
import statistics
import subprocess
import sys

import numpy as np

sys.path.insert(0, "/tmp/opencode/ce_repo/06_gaussian_bandfilter_caller")
from cimarron_basecaller.spacing_caller import (
    TrackedBase, DEFAULT_CHM, DEFAULT_MOBILITY_SHIFTS, trim_to_quality_block,
    smooth_trace, apply_spectral_separation, detect_signal_region,
    estimate_global_spacing, precompute_channel_peak_masks,
    apply_gaussian_reconstruction_windowed,
)
from cimarron_basecaller.simple_caller import (
    robust_baseline_subtract, normalize_channels_local, apply_mobility_correction,
)
from cimarron_basecaller.rsd_io import read_rsd, to_acgt_trace

RSD = "/tmp/opencode/ce_repo/MB1000_M13_DT"
BLASTN = "/tmp/opencode/ncbi-blast-2.17.0+/bin/blastn"
DB = "/tmp/opencode/rsd/m13db"
WORK = "/tmp/opencode/rsd/exp_para"

CFG = dict(window_frac=(0.75, 1.25), local_norm_window=1800,
           channel_peak_bonus=1.6, pullback_weight=0.019, ema_alpha=0.10,
           gaussian_recon_segment_size=384)


def parabolic_offset(env, p):
    if p <= 0 or p >= len(env) - 1:
        return 0.0
    y0, y1, y2 = env[p - 1], env[p], env[p + 1]
    denom = y0 - 2.0 * y1 + y2
    if denom == 0:
        return 0.0
    d = 0.5 * (y0 - y2) / denom
    return float(np.clip(d, -0.5, 0.5))


def call(trace, mode):
    baseline = robust_baseline_subtract(smooth_trace(trace, 2), window=151)
    baseline = apply_spectral_separation(baseline, DEFAULT_CHM)
    baseline = apply_mobility_correction(baseline, DEFAULT_MOBILITY_SHIFTS)
    norm = normalize_channels_local(baseline, window=CFG["local_norm_window"])
    env0 = norm.max(axis=1)
    s0, e0 = detect_signal_region(baseline)
    gsp = estimate_global_spacing(env0, s0, e0)
    norm = apply_gaussian_reconstruction_windowed(
        norm, np.full(norm.shape[0], gsp), segment_size=CFG["gaussian_recon_segment_size"])
    norm = np.clip(norm, 0, None)
    mask = precompute_channel_peak_masks(norm)
    boosted = norm * (1.0 + mask.astype(float) * CFG["channel_peak_bonus"])
    env = boosted.max(axis=1)
    best = boosted.argmax(axis=1)
    n = len(env)
    sig_start, sig_end = detect_signal_region(baseline)
    gsp = estimate_global_spacing(env, sig_start, sig_end)
    pos = float(sig_start)
    spacing = gsp
    misses = 0
    res = []
    while pos < n - 1:
        expected = pos + spacing
        lo = int(expected - spacing * (1 - CFG["window_frac"][0]))
        hi = int(expected + spacing * (CFG["window_frac"][1] - 1))
        lo = max(lo, int(pos) + 2)
        hi = min(hi, n - 1)
        if lo > hi:
            break
        w = env[lo:hi + 1]
        off = int(np.argmax(w))
        peak = lo + off
        val = float(w[off])
        if val < 0.05:
            misses += 1
            pos = expected
            if misses > 6:
                break
            continue
        misses = 0
        if mode == "ctrl":
            sub = float(peak)
        else:
            sub = peak + parabolic_offset(env, peak)
        observed = sub - pos
        spacing = (1 - CFG["ema_alpha"]) * spacing + CFG["ema_alpha"] * observed
        spacing = (1 - CFG["pullback_weight"]) * spacing + CFG["pullback_weight"] * gsp
        spacing = float(np.clip(spacing, gsp * 0.5, gsp * 2.0))
        res.append(TrackedBase(peak, int(best[peak]), val, expected, spacing))
        pos = sub if mode == "para_float" else float(peak)
    if res:
        a, b = trim_to_quality_block(res, min_quality_percentile=10)
        res = res[a:b]
    return "".join("ACGT"[r.channel] for r in res)


def blast_identical(fasta):
    fmt = "6 qseqid sseqid pident length nident"
    p = subprocess.run([BLASTN, "-task", "megablast", "-query", fasta, "-db", DB,
                        "-outfmt", fmt, "-max_target_seqs", "5", "-evalue", "1e-5"],
                       capture_output=True, text=True)
    best = {}
    for line in p.stdout.splitlines():
        f = line.split("\t")
        if len(f) < 5 or "M77815.1" not in f[1]:
            continue
        if f[0] not in best or int(f[4]) > best[f[0]]:
            best[f[0]] = int(f[4])
    return best, sum(best.values())


def run(mode):
    os.makedirs(WORK, exist_ok=True)
    fasta = os.path.join(WORK, mode + ".fasta")
    wells = sorted(os.path.basename(x)[:-4] for x in glob.glob(os.path.join(RSD, "*.rsd")))
    with open(fasta, "w") as fh:
        for w in wells:
            tr, order = to_acgt_trace(read_rsd(os.path.join(RSD, w + ".rsd")), base_order="TGCA")
            fh.write(">%s\n%s\n" % (w, call(tr, mode)))
    best, total = blast_identical(fasta)
    print("%-10s wells=%d identical=%d" % (mode, len(best), total), flush=True)
    return total


if __name__ == "__main__":
    for m in ("ctrl", "para", "para_float"):
        run(m)
