"""Pure-function signal-processing core for the MegaBACE basecalling pipeline.

Everything here is extracted verbatim (same math) from sequencing_gui_V9's
QMainWindow methods, but decoupled from Qt/self so it can be:
  - called by the GUI (thin wrapper around these functions), and
  - called by optimize_params.py in a headless loop, thousands of times,
    without importing PyQt5 at all.

Nothing in this file touches a widget, a file dialog, or a plot. If you
change the math, change it here once and both the GUI and the optimizer
pick it up.
"""
import numpy as np

CHAN_COLORS = ['red', 'green', 'blue', 'orange']
BASE_LETTERS = {0: 'T', 1: 'G', 2: 'C', 3: 'A'}
CHEM_MAP = {0: 'T', 1: 'G', 2: 'C', 3: 'A'}

DEFAULT_SPEC_MATRIX = np.array([
    [0.85, 0.03, 0.05, 0.07],
    [0.02, 0.88, 0.04, 0.06],
    [0.06, 0.04, 0.86, 0.04],
    [0.07, 0.05, 0.05, 0.83],
], dtype=np.float64)

# Off-diagonal pattern from DEFAULT (fraction of bleed to each other channel)
OFF_PATTERN = np.array([
    [0.00, 0.20, 0.33, 0.47],
    [0.17, 0.00, 0.33, 0.50],
    [0.43, 0.29, 0.00, 0.29],
    [0.41, 0.29, 0.29, 0.00],
], dtype=np.float64)

BASELINE_METHODS = [
    'Rolling Minimum', 'Rolling Median', 'ALS', 'airPLS', 'SNIP',
    'Morphological (Top-hat)', 'Polynomial Detrend',
]

SMOOTH_METHODS = [
    'Savitzky-Golay', 'Gaussian', 'Moving Avg', 'Median', 'Whittaker',
    'Butterworth', 'Wavelet', 'LOWESS', 'FFT Lowpass',
]

# (label1, range1, label2, range2) per smoothing method - single source of
# truth shared by the GUI (for slider ranges/labels) and the optimizer (for
# clamping candidate parameters into the valid range for that method).
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
    'Rolling Minimum':          ('Window:', (20, 1000)),
    'Rolling Median':           ('Window:', (20, 1000)),
    'ALS':                      ('Lambda:', (20, 100000)),
    'airPLS':                   ('Lambda:', (20, 100000)),
    'SNIP':                     ('Iterations:', (5, 500)),
    'Morphological (Top-hat)':  ('Window:', (3, 1000)),
    'Polynomial Detrend':       ('Order:', (1, 15)),
}


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


def shift_channel(arr, shift):
    """Shift a 1-D channel trace by `shift` scans, padding with the edge
    value instead of wrapping (np.roll would wrap, smearing the end of the
    trace into the start). Positive shift delays the channel (peaks move
    right); negative advances it (peaks move left)."""
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


def apply_mobility_shifts(raw, shifts):
    """raw: (n,4) array. shifts: length-4 sequence of per-channel scan
    shifts (dye mobility correction)."""
    out = raw.copy()
    for ch in range(4):
        s = int(shifts[ch])
        if s != 0:
            out[:, ch] = shift_channel(out[:, ch], s)
    return out


# ---------------------------------------------------------------------------
# Baseline
# ---------------------------------------------------------------------------
def _airpls_baseline(y, lam, itermax=15):
    """Adaptive iteratively reweighted penalized least squares (Zhang et al.
    2010): like ALS, but the asymmetry weights are re-derived every
    iteration from how far points fall below the current baseline estimate
    instead of using a fixed p, so it needs only one knob (lambda) and
    tracks non-uniform, drifting baselines better than plain ALS."""
    from scipy import sparse
    from scipy.sparse.linalg import spsolve
    n = len(y)
    y = y.astype(np.float64)
    w = np.ones(n)
    e = np.ones(n)
    D2 = sparse.diags([e, -2 * e, e], [0, 1, 2], shape=(n - 2, n))
    A0 = D2.T @ D2
    z = y.copy()
    total = np.abs(y).sum() or 1.0
    for it in range(1, itermax + 1):
        W = sparse.diags(w, 0)
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


