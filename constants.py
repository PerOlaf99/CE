"""Shared constants for the Sanger basecalling toolkit.

Matrices, colour maps, base-letter codes, method lists, parameter ranges,
and tooltip text.  Imported by dsp.py, basecall.py, and the GUI.
"""
import numpy as np

# ── Channel / base mapping ─────────────────────────────────────────────
CHAN_COLORS = ['red', 'green', 'blue', 'orange']
BASE_LETTERS = {0: 'T', 1: 'G', 2: 'C', 3: 'A'}
CHEM_MAP = {0: 'T', 1: 'G', 2: 'C', 3: 'A'}

# ── IUPAC ambiguity codes ──────────────────────────────────────────────
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

# ── Separation matrices ────────────────────────────────────────────────
DEFAULT_SPEC_MATRIX = np.array([
    [0.85, 0.03, 0.05, 0.07],
    [0.02, 0.88, 0.04, 0.06],
    [0.06, 0.04, 0.86, 0.04],
    [0.07, 0.05, 0.05, 0.83],
], dtype=np.float64)

_TUNED_SSM = np.array([
    [1.0, 1.00, 0.26, 0.46],
    [0.07, 1.00, 0.075, 0.006],
    [0.38, 0.33, 1.00, 1.52],
    [0.27, 0.26, 0.189, 1.00],
], dtype=np.float64)

OFF_PATTERN = np.array([
    [0.00, 0.20, 0.33, 0.47],
    [0.17, 0.00, 0.33, 0.50],
    [0.43, 0.29, 0.00, 0.29],
    [0.41, 0.29, 0.29, 0.00],
], dtype=np.float64)

# ── Method lists ───────────────────────────────────────────────────────
BASELINE_METHODS = [
    'None', 'Rolling Minimum', 'Rolling Median', 'ALS', 'airPLS', 'SNIP',
    'Morphological (Top-hat)', 'Polynomial Detrend',
    'Rubberband', 'AsyLS', 'arPLS', 'Flat Offset (200-1200)',
    'Noise Offset (pre-1500)',
]

SMOOTH_METHODS = [
    'Savitzky-Golay', 'Gaussian', 'Moving Avg', 'Median', 'Whittaker',
    'Butterworth', 'Wavelet', 'LOWESS', 'FFT Lowpass',
]

# ── Parameter ranges and tooltips ──────────────────────────────────────
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
    'Noise Offset (pre-1500)':  ('Noise start:', (0, 500), 'Noise end:', (500, 3000)),
}

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
