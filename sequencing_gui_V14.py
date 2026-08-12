#!/usr/bin/env python3
"""Sequencing basecaller GUI V10 — single self-contained file.

Merges dsp_core.py, peak_calling.py, and sequencing_gui_V9.py (Claude/030826)
into one runnable file. No sibling modules required beyond the standard
extract_training_data.py parser already on the well-known path.

New in V10 vs V9:
  * FFT Lowpass smoothing method (frequency-domain notch/null with cosine taper)
  * dominant_periodicities() diagnostic to spot periodic noise before smoothing
  * Independent peak-call button (finds its own peaks via scipy.find_peaks,
    no reliance on ESD's peak_positions) compared against M13/ESD via
    Needleman-Wunsch alignment
  * Auto mobility shift estimation via cross-correlation of channel envelopes
    (only valid on calibration-standard runs — caveated in the docstring)
  * optimize_params.py integration (shells out to differential-evolution search)
  * All math lives in pure functions (dsp_* / pc_* prefixes) so it is
    identical whether driven by the GUI or by the headless optimizer.
"""
import sys, os, struct, json, subprocess, tempfile
import numpy as np
from scipy.ndimage import (
    minimum_filter1d, gaussian_filter1d, median_filter,
    maximum_filter1d, grey_opening, uniform_filter1d,
)
from scipy.sparse import diags as sparse_diags
from scipy.sparse.linalg import spsolve
from scipy.signal import savgol_filter, find_peaks

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QComboBox, QSpinBox, QDoubleSpinBox, QCheckBox, QPushButton,
    QGroupBox, QGridLayout, QSlider, QTextEdit, QSplitter, QTabWidget,
    QFileDialog, QProgressBar
)
from PyQt5.QtCore import Qt, QTimer, QSettings, QThread, pyqtSignal

import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT
from matplotlib.figure import Figure
from matplotlib.collections import LineCollection

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from extract_training_data import parse_rsd, parse_esd

BASE_DIR = "/media/tv/78B0C7DE1FA7081C/electropherogram/MB1000_M13_DT"
CHAN_COLORS = ['red', 'green', 'blue', 'orange']
BASE_LETTERS = {0: 'T', 1: 'G', 2: 'C', 3: 'A'}
CHEM_MAP = {0: 'T', 1: 'G', 2: 'C', 3: 'A'}

IUPAC_CODES = {
    frozenset({'A'}): 'A', frozenset({'C'}): 'C',
    frozenset({'G'}): 'G', frozenset({'T'}): 'T',
    frozenset({'A', 'C'}): 'M',
    frozenset({'A', 'G'}): 'R',
    frozenset({'A', 'T'}): 'W',
    frozenset({'C', 'G'}): 'S',
    frozenset({'C', 'T'}): 'Y',
    frozenset({'G', 'T'}): 'K',
    frozenset({'A', 'C', 'G'}): 'V',
    frozenset({'A', 'C', 'T'}): 'H',
    frozenset({'A', 'G', 'T'}): 'D',
    frozenset({'C', 'G', 'T'}): 'B',
    frozenset({'A', 'C', 'G', 'T'}): 'N',
}

DEFAULT_SPEC_MATRIX = np.array([
    [0.85, 0.03, 0.05, 0.07],
    [0.02, 0.88, 0.04, 0.06],
    [0.06, 0.04, 0.86, 0.04],
    [0.07, 0.05, 0.05, 0.83],
], dtype=np.float64)

OFF_PATTERN = np.array([
    [0.00, 0.20, 0.33, 0.47],
    [0.17, 0.00, 0.33, 0.50],
    [0.43, 0.29, 0.00, 0.29],
    [0.41, 0.29, 0.29, 0.00],
], dtype=np.float64)

BASELINE_METHODS = [
    'Rolling Minimum', 'Rolling Median', 'ALS', 'airPLS', 'SNIP',
    'Morphological (Top-hat)', 'Polynomial Detrend',
    'Rubberband', 'AsyLS', 'arPLS',
]

SMOOTH_METHODS = [
    'Savitzky-Golay', 'Gaussian', 'Moving Avg', 'Median', 'Whittaker',
    'Butterworth', 'Wavelet', 'LOWESS', 'FFT Lowpass',
]

SMOOTH_PARAM_CONFIG = {
    'Savitzky-Golay': ('Window:', (3, 51), 'Order:', (1, 20)),
    'Gaussian':       ('Window:', (3, 51), 'Sigma:', (1, 20)),
    'Moving Avg':     ('Window:', (3, 51), 'Order:', (1, 20)),
    'Median':         ('Window:', (3, 51), 'Order:', (1, 20)),
    'Whittaker':      ('Lambda:', (100, 100000), 'Order:', (1, 20)),
    'Butterworth':    ('Cutoff period:', (3, 500), 'Order:', (1, 10)),
    'Wavelet':        ('Level:', (1, 8), 'Thresh x100:', (10, 300)),
    'LOWESS':         ('Frac x1000:', (1, 500), 'Iterations:', (0, 5)),
    'FFT Lowpass':    ('Cutoff period:', (3, 500), 'Taper %:', (0, 50)),
}

BASELINE_PARAM_CONFIG = {
    'Rolling Minimum':          ('Window:', (20, 1000), None, None),
    'Rolling Median':           ('Window:', (20, 1000), None, None),
    'ALS':                      ('Lambda:', (20, 100000), 'Asymmetry x100:', (1, 100)),
    'airPLS':                   ('Lambda:', (20, 100000), 'Max iters:', (5, 50)),
    'SNIP':                     ('Iterations:', (5, 500), None, None),
    'Morphological (Top-hat)':  ('Window:', (3, 1000), None, None),
    'Polynomial Detrend':       ('Order:', (1, 15), None, None),
    'Rubberband':               ('Smooth win:', (3, 101), None, None),
    'AsyLS':                    ('Lambda:', (20, 100000), 'Asymmetry x100:', (1, 100)),
    'arPLS':                    ('Lambda:', (20, 100000), 'Max iters:', (5, 200)),
}


def find_esd_subdirs(base_dir):
    dirs = {}
    for d in sorted(os.listdir(base_dir)):
        dp = os.path.join(base_dir, d)
        if os.path.isdir(dp) and d.endswith('_MD1'):
            name = d.replace('MB1000_M13_DT_', '').replace('_MD1', '')
            dirs[name] = d
    return dirs


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


# ---------------------------------------------------------------------------
# dsp_core: Signal Processing Core (inlined from dsp_core.py)
# ---------------------------------------------------------------------------
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


# --- Baseline ---
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
    """SNIP (Statistics-sensitive Non-linear Iterative Peak-clipping).
    Works on an LLS-transformed copy (compresses peak heights so tall peaks
    don't dominate clipping), iteratively clips each point down to the
    average of its two neighbors at growing distance."""
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
    """Rubberband (convex hull) baseline.  Computes the lower convex hull
    of the inverted signal and linearly interpolates between hull vertices
    to form a baseline floor.  smooth_win (>1) pre-smooths the signal via
    a moving average before hull construction to suppress noise that would
    otherwise create spurious hull vertices."""
    from scipy.spatial import ConvexHull
    from scipy.ndimage import uniform_filter1d
    n = len(y)
    s = min(int(smooth_win), n) if smooth_win > 1 else 1
    if s > 1:
        y = uniform_filter1d(y, size=s, mode='nearest')
    else:
        y = np.asarray(y, dtype=np.float64)
    x = np.arange(n, dtype=np.float64)
    points = np.column_stack([x, -y])
    hull = ConvexHull(points)
    hull_pts = points[hull.vertices]
    hull_pts = hull_pts[np.argsort(hull_pts[:, 0])]
    baseline = np.interp(x, hull_pts[:, 0], hull_pts[:, 1])
    return -baseline


def dsp_asylS_baseline(y, lam, p=0.01, niter=10):
    """Asymmetric Least Squares baseline (Eilers 2001).  Same penalty as ALS
    but uses a constant asymmetry parameter p instead of iterating weights."""
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
    """Adaptive iteratively reweighted PLS baseline (Oller-More et al.
    2006).  Uses a smooth weight function based on the std of positive
    residuals, giving robust automatic weight updates without the manual p
    parameter of ALS."""
    n = len(y)
    y = y.astype(np.float64)
    e = np.ones(n)
    D2 = sparse_diags([e, -2 * e, e], [0, 1, 2], shape=(n - 2, n))
    A = D2.T @ D2
    w = np.ones(n)
    for _ in range(max_iter):
        W = sparse_diags(w, 0)
        z = spsolve(W + lam * A, w * y)
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
    """raw: (n,4). window2 is the method-specific secondary parameter shown
    by the 'Secondary:' slider (BASELINE_PARAM_CONFIG), or None for methods
    that don't use one:
      ALS / AsyLS  -> window2 is 'Asymmetry x100' (1-100); p = window2/100
      airPLS/arPLS -> window2 is 'Max iters' directly
    Returns baseline (n,4) array."""
    n = len(raw)
    bl = np.zeros_like(raw)
    bw = window
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
    else:
        raise ValueError(f'Unknown baseline method: {method}')
    return bl


# --- Smoothing ---
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
    """Zero (with a cosine taper, to avoid ringing) all FFT bins whose
    period is shorter than ``cutoff_period`` scans, then inverse-transform.

    Unlike Butterworth/savgol, this directly nulls periodic noise
    (electrical pickup, pump/stepper ripple, CCD readout striping) at a
    specific frequency while keeping gain=1 below the cutoff, so sharp
    electrophoretic peaks at the bases aren't rounded off."""
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
    """Return the top_n strongest non-DC frequency components as
    (period_in_scans, relative_power) tuples, sorted by power descending.
    Use this to spot periodic noise sources before choosing a smoothing
    method or an FFT-lowpass cutoff."""
    y = np.asarray(y, dtype=np.float64)
    n = len(y)
    y = y - y.mean()
    spec = np.fft.rfft(y)
    freqs = np.fft.rfftfreq(n, d=1.0)
    power = np.abs(spec) ** 2
    power[0] = 0.0  # drop DC
    order = np.argsort(power)[::-1][:top_n]
    out = []
    for idx in order:
        f = freqs[idx]
        period = (1.0 / f) if f > 0 else np.inf
        out.append((float(period), float(power[idx])))
    return out


def dsp_smooth_signal(corr, method, window, order):
    """corr: (n,4) baseline-subtracted signal.
    window/order: the two tunable params for ``method`` (see SMOOTH_PARAM_CONFIG)."""
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
        taper_frac = so / 100.0  # "Taper %" slider, 0-50
        for ch in range(4):
            sm[:, ch] = dsp_fft_lowpass(sm[:, ch], sw, taper_frac=max(taper_frac, 0.01))
    else:
        raise ValueError(f'Unknown smoothing method: {method}')
    return sm


def dsp_separate_channels(sm, bl, matrix):
    """Spectral (dye-bleed) separation via matrix inversion."""
    try:
        inv = np.linalg.inv(matrix)
    except np.linalg.LinAlgError:
        inv = np.linalg.pinv(matrix)
    bm = np.median(bl, axis=0)
    gn = sm / (bm[np.newaxis, :] + 1e-10)
    separated = gn @ inv.T
    return np.clip(separated, 0, None)


def dsp_full_pipeline(raw, mobility_shifts, baseline_method, baseline_window,
                       smooth_method, smooth_window, smooth_order, matrix,
                       baseline_window2=None):
    """Full processing pipeline. Returns (raw, bl, corr, sm, separated, mix)."""
    raw = dsp_apply_mobility_shifts(raw, mobility_shifts)
    bl = dsp_compute_baseline(raw, baseline_method, baseline_window, baseline_window2)
    corr = np.clip(raw - bl, 0, None)
    sm = dsp_smooth_signal(corr, smooth_method, smooth_window, smooth_order)
    separated = dsp_separate_channels(sm, bl, matrix)
    return raw, bl, corr, sm, separated, matrix


# ---------------------------------------------------------------------------
# peak_calling: Independent peak detection + mobility estimation (inlined)
# ---------------------------------------------------------------------------
def pc_normalize_peaks(separated, mode='total_signal', window=800):
    """Normalize the 4-channel separated trace so peak heights are
    comparable across channels and across the run.

    mode:
      'channel_max'  - divide each channel by its own global max.
      'total_signal' - divide each scan by the sum across all 4 channels
                       at that scan. Removes overall intensity drift while
                       preserving the relative dye ratio at each scan.
      'rolling_local' - divide by a rolling max so normalization tracks
                        the slow loss of signal amplitude late in a long run.
    """
    x = np.clip(np.asarray(separated, dtype=np.float64), 0, None)
    if mode == 'channel_max':
        cmax = x.max(axis=0)
        cmax[cmax == 0] = 1.0
        return x / cmax[np.newaxis, :]
    elif mode == 'total_signal':
        total = x.sum(axis=1)
        scale = np.median(total[total > 0]) if np.any(total > 0) else 1.0
        total_safe = np.where(total > 0, total, scale)
        return x / total_safe[:, np.newaxis] * scale
    elif mode == 'rolling_local':
        total = x.sum(axis=1)
        local_max = maximum_filter1d(total, size=max(int(window), 3), mode='nearest')
        local_max = np.clip(local_max, np.percentile(total, 50) * 0.05 + 1e-9, None)
        target = np.median(local_max)
        return x / local_max[:, np.newaxis] * target
    else:
        raise ValueError(f'Unknown normalization mode: {mode}')


