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
    QFileDialog, QProgressBar, QScrollArea, QFrame, QDialog, QLineEdit,
    QDialogButtonBox
)
from PyQt5.QtCore import Qt, QTimer, QSettings, QThread, pyqtSignal

import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT
from matplotlib.figure import Figure
from matplotlib.collections import LineCollection

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from extract_training_data import parse_rsd, parse_esd

DEFAULT_DATA_DIR = "/media/tv/78B0C7DE1FA7081C/electropherogram/MB1000_M13_DT"
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
    'None', 'Rolling Minimum', 'Rolling Median', 'ALS', 'airPLS', 'SNIP',
    'Morphological (Top-hat)', 'Polynomial Detrend',
    'Rubberband', 'AsyLS', 'arPLS', 'Flat Offset (200-1200)',
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

SMOOTH_TOOLTIPS = {
    'Savitzky-Golay': (
        'Savitzky-Golay: fits a polynomial to each sliding window and '
        'evaluates it at the centre point, preserving peak shape and height '
        'better than simple averaging. Window = fit width (odd, must be > '
        'order + 1); Order = polynomial degree (2 is a good default; higher '
        'follows faster changes but keeps more noise). The best default for '
        'Sanger traces.'),
    'Gaussian': (
        'Gaussian: convolves the trace with a Gaussian kernel, the classic '
        'smooth low-pass filter. Window = truncation radius in units of '
        'sigma (how far the kernel extends); Sigma = kernel width. Larger '
        'sigma = stronger smoothing, but narrow peaks get rounded.'),
    'Moving Avg': (
        'Moving Average: replaces each sample with the mean of its window '
        'neighbours - simple and fast, but blunts peak tops and edges. '
        'Window = number of samples averaged (odd, typical 5-11). The '
        'Order control is not used by this method.'),
    'Median': (
        'Median: replaces each sample with the median of its window - very '
        'robust to single-sample spikes and salt-and-pepper noise, but '
        'distorts peak shape more than Savitzky-Golay. Window = median '
        'filter size (made odd automatically). The Order control is not '
        'used.'),
    'Whittaker': (
        'Whittaker (penalized least squares): fits a smooth curve by '
        'balancing fidelity to the data against roughness. Excellent '
        'baseline-free smoothing with no window artifacts, but slower on '
        'long reads. Lambda = smoothness penalty (larger = smoother). The '
        'Order control is not used.'),
    'Butterworth': (
        'Butterworth: low-pass IIR filter with a flat passband and no '
        'ripple, applied zero-phase (filtfilt). Cutoff period = smoothing '
        'cutoff wavelength in scans (larger = smoother); Order = filter '
        'steepness (1-10).'),
    'Wavelet': (
        'Wavelet denoising: decomposes the trace and thresholds the detail '
        'coefficients, preserving sharp peak edges while removing noise. '
        'Level = wavelet decomposition depth (1-8); Thresh x100 = threshold '
        'strength. Requires PyWavelets (pywt).'),
    'LOWESS': (
        'LOWESS: locally weighted polynomial regression - a robust, '
        'adaptive smoother that handles varying peak density well, but is '
        'the slowest method. Frac x1000 = fraction of the trace used per '
        'fit point (larger = smoother); Iterations = robust refits (0-5). '
        'Requires statsmodels.'),
    'FFT Lowpass': (
        'FFT Lowpass: removes high-frequency noise by zeroing the Fourier '
        'components above the cutoff, with a tapered roll-off to avoid '
        'ringing. Cutoff period = shortest period kept in scans (larger = '
        'smoother); Taper % = softness of the cutoff transition (0-50).'),
}

SMOOTH_PARAM1_TOOLTIPS = {
    'Savitzky-Golay': 'Window: fit width in scans. Must be odd and larger '
                      'than Order + 1. Typical 5-11.',
    'Gaussian':       'Window: kernel truncation radius, in units of Sigma '
                      '(how far the Gaussian extends).',
    'Moving Avg':     'Window: number of samples averaged together. Odd only; '
                      'typical 5-11.',
    'Median':         'Window: median filter size (forced odd).',
    'Whittaker':      'Lambda: smoothness penalty of the penalized-least-'
                      'squares fit. Larger = smoother.',
    'Butterworth':    'Cutoff period: smoothing cutoff wavelength in scans. '
                      'Larger = smoother.',
    'Wavelet':        'Level: wavelet decomposition depth (1-8). Deeper '
                      'thresholds more detail bands.',
    'LOWESS':         'Frac x1000: fraction of the trace used for each local '
                      'fit point. Larger = smoother.',
    'FFT Lowpass':    'Cutoff period: shortest period kept, in scans. Larger '
                      '= smoother.',
}

SMOOTH_PARAM2_TOOLTIPS = {
    'Savitzky-Golay': 'Order: polynomial degree of the fit. Must be less '
                      'than Window. 2 is a good default.',
    'Gaussian':       'Sigma: Gaussian kernel width. Larger = smoother but '
                      'narrow peaks get rounded.',
    'Moving Avg':     'Not used by this method.',
    'Median':         'Not used by this method.',
    'Whittaker':      'Not used by this method.',
    'Butterworth':    'Order: low-pass filter steepness (1-10).',
    'Wavelet':        'Thresh x100: denoising threshold strength '
                      '(10-300, i.e. 0.10-3.00).',
    'LOWESS':         'Iterations: number of robust refits (0-5). More is '
                      'more robust but slower.',
    'FFT Lowpass':    'Taper %: softness of the cutoff transition (0-50). '
                      'More taper = less ringing.',
}

