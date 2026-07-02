"""
Python port of TraceTuner's spectral separation (multicomponent) algorithm.
Estimates the 4x4 spectral mixing matrix from raw multi-channel data,
then inverts it via the adjugate matrix to produce unmixed traces.
"""

import numpy as np

NUM_COLORS = 4
NUM_WINDOWS = 40
MIN_WIN_SIZE = 300
NUM_ITERATIONS = 16


def get_baseline(channel: np.ndarray, beg: int, end: int) -> float:
    """Return minimum value in window."""
    return float(np.min(channel[beg:end]))


def get_normfact(channel: np.ndarray, beg: int, end: int) -> float:
    """Return max value (minus baseline=0) in window."""
    return float(np.max(channel[beg:end]))


def is_highest_signal(chromatogram: np.ndarray, color: int, pos: int) -> bool:
    """Check if given channel has the highest signal at this position."""
    sig = chromatogram[color, pos]
    for i in range(NUM_COLORS):
        if i == color:
            continue
        if sig <= chromatogram[i, pos]:
            return False
    return True


def determinant3(m: np.ndarray) -> float:
    """3x3 determinant."""
    return (m[0, 0] * (m[1, 1] * m[2, 2] - m[2, 1] * m[1, 2])
            - m[0, 1] * (m[1, 0] * m[2, 2] - m[2, 0] * m[1, 2])
            + m[0, 2] * (m[1, 0] * m[2, 1] - m[2, 0] * m[1, 1]))


def determinant4(m: np.ndarray) -> float:
    """4x4 determinant via Laplace expansion."""
    det = 0.0
    for i in range(4):
        minor = np.delete(np.delete(m, 0, axis=0), i, axis=1)
        det += ((-1) ** i) * m[0, i] * determinant3(minor)
    return det


def get_minor_matrix(m: np.ndarray) -> np.ndarray:
    """Compute the matrix of minors for a 4x4 matrix."""
    minors = np.zeros((4, 4), dtype=np.float64)
    for i in range(4):
        for j in range(4):
            minor = np.delete(np.delete(m, i, axis=0), j, axis=1)
            minors[i, j] = determinant3(minor)
    return minors


def prebaseline(chromatogram: np.ndarray):
    """Subtract per-window minimum baseline from each channel."""
    npts = chromatogram.shape[1]
    num_wins = NUM_WINDOWS
    win_size = npts // num_wins
    if win_size < MIN_WIN_SIZE:
        win_size = MIN_WIN_SIZE
        num_wins = npts // win_size - 1
    for i in range(num_wins):
        win_beg = win_size * i
        win_end = min(win_size * (i + 1), npts)
        for j in range(NUM_COLORS):
            baseline = get_baseline(chromatogram[j], win_beg, win_end)
            chromatogram[j, win_beg:win_end] -= baseline


def make_multicomponent_iteration(chromatogram: np.ndarray):
    """
    One iteration of multicomponent analysis:
    1. Estimate 4x4 mixing matrix from the data
    2. Compute inverse via adjugate
    3. Apply to unmix channels
    """
    npts = chromatogram.shape[1]
    num_wins = NUM_WINDOWS
    win_size = npts // num_wins
    if win_size < MIN_WIN_SIZE:
        win_size = MIN_WIN_SIZE
        num_wins = npts // win_size - 1

    mcmatrix = np.zeros((NUM_COLORS, NUM_COLORS), dtype=np.float64)
    mcstddev = np.zeros((NUM_COLORS, NUM_COLORS), dtype=np.float64)
    num_good_wins = np.zeros((NUM_COLORS, NUM_COLORS), dtype=np.int32)

    for win in range(num_wins):
        win_beg = win_size * win
        win_end = min(win_size * (win + 1), npts)

        for j in range(NUM_COLORS):
            for k in range(NUM_COLORS):
                if j == k:
                    mcmatrix[j, k] += 1.0
                    continue

                min_sig_ratio = float('inf')

                for pos in range(win_beg, win_end):
                    if not is_highest_signal(chromatogram, k, pos):
                        continue
                    if chromatogram[k, pos] <= 0:
                        continue

                    numer = float(chromatogram[j, pos])
                    denom = float(chromatogram[k, pos])
                    ratio = numer / denom
                    if ratio < min_sig_ratio:
                        min_sig_ratio = ratio

                if min_sig_ratio < 1.0:
                    mcmatrix[j, k] += min_sig_ratio
                    mcstddev[j, k] += min_sig_ratio * min_sig_ratio
                    num_good_wins[j, k] += 1

    # Average over windows
    for j in range(NUM_COLORS):
        for k in range(NUM_COLORS):
            if j != k and num_good_wins[j, k] > 0:
                mcmatrix[j, k] /= num_good_wins[j, k]

    det4 = determinant4(mcmatrix)
    if abs(det4) < 1e-10:
        return  # matrix is singular, skip

    # Compute matrix of minors (adjugate)
    mcminmat = get_minor_matrix(mcmatrix)

    # Apply: new[j] = sum_k (-1)^(j+k) * raw[k] * minor[k][j]
    new_chrom = np.zeros_like(chromatogram)
    for m in range(num_wins):
        win_beg = win_size * m
        win_end = min(win_size * (m + 1), npts)
        for j in range(NUM_COLORS):
            for i in range(win_beg, win_end):
                val = 0.0
                for k in range(NUM_COLORS):
                    val += ((-1) ** (j + k)) * chromatogram[k, i] * mcminmat[k, j]
                new_chrom[j, i] = val

    # Replace original with separated (clip negatives)
    np.copyto(chromatogram, new_chrom)
    chromatogram[chromatogram < 0] = 0


def multicomponent_data(chromatogram: np.ndarray):
    """Run multicomponent separation for N iterations,
    with baseline correction between each."""
    for it in range(NUM_ITERATIONS):
        make_multicomponent_iteration(chromatogram)
        prebaseline(chromatogram)


def trace_tuner_separate(raw_traces: np.ndarray) -> np.ndarray:
    """
    Apply TraceTuner spectral separation to raw 4-channel traces.

    Parameters
    ----------
    raw_traces : np.ndarray of shape (4, n_scans)
        Raw 4-channel trace data (e.g. from RSD file)

    Returns
    -------
    separated : np.ndarray of shape (4, n_scans)
        Spectrally separated traces
    """
    traces = raw_traces.astype(np.float64).copy()

    # Step 1: prefilter and prebaseline
    prebaseline(traces)

    # Step 2: multicomponent separation (16 iterations)
    multicomponent_data(traces)

    return traces