def pc_detect_peaks_4ch(separated, min_distance=6, prominence_frac=0.02, width=None):
    """Run find_peaks independently on each of the 4 (normalized)
    separated channels, then merge into one ordered list of
    (position, channel, height) picking the tallest candidate within
    ``min_distance`` scans whenever two channels both claim a peak there."""
    x = np.clip(np.asarray(separated, dtype=np.float64), 0, None)
    candidates = []
    for ch in range(4):
        scale = np.percentile(x[:, ch], 99.5)
        if scale <= 0:
            continue
        prom = max(scale * prominence_frac, 1e-9)
        kwargs = dict(distance=max(1, int(min_distance)), prominence=prom)
        if width is not None:
            kwargs['width'] = width
        peaks, _ = find_peaks(x[:, ch], **kwargs)
        for p in peaks:
            candidates.append((int(p), ch, float(x[p, ch])))
    candidates.sort(key=lambda c: c[0])

    merged = []
    i = 0
    while i < len(candidates):
        j = i
        cluster = [candidates[i]]
        while j + 1 < len(candidates) and \
              candidates[j + 1][0] - cluster[-1][0] <= min_distance:
            j += 1
            cluster.append(candidates[j])
        best = max(cluster, key=lambda c: c[2])
        merged.append(best)
        i = j + 1
    return merged


def pc_call_bases(separated, min_distance=6, prominence_frac=0.02,
                  normalize_mode='total_signal'):
    """End-to-end independent basecall: normalize -> detect peaks per
    channel -> merge -> assign letters. Returns (positions, sequence, heights)."""
    norm = pc_normalize_peaks(separated, mode=normalize_mode)
    merged = pc_detect_peaks_4ch(norm, min_distance=min_distance,
                                 prominence_frac=prominence_frac)
    positions = np.array([m[0] for m in merged], dtype=np.int64)
    sequence = ''.join(BASE_LETTERS[m[1]] for m in merged)
    heights = np.array([m[2] for m in merged], dtype=np.float64)
    return positions, sequence, heights