def _snip_baseline(y, iterations):
    """SNIP (Statistics-sensitive Non-linear Iterative Peak-clipping).
    Works on an LLS-transformed copy of the trace (compresses peak heights
    so tall peaks don't dominate the clipping) and iteratively clips each
    point down to the average of its two neighbors at growing distance,
    whenever that average is lower."""
    y = np.clip(np.asarray(y, dtype=np.float64), 0, None)
    v = np.log(np.log(np.sqrt(y + 1) + 1) + 1)
    iterations = max(1, min(int(iterations), len(v) // 2 - 1))
    for p in range(1, iterations + 1):
        left = shift_channel(v, p)
        right = shift_channel(v, -p)
        v = np.minimum(v, 0.5 * (left + right))
    baseline = (np.exp(np.exp(v) - 1) - 1) ** 2 - 1
    return np.clip(baseline, 0, None)


def compute_baseline(raw, method, window):
    """raw: (n,4). window: the single tunable parameter for `method`
    (window size, lambda, or polynomial order depending on method - same
    overloading the original GUI used, kept for slider compatibility)."""
    from scipy.ndimage import minimum_filter1d, median_filter, grey_opening
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
        from scipy import sparse
        from scipy.sparse.linalg import spsolve
        lam = bw
        p = 0.005
        e = np.ones(n)
        D2 = sparse.diags([e, -2 * e, e], [0, 1, 2], shape=(n - 2, n))
        A = lam * D2.T @ D2
        for ch in range(4):
            y = raw[:, ch].astype(np.float64)
            w = np.ones(n)
            z = y
            for _ in range(10):
                W = sparse.diags(w, 0)
                z = spsolve(W + A, w * y)
                w = p * (y > z) + (1 - p) * (y <= z)
            bl[:, ch] = z
    elif method == 'airPLS':
        for ch in range(4):
            bl[:, ch] = _airpls_baseline(raw[:, ch], bw)
    elif method == 'SNIP':
        for ch in range(4):
            bl[:, ch] = _snip_baseline(raw[:, ch], bw)
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
    else:
        raise ValueError(f'Unknown baseline method: {method}')
    return bl


# ---------------------------------------------------------------------------
# Smoothing
# ---------------------------------------------------------------------------
def _wavelet_denoise(y, pywt, level, threshold_scale=1.0, wavelet='db4'):
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
    new_coeffs = [coeffs[0]] + [pywt.threshold(c, uthresh, mode='soft') for c in coeffs[1:]]
    denoised = pywt.waverec(new_coeffs, wavelet)
    return denoised[:n]


def fft_lowpass(y, cutoff_period, taper_frac=0.1):
    """Zero (with a cosine taper, to avoid ringing) all FFT bins whose
    period is shorter than `cutoff_period` scans, then inverse-transform.
    Unlike Butterworth, this is a direct frequency-domain null: useful when
    the noise is closer to periodic (electrical pickup, pump/stepper
    ripple, CCD readout striping) than broadband, since you can see exactly
    which bins to remove instead of rolling off everything above a knee."""
    y = np.asarray(y, dtype=np.float64)
    n = len(y)
    spec = np.fft.rfft(y)
    freqs = np.fft.rfftfreq(n, d=1.0)
    cutoff_freq = 1.0 / max(cutoff_period, 2.0)
    taper_width = max(cutoff_freq * taper_frac, 1e-6)
    # Smooth (cosine) roll-off around cutoff_freq instead of a hard cut,
    # which avoids Gibbs ringing at sharp peak edges.
    gain = np.ones_like(freqs)
    hi = cutoff_freq + taper_width
    lo = cutoff_freq - taper_width
    ramp = (freqs > lo) & (freqs < hi)
    gain[freqs >= hi] = 0.0
    if np.any(ramp):
        gain[ramp] = 0.5 * (1 + np.cos(np.pi * (freqs[ramp] - lo) / (hi - lo)))
    filtered = np.fft.irfft(spec * gain, n=n)
    return filtered


def dominant_periodicities(y, top_n=5):
    """Return the top_n strongest non-DC frequency components as
    (period_in_scans, relative_power) tuples, sorted by power descending.
    Use this to spot periodic noise sources before choosing a smoothing
    method or an FFT-lowpass cutoff - a plain moving-average/Gaussian
    smoother blurs a periodic component rather than removing it, while
    knowing its period lets fft_lowpass or a notch null it directly."""
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


def smooth_signal(corr, method, window, order):
    """corr: (n,4) baseline-subtracted signal. window/order: the two
    tunable params for `method`, same overloading as the GUI sliders
    (see SMOOTH_PARAM_CONFIG for what they mean per method)."""
    sm = corr.copy()
    sw, so = window, order
    if method == 'Savitzky-Golay':
        from scipy.signal import savgol_filter
        if sw > so + 1 and sw % 2 == 1:
            for ch in range(4):
                sm[:, ch] = savgol_filter(sm[:, ch], sw, so)
    elif method == 'Gaussian':
        from scipy.ndimage import gaussian_filter1d
        for ch in range(4):
            sm[:, ch] = gaussian_filter1d(sm[:, ch], sigma=so, truncate=sw / so / 2)
    elif method == 'Moving Avg':
        if sw >= 3:
            kernel = np.ones(sw) / sw
            for ch in range(4):
                sm[:, ch] = np.convolve(sm[:, ch], kernel, mode='same')
    elif method == 'Median':
        from scipy.ndimage import median_filter
        sw2 = max(3, sw if sw % 2 == 1 else sw + 1)
        for ch in range(4):
            sm[:, ch] = median_filter(sm[:, ch], size=sw2, mode='reflect')
    elif method == 'Whittaker':
        from scipy import sparse
        from scipy.sparse.linalg import spsolve
        lam = sw
        n = len(sm)
        e = np.ones(n)
        D2 = sparse.diags([e, -2 * e, e], [0, 1, 2], shape=(n - 2, n))
        A = sparse.eye(n) + lam * D2.T @ D2
        for ch in range(4):
            sm[:, ch] = spsolve(A, sm[:, ch])
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
                sm[:, ch] = _wavelet_denoise(sm[:, ch], pywt, level, thresh_scale)
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
            sm[:, ch] = fft_lowpass(sm[:, ch], sw, taper_frac=max(taper_frac, 0.01))
    else:
        raise ValueError(f'Unknown smoothing method: {method}')
    return sm


# ---------------------------------------------------------------------------
# Spectral (dye-bleed) separation
# ---------------------------------------------------------------------------
def separate_channels(sm, bl, matrix):
    try:
        inv = np.linalg.inv(matrix)
    except np.linalg.LinAlgError:
        inv = np.linalg.pinv(matrix)
    bm = np.median(bl, axis=0)
    gn = sm / (bm[np.newaxis, :] + 1e-10)
    separated = gn @ inv.T
    return np.clip(separated, 0, None)


# ---------------------------------------------------------------------------
# Full pipeline (same return signature as the old QMainWindow._process)
# ---------------------------------------------------------------------------
def full_pipeline(raw, mobility_shifts, baseline_method, baseline_window,
                   smooth_method, smooth_window, smooth_order, matrix):
    """raw: (n,4) float64. Returns (raw, bl, corr, sm, separated, mix)."""
    raw = raw.copy()
    raw = apply_mobility_shifts(raw, mobility_shifts)
    bl = compute_baseline(raw, baseline_method, baseline_window)
    corr = np.clip(raw - bl, 0, None)
    sm = smooth_signal(corr, smooth_method, smooth_window, smooth_order)
    separated = separate_channels(sm, bl, matrix)
    return raw, bl, corr, sm, separated, matrix
