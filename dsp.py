"""Signal-processing core for the MegaBACE basecalling pipeline.

Pure functions extracted from sequencing_gui_V15.py.  No Qt, no widgets,
no file I/O — just numpy/scipy math that the GUI and headless callers
both use.

Dependencies: numpy, scipy (ndimage, sparse, signal, spatial), constants.
"""
import os
import numpy as np
from scipy.ndimage import (
    minimum_filter1d, gaussian_filter1d, median_filter,
    maximum_filter1d, grey_opening, uniform_filter1d,
)
from scipy.sparse import diags as sparse_diags
from scipy.sparse.linalg import spsolve
from scipy.signal import savgol_filter

from constants import OFF_PATTERN

# ── File discovery ─────────────────────────────────────────────────────

def find_esd_subdirs(base_dir):
    """Return {well_name: dirname} for *_MD1 ESD subdirectories."""
    dirs = {}
    for d in sorted(os.listdir(base_dir)):
        dp = os.path.join(base_dir, d)
        if os.path.isdir(dp) and d.endswith('_MD1'):
            name = d.replace('MB1000_M13_DT_', '').replace('_MD1', '')
            dirs[name] = d
    return dirs


# ── Matrix helpers ─────────────────────────────────────────────────────

def make_matrix_from_diagonals(diag):
    """Build 4x4 mixing matrix from 4 diagonal values.
    Off-diagonals follow DEFAULT pattern scaled to (1-diag) total bleed."""
    mix = np.zeros((4, 4), dtype=np.float64)
    for col in range(4):
        bleed = 1.0 - diag[col]
        pattern = OFF_PATTERN[:, col].copy()
        pattern[col] = 0
        psum = pattern.sum()
        if psum > 0:
            pattern = pattern / psum * bleed
        pattern[col] = diag[col]
        mix[:, col] = pattern
    return mix


# ── Mobility shift ─────────────────────────────────────────────────────

def dsp_shift_channel(arr, shift):
    """Shift a 1-D array by ``shift`` scans, padding with the edge value
    instead of wrapping. Positive shift delays (peaks move right); negative
    advances (peaks move left)."""
    n = len(arr)
    shift = int(np.clip(shift, -(n - 1), n - 1))
    if shift == 0:
        return arr.copy()
    out = np.empty_like(arr)
    if shift > 0:
        out[:shift] = arr[0]
        out[shift:] = arr[:-shift]
    else:
        k = -shift
        out[-k:] = arr[-1]
        out[:-k] = arr[k:]
    return out


def dsp_apply_mobility_shifts(raw, shifts):
    """raw: (n,4). shifts: length-4 sequence of per-channel scan shifts."""
    out = raw.copy()
    for ch in range(4):
        s = int(shifts[ch])
        if s != 0:
            out[:, ch] = dsp_shift_channel(out[:, ch], s)
    return out


# ── Baseline methods ───────────────────────────────────────────────────

def dsp_airpls_baseline(y, lam, itermax=15):
    """Adaptive iteratively reweighted penalized least squares (Zhang et al.
    2010). Like ALS but weights are re-derived every iteration from how far
    points fall below the current baseline estimate, so it tracks drifting
    baselines with a single parameter."""
    n = len(y)
    y = y.astype(np.float64)
    w = np.ones(n)
    e = np.ones(n)
    D2 = sparse_diags([e, -2 * e, e], [0, 1, 2], shape=(n - 2, n))
    A0 = D2.T @ D2
    z = y.copy()
    total = np.abs(y).sum() or 1.0
    for it in range(1, itermax + 1):
        W = sparse_diags(w, 0)
        z = spsolve(W + lam * A0, w * y)
        d = y - z
        neg = d[d < 0]
        dssn = np.abs(neg.sum())
        if dssn < 0.001 * total or len(neg) == 0:
            break
        w[d >= 0] = 0
        w[d < 0] = np.exp(it * np.abs(neg) / dssn)
        w[0] = np.exp(it * np.abs(neg).max() / dssn)
        w[-1] = w[0]
    return z


