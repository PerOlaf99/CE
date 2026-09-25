"""Signal processing for capillary sequencing traces.

Baseline subtraction, light smoothing, mobility (dye-specific time-shift)
correction and peak detection.  These operations are shared by the basecaller
and the simulator.
"""

from __future__ import annotations

import numpy as np
from scipy import ndimage, signal as sp_signal


def subtract_baseline(x: np.ndarray, window: int | None = None) -> np.ndarray:
    """Remove the slowly drifting fluorescence baseline of a 1-D trace.

    A morphological opening (rolling minimum then maximum) tracks the local
    baseline; the result is subtracted and clipped at zero.
    """
    x = np.asarray(x, dtype=np.float64)
    n = x.size
    if n == 0:
        return x
    if window is None:
        window = max(128, n // 32)
    if window >= n:
        window = max(1, n // 4)
    opened = ndimage.minimum_filter(x, size=window, mode="reflect")
    opened = ndimage.maximum_filter(opened, size=window // 4 + 1, mode="reflect")
    return np.clip(x - opened, 0.0, None)


def subtract_baseline_multi(traces: np.ndarray, window: int | None = None) -> np.ndarray:
    out = np.empty_like(traces)
    for i in range(traces.shape[0]):
        out[i] = subtract_baseline(traces[i], window)
    return out


def smooth(x: np.ndarray, window: int = 3) -> np.ndarray:
    """Apply a light Savitzky-Golay-like smoothing using a moving average."""
    if window < 2 or x.size < window:
        return x.copy()
    kernel = np.ones(window, dtype=np.float64) / window
    return np.convolve(x, kernel, mode="same")


def _lag_between(a: np.ndarray, b: np.ndarray, max_lag: int) -> int:
    max_lag = min(max_lag, a.size // 4, b.size // 4)
    c = np.correlate(a, b, mode="full")
    mid = c.size // 2
    lo = max(0, mid - max_lag)
    hi = min(c.size, mid + max_lag + 1)
    win = c[lo:hi]
    if win.size == 0:
        return 0
    k = int(np.argmax(win))
    return k - (mid - lo)


def _segment_lag_costs(
    seg: np.ndarray,
    ref: np.ndarray,
    lags_grid: np.ndarray,
) -> np.ndarray:
    """Negative Pearson correlation of ``seg`` against ``ref`` per shift."""
    costs = np.empty(lags_grid.size, dtype=np.float64)
    seg_c = seg - seg.mean()
    ref_c = ref - ref.mean()
    denom = np.linalg.norm(seg_c) * np.linalg.norm(ref_c)
    if denom < 1e-12:
        return np.zeros_like(costs)
    n = seg.size
    for k, lag in enumerate(lags_grid):
        if lag < 0:
            a = seg_c[-lag:]
            b = ref_c[:n + lag]
        elif lag > 0:
            a = seg_c[:n - lag]
            b = ref_c[lag:]
        else:
            a, b = seg_c, ref_c
        num = float(np.dot(a, b))
        an = np.linalg.norm(a)
        bn = np.linalg.norm(b)
        r = num / (an * bn) if an > 1e-12 and bn > 1e-12 else 0.0
        costs[k] = -r
    return costs


def _align_lag_path(costs: np.ndarray, smooth_penalty: float) -> np.ndarray:
    """Viterbi-style path over lags with a continuity prior."""
    n_seg, n_lags = costs.shape
    if n_seg <= 1:
        return np.argmin(costs, axis=1)
    dp = costs.copy()
    back = np.zeros_like(dp, dtype=np.int64)
    for s in range(1, n_seg):
        for k in range(n_lags):
            prev = dp[s - 1] + smooth_penalty * np.abs(np.arange(n_lags) - k)
            j = int(np.argmin(prev))
            dp[s, k] = costs[s, k] + prev[j]
            back[s, k] = j
    path = np.empty(n_seg, dtype=np.int64)
    path[-1] = int(np.argmin(dp[-1]))
    for s in range(n_seg - 1, 0, -1):
        path[s - 1] = back[s, path[s]]
    return path


def align_channels(
    traces: np.ndarray,
    n_segments: int = 16,
    max_lag: int = 12,
    poly_order: int = 2,
    smooth_penalty: float = 1.5,
) -> tuple[np.ndarray, np.ndarray]:
    """Align dye channels to a common time axis.

    Different dyes migrate at slightly different speeds, so a base appears at
    slightly different times in each channel.  For each dye, a segment-wise
    negative-correlation cost against the summed reference is minimised with a
    continuity prior (Viterbi over lags), giving a smooth lag(t) per channel;
    channels are then resampled onto the corrected time axis.

    Returns (aligned_traces, lags) where lags has shape (n_dyes, n_points).
    """
    n_dyes, n = traces.shape
    if n < 64:
        return traces.copy(), np.zeros((n_dyes, n))
    other = np.array([traces.sum(axis=0) - traces[d] for d in range(n_dyes)])
    smooth_other = np.array([smooth(other[d], window=7) for d in range(n_dyes)])
    seg_edges = np.linspace(0, n, n_segments + 1, dtype=int)
    lags_grid = np.arange(-max_lag, max_lag + 1)

    lags = np.zeros((n_dyes, n_segments), dtype=np.float64)
    for d in range(n_dyes):
        sig = smooth(traces[d], window=7)
        costs = np.zeros((n_segments, lags_grid.size))
        for s in range(n_segments):
            lo, hi = seg_edges[s], seg_edges[s + 1]
            if hi - lo < 8:
                costs[s] = np.zeros(lags_grid.size)
                continue
            costs[s] = _segment_lag_costs(sig[lo:hi], smooth_other[d][lo:hi], lags_grid)
        path = _align_lag_path(costs, smooth_penalty)
        lags[d] = lags_grid[path]

    seg_centers = 0.5 * (seg_edges[:-1] + seg_edges[1:])
    t = np.arange(n, dtype=np.float64)
    lag_curves = np.zeros((n_dyes, n), dtype=np.float64)
    for d in range(n_dyes):
        coeffs = np.polyfit(seg_centers, lags[d], poly_order)
        lag_curves[d] = np.polyval(coeffs, t)

    if np.abs(lag_curves).max() < 0.75:
        return traces.copy(), lag_curves

    aligned = np.empty_like(traces)
    for d in range(n_dyes):
        pos = np.clip(t - lag_curves[d], 0, n - 1)
        aligned[d] = np.interp(t, pos, traces[d])
    return aligned, lag_curves


def normalize_channels(traces: np.ndarray, q: float = 99.0) -> np.ndarray:
    """Scale each channel to a comparable dynamic range."""
    out = np.empty_like(traces)
    for i in range(traces.shape[0]):
        row = traces[i]
        m = np.percentile(row, q) if row.size else 1.0
        if m <= 0:
            m = row.max() if row.size else 1.0
        out[i] = row / (m if m > 0 else 1.0)
    return out


def detect_peaks(
    signal: np.ndarray,
    min_distance: int = 4,
    min_prominence: float = 0.0,
) -> tuple[np.ndarray, dict]:
    """Find local maxima; returns (peak_positions, properties_dict)."""
    props = sp_signal.find_peaks(
        signal,
        distance=min_distance,
        prominence=min_prominence,
    )[1]
    peaks = sp_signal.find_peaks(
        signal, distance=min_distance, prominence=min_prominence
    )[0]
    return peaks, props


def _median_band_spacing(sig: np.ndarray, min_distance: int = 3) -> float:
    """Median spacing (samples) between adjacent peaks of a channel."""
    pk, _ = detect_peaks(sig, min_distance=min_distance, min_prominence=0.0)
    if pk.size < 3:
        return 0.0
    gaps = np.diff(pk)
    gaps = gaps[gaps > 0]
    if gaps.size == 0:
        return 0.0
    return float(np.median(gaps))


def _quefrency_lifter(n: int, bgnpt: int, endpt: int) -> np.ndarray:
    """Sine-ramp window on the cepstrum (patent ``bdStatics``).

    Zeros quefrency below ``bgnpt``, ramps ``0.5*(1+sin)`` up to ``endpt``,
    then keeps everything.  Removes the low-quefrency band-shape blur while
    preserving the pulse-train structure.
    """
    lifter = np.ones(n)
    lifter[0] = 0.0
    if n % 2 == 0:
        lifter[n // 2] = 1.0
    m = np.pi / (endpt - bgnpt)
    b = np.pi / 2.0 - m * endpt
    for s in range(1, n // 2):
        if s < bgnpt:
            lifter[s] = 0.0
        elif s <= endpt:
            lifter[s] = 0.5 * (1.0 + np.sin(m * s + b))
        else:
            lifter[s] = 1.0
        lifter[n - s] = lifter[s]
    return lifter


def cepstral_deconvolve(
    traces: np.ndarray,
    window: int = 2048,
    hop: int = 1900,
    bgnpt: int = 13,
    endpt: int = 23,
    crossover: float = 0.23,
    max_fbw: int = 100,
) -> np.ndarray:
    """Blind deconvolution of the band shape (patent EP0944739A1 ``blindeconv``).

    Each channel is processed in overlapping 2048-point segments.  Per segment
    the median band spacing ``p`` sets the reconstruction filter band width
    ``FBW = (K/p)*N/(2*pi)`` with ``K = 2 + sqrt(log(CROSSOVER)/-0.5)`` so that
    the Gaussian filter cut-off follows the local band spacing.  A quefrency
    lifter removes low-quefrency band-shape energy; the phase of the original
    spectrum is restored, the magnitude re-exponentiated, the Gaussian
    low-pass applied and the signal reconstructed.
    """
    n_ch, n_pts = traces.shape
    if n_pts < 64:
        return traces.copy()
    win = np.hanning(window) if window > 1 else np.ones(window)
    K = 2.0 + np.sqrt(np.log(crossover) / -0.5)
    glob_spacing = _median_band_spacing(np.sum(traces, axis=0))

    out = np.zeros((n_ch, n_pts))
    wsum = np.zeros(n_pts)
    starts = list(range(0, n_pts - window + 1, hop))
    if starts[-1] + window < n_pts:
        starts.append(n_pts - window)
    for s0 in starts:
        s1 = s0 + window
        seg = traces[:, s0:s1]
        spacing = _median_band_spacing(np.sum(seg, axis=0))
        if spacing <= 0:
            spacing = glob_spacing
        if spacing <= 0:
            spacing = 16.0
        fbw = int(0.5 + (K / spacing) * window / (2 * np.pi))
        fbw = min(max(fbw, 1), max_fbw)
        lifter = _quefrency_lifter(window, bgnpt, endpt)
        w = 2 * np.pi * np.fft.fftfreq(window)
        fsigma = (fbw - 1) * 2 * np.pi / window
        alpha = 0.5 * fsigma * fsigma
        c = np.sqrt(np.pi / alpha)
        filt = c * np.exp(-(w * w) / (4 * alpha))
        for ch in range(n_ch):
            X = np.fft.fft(seg[ch])
            mag = np.maximum(np.abs(X), 1e-10)
            phase = np.angle(X)
            cep = np.real(np.fft.ifft(np.log(mag)))
            rec = np.exp(np.real(np.fft.fft(cep * lifter)) + 1j * phase)
            y = np.real(np.fft.ifft(rec * filt))
            out[ch, s0:s1] += y * win
        wsum[s0:s1] += win
    keep = wsum > 1e-12
    out[:, keep] /= wsum[keep]
    return out
