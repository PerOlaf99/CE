#!/usr/bin/env python3
"""Smoke test: run the caller on a synthetic 4-channel trace (no data needed).

    python3 test_smoke.py
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cimarron_basecaller import track_bases

WIN_CONFIG = dict(
    use_gaussian_reconstruction=True, gaussian_recon_segment_size=384,
    use_combined_channel_score=True, window_frac=(0.75, 1.25),
    local_norm_window=1800, channel_peak_bonus=1.6,
    pullback_weight=0.019, ema_alpha=0.10,
)


def synthetic_trace(n=6000, spacing=11, seed=0):
    """A minimal 4-channel trace with evenly spaced Gaussian peaks.

    The caller ignores the first ~1500 scans when locating the signal region,
    so the trace is long enough that real peaks fall inside it.
    """
    rng = np.random.default_rng(seed)
    t = np.arange(n)
    trace = np.zeros((n, 4))
    truth = []
    for i, pos in enumerate(range(80, n - 80, spacing)):
        ch = i % 4
        trace[:, ch] += 1000.0 * np.exp(-0.5 * ((t - pos) / 3.0) ** 2)
        truth.append("ACGT"[ch])
    trace += rng.normal(0, 20.0, trace.shape)
    return trace, "".join(truth)


def main():
    trace, truth = synthetic_trace()
    seq, quals, _bands = track_bases(trace, base_order="ACGT", **WIN_CONFIG)
    print("called %d bases (synthetic peaks %d)" % (len(seq), len(truth)))
    print("first 40:", seq[:40])
    assert len(seq) > 100, "caller returned too few bases"
    assert set(seq) <= set("ACGTN"), "unexpected characters in output"
    assert len(quals) == len(seq), "quality length mismatch"
    print("OK")


if __name__ == "__main__":
    main()
