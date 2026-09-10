"""Phred quality-score estimation from basecaller confidence.

Converts per-base softmax probabilities (pmax) into Phred Q-scores
using calibrated mapping derived from empirical error rates on the
MB1000/M13 training plate.

Q = -10 * log10(p_error)   where p_error = 1 - pmax
"""
import numpy as np
import json
import os


def pmax_to_phred(pmax):
    """Convert raw softmax confidence to Phred quality score.

    Q = -10 * log10(max(1 - pmax, 1e-15))

    Returns array of int8 Phred scores clamped to [0, 93].
    """
    p = np.asarray(pmax, dtype=np.float64)
    p_err = np.clip(1.0 - p, 1e-15, 1.0)
    q = -10.0 * np.log10(p_err)
    return np.clip(np.round(q), 0, 93).astype(np.int8)


def phred_to_prob(q):
    """Convert Phred score back to error probability."""
    q = np.asarray(q, dtype=np.float64)
    return np.power(10.0, -q / 10.0)


def confidence_to_phred(confidences):
    """Convert a list/array of per-base confidence values (0-1) to
    Phred Q-scores.  confidences can be in 0-1 float or 0-100 percent."""
    c = np.asarray(confidences, dtype=np.float64)
    if c.max() > 1.5:
        c = c / 100.0
    return pmax_to_phred(c)


def mean_quality(phred_scores):
    """Mean Phred quality over all non-zero positions."""
    q = np.asarray(phred_scores)
    q = q[q > 0]
    return float(np.mean(q)) if len(q) else 0.0


def median_quality(phred_scores):
    """Median Phred quality."""
    q = np.asarray(phred_scores)
    q = q[q > 0]
    return float(np.median(q)) if len(q) else 0.0


def quality_distribution(phred_scores):
    """Return a dict summarizing quality distribution:
    {q20_bases, q30_bases, total_bases, pct_q20, pct_q30, mean_q, median_q}."""
    q = np.asarray(phred_scores)
    q = q[q > 0]
    total = len(q)
    if total == 0:
        return dict(q20_bases=0, q30_bases=0, total_bases=0,
                    pct_q20=0.0, pct_q30=0.0, mean_q=0.0, median_q=0.0)
    q20 = int(np.sum(q >= 20))
    q30 = int(np.sum(q >= 30))
    return dict(
        q20_bases=q20,
        q30_bases=q30,
        total_bases=total,
        pct_q20=100.0 * q20 / total,
        pct_q30=100.0 * q30 / total,
        mean_q=float(np.mean(q)),
        median_q=float(np.median(q)),
    )


# ── Calibration from empirical data ────────────────────────────────────

def load_calibration(path):
    """Load a calibration curve from JSON.  Returns a callable
    pmax -> Q that interpolates the empirical mapping."""
    with open(path) as f:
        data = json.load(f)
    pmax_arr = np.array(data['pmax'], dtype=np.float64)
    q_arr = np.array(data['phred'], dtype=np.float64)
    return lambda p: float(np.interp(p, pmax_arr, q_arr))


def save_calibration(path, pmax_values, phred_values):
    """Save a calibration curve to JSON."""
    with open(path, 'w') as f:
        json.dump({'pmax': pmax_values.tolist(),
                    'phred': phred_values.tolist()}, f, indent=2)


def build_calibration_from_positions(pmax_array, correct_array):
    """Build a calibration curve from per-position pmax and correctness.

    pmax_array: (N,) softmax confidence for each position
    correct_array: (N,) bool — True if the call matched the reference

    Bins positions by pmax, computes empirical error rate per bin,
    then maps pmax -> Q = -10*log10(error_rate).
    """
    pmax = np.asarray(pmax_array, dtype=np.float64)
    correct = np.asarray(correct_array, dtype=bool)
    bins = np.linspace(0, 1, 21)
    bin_centers = 0.5 * (bins[:-1] + bins[1:])
    bin_qs = np.zeros(len(bin_centers), dtype=np.float64)
    for i in range(len(bins) - 1):
        mask = (pmax >= bins[i]) & (pmax < bins[i + 1])
        n = mask.sum()
        if n < 5:
            bin_qs[i] = max(bin_qs[max(0, i - 1)] - 2, 0)
            continue
        errors = (~correct[mask]).sum()
        err_rate = max(errors / n, 1e-15)
        bin_qs[i] = -10.0 * np.log10(err_rate)
    bin_qs = np.clip(bin_qs, 0, 93)
    return bin_centers, bin_qs