def dsp_snip_baseline(y, iterations):
    """SNIP (Statistics-sensitive Non-linear Iterative Peak-clipping)."""
    y = np.clip(np.asarray(y, dtype=np.float64), 0, None)
    v = np.log(np.log(np.sqrt(y + 1) + 1) + 1)
    iterations = max(1, min(int(iterations), len(v) // 2 - 1))
    for p in range(1, iterations + 1):
        left = dsp_shift_channel(v, p)
        right = dsp_shift_channel(v, -p)
        v = np.minimum(v, 0.5 * (left + right))
    baseline = (np.exp(np.exp(v) - 1) - 1) ** 2 - 1
    return np.clip(baseline, 0, None)


def dsp_rubberband_baseline(y, smooth_win=1):
    """Rubberband (convex hull) baseline."""
    from scipy.spatial import ConvexHull
    from scipy.ndimage import uniform_filter1d as _uf
    n = len(y)
    s = min(int(smooth_win), n) if smooth_win > 1 else 1
    if s > 1:
        y = _uf(y, size=s, mode='nearest')
    else:
        y = np.asarray(y, dtype=np.float64)
    x = np.arange(n, dtype=np.float64)
    points = np.column_stack([x, -y])
    try:
        hull = ConvexHull(points)
    except Exception:
        hull_pts = np.column_stack([x, -y])
        hull_pts = hull_pts[np.argsort(hull_pts[:, 0])]
        return -np.interp(x, hull_pts[:, 0], hull_pts[:, 1])
    hull_pts = points[hull.vertices]
    hull_pts = hull_pts[np.argsort(hull_pts[:, 0])]
    baseline = np.interp(x, hull_pts[:, 0], hull_pts[:, 1])
    return -baseline


def dsp_asylS_baseline(y, lam, p=0.01, niter=10):
    """Asymmetric Least Squares baseline (Eilers 2001)."""
    n = len(y)
    y = y.astype(np.float64)
    e = np.ones(n)
    D2 = sparse_diags([e, -2 * e, e], [0, 1, 2], shape=(n - 2, n))
    A = lam * (D2.T @ D2)
    w = np.ones(n)
    for _ in range(niter):
        W = sparse_diags(w, 0)
        z = spsolve(W + A, w * y)
        w = p * (y > z) + (1 - p) * (y < z)
    return z


def dsp_arpls_baseline(y, lam=1e5, max_iter=100, tol=1e-5):
    """Adaptive iteratively reweighted PLS baseline (Oller-More et al. 2006)."""
    n = len(y)
    y = y.astype(np.float64)
    e = np.ones(n)
    D2 = sparse_diags([e, -2 * e, e], [0, 1, 2], shape=(n - 2, n))
    A = D2.T @ D2
    w = np.ones(n)
    for _ in range(max_iter):
        W = sparse_diags(w, 0)
        z = spsolve(w * y, W + lam * A) if False else spsolve(W + lam * A, w * y)
        d = y - z
        neg = d[d < 0]
        dssn = np.abs(neg.sum())
        if dssn < 1e-8 or len(neg) == 0:
            break
        sigma = np.std(neg)
        if sigma < 1e-8:
            break
        w_new = 1.0 / (1 + np.exp(2 * (d - dssn) / sigma))
        if np.linalg.norm(w_new - w) / (np.linalg.norm(w) + 1e-10) < tol:
            w = w_new
            break
        w = w_new
    return z


def dsp_compute_baseline(raw, method, window, window2=None):
    """raw: (n,4).  Returns baseline (n,4) array."""
    n = len(raw)
    bl = np.zeros_like(raw)
    bw = window
    if method == 'None':
        return bl
    if method == 'Rolling Minimum':
        for ch in range(4):
            bl[:, ch] = minimum_filter1d(raw[:, ch], size=int(bw), mode='reflect')
    elif method == 'Rolling Median':
        for ch in range(4):
            bl[:, ch] = median_filter(raw[:, ch], size=int(bw), mode='reflect')
    elif method == 'ALS':
        lam = bw
        p = (window2 / 100.0) if window2 is not None else 0.005
        e = np.ones(n)
        D2 = sparse_diags([e, -2 * e, e], [0, 1, 2], shape=(n - 2, n))
        A = lam * D2.T @ D2
        for ch in range(4):
            y = raw[:, ch].astype(np.float64)
            w = np.ones(n)
            z = y
            for _ in range(10):
                W = sparse_diags(w, 0)
                z = spsolve(W + A, w * y)
                w = p * (y > z) + (1 - p) * (y <= z)
            bl[:, ch] = z
    elif method == 'airPLS':
        itermax = int(window2) if window2 is not None else 15
        for ch in range(4):
            bl[:, ch] = dsp_airpls_baseline(raw[:, ch], bw, itermax=itermax)
    elif method == 'SNIP':
        for ch in range(4):
            bl[:, ch] = dsp_snip_baseline(raw[:, ch], bw)
    elif method == 'Morphological (Top-hat)':
        size = max(3, int(bw))
        for ch in range(4):
            bl[:, ch] = grey_opening(raw[:, ch], size=size)
    elif method == 'Polynomial Detrend':
        order = max(1, min(int(bw), n - 1))
        x_idx = np.arange(n, dtype=np.float64)
        for ch in range(4):
            coeffs = np.polyfit(x_idx, raw[:, ch], order)
            bl[:, ch] = np.polyval(coeffs, x_idx)
    elif method == 'Rubberband':
        for ch in range(4):
            bl[:, ch] = dsp_rubberband_baseline(raw[:, ch], smooth_win=max(1, int(bw)))
    elif method == 'AsyLS':
        lam = bw
        p = (window2 / 100.0) if window2 is not None else 0.01
        for ch in range(4):
            bl[:, ch] = dsp_asylS_baseline(raw[:, ch], lam, p=p, niter=10)
    elif method == 'arPLS':
        max_iter = int(window2) if window2 is not None else 100
        for ch in range(4):
            bl[:, ch] = dsp_arpls_baseline(raw[:, ch], lam=bw, max_iter=max_iter)
    elif method == 'Flat Offset (200-1200)':
        start = max(0, int(bw))
        end = min(n, int(window2) if window2 is not None else start + 1000)
        if end <= start:
            end = start + 1000
        region = raw[max(0, start):min(n, end)]
        for ch in range(4):
            ch_region = region[:, ch]
            if len(ch_region) > 0:
                bl[:, ch] = float(np.median(ch_region))
    elif method == 'Noise Offset (pre-1500)':
        end = min(n, 1500)
        if end <= 1:
            end = n
        region = raw[:end]
        for ch in range(4):
            ch_region = region[:, ch]
            if len(ch_region) > 0:
                bl[:, ch] = float(np.median(ch_region))
    else:
        raise ValueError(f'Unknown baseline method: {method}')
    return bl


# ── Smoothing methods ──────────────────────────────────────────────────

def dsp_wavelet_denoise(y, pywt, level, threshold_scale=1.0, wavelet='db4'):
    y = np.asarray(y, dtype=np.float64)
    n = len(y)
    max_level = pywt.dwt_max_level(n, pywt.Wavelet(wavelet).dec_len)
    level = min(level, max_level) if max_level > 0 else 0
    if level < 1:
        return y.copy()
    coeffs = pywt.wavedec(y, wavelet, level=level)
    detail1 = coeffs[-1]
    sigma = np.median(np.abs(detail1)) / 0.6745 if len(detail1) else 0.0
    uthresh = sigma * np.sqrt(2 * np.log(max(n, 2))) * threshold_scale
    new_coeffs = [coeffs[0]] + [pywt.threshold(c, uthresh, mode='soft')
                                for c in coeffs[1:]]
    denoised = pywt.waverec(new_coeffs, wavelet)
    return denoised[:n]


def dsp_fft_lowpass(y, cutoff_period, taper_frac=0.1):
    """Zero (with cosine taper) all FFT bins whose period is shorter than
    ``cutoff_period`` scans, then inverse-transform."""
    y = np.asarray(y, dtype=np.float64)
    n = len(y)
    spec = np.fft.rfft(y)
    freqs = np.fft.rfftfreq(n, d=1.0)
    cutoff_freq = 1.0 / max(cutoff_period, 2.0)
    taper_width = max(cutoff_freq * taper_frac, 1e-6)
    gain = np.ones_like(freqs)
    hi = cutoff_freq + taper_width
    lo = cutoff_freq - taper_width
    ramp = (freqs > lo) & (freqs < hi)
    gain[freqs >= hi] = 0.0
    if np.any(ramp):
        gain[ramp] = 0.5 * (1 + np.cos(np.pi * (freqs[ramp] - lo) / (hi - lo)))
    filtered = np.fft.irfft(spec * gain, n=n)
    return filtered


def dsp_dominant_periodicities(y, top_n=5):
    """Return top_n strongest non-DC frequency components as
    (period_in_scans, relative_power) tuples."""
    y = np.asarray(y, dtype=np.float64)
    n = len(y)
    y = y - y.mean()
    spec = np.fft.rfft(y)
    freqs = np.fft.rfftfreq(n, d=1.0)
    power = np.abs(spec) ** 2
    power[0] = 0.0
    order = np.argsort(power)[::-1][:top_n]
    out = []
    for idx in order:
        f = freqs[idx]
        period = (1.0 / f) if f > 0 else np.inf
        out.append((float(period), float(power[idx])))
    return out


def dsp_smooth_signal(corr, method, window, order):
    """corr: (n,4) baseline-subtracted signal."""
    sm = corr.copy()
    sw, so = window, order
    if method == 'Savitzky-Golay':
        if sw > so + 1 and sw % 2 == 1:
            for ch in range(4):
                sm[:, ch] = savgol_filter(sm[:, ch], sw, so)
    elif method == 'Gaussian':
        for ch in range(4):
            sm[:, ch] = gaussian_filter1d(sm[:, ch], sigma=so, truncate=sw / so / 2)
    elif method == 'Moving Avg':
        if sw >= 3:
            kernel = np.ones(sw) / sw
            for ch in range(4):
                sm[:, ch] = np.convolve(sm[:, ch], kernel, mode='same')
    elif method == 'Median':
        sw2 = max(3, sw if sw % 2 == 1 else sw + 1)
        for ch in range(4):
            sm[:, ch] = median_filter(sm[:, ch], size=sw2, mode='reflect')
    elif method == 'Whittaker':
        lam = sw
        n = len(sm)
        e = np.ones(n)
        D2 = sparse_diags([e, -2 * e, e], [0, 1, 2], shape=(n - 2, n))
        A = sparse_diags(np.ones(n), 0) + lam * D2.T @ D2
        for ch in range(4):
            sm[:, ch] = spsolve(A.tocsr(), sm[:, ch])
    elif method == 'Butterworth':
        from scipy.signal import butter, filtfilt
        order_ = max(1, min(so, 10))
        wn = float(np.clip(2.0 / max(sw, 2), 1e-4, 0.99))
        b, a = butter(order_, wn, btype='low')
        padlen = 3 * (max(len(a), len(b)) - 1)
        if len(sm) > padlen:
            for ch in range(4):
                sm[:, ch] = filtfilt(b, a, sm[:, ch])
    elif method == 'Wavelet':
        try:
            import pywt
        except ImportError:
            pass
        else:
            level = max(1, min(sw, 8))
            thresh_scale = max(so, 1) / 100.0
            for ch in range(4):
                sm[:, ch] = dsp_wavelet_denoise(sm[:, ch], pywt, level, thresh_scale)
    elif method == 'LOWESS':
        try:
            from statsmodels.nonparametric.smoothers_lowess import lowess as sm_lowess
        except ImportError:
            pass
        else:
            frac = float(np.clip(sw / 1000.0, 0.001, 0.5))
            iters = max(0, min(so, 5))
            x_idx = np.arange(len(sm), dtype=np.float64)
            delta = 0.01 * (x_idx[-1] - x_idx[0]) if len(x_idx) > 1 else 0.0
            for ch in range(4):
                sm[:, ch] = sm_lowess(sm[:, ch], x_idx, frac=frac, it=iters,
                                      delta=delta, return_sorted=False)
    elif method == 'FFT Lowpass':
        taper_frac = so / 100.0
        for ch in range(4):
            sm[:, ch] = dsp_fft_lowpass(sm[:, ch], sw, taper_frac=max(taper_frac, 0.01))
    else:
        raise ValueError(f'Unknown smoothing method: {method}')
    return sm


# ── Channel separation ─────────────────────────────────────────────────

def dsp_separate_channels(sm, bl, matrix):
    """Spectral (dye-bleed) separation via matrix inversion."""
    try:
        inv = np.linalg.inv(matrix)
    except np.linalg.LinAlgError:
        inv = np.linalg.pinv(matrix)
    bm = np.median(bl, axis=0)
    bm[bm <= 1e-9] = 1.0
    gn = sm / (bm[np.newaxis, :] + 1e-10)
    separated = gn @ inv.T
    return np.clip(separated, 0, None)


# ── Full pipeline ──────────────────────────────────────────────────────

def dsp_full_pipeline(raw, mobility_shifts, baseline_method, baseline_window,
                      smooth_method, smooth_window, smooth_order, matrix,
                      baseline_window2=None, matrix_apply_point='smoothed'):
    """Full processing pipeline.  Returns (raw, bl, corr, sm, separated, mix).

    ``matrix_apply_point`` picks which stage the crosstalk separation matrix
    is applied to: 'none', 'offset', 'raw', 'corrected', 'smoothed',
    'shifted'.
    """
    raw = raw.copy()
    if matrix_apply_point == 'offset':
        off = dsp_compute_baseline(raw, 'Noise Offset (pre-1500)',
                                   baseline_window, baseline_window2)
        off_corr = np.clip(raw - off, 0, None)
        sep_raw = dsp_separate_channels(off_corr, off, matrix)
        sep_bl = dsp_compute_baseline(sep_raw, baseline_method, baseline_window,
                                      baseline_window2)
        sep_corr = np.clip(sep_raw - sep_bl, 0, None)
        separated = dsp_smooth_signal(sep_corr, smooth_method, smooth_window,
                                      smooth_order)
        return raw, off, off_corr, sep_corr, separated, matrix
    bl = dsp_compute_baseline(raw, baseline_method, baseline_window, baseline_window2)
    corr = np.clip(raw - bl, 0, None)
    sm = dsp_smooth_signal(corr, smooth_method, smooth_window, smooth_order)
    if matrix_apply_point == 'raw':
        sep_raw = dsp_separate_channels(raw, bl, matrix)
        sep_bl = dsp_compute_baseline(sep_raw, baseline_method, baseline_window,
                                      baseline_window2)
        sep_corr = np.clip(sep_raw - sep_bl, 0, None)
        separated = dsp_smooth_signal(sep_corr, smooth_method, smooth_window,
                                      smooth_order)
    elif matrix_apply_point == 'corrected':
        sep_corr = dsp_separate_channels(corr, bl, matrix)
        separated = dsp_smooth_signal(sep_corr, smooth_method, smooth_window,
                                      smooth_order)
    elif matrix_apply_point == 'none':
        separated = sm.copy()
    elif matrix_apply_point == 'shifted':
        shifted = np.empty_like(sm)
        for ch in range(4):
            shifted[:, ch] = dsp_shift_channel(sm[:, ch], int(mobility_shifts[ch]))
        separated = dsp_separate_channels(shifted, bl, matrix)
    else:
        separated = dsp_separate_channels(sm, bl, matrix)
    return raw, bl, corr, sm, separated, matrix