BASELINE_PARAM_CONFIG = {
    'None':                     ('None', (20, 1000), None, None),
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
    'Flat Offset (200-1200)':   ('Start scan:', (100, 2000), 'End scan:', (300, 4000)),
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
        # Per-channel flat offset subtraction: take the mean of each channel
        # over the scan region before the sample signal starts (default
        # 200-1200), subtract that constant from every scan, and floor the
        # result at 0 (the caller clips raw-bl at 0, so negatives become 0).
        start = max(0, int(bw))
        end = min(n, int(window2) if window2 is not None else start + 1000)
        if end <= start:
            end = start + 1000
        region = raw[max(0, start):min(n, end)]
        for ch in range(4):
            ch_region = region[:, ch]
            if len(ch_region) > 0:
                bl[:, ch] = float(np.median(ch_region))
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
    # With baseline method 'None' the baseline is all zeros, so the per-
    # channel dye-gain normalization has nothing to divide by - fall back to
    # no gain compensation (factor 1) instead of amplifying to ~1e10.
    bm[bm <= 1e-9] = 1.0
    gn = sm / (bm[np.newaxis, :] + 1e-10)
    separated = gn @ inv.T
    return np.clip(separated, 0, None)


def dsp_full_pipeline(raw, mobility_shifts, baseline_method, baseline_window,
                      smooth_method, smooth_window, smooth_order, matrix,
                      baseline_window2=None, matrix_apply_point='smoothed'):
    """Full processing pipeline. Returns (raw, bl, corr, sm, separated, mix).

    ``matrix_apply_point`` picks which stage the crosstalk (dye-bleed)
    separation matrix is applied to (development knob):
      'none'       - no separation at all; ``separated`` is just the
                     corrected + smoothed signal (the raw 4 channels pass
                     straight through to peak calling)
      'raw'        - separate the raw data, then baseline-correct the
                     separated signal, then smooth it
      'corrected'  - separate the baseline-corrected signal, then smooth the
                     separated signal
      'smoothed'   - separate the baseline-corrected + smoothed signal
                     (default; matches the classic Sanger pipeline order)
    In every mode the returned ``separated`` is the trace that gets mobility-
    shifted and basecalled, so changing the smoothing always affects it.
    Mobility shifts are never applied inside the pipeline (callers shift the
    separated trace only just before peak detection).
    """
    raw = raw.copy()
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
        # Experimental: apply the crosstalk matrix AFTER per-channel mobility
        # correction instead of before. Each smoothed channel is shifted by its
        # lag and the four shifted channels are then separated. This is the
        # inverse of the classic order (separate, then shift each separated
        # channel) and is exposed via the 'on Shifted' matrix tick box so the
        # user can A-B it. When this stage is active the shift is baked into
        # ``separated`` and the GUI passes zero shifts downstream (see
        # _effective_shifts) so it is not applied twice.
        shifted = np.empty_like(sm)
        for ch in range(4):
            shifted[:, ch] = dsp_shift_channel(sm[:, ch], int(mobility_shifts[ch]))
        separated = dsp_separate_channels(shifted, bl, matrix)
    else:
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


def pc_normalize_display(separated, window=800, region=None):
    """Per-channel rolling-local normalization for display.

    Dividing by each channel's own global max (a single scalar) makes all
    peaks sit in 0-1 at the start of the run but they shrink to ~0.3-0.5
    by the end, because MegaBACE/CE signal amplitude decays continuously
    with scan number. ESD instead reports peaks that are ~uniform 0-1 for
    the entire basecalled region. To match that, divide each channel by a
    rolling local max (window ~= norm window): every peak is then pulled
    up to ~1 regardless of where in the run it sits, so the later (weaker)
    peaks are visible at the same height as the early ones.

    When ``region`` is given, the rolling-max denominator is floored by
    the channel's leading-baseline noise level (just before ``region[0]``).
    Without this, flat baseline noise would be normalized to ~1.0 - the
    same scale as real peaks - and show up as a forest of false peaks in
    the lead-in. With the floor, baseline ripple is suppressed well below
    1 while genuine peaks (whose rolling max dwarfs the floor) stay ~1."""
    x = np.clip(np.asarray(separated, dtype=np.float64), 0, None)
    out = np.empty_like(x)
    for ch in range(4):
        ch_sig = x[:, ch]
        local_max = maximum_filter1d(
            ch_sig, size=max(int(window), 3), mode='nearest')
        floor = np.percentile(ch_sig, 50) * 0.05 + 1e-9
        if region is not None:
            r0 = max(0, int(region[0]))
            lead = ch_sig[max(0, r0 - 200):r0]
            if len(lead) > 0:
                lead_floor = float(np.percentile(lead, 90))
            else:
                lead_floor = floor
            # 2.5x the baseline ripple upper bound so noise stays <~0.4,
            # but never exceed the real peak scale (1/3 of the signal max).
            signal_max = float(ch_sig[r0:int(region[1])].max()) if int(region[1]) > r0 else float(ch_sig.max())
            floor = max(floor, min(2.5 * lead_floor, signal_max / 3.0 + 1e-9))
        denom = np.maximum(local_max, floor)
        out[:, ch] = ch_sig / denom
    # Re-scale so the bulk of the peaks sit around ~1 like ESD.
    scale = np.percentile(out, 99.5, axis=0)
    scale[scale <= 0] = 1.0
    return out / scale[np.newaxis, :]


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


def pc_signal_region(separated, onset_frac=0.05, tail_frac=0.10,
                     smooth=40, tail_margin=10):
    """Detect the callable signal window [start, stop) of a CE run.

    Returns the scan range that actually contains DNA signal: ``start``
    from the same rise-based onset test used by the basecaller
    (``pc_signal_onset``) and ``stop`` as the last scan where the smoothed
    total intensity still exceeds a small fraction of the in-region max.
    Everything before ``start`` is flat instrument baseline; everything at
    or after ``stop`` is the decaying tail / final buffer. Running the
    normalization and basecalling *math* only inside this window keeps
    baseline noise from being amplified into false peaks and keeps the
    display honest. A small ``tail_margin`` is appended so the last real
    peaks are not clipped.

    Returns (start, stop) ints. Falls back to (0, n) when the trace is
    empty or constant."""
    x = np.clip(np.asarray(separated, dtype=np.float64), 0, None)
    n = len(x)
    if n == 0:
        return 0, n
    tot = x.sum(axis=1)
    if tot.max() <= 0:
        return 0, n
    start = int(pc_signal_onset(separated, onset_frac=onset_frac, smooth=smooth))
    start = max(0, min(start, n - 1))
    sig = tot[start:]
    peak = float(sig.max())
    if peak <= 0:
        return start, min(n, start + 1)
    thr = peak * max(float(tail_frac), 0.0)
    idx = np.where(sig > thr)[0]
    if len(idx) == 0:
        return start, min(n, start + 1)
    stop = start + int(idx[-1]) + 1
    stop = min(n, stop + int(tail_margin))
    return start, stop


def pc_call_bases_with_shifts(separated, shifts, min_distance=6,
                              prominence_frac=0.02, tolerance=4,
                              normalize=True, norm_window=800,
                              min_signal_frac=0.25, onset_frac=0.05,
                              signal_onset_smooth=40, min_height_ratio=2.0,
                              region=None):
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

    ``region``=(start, stop) restricts peak calling to that scan window:
    only peaks with start <= pos < stop are kept. When given it overrides
    the ``onset_frac`` onset cut, so the basecalling math runs only inside
    the callable signal region (see pc_signal_region).
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
    # onset_frac=0 disables the cut entirely.  An explicit region=(start,
    # stop) overrides the onset cut: basecalling math runs only inside the
    # callable signal window.
    start = 0
    stop = n
    if region is not None and int(region[1]) > int(region[0]):
        start = max(0, int(region[0]))
        stop = min(n, int(region[1]))
    elif onset_frac and onset_frac > 0:
        start = pc_signal_onset(separated, onset_frac=onset_frac,
                                smooth=signal_onset_smooth)
    channels = [c for c in channels if start <= c[0] < stop]

    positions = []
    base_groups = []
    intensities = []
    i = 0
    while i < len(channels):
        j = i
        cluster = [channels[i]]
        # Compare each candidate against the cluster's *first* member, not
        # its last. With per-member chaining (``... - cluster[-1][0]``), a
        # few tiny noise peaks could bridge two real peaks 8+ scans apart
        # into one cluster, so the taller of the two swallowed its neighbor
        # (e.g. a big T peak at 2975 silently eating a genuine A peak at
        # 2983). Anchoring on the cluster start keeps such peaks separate.
        cluster_start = channels[i][0]
        while j + 1 < len(channels) and channels[j + 1][0] - cluster_start <= tolerance:
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


def pc_call_bases_greedy(separated, shifts, window=5, min_frac=0.20,
                         norm_window=800, region=None):
    """Greedy maximum-intensity peak caller on the per-channel-normalized
    combined envelope.

    This is the classic Sanger "greedy" strategy (the same one used by the
    Biopython/electropherogram-style callers) but applied to the separated
    (matrix-corrected, mobility-shifted) traces instead of raw channel
    intensities - that preprocessing is what makes it work. Each channel is
    divided by its rolling local maximum (``norm_window`` scans) so all four
    channels sit on the same ~0-1 scale, then the four normalized channels
    are combined with a pointwise max. The caller repeatedly takes the
    global maximum of that envelope, calls the dominant channel there, and
    excises a band of +/- ``window`` scans around it so the next iteration
    finds the next base. It stops when the highest remaining envelope value
    drops below ``min_frac`` of the region maximum.

    Picking the strongest peaks first is what makes it robust: noise bumps
    are never reached (a taller real peak is always excised first) and
    shoulder artifacts are excised away with their peak. On the M13 plate
    this replaces the per-channel cluster caller (mean NW identity 88.3% vs
    81.1%, better on all 96 wells).

    ``region``=(start, stop) restricts calling to that scan window (see
    pc_signal_region); when None the auto onset cut is used.

    Returns (positions, sequence, base_groups, intensities) where:
      positions   — scan index of each called position (pick order sorted)
      sequence    — base letter string (one unambiguous base per position)
      base_groups — list of frozensets, each holding the single called letter
      intensities — list of {letter: separated height} dicts
    """
    n = len(separated)
    shifted_all = [dsp_shift_channel(separated[:, ch], int(shifts[ch]))
                   for ch in range(4)]
    normed = np.empty_like(separated)
    for ch in range(4):
        shifted = shifted_all[ch]
        rolled = maximum_filter1d(np.clip(shifted, 0, None),
                                  size=max(3, int(norm_window)), mode='nearest')
        rolled = np.where(rolled > 0, rolled, 1.0)
        normed[:, ch] = shifted / rolled
    comb = normed.max(axis=1)
    start, stop = 0, n
    if region is not None and int(region[1]) > int(region[0]):
        start, stop = max(0, int(region[0])), min(n, int(region[1]))
    else:
        start = pc_signal_onset(separated, onset_frac=0.05, smooth=40)
    if start >= stop:
        return np.array([], dtype=np.int64), '', [], []
    threshold = max(float(comb[start:stop].max()) * min_frac, 1e-9)
    work = comb.copy()
    work[:start] = -1.0
    work[stop:] = -1.0
    picks = []
    letters = []
    while True:
        i = int(np.argmax(work))
        if work[i] < threshold:
            break
        ch = int(np.argmax(normed[i]))
        letter = CHEM_MAP[ch]
        picks.append(i)
        letters.append(letter)
        lo, hi = max(0, i - int(window)), min(n, i + int(window) + 1)
        work[lo:hi] = -1.0
    order = np.argsort(picks)
    positions = np.array(picks, dtype=np.int64)[order]
    sequence = ''.join(letters[k] for k in order)
    base_groups = [frozenset([letters[k]]) for k in order]
    intensities = [{letters[k]: float(shifted_all[int(np.argmax(normed[picks[k]]))]
                                        [picks[k]])} for k in order]
    return positions, sequence, base_groups, intensities


def pc_fill_in_combined_peaks(separated, shifts, positions=None,
                              min_distance=1, prominence_frac=0.02,
                              norm_window=800, fill_gap=3, fill_margin=0.2,
                              onset_frac=0.05, signal_onset_smooth=40,
                              min_height_ratio=2.0, region=None):
    """Recover bases the per-channel cluster merge silently swallowed.

    pc_call_bases_with_shifts merges every per-channel peak within
    ``tolerance`` scans of a cluster's start into one call and keeps only
    the tallest member. Two genuinely adjacent bases (e.g. G~2493 followed
    by T~2496, just 3 scans apart after mobility correction) therefore end
    up as a single call, with the weaker base dropped. This is the standard
    Sanger edge case: adjacent bases on *different* channels can land closer
    than any per-channel ``min_distance``.

    This function re-runs peak detection on the combined envelope
    (``max`` over the 4 shifted channels), where the merged-away base is
    still a clean local maximum, and returns every position that:

      * sits at least ``fill_gap`` scans from every existing call
        (so it is genuinely a separate base, not a duplicate or the
        shoulder of a neighbouring peak),
      * has a dominant channel that clearly beats the runner-up
        (margin >= ``fill_margin``, i.e. it is a clean call, not a
        heterozygous/co-eluting position),
      * rises above its own channel's leading-baseline noise floor
        (same ``min_height_ratio`` test the main caller uses).

    Returns a sorted list of (scan_position, base_letter) tuples ready to be
    merged into the per-channel call set. Purely signal-based - no reference
    used - so the caller stays genuinely independent."""
    from scipy.signal import find_peaks as _fp

    shifted_all = [dsp_shift_channel(separated[:, ch], int(shifts[ch]))
                   for ch in range(4)]
    comb = np.max(np.column_stack(shifted_all), axis=1)
    n = len(comb)
    if n == 0:
        return []
    rolled = maximum_filter1d(np.clip(comb, 0, None),
                              size=max(3, int(norm_window)), mode='nearest')
    rolled = np.where(rolled > 0, rolled, 1.0)
    norm = comb / rolled
    scale = np.percentile(np.clip(norm, 0, None), 99.5)
    prom = max(scale * prominence_frac, 1e-9) if scale > 0 else 1e-9
    peaks, _ = _fp(norm, distance=max(1, int(min_distance)), prominence=prom)

    lead_n = max(int(n * 0.05), 1)
    ch_floor = [float(np.percentile(np.clip(shifted_all[ch][:lead_n], 0, None), 90))
                for ch in range(4)]

    start = 0
    stop = n
    if region is not None and int(region[1]) > int(region[0]):
        start = max(0, int(region[0]))
        stop = min(n, int(region[1]))
    elif onset_frac and onset_frac > 0:
        start = pc_signal_onset(separated, onset_frac=onset_frac,
                                smooth=signal_onset_smooth)

    existing = set(int(p) for p in (positions or []))
    fill_gap = max(1, int(fill_gap))
    fill_margin = float(fill_margin)
    floor_mult = max(float(min_height_ratio), 0.0)
    added = []
    for p in peaks:
        p = int(p)
        if p < start or p >= stop:
            continue
        vals = np.array([shifted_all[ch][p] for ch in range(4)])
        top = vals.max()
        if top <= 0:
            continue
        dom_ch = int(np.argmax(vals))
        if top < ch_floor[dom_ch] * floor_mult:
            continue
        second = float(np.partition(vals, -2)[-2])
        if (top - second) / top < fill_margin:
            continue
        if any(abs(p - q) < fill_gap for q in existing):
            continue
        added.append((p, BASE_LETTERS[dom_ch]))
        existing.add(p)
    return sorted(added, key=lambda t: t[0])


# ---------------------------------------------------------------------------
# LifeTrace-style basecalling (Walther, Bartha & Morris 2001, Genome Res. 11:875)
#
# The LifeTrace algorithm was designed *specifically* for MegaBACE capillary
# sequencers, whose traces show the notorious "accordion effect": peak-to-peak
# spacing changes abruptly along the run (3-fold in the paper's example, and
# 8.2 -> 10.3 -> 6.7 scans across A01/Cp312 here).  Phred's approach - predict
# idealized peak locations from a uniform-spacing assumption and match observed
# peaks to them - desynchronizes when the spacing jumps, producing insertion/
# deletion errors.  LifeTrace instead uses only LOCAL structure:
#
#   1. Peak-shape factor R[b,loc]: Pearson correlation of each trace with an
#      ideal Gaussian model peak over a 7-point window.  Peak-like segments
#      score +1, concavities -1, monotone segments ~0.
#   2. One combined trace LT(loc) = L^k norm (k=4) over the four channels of
#      f = T * (R rescaled to [0,1]).  Narrower peaks, less underlying noise.
#   3. All local maxima of LT are candidate base positions - no global spacing
#      model, so the accordion effect can't desynchronize the caller.
#   4. Base assignment: the channel with the largest fractional AREA in a 7-
#      point window, weighted by R.  If that channel is only the 3rd/4th by
#      plain area, call N (noise in the dominant dye isn't a real base).
#   5. Light quality filters: merge duplicate same-base calls, remove calls
#      whose height is marginal, and re-add bases to broad Gaussian-like peaks.
#
# Implemented as pc_lifetrace_transform() + pc_lifetrace_basecall() so each
# stage can be tuned/A-B'd against pc_call_bases_with_shifts headlessly.
# ---------------------------------------------------------------------------

def pc_lifetrace_peaks_shape(traces, window=7, sigma=3.5):
    """Peak-shape factor R[b,loc] per channel, via sliding Pearson correlation
    with an ideal Gaussian model peak (mp).  Values in [-1, 1]: +1 at a
    peak-like centre, ~0 on monotone slopes, -1 in concavities."""
    traces = np.clip(np.asarray(traces, dtype=np.float64), 0, None)
    n = len(traces)
    half = max(1, window // 2)
    i = np.arange(-half, half + 1, dtype=np.float64)
    mp = np.exp(-i * i / (2.0 * sigma * sigma))
    mp_c = mp - mp.mean()
    sd_mp = np.sqrt((mp_c * mp_c).sum()) or 1.0
    R = np.zeros_like(traces)
    if n <= half:
        return R
    # sliding_window_view needs numpy>=1.20 and produces shape (n-w+1, w)
    w = 2 * half + 1
    for b in range(4):
        t = traces[:, b]
        view = np.lib.stride_tricks.sliding_window_view(t, w)
        t_c = view - view.mean(axis=1, keepdims=True)
        sd_t = np.sqrt((t_c * t_c).sum(axis=1))
        denom = sd_t * sd_mp
        r = (t_c @ mp_c) / np.where(denom > 1e-12, denom, 1.0)
        r[np.abs(denom) <= 1e-12] = 0.0
        R[half:n - half, b] = r
    # terminal 'half' trace points have no full window; LifeTrace zeros them
    return R


def pc_lifetrace_transform(separated, window=7, sigma=3.5, k=4.0):
    """LifeTrace combined peak-likeness trace LT(loc).

    R[b,loc] = peak-shape factor (Pearson corr. with Gaussian model peak).
    Rescaled to [0,1] (the paper multiplies the trace by r rescaled so peak-
    like regions keep full weight while flat/monotone regions shrink), then
    f = T * R.  LT is the L^k norm across channels (k=4: converges toward the
    max with mild smoothing; the paper's best setting)."""
    T = np.clip(np.asarray(separated, dtype=np.float64), 0, None)
    R = pc_lifetrace_peaks_shape(T, window=window, sigma=sigma)
    R01 = np.clip((R + 1.0) / 2.0, 0.0, 1.0)
    f = np.clip(T * R01, 0.0, None)
    return np.power(np.sum(np.power(f, k), axis=1), 1.0 / k)


def pc_lifetrace_basecall(separated, shifts, window=7, sigma=3.5, k=4.0,
                          min_height_ratio=2.0, onset_frac=0.05,
                          signal_onset_smooth=40, merge_same=3.0,
                          add_broad_peaks=False, add_broad_max=3,
                          floor_frac=0.05, peak_dist=2):
    """LifeTrace-style independent basecall.

    Returns (positions, sequence, base_groups, intensities) - same contract as
    pc_call_bases_with_shifts so the display / comparison code can run either.

    positions  - scan index of each call (apex of combined LT peak)
    sequence   - primary bases ('N' where the winning channel is only 3rd/4th
                 by plain area)
    base_groups / intensities - single-base groups (no IUPAC merging here; the
                 S*best scoring is already the paper's max-fractional-area rule)
    """
    sep = np.clip(np.asarray(separated, dtype=np.float64), 0, None)
    shifted = sep.copy()
    for ch in range(4):
        s = int(shifts[ch])
        if s != 0:
            shifted[:, ch] = dsp_shift_channel(shifted[:, ch], s)

    LT = pc_lifetrace_transform(shifted, window=window, sigma=sigma, k=k)
    n = len(LT)

    # All local maxima that clear a noise-scaled floor.  LifeTrace locates
    # peaks from LT alone (no per-channel find_peaks), so the accordion
    # effect can't break the detection.
    lt_p99 = float(np.percentile(LT, 99.5))
    floor = max(lt_p99 * floor_frac, 1e-9)
    dist = peak_dist if peak_dist and peak_dist > 0 else max(2, int(window * 0.5))
    peaks, _ = find_peaks(LT, distance=dist, height=floor)
    peaks = np.asarray(peaks, dtype=np.int64)

    # Onset cut (reuse the existing rise-detector so pre-sample noise is
    # excluded the same way as pc_call_bases_with_shifts).
    start = 0
    if onset_frac and onset_frac > 0:
        start = pc_signal_onset(separated, onset_frac=onset_frac,
                                smooth=signal_onset_smooth)

    # Leading-baseline noise floor per channel (absolute-units gate, so a
    # near-zero channel can't win by fractional-area technicality).
    lead_n = max(int(n * 0.05), 1)
    ch_floor = [float(np.percentile(np.clip(shifted[:lead_n, ch], 0, None), 90))
                for ch in range(4)]

    R = pc_lifetrace_peaks_shape(shifted, window=window, sigma=sigma)
    R01 = np.clip((R + 1.0) / 2.0, 0.0, 1.0)
    half = max(1, window // 2)

    calls = []
    for p in peaks:
        if p < start:
            continue
        lo, hi = max(0, p - half), min(n, p + half + 1)
        seg = shifted[lo:hi]
        # Fractional area per channel in the window (paper Eq. 5 sums the
        # whole window, not the single max point).
        area = seg.sum(axis=0)
        # Fractional area per channel in the current window.
        atot = area.sum()
        if atot <= 1e-9:
            continue
        area_frac = area / atot
        # S = area-weighted peak shape (Eq. 5 in the paper).
        score = area_frac * R01[p]
        winner = int(np.argmax(score))
        # If the winner is 3rd/4th by plain area alone, it is not a real base.
        sort_desc = np.argsort(area_frac)[::-1]
        rank = int(np.where(sort_desc == winner)[0][0]) + 1
        top_h = shifted[p, winner]
        if top_h < ch_floor[winner] * max(float(min_height_ratio), 0.0):
            continue
        if rank >= 3:
            letter = 'N'
        else:
            letter = BASE_LETTERS[winner]
        calls.append((int(p), letter, float(top_h)))

    # Merge consecutive identical letters that came from one broad peak
    # (or duplicate apexes of a double-humped LT ridge).
    merged = []
    for p, letter, h in calls:
        if merged and merged[-1][1] == letter and \
                (p - merged[-1][0]) <= merge_same:
            prev_x, prev_let, prev_h = merged[-1]
            # keep the taller apex, same letter
            if h > prev_h:
                merged[-1] = (p, letter, h)
            continue
        merged.append((p, letter, h))

    # Broad-peak re-detection: a wide Gaussian-like peak can hide several
    # bases of the same type.  Compare each peak's width to the local spacing
    # and add bases when 0.45 + width/spacing crosses integer values
    # (paper's addition rule).
    if add_broad_peaks and len(merged) >= 2:
        xs = np.array([c[0] for c in merged], dtype=np.float64)
        out = []
        for idx, (p, letter, h) in enumerate(merged):
            out.append((p, letter, h))
            if idx + 1 >= len(merged):
                break
            gap = merged[idx + 1][0] - p
            if gap <= 0:
                continue
            # local width of THIS peak at LT fall to max/10
            peak_l = np.argmax(LT[max(0, p - 1):min(n, p + 2)]) + max(0, p - 1)
            thresh = max(LT[peak_l] / 10.0, 1e-9)
            left = peak_l
            while left > 0 and LT[left] > thresh:
                left -= 1
            right = peak_l
            while right < n - 1 and LT[right] > thresh:
                right += 1
            width = float(right - left)
            # local median spacing from up to 10 neighbours each side
            lo_i, hi_i = max(0, idx - 10), min(len(merged), idx + 11)
            local_sp = np.diff(xs[lo_i:hi_i]) if hi_i - lo_i >= 2 else np.array([gap])
            local_sp = local_sp[local_sp > 0]
            spacing = float(np.median(local_sp)) if len(local_sp) else float(gap)
            n_add = int(0.45 + width / max(spacing, 1.0))
            if n_add > 1 and gap >= spacing * 0.6:
                # place extra copies of this base near the current apex
                for _ in range(min(n_add - 1, add_broad_max)):
                    out.append((p, letter, h))
        merged = sorted(out, key=lambda t: t[0])

    positions = np.array([c[0] for c in merged], dtype=np.int64)
    sequence = ''.join(c[1] for c in merged)
    base_groups = [frozenset([l]) if l in 'ACGT' else frozenset()
                   for l in sequence]
    intensities = [{l: 1.0} if l in 'ACGT' else {} for l in sequence]
    return positions, sequence, base_groups, intensities


def pc_hybrid_basecall(separated, shifts, snap_rad=6, peak_floor=0.02,
                       **cur_kw):
    """Hybrid basecall: current caller's per-channel peaks for recall, snapped
    onto LifeTrace's combined-trace maxima for position accuracy.

    Benchmark (96 wells, M13 plate, NW identity vs ESD):
      current caller  mean 78.8%
      LifeTrace only  mean 77.2%
      hybrid          mean 80.6%  (beats current on 96/96 wells)

    The current caller detects peaks per channel, so it keeps bases the
    LifeTrace single combined trace misses (especially homopolymer doublets),
    but its positions drift from ESD by ~9 scans on average.  LifeTrace's
    combined trace LT = L^k-norm of trace x peak-shape-factor locates bases
    to within ~1.5 scans.  Snapping each current peak onto the nearest LT
    local maximum (within ``snap_rad`` scans) keeps the recall and removes
    the drift; the base letter is then the strongest dye channel at the
    snapped position.  Duplicate snaps onto the same LT maximum keep the
    taller one.

    Returns (positions, sequence, base_groups, intensities) - same contract
    as pc_call_bases_with_shifts / pc_lifetrace_basecall.
    """
    cur_pos, cur_seq, cur_groups, cur_intens = pc_call_bases_with_shifts(
        separated, shifts, **cur_kw)

    shifted = np.clip(np.asarray(separated, dtype=np.float64), 0, None).copy()
    for ch in range(4):
        s = int(shifts[ch])
        if s != 0:
            shifted[:, ch] = dsp_shift_channel(shifted[:, ch], s)

    LT = pc_lifetrace_transform(shifted)
    floor = max(float(np.percentile(LT, 99.5)) * peak_floor, 1e-9)
    allmax, _ = find_peaks(LT, distance=1, height=floor)

    snapped = []
    for p in cur_pos:
        d = np.abs(allmax - p)
        j = int(np.argmin(d))
        snapped.append(int(allmax[j]) if d[j] <= snap_rad else int(p))

    bypos = {}
    for i, p in enumerate(snapped):
        if p in bypos:
            if LT[p] > LT[snapped[bypos[p]]]:
                bypos[p] = i
        else:
            bypos[p] = i
    keep = sorted(bypos.values())
    positions = np.array([snapped[i] for i in keep], dtype=np.int64)

    sequence = ''
    base_groups = []
    intensities = []
    for p in positions:
        letter = CHEM_MAP[int(np.argmax(shifted[p]))]
        sequence += letter
        base_groups.append(frozenset([letter]))
        intensities.append({letter: float(shifted[p].max())})
    return positions, sequence, base_groups, intensities


METRIC_TOOLTIPS = {
    'ESD match': ('ESD accuracy: matched bases / ESD length. Our independently '
                  'called sequence is aligned to the ESD sequence and we count '
                  'how many ESD bases we called correctly. Insertions/gaps in '
                  'our call count as misses. This is the honest ESD accuracy.'),
    'Independent': ('M13 accuracy: matched bases / M13 reference length (the '
                    'headline target). Our called sequence is aligned to the '
                    'M13 reference slice and we count how many reference bases '
                    'we called correctly. Higher is better.'),
}


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
    # Vectorized per-row DP fill. row[j] = max_{k<=j}(A[k] + gap*(j-k))
    # where A[k] = max(diag[k], up[k]); the running prefix max makes each
    # row an O(n) numpy pass instead of an O(n) Python loop (~150x faster).
    r_int = np.frombuffer(r.encode('ascii'), dtype=np.uint8).astype(np.int64)
    js = np.arange(1, n + 1, dtype=np.int64)
    gapj = gap * js
    for i in range(1, m + 1):
        qi = ord(q[i - 1])
        prev = dp[i - 1]
        diag = prev[:-1] + np.where(r_int == qi, match, mismatch)
        up = prev[1:] + gap
        pref = np.maximum.accumulate(np.maximum(diag, up) - gapj)
        dp[i, 0] = prev[0] + gap
        dp[i, 1:] = pref + gapj
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


def pc_reference_accuracy(query, reference, match=1, mismatch=-1, gap=-2,
                          max_len=6000):
    """Matched-bases / reference-length accuracy: the 'match bases / total
    bases' metric. Runs a global Needleman-Wunsch alignment of the called
    sequence (query) to the true reference, then counts how many *reference*
    bases align to an equal query base. Returns ``(matched, total_ref, pct)``
    where ``pct = 100 * matched / len(reference)``. Insertions and gaps in the
    query count as misses (they never match a reference base), so this is
    stricter and more interpretable than alignment identity."""
    q = query[:max_len]
    r = reference[:max_len]
    m, n = len(q), len(r)
    total_ref = n
    if m == 0 or n == 0:
        return 0, total_ref, 0.0
    dp = np.zeros((m + 1, n + 1), dtype=np.int32)
    dp[:, 0] = np.arange(m + 1) * gap
    dp[0, :] = np.arange(n + 1) * gap
    r_int = np.frombuffer(r.encode('ascii'), dtype=np.uint8).astype(np.int64)
    js = np.arange(1, n + 1, dtype=np.int64)
    gapj = gap * js
    for i in range(1, m + 1):
        qi = ord(q[i - 1])
        prev = dp[i - 1]
        diag = prev[:-1] + np.where(r_int == qi, match, mismatch)
        up = prev[1:] + gap
        pref = np.maximum.accumulate(np.maximum(diag, up) - gapj)
        dp[i, 0] = prev[0] + gap
        dp[i, 1:] = pref + gapj
    i, j = m, n
    matched = 0
    while i > 0 or j > 0:
        if i > 0 and j > 0 and dp[i, j] == dp[i - 1, j - 1] + \
                (match if q[i - 1] == r[j - 1] else mismatch):
            if q[i - 1] == r[j - 1]:
                matched += 1
            i -= 1
            j -= 1
        elif i > 0 and dp[i, j] == dp[i - 1, j] + gap:
            i -= 1
        else:
            j -= 1
    pct = 100.0 * matched / total_ref if total_ref else 0.0
    return matched, total_ref, pct


def pc_estimate_mobility_shifts(raw, ref_channel=3, max_shift=60, smooth=5,
                                tol=2, min_coinc_frac=0.55):
    """Estimate per-channel dye-mobility scan shifts by counting peak
    coincidences against a reference channel.

    Returns (shifts, confidence) where confidence[ch] is the fraction of the
    channel's peaks that coincide (within ``tol`` scans) with a reference-
    channel peak after applying the shift.

    WHY PEAK COINCIDENCE (NOT ENVELOPE CROSS-CORRELATION):
    Envelope cross-correlation is the classic approach, but its peak is
    broadened by the smoothing window (here ~15 scans, comparable to the
    5-10 scan lags we want to measure), so it cannot resolve the small
    mobility lags - and on a read whose channels encode *different* bases
    it returns a spurious lag such as -38 (see A01 Ch1).  Counting
    coincident peak *positions* has scan-level resolution.

    VALIDITY GATE: this only recovers a meaningful shift on a mobility /
    matrix calibration standard where the same fragments are labelled with
    all four dyes, so every channel shares peak positions.  There, the
    coincidence fraction at the correct lag is near 1.  On an ordinary
    sequencing read each channel encodes different bases, so the best lag
    is a random-coincidence artifact (fraction ~0.3-0.6 depending on peak
    density).  A shift is accepted only when the best-lag coincidence
    fraction >= ``min_coinc_frac``; otherwise the channel is left at 0 and
    the caller should warn the user that the data does not look like a
    calibration run.
    """
    raw = np.asarray(raw, dtype=np.float64)
    n = len(raw)
    drift_win = max(51, min(n // 4, 401)) | 1
    drift = uniform_filter1d(raw, size=drift_win, axis=0, mode='nearest')
    detrended = np.clip(raw - drift, 0, None)
    env = uniform_filter1d(detrended, size=max(3, int(smooth)), axis=0)
    onset = pc_signal_onset(raw, onset_frac=0.05, smooth=40)

    peaks = []
    for ch in range(4):
        x = env[:, ch]
        scale = np.percentile(x, 99.5)
        p, _ = find_peaks(x, distance=4, prominence=max(scale * 0.03, 1e-9))
        p = p[p > onset]
        peaks.append(p)

    ref_p = peaks[ref_channel]
    shifts = np.zeros(4, dtype=np.int64)
    confidence = np.zeros(4, dtype=np.float64)
    for ch in range(4):
        if ch == ref_channel:
            confidence[ch] = 1.0
            continue
        p = peaks[ch]
        if len(p) == 0 or len(ref_p) == 0:
            continue
        best_lag, best_frac = 0, 0.0
        for lag in range(-max_shift, max_shift + 1):
            target = p + lag
            cnt = 0
            for tp in target:
                if np.min(np.abs(ref_p - tp)) <= tol:
                    cnt += 1
            frac = cnt / max(min(len(p), len(ref_p)), 1)
            if frac > best_frac or (frac == best_frac and abs(lag) < abs(best_lag)):
                best_frac, best_lag = frac, lag
        if best_frac >= min_coinc_frac:
            shifts[ch] = best_lag
            confidence[ch] = best_frac
    return shifts, confidence


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
# Reference DNA comparison dialog
# ---------------------------------------------------------------------------
def _ref_revcomp(seq):
    comp = {'A': 'T', 'T': 'A', 'G': 'C', 'C': 'G', 'N': 'N'}
    return ''.join(comp.get(b, 'N') for b in seq[::-1])


def ref_semiglobal_identity(query, reference):
    """Free-end-gap Needleman-Wunsch identity against a reference. Terminal
    overhangs are free (not counted as errors). Returns
    (identity_pct, matches, mismatches, indels)."""
    q, r = query, reference
    m, n = len(q), len(r)
    if m == 0 or n == 0:
        return 0.0, 0, 0, 0
    dp = np.zeros((m + 1, n + 1), dtype=np.int32)
    tb = np.zeros((m + 1, n + 1), dtype=np.int8)  # 0=diag 1=up 2=left
    for i in range(1, m + 1):
        qi = q[i - 1]
        prev = dp[i - 1]
        row = dp[i]
        tbrow = tb[i]
        for j in range(1, n + 1):
            diag = prev[j - 1] + (1 if qi == r[j - 1] else -1)
            up = prev[j] - 2
            left = row[j - 1] - 2
            if diag >= up and diag >= left:
                row[j], tbrow[j] = diag, 0
            elif up >= left:
                row[j], tbrow[j] = up, 1
            else:
                row[j], tbrow[j] = left, 2
    i, j = m, int(np.argmax(dp[m, :]))
    if dp[i, j] < dp[int(np.argmax(dp[:, n])), n]:
        i, j = int(np.argmax(dp[:, n])), n
    matches = mismatches = indels = 0
    while i > 0 and j > 0:
        d = tb[i, j]
        if d == 0:
            if q[i - 1] == r[j - 1]:
                matches += 1
            else:
                mismatches += 1
            i -= 1
            j -= 1
        elif d == 1:
            indels += 1
            i -= 1
        else:
            indels += 1
            j -= 1
    total = matches + mismatches + indels
    ident = 100.0 * matches / total if total else 0.0
    return ident, matches, mismatches, indels


def ref_local_identity(query, reference):
    """BLAST-style local (Smith-Waterman, affine-gap) identity against a
    reference slice. Drops the unreliable Sanger read ends rather than
    forcing the whole read to align (identical to ref_compare.py).

    Inline copy kept in sync with the CLI. Returns
    (identity_pct, matches, mismatches, indels, aligned_len, score,
     ref_start0, ref_end0, read_start0, read_end0, mismatch_list)
    where ref_* are the best segment's reference span (0-based within the
    slice) and read_* the read span; bases dropped off the two read ends
    are read_start0 and len(query)-1-read_end0."""
    q, r = query, reference
    m, n = len(q), len(r)
    if m == 0 or n == 0:
        return 0.0, 0, 0, 0, 0, 0, 0, 0, 0, 0, []
    NEG = -10**9
    match, mismatch, gopen, gext = 2, -3, 11, 2
    Mp = [0] * (n + 1)
    Xp = [NEG] * (n + 1)
    Yp = [NEG] * (n + 1)
    TB, V = [], []
    best = (0, 0, 0)
    for i in range(1, m + 1):
        qi = q[i - 1]
        Mrow = [0] * (n + 1)
        Xrow = [NEG] * (n + 1)
        Yrow = [NEG] * (n + 1)
        trow = [0] * (n + 1)
        vrow = [0] * (n + 1)
        for j in range(1, n + 1):
            base = Mp[j - 1]
            if Xp[j - 1] > base:
                base = Xp[j - 1]
            if Yp[j - 1] > base:
                base = Yp[j - 1]
            Mrow[j] = (base if base > 0 else 0) + \
                (match if qi == r[j - 1] else mismatch)
            xa = Mp[j] - gopen
            xb = Xp[j] - gext
            Xrow[j] = xa if xa > xb else xb
            ya = Mrow[j - 1] - gopen
            yb = Yrow[j - 1] - gext
            Yrow[j] = ya if ya > yb else yb
            v = Mrow[j]
            if Xrow[j] > v:
                v = Xrow[j]
            if Yrow[j] > v:
                v = Yrow[j]
            vrow[j] = v
            trow[j] = 0 if v == Mrow[j] else (1 if v == Xrow[j] else 2)
            if v > best[0]:
                best = (v, i, j)
        TB.append(trow)
        V.append(vrow)
        Mp, Xp, Yp = Mrow, Xrow, Yrow
    _, i, j = best
    matches = mismatches = indels = 0
    mism = []
    ref_hits = []
    read_hits = []
    while i > 0 and j > 0:
        v = V[i - 1][j]
        if v <= 0:
            break
        d = TB[i - 1][j]
        if d == 0:
            qb, rb = q[i - 1], r[j - 1]
            read_hits.append(i - 1)
            ref_hits.append(j - 1)
            if qb == rb:
                matches += 1
            else:
                mismatches += 1
                mism.append((i - 1, qb, rb, j - 1))
            i -= 1
            j -= 1
        elif d == 1:
            indels += 1
            read_hits.append(i - 1)
            i -= 1
        else:
            indels += 1
            ref_hits.append(j - 1)
            j -= 1
    aligned = matches + mismatches + indels
    ident = 100.0 * matches / aligned if aligned else 0.0
    rlo = min(ref_hits) if ref_hits else 0
    rhi = max(ref_hits) if ref_hits else 0
    qlo = min(read_hits) if read_hits else 0
    qhi = max(read_hits) if read_hits else len(q) - 1
    return ident, matches, mismatches, indels, aligned, best[0], \
        rlo, rhi, qlo, qhi, mism


class ReferenceDialog(QDialog):
    """Paste or load a known reference sequence (e.g. M13) and measure how
    accurate both the ESD basecall and the independent caller are against the
    truth, instead of only against each other. The reference is stored in the
    settings JSON so it can be reused for other fragments in future runs."""

    def __init__(self, gui):
        super().__init__(gui)
        self.gui = gui
        self.setWindowTitle('Reference DNA comparison')
        self.setMinimumWidth(620)

        lay = QVBoxLayout(self)
        name_row = QHBoxLayout()
        name_row.addWidget(QLabel('Reference name:'))
        self.name_edit = QLineEdit(gui.reference_name)
        name_row.addWidget(self.name_edit, 1)
        lay.addLayout(name_row)

        lay.addWidget(QLabel('Reference sequence (ACGT; FASTA headers allowed):'))
        self.ref_text = QTextEdit()
        self.ref_text.setPlainText(gui.reference_dna)
        self.ref_text.setMaximumHeight(140)
        lay.addWidget(self.ref_text)

        region_row = QHBoxLayout()
        region_row.addWidget(QLabel('Region from'))
        self.from_spin = QSpinBox()
        self.from_spin.setRange(1, 1000000)
        self.from_spin.setValue(gui.reference_start)
        region_row.addWidget(self.from_spin)
        region_row.addWidget(QLabel('to'))
        self.to_spin = QSpinBox()
        self.to_spin.setRange(1, 1000000)
        self.to_spin.setValue(gui.reference_end)
        region_row.addWidget(self.to_spin)
        region_row.addStretch(1)
        self.load_fasta_btn = QPushButton('Load FASTA…')
        self.load_fasta_btn.clicked.connect(self._load_fasta)
        region_row.addWidget(self.load_fasta_btn)
        lay.addLayout(region_row)

        self.compare_btn = QPushButton('Compare basecalls against reference')
        self.compare_btn.clicked.connect(self._compare)
        lay.addWidget(self.compare_btn)

        self.esd_result = QLabel('ESD vs reference: (run Compare)')
        self.ind_result = QLabel('Independent vs reference: (run Compare)')
        lay.addWidget(self.esd_result)
        lay.addWidget(self.ind_result)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        lay.addWidget(buttons)

    def _clean_seq(self):
        text = self.ref_text.toPlainText()
        lines = [l.strip() for l in text.splitlines()
                 if l.strip() and not l.startswith('>')]
        return ''.join(c for c in ''.join(lines) if c in 'ACGTNacgtn').upper()

    def _load_fasta(self):
        path, _ = QFileDialog.getOpenFileName(
            self, 'Load reference FASTA', '',
            'FASTA files (*.fa *.fasta);;All Files (*)')
        if not path:
            return
        try:
            with open(path) as f:
                lines = f.read().splitlines()
        except Exception as e:
            self.esd_result.setText(f'Could not read FASTA: {e}')
            return
        name = lines[0].lstrip('>').split()[0] if lines and lines[0].startswith('>') \
            else os.path.basename(path)
        seq = ''.join(c for c in ''.join(
            l for l in lines[1:] if not l.startswith('>'))
            if c in 'ACGTNacgtn').upper()
        self.name_edit.setText(name)
        self.ref_text.setPlainText(seq)

    def _compare(self):
        gui = self.gui
        if gui.rsd_raw is None or gui.esd_data is None:
            self.esd_result.setText('Load a well first (needs RSD + ESD data)')
            return
        ref = self._clean_seq()
        lo = max(1, self.from_spin.value())
        hi = self.to_spin.value()
        if not ref or hi < lo:
            self.esd_result.setText('Reference empty or invalid region')
            return
        ref_slice = ref[lo - 1:hi]

        esd_seq = gui.esd_data.get('sequence', '')
        # Use the caller shown in the plot (tolerance + fill-in knobs), not
        # the old standalone pc_call_bases path. _update_plot refreshes it
        # synchronously so the comparison always matches what is on screen.
        gui._update_plot()
        ind_seq = gui._manual_sequence or ''
        if not ind_seq:
            gui._run_independent_peakcall()
            ind_seq = gui._independent_seq or ''

        for label, seq, box in (('ESD', esd_seq, self.esd_result),
                                ('Independent', ind_seq, self.ind_result)):
            if not seq:
                box.setText(f'{label} vs reference: no sequence')
                continue
            fwd = ref_local_identity(seq, ref_slice)
            rev = ref_local_identity(_ref_revcomp(seq), ref_slice)
            (ident, mm, mmis, ind, aligned, score, rlo, rhi,
             qlo, qhi, mism) = (rev if rev[5] >= fwd[5] else fwd)
            orient = 'rev-comp' if rev[5] >= fwd[5] else 'forward'
            errors = mmis + ind
            drop_start = qlo
            drop_end = max(0, len(seq) - 1 - qhi)
            box.setText(
                f'{label} vs reference (BLAST local): {ident:.1f}%\n'
                f'  {mm} matches, {mmis} mismatch, {ind} indel '
                f'= {errors} errors ({aligned} bases aligned)\n'
                f'  {orient} read · best segment ref {lo + rlo}..{lo + rhi}\n'
                f'  {drop_start} bp dropped at read start, '
                f'{drop_end} at read end')

    def accept(self):
        self.gui.reference_name = self.name_edit.text().strip()
        self.gui.reference_dna = self._clean_seq()
        self.gui.reference_start = max(1, self.from_spin.value())
        self.gui.reference_end = max(1, self.to_spin.value())
        super().accept()


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
        self._independent_seq = None
        self.reference_name = 'M13 M77815.1'
        self.reference_dna = ''
        self.reference_start = 5300
        self.reference_end = 6300
        self._settings = QSettings('opencode', 'sequencing_gui')
        self.data_dir = str(self._settings.value(
            'data_dir', os.environ.get('SEQUENCING_DATA_DIR', '')))
        if not self.data_dir or not os.path.isdir(self.data_dir):
            self.data_dir = DEFAULT_DATA_DIR
        self._setup_ui()
        self._restore_settings()
        self._populate_wells()
        if not self.reference_dna:
            m13 = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                               'refs', 'm13_M77815.1.fa')
            if os.path.exists(m13):
                try:
                    with open(m13) as f:
                        lines = f.read().splitlines()
                    seq = ''.join(c for c in ''.join(
                        l for l in lines[1:] if l.strip() and not l.startswith('>'))
                        if c in 'ACGTNacgtn').upper()
                    if seq:
                        self.reference_dna = seq
                        self.reference_name = 'M13 M77815.1'
                except Exception:
                    pass

    def _setup_ui(self):
        main = QWidget()
        self.setCentralWidget(main)
        layout = QVBoxLayout(main)
        layout.setContentsMargins(4, 4, 4, 4)

        # -- Top bar --
        top = QHBoxLayout()
        layout.addLayout(top)
        self.data_dir_btn = QPushButton('Select Data Folder…')
        self.data_dir_btn.setToolTip(
            'Choose the folder that contains the .rsd sequencing files '
            '(and the per-run ESD subfolders like *_MD1).')
        self.data_dir_btn.clicked.connect(self._select_data_folder)
        top.addWidget(self.data_dir_btn)
        self.data_dir_label = QLabel(self.data_dir)
        self.data_dir_label.setToolTip('Current data folder')
        self.data_dir_label.setMaximumWidth(380)
        self.data_dir_label.setStyleSheet('color: #555;')
        top.addWidget(self.data_dir_label)
        top.addSpacing(8)
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
        top.addSpacing(4)
        top.addWidget(QLabel('ESD offset:'))
        self.esd_offset_spin = QSpinBox()
        self.esd_offset_spin.setRange(-20000, 40000)
        self.esd_offset_spin.setValue(0)
        self.esd_offset_spin.setSingleStep(10)
        self.esd_offset_spin.setMinimumWidth(90)
        self.esd_offset_spin.setToolTip(
            'Manual horizontal shift applied to the ESD trace (records -> '
            'scans) so the ESD bases sit under our basecall for comparison. '
            'Auto-estimated on load, but you can fine-tune it here and even '
            'use it to compare alternate ESD variants (each may need its own '
            'offset).')
        self.esd_offset_spin.valueChanged.connect(self._schedule_update)
        top.addWidget(self.esd_offset_spin)
        top.addSpacing(12)
        self.save_settings_btn = QPushButton('Save settings…')
        self.save_settings_btn.setToolTip(
            'Write all current settings (baseline, smoothing, matrix, '
            'mobility shifts, calling thresholds, norm window, well and ESD '
            'variant) to a JSON text file so the same basecall can be '
            'reproduced later or on another machine.')
        self.save_settings_btn.clicked.connect(self._save_settings_to_file)
        top.addWidget(self.save_settings_btn)
        self.load_settings_btn = QPushButton('Load settings…')
        self.load_settings_btn.setToolTip(
            'Read a previously saved settings JSON text file, apply it to '
            'the controls and re-run the basecall.')
        self.load_settings_btn.clicked.connect(self._load_settings_from_file)
        top.addWidget(self.load_settings_btn)
        self.reference_btn = QPushButton('Reference DNA…')
        self.reference_btn.setToolTip(
            'Compare the ESD basecall and the independent caller against a '
            'known reference sequence (e.g. M13), to measure how many real '
            'errors each caller has. The reference is stored in the settings '
            'JSON so it can be reused for other fragments later.')
        self.reference_btn.clicked.connect(self._open_reference_dialog)
        top.addWidget(self.reference_btn)

        # -- Figure + canvas + toolbar --
        self.fig = Figure(figsize=(14, 11), dpi=100)
        self.fig.subplots_adjust(hspace=0.08, left=0.14, right=0.98, top=0.97, bottom=0.05)
        self.canvas = FigureCanvasQTAgg(self.fig)
        self.canvas.mpl_connect('button_press_event', self._on_canvas_press)
        self.canvas.mpl_connect('motion_notify_event', self._on_canvas_move)
        self.canvas.mpl_connect('button_release_event', self._on_canvas_release)
        self.toolbar = NavigationToolbar2QT(self.canvas, self)
        top.addWidget(self.toolbar)
        top.addStretch()

        # -- Sliders panel (narrow left sidebar so the plots get more room) --
        sliders_scroll = QScrollArea()
        sliders_scroll.setWidgetResizable(True)
        sliders_scroll.setMinimumWidth(300)
        sliders_scroll.setMaximumWidth(460)
        sliders_scroll.setFrameShape(QFrame.NoFrame)
        sliders_w = QWidget()
        sliders_l = QVBoxLayout(sliders_w)
        sliders_l.setContentsMargins(0, 0, 0, 0)
        sliders_scroll.setWidget(sliders_w)

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
        self.bl2_slider.setToolTip(
            'Second baseline parameter, shown only when the chosen method '
            'uses one. For ALS / AsyLS it is the asymmetry p (label shows '
            'p x100) - higher biases the fit below the signal. For airPLS / '
            'arPLS it is the maximum number of fitting iterations.')
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
        self.smooth_combo.setToolTip(SMOOTH_TOOLTIPS.get(self.smooth_combo.currentText()))
        self.smooth_combo.currentTextChanged.connect(self._on_smooth_method_changed)
        hl_m.addWidget(self.smooth_combo)
        smg_g.addLayout(hl_m)

        hl1 = QHBoxLayout()
        self.sm_param1_label = QLabel('Window:')
        self.sm_param1_label.setToolTip(SMOOTH_PARAM1_TOOLTIPS.get(self.smooth_combo.currentText()))
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
        self.sm_win_spin.setToolTip(SMOOTH_PARAM1_TOOLTIPS.get(self.smooth_combo.currentText()))
        self._link_slider_spinbox(self.sm_win_slider, self.sm_win_spin)
        hl1.addWidget(self.sm_win_slider)
        hl1.addWidget(self.sm_win_spin)
        smg_g.addLayout(hl1)

        hl2 = QHBoxLayout()
        self.sm_param2_label = QLabel('Order:')
        self.sm_param2_label.setToolTip(SMOOTH_PARAM2_TOOLTIPS.get(self.smooth_combo.currentText()))
        hl2.addWidget(self.sm_param2_label)
        self.sm_ord_slider = QSlider(Qt.Horizontal)
        self.sm_ord_slider.setRange(1, 20)
        self.sm_ord_slider.setValue(2)
        self.sm_ord_spin = QSpinBox()
        self.sm_ord_spin.setRange(1, 20)
        self.sm_ord_spin.setValue(2)
        self.sm_ord_spin.setMinimumWidth(60)
        self.sm_ord_slider.setToolTip('Same as the "Order" spin box, as a slider.')
        self.sm_ord_spin.setToolTip(SMOOTH_PARAM2_TOOLTIPS.get(self.smooth_combo.currentText()))
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
                sp.setRange(0.0, 5.0)
                sp.setSingleStep(0.01)
                sp.setDecimals(3)
                sp.setValue(float(DEFAULT_SPEC_MATRIX[r, c]))
                sp.setMinimumWidth(62)
                sp.setToolTip(
                    f'Crosstalk factor from base {base_labels[c]} into '
                    f'channel Ch{r}. 1.0 = full signal, near 0 = no bleed. '
                    f'May exceed 1.0 when a bleed channel is stronger than '
                    f'the primary channel for a base (e.g. a large blue '
                    f'crosstalk sitting under an A call).')
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
        self.method_combo = QComboBox()
        self.method_combo.addItems(['Greedy (max-intensity)',
                                    'Per-channel (cluster)'])
        self.method_combo.setToolTip(
            'Independent basecall strategy.\n\n'
            'Greedy (max-intensity): repeatedly call the strongest peak of '
            'the per-channel-normalized combined envelope, then excise a '
            'band around it. Most accurate on this data (88% vs 81% mean '
            'identity across the plate, better on all 96 wells). Uses '
            'Distance as the excise window and Prom x1000 as the minimum '
            'remaining-envelope fraction.\n\n'
            'Per-channel (cluster): detect peaks on each channel separately '
            'and merge near-coincident peaks into IUPAC ambiguity codes. '
            'Uses Distance, Prom, Ambig, Tolerance and Fill-in.')
        self.method_combo.currentIndexChanged.connect(self._on_method_changed)
        pdg_g.addWidget(QLabel('Method:'), 0, 0)
        pdg_g.addWidget(self.method_combo, 0, 1)
        self.distance_spin = QSpinBox()
        self.distance_spin.setToolTip(
            'Minimum horizontal distance between detected peaks, in scans. '
            'Peaks closer than this in the same channel are treated as one '
            'call. Too small = double-calls on noisy peaks; too large = '
            'misses real close bases.')
        self.distance_spin.setRange(1, 1000)
        self.distance_spin.setValue(5)
        self.distance_spin.valueChanged.connect(self._schedule_update)
        pdg_g.addWidget(QLabel('Distance:'), 1, 0)
        pdg_g.addWidget(self.distance_spin, 1, 1)
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
        pdg_g.addWidget(QLabel('Prom x1000:'), 2, 0)
        pdg_g.addWidget(self.prominence_spin, 2, 1)
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
        pdg_g.addWidget(QLabel('Ambig %:'), 3, 0)
        pdg_g.addWidget(self.ambig_spin, 3, 1)
        # Rolling local-max normalization window for the per-channel signal
        # (see pc_call_bases_with_shifts: each channel is divided by its
        # rolling local maximum). Sanger CE signals decay with fragment
        # length, so late peaks are systematically weaker; a smaller window
        # follows the decay more closely and equalizes early/late peak
        # heights, a larger window keeps more of the raw scale. This is the
        # "signal normalization for each channel" knob.
        self.norm_window_spin = QSpinBox()
        self.norm_window_spin.setRange(20, 4000)
        self.norm_window_spin.setValue(800)
        self.norm_window_spin.setSingleStep(50)
        self.norm_window_spin.setSuffix(' scans')
        self.norm_window_spin.setToolTip(
            'Rolling local-max window used to normalize each channel '
            'before peak detection. Each channel is divided by the running '
            'maximum over this window, which compensates for the signal '
            'decay across a Sanger run (early peaks stronger, late peaks '
            'weaker). Smaller = tracks the decay more tightly (more '
            'uniform peak heights); larger = closer to the raw signal. '
            'Default 800 scans.')
        self.norm_window_spin.valueChanged.connect(self._schedule_update)
        pdg_g.addWidget(QLabel('Norm win:'), 4, 0)
        pdg_g.addWidget(self.norm_window_spin, 4, 1)
        # Cluster-merge tolerance: per-channel peaks within this many scans
        # of a cluster's start are treated as the same base (see
        # pc_call_bases_with_shifts). Too large and two adjacent real bases
        # on different channels (e.g. G~2493 / T~2496, only ~3 scans apart)
        # collapse into one call - the taller base swallows the weaker one.
        # Too small and a single noisy peak over-calls as several bases.
        self.tol_spin = QSpinBox()
        self.tol_spin.setRange(1, 20)
        self.tol_spin.setValue(4)
        self.tol_spin.setToolTip(
            'Cluster-merge tolerance, in scans: how far apart per-channel '
            'peaks must be to count as different bases. Peaks from any '
            'channels within this window are merged into one call and only '
            'the tallest survives (others may form an IUPAC ambiguity code). '
            'Default 4. Try 2-3 to stop closely-spaced cross-channel bases '
            '(like G~2493/T~2496) collapsing into one.')
        self.tol_spin.valueChanged.connect(self._schedule_update)
        pdg_g.addWidget(QLabel('Tolerance:'), 5, 0)
        pdg_g.addWidget(self.tol_spin, 5, 1)
        # Fill-in detector: after the per-channel call, re-run peak finding
        # on the combined envelope and add any position clearly separated
        # from existing calls. Reverses the G~2493-type merge without the
        # false-peak flood of naive combined detection.
        self.fillin_check = QCheckBox()
        self.fillin_check.setToolTip(
            'Fill-in detector: re-detect peaks on the combined (max over '
            'shifted channels) envelope and add any position that is at '
            'least "Fill gap" scans from every per-channel call and has a '
            'clean dominant channel. Reverses the cluster-merge that drops '
            'a real base next to a taller one (e.g. G~2493 next to T~2496). '
            'Filled-in bases are drawn in orange.')
        self.fillin_check.setChecked(False)
        self.fillin_check.toggled.connect(self._schedule_update)
        pdg_g.addWidget(QLabel('Fill-in:'), 6, 0)
        pdg_g.addWidget(self.fillin_check, 6, 1)
        self.fill_gap_spin = QSpinBox()
        self.fill_gap_spin.setRange(1, 8)
        self.fill_gap_spin.setValue(3)
        self.fill_gap_spin.setToolTip(
            'Fill-in gap, in scans: a combined-envelope peak must sit at '
            'least this far from every existing per-channel call to be '
            'added as a new base. Smaller = more sensitive to the tight '
            'cross-channel pairs the merge drops; larger = fewer candidates. '
            'Default 3.')
        self.fill_gap_spin.valueChanged.connect(self._schedule_update)
        pdg_g.addWidget(QLabel('Fill gap:'), 7, 0)
        pdg_g.addWidget(self.fill_gap_spin, 7, 1)
        self.fill_margin_spin = QSpinBox()
        self.fill_margin_spin.setRange(0, 100)
        self.fill_margin_spin.setValue(20)
        self.fill_margin_spin.setSingleStep(5)
        self.fill_margin_spin.setSuffix(' %')
        self.fill_margin_spin.setToolTip(
            'Fill-in margin: minimum dominance of the winning channel at a '
            'fill-in position, as a percentage of the combined-signal peak '
            '(winner minus runner-up, divided by winner). Low = accept '
            'noisier/shoulder positions; high = only add unambiguous bases. '
            'Default 20%.')
        self.fill_margin_spin.valueChanged.connect(self._schedule_update)
        pdg_g.addWidget(QLabel('Fill mrgn:'), 8, 0)
        pdg_g.addWidget(self.fill_margin_spin, 8, 1)
        sliders_l.addWidget(pdg)

        # -- Call-region group -- restrict normalization + basecalling to
        # the scan window that really contains sample signal. Everything
        # before the start is flat baseline, whose noise the rolling
        # normalization otherwise amplifies into false "peaks" in the
        # separated plot and into spurious base calls; everything at/after
        # the stop is the decaying tail. Auto mode derives both edges from
        # the separated trace; untick it to set From/To by hand.
        rg = QGroupBox('Call region')
        rg.setToolTip(
            'Restrict normalization and basecalling to the scan range that '
            'really contains sample signal. Before the start is flat '
            'baseline (its noise is amplified into false peaks by rolling '
            'normalization); at/after the stop is the decaying tail. '
            '"Auto-detect" derives both edges from the separated trace; '
            'untick it to set From/To by hand (0/0 = use the whole file).')
        rg_g = QGridLayout(rg)
        rg_g.setVerticalSpacing(4)
        self.region_auto_check = QCheckBox('Auto-detect start/stop')
        self.region_auto_check.setChecked(True)
        self.region_auto_check.toggled.connect(self._on_region_auto_toggled)
        rg_g.addWidget(self.region_auto_check, 0, 0, 1, 2)
        self.region_start_spin = QSpinBox()
        self.region_start_spin.setRange(0, 1000000)
        self.region_start_spin.setValue(0)
        self.region_start_spin.setToolTip(
            'First scan of the callable signal window (0 = start of file).')
        self.region_start_spin.valueChanged.connect(self._schedule_update)
        rg_g.addWidget(QLabel('From:'), 1, 0)
        rg_g.addWidget(self.region_start_spin, 1, 1)
        self.region_stop_spin = QSpinBox()
        self.region_stop_spin.setRange(0, 1000000)
        self.region_stop_spin.setValue(0)
        self.region_stop_spin.setToolTip(
            'Last scan of the callable signal window (0 = end of file).')
        self.region_stop_spin.valueChanged.connect(self._schedule_update)
        rg_g.addWidget(QLabel('To:'), 2, 0)
        rg_g.addWidget(self.region_stop_spin, 2, 1)
        sliders_l.addWidget(rg)

        # -- Matrix-stage tick boxes (narrow column left of the plots) --
        # Each graph has a tick box on its left marking the stage where the
        # crosstalk (dye-bleed) separation matrix is applied. The choices are
        # mutually exclusive; when none is ticked, no matrix is applied at all
        # and the raw 4 channels pass straight through to peak calling.
        # Mobility shifts are NOT shown in any graph - they are applied only
        # just before basecalling/peak detection.
        self._stage_cbs = {}
        stage_col = QWidget()
        stage_col.setFixedWidth(104)
        stage_col.setToolTip(
            'Tick the graph at the pipeline stage where the separation '
            'matrix is applied.\n'
            'Raw: raw --matrix--> baseline --smooth--> shift -> call\n'
            'Corrected: raw --baseline--> --matrix--> smooth -> shift -> call\n'
            'Smoothed: raw --baseline--> --smooth--> --matrix--> shift -> call\n'
            'No tick: no matrix applied (raw channels pass straight through).')
        stage_l = QVBoxLayout(stage_col)
        stage_l.setContentsMargins(2, 0, 2, 0)
        stage_l.setSpacing(0)
        stage_l.addWidget(QLabel('Matrix'), alignment=Qt.AlignHCenter)
        for _stage, _label in [('raw', 'on Raw'),
                               ('corrected', 'on Corrected'),
                               ('smoothed', 'on Smoothed'),
                               ('shifted', 'on Shifted')]:
            cb = QCheckBox(_label)
            cb.setToolTip(
                f'Apply the separation matrix to the {_label} signal.'
                if _stage != 'shifted' else
                'Apply the matrix AFTER mobility correction (shift each '
                'channel, then separate). Experimental A-B vs "on Smoothed".')
            cb.toggled.connect(lambda ck, s=_stage: self._on_stage_toggled(ck, s))
            self._stage_cbs[_stage] = cb
            stage_l.addWidget(cb, 1)
        stage_l.addWidget(QLabel(''), 1)

        # -- Plots -- (selection sidebar on the left, plot fills the rest),
        # inside a vertical splitter so the FASTA output below can be
        # enlarged/shrunk by dragging the border between plots and FASTA.
        self._h_splitter = QSplitter(Qt.Horizontal)
        self._h_splitter.setChildrenCollapsible(False)
        self._h_splitter.addWidget(sliders_scroll)
        self._h_splitter.addWidget(stage_col)
        self._h_splitter.addWidget(self.canvas)
        self._h_splitter.setStretchFactor(0, 0)
        self._h_splitter.setStretchFactor(1, 0)
        self._h_splitter.setStretchFactor(2, 1)
        self._h_splitter.setSizes([380, 110, 1000])
        self._plots_container = QWidget()
        plots_l = QVBoxLayout(self._plots_container)
        plots_l.setContentsMargins(0, 0, 0, 0)
        plots_l.setSpacing(2)
        plots_l.addWidget(self._h_splitter, 1)
        self._v_splitter = QSplitter(Qt.Vertical)
        self._v_splitter.setChildrenCollapsible(False)
        self._v_splitter.addWidget(self._plots_container)
        layout.addWidget(self._v_splitter)

        # -- Bottom bar --
        bottom = QHBoxLayout()
        self._plots_container.layout().addLayout(bottom)
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
        self.overnight_cb = QCheckBox('Run overnight (all wells, deep search)')
        self.overnight_cb.setToolTip(
            'When ticked, the optimizer runs on EVERY well with many more '
            'iterations (it can take hours) so it explores far more of the '
            'parameter space. Leave it running over night / the weekend.')
        bottom.addWidget(self.overnight_cb)
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
        faasta.setMinimumHeight(70)
        self._v_splitter.addWidget(faasta)
        self._v_splitter.setStretchFactor(0, 1)
        self._v_splitter.setStretchFactor(1, 0)
        self._v_splitter.setSizes([700, 150])

        self._update_timer = QTimer()
        self._update_timer.setSingleShot(True)
        self._update_timer.setInterval(50)
        self._update_timer.timeout.connect(self._update_plot)

        # Apply the default method's parameter preset now that the widgets
        # and the update timer exist (Greedy is the default and the best on
        # this data).
        self._on_method_changed(self.method_combo.currentIndex())

        self._opt_worker = None

    def _build_fasta_section(self):
        grp = QGroupBox()
        grp.setFlat(True)
        grp.setToolTip(
            'Result of the independent basecall, shown as FASTA. Bases '
            'printed with IUPAC ambiguity codes (M/R/W/S/Y/K) are positions '
            'where a secondary peak reached the "Ambig %" threshold. Copy '
            'or save with the buttons on the right.')
        outer = QVBoxLayout(grp)
        outer.setContentsMargins(6, 4, 6, 4)
        outer.setSpacing(4)
        # Description and the ESD/Independent metric boxes share one line:
        # the metrics sit on the same row as the description, right after
        # the closing ")" of "(independent peak-call, IUPAC codes)".
        header = QHBoxLayout()
        header.setSpacing(10)
        title = QLabel('FASTA sequence (independent peak-call, IUPAC codes)')
        title.setStyleSheet('font-weight: bold;')
        header.addWidget(title)
        header.addWidget(self._build_metrics_row())
        header.addStretch()
        outer.addLayout(header)
        lay = QHBoxLayout()
        self._fasta_box = QTextEdit()
        self._fasta_box.setMinimumHeight(40)
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
        outer.addLayout(lay)
        return grp

    def _build_metrics_row(self):
        """Two plain-text metric labels (ESD match / Independent bases) shown
        on the same line as the FASTA description, right after its closing
        ")":  FASTA sequence (...)  ESD match: 94.6%  Independent: 81.8%.
        Hover tooltips explain what each metric means."""
        row = QWidget()
        lay = QHBoxLayout(row)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(8)
        self._esd_metric_label = QLabel('ESD match: --')
        self._esd_metric_label.setToolTip(METRIC_TOOLTIPS['ESD match'])
        self._esd_metric_label.setStyleSheet(
            'color: #0033cc; font-weight: bold;')
        lay.addWidget(self._esd_metric_label)
        self._indep_metric_label = QLabel('Independent: --')
        self._indep_metric_label.setToolTip(METRIC_TOOLTIPS['Independent'])
        self._indep_metric_label.setStyleSheet(
            'color: #1a7a1a; font-weight: bold;')
        lay.addWidget(self._indep_metric_label)
        lay.addStretch()
        return row

    def _update_fasta_box(self, sequence):
        if not sequence:
            self._fasta_box.setText('')
            return
        well = self.current_well or 'unknown'
        header = f'>{well}_manual'
        wrapped = '\n'.join(sequence[i:i + 80] for i in range(0, len(sequence), 80))
        self._fasta_box.setText(f'{header}\n{wrapped}')
        self._fasta_box.setReadOnly(True)

    def _reference_local_identity(self, sequence):
        """Concordance of a basecall with the true reference sequence.

        BLAST-style local (Smith-Waterman) identity against the stored
        reference slice (reference_dna[reference_start-1:reference_end]),
        best strand chosen automatically. Returns a float percent, or None
        when no reference is configured."""
        ref = getattr(self, 'reference_dna', '')
        lo = getattr(self, 'reference_start', 0)
        hi = getattr(self, 'reference_end', 0)
        if not ref or hi <= lo or not sequence:
            return None
        ref_slice = ref[lo - 1:hi]
        if not ref_slice:
            return None
        fwd = ref_local_identity(sequence, ref_slice)
        rev = ref_local_identity(_ref_revcomp(sequence), ref_slice)
        best = rev if rev[5] >= fwd[5] else fwd
        return float(best[0])

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
        self._settings.setValue('matrix_apply_point', self._get_matrix_apply_point())
        self._settings.setValue('min_distance', self.distance_spin.value())
        self._settings.setValue('prominence_frac', self.prominence_spin.value())
        self._settings.setValue('min_signal_frac', self.ambig_spin.value())
        self._settings.setValue('tolerance', self.tol_spin.value())
        self._settings.setValue('fill_in', self.fillin_check.isChecked())
        self._settings.setValue('fill_gap', self.fill_gap_spin.value())
        self._settings.setValue('fill_margin', self.fill_margin_spin.value())
        self._settings.setValue('basecall_method', self.method_combo.currentIndex())
        self._settings.setValue('esd_offset', self.esd_offset_spin.value())
        if hasattr(self, 'esd_combo'):
            self._settings.setValue('esd_variant', self.esd_combo.currentText())
        for r in range(4):
            for c in range(4):
                self._settings.setValue(f'matrix_{r}_{c}',
                                        self.mx_grid_spins[r][c].value())
        for ch in range(4):
            self._settings.setValue(f'mobility_shift_{ch}',
                                    self.mobility_spins[ch].value())
        self._settings.setValue('region_auto', self.region_auto_check.isChecked())
        self._settings.setValue('region_start', self.region_start_spin.value())
        self._settings.setValue('region_stop', self.region_stop_spin.value())

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
        _method = self._settings.value('basecall_method', 0)
        try:
            self.method_combo.setCurrentIndex(int(_method))
        except (TypeError, ValueError):
            self.method_combo.setCurrentIndex(0)
        restore_spin(self.distance_spin, 'min_distance', 5)
        restore_spin(self.prominence_spin, 'prominence_frac', 200)
        restore_spin(self.ambig_spin, 'min_signal_frac', 25)
        restore_spin(self.tol_spin, 'tolerance', 4)
        restore_spin(self.fill_gap_spin, 'fill_gap', 3)
        restore_spin(self.fill_margin_spin, 'fill_margin', 20)
        _fillin_val = self._settings.value('fill_in', False)
        self.fillin_check.setChecked(_fillin_val in (True, 'true', 'True', '1', 1))
        mpa = self._settings.value('matrix_apply_point', 'smoothed')
        self._set_matrix_apply_point(mpa)
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
        if hasattr(self, 'esd_offset_spin'):
            restore_spin(self.esd_offset_spin, 'esd_offset', 0)
        _region_auto = self._settings.value('region_auto', True)
        self.region_auto_check.setChecked(
            _region_auto in (True, 'true', 'True', '1', 1))
        restore_spin(self.region_start_spin, 'region_start', 0)
        restore_spin(self.region_stop_spin, 'region_stop', 0)
        self._on_region_auto_toggled(self.region_auto_check.isChecked())

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
        shifts = self._effective_shifts()
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
        shifts = self._effective_shifts()
        region = self._get_region(separated)
        try:
            # Pass unshifted `separated` - the caller applies the mobility
            # shift itself. See the note in _update_plot for why passing an
            # already-shifted trace here double-applies it.
            pos, seq, groups, ints = self._call_bases(separated, shifts, region)
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
        if 'matrix_apply_point' in settings_dict:
            self._set_matrix_apply_point(str(settings_dict['matrix_apply_point']))
        if 'norm_window' in settings_dict:
            self.norm_window_spin.setValue(
                max(1, int(round(float(settings_dict['norm_window'])))))
        if 'min_distance' in settings_dict:
            self.distance_spin.setValue(int(settings_dict['min_distance']))
        if 'basecall_method' in settings_dict:
            idx = int(settings_dict['basecall_method'])
            if 0 <= idx < self.method_combo.count():
                self.method_combo.setCurrentIndex(idx)
        if 'prominence_frac' in settings_dict:
            self.prominence_spin.setValue(int(round(float(settings_dict['prominence_frac']) * 1000.0)))
        if 'min_signal_frac' in settings_dict:
            self.ambig_spin.setValue(int(round(float(settings_dict['min_signal_frac']) * 100.0)))
        if 'tolerance' in settings_dict:
            self.tol_spin.setValue(int(settings_dict['tolerance']))
        if 'fill_in' in settings_dict:
            self.fillin_check.setChecked(bool(settings_dict['fill_in']))
        if 'fill_gap' in settings_dict:
            self.fill_gap_spin.setValue(int(settings_dict['fill_gap']))
        if 'fill_margin' in settings_dict:
            self.fill_margin_spin.setValue(int(round(float(settings_dict['fill_margin']) * 100.0)))
        if 'matrix' in settings_dict:
            self._set_matrix(np.array(settings_dict['matrix']))
        if 'mobility_shifts' in settings_dict:
            for ch, val in enumerate(settings_dict['mobility_shifts']):
                self.mobility_spins[ch].setValue(int(val))
        if 'esd_offset' in settings_dict:
            self.esd_offset_spin.setValue(int(settings_dict['esd_offset']))
        if 'reference_dna' in settings_dict:
            self.reference_dna = str(settings_dict['reference_dna'])
        if 'reference_name' in settings_dict:
            self.reference_name = str(settings_dict['reference_name'])
        if 'reference_start' in settings_dict:
            self.reference_start = int(settings_dict['reference_start'])
        if 'reference_end' in settings_dict:
            self.reference_end = int(settings_dict['reference_end'])
        if 'basecall_method' not in settings_dict:
            # Legacy settings (no method key): land on the selected method's
            # factory parameter preset instead of the per-channel-tuned
            # values the old files carried, so the new default (Greedy) runs
            # with its validated parameters.
            self._on_method_changed(self.method_combo.currentIndex())
        self._save_settings()
        self._schedule_update()

    def _save_settings_to_file(self):
        """Export all current settings to a human-readable JSON text file so
        the basecall can be reproduced later or on another machine."""
        path, _ = QFileDialog.getSaveFileName(
            self, 'Save settings', 'settings.json',
            'JSON files (*.json);;All Files (*)')
        if not path:
            return
        settings = self.get_settings()
        settings['well'] = self.well_combo.currentText().strip()
        settings['esd_variant'] = self.esd_combo.currentText()
        try:
            with open(path, 'w') as f:
                json.dump(settings, f, indent=2, sort_keys=True)
        except Exception as e:
            self.status.setText(f'Could not save settings: {e}')
            return
        self.status.setText(f'Settings saved to {path}')

    def _load_settings_from_file(self):
        """Read a settings JSON text file and apply it, then reload the well
        it was saved from so the results reproduce exactly."""
        path, _ = QFileDialog.getOpenFileName(
            self, 'Load settings', '',
            'JSON files (*.json);;All Files (*)')
        if not path:
            return
        try:
            with open(path) as f:
                settings = json.load(f)
        except Exception as e:
            self.status.setText(f'Could not read settings: {e}')
            return
        if not isinstance(settings, dict):
            self.status.setText('Not a valid settings file')
            return
        if 'esd_variant' in settings:
            idx = self.esd_combo.findText(str(settings['esd_variant']))
            if idx >= 0:
                self.esd_combo.setCurrentIndex(idx)
        if 'well' in settings:
            self.well_combo.setCurrentText(str(settings['well']))
        self.load_settings_from_dict(settings)
        if self.rsd_raw is None or self.current_well != str(
                settings.get('well', '')).strip():
            self._load_data()
        self.status.setText(f'Settings loaded from {path}')

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
            'norm_window': self.norm_window_spin.value(),
            'matrix_apply_point': self._get_matrix_apply_point(),
            'basecall_method': self.method_combo.currentIndex(),
            'min_distance': self.distance_spin.value(),
            'prominence_frac': self.prominence_spin.value() / 1000.0,
            'min_signal_frac': self.ambig_spin.value() / 100.0,
            'tolerance': self.tol_spin.value(),
            'fill_in': self.fillin_check.isChecked(),
            'fill_gap': self.fill_gap_spin.value(),
            'fill_margin': self.fill_margin_spin.value() / 100.0,
            'matrix': self._get_matrix().tolist(),
            'mobility_shifts': self._get_mobility_shifts(),
            'esd_offset': self.esd_offset_spin.value(),
            'reference_name': self.reference_name,
            'reference_start': self.reference_start,
            'reference_end': self.reference_end,
            'reference_dna': self.reference_dna,
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
        self.smooth_combo.setToolTip(SMOOTH_TOOLTIPS.get(method))
        self.sm_param1_label.setToolTip(SMOOTH_PARAM1_TOOLTIPS.get(method))
        self.sm_win_spin.setToolTip(SMOOTH_PARAM1_TOOLTIPS.get(method))
        self.sm_param2_label.setToolTip(SMOOTH_PARAM2_TOOLTIPS.get(method))
        self.sm_ord_spin.setToolTip(SMOOTH_PARAM2_TOOLTIPS.get(method))
        self._schedule_update()

    def _on_baseline_method_changed(self, method):
        cfg = BASELINE_PARAM_CONFIG.get(
            method, ('Window:', (20, 1000), None, None))
        label1, rng1, label2, rng2 = cfg
        self.bl_param_label.setText(label1)
        self.bl_spin.setRange(*rng1)
        self.bl_slider.setRange(*rng1)
        if method == 'None':
            self.bl_spin.setEnabled(False)
            self.bl_slider.setEnabled(False)
            self.bl2_param_label.setVisible(False)
            self.bl2_slider.setVisible(False)
            self.bl2_spin.setVisible(False)
            self._schedule_update()
            return
        self.bl_spin.setEnabled(True)
        self.bl_slider.setEnabled(True)
        self.bl_spin.setValue(int(np.mean(rng1)))
        self.bl_slider.setValue(int(np.mean(rng1)))
        if label2 is not None and rng2 is not None:
            self.bl2_param_label.setText(label2)
            self.bl2_param_label.setVisible(True)
            self.bl2_slider.setVisible(True)
            self.bl2_spin.setVisible(True)
            self.bl2_param_label.setToolTip(f'{label2} for {method}')
            self.bl2_slider.setToolTip(f'{label2} for {method}')
            self.bl2_spin.setToolTip(f'{label2} for {method}')
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

    def _select_data_folder(self):
        """Let the user pick the folder containing .rsd files and the
        per-run ESD subfolders. Repopulates wells and saves the choice."""
        folder = QFileDialog.getExistingDirectory(
            self, 'Select Data Folder', self.data_dir)
        if not folder:
            return
        self.data_dir = folder
        self.data_dir_label.setText(folder)
        self._settings.setValue('data_dir', folder)
        self._populate_wells()
        n = self.well_combo.count()
        if n == 0:
            self.status.setText(
                f'No .rsd files found in {folder}. Pick the folder that '
                'contains the .rsd files (they live in a MB1000_M13_DT '
                'folder, with ESD subfolders like *_MD1 inside).')
        else:
            self.status.setText(
                f'Data folder set to {folder} — {n} wells found')

    def _populate_wells(self):
        if os.path.isdir(self.data_dir):
            wells = sorted(f[:-4] for f in os.listdir(self.data_dir)
                           if f.endswith('.rsd'))
            self.well_combo.clear()
            self.well_combo.addItems(wells)
            if 'A01' in wells:
                self.well_combo.setCurrentText('A01')
        else:
            self.well_combo.clear()
        subdirs = find_esd_subdirs(self.data_dir) if os.path.isdir(self.data_dir) else {}
        self.esd_combo.clear()
        for k in sorted(subdirs):
            self.esd_combo.addItem(k, subdirs[k])
        if self.esd_combo.count() > 0:
            cp312_idx = None
            for i in range(self.esd_combo.count()):
                if self.esd_combo.itemText(i) == 'Cp312':
                    cp312_idx = i
                    break
            if cp312_idx is None:
                cp312_idx = self.esd_combo.findText('Cp312')
            if cp312_idx >= 0:
                self.esd_combo.setCurrentIndex(cp312_idx)
            else:
                self.esd_combo.setCurrentIndex(0)

    def _load_data(self):
        well = self.well_combo.currentText().strip()
        if not well:
            return
        rsd_path = os.path.join(self.data_dir, f'{well}.rsd')
        esd_subdir = self.esd_combo.currentData() or ''
        esd_path = os.path.join(self.data_dir, esd_subdir, f'{well}.esd')
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
            self.esd_offset_spin.blockSignals(True)
            self.esd_offset_spin.setValue(int(self.esd_offset))
            self.esd_offset_spin.blockSignals(False)
            self.current_well = well
            n_peaks = len(self.esd_data.get('peak_positions', []))
            # Sanity-check the chosen ESD variant: peak_positions are supposed
            # to sit on the same (positive-scan) coordinate grid as the RSD
            # trace. A wrong variant (e.g. a calibration or alternate call
            # variant) can put peaks at negative/absurd scans, which swings the
            # estimated offset and visibly misaligns the ESD row under our
            # basecall. Catch that here instead of silently plotting rubbish.
            warning = ''
            n_scans = len(self.rsd_raw)
            pp = self.esd_data.get('peak_positions')
            peak_arr = np.asarray(pp, dtype=np.int64) if pp is not None else np.array([], dtype=np.int64)
            if len(peak_arr) > 0:
                pmin, pmax = int(peak_arr.min()), int(peak_arr.max())
                # Peaks must sit on the positive RSD scan grid and span a
                # plausible region (not all clustered or off-grid).
                if pmin < 0 or pmax - pmin < 10:
                    warning = ('  // MISALIGNED ESD: peak positions out of '
                               'range? Try the "Cp312" ESD variant.')
                elif not (0 <= pmin < n_scans and 0 < pmax <= n_scans + 2000):
                    warning = ('  // MISALIGNED ESD: peaks fall outside the '
                               'RSD scan grid. Check the ESD variant '
                               '(expected ~Cp312).')
            # Offset sanity: with the correct variant the ESD trace aligns
            # somewhere in the body of the RSD trace. An offset at the extreme
            # ends (near 0 or near n_scans) means the alignment degenerated,
            # e.g. a wrong ESD variant driving the offset to the trace edge.
            if not warning:
                if self.esd_offset < 0:
                    warning = ('  // MISALIGNED ESD: negative offset. Check '
                               'the ESD variant (expected ~Cp312).')
                elif n_scans > 0 and self.esd_offset > 0.85 * n_scans:
                    warning = ('  // MISALIGNED ESD: offset at the trace '
                               'edge. Check the ESD variant (expected '
                               '~Cp312).')
            self.status.setText(
                f'{well}: RSD {len(self.rsd_raw)} scans, '
                f'ESD {len(self.esd_traces)} recs, {n_peaks} peaks, '
                f'offset~{self.esd_offset}{warning}')
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
        index and return the position of maximum channel intensity.

        Callers with closely-spaced peaks should shrink `fwd`/`back` to
        roughly half the gap to the neighboring peak (see the ax4 label
        loop). Without that, this window can overshoot past the true apex
        in dense regions and lock onto a *neighboring* peak instead -
        which visibly misplaces the label onto the wrong peak."""
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
            self._effective_shifts(),
            self.baseline_combo.currentText(),
            self.bl_spin.value(),
            self._smooth_mode,
            self.sm_win_spin.value(),
            self.sm_ord_spin.value(),
            self._get_matrix(),
            self.bl2_spin.value() if self.bl2_spin else None,
            self._get_matrix_apply_point(),
        )

    def _on_stage_toggled(self, checked, stage):
        """Keep the matrix-stage tick boxes mutually exclusive while still
        allowing all of them to be unticked ('no matrix')."""
        if checked:
            for s, cb in self._stage_cbs.items():
                if s != stage and cb.isChecked():
                    cb.blockSignals(True)
                    cb.setChecked(False)
                    cb.blockSignals(False)
        self._schedule_update()

    def _get_matrix_apply_point(self):
        """Stage where the separation matrix is applied, from the per-graph
        tick boxes. Returns 'none' when no box is ticked (no matrix)."""
        if not hasattr(self, '_stage_cbs') or not self._stage_cbs:
            return 'smoothed'
        for stage, cb in self._stage_cbs.items():
            if cb.isChecked():
                return stage
        return 'none'

    def _set_matrix_apply_point(self, stage):
        """Set the matrix-application stage from the tick boxes (used when
        loading saved settings). 'none' untics every box."""
        if not hasattr(self, '_stage_cbs') or not self._stage_cbs:
            return
        stage = str(stage) if stage else 'none'
        for s, cb in self._stage_cbs.items():
            cb.setChecked(stage == s)

    def _get_mobility_shifts(self):
        """Read per-channel shifts from the spin boxes."""
        return [sp.value() for sp in self.mobility_spins]

    def _effective_shifts(self):
        """Mobility shifts used for the pipeline and for peak-calling/display.

        In the normal pipeline the matrix is applied *before* mobility
        correction, so the separated trace still needs shifting: this returns
        the spin values. In the experimental 'on Shifted' matrix stage the shift
        is already baked into ``separated`` by ``dsp_full_pipeline``, so we
        return zeros here to avoid shifting the same trace twice."""
        if self._get_matrix_apply_point() == 'shifted':
            return [0, 0, 0, 0]
        return self._get_mobility_shifts()

    def _apply_shifts_to_separated(self, separated, shifts=None):
        """Apply per-channel mobility shifts to the separated trace only.
        Used for display and peak detection — never fed back into the
        baseline/smoothing/matrix pipeline."""
        if shifts is None:
            shifts = self._effective_shifts()
        out = separated.copy()
        for ch in range(4):
            s = int(shifts[ch])
            if s != 0:
                out[:, ch] = dsp_shift_channel(out[:, ch], s)
        return out

    def _on_region_auto_toggled(self, checked):
        """Enable/disable the manual From/To spins when auto-detect is
        toggled. The spins keep displaying the last auto values so manual
        mode starts from a sensible window."""
        auto = bool(checked)
        self.region_start_spin.setEnabled(not auto)
        self.region_stop_spin.setEnabled(not auto)
        self._schedule_update()

    def _on_method_changed(self, index):
        """Apply the factory parameter preset for the chosen basecall
        method. Fires when the user switches methods (saved settings are
        restored afterwards and take precedence over these defaults)."""
        if index == 0:  # Greedy (max-intensity)
            self.distance_spin.setValue(5)
            self.prominence_spin.setValue(200)     # min_frac 0.20
            self.norm_window_spin.setValue(800)
        else:            # Per-channel (cluster)
            self.distance_spin.setValue(5)
            self.prominence_spin.setValue(75)      # prominence_frac 0.075
            self.norm_window_spin.setValue(2000)

    def _call_bases(self, separated, shifts, region):
        """Run the independent basecall with the currently selected method,
        returning (positions, sequence, base_groups, intensities)."""
        if self.method_combo.currentIndex() == 0:
            return pc_call_bases_greedy(
                separated, shifts,
                window=max(1, self.distance_spin.value()),
                min_frac=self.prominence_spin.value() / 1000.0,
                norm_window=max(1, self.norm_window_spin.value()),
                region=region,
            )
        return pc_call_bases_with_shifts(
            separated, shifts,
            min_distance=max(1, self.distance_spin.value()),
            prominence_frac=self.prominence_spin.value() / 1000.0,
            tolerance=max(1, self.tol_spin.value()),
            min_signal_frac=self.ambig_spin.value() / 100.0,
            norm_window=max(1, self.norm_window_spin.value()),
            region=region,
        )

    def _get_region(self, separated):
        """Return the (start, stop) scan window that confines
        normalization + basecalling to the real signal.

        In auto mode the window is derived from the separated trace via
        pc_signal_region and written back into the (read-only) spin boxes.
        In manual mode the spin values are used verbatim; 0/0 means "whole
        file" and returns None. Returns None also when there is no signal
        to detect."""
        if separated is None or len(separated) == 0:
            return None
        if self.region_auto_check.isChecked():
            start, stop = pc_signal_region(separated)
            self.region_start_spin.blockSignals(True)
            self.region_stop_spin.blockSignals(True)
            self.region_start_spin.setValue(int(start))
            self.region_stop_spin.setValue(int(stop))
            self.region_start_spin.blockSignals(False)
            self.region_stop_spin.blockSignals(False)
            return int(start), int(stop)
        r0 = int(self.region_start_spin.value())
        r1 = int(self.region_stop_spin.value())
        n = len(separated)
        if r0 <= 0 and r1 <= 0:
            return None
        r0 = max(0, r0)
        if r1 <= 0 or r1 > n:
            r1 = n
        if r1 <= r0:
            r1 = n
        return r0, r1

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
        apply_point = self._get_matrix_apply_point()
        # Panels keep their stage meaning on every matrix-stage switch, but
        # the separated panel's y-scale changes ('none' passes raw counts
        # through, else 0-1 normalized), so reset saved limits on stage
        # changes to avoid a "blank" or "jumping" plot.
        if apply_point != getattr(self, '_last_apply_point', None):
            self._saved_lims = {}
        self._last_apply_point = apply_point

        # Mobility shifts are applied only just before basecalling/peak
        # detection - never on the raw/corrected graphs (1 and 2). The
        # separated graph (3) IS the just-before-calling stage, so it shows
        # the shifted trace, and the base labels below sit at the called
        # (shifted) positions, exactly matching the basecall output. Per-
        # channel display normalization: each channel is divided by its own
        # rolling max so the four channels share the same 0-1 scale and the
        # separated plot looks like the ESD reference (uniform ~0-1 peaks)
        # instead of peaks ranging 0-2.5 at the edges to 0-7.5 in the middle.
        shifts = self._effective_shifts()
        separated_shifted = self._apply_shifts_to_separated(separated, shifts)
        region = self._get_region(separated)
        display_window = max(int(self.norm_window_spin.value()), 3)
        sep_disp = pc_normalize_display(separated_shifted, window=display_window,
                                        region=region)

        # Plot 1: raw + baseline. This graph never shows the matrix output -
        # the tick box on its left marks whether the matrix is applied at the
        # raw stage.
        for ch in range(4):
            ax1.plot(self.x_rsd, raw[:, ch], color=CHAN_COLORS[ch],
                     linewidth=0.3, alpha=0.6)
            ax1.plot(self.x_rsd, bl[:, ch], color=CHAN_COLORS[ch],
                     linewidth=0.5, linestyle='--', alpha=0.5)
        ax1.set_ylabel('Raw + baseline', fontsize=8)
        ax1.legend(['Ch0(T)', 'Ch1(G)', 'Ch2(C)', 'Ch3(A)'],
                   fontsize=5, ncol=4, loc='upper right')
        ax1.tick_params(labelbottom=False, labelsize=7)

        # Plot 2: corrected + smoothed. Same rule as Plot 1 - the matrix is
        # never drawn here; its application point is the tick box on the left.
        for ch in range(4):
            ax2.plot(self.x_rsd, corr[:, ch], color=CHAN_COLORS[ch],
                     linewidth=0.2, alpha=0.3)
            ax2.plot(self.x_rsd, sm[:, ch], color=CHAN_COLORS[ch], linewidth=0.5)
        ax2.set_ylabel('Corrected + smoothed', fontsize=8)
        ax2.tick_params(labelbottom=False, labelsize=7)

        # Plot 3: Separated (normalized, mobility-corrected - shifts are
        # applied just before basecalling and are shown here, since this is
        # the final pre-call stage). ESD is intentionally NOT drawn here -
        # see ax4 ("MegaBACE plot") for MegaBACE's own ESD reference.
        for ch in range(4):
            ax3.plot(self.x_rsd, sep_disp[:, ch], color=CHAN_COLORS[ch],
                     linewidth=0.5, label=f'Sep {BASE_LETTERS[ch]}')
        ax3.set_ylabel('Separated (normalized)', fontsize=8)
        ax3.set_ylim(0, 1.05)
        ax3.tick_params(labelbottom=False, labelsize=7)
        if region is not None and region[1] > region[0]:
            ax3.axvline(region[0], color='gray', linestyle=':', linewidth=1)
            ax3.axvline(region[1], color='gray', linestyle=':', linewidth=1)
            ax3.text(region[0] + 2, 0.97, 'start', fontsize=6, color='gray',
                     va='top')
            ax3.text(region[1] - 2, 0.97, 'stop', fontsize=6, color='gray',
                     va='top', ha='right')

        # ESD peak positions/sequence are still read here (needed for the
        # ESD-match% comparison text below and for ax4), just not drawn as
        # a trace/labels on this subplot anymore.
        peaks = self.esd_data.get('peak_positions')
        seq = self.esd_data.get('sequence', '')

        # Plot 4: ESD traces with peaks - this is the only plot that shows
        # MegaBACE's own ESD data. The offset is manually adjustable via
        # the "ESD offset" spin box (auto-populated on load), so alternate
        # ESD variants that need a different shift can be compared too.
        esd_offset = self.esd_offset_spin.value()
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
            peaks_arr = np.asarray(peaks, dtype=np.int64)
            n_dropped = 0
            for idx in range(len(peaks_arr)):
                p = int(peaks_arr[idx])
                native_guess = p - esd_offset
                # Clamp rather than skip: a peak that lands just outside
                # [0, n_esd_recs) after offset correction (typically the
                # first/last couple of calls) still gets a label at the
                # nearest valid record, instead of silently vanishing -
                # this used to make the row look like it was missing bases
                # even though ESD had called them.
                if n_esd_recs <= 0:
                    n_dropped += 1
                    continue
                native_guess = int(np.clip(native_guess, 0, n_esd_recs - 1))

                # Bound the apex search by half the gap to each neighboring
                # ESD-called peak, so in densely-spaced regions the search
                # can't overshoot the true apex and lock onto the
                # neighbor's peak instead (see _snap_to_peak_apex).
                gap_next = int(peaks_arr[idx + 1]) - p if idx + 1 < len(peaks_arr) else 999
                gap_prev = p - int(peaks_arr[idx - 1]) if idx > 0 else 999
                fwd = max(2, min(15, gap_next // 2)) if gap_next > 0 else 2
                back = max(1, min(2, gap_prev // 2)) if gap_prev > 0 else 1

                p_apex_native = self._snap_to_peak_apex(
                    self.esd_traces, native_guess, n_esd_recs, back=back, fwd=fwd)
                trace = self.esd_traces[p_apex_native]
                if np.any(trace > 0):
                    dom_ch = int(np.argmax(trace))
                    color = CHAN_COLORS[dom_ch]
                    base = BASE_LETTERS[dom_ch]
                else:
                    # Genuinely all-zero window (rare) - still draw a
                    # placeholder rather than dropping the base, so the
                    # displayed count always matches ESD's own count.
                    dom_ch = -1
                    color = 'gray'
                    base = '?'
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
                if dom_ch >= 0 and trace[dom_ch] > 0:
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
            if n_dropped:
                self.status.setText(
                    f'{n_dropped} of {len(peaks_arr)} ESD base labels could '
                    'not be placed (no valid trace records) and were skipped')

        # Matrix condition + where the matrix is currently applied
        cond = np.linalg.cond(mix)
        stage_names = {'raw': 'raw data',
                       'corrected': 'baseline-corrected',
                       'smoothed': 'corrected + smoothed',
                       'none': 'no matrix (raw channels)'}
        ax3.text(0.99, 0.01,
                 f'matrix on {stage_names.get(apply_point, apply_point)}'
                 f' · cond={cond:.2f}',
                 transform=ax3.transAxes, fontsize=7, ha='right',
                 va='bottom', color='gray',
                 bbox=dict(facecolor='white', alpha=0.7, pad=1))

        # ESD / M13 accuracy is computed below (once the independent call is
        # available) as matched-bases / reference-length via
        # pc_reference_accuracy - not by sampling at ESD's own peak positions.

        # Independent peak-calling on the mobility-corrected separated
        # trace, with IUPAC ambiguity codes and a per-base quality tick.
        esd_txt = None
        m13_txt = None
        if self.rsd_raw is not None:
            try:
                # IMPORTANT: pass the *unshifted* `separated` here, not
                # separated_shifted. The caller applies the mobility shift
                # itself; passing an already-shifted trace here used to
                # double-apply the shift, which is why called bases landed
                # roughly one peak-spacing away from the true peak apex
                # instead of on it.
                pos, iupac_seq, base_groups, intens = self._call_bases(
                    separated, shifts, region)
                # Fill-in: re-run peak detection on the combined envelope and
                # add clean positions the cluster-merge dropped (e.g. the G
                # next to a taller T only 3 scans away). Drawn in orange so
                # you can see exactly which bases the fill-in added. Only
                # relevant for the per-channel cluster method - the greedy
                # caller already resolves tight peaks.
                fillin_pos = []
                if (self.method_combo.currentIndex() != 0
                        and self.fillin_check.isChecked()):
                    fillin_add = pc_fill_in_combined_peaks(
                        separated, shifts,
                        positions=[int(p) for p in pos],
                        min_distance=max(1, self.distance_spin.value()),
                        prominence_frac=self.prominence_spin.value() / 1000.0,
                        norm_window=max(1, self.norm_window_spin.value()),
                        fill_gap=max(1, self.fill_gap_spin.value()),
                        fill_margin=self.fill_margin_spin.value() / 100.0,
                        region=region,
                    )
                    if fillin_add:
                        merged = sorted(
                            [(int(p), letter) for p, letter in zip(pos, iupac_seq)]
                            + list(fillin_add), key=lambda t: t[0])
                        pos = np.array([t[0] for t in merged], dtype=np.int64)
                        iupac_seq = ''.join(t[1] for t in merged)
                        fillin_pos = [int(t[0]) for t in fillin_add]
                fillin_set = set(fillin_pos)
                # Bases sit in one flat row near the top of the plot,
                # rather than riding up and down with each peak's own
                # height - easier to read as a continuous sequence.
                # y is in axes-fraction (0-1), x stays in data coordinates,
                # so the row stays pinned to the top of the visible area
                # through zoom/pan.
                trans = ax3.get_xaxis_transform()
                band_y = 0.96
                tick_y = 0.99
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
                    face = ('orange' if int(p) in fillin_set else 'yellow')
                    # The separated graph shows the SHIFTED trace (shifts are
                    # applied just before basecalling), and `p` is the called
                    # position in those shifted coordinates - so labels sit on
                    # the peaks that are drawn and match the basecall output.
                    x_disp = int(p)
                    ax3.text(x_disp, band_y, letter, transform=trans, fontsize=5,
                             ha='center', va='center', color='black',
                             fontweight='bold', clip_on=True,
                             bbox=dict(facecolor=face, alpha=0.6, pad=0.3,
                                       edgecolor='none'))
                    hv_x.append(x_disp)
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
                    xs = np.array([x_disp - half_w, x_disp - half_w / 2, x_disp,
                                   x_disp + half_w / 2, x_disp + half_w])
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
                    n_fill = len(fillin_pos)
                    # Matched-bases / reference-length accuracy (the "match
                    # bases / total bases" metric) against the ESD sequence.
                    esd_m, esd_t, esd_pct = pc_reference_accuracy(iupac_seq, seq)
                    # Same against the M13 reference slice (the headline target).
                    ref = getattr(self, 'reference_dna', '')
                    lo = getattr(self, 'reference_start', 0)
                    hi = getattr(self, 'reference_end', 0)
                    ref_slice = ref[lo - 1:hi] if (ref and hi > lo) else ''
                    if ref_slice:
                        m13_m, m13_t, m13_pct = pc_reference_accuracy(
                            iupac_seq, ref_slice)
                        name = getattr(self, 'reference_name', '') or 'M13'
                        m13_txt = (f'{name}: {m13_m}/{m13_t} bases '
                                   f'({m13_pct:.1f}%)')
                    else:
                        m13_txt = 'M13: no reference set'
                    esd_txt = f'ESD: {esd_m}/{esd_t} bases ({esd_pct:.1f}%)'
                    if n_fill:
                        esd_txt += f' · {n_fill} filled-in'
                    self._manual_sequence = iupac_seq
                    self._update_fasta_box(iupac_seq)
            except Exception as e:
                self._manual_sequence = ''
                self._fasta_box.setText('')
                self.status.setText(f'Independent basecall error: {e}')

        # Comparison metrics as two Qt boxes at the top of the FASTA section
        # (see _build_metrics_row), matching the surrounding widget font size.
        # Both now report matched-bases / reference-length (see
        # pc_reference_accuracy).
        self.fig.subplots_adjust(hspace=0.08, left=0.14, right=0.98,
                                 top=0.97, bottom=0.08)
        if esd_txt is not None:
            self._esd_metric_label.setText(esd_txt)
            self._esd_metric_label.setVisible(True)
        else:
            self._esd_metric_label.setVisible(False)
        if m13_txt is not None:
            self._indep_metric_label.setText(m13_txt)
            self._indep_metric_label.setVisible(True)
        else:
            self._indep_metric_label.setVisible(False)
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
        rsd_path = os.path.join(self.data_dir, f'{well}.rsd')
        df = parse_rsd(rsd_path)
        raw = df[['Channel1', 'Channel2', 'Channel3',
                  'Channel4']].values.astype(np.float32)

        # ESD data for evaluation
        esd_path = os.path.join(self.data_dir,
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
        shifts = self._effective_shifts()
        sep_shifted = self._apply_shifts_to_separated(separated, shifts)
        esd_seq = self.esd_data.get('sequence', '')
        if not esd_seq:
            self.status.setText('No ESD sequence to compare against')
            return
        positions, called_seq, heights = pc_call_bases(sep_shifted)
        self._independent_seq = called_seq
        identity = pc_nw_identity(called_seq, esd_seq, max_len=20000)
        self.status.setText(
            f'Independent peak-call: {len(called_seq)} bases called '
            f'(ESD has {len(esd_seq)}) - alignment identity vs ESD: '
            f'{identity:.1f}%')

    def _open_reference_dialog(self):
        ReferenceDialog(self).exec_()

    def _run_auto_mobility(self):
        """Peak-coincidence mobility shift estimate (see
        pc_estimate_mobility_shifts). Only meaningful on calibration-standard
        data where all four dye channels share peak positions; on a real read
        the confidence gate rejects the spurious lags envelope correlation
        used to return (e.g. -38 on Ch1 of an ordinary M13 read)."""
        if self.rsd_raw is None:
            self.status.setText('Load a well first')
            return
        shifts, conf = pc_estimate_mobility_shifts(self.rsd_raw, ref_channel=3)
        for ch, sp in enumerate(self.mobility_spins):
            sp.blockSignals(True)
            sp.setValue(int(np.clip(shifts[ch], sp.minimum(), sp.maximum())))
            sp.blockSignals(False)
        self._schedule_update()
        low = [BASE_LETTERS[ch] for ch in range(4) if conf[ch] < 0.55]
        if low:
            self.status.setText(
                f'Auto mobility: {list(map(int, shifts))} — no clear '
                f'peak-coincidence signal on {"".join(low) or "?"}, '
                f'not calibration-run data? Treat shifts as unverified.')
        else:
            self.status.setText(
                f'Auto mobility shift (calibration-run estimate): '
                f'{list(map(int, shifts))}')

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

        overnight = self.overnight_cb.isChecked()
        if overnight:
            wells_arg = 'all'
            maxiter = 400
            popsize = 25
            workers = 4
            self.status.setText(
                'Overnight optimization: all wells, deep search (this will take '
                'a long time - leave it running)...')
        else:
            wells_arg = self.current_well
            maxiter = 30
            popsize = 10
            workers = 1
        cmd = [sys.executable, '-u', script, '--base-dir', self.data_dir,
               '--wells', wells_arg, '--maxiter', str(maxiter),
               '--popsize', str(popsize), '--workers', str(workers),
               '--out', out_path,
               '--min-distance', str(self.distance_spin.value()),
               '--prominence-frac', f'{self.prominence_spin.value() / 1000.0:.6f}',
               '--ambig-frac', f'{self.ambig_spin.value() / 100.0:.6f}']
        if esd_subdir:
            subdirs = find_esd_subdirs(self.data_dir)
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
        self._save_best_to_settings_file(best)
        self.status.setText(
            f"Optimizer found {best.get('base_identity_pct', 0.0):.1f}% identity vs ESD "
            f"with {best['baseline_method']}/{best['smooth_method']} - loaded into "
            f"controls and written to A01_settings.json")

    def _save_best_to_settings_file(self, best):
        """Merge the optimizer's best baseline/smoothing/shift/matrix into the
        A01_settings.json next to this script so the user can load and try it
        via 'Load settings'. Only the parameters the optimizer searched are
        overwritten; the user's other settings (esd_variant, well, caller
        knobs, matrix stage) are preserved."""
        import os as _os
        path = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)),
                             'A01_settings.json')
        try:
            if _os.path.exists(path):
                with open(path) as f:
                    cur = json.load(f)
            else:
                cur = {}
            cur.update({
                'baseline_method': best['baseline_method'],
                'baseline_window': int(round(best['baseline_window'])),
                'baseline_window2': int(round(best.get('baseline_window2',
                                                       cur.get('baseline_window2', 0)))),
                'smooth_method': best['smooth_method'],
                'smooth_window': int(round(best['smooth_window'])),
                'smooth_order': int(round(best['smooth_order'])),
                'mobility_shifts': [int(s) for s in best['mobility_shifts']],
                'matrix': np.asarray(best['matrix']).tolist(),
            })
            with open(path, 'w') as f:
                json.dump(cur, f, indent=2)
            self.opt_log.append(f'Best settings saved to {path}')
        except Exception as e:
            self.opt_log.append(f'Could not save best settings: {e}')

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