def pc_signal_onset(separated, onset_frac=0.05, smooth=40, rise_sigma=4.0,
                    lead_frac=0.05, rise_window=None):
    """Find the scan index where the sample DNA signal first starts to
    *rise* above the instrument baseline, rather than where it merely
    crosses a fixed threshold.

    CE reads begin with a long flat baseline (electrokinetic injection +
    buffer drift) before the first dye-labeled fragment arrives; naive peak
    detection happily calls spurious ambiguous bases in that flat region
    because rolling-local normalization amplifies the noise there.  A
    fixed amplitude threshold is fragile: a run with unusually low noise
    crosses it during a gentle pre-peak slope too early, while a run with
    weak early signal but a high later max crosses it only after the first
    real peaks are long gone.

    Instead we look at the RATE of increase of the smoothed summed
    intensity: the baseline is flat (rise ~ noise), the sample is where the
    rise clearly exceeds the noise of the leading baseline.  We return the
    first scan where intensity rises by ``rise_sigma`` noise-sigmas over a
    window of ``rise_window`` scans while also sitting above the leading
    baseline floor.

    Returns 0 if the trace is empty/constant (caller should then keep all
    peaks)."""
    x = np.clip(np.asarray(separated, dtype=np.float64), 0, None)
    tot = x.sum(axis=1)
    n = len(tot)
    if n == 0 or tot.max() <= 0:
        return 0
    smooth = max(1, int(smooth))
    if n >= smooth:
        tot = np.convolve(tot, np.ones(smooth) / smooth, mode='same')
    W = int(rise_window) if rise_window else max(10, n // 200)
    W = max(2, min(W, n - 1))
    lead_n = max(int(n * max(float(lead_frac), 0.01)), 1)
    lead = tot[:lead_n]
    floor = float(np.median(lead))
    mad = float(np.median(np.abs(lead - floor)))
    spread = max(float(lead.std()), 1.5 * mad, 1e-9)
    rise = tot[W:] - tot[:-W]
    # noise of the rise in the flat leading region
    rise_lead = rise[:max(1, lead_n - W)]
    rise_noise = max(float(rise_lead.std()) if len(rise_lead) > 1 else 0.0, 1e-9)
    rise_thresh = float(rise_sigma) * rise_noise
    above_floor = tot >= floor + float(rise_sigma) * spread
    candidates = np.where((rise > rise_thresh) & above_floor[W:])[0]
    if len(candidates) == 0:
        # fall back to the amplitude test rather than returning 0
        idx = np.where(tot >= max(floor + rise_thresh,
                                  tot.max() * max(float(onset_frac), 1e-6)))[0]
        if len(idx) == 0:
            return 0
        return max(0, int(idx[0]) - smooth // 2)
    # Skip short (<=2 scan) isolated bumps: the real ramp produces a
    # sustained run of candidates. Find the first run of >= 3 consecutive.
    c = candidates[0]
    i = 0
    while i < len(candidates):
        j = i
        while j + 1 < len(candidates) and candidates[j + 1] == candidates[j] + 1:
            j += 1
        if j - i + 1 >= 3:
            c = candidates[i]
            break
        i = j + 1
    onset = W + int(c) + smooth // 4
    # step back a few scans so we don't clip the first genuine peak apex
    return max(0, int(onset) - W // 2)


def pc_call_bases_with_shifts(separated, shifts, min_distance=6,
                              prominence_frac=0.02, tolerance=4,
                              normalize=True, norm_window=800,
                              min_signal_frac=0.25, onset_frac=0.05,
                              signal_onset_smooth=40, min_height_ratio=2.0):
    """Detect peaks on per-channel-shifted separated traces and merge with
    IUPAC ambiguity codes.

    Unlike ``pc_call_bases``, this applies per-channel mobility shifts
    *after* baseline/smoothing/matrix, then runs ``find_peaks`` independently
    on each shifted channel. Peaks from different channels within
    ``tolerance`` scans of each other are at the same base position and
    combined using IUPAC single-letter codes (e.g. A+C -> M, A+G+T -> D).

    If ``normalize`` is True, each channel is divided by a rolling local
    maximum (window = ``norm_window`` scans) to compensate for the signal
    decay inherent in Sanger sequencing by CE — shorter fragments produce
    stronger signals, so later (longer) peaks are systematically weaker.
    Per-channel rolling normalization makes late peaks detectable at the
    same relative threshold as early ones.

    ``min_signal_frac`` sets the minimum fraction of the tallest peak's
    signal required for a channel to contribute to an ambiguous base call.
    For example, with min_signal_frac=0.25, a minor bump at 15% of the
    dominant peak's height is rejected — only genuinely overlapping signals
    (each >25% of the max) are combined into IUPAC codes. This prevents
    noise/artifact peaks under a large peak from being mis-called as
    ambiguous bases (e.g. falsely calling W instead of just A).

    Returns (positions, sequence, base_groups, intensities) where:
      positions  — scan index of each called position (midpoint of merged peaks)
      sequence   — IUPAC-coded base string
      base_groups — list of sets of base letters at each position
      intensities — dict {base_letter: height} at each position
    """
    from scipy.signal import find_peaks as _fp

    n = len(separated)
    shifted_all = [dsp_shift_channel(separated[:, ch], int(shifts[ch]))
                   for ch in range(4)]

    # Per-channel absolute height floor derived from the leading baseline
    # noise.  Rolling-local normalization makes flat-baseline noise sit at
    # ~1.0 (the same scale as real peaks), so peaks slammed together by
    # noise in a run with a bumpy baseline can still pass prominence.  Each
    # called peak must therefore rise at min_height_ratio x above its own
    # channel's leading-baseline noise level, which cleanly separates
    # genuine fragments from baseline ripple regardless of normalization.
    # The 90th percentile (rather than the median) captures the noise-ripple
    # upper bound so bumpy-baseline runs are rejected without throwing away
    # weak-but-real peaks from low-signal runs.
    lead_n = max(int(n * 0.05), 1)
    ch_floor = [float(np.percentile(np.clip(shifted_all[ch][:lead_n], 0, None), 90))
                for ch in range(4)]

    channels = []
    for ch in range(4):
        shifted = shifted_all[ch]
        if normalize:
            rolled = maximum_filter1d(np.clip(shifted, 0, None),
                                      size=max(3, int(norm_window)),
                                      mode='nearest')
            rolled = np.where(rolled > 0, rolled, 1.0)
            norm_ch = shifted / rolled
        else:
            norm_ch = shifted / (shifted.max() + 1e-12) if shifted.max() > 0 else shifted
        # Prominence threshold must be in norm_ch's own units (~0-1 after
        # either normalization branch above), not the raw signal's units -
        # using the raw scale here made the threshold roughly 100-300x too
        # large for the normalized signal, silently rejecting real peaks.
        scale = np.percentile(np.clip(norm_ch, 0, None), 99.5)
        prom = max(scale * prominence_frac, 1e-9) if scale > 0 else 1e-9
        peaks, _ = _fp(norm_ch, distance=max(1, min_distance), prominence=prom)
        floor_ch = ch_floor[ch] * max(float(min_height_ratio), 0.0)
        for p in peaks:
            if shifted[p] >= floor_ch:
                channels.append((int(p), ch, float(shifted[p])))

    channels.sort(key=lambda c: c[0])

    # Reject spurious peaks called in the flat baseline before the sample
    # actually reaches the detector window (see pc_signal_onset).  Setting
    # onset_frac=0 disables the cut entirely.
    start = 0
    if onset_frac and onset_frac > 0:
        start = pc_signal_onset(separated, onset_frac=onset_frac,
                                smooth=signal_onset_smooth)
        channels = [c for c in channels if c[0] >= start]

    positions = []
    base_groups = []
    intensities = []
    i = 0
    while i < len(channels):
        j = i
        cluster = [channels[i]]
        while j + 1 < len(channels) and channels[j + 1][0] - cluster[-1][0] <= tolerance:
            j += 1
            cluster.append(channels[j])
        max_signal = max(c[2] for c in cluster)
        min_signal = max_signal * min_signal_frac
        valid = [c for c in cluster if c[2] >= min_signal]
        if len(valid) == 1:
            bases = frozenset([BASE_LETTERS[valid[0][1]]])
        else:
            bases = frozenset(BASE_LETTERS[c[1]] for c in valid)
        best = max(valid, key=lambda c: c[2])
        pos = best[0]
        seq_letter = IUPAC_CODES.get(bases, 'N')
        intens = {BASE_LETTERS[c]: h for _, c, h in valid}
        positions.append(pos)
        base_groups.append(bases)
        intensities.append(intens)
        i = j + 1

    positions = np.array(positions, dtype=np.int64)
    sequence = ''.join(IUPAC_CODES.get(b, 'N') for b in base_groups)
    return positions, sequence, base_groups, intensities



def pc_nw_identity(query, reference, match=1, mismatch=-1, gap=-2, max_len=6000):
    """Global (Needleman-Wunsch) alignment identity between two base-letter
    strings, in percent. Robust to insertions/deletions via alignment,
    unlike position-indexed comparison."""
    q = query[:max_len]
    r = reference[:max_len]
    m, n = len(q), len(r)
    if m == 0 or n == 0:
        return 0.0
    dp = np.zeros((m + 1, n + 1), dtype=np.int32)
    dp[:, 0] = np.arange(m + 1) * gap
    dp[0, :] = np.arange(n + 1) * gap
    for i in range(1, m + 1):
        qi = q[i - 1]
        row_prev = dp[i - 1]
        row = dp[i]
        for j in range(1, n + 1):
            diag = row_prev[j - 1] + (match if qi == r[j - 1] else mismatch)
            up = row_prev[j] + gap
            left = row[j - 1] + gap
            row[j] = max(diag, up, left)
    i, j = m, n
    matches = 0
    aligned = 0
    while i > 0 or j > 0:
        if i > 0 and j > 0 and dp[i, j] == dp[i - 1, j - 1] + \
                (match if q[i - 1] == r[j - 1] else mismatch):
            aligned += 1
            if q[i - 1] == r[j - 1]:
                matches += 1
            i -= 1
            j -= 1
        elif i > 0 and dp[i, j] == dp[i - 1, j] + gap:
            aligned += 1
            i -= 1
        else:
            aligned += 1
            j -= 1
    return 100.0 * matches / aligned if aligned else 0.0


def pc_estimate_mobility_shifts(raw, ref_channel=3, max_shift=60, smooth=15):
    """Cross-correlate each channel's smoothed envelope against a reference
    channel and return the integer scan shift (in dsp_core's convention).

    IMPORTANT PHYSICAL CAVEAT: this only recovers a meaningful shift when
    the channels actually share peak timing — i.e. on a mobility/matrix
    calibration standard run where the same DNA fragments are labeled with
    each of the 4 dyes so every channel sees a peak at (almost) the same
    physical positions. On an ordinary sequencing read, each channel
    encodes a *different* set of bases at different times; cross-correlating
    them converges on spurious alignment rather than true dye-mobility lag.
    """
    raw = np.asarray(raw, dtype=np.float64)
    n = len(raw)
    drift_win = max(51, min(n // 4, 401)) | 1
    drift = uniform_filter1d(raw, size=drift_win, axis=0, mode='nearest')
    detrended = np.clip(raw - drift, 0, None)
    env = uniform_filter1d(detrended, size=max(3, int(smooth)), axis=0)
    ref = env[:, ref_channel] - env[:, ref_channel].mean()
    shifts = np.zeros(4, dtype=np.int64)
    for ch in range(4):
        if ch == ref_channel:
            continue
        sig = env[:, ch] - env[:, ch].mean()
        best_lag, best_score = 0, -np.inf
        for lag in range(-max_shift, max_shift + 1):
            if lag >= 0:
                a = ref[lag:]
                b = sig[:n - lag]
            else:
                a = ref[:n + lag]
                b = sig[-lag:]
            if len(a) < 10:
                continue
            denom = (np.linalg.norm(a) * np.linalg.norm(b))
            score = float(a @ b) / denom if denom > 0 else -np.inf
            if score > best_score:
                best_score, best_lag = score, lag
        shifts[ch] = best_lag
    return shifts


# ---------------------------------------------------------------------------
# Optimizer worker thread (keeps GUI responsive during subprocess.run)
# ---------------------------------------------------------------------------
class OptimizerWorker(QThread):
    """Runs optimize_params.py in a background thread so the Qt main loop
    stays responsive and the desktop environment doesn't report the window
    as 'not responding'. Streams stdout line-by-line to the GUI so the user
    can see optimization progress in real time."""

    finished = pyqtSignal(str)         # out_path or error message
    stdout_line = pyqtSignal(str)      # progress line from optimize_params.py

    def __init__(self, cmd, out_path, parent=None):
        super().__init__(parent)
        self.cmd = cmd
        self.out_path = out_path
        self._process = None
        self._user_cancelled = False

    def run(self):
        try:
            proc = subprocess.Popen(
                self.cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, bufsize=1)
            self._process = proc
            for line in iter(proc.stdout.readline, ''):
                if self._user_cancelled:
                    proc.terminate()
                    break
                self.stdout_line.emit(line.rstrip())
            proc.wait()
            if self._user_cancelled:
                self.finished.emit('ERROR: Cancelled by user')
            elif proc.returncode != 0:
                raise RuntimeError(
                    f'optimize_params.py exited with code {proc.returncode}.')
            else:
                self.finished.emit(self.out_path)
        except Exception as e:
            self.finished.emit(f'ERROR: {e}')

    def cancel(self):
        self._user_cancelled = True


# ---------------------------------------------------------------------------
# GUI
# ---------------------------------------------------------------------------
class SequencingGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Sequencing Basecaller GUI V10')
        self.setGeometry(50, 50, 1500, 950)
        self.rsd_raw = None
        self.esd_traces = None
        self.esd_data = None
        self.esd_offset = 0
        self.current_well = None
        self._saved_lims = {}
        self._smooth_mode = 'Savitzky-Golay'
        self._manual_sequence = ''
        self._shift_lines = {}
        self._drag_channel = None
        self._drag_start_x = 0
        self._last_separated = None
        self._settings = QSettings('opencode', 'sequencing_gui')
        self._setup_ui()
        self._restore_settings()
        self._populate_wells()

    def _setup_ui(self):
        main = QWidget()
        self.setCentralWidget(main)
        layout = QVBoxLayout(main)
        layout.setContentsMargins(4, 4, 4, 4)

        # -- Top bar --
        top = QHBoxLayout()
        layout.addLayout(top)
        top.addWidget(QLabel('Well:'))
        self.well_combo = QComboBox()
        self.well_combo.setEditable(True)
        self.well_combo.setMinimumWidth(80)
        self.well_combo.setToolTip(
            'Select the RSD (raw sequencing data) well to load. Typed '
            'names are matched against the .rsd files in the data folder.')
        top.addWidget(self.well_combo)
        self.load_btn = QPushButton('Load')
        self.load_btn.setToolTip('Load the selected well\'s RSD trace and '
                                 'its matching ESD basecall data and update '
                                 'the plot.')
        self.load_btn.clicked.connect(self._load_data)
        top.addWidget(self.load_btn)
        top.addWidget(QLabel('  ESD variant:'))
        self.esd_combo = QComboBox()
        self.esd_combo.setToolTip(
            'Choose which ESD (basecaller output) variant to compare '
            'against. "Cp312" is the standard alignment. Other entries are '
            'alternate peak-calling variants; use Cp312 for the best '
            'machine-learning match.')
        top.addWidget(self.esd_combo)

        # -- Figure + canvas + toolbar --
        self.fig = Figure(figsize=(14, 11), dpi=100)
        self.fig.subplots_adjust(hspace=0.08, left=0.05, right=0.98, top=0.97, bottom=0.05)
        self.canvas = FigureCanvasQTAgg(self.fig)
        self.canvas.mpl_connect('button_press_event', self._on_canvas_press)
        self.canvas.mpl_connect('motion_notify_event', self._on_canvas_move)
        self.canvas.mpl_connect('button_release_event', self._on_canvas_release)
        self.toolbar = NavigationToolbar2QT(self.canvas, self)
        top.addWidget(self.toolbar)
        top.addStretch()

        # -- Sliders panel --
        sliders_w = QWidget()
        sliders_w.setMinimumHeight(260)
        sliders_l = QHBoxLayout(sliders_w)
        sliders_l.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(sliders_w)

        # Baseline group
        blg = QGroupBox('Baseline')
        blg.setToolTip(
            'Baseline correction removes the slowly-varying background '
            'drift from each channel before peak detection. Pick a method '
            'below and tune its window and secondary parameter with the '
            'sliders. arPLS and ALS generally give the flattest baseline '
            'with the least distortion.')
        blg_g = QVBoxLayout(blg)
        hl_m = QHBoxLayout()
        hl_m.addWidget(QLabel('Method:'))
        self.baseline_combo = QComboBox()
        self.baseline_combo.addItems(BASELINE_METHODS)
        self.baseline_combo.setToolTip(
            'Baseline method: Rolling Minimum / Rolling Median roll a '
            'window along the trace; ALS / AsyLS / arPLS fit an asymmetric '
            'least-squares baseline; airPLS is an iterative variant; SNIP '
            'erodes the trace; Rubberband fits a convex hull below the '
            'signal; Polynomial Detrend removes a fitted trend. Try arPLS '
            'or ALS for clean, low-drift results.')
        self.baseline_combo.currentTextChanged.connect(self._on_baseline_method_changed)
        hl_m.addWidget(self.baseline_combo)
        blg_g.addLayout(hl_m)
        self.bl_param_label = QLabel('Window:')
        self.bl_param_label.setToolTip(
            'Window (scans) over which the baseline is estimated. Larger '
            'windows follow slow drift only; smaller windows hug faster '
            'changes but risk fitting peaks as baseline.')
        blg_g.addWidget(self.bl_param_label)
        hl = QHBoxLayout()
        self.bl_slider = QSlider(Qt.Horizontal)
        self.bl_slider.setRange(20, 1000)
        self.bl_slider.setValue(200)
        self.bl_slider.setSingleStep(10)
        self.bl_slider.setToolTip('Same as the "Window" spin box, as a slider.')
        self.bl_spin = QSpinBox()
        self.bl_spin.setRange(20, 1000)
        self.bl_spin.setValue(200)
        self.bl_spin.setSingleStep(10)
        self.bl_spin.setMinimumWidth(70)
        self.bl_spin.setToolTip(
            'Baseline window in scans. Larger = only slow background is '
            'removed; smaller = more aggressive, may eat real peaks.')
        self._link_slider_spinbox(self.bl_slider, self.bl_spin)
        hl.addWidget(self.bl_slider)
        hl.addWidget(self.bl_spin)
        blg_g.addLayout(hl)

        # Baseline secondary param (asymmetry p for ALS/AsyLS, max iters for airPLS/arPLS)
        blg_g2 = QHBoxLayout()
        self.bl2_param_label = QLabel('Secondary:')
        self.bl2_slider = QSlider(Qt.Horizontal)
        self.bl2_slider.setRange(1, 100)
        self.bl2_slider.setValue(1)
        self.bl2_slider.setSingleStep(1)
        self.bl2_slider.setTickPosition(QSlider.TicksBelow)
        self.bl2_param_label.setToolTip('Secondary baseline parameter: asymmetry p (ALS/AsyLS) or max iterations (airPLS, arPLS)')
        self.bl2_spin = QSpinBox()
        self.bl2_spin.setRange(1, 100)
        self.bl2_spin.setValue(1)
        self.bl2_spin.setSingleStep(1)
        self.bl2_spin.setMinimumWidth(70)
        self.bl2_spin.setToolTip(
            'Second baseline parameter, shown only when the chosen method '
            'uses one. For ALS / AsyLS it is the asymmetry p (the label '
            'shows p x100) - higher biases the fit below the signal. For '
            'airPLS / arPLS it is the maximum number of fitting '
            'iterations.')
        self._link_slider_spinbox(self.bl2_slider, self.bl2_spin)
        blg_g2.addWidget(self.bl2_param_label)
        blg_g2.addWidget(self.bl2_slider)
        blg_g2.addWidget(self.bl2_spin)
        blg_g.addLayout(blg_g2)
        sliders_l.addWidget(blg)

        # Smoothing group
        smg = QGroupBox('Smooth')
        smg.setToolTip(
            'Smoothing filters noise from the baseline-corrected trace '
            'before peak detection. Choose a method and a window/order. '
            'Savitzky-Golay preserves peak shape well; too large a window '
            'can merge close peaks.')
        smg_g = QVBoxLayout(smg)
        smg_g.setSpacing(2)
        hl_m = QHBoxLayout()
        hl_m.addWidget(QLabel('Method:'))
        self.smooth_combo = QComboBox()
        self.smooth_combo.addItems(SMOOTH_METHODS)
        self.smooth_combo.setToolTip(
            'Smoothing method. Savitzky-Golay fits a polynomial in each '
            'window (best peak preservation); Moving Average simply '
            'averages the window; others are scipy variants. Pick '
            'Savitzky-Golay for Sanger traces.')
        self.smooth_combo.currentTextChanged.connect(self._on_smooth_method_changed)
        hl_m.addWidget(self.smooth_combo)
        smg_g.addLayout(hl_m)

        hl1 = QHBoxLayout()
        self.sm_param1_label = QLabel('Window:')
        self.sm_param1_label.setToolTip(
            'Smoothing window: number of samples averaged/fitted together. '
            'Odd numbers only. Larger = smoother but risks flattening '
            'narrow peaks.')
        hl1.addWidget(self.sm_param1_label)
        self.sm_win_slider = QSlider(Qt.Horizontal)
        self.sm_win_slider.setRange(3, 51)
        self.sm_win_slider.setValue(7)
        self.sm_win_slider.setSingleStep(2)
        self.sm_win_slider.setTickPosition(QSlider.TicksBelow)
        self.sm_win_slider.setToolTip('Same as the "Window" spin box, as a slider.')
        self.sm_win_spin = QSpinBox()
        self.sm_win_spin.setRange(3, 51)
        self.sm_win_spin.setValue(7)
        self.sm_win_spin.setSingleStep(2)
        self.sm_win_spin.setMinimumWidth(60)
        self.sm_win_spin.setToolTip(
            'Width of the smoothing window in scans. Must be odd. Typical '
            'values 5-11 for Sanger traces.')
        self._link_slider_spinbox(self.sm_win_slider, self.sm_win_spin)
        hl1.addWidget(self.sm_win_slider)
        hl1.addWidget(self.sm_win_spin)
        smg_g.addLayout(hl1)

        hl2 = QHBoxLayout()
        self.sm_param2_label = QLabel('Order:')
        self.sm_param2_label.setToolTip(
            'Polynomial order for Savitzky-Golay smoothing. Higher orders '
            'follow faster signal changes but keep more noise. Order 2 is '
            'a good default.')
        hl2.addWidget(self.sm_param2_label)
        self.sm_ord_slider = QSlider(Qt.Horizontal)
        self.sm_ord_slider.setRange(1, 20)
        self.sm_ord_slider.setValue(2)
        self.sm_ord_spin = QSpinBox()
        self.sm_ord_spin.setRange(1, 20)
        self.sm_ord_spin.setValue(2)
        self.sm_ord_spin.setMinimumWidth(60)
        self.sm_ord_slider.setToolTip('Same as the "Order" spin box, as a slider.')
        self.sm_ord_spin.setToolTip(
            'Savitzky-Golay polynomial order. Must be less than the window. '
            'Higher = fits faster changes (noisier); lower = smoother.')
        self._link_slider_spinbox(self.sm_ord_slider, self.sm_ord_spin)
        hl2.addWidget(self.sm_ord_slider)
        hl2.addWidget(self.sm_ord_spin)
        smg_g.addLayout(hl2)
        sliders_l.addWidget(smg)

        # Matrix group: full 4x4 grid
        mxg = QGroupBox('Matrix (row=channel, col=base)')
        mxg.setToolTip(
            'Spectral overlap (crosstalk) matrix. Row = detected channel, '
            'column = fluorophore/base. Entry M[r][c] is how much of base '
            '"c" appears in channel "r". Used for spectral deconvolution '
            '(colour separation) of the raw trace. Diagonal entries should '
            'dominate with small off-diagonal bleed values.')
        mxg_g = QGridLayout(mxg)
        mxg_g.setVerticalSpacing(3)
        mxg_g.setHorizontalSpacing(3)
        base_labels = ['T', 'G', 'C', 'A']
        base_colors = ['red', 'green', 'blue', 'orange']
        mxg_g.addWidget(QLabel(''), 0, 0)
        for c in range(4):
            lbl = QLabel(base_labels[c])
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet(f'color: {base_colors[c]}; font-weight: bold;')
            mxg_g.addWidget(lbl, 0, c + 1)
        self.mx_grid_spins = [[None] * 4 for _ in range(4)]
        for r in range(4):
            row_lbl = QLabel(f'Ch{r}')
            row_lbl.setStyleSheet(f'color: {base_colors[r]}; font-weight: bold;')
            mxg_g.addWidget(row_lbl, r + 1, 0)
            for c in range(4):
                sp = QDoubleSpinBox()
                sp.setRange(0.0, 1.0)
                sp.setSingleStep(0.01)
                sp.setDecimals(3)
                sp.setValue(float(DEFAULT_SPEC_MATRIX[r, c]))
                sp.setMinimumWidth(62)
                sp.setToolTip(
                    f'Crosstalk factor from base {base_labels[c]} into '
                    f'channel Ch{r}. 1.0 = full signal, near 0 = no bleed.')
                if r == c:
                    sp.setStyleSheet('QDoubleSpinBox { font-weight: bold; }')
                sp.valueChanged.connect(self._schedule_update)
                mxg_g.addWidget(sp, r + 1, c + 1)
                self.mx_grid_spins[r][c] = sp
        preset_l = QHBoxLayout()
        for name, m in [('Default', DEFAULT_SPEC_MATRIX),
                        ('Identity', np.eye(4)),
                        ('Uniform', np.full((4, 4), 0.25))]:
            btn = QPushButton(name)
            btn.setToolTip(
                {'Default': 'Load the standard calibration crosstalk matrix.',
                 'Identity': 'No crosstalk - each channel is its own base '
                             '(ignore spectral bleed).',
                 'Uniform': 'Flat 0.25 matrix (worst case, rarely useful).'}[name])
            btn.clicked.connect(lambda checked, mm=m: self._set_matrix(mm))
            preset_l.addWidget(btn)
        mxg_g.addLayout(preset_l, 5, 0, 1, 5)
        sliders_l.addWidget(mxg)

        # Mobility shift group
        msg = QGroupBox('Mobility Shift (scans)')
        msg.setToolTip(
            'Mobility shift: a per-channel constant scan offset applied '
            'after matrix separation. Dye mobilities differ slightly, so '
            'the four base peaks for the same fragment land a few scans '
            'apart. Positive shifts a channel right (to later scans). '
            'Fine-tune by dragging the dashed coloured lines on the '
            'separated plot with "Drag shift lines" active.')
        msg_g = QGridLayout(msg)
        msg_g.setVerticalSpacing(4)
        msg_g.setHorizontalSpacing(4)
        self.mobility_spins = []
        for i, (label, color) in enumerate(zip(['T (Ch0)', 'G (Ch1)', 'C (Ch2)', 'A (Ch3)'],
                                                  CHAN_COLORS)):
            lbl = QLabel(label)
            lbl.setStyleSheet(f'color: {color}; font-weight: bold;')
            msg_g.addWidget(lbl, i, 0)
            sp = QSpinBox()
            sp.setRange(-500, 500)
            sp.setValue(0)
            sp.setSingleStep(1)
            sp.setMinimumWidth(70)
            sp.setStyleSheet(f'QSpinBox {{ color: {color}; font-weight: bold; }}')
            sp.setToolTip(f'{label} mobility shift in scans. Positive moves '
                          f'this channel\'s peaks to later scan positions.')
            sp.valueChanged.connect(self._schedule_update)
            msg_g.addWidget(sp, i, 1)
            self.mobility_spins.append(sp)
        reset_shift_btn = QPushButton('Reset shifts')
        reset_shift_btn.setToolTip('Set all four mobility shifts back to 0.')
        reset_shift_btn.clicked.connect(self._reset_mobility_shifts)
        msg_g.addWidget(reset_shift_btn, 4, 0, 1, 2)
        sliders_l.addWidget(msg)

        # Peak detection group (for independent basecall)
        pdg = QGroupBox('Peak detection')
        pdg.setToolTip(
            'Settings for the independent basecaller (no ESD peak positions '
            'used). Distance is the minimum spacing between detected peaks, '
            'Prom x1000 the minimum prominence threshold, and Ambig % the '
            'IUPAC ambiguity window.')
        pdg_g = QGridLayout(pdg)
        pdg_g.setVerticalSpacing(4)
        self.distance_spin = QSpinBox()
        self.distance_spin.setToolTip(
            'Minimum horizontal distance between detected peaks, in scans. '
            'Peaks closer than this in the same channel are treated as one '
            'call. Too small = double-calls on noisy peaks; too large = '
            'misses real close bases.')
        self.distance_spin.setRange(1, 1000)
        self.distance_spin.setValue(5)
        self.distance_spin.valueChanged.connect(self._schedule_update)
        pdg_g.addWidget(QLabel('Distance:'), 0, 0)
        pdg_g.addWidget(self.distance_spin, 0, 1)
        self.prominence_spin = QSpinBox()
        self.prominence_spin.setToolTip(
            'Minimum prominence for a peak, shown as x1000 of the channel '
            'maximum (so 20 = 2.0% of the channel max). Prominence is how '
            'much a peak stands above its immediate surroundings, not its '
            'absolute height. Raise it to reject small baseline bumps.')
        self.prominence_spin.setRange(1, 10000)
        self.prominence_spin.setValue(20)
        self.prominence_spin.setSingleStep(5)
        self.prominence_spin.valueChanged.connect(self._schedule_update)
        pdg_g.addWidget(QLabel('Prom x1000:'), 1, 0)
        pdg_g.addWidget(self.prominence_spin, 1, 1)
        # Ambiguous-window threshold: minimum secondary-peak height (as a %
        # of the dominant peak in a cluster) required for it to be merged
        # into an IUPAC ambiguity code instead of being ignored as noise.
        self.ambig_spin = QSpinBox()
        self.ambig_spin.setToolTip(
            'Ambiguous window: minimum height of a secondary peak, as a '
            'percentage of the dominant peak in the same cluster, needed '
            'for it to be merged into an IUPAC ambiguity code. For '
            'example, at 25% a minor bump reaching 15% of the main peak is '
            'treated as noise (fully unambiguous base), but a bump at 30% '
            'is a real co-eluting fragment (called e.g. M for A+C). Lower '
            '= more sensitive to weak under-peaks; higher = only merges '
            'strong secondary signals. Default 25%.')
        self.ambig_spin.setRange(1, 100)
        self.ambig_spin.setValue(25)
        self.ambig_spin.setSingleStep(5)
        self.ambig_spin.setSuffix(' %')
        self.ambig_spin.setMinimumWidth(70)
        self.ambig_spin.valueChanged.connect(self._schedule_update)
        pdg_g.addWidget(QLabel('Ambig %:'), 2, 0)
        pdg_g.addWidget(self.ambig_spin, 2, 1)
        sliders_l.addWidget(pdg)

        # -- Plots --
        layout.addWidget(self.canvas)

        # -- Bottom bar --
        bottom = QHBoxLayout()
        layout.addLayout(bottom)
        self.save_btn = QPushButton('Save processed data...')
        self.save_btn.setToolTip(
            'Export the processed traces (baseline, corrected, smoothed, '
            'separated) for the current well to a .npz file.')
        self.save_btn.clicked.connect(self._save_data)
        bottom.addWidget(self.save_btn)
        self.ml_btn = QPushButton('Run ML basecalling')
        self.ml_btn.setToolTip(
            'Run the trained neural-network basecaller on the separated '
            'trace and report its agreement with the ESD sequence.')
        self.ml_btn.clicked.connect(self._run_ml)
        bottom.addWidget(self.ml_btn)
        self.peakcall_btn = QPushButton('Independent peak-call vs ESD')
        self.peakcall_btn.setToolTip(
            'Detects peaks on the separated trace itself (no ESD peak '
            'positions used as input) and aligns the result against the '
            "ESD sequence. This is the fair accuracy number - the plot's "
            "'ESD match %' samples the trace at ESD's own peak positions, "
            "which is circular.")
        self.peakcall_btn.clicked.connect(self._run_independent_peakcall)
        bottom.addWidget(self.peakcall_btn)
        self.mobility_btn = QPushButton('Auto mobility shift (calib. run)')
        self.mobility_btn.setToolTip(
            'Cross-correlates channels to estimate a constant per-channel '
            'lag. Only meaningful on a mobility/matrix calibration '
            'standard, where all 4 dyes label the same fragments - on an '
            "ordinary sequencing read the channels carry different bases "
            "at different times and don't share peak timing to correlate.")
        self.mobility_btn.clicked.connect(self._run_auto_mobility)
        bottom.addWidget(self.mobility_btn)
        self.optimize_btn = QPushButton('Optimize parameters...')
        self.optimize_btn.setToolTip(
            'Runs optimize_params.py (differential evolution) against the '
            'currently loaded well, scoring candidates by independent '
            'peak-call identity vs the ESD sequence, then loads the best '
            'settings found into these controls.')
        self.optimize_btn.clicked.connect(self._run_optimizer)
        bottom.addWidget(self.optimize_btn)
        self.cancel_opt_btn = QPushButton('Cancel optimization')
        self.cancel_opt_btn.setToolTip('Terminate the running optimization process.')
        self.cancel_opt_btn.clicked.connect(self._cancel_optimizer)
        self.cancel_opt_btn.setVisible(False)
        bottom.addWidget(self.cancel_opt_btn)
        self.reset_btn = QPushButton('Reset view')
        self.reset_btn.setToolTip('Reset the plot zoom/pan back to the full view.')
        self.reset_btn.clicked.connect(self._reset_view)
        bottom.addWidget(self.reset_btn)
        self.drag_mode_btn = QPushButton('Drag shift lines')
        self.drag_mode_btn.setCheckable(True)
        self.drag_mode_btn.setToolTip(
            'Enable dragging colored vertical lines on the plot to adjust '
            'per-channel mobility shifts. The shift is computed relative to '
            'the current spin-box value and applied immediately.')
        self.drag_mode_btn.toggled.connect(self._on_drag_mode_toggled)
        self.drag_mode_btn.setVisible(False)
        bottom.addWidget(self.drag_mode_btn)
        self.call_btn = QPushButton('Run basecall')
        self.call_btn.setToolTip('Run independent peak-calling with current shifts and matrix')
        self.call_btn.clicked.connect(self._run_basecall)
        bottom.addWidget(self.call_btn)
        self.progress = QProgressBar()
        self.progress.setMaximumWidth(200)
        self.progress.setVisible(False)
        self.progress.setToolTip('Progress of the currently running '
                                 'optimization or batch task.')
        bottom.addWidget(self.progress)
        self.opt_log = QTextEdit()
        self.opt_log.setMaximumHeight(100)
        self.opt_log.hide()
        self.opt_log.setToolTip('Log output of the parameter optimizer.')
        bottom.addWidget(self.opt_log)
        bottom.addStretch()
        self.status = QLabel('Load a well to begin')
        self.status.setStyleSheet('color: gray;')
        bottom.addWidget(self.status)
        self._fasta_box = None  # set up in _build_fasta_section

        faasta = self._build_fasta_section()
        layout.addWidget(faasta)

        self._update_timer = QTimer()
        self._update_timer.setSingleShot(True)
        self._update_timer.setInterval(50)
        self._update_timer.timeout.connect(self._update_plot)

        self._opt_worker = None

    def _build_fasta_section(self):
        grp = QGroupBox('FASTA sequence (independent peak-call, IUPAC codes)')
        grp.setFlat(True)
        grp.setToolTip(
            'Result of the independent basecall, shown as FASTA. Bases '
            'printed with IUPAC ambiguity codes (M/R/W/S/Y/K) are positions '
            'where a secondary peak reached the "Ambig %" threshold. Copy '
            'or save with the buttons on the right.')
        lay = QHBoxLayout(grp)
        self._fasta_box = QTextEdit()
        self._fasta_box.setMaximumHeight(80)
        self._fasta_box.setReadOnly(True)
        self._fasta_box.setPlaceholderText('Run independent peak-call to see sequence here')
        self._fasta_box.setToolTip(
            'Called sequence with IUPAC ambiguity codes. Highlight and '
            'copy, or use the Copy / Save FASTA buttons.')
        lay.addWidget(self._fasta_box, stretch=1)
        copy_btn = QPushButton('Copy')
        copy_btn.setToolTip('Copy FASTA to clipboard')
        copy_btn.clicked.connect(self._copy_fasta)
        lay.addWidget(copy_btn)
        save_seq_btn = QPushButton('Save FASTA...')
        save_seq_btn.setToolTip('Save FASTA sequence to a file')
        save_seq_btn.clicked.connect(self._save_fasta)
        lay.addWidget(save_seq_btn)
        return grp

    def _update_fasta_box(self, sequence):
        if not sequence:
            self._fasta_box.setText('')
            return
        well = self.current_well or 'unknown'
        header = f'>{well}_manual'
        wrapped = '\n'.join(sequence[i:i + 80] for i in range(0, len(sequence), 80))
        self._fasta_box.setText(f'{header}\n{wrapped}')
        self._fasta_box.setReadOnly(True)

    def _copy_fasta(self):
        if self._fasta_box and self._fasta_box.toPlainText():
            clipboard = QApplication.clipboard()
            clipboard.setText(self._fasta_box.toPlainText())
            self.status.setText('FASTA sequence copied to clipboard')
            QTimer.singleShot(3000, lambda: self.status.setText(
                f'{self.current_well}: ready' if self.rsd_raw else 'Load a well to begin'))

    def _save_fasta(self):
        if not self._manual_sequence:
            return
        from PyQt5.QtWidgets import QFileDialog
        path, _ = QFileDialog.getSaveFileName(self, 'Save FASTA', '',
                                               'FASTA Files (*.fasta *.fa *.fna);;All Files (*)')
        if not path:
            return
        well = self.current_well or 'unknown'
        header = f'>{well}_manual'
        wrapped = '\n'.join(self._manual_sequence[i:i + 80]
                            for i in range(0, len(self._manual_sequence), 80))
        with open(path, 'w') as f:
            f.write(header + '\n')
            f.write(wrapped + '\n')
        self.status.setText(f'Saved FASTA to {path}')

    def _link_slider_spinbox(self, slider, spinbox):
        def on_slider(v):
            spinbox.blockSignals(True)
            spinbox.setValue(v)
            spinbox.blockSignals(False)
            self._schedule_update()
        def on_spinbox(v):
            slider.blockSignals(True)
            slider.setValue(v)
            slider.blockSignals(False)
            self._schedule_update()
        slider.valueChanged.connect(on_slider)
        spinbox.valueChanged.connect(on_spinbox)

    def _reset_mobility_shifts(self):
        for sp in self.mobility_spins:
            sp.blockSignals(True)
            sp.setValue(0)
            sp.blockSignals(False)
        self._schedule_update()

    def _save_settings(self):
        self._settings.setValue('baseline_method', self.baseline_combo.currentText())
        self._settings.setValue('baseline_window', self.bl_spin.value())
        self._settings.setValue('baseline_window2', self.bl2_spin.value())
        self._settings.setValue('smooth_method', self.smooth_combo.currentText())
        self._settings.setValue('smooth_window', self.sm_win_spin.value())
        self._settings.setValue('smooth_order', self.sm_ord_spin.value())
        self._settings.setValue('min_distance', self.distance_spin.value())
        self._settings.setValue('prominence_frac', self.prominence_spin.value())
        self._settings.setValue('min_signal_frac', self.ambig_spin.value())
        for r in range(4):
            for c in range(4):
                self._settings.setValue(f'matrix_{r}_{c}',
                                        self.mx_grid_spins[r][c].value())
        for ch in range(4):
            self._settings.setValue(f'mobility_shift_{ch}',
                                    self.mobility_spins[ch].value())

    def _restore_settings(self):
        def restore_combo(combo, key, default):
            val = self._settings.value(key, default)
            idx = combo.findText(val)
            if idx >= 0:
                combo.setCurrentIndex(idx)
        def restore_spin(spin, key, default):
            spin.setValue(int(self._settings.value(key, default)))
        restore_combo(self.baseline_combo, 'baseline_method', 'Rolling Minimum')
        restore_spin(self.bl_spin, 'baseline_window', 200)
        restore_spin(self.bl2_spin, 'baseline_window2', 1)
        restore_combo(self.smooth_combo, 'smooth_method', 'Savitzky-Golay')
        restore_spin(self.sm_win_spin, 'smooth_window', 7)
        restore_spin(self.sm_ord_spin, 'smooth_order', 2)
        self._on_smooth_method_changed(self.smooth_combo.currentText())
        restore_spin(self.distance_spin, 'min_distance', 5)
        restore_spin(self.prominence_spin, 'prominence_frac', 20)
        restore_spin(self.ambig_spin, 'min_signal_frac', 25)
        for r in range(4):
            for c in range(4):
                default = float(DEFAULT_SPEC_MATRIX[r, c])
                val = float(self._settings.value(f'matrix_{r}_{c}', default))
                sp = self.mx_grid_spins[r][c]
                sp.blockSignals(True)
                sp.setValue(val)
                sp.blockSignals(False)
        for ch in range(4):
            val = int(self._settings.value(f'mobility_shift_{ch}', 0))
            sp = self.mobility_spins[ch]
            sp.blockSignals(True)
            sp.setValue(val)
            sp.blockSignals(False)

    def closeEvent(self, event):
        self._save_settings()
        super().closeEvent(event)

    # ------------------------------------------------------------------
    # Manual shift line dragging
    # ------------------------------------------------------------------

    def _on_drag_mode_toggled(self, checked):
        if checked:
            self.status.setText('Drag mode: click a colored line on the separated plot to adjust')
            self.drag_mode_btn.setText('✓ Drag mode')
        else:
            self.drag_mode_btn.setText('Drag shift lines')
            self.status.setText('Drag mode off')
            if self._drag_channel is not None:
                self._drag_channel = None
                self._schedule_update()

    def _on_canvas_press(self, event):
        if not self.drag_mode_btn.isChecked() or event.button != 1:
            return
        if event.inaxes is None:
            return
        ax = event.inaxes
        # Only allow dragging on ax3 (separated plot, subplot index 3 = 4th)
        axes_list = self.fig.axes
        if ax not in axes_list or axes_list.index(ax) != 2:
            return
        x = event.xdata
        if x is None:
            return
        # Find nearest draggable line (one per channel, drawn as dashed vlines)
        if not hasattr(self, '_shift_lines') or not self._shift_lines:
            self._draw_shift_lines(ax)
        best_ch = -1
        best_dist = 50
        for ch, (line, _) in self._shift_lines.items():
            lx = line.get_xdata()[0]
            dist = abs(lx - x)
            if dist < best_dist:
                best_dist = dist
                best_ch = ch
        if best_ch < 0:
            self._drag_channel = None
            return
        self._drag_channel = best_ch
        self._drag_start_x = x
        self._shift_lines[best_ch][0].set_linewidth(2.0)
        self.canvas.draw()

    def _on_canvas_move(self, event):
        if self._drag_channel is None or event.inaxes is None:
            return
        x = event.xdata
        if x is None:
            return
        line, base_pos = self._shift_lines[self._drag_channel]
        line.set_xdata([x])
        self.canvas.draw_idle()

    def _on_canvas_release(self, event):
        if self._drag_channel is None:
            return
        ch = self._drag_channel
        line, base_pos = self._shift_lines[ch]
        new_x = line.get_xdata()[0]
        delta = int(new_x - base_pos)
        if delta != 0:
            new_val = self.mobility_spins[ch].value() + delta
            new_val = max(self.mobility_spins[ch].minimum(),
                          min(self.mobility_spins[ch].maximum(), new_val))
            self.mobility_spins[ch].blockSignals(True)
            self.mobility_spins[ch].setValue(new_val)
            self.mobility_spins[ch].blockSignals(False)
        self._drag_channel = None
        self._schedule_update()

    def _draw_shift_lines(self, ax):
        """Draw a dashed vertical line for each channel at the position of
        that channel's tallest peak, or at a fixed reference. The line's
        x-position represents the channel's current effective shift."""
        if not hasattr(self, '_shift_lines'):
            self._shift_lines = {}
        for line in self._shift_lines.values():
            line[0].remove()
        self._shift_lines.clear()
        separated = getattr(self, '_last_separated', None)
        shifts = self._get_mobility_shifts()
        for ch in range(4):
            if separated is not None and separated[:, ch].max() > 0:
                ref_pos = int(np.argmax(separated[:, ch]))
            else:
                ref_pos = 100
            line = ax.axvline(x=ref_pos, color=CHAN_COLORS[ch],
                               linestyle='--', linewidth=1.5, alpha=0.8,
                               label=f'{BASE_LETTERS[ch]} shift={shifts[ch]}')
            self._shift_lines[ch] = (line, ref_pos)

    # ------------------------------------------------------------------
    # Automated / explicit basecalling
    # ------------------------------------------------------------------

    def _run_basecall(self):
        """Run the independent peak-call with current settings and update
        the FASTA box, plot, and status. Can be called programmatically:

            gui = SequencingGUI()
            gui._load_data_with_path(rsd_path, esd_path)
            gui._run_basecall()
        """
        if self.rsd_raw is None:
            self.status.setText('Load a well first')
            return
        result = self._process()
        if result is None:
            return
        raw, bl, corr, sm, separated, mix = result
        self._last_separated = separated
        shifts = self._get_mobility_shifts()
        try:
            # Pass unshifted `separated` - pc_call_bases_with_shifts applies
            # the mobility shift itself. See the note in _update_plot for
            # why passing an already-shifted trace here double-applies it.
            pos, seq, groups, ints = pc_call_bases_with_shifts(
                separated, shifts,
                min_distance=max(1, self.distance_spin.value()),
                prominence_frac=self.prominence_spin.value() / 1000.0,
                min_signal_frac=self.ambig_spin.value() / 100.0,
            )
            self._manual_sequence = seq
            self._update_fasta_box(seq)
            self.status.setText(f'Basecalled {len(seq)} bases with IUPAC codes')
        except Exception as e:
            self.status.setText(f'Basecall error: {e}')
        self._schedule_update()

    def load_settings_from_dict(self, settings_dict):
        """Programmatic API: apply a dict of settings and refresh.
        Keys: baseline_method, baseline_window, smooth_method,
        smooth_window, smooth_order, matrix (4x4 list),
        mobility_shifts (4-list of ints)."""
        if 'baseline_method' in settings_dict:
            idx = self.baseline_combo.findText(settings_dict['baseline_method'])
            if idx >= 0:
                self.baseline_combo.setCurrentIndex(idx)
        if 'baseline_window' in settings_dict:
            self.bl_spin.setValue(int(settings_dict['baseline_window']))
        if 'baseline_window2' in settings_dict:
            self.bl2_spin.setValue(int(settings_dict['baseline_window2']))
        if 'smooth_method' in settings_dict:
            idx = self.smooth_combo.findText(settings_dict['smooth_method'])
            if idx >= 0:
                self.smooth_combo.setCurrentIndex(idx)
        if 'smooth_window' in settings_dict:
            self.sm_win_spin.setValue(int(settings_dict['smooth_window']))
        if 'smooth_order' in settings_dict:
            self.sm_ord_spin.setValue(int(settings_dict['smooth_order']))
        if 'min_distance' in settings_dict:
            self.distance_spin.setValue(int(settings_dict['min_distance']))
        if 'prominence_frac' in settings_dict:
            self.prominence_spin.setValue(int(round(float(settings_dict['prominence_frac']) * 1000.0)))
        if 'min_signal_frac' in settings_dict:
            self.ambig_spin.setValue(int(round(float(settings_dict['min_signal_frac']) * 100.0)))
        if 'matrix' in settings_dict:
            self._set_matrix(np.array(settings_dict['matrix']))
        if 'mobility_shifts' in settings_dict:
            for ch, val in enumerate(settings_dict['mobility_shifts']):
                self.mobility_spins[ch].setValue(int(val))
        self._save_settings()
        self._schedule_update()

    def _write_init_json(self):
        """Write current GUI settings to a temp JSON file and return its path
        for passing to optimize_params.py via --init-json."""
        if self.rsd_raw is None:
            return None
        try:
            settings = self.get_settings()
            path = os.path.join(tempfile.mkdtemp(prefix='gui_init_'),
                                'current_settings.json')
            with open(path, 'w') as f:
                json.dump(settings, f)
            return path
        except Exception:
            return None

    def get_settings(self):
        """Return current settings as a dict for automation/saving."""
        return {
            'baseline_method': self.baseline_combo.currentText(),
            'baseline_window': self.bl_spin.value(),
            'baseline_window2': self.bl2_spin.value(),
            'smooth_method': self.smooth_combo.currentText(),
            'smooth_window': self.sm_win_spin.value(),
            'smooth_order': self.sm_ord_spin.value(),
            'min_distance': self.distance_spin.value(),
            'prominence_frac': self.prominence_spin.value() / 1000.0,
            'min_signal_frac': self.ambig_spin.value() / 100.0,
            'matrix': self._get_matrix().tolist(),
            'mobility_shifts': self._get_mobility_shifts(),
        }

    def _on_smooth_method_changed(self, method):
        self._smooth_mode = method
        label1, range1, label2, range2 = SMOOTH_PARAM_CONFIG.get(
            method, ('Window:', (3, 51), 'Order:', (1, 20)))
        self.sm_param1_label.setText(label1)
        self.sm_param2_label.setText(label2)
        self.sm_win_slider.setRange(*range1)
        self.sm_win_spin.setRange(*range1)
        self.sm_ord_slider.setRange(*range2)
        self.sm_ord_spin.setRange(*range2)
        self._schedule_update()

    def _on_baseline_method_changed(self, method):
        cfg = BASELINE_PARAM_CONFIG.get(
            method, ('Window:', (20, 1000), None, None))
        label1, rng1, label2, rng2 = cfg
        self.bl_param_label.setText(label1)
        self.bl_spin.setRange(*rng1)
        self.bl_slider.setRange(*rng1)
        self.bl_spin.setValue(int(np.mean(rng1)))
        self.bl_slider.setValue(int(np.mean(rng1)))
        if label2 is not None and rng2 is not None:
            self.bl2_param_label.setText(label2)
            self.bl2_param_label.setVisible(True)
            self.bl2_slider.setVisible(True)
            self.bl2_spin.setVisible(True)
            self.bl2_param_label.setToolTip(f'{label2} for {method}')
            self.bl2_slider.setRange(*rng2)
            self.bl2_spin.setRange(*rng2)
            self.bl2_spin.setValue(int(np.mean(rng2)))
            self.bl2_slider.setValue(int(np.mean(rng2)))
        else:
            self.bl2_param_label.setVisible(False)
            self.bl2_slider.setVisible(False)
            self.bl2_spin.setVisible(False)
        self._schedule_update()

    def _set_matrix(self, mat):
        mat = np.asarray(mat, dtype=np.float64)
        for r in range(4):
            for c in range(4):
                sp = self.mx_grid_spins[r][c]
                sp.blockSignals(True)
                sp.setValue(float(mat[r, c]))
                sp.blockSignals(False)
        self._schedule_update()

    def _get_matrix(self):
        mat = np.zeros((4, 4), dtype=np.float64)
        for r in range(4):
            for c in range(4):
                mat[r, c] = self.mx_grid_spins[r][c].value()
        return mat

    def _schedule_update(self):
        self._update_timer.start()

    def _populate_wells(self):
        if os.path.isdir(BASE_DIR):
            wells = sorted(f[:-4] for f in os.listdir(BASE_DIR)
                           if f.endswith('.rsd'))
            self.well_combo.clear()
            self.well_combo.addItems(wells)
            if 'A01' in wells:
                self.well_combo.setCurrentText('A01')
        subdirs = find_esd_subdirs(BASE_DIR) if os.path.isdir(BASE_DIR) else {}
        self.esd_combo.clear()
        for k in sorted(subdirs):
            self.esd_combo.addItem(k, subdirs[k])
        if self.esd_combo.count() > 0:
            cp312_idx = self.esd_combo.findText('Cp312')
            if cp312_idx >= 0:
                self.esd_combo.setCurrentIndex(cp312_idx)
            else:
                self.esd_combo.setCurrentIndex(0)

    def _load_data(self):
        well = self.well_combo.currentText().strip()
        if not well:
            return
        rsd_path = os.path.join(BASE_DIR, f'{well}.rsd')
        esd_subdir = self.esd_combo.currentData() or ''
        esd_path = os.path.join(BASE_DIR, esd_subdir, f'{well}.esd')
        if not os.path.exists(rsd_path):
            self.status.setText(f'Missing: {rsd_path}')
            return
        if not os.path.exists(esd_path):
            self.status.setText(f'Missing: {esd_path}')
            return
        try:
            df = parse_rsd(rsd_path)
            self.rsd_raw = df[['Channel1', 'Channel2', 'Channel3',
                               'Channel4']].values.astype(np.float64)
            self.x_rsd = np.arange(len(self.rsd_raw))
            self.esd_data = parse_esd(esd_path)
            self._load_esd_traces(esd_path)
            self.x_esd = np.arange(len(self.esd_traces))
            self.esd_offset = self._estimate_esd_offset(
                self.esd_data.get('peak_positions'), self.esd_traces)
            self.current_well = well
            n_peaks = len(self.esd_data.get('peak_positions', []))
            self.status.setText(
                f'{well}: RSD {len(self.rsd_raw)} scans, '
                f'ESD {len(self.esd_traces)} recs, {n_peaks} peaks, '
                f'offset~{self.esd_offset}')
            self._update_plot()
            self.drag_mode_btn.setVisible(True)
        except Exception as e:
            self.status.setText(f'Error: {e}')
            import traceback
            traceback.print_exc()

    def _estimate_esd_offset(self, peak_positions, esd_traces):
        """Find the constant shift that puts the largest total amplitude
        of the ESD envelope at the ESD-labeled peak positions.

        The ESD basecaller's peak_positions are already on the correct
        coordinate for the RSD trace. But esd_traces (the raw per-record
        amplitude array) starts at record 0 independently, so it doesn't
        line up under those labels. We search for the offset that
        maximizes the average envelope amplitude at the labeled positions."""
        if peak_positions is None or esd_traces is None:
            return 0
        peak_positions = np.asarray(peak_positions, dtype=np.int64)
        peak_positions = peak_positions[peak_positions >= 0]
        if len(peak_positions) == 0:
            return 0
        n_e = len(esd_traces)
        envelope = esd_traces.max(axis=1).astype(np.float64)
        max_pos = int(peak_positions.max())

        def score(offset):
            idx = peak_positions - offset
            m = (idx >= 0) & (idx < n_e)
            if not np.any(m):
                return -np.inf
            return float(envelope[idx[m]].sum()) / max(1, int(m.sum()))

        lo, hi = -n_e, max_pos + 1
        if hi <= lo:
            return 0
        coarse_step = max(1, (hi - lo) // 400)
        best_offset = max(range(lo, hi, coarse_step), key=score)
        best_offset = max(
            range(best_offset - coarse_step, best_offset + coarse_step + 1),
            key=score)
        return int(best_offset)

    def _shift_channel(self, arr, shift):
        """Shift a 1-D channel trace by ``shift`` scans, padding with the
        edge value instead of wrapping (np.roll wraps, smearing the end
        of the trace into the start)."""
        n = len(arr)
        shift = int(np.clip(shift, -(n - 1), n - 1))
        if shift == 0:
            return arr
        out = np.empty_like(arr)
        if shift > 0:
            out[:shift] = arr[0]
            out[shift:] = arr[:-shift]
        else:
            k = -shift
            out[-k:] = arr[-1]
            out[:-k] = arr[k:]
        return out

    def _snap_to_peak_apex(self, traces, p, n_recs, back=2, fwd=15):
        """ESD-called peak positions are systematically shifted left of the
        true apex. Search a small window (mostly forward) around the called
        index and return the position of maximum channel intensity."""
        lo = max(0, p - back)
        hi = min(n_recs, p + fwd + 1)
        if hi <= lo:
            return p
        seg_height = traces[lo:hi].max(axis=1)
        return lo + int(np.argmax(seg_height))

    def _load_esd_traces(self, path):
        with open(path, 'rb') as f:
            raw = f.read()
        n_records = len(raw) // 20
        esd_traces = np.zeros((n_records, 4), dtype=np.float64)
        for i in range(n_records):
            try:
                ch = struct.unpack('<ffff', raw[i*20+4:(i+1)*20])
                ch = tuple(0.0 if (np.isnan(c) or np.isinf(c) or abs(c) > 1000)
                           else max(0.0, c) for c in ch)
                esd_traces[i] = ch
            except Exception:
                esd_traces[i] = 0.0
        max_per_rec = esd_traces.max(axis=1)
        spikes = np.where(max_per_rec > 5)[0]
        if len(spikes) > 0:
            clean_end = spikes[0]
            clean_max = max_per_rec[:clean_end]
            if len(clean_max) > 0:
                limit = float(np.percentile(clean_max, 99.9))
                if 0 < limit < 1000:
                    esd_traces = np.clip(esd_traces, 0, limit)
        non_zero = np.any(esd_traces > 0, axis=1)
        if non_zero.any():
            last_nz = np.where(non_zero)[0][-1]
            self.esd_traces = esd_traces[:last_nz + 50]
        else:
            self.esd_traces = esd_traces

    def _process(self):
        """Thin wrapper around dsp_full_pipeline, reading current widget values.

        Mobility shifts are NOT applied inside the pipeline (so baseline,
        smoothing, and matrix inversion operate on the raw aligned signal).
        Shifts are applied separately to the separated trace for display
        and peak-calling only."""
        if self.rsd_raw is None:
            return None
        return dsp_full_pipeline(
            self.rsd_raw,
            [0, 0, 0, 0],
            self.baseline_combo.currentText(),
            self.bl_spin.value(),
            self._smooth_mode,
            self.sm_win_spin.value(),
            self.sm_ord_spin.value(),
            self._get_matrix(),
            self.bl2_spin.value() if self.bl2_spin else None,
        )

    def _get_mobility_shifts(self):
        """Read per-channel shifts from the spin boxes."""
        return [sp.value() for sp in self.mobility_spins]

    def _apply_shifts_to_separated(self, separated, shifts=None):
        """Apply per-channel mobility shifts to the separated trace only.
        Used for display and peak detection — never fed back into the
        baseline/smoothing/matrix pipeline."""
        if shifts is None:
            shifts = self._get_mobility_shifts()
        out = separated.copy()
        for ch in range(4):
            s = int(shifts[ch])
            if s != 0:
                out[:, ch] = dsp_shift_channel(out[:, ch], s)
        return out

    def _save_limits(self):
        self._saved_lims = {}
        for i, ax in enumerate(self.fig.axes):
            self._saved_lims[i] = {
                'xlim': ax.get_xlim(),
                'ylim': ax.get_ylim(),
                'x_autoscale': ax.get_autoscalex_on(),
                'y_autoscale': ax.get_autoscaley_on(),
            }

    def _restore_limits(self, axes):
        for i, ax in enumerate(axes):
            if i in self._saved_lims:
                lims = self._saved_lims[i]
                if lims['y_autoscale']:
                    ax.autoscale(True, axis='y')
                else:
                    ax.autoscale(False, axis='y')
                    ax.set_ylim(lims['ylim'])
                if not lims['x_autoscale']:
                    ax.set_xlim(lims['xlim'])

    def _update_plot(self):
        if self.rsd_raw is None or self.esd_traces is None:
            return
        result = self._process()
        if result is None:
            return
        self._save_limits()

        raw, bl, corr, sm, separated, mix = result
        self._last_separated = separated
        self.fig.clear()
        ax1 = self.fig.add_subplot(4, 1, 1)
        ax2 = self.fig.add_subplot(4, 1, 2, sharex=ax1)
        ax3 = self.fig.add_subplot(4, 1, 3, sharex=ax1)
        ax4 = self.fig.add_subplot(4, 1, 4, sharex=ax1)
        for ch in range(4):
            ax1.plot(self.x_rsd, raw[:, ch], color=CHAN_COLORS[ch],
                     linewidth=0.3, alpha=0.6)
            ax1.plot(self.x_rsd, bl[:, ch], color=CHAN_COLORS[ch],
                     linewidth=0.5, linestyle='--', alpha=0.5)
        ax1.set_ylabel('Raw + baseline', fontsize=8)
        ax1.tick_params(labelbottom=False, labelsize=7)
        ax1.legend(['Ch0(T)', 'Ch1(G)', 'Ch2(C)', 'Ch3(A)'],
                   fontsize=5, ncol=4, loc='upper right')

        for ch in range(4):
            ax2.plot(self.x_rsd, corr[:, ch], color=CHAN_COLORS[ch],
                     linewidth=0.2, alpha=0.3)
            ax2.plot(self.x_rsd, sm[:, ch], color=CHAN_COLORS[ch], linewidth=0.5)
        ax2.set_ylabel('Corrected + smoothed', fontsize=8)
        ax2.tick_params(labelbottom=False, labelsize=7)

        # Plot 3: Separated (mobility-corrected), our own basecall only.
        # ESD is intentionally NOT drawn here - see ax4 ("MegaBACE plot")
        # for MegaBACE's own ESD-called reference trace/sequence.
        shifts = self._get_mobility_shifts()
        separated_shifted = self._apply_shifts_to_separated(separated, shifts)
        for ch in range(4):
            ax3.plot(self.x_rsd, separated_shifted[:, ch], color=CHAN_COLORS[ch],
                     linewidth=0.5, label=f'Sep {BASE_LETTERS[ch]}')
        ax3.set_ylabel('Separated (mobility-corrected)', fontsize=8)
        ax3.tick_params(labelbottom=False, labelsize=7)

        # ESD peak positions/sequence are still read here (needed for the
        # ESD-match% comparison text below and for ax4), just not drawn as
        # a trace/labels on this subplot anymore.
        peaks = self.esd_data.get('peak_positions')
        seq = self.esd_data.get('sequence', '')

        # Plot 4: ESD traces with peaks - this is the only plot that shows
        # MegaBACE's own ESD data.
        esd_offset = getattr(self, 'esd_offset', 0)
        x_esd_aligned = self.x_esd + esd_offset
        for ch in range(4):
            ax4.plot(x_esd_aligned, self.esd_traces[:, ch],
                     color=CHAN_COLORS[ch], linewidth=0.5,
                     label=f'ESD {BASE_LETTERS[ch]}')
        ax4.set_ylabel('ESD traces (MegaBACE)', fontsize=8)
        ax4.set_xlabel('Scan / Record index (aligned)', fontsize=8)
        ax4.tick_params(labelsize=7)
        ax4.legend(fontsize=5, ncol=4, loc='upper right')
        if esd_offset:
            ax4.text(0.01, 0.95,
                     f'ESD trace shifted +{esd_offset} to align under labels',
                     transform=ax4.transAxes, fontsize=6, ha='left', va='top',
                     color='gray')

        if peaks is not None:
            n_esd_recs = len(self.esd_traces)
            esd_max = self.esd_traces.max(axis=0)
            # Draw every MegaBACE ESD base letter in a single flat row near
            # the top of the plot, pinned in axes-fraction so it stays put
            # through zoom/pan - far easier to read as a continuous sequence
            # than labels riding up and down on each peak's own height.
            # Rendering is also batched (one vlines call + one text loop)
            # instead of a separate axvline per base, which was ~840 Line2D
            # artists re-created on every redraw and made the GUI sluggish.
            band_y = 0.93
            tick_y = 0.98
            zero_frac = max(esd_max.max(), 1e-9)
            vx, vcol = [], []
            tick_segs, tick_cols = [], []
            for p in peaks:
                p = int(p)
                native_guess = p - esd_offset
                if native_guess < 0 or native_guess >= n_esd_recs:
                    continue
                p_apex_native = self._snap_to_peak_apex(
                    self.esd_traces, native_guess, n_esd_recs)
                trace = self.esd_traces[p_apex_native]
                dom_ch = np.argmax(trace) if np.any(trace > 0) else -1
                if dom_ch < 0:
                    continue
                color = CHAN_COLORS[dom_ch]
                base = BASE_LETTERS[dom_ch]
                x_disp = p_apex_native + esd_offset
                # short hairline under its letter, colored by winning channel
                vx.append(x_disp)
                vcol.append(color)
                ax4.text(x_disp, band_y, base, transform=ax4.get_xaxis_transform(),
                         fontsize=6, ha='center', va='center', color='black',
                         fontweight='bold', clip_on=True,
                         bbox=dict(facecolor=color, alpha=0.35, pad=0.2,
                                   edgecolor='none'))
                # tiny quality tick pinned above: flat = confident call
                if trace[dom_ch] > 0:
                    conf = float(np.clip(
                        (trace[dom_ch] - np.sort(trace)[-2]) / trace[dom_ch], 0, 1)) \
                        if len(trace) > 1 else 1.0
                    wob = (1.0 - conf) * 0.02
                    xr = np.array([x_disp - 2, x_disp - 1, x_disp,
                                   x_disp + 1, x_disp + 2], dtype=float)
                    tick_segs.append(np.column_stack(
                        [xr, tick_y + wob * np.array([0, 1, -1, 1, 0])]))
                    tick_cols.append(color)
            if vx:
                ax4.vlines(vx, 0.97 * zero_frac, 0.995 * zero_frac,
                           colors=vcol, linewidths=[0.4] * len(vx),
                           alpha=0.15)
                if tick_segs:
                    lc = LineCollection(tick_segs,
                                        transform=ax4.get_xaxis_transform(),
                                        colors=tick_cols, linewidths=0.6,
                                        alpha=0.8, capstyle='round')
                    ax4.add_collection(lc)

        # Matrix condition
        cond = np.linalg.cond(mix)
        ax3.text(0.99, 0.01, f'cond={cond:.2f}', transform=ax3.transAxes,
                 fontsize=7, ha='right', va='bottom', color='gray',
                 bbox=dict(facecolor='white', alpha=0.7, pad=1))

        # ESD match percentage: samples OUR separated trace at ESD's own
        # peak positions. A derived number, not the ESD trace itself, so
        # it's fine to report here even though the ESD trace isn't drawn.
        if peaks is not None and seq:
            n = min(len(seq), len(peaks))
            called = []
            for i in range(n):
                p = int(peaks[i])
                if 0 <= p < len(separated_shifted):
                    ch = np.argmax(separated_shifted[p])
                    called.append(CHEM_MAP[ch])
                else:
                    called.append('N')
            matches = sum(1 for a, b in zip(called, seq) if a == b)
            pct = matches / n * 100 if n > 0 else 0
            ax3.text(0.99, 0.07, f'ESD match: {pct:.1f}%',
                     transform=ax3.transAxes,
                     fontsize=7, ha='right', va='bottom', color='blue',
                     bbox=dict(facecolor='white', alpha=0.7, pad=1))

        # Independent peak-calling on the mobility-corrected separated
        # trace, with IUPAC ambiguity codes and a per-base quality tick.
        if self.rsd_raw is not None:
            try:
                # IMPORTANT: pass the *unshifted* `separated` here, not
                # separated_shifted. pc_call_bases_with_shifts applies the
                # mobility shift itself; passing an already-shifted trace
                # here used to double-apply the shift, which is why called
                # bases landed roughly one peak-spacing away from the true
                # peak apex instead of on it.
                pos, iupac_seq, base_groups, intens = pc_call_bases_with_shifts(
                    separated, shifts,
                    min_distance=max(1, self.distance_spin.value()),
                    prominence_frac=self.prominence_spin.value() / 1000.0,
                    tolerance=4,
                    min_signal_frac=self.ambig_spin.value() / 100.0,
                )
                # Bases sit in one flat row near the top of the plot,
                # rather than riding up and down with each peak's own
                # height - easier to read as a continuous sequence.
                # y is in axes-fraction (0-1), x stays in data coordinates,
                # so the row stays pinned to the top of the visible area
                # through zoom/pan.
                trans = ax3.get_xaxis_transform()
                band_y = 0.90
                tick_y = 0.97
                tick_amp = 0.035  # max vertical wobble for a fully ambiguous call
                half_w = max(1.0, self.distance_spin.value() / 3.0)
                # Batching: one vlines call for all hairlines + one
                # LineCollection for all quality ticks, instead of ~2 plots
                # per base. This cut redraw time dramatically (hundreds of
                # Line2D artists were being recreated on every slider move).
                hv_x, hv_col = [], []
                tick_segs, tick_cols = [], []
                for p, letter in zip(pos, iupac_seq):
                    if not (0 <= p < len(separated_shifted)):
                        continue
                    vals = separated_shifted[p]
                    dom_ch = int(np.argmax(vals))
                    color = CHAN_COLORS[dom_ch]
                    ax3.text(p, band_y, letter, transform=trans, fontsize=5,
                             ha='center', va='center', color='black',
                             fontweight='bold', clip_on=True,
                             bbox=dict(facecolor='yellow', alpha=0.6, pad=0.3,
                                       edgecolor='none'))
                    hv_x.append(p)
                    hv_col.append(color)

                    # Quality tick above the base: how clearly the winning
                    # channel beats the runner-up at this position. A
                    # confident call (winner >> runner-up) draws a flat
                    # horizontal line; an ambiguous call (winner ~= runner-
                    # up, e.g. a heterozygous/IUPAC position) draws a
                    # visibly wobbling one - straighter is better.
                    top, second = np.sort(vals)[-1], np.sort(vals)[-2]
                    confidence = float(np.clip((top - second) / top, 0, 1)) if top > 0 else 0.0
                    wobble = (1.0 - confidence) * tick_amp
                    xs = np.array([p - half_w, p - half_w / 2, p, p + half_w / 2, p + half_w])
                    ys = tick_y + wobble * np.array([0.0, 1.0, -1.0, 1.0, 0.0])
                    tick_segs.append(np.column_stack([xs, ys]))
                    tick_cols.append(color)
                if hv_x:
                    ax3.vlines(hv_x, tick_y, band_y, transform=trans,
                               colors=hv_col, linewidths=[0.3] * len(hv_x),
                               alpha=0.15)
                if tick_segs:
                    lc = LineCollection(tick_segs, transform=trans,
                                        colors=tick_cols, linewidths=0.8,
                                        alpha=0.85, capstyle='round')
                    ax3.add_collection(lc)

                if iupac_seq and len(iupac_seq) > 10:
                    matches_esd = sum(1 for a, b in zip(iupac_seq[:len(seq)], seq[:len(iupac_seq)]) if a == b)
                    n_cmp = min(len(iupac_seq), len(seq))
                    pct_manual = matches_esd / n_cmp * 100 if n_cmp else 0
                    ax3.text(0.99, 0.13, f'Independent: {len(iupac_seq)} bases ({pct_manual:.1f}% vs ESD)',
                             transform=ax3.transAxes, fontsize=7, ha='right', va='bottom',
                             color='green', bbox=dict(facecolor='white', alpha=0.7, pad=1))
                    self._manual_sequence = iupac_seq
                    self._update_fasta_box(iupac_seq)
            except Exception as e:
                self._manual_sequence = ''
                self._fasta_box.setText('')
                self.status.setText(f'Independent basecall error: {e}')

        self.fig.subplots_adjust(hspace=0.08, left=0.05, right=0.98,
                                 top=0.97, bottom=0.05)
        self._restore_limits([ax1, ax2, ax3, ax4])
        for ax in [ax1, ax2, ax3]:
            ax.set_xlabel('')
        ax4.set_xlabel('Scan / Record index (aligned)', fontsize=8)
        if self.drag_mode_btn.isChecked():
            self._draw_shift_lines(ax3)
            self.drag_mode_btn.setVisible(True)
        else:
            self._shift_lines.clear()
        self.canvas.draw()

    def _save_data(self):
        if self.rsd_raw is None:
            return
        result = self._process()
        if result is None:
            return
        raw, bl, corr, sm, separated, mix = result
        dir_path = QFileDialog.getExistingDirectory(self, 'Select save directory')
        if not dir_path:
            return
        well = self.current_well or 'unknown'
        np.savez(os.path.join(dir_path, f'{well}_processed.npz'),
                 raw=raw, baseline=bl, corrected=corr, smoothed=sm,
                 separated=separated, mixing_matrix=mix,
                 esd_traces=self.esd_traces)
        with open(os.path.join(dir_path, f'{well}_matrix.json'), 'w') as f:
            json.dump({
                'well': well,
                'matrix': mix.tolist(),
                'diagonals': np.diag(mix).tolist(),
                'baseline_window': self.bl_spin.value(),
                'baseline_window2': self.bl2_spin.value(),
                'smooth_window': self.sm_win_spin.value(),
'smooth_order': self.sm_ord_spin.value(),
            'min_distance': self.distance_spin.value(),
            'prominence_frac': self.prominence_spin.value() / 1000.0,
            'min_signal_frac': self.ambig_spin.value() / 100.0,
                'mobility_shifts': [sp.value() for sp in self.mobility_spins],
                'condition': float(np.linalg.cond(mix)),
            }, f, indent=2)
        self.status.setText(f'Saved to {dir_path}')

    def _run_ml(self):
        """ML basecalling: feeds raw (unseparated) RSD trace patches centered
        at ESD peak positions through the trained CNN model.

        The model was trained on raw 4-channel patches at ESD-aligned peaks,
        so it implicitly handles spectral unmixing — no baseline correction,
        smoothing, or matrix inversion needed. This is why it achieves
        ~98% vs ESD (vs ~30% for naive argmax on separated traces).

        Also evaluates against the M13 reference (the true ground truth),
        since ESD itself only matches M13 at ~92%."""
        if self.current_well is None:
            self.status.setText('Load a well first')
            return
        self.progress.setVisible(True)
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.status.setText('Running ML basecalling...')
        QApplication.processEvents()

        from basecaller import _load_ml_model, ML_LABELS
        model = _load_ml_model()
        window = 15

        # Read raw RSD trace (NOT the processed/separated trace)
        well = self.current_well
        rsd_path = os.path.join(BASE_DIR, f'{well}.rsd')
        df = parse_rsd(rsd_path)
        raw = df[['Channel1', 'Channel2', 'Channel3',
                  'Channel4']].values.astype(np.float32)

        # ESD data for evaluation
        esd_path = os.path.join(BASE_DIR,
                                self.esd_combo.currentData() or '',
                                f'{well}.esd')
        esd_data = parse_esd(esd_path)
        positions = esd_data.get('peak_positions')
        seq = esd_data.get('sequence', '')
        if positions is None or not seq:
            self.status.setText('No ESD peaks to evaluate')
            self.progress.setVisible(False)
            return

        n_scans = len(raw)
        # Clamp positions to valid range for patch extraction
        valid = np.where((positions >= window) &
                         (positions < n_scans - window))[0]
        valid_positions = positions[valid]

        self.progress.setValue(20)
        QApplication.processEvents()

        # Build batch of normalized patches
        X = np.array([raw[int(p) - window:int(p) + window + 1]
                      for p in valid_positions], dtype=np.float32)
        X_mean = X.mean(axis=(1,), keepdims=True)
        X_std = X.std(axis=(1,), keepdims=True) + 1e-8
        X = (X - X_mean) / X_std

        self.progress.setValue(40)
        QApplication.processEvents()

        preds = model.predict(X, verbose=0)
        pred_classes = preds.argmax(axis=1)
        pred_probs = preds.max(axis=1)

        self.progress.setValue(70)
        QApplication.processEvents()

        # Assemble called sequence at ESD positions
        esd_seq_valid = ''.join(seq[i] for i in valid if i < len(seq))
        bases = []
        quals = []
        for cls, prob in zip(pred_classes, pred_probs):
            base = ML_LABELS[cls]
            qual = int(round(prob * 100))
            if qual < 20:
                base = 'N'
            bases.append(base)
            quals.append(qual)
        called = ''.join(bases)

        # Identity vs ESD
        n = min(len(called), len(esd_seq_valid))
        matches_esd = sum(1 for a, b in zip(called[:n], esd_seq_valid[:n])
                         if a == b)
        esd_identity = matches_esd / n * 100 if n > 0 else 0

        # Identity vs M13 (true ground truth)
        from simple_align import M13_REFERENCE
        q = ''.join(c for c in bases if c in 'ACGT')
        m13_result = self._align_to_m13(q)
        m13_identity = m13_result.get('identity', 0) if m13_result else 0

        # Quality distribution
        conf_called = [p for b, p in zip(bases, pred_probs) if b != 'N']
        if conf_called:
            avg_conf = np.mean(conf_called) * 100
        else:
            avg_conf = 0

        non_n = sum(1 for b in bases if b != 'N')
        self.progress.setValue(100)
        self.status.setText(
            f'ML basecall: {non_n}/{len(bases)} called (avg conf {avg_conf:.0f}%). '
            f'vs ESD={esd_identity:.1f}%, vs M13={m13_identity:.1f}%')
        QTimer.singleShot(3000, lambda: self.progress.setVisible(False))

    @staticmethod
    def _align_to_m13(query, ref=None):
        """Needleman-Wunsch alignment of query string to M13 reference."""
        from simple_align import M13_REFERENCE
        if ref is None:
            ref = M13_REFERENCE
        q = ''.join(c for c in query if c in 'ACGT')
        if len(q) < 20:
            return None
        m, n = len(q), len(ref)
        dp = np.zeros((m + 1, n + 1), dtype=np.int32)
        dp[:, 0] = np.arange(m + 1) * -2
        dp[0, :] = np.arange(n + 1) * -2
        for i in range(1, m + 1):
            for j in range(1, n + 1):
                diag = dp[i - 1, j - 1] + (1 if q[i - 1] == ref[j - 1] else -1)
                up = dp[i - 1, j] + -2
                left = dp[i, j - 1] + -2
                dp[i, j] = max(diag, up, left)
        i, j = m, n
        matches = 0
        aligned = 0
        while i > 0 or j > 0:
            if i > 0 and j > 0 and dp[i, j] == dp[i - 1, j - 1] + \
                    (1 if q[i - 1] == ref[j - 1] else -1):
                aligned += 1
                if q[i - 1] == ref[j - 1]:
                    matches += 1
                i -= 1
                j -= 1
            elif i > 0 and dp[i, j] == dp[i - 1, j] + -2:
                aligned += 1
                i -= 1
            else:
                aligned += 1
                j -= 1
        return {
            'matches': matches,
            'alignment_length': aligned,
            'identity': matches / aligned * 100 if aligned else 0,
        } if aligned else None

    def _nw_identity(self, q, r, match=1, mismatch=-1, gap=-2):
        m, n = len(q), len(r)
        dp = [[0] * (n + 1) for _ in range(m + 1)]
        for i in range(1, m + 1):
            dp[i][0] = dp[i-1][0] + gap
        for j in range(1, n + 1):
            dp[0][j] = dp[0][j-1] + gap
        for i in range(1, m + 1):
            for j in range(1, n + 1):
                diag = dp[i-1][j-1] + (match if q[i-1] == r[j-1] else mismatch)
                up = dp[i-1][j] + gap
                left = dp[i][j-1] + gap
                dp[i][j] = max(diag, up, left)
        i, j = m, n
        matches = 0
        aligned = 0
        while i > 0 or j > 0:
            if i > 0 and j > 0 and dp[i][j] == dp[i-1][j-1] + \
                    (match if q[i-1] == r[j-1] else mismatch):
                aligned += 1
                if q[i-1] == r[j-1]:
                    matches += 1
                i -= 1
                j -= 1
            elif i > 0 and dp[i][j] == dp[i-1][j] + gap:
                aligned += 1
                i -= 1
            else:
                aligned += 1
                j -= 1
        return 100.0 * matches / aligned if aligned else 0.0

    def _run_independent_peakcall(self):
        """Run a real peak detector on the shifted separated trace (no ESD peak
        positions involved) and align the result against the ESD sequence.
        This is the number to trust over the plot's 'ESD match %', which
        only samples the trace at positions ESD already told it were peaks."""
        if self.rsd_raw is None or self.esd_data is None:
            self.status.setText('Load a well first')
            return
        result = self._process()
        if result is None:
            return
        _, _, _, _, separated, _ = result
        shifts = self._get_mobility_shifts()
        sep_shifted = self._apply_shifts_to_separated(separated, shifts)
        esd_seq = self.esd_data.get('sequence', '')
        if not esd_seq:
            self.status.setText('No ESD sequence to compare against')
            return
        positions, called_seq, heights = pc_call_bases(sep_shifted)
        identity = pc_nw_identity(called_seq, esd_seq, max_len=20000)
        self.status.setText(
            f'Independent peak-call: {len(called_seq)} bases called '
            f'(ESD has {len(esd_seq)}) - alignment identity vs ESD: '
            f'{identity:.1f}%')

    def _run_auto_mobility(self):
        """Cross-correlation-based mobility shift estimate. Only reliable
        on calibration-standard data - see the button tooltip and
        pc_estimate_mobility_shifts's docstring for why an ordinary
        sequencing read doesn't give this a fair signal to lock onto."""
        if self.rsd_raw is None:
            self.status.setText('Load a well first')
            return
        shifts = pc_estimate_mobility_shifts(self.rsd_raw, ref_channel=3)
        for ch, sp in enumerate(self.mobility_spins):
            sp.blockSignals(True)
            sp.setValue(int(np.clip(shifts[ch], sp.minimum(), sp.maximum())))
            sp.blockSignals(False)
        self._schedule_update()
        self.status.setText(
            f'Auto mobility shift (calibration-run estimate): {list(shifts)} '
            '- verify against a known standard before trusting on real reads')

    def _run_optimizer(self):
        """Shell out to optimize_params.py in a background thread so the
        GUI stays responsive (the optimization can take 1-30 minutes
        depending on well count and maxiter)."""
        if self.current_well is None:
            self.status.setText('Load a well first')
            return
        script = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                              'optimize_params.py')
        if not os.path.exists(script):
            self.status.setText('optimize_params.py not found next to this script')
            return
        esd_subdir = self.esd_combo.currentData() or ''
        out_path = os.path.join(tempfile.mkdtemp(prefix='optimize_'),
                                'best_params.json')
        self.status.setText(
            f'Optimizing parameters for well {self.current_well} ...')
        self.progress.setVisible(True)
        self.progress.setRange(0, 0)
        self.progress.setValue(-1)
        self.opt_log.clear()
        self.opt_log.show()
        self.cancel_opt_btn.setVisible(True)
        self._disable_controls()

        cmd = [sys.executable, '-u', script, '--base-dir', BASE_DIR,
               '--wells', self.current_well, '--maxiter', '30',
               '--popsize', '10', '--out', out_path]
        if esd_subdir:
            subdirs = find_esd_subdirs(BASE_DIR)
            for name, d in subdirs.items():
                if d == esd_subdir:
                    cmd += ['--esd-subdir', name]
                    break
        init_json = self._write_init_json()
        if init_json:
            cmd += ['--init-json', init_json]
            self.status.setText(
                f'Optimizing from current settings ...')
        else:
            self.status.setText(
                f'Optimizing parameters for well {self.current_well} ...')

        worker = OptimizerWorker(cmd, out_path, self)
        worker.finished.connect(self._on_optimizer_finished)
        worker.stdout_line.connect(self._on_optimizer_stdout)
        worker.start()
        self._opt_worker = worker

    def _cancel_optimizer(self):
        if self._opt_worker and self._opt_worker.isRunning():
            self._opt_worker.cancel()
            self.status.setText('Cancelling optimizer...')
        self.cancel_opt_btn.setVisible(False)

    def _on_optimizer_stdout(self, line):
        """Stream optimizer progress lines to the log window."""
        self.opt_log.append(line)
        vs = self.opt_log.verticalScrollBar()
        if vs:
            vs.setValue(vs.maximum())

    def _disable_controls(self):
        for w in [self.well_combo, self.esd_combo, self.load_btn,
                  self.save_btn, self.ml_btn, self.peakcall_btn,
                  self.mobility_btn, self.optimize_btn]:
            w.setEnabled(False)

    def _enable_controls(self):
        for w in [self.well_combo, self.esd_combo, self.load_btn,
                  self.save_btn, self.ml_btn, self.peakcall_btn,
                  self.mobility_btn, self.optimize_btn]:
            w.setEnabled(True)

    def _on_optimizer_finished(self, result):
        """Handle the OptimizerWorker.finished signal."""
        self.progress.setRange(0, 100)
        self.progress.setVisible(False)
        self.cancel_opt_btn.setVisible(False)
        self.opt_log.hide()
        self._enable_controls()

        if result.startswith('ERROR:'):
            self.status.setText(result)
            return

        out_path = result
        try:
            with open(out_path) as f:
                best = json.load(f)
        except Exception as e:
            self.status.setText(f'Could not read optimizer output: {e}')
            return

        idx = self.baseline_combo.findText(best['baseline_method'])
        if idx >= 0:
            self.baseline_combo.setCurrentIndex(idx)
        self.bl_spin.setValue(int(round(best['baseline_window'])))
        if 'baseline_window2' in best:
            self.bl2_spin.setValue(int(round(best['baseline_window2'])))
        idx = self.smooth_combo.findText(best['smooth_method'])
        if idx >= 0:
            self.smooth_combo.setCurrentIndex(idx)
        self.sm_win_spin.setValue(int(round(best['smooth_window'])))
        self.sm_ord_spin.setValue(int(round(best['smooth_order'])))
        for ch, sp in enumerate(self.mobility_spins):
            sp.blockSignals(True)
            sp.setValue(int(best['mobility_shifts'][ch]))
            sp.blockSignals(False)
        self._set_matrix(np.array(best['matrix']))
        self.status.setText(
            f"Optimizer found {best['best_identity_pct']:.1f}% identity vs ESD "
            f"with {best['baseline_method']}/{best['smooth_method']} - loaded into controls")

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_R:
            self._reset_view()
        elif event.key() == Qt.Key_L:
            self._load_data()

    def _reset_view(self):
        self._saved_lims = {}
        for ax in self.fig.axes:
            ax.autoscale(True)
        self.canvas.draw()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    window = SequencingGUI()
    window.show()
    sys.exit(app.exec_())
