"""Quality-based sequence trimming.

Sliding-window and trailing-trim algorithms for removing low-quality
read ends — standard in Sanger sequencing workflows.
"""
import numpy as np


def sliding_window_trim(sequence, phred_scores, window=20, threshold=20,
                        min_length=50):
    """Slide a window across the sequence; trim where the rolling mean
    Phred drops below ``threshold``.

    Returns (trim_start, trim_end, trimmed_seq, trimmed_phred).
    The window starts from the left and from the right; the wider
    trim wins (conservative).
    """
    seq = list(sequence)
    q = np.asarray(phred_scores, dtype=np.float64)
    n = len(q)
    if n == 0:
        return 0, 0, '', np.array([], dtype=np.int8)
    w = min(window, n)
    # left trim: find first position where rolling mean >= threshold
    left = 0
    for i in range(0, n - w + 1):
        if q[i:i + w].mean() >= threshold:
            left = i
            break
    else:
        left = n
    # right trim: find last position where rolling mean >= threshold
    right = n
    for i in range(n - w, -1, -1):
        if q[i:i + w].mean() >= threshold:
            right = i + w
            break
    else:
        right = 0
    # enforce minimum length from the best region
    if right - left < min_length and n >= min_length:
        center = n // 2
        left = max(0, center - min_length // 2)
        right = min(n, left + min_length)
    trimmed_seq = ''.join(seq[left:right])
    trimmed_q = q[left:right].astype(np.int8)
    return left, right, trimmed_seq, trimmed_q


def trailing_trim(sequence, phred_scores, threshold=20, min_length=50):
    """Trim from both ends until Phred >= threshold is found.

    Simpler than sliding window — just finds the first/last high-quality
    base from each end.
    """
    q = np.asarray(phred_scores, dtype=np.float64)
    n = len(q)
    if n == 0:
        return 0, 0, '', np.array([], dtype=np.int8)
    left = 0
    for i in range(n):
        if q[i] >= threshold:
            left = i
            break
    else:
        left = n
    right = n
    for i in range(n - 1, -1, -1):
        if q[i] >= threshold:
            right = i + 1
            break
    else:
        right = 0
    if right - left < min_length and n >= min_length:
        center = n // 2
        left = max(0, center - min_length // 2)
        right = min(n, left + min_length)
    return left, right, sequence[left:right], q[left:right].astype(np.int8)


def window_mask(phred_scores, window=20, threshold=20):
    """Return a boolean mask marking positions inside quality-acceptable
    windows.  Useful for visualization (shade low-quality regions)."""
    q = np.asarray(phred_scores, dtype=np.float64)
    n = len(q)
    mask = np.zeros(n, dtype=bool)
    w = min(window, n)
    for i in range(n - w + 1):
        if q[i:i + w].mean() >= threshold:
            mask[i:i + w] = True
    return mask


def compute_error_probs(phred_scores):
    """Return per-base error probabilities from Phred scores."""
    q = np.asarray(phred_scores, dtype=np.float64)
    return np.power(10.0, -q / 10.0)


def expected_errors(phred_scores):
    """Total expected errors across the sequence."""
    return float(np.sum(compute_error_probs(phred_scores)))
