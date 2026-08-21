"""
cimarrontv.py - Pure-Python port of the Cimarron Software (Cimarron 3.12)
MegaBACE base-calling engine.

Reverse-engineered from CimBC030012_noPuff.dll (build 2001-10-18) and its
core engine csibq030012.dll (217KB / 450 exports).  The original is a 32-bit
MSVC 4.x Windows DLL using the Numerical Recipes library; this is a faithful
re-implementation in pure Python + numpy/scipy that reproduces the same
algorithmic stages and uses the same numeric constants recovered during the
reverse-engineering (see REVERSE_ENGINEERED.md for the evidence).

Variants (cf. MegaBACE/Base Calling/Basecall.ini):
    "3.12"      -> Cimarron 3.12           (CimBC030012_noPuff.dll)  base call
    "3.12a"     -> Cimarron 3.12 Aligned   (CimBC030012_beautify.dll)  SW/ShftVect realignment
    "3.12e"     -> Cimarron 3.12 Even Space(CimBC030012_printify.dll)  even-spacing resample

Algorithm stages (verified via class/method map):
    1. Wvfm  baseline + smoothing        (sc_la / savitzkyGolay / smooth3)
    2. ObsInpSpec xtalk = SSM deconvolve (4x4 Spectral Separation Matrix, LU)
    3. Wvfm.putativePks  -> peak detect   (SNR >= 3.0 ; noise frac 0.0587)
    4. BandStat per peak  (14 fields incl. widt ratio 1.12..1.92)
    5. Mobility table search (70-entry std-ladder, lower-bound match)
    6. SW self alignment  -> template region (SSNODE start/stop, SWold/swwalk)
    7. ShftVect  -> per-base indel realign
    8. RdrOut     -> clip + edit (N) + Staden-Phred quality
    9. output sequence + qualities

Only stdlib + numpy + scipy are required (mirrors the Numerical Recipes deps).
"""

from __future__ import annotations

import math
import os
import struct
from dataclasses import dataclass, field
from typing import Optional, Tuple, List

import numpy as np
from scipy.signal import savgol_filter, find_peaks, butter, filtfilt
from scipy.ndimage import minimum_filter1d, maximum_filter1d
from scipy.sparse import diags as sparse_diags
from scipy.sparse.linalg import spsolve
from scipy.linalg import solve  # noqa: F401  (SSM inversion helper, kept for parity)

# --------------------------------------------------------------------------- #
# Reverse-engineered constants (see REVERSE_ENGINEERED.md)
# --------------------------------------------------------------------------- #
# Dye order used by MegaBACE 10-line gel: 0=FAM, 1=JOE, 2=TAMRA, 3=CY5
DYE_ORDER = ("FAM", "JOE", "TAMRA", "CY5")

# Channel -> base map.  The MegaBACE / ESD colour convention used by this
# project (sequencing_gui_V15.py BASE_LETTERS / CHAN_COLORS) is:
#   channel 0 = red   -> T
#   channel 1 = green -> G
#   channel 2 = blue  -> C
#   channel 3 = orange-> A
# Override per-run via Cimarron312(base_letters=...).
BASE_OF_DYE = DEFAULT_BASE_OF_DYE = ("T", "G", "C", "A")

# Peak-detection SNR threshold.  Confirmed: fld of the double 3.0012 in
# csibq030012.dll .data, used as the call-vs-noise cutoff in Wvfm/ObsInpSpec.
SNR_CALL_THRESHOLD = 3.0

# Noise-estimation width as a fraction of the peak spacing.
# Confirmed: the float pair 0.0587 (== 3/51) appears in csibq .rdata/.data,
# paired in the per-channel width-ratio table; 0.0558/0.0592 cluster == noise
# fraction used by ObsInpSpec::widthStats / xtalk.
NOISE_FRAC = 0.0587

# Per-lane peak-width-ratio table (grows along the lane as bands broaden).
# Confirmed values from csibq030012.dll .rdata (1.875 floor, growing 1.12->1.94).
# Indexed by fractional migration position f in [0,1).
_WIDTH_RATIOS = np.array(
    [1.12, 1.16, 1.20, 1.24, 1.265, 1.285, 1.305, 1.325, 1.45, 1.51,
     1.515, 1.52, 1.535, 1.7, 1.74, 1.7425, 1.7625, 1.875, 1.91875, 1.9375],
    dtype=float
)

# Savitzky-Golay baseline smoothing (Wvfm::savitzkyGolay / sc_la).  3.0 basecall
# used window 9, polyorder 3; 3.12 keeps the same window but the noise_frac
# above for adaptive width.
SAVGOL_WINDOW = 11
SAVGOL_POLY = 3

# Mobility: 70-entry size-ladder.  3.12 Mobility::search loops `i < 0x46 (70)`
# over 0x24-byte structs whose +0x20 float field is the size standard.
# The standard MegaBACE/ABI ladders (3.1-1200bp Hi-Dye or 1-500bp); the *ordering*
# is what matters for base-calling (earliest time -> base 1).
MOBILITY_NSTD = 70

# Staden-Phred quality mapping (QualCtrl::StadenQual / bspac).
# Cimarron maps signal/noise to a Staden phred-ish quality via the bspac table.
# We approximate with the standard Phred formula q = -10*log10(p), p derived from SNR.
QUAL_CAP = 90

# Default 4x4 Spectral Separation Matrix (SSM) = identity.  3.12 loads the
# real bleed/crosstalk matrix at runtime via Wvfm::ssm / ObsInpSpec
# Annotate::setCFixSts (cf. Basecall.ini "Set Spectral Separation Matrix"
# and each run's settings.json "matrix").  The engine inverts this crosstalk
# matrix internally (mirrors dsp_separate_channels / Wvfm::specSep), so pass
# the *crosstalk* matrix (detected = M @ pure) here; the default identity
# means "no crosstalk / pre-separated data".
DEFAULT_SSM = np.eye(4)

# Canonical MegaBACE ET-dye crosstalk matrix (cf. basecall_megabace.py default).
# Use this when no run-specific matrix is supplied.
ETDYE_CROSSTALK = np.array([
    [1.00, 0.18, 0.02, 0.00],
    [0.22, 1.00, 0.20, 0.03],
    [0.05, 0.25, 1.00, 0.28],
    [0.00, 0.04, 0.21, 1.00],
], dtype=float)

# Channel -> base map.  The MegaBACE / ESD colour convention used by this project
# (matches sequencing_gui_V15.py BASE_LETTERS / CHAN_COLORS) is:
#   channel 0 = red   -> T
#   channel 1 = green -> G
#   channel 2 = blue  -> C
#   channel 3 = orange-> A
# Override per-run via Cimarron312(base_letters=...).
DEFAULT_BASE_OF_DYE = BASE_OF_DYE

# Peak-caller constants (mirror sequencing_gui_V15.py).
# channel index -> called base (greedy max-intensity caller).
CHEM_MAP = {0: BASE_OF_DYE[0], 1: BASE_OF_DYE[1],
            2: BASE_OF_DYE[2], 3: BASE_OF_DYE[3]}
BASE_LETTERS = BASE_OF_DYE

# Greedy caller defaults (proven on the MB1000_M13_DT plate, see the
# basecall_scripts/greedy_fullplate.py benchmark: mean NW identity ~88-90%).
GREEDY_WINDOW = 5          # excision half-band (scans) around each picked peak
GREEDY_MIN_FRAC = 0.20     # stop when best envelope value < 20% of region max
GREEDY_NORM_WINDOW = 400   # rolling-max normalization window (scans)

# Proven DSP pipeline defaults (tuned on A01 vs its .esd reference).
PIPELINE_BASELINE_METHOD = "AsyLS"
PIPELINE_BASELINE_WINDOW = 50000      # AsyLS smoothing lambda
PIPELINE_BASELINE_P = 0.01            # AsyLS asymmetry
PIPELINE_SMOOTH_METHOD = "Butterworth"
PIPELINE_SMOOTH_WINDOW = 5            # Butterworth critical period (scans)
PIPELINE_SMOOTH_ORDER = 9             # Butterworth order
PIPELINE_MATRIX_APPLY_POINT = "corrected"
PIPELINE_MOBILITY_SHIFTS = (5, 11, 10, 10)   # per-channel lag (scans)

# Current-sag migration correction (Wvfm::fixCurrent / Wvfm::fixCurrentSag,
# csibq030012.dll 0x1ef20 / 0x1eb26).  Constants confirmed from .rdata:
#   - sag threshold ratio 0.9 (0x10038b30/0x10038b34): current is "in sag" when
#     current[x] < 0.9 * fit[x]; 45 (0x2d) consecutive scans declare a dip, then
#     45 consecutive recovered scans close it.
#   - the fit threshold is the 25th percentile of the current trace
#     (sorted_current[n - n*3//4], n = run length).
#   - no-resample gate 0.75 (0x10038b44); scale divisor 2.0 (0x10038b60, qword)
#     -> scale = (baseline_fit + recovery_fit) / 2.
CURRENT_SAG_RATIO = 0.9
CURRENT_SAG_MIN_RUN = 45
CURRENT_FIT_QUANTILE = 0.25
CURRENT_AVG_GATE = 0.75


@dataclass
class Peak:
    """A called electrophoretic peak (mirrors 3.0 BandStat fields, see REVERSE_ENGINEERED.md)."""
    idx: int            # array index of the peak maximum
    time: float         # migration time (scan index)
    channel: int        # dye channel 0..3
    base: str           # called base
    height: float       # peak height above local baseline
    snr: float          # signal-to-noise ratio
    width: float        # FWHM in scans
    quality: int        # Staden-style phred quality (0..90)
    # BandStat-style extra fields (kept for parity / debugging)
    bbgn: int = 0
    bend: int = 0
    lowv: float = 0.0
    xbnd: float = 0.0
    buzz: float = 0.0
    shap: float = 0.0
    widt_ratio: float = 1.0
    ntnr: float = 0.0
    insr: float = 0.0
    awid: float = 0.0


@dataclass
class CallResult:
    sequence: str
    quality: str            # phred+33 ascii
    peaks: List[Peak] = field(default_factory=list)
    mobility_bp: List[float] = field(default_factory=list)   # if mobility table known
    trace_time: Optional[np.ndarray] = None


# --------------------------------------------------------------------------- #
# Stage 1+2: baseline removal & spectral separation
# --------------------------------------------------------------------------- #
def _baseline(trace: np.ndarray, window: int = SAVGOL_WINDOW, poly: int = SAVGOL_POLY) -> np.ndarray:
    """Wvfm::bestBaseline_ / sc_la: robust lower-envelope baseline that does
    NOT follow the peaks (a plain Savitzky-Golay of the raw signal would sit on
    top of narrow peaks and subtract them).  Cimarron fits a baseline to the
    local minima, so we use a morphological moving-minimum (radius ~ the peak
    spacing*noise_frac) smoothed with a light Savitzky-Golay filter.  The
    returned array is the *baseline estimate* (callers subtract it)."""
    n = len(trace)
    # radius for the minimum filter: ~ a few peak widths.  Use the noise-frac
    # spacing rule-of-thumb so the filter sits below real peaks.
    rad = max(3, int(2 * n * NOISE_FRAC / 4))
    rad = min(rad, max(3, n // 10))
    # moving minimum tracks the lower envelope (valleys) without following peaks
    base = minimum_filter1d(trace, size=2 * rad + 1, mode='nearest')
    # light smoothing of the envelope (mirror of Wvfm::smooth3 / savgol)
    if n > rad and rad >= 3:
        try:
            base = savgol_filter(base, max(5, min(window, n if n % 2 else n - 1)), poly)
        except Exception:
            pass
    return np.clip(base, None, trace.max() if n else 0.0)


def _noise_floor(trace: np.ndarray) -> float:
    """Robust noise std (median absolute deviation) - ObsInpSpec::widthStats."""
    if len(trace) < 5:
        return float(max(np.std(trace), 1e-6))
    mad = np.median(np.abs(trace - np.median(trace)))
    std = 1.4826 * mad  # MAD->Gaussian sigma
    return float(max(std, 1e-6))


# --------------------------------------------------------------------------- #
# Current-sag migration correction (Wvfm::fixCurrent + Wvfm::fixCurrentSag)
# --------------------------------------------------------------------------- #
# Under constant voltage the run current decays as the capillary resistance
# grows; since the migrated distance is proportional to the transported charge
# (integral of the current), Cimarron remaps the trace from time-space into
# charge-space whenever the current sags more than 10% below its fitted
# baseline for a sustained run of scans.  Each affected window is resampled
# from ``len`` scans to ``round(sum(current)/scale + 0.5)`` scans, which both
# corrects peak positions (migration) and compresses the sagged region.
def _current_fit_baseline(current: np.ndarray) -> np.ndarray:
    """Quadratic LSQ fit of current vs scan position over samples above the
    25th percentile (mirrors fixCurrent: threshold = sorted[n - n*3//4])."""
    n = len(current)
    x = np.arange(1, n + 1, dtype=np.float64)
    idx = int(n - n * 3 // 4)
    thr = float(np.sort(current)[min(max(idx, 0), n - 1)])
    m = current > thr
    if m.sum() < 5:
        return np.full(n, current.mean())
    c = np.polyfit(x[m], current[m], 2)
    return np.polyval(c, x)


def _detect_current_sag(current: np.ndarray, fit: np.ndarray
                        ) -> List[Tuple[int, int, float]]:
    """Detect sag segments of the current trace relative to the fitted
    baseline.  Returns (bgn, end, scale) tuples, 1-based inclusive scan
    indices, scale = (baseline_fit + recovery_fit) / 2.

    Mirrors Wvfm::fixCurrent: dip when r = current/fit < 0.9 for 45
    consecutive scans, recovered when r >= 0.9 for 45 consecutive scans."""
    n = len(current)
    r = current / fit
    segs: List[Tuple[int, int, float]] = []
    phase = 1            # 1 = normal (hunting a dip), 0 = in sag (hunting recovery)
    cnt = 0
    base_fit = 0.0
    dip_bgn = 0
    for i in range(1, n + 1):
        if phase == 1:
            if r[i - 1] < CURRENT_SAG_RATIO:
                cnt += 1
                if cnt >= CURRENT_SAG_MIN_RUN:
                    base_fit = float(fit[i - 1])
                    dip_bgn = i - cnt + 1
                    phase = 0
                    cnt = 0
            else:
                if cnt > 0:
                    cnt -= 1
        else:
            if r[i - 1] >= CURRENT_SAG_RATIO:
                cnt += 1
                if cnt > CURRENT_SAG_MIN_RUN:
                    rec_end = i
                    scale = (base_fit + float(fit[i - 1])) / 2.0
                    segs.append((dip_bgn, rec_end - cnt + 1, scale))
                    phase = 1
                    cnt = 0
            else:
                if cnt > 0:
                    cnt -= 1
    if phase == 0:
        segs.append((dip_bgn, n, (base_fit + float(fit[-1])) / 2.0))
    return segs


def _fix_current_sag_segment(channels: np.ndarray, current: np.ndarray,
                             bgn: int, end: int, scale: float) -> np.ndarray:
    """Resample one sag segment [bgn,end] (1-based inclusive) of the (N,4)
    raw trace into charge-space.  Mirrors Wvfm::fixCurrentSag (0x1eb26):
    5 windows; each window's output length = round(sum(current)/scale + 0.5);
    if the whole segment averages >= 0.75*len it is copied straight through."""
    L = end - bgn + 1
    L5 = L // 5
    # window boundaries: bound[b] = bgn + b*(L5+1); offs[b] = bound[b]+L5; offs[4]=end
    bounds = [bgn + b * (L5 + 1) for b in range(5)]
    offs = [bounds[b] + L5 for b in range(5)]
    offs[4] = end
    cnts = []
    for b in range(5):
        s = float(current[bounds[b] - 1:offs[b]].sum())
        cnts.append(int(s / scale + 0.5))     # ftol-style round-half-up
    total = sum(cnts)
    if total / L >= CURRENT_AVG_GATE:
        return channels[bgn - 1:end].copy()
    out = np.empty((max(total, 1), channels.shape[1]), dtype=np.float64)
    o = 0
    for b in range(5):
        n_out = cnts[b]
        if n_out <= 0:
            continue
        w = channels[bounds[b] - 1:offs[b]]      # (wlen, 4)
        if n_out == w.shape[0]:
            out[o:o + n_out] = w
        else:
            xi = np.linspace(0, w.shape[0] - 1, n_out)
            out[o:o + n_out] = np.column_stack(
                [np.interp(xi, np.arange(w.shape[0]), w[:, c]) for c in range(w.shape[1])])
        o += n_out
    return out[:o]


def wvfm_fix_current(channels: np.ndarray, current: np.ndarray
                     ) -> Tuple[np.ndarray, np.ndarray, int]:
    """Wvfm::fixCurrent (0x1ef20): current-sag migration correction applied to
    the RAW (N,4) channel trace before baseline/SSM.  Returns
    (corrected_channels, corrected_current, n_sag_segments); unchanged copies
    when no sag is detected.  Corrected trace may be shorter than the input
    (the sagged scans are compressed into charge-space)."""
    channels = np.asarray(channels, dtype=np.float64)
    current = np.asarray(current, dtype=np.float64)
    n = len(current)
    if n < 200 or channels.ndim != 2 or channels.shape[0] != n:
        return channels, current, 0
    fit = _current_fit_baseline(current)
    segs = _detect_current_sag(current, fit)
    if not segs:
        return channels, current, 0

    out_ch = np.empty_like(channels, dtype=np.float64)
    out_cur = np.empty(n, dtype=np.float64)
    out_idx = 0
    src_idx = 0
    for (bgn, end, scale) in segs:
        k = (bgn - 1) - src_idx
        if k > 0:
            out_ch[out_idx:out_idx + k] = channels[src_idx:bgn - 1]
            out_cur[out_idx:out_idx + k] = current[src_idx:bgn - 1]
            out_idx += k
        seg_out = _fix_current_sag_segment(channels, current, bgn, end, scale)
        k = seg_out.shape[0]
        out_ch[out_idx:out_idx + k] = seg_out
        out_cur[out_idx:out_idx + k] = scale     # DLL writes the expected current
        out_idx += k
        src_idx = end
    if src_idx < n:
        k = n - src_idx
        out_ch[out_idx:out_idx + k] = channels[src_idx:src_idx + k]
        out_cur[out_idx:out_idx + k] = current[src_idx:src_idx + k]
        out_idx += k
    return out_ch[:out_idx], out_cur[:out_idx], len(segs)


# --------------------------------------------------------------------------- #
# Signal-processing pipeline (ported from sequencing_gui_V15.py; these are the
# functions proven to separate the MegaBACE dye channels correctly, unlike the
# speculative morphological-minimum baseline + SNR peak detection above).
# --------------------------------------------------------------------------- #
def dsp_shift_channel(arr: np.ndarray, shift: int) -> np.ndarray:
    """Shift a 1-D array by ``shift`` scans, padding with the edge value
    instead of wrapping.  Positive shift delays (peaks move right); negative
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


def dsp_apply_mobility_shifts(raw: np.ndarray, shifts) -> np.ndarray:
    """raw: (n,4).  shifts: length-4 sequence of per-channel scan shifts."""
    out = raw.copy()
    for ch in range(4):
        s = int(shifts[ch])
        if s != 0:
            out[:, ch] = dsp_shift_channel(out[:, ch], s)
    return out


def dsp_asyls_baseline(y: np.ndarray, lam: float, p: float = 0.01,
                       niter: int = 10) -> np.ndarray:
    """Asymmetric Least Squares baseline (Eilers 2001).  Smooths the lower
    envelope under the peaks with a second-derivative penalty ``lam`` and
    asymmetry ``p``; does not follow narrow bands."""
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
    return np.asarray(z)


def dsp_compute_baseline(raw: np.ndarray, method: str = "AsyLS",
                         window: float = PIPELINE_BASELINE_WINDOW,
                         window2: Optional[float] = None) -> np.ndarray:
    """raw: (n,4).  window2 = AsyLS asymmetry x100 (1-100) when given.
    Returns the (n,4) baseline estimate (callers subtract it)."""
    bl = np.zeros_like(raw)
    if method == 'None':
        return bl
    if method == 'AsyLS':
        lam = window
        p = (window2 / 100.0) if window2 is not None else PIPELINE_BASELINE_P
        for ch in range(4):
            bl[:, ch] = dsp_asyls_baseline(raw[:, ch], lam, p=p, niter=10)
    elif method == 'ALS':
        lam = window
        p = (window2 / 100.0) if window2 is not None else 0.005
        n = len(raw)
        e = np.ones(n)
        D2 = sparse_diags([e, -2 * e, e], [0, 1, 2], shape=(n - 2, n))
        A = lam * (D2.T @ D2)
        for ch in range(4):
            y = raw[:, ch].astype(np.float64)
            w = np.ones(n)
            z = y.copy()
            for _ in range(10):
                W = sparse_diags(w, 0)
                z = spsolve(W + A, w * y)
                w = p * (y > z) + (1 - p) * (y <= z)
            bl[:, ch] = z
    elif method == 'Rolling Minimum':
        bw = max(3, int(window))
        for ch in range(4):
            bl[:, ch] = minimum_filter1d(raw[:, ch], size=bw, mode='reflect')
    elif method == 'Rolling Median':
        bw = max(3, int(window))
        from scipy.ndimage import median_filter
        for ch in range(4):
            bl[:, ch] = median_filter(raw[:, ch], size=bw, mode='reflect')
    elif method == 'Flat Offset':
        start = max(0, int(window))
        end = min(len(raw), int(window2) if window2 is not None else start + 1000)
        if end <= start:
            end = start + 1000
        region = raw[max(0, start):min(len(raw), end)]
        for ch in range(4):
            ch_region = region[:, ch]
            if len(ch_region) > 0:
                bl[:, ch] = float(np.median(ch_region))
    else:
        raise ValueError(f'Unknown baseline method: {method}')
    return bl


def dsp_smooth_signal(corr: np.ndarray, method: str = "Butterworth",
                      window: int = PIPELINE_SMOOTH_WINDOW,
                      order: int = PIPELINE_SMOOTH_ORDER) -> np.ndarray:
    """corr: (n,4) baseline-subtracted signal.  Smooth each channel."""
    sm = corr.copy()
    if method in (None, 'None'):
        return sm
    if method == 'Butterworth':
        order_ = max(1, min(int(order), 10))
        wn = float(np.clip(2.0 / max(int(window), 2), 1e-4, 0.99))
        b, a = butter(order_, wn, btype='low')
        padlen = 3 * (max(len(a), len(b)) - 1)
        if len(sm) > padlen:
            for ch in range(4):
                sm[:, ch] = filtfilt(b, a, sm[:, ch])
    elif method == 'Savitzky-Golay':
        sw, so = int(window), int(order)
        if sw > so + 1 and sw % 2 == 1:
            for ch in range(4):
                sm[:, ch] = savgol_filter(sm[:, ch], sw, so)
    elif method == 'Moving Avg':
        sw = max(3, int(window))
        kernel = np.ones(sw) / sw
        for ch in range(4):
            sm[:, ch] = np.convolve(sm[:, ch], kernel, mode='same')
    elif method == 'Median':
        from scipy.ndimage import median_filter
        sw2 = max(3, int(window) if int(window) % 2 == 1 else int(window) + 1)
        for ch in range(4):
            sm[:, ch] = median_filter(sm[:, ch], size=sw2, mode='reflect')
    else:
        raise ValueError(f'Unknown smoothing method: {method}')
    return sm


def dsp_separate_channels(sm: np.ndarray, bl: np.ndarray,
                          matrix: Optional[np.ndarray]) -> np.ndarray:
    """Spectral (dye-bleed) separation via matrix inversion.

    ``matrix`` is the *crosstalk/bleed* matrix (detected = M @ pure dyes), as
    stored in each run's settings.json and passed to set_spec_sep_matrix.  It
    is inverted internally; the per-channel dye gains are normalized by the
    median baseline level of each channel (dsp_separate_channels in V15)."""
    if matrix is None:
        return sm.copy()
    m = np.asarray(matrix, dtype=float)
    if m.shape != (4, 4):
        raise ValueError(f'need a 4x4 crosstalk matrix, got {m.shape}')
    try:
        inv = np.linalg.inv(m)
    except np.linalg.LinAlgError:
        inv = np.linalg.pinv(m)
    bm = np.median(bl, axis=0)
    bm[bm <= 1e-9] = 1.0
    gn = sm / (bm[np.newaxis, :] + 1e-10)
    separated = gn @ inv.T
    return np.clip(separated, 0, None)


def dsp_separate_channels_dll(raw: np.ndarray,
                              matrix: Optional[np.ndarray]) -> np.ndarray:
    """Faithful port of Cimarron 3.12 specSep (csibq030012.dll 0x30a2c) +
    wrapper CimBC030012_noPuff.dll ExecuteProcedure matrix prep.

    The analysis software supplies the *raw* bleed matrix M (diag ~1,
    off-diag bleed fractions).  The wrapper inverts it (Gauss-Jordan, 0x11e0,
    singular check vs 0.0) and normalizes each column by its max (columns with
    max <= 0 are skipped), giving M_final at Wvfm+0xe8.  specSep then applies,
    on the RAW pre-baseline trace, per scan i and dye d:

        sep[i][d] = sum_c raw[i][c] * M_final[d-1][c]     (row d of x.M_final^T)

    and clamps negatives to 0 (0x30f60).  Returns (N,4)."""
    if matrix is None:
        return np.clip(raw, 0, None)
    m = np.asarray(matrix, dtype=float)
    if m.shape != (4, 4):
        raise ValueError(f'need a 4x4 crosstalk matrix, got {m.shape}')
    try:
        inv = np.linalg.inv(m)
    except np.linalg.LinAlgError:
        inv = np.linalg.pinv(m)
    colmax = np.abs(inv).max(axis=0)
    colmax[colmax <= 0.0] = 1.0
    mfinal = inv / colmax[np.newaxis, :]
    sep = raw @ mfinal.T
    return np.clip(sep, 0, None)


def dsp_full_pipeline(raw: np.ndarray, mobility_shifts,
                      baseline_method: str = PIPELINE_BASELINE_METHOD,
                      baseline_window: float = PIPELINE_BASELINE_WINDOW,
                      smooth_method: str = PIPELINE_SMOOTH_METHOD,
                      smooth_window: int = PIPELINE_SMOOTH_WINDOW,
                      smooth_order: int = PIPELINE_SMOOTH_ORDER,
                      matrix: Optional[np.ndarray] = None,
                      baseline_window2: Optional[float] = None,
                      matrix_apply_point: str = PIPELINE_MATRIX_APPLY_POINT,
                      ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Full processing pipeline -> (baseline, corrected, smoothed, separated).

    Order (mirrors V15 dsp_full_pipeline): baseline-subtract each raw channel,
    smooth, then apply the crosstalk matrix at the requested stage.  Mobility
    shifts are never applied here; the caller shifts the returned ``separated``
    trace right before peak detection.

    ``matrix_apply_point``:
      'none'       - no separation; separated = corrected+smoothed signal
      'raw'        - separate raw, then baseline-correct + smooth the result
      'corrected'  - separate the baseline-corrected signal, then smooth it
      'smoothed'   - separate the corrected+smoothed signal (classic order)
      'shifted'    - shift the smoothed channels first, then separate
    """
    raw = np.asarray(raw, dtype=np.float64)
    n = len(raw)
    bl = dsp_compute_baseline(raw, baseline_method, baseline_window,
                              baseline_window2)
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
        separated = dsp_smooth_signal(
            dsp_separate_channels(corr, bl, matrix),
            smooth_method, smooth_window, smooth_order)
    elif matrix_apply_point == 'dll':
        sep_raw = dsp_separate_channels_dll(raw, matrix)
        sep_bl = dsp_compute_baseline(sep_raw, baseline_method,
                                      baseline_window, baseline_window2)
        sep_corr = np.clip(sep_raw - sep_bl, 0, None)
        separated = dsp_smooth_signal(sep_corr, smooth_method, smooth_window,
                                      smooth_order)
    elif matrix_apply_point == 'none':
        separated = sm.copy()
    elif matrix_apply_point == 'shifted':
        shifted = np.empty_like(sm)
        for ch in range(4):
            shifted[:, ch] = dsp_shift_channel(sm[:, ch],
                                               int(mobility_shifts[ch]))
        separated = dsp_separate_channels(shifted, bl, matrix)
    else:
        separated = dsp_separate_channels(sm, bl, matrix)
    return bl, corr, sm, np.asarray(separated, dtype=np.float64)


def pc_signal_onset(separated: np.ndarray, onset_frac: float = 0.05,
                    smooth: int = 40, rise_sigma: float = 4.0,
                    lead_frac: float = 0.05,
                    rise_window: Optional[int] = None) -> int:
    """First scan where the sample DNA signal starts to *rise* above the
    instrument baseline (faithful port of V15 pc_signal_onset).

    Returns the first scan whose intensity rises by ``rise_sigma`` noise-sigmas
    over a ``rise_window`` span while sitting above the leading-baseline floor;
    short (<3 scan) isolated bumps are skipped.  Returns 0 if the trace is
    empty or constant."""
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
    rise_lead = rise[:max(1, lead_n - W)]
    rise_noise = max(float(rise_lead.std()) if len(rise_lead) > 1 else 0.0, 1e-9)
    rise_thresh = float(rise_sigma) * rise_noise
    above_floor = tot >= floor + float(rise_sigma) * spread
    candidates = np.where((rise > rise_thresh) & above_floor[W:])[0]
    if len(candidates) == 0:
        idx = np.where(tot >= max(floor + rise_thresh,
                                  tot.max() * max(float(onset_frac), 1e-6)))[0]
        if len(idx) == 0:
            return 0
        return max(0, int(idx[0]) - smooth // 2)
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
    return max(0, int(onset) - W // 2)


def _region_onset(separated: np.ndarray, smooth: int = 40,
                  frac: float = 0.05, osc_frac: float = 0.08,
                  env_win: int = 50) -> int:
    """Read-start detector tuned against the real Cimarron 3.12 ESD peak
    positions (validated on all 96 wells of MB1000_M13_DT).

    The true read start is taken as the later of two independent cues, which
    together reject the two pre-read artefacts seen in real runs:

    * ``frac`` amplitude cue - first scan where the smoothed total signal
      exceeds ``frac`` of the run maximum.  Fires correctly when the
      pre-read region is flat instrument noise (most wells).
    * ``osc_frac`` oscillation cue - first scan where the envelope of the
      base-band residual (|total - smoothed|) exceeds ``osc_frac`` of its
      run maximum.  Fires correctly when the pre-read region contains a
      strong but *smooth* dye/primer ramp that the amplitude test would
      start too early on (the DLL calls no bases in a ramp).

    Taking the max makes the detector ignore both flat noise and smooth
    ramps: median error +7 scans vs the DLL's first base position, 91% of
    wells within +/-100 scans."""
    x = np.clip(np.asarray(separated, dtype=np.float64), 0, None)
    tot = x.sum(axis=1)
    n = len(tot)
    if n == 0 or tot.max() <= 0:
        return 0
    smooth = max(1, int(smooth))
    if n >= smooth:
        sm = np.convolve(tot, np.ones(smooth) / smooth, mode='same')
    else:
        sm = tot.copy()
    mx = float(tot.max())

    amp = 0
    idx = np.where(sm > mx * max(float(frac), 1e-6))[0]
    if len(idx):
        amp = int(idx[0])

    osc = 0
    resid = np.abs(tot - sm)
    env = np.convolve(resid, np.ones(env_win) / env_win, mode='same')
    emax = float(env.max())
    if emax > 0:
        idx = np.where(env > emax * max(float(osc_frac), 1e-6))[0]
        if len(idx):
            osc = int(idx[0])

    return max(amp, osc)


def pc_signal_region(separated: np.ndarray, onset_frac: float = 0.05,
                     tail_frac: float = 0.10, tail_margin: int = 10
                     ) -> Tuple[int, int]:
    """Callable scan window [start, stop) of a CE run (see V15
    pc_signal_region): start from the read-start detector
    (``_region_onset``, tuned to the DLL's basefinder), stop just past the
    last scan where the smoothed total still exceeds ``tail_frac`` of its
    in-region max."""
    x = np.clip(np.asarray(separated, dtype=np.float64), 0, None)
    n = len(x)
    if n == 0 or x.sum() <= 0:
        return 0, n
    tot = x.sum(axis=1)
    start = max(0, min(int(_region_onset(separated, frac=onset_frac)), n - 1))
    sig = tot[start:]
    peak = float(sig.max())
    if peak <= 0:
        return start, min(n, start + 1)
    thr = peak * max(float(tail_frac), 0.0)
    idx = np.where(sig > thr)[0]
    if len(idx) == 0:
        return start, min(n, start + 1)
    stop = start + int(idx[-1]) + 1
    return start, min(n, stop + int(tail_margin))


def _ftol(x: float) -> int:
    """MSVC __ftol: double on x87 -> int (truncation toward zero)."""
    return int(x)


def _b6db(vec: np.ndarray, i0: int, lo: int, hi: int, val: int) -> bool:
    """DLL helper 0xb6db: cdecl (vec, i0, lo, hi, val).
    True if vec[i0]/val > 6.0 and >=10 consecutive vec[i] > val in [lo,hi)."""
    if float(vec[i0]) / float(val) <= 6.0:
        return False
    n = 0
    i = i0
    while i >= lo:
        if float(val) >= vec[i]:
            break
        n += 1
        i -= 1
    i = i0 + 1
    while i < hi:
        if float(val) >= vec[i]:
            break
        n += 1
        i += 1
    return n >= 10


def _a866_flatten(data: np.ndarray) -> Tuple[int, float]:
    """DLL helper 0xa866: cdecl (data, scanl, &outMax, &outPos).
    Flattens data[1..scanl] in place (piecewise-linear baseline through
    per-100-pt rounded window minima, clamp >=0) and returns (outPos, outMax)."""
    scanl = len(data) - 1
    n = scanl // 100
    if n < 2:
        out = 1
        mx = data[1]
        for j in range(1, scanl + 1):
            if data[j] < 0.0:
                data[j] = 0.0
            if data[j] > mx:
                mx = data[j]
                out = j
        return out, mx
    a2 = [0] * n
    a1 = [0] * n
    off = 50
    j = 1
    for i in range(n):
        a2[i] = off
        a1[i] = _ftol(0.5 + data[j])
        j += 1
        off += 100
        for _ in range(1, 100):
            if a1[i] > data[j]:
                a1[i] = _ftol(0.5 + data[j])
            j += 1
    out_pos = 1
    out_max = data[1]
    slope0 = (a1[1] - a1[0]) / 100.0
    b0 = a1[1] - a2[1] * slope0
    j = 1
    for i in range(n):
        for _ in range(100):
            v = data[j] - (j * slope0 + b0)
            if v < 0.0:
                v = 0.0
            data[j] = v
            if v > out_max:
                out_pos = j
                out_max = v
            j += 1
        if i < n - 1:
            slope0 = (a1[i + 1] - a1[i]) / 100.0
            b0 = a1[i] - a2[i] * slope0
    while j <= scanl:
        v = data[j] - (j * slope0 + b0)
        if v < 0.0:
            v = 0.0
        data[j] = v
        if v > out_max:
            out_pos = j
            out_max = v
        j += 1
    return out_pos, out_max


def cimarron_bgn_end(trace: np.ndarray, method: str = "histogram",
                     bgni: int = 1, endi: Optional[int] = None,
                     ) -> Tuple[int, int]:
    """Cimarron 3.12 start/stop detection (port of Wvfm::bgnEnd -> 0x92e0).

    ``trace`` is the (N,4) pre-separation 4-channel trace (float).  Returns
    (bgn, end) in 1-based, inclusive-upper scan indices (as Wvfm 0x174/0x178).

    ``method``:
      'histogram' - detector histogram path (opts[0]&1 == 0): min-channel
                    envelope -> descent tops -> quiet-region -> band histogram
                    -> final assembly (0xa040..0xac91).
      'perbase'   - per-base CV-run path (opts[0]&1 == 1): 0x9a67 d=1..4.
    """
    trace = np.asarray(trace, dtype=np.float64)
    scanl = len(trace)
    if endi is None:
        endi = scanl
    bgni, endi = int(bgni), int(endi)

    if method == "perbase":
        return _perbase_bgn_end(trace, scanl, bgni, endi)

    # ---------------- histogram path (opts[0]&1 == 0) ------------------ #
    # 0xa040: min-channel envelope
    floor = trace.min(axis=0)
    S = np.zeros(scanl + 1)               # 1-based
    S[1:] = (trace - floor).min(axis=1)

    # 0xa17b: descent-start ("peak top") positions
    edges: List[int] = []
    state = 1
    for i in range(bgni + 1, endi):
        d = S[i] - S[i - 1]
        if state == 0:
            if d < 0.0:
                state = 1
                edges.append(i - 1)
        elif d > 0.0:
            state = 0
    m = len(edges)
    nbins = scanl // 200
    if nbins < 2 or m < 2:
        return (bgni, endi)

    # 0xa24e: histogram of peak-top positions
    prev = edges[0]
    last = edges[-1]
    span = last - prev + 1
    if span <= 0:
        return (bgni, endi)
    scale = float(nbins) / float(span)
    offset = -float(prev) * scale
    hist = np.zeros(nbins + 1, dtype=np.int64)
    for p in edges:
        b = _ftol(float(p) * scale + offset)
        if 0 <= b < nbins:
            hist[b] += 1
    total = float(hist[:nbins].sum())
    if total <= 0.0:
        return (bgni, endi)
    mean_cnt = float(nbins) / total
    sumsq = float((hist[:nbins] ** 2).sum())
    stddev = math.sqrt(sumsq / float(nbins) - mean_cnt * mean_cnt)

    # 0xa3b8: widest quiet region (>=3 low bins then >=3 high bins, leaky runs)
    thresh = _ftol(mean_cnt)
    best_start = 0
    best_end = 0
    run = 0
    flag = 0
    start = 0
    end = 0
    for j in range(nbins):
        d = int(hist[j]) - thresh
        if flag == 0:
            if d <= 0:
                run += 1
                if run >= 3:
                    start = j - run + 1
                    flag = 1
                    run = 0
            else:
                if run > 0:
                    run -= 1
        else:
            if d <= 0:
                if run > 0:
                    run -= 1
            else:
                run += 1
                if run >= 3:
                    end = j - run + 1
                    flag = 0
                    run = 0
                    if end - start > best_end - best_start:
                        best_start = start
                        best_end = end
                        if j + best_end - best_start + 1 > nbins:
                            break
    if flag == 1:
        end = nbins - 1
        if end - start > best_end - best_start:
            best_start = start
            best_end = end
    bin_pos = np.array([(2 * k + 1) * scanl // (2 * nbins)
                        for k in range(nbins + 1)], dtype=np.int64)
    if best_start > 0:
        cbgn = (int(bin_pos[best_start - 1]) + int(bin_pos[best_start])) // 2
    else:
        cbgn = int(bin_pos[best_start]) // 2
    cend = int(bin_pos[best_end])
    if cend <= cbgn:
        cend = scanl

    # 0xa866 flatten of the envelope (in place) + peak pos
    rng_end, peak_max = _a866_flatten(S)

    # 0xa572: min/max of S[cbgn..scanl]
    v1 = float(S[cbgn:scanl + 1].max())
    v2 = float(S[cbgn:scanl + 1].min())

    # 0xa61f: iterative band-map refinement (max 3 passes)
    count = 50
    k = 0
    for _ in range(3):
        if k >= count // 2:
            break
        hit = 0
        step = float(count) / (v1 - v2 + 1.0)
        base = -step * v2
        bands1 = [0] * count
        bands2 = [0] * count
        for i in range(count):
            bands2[i] = 0
            bands1[i] = _ftol((float(i) - base) / step)
        v2 = peak_max
        for i in range(cbgn, scanl + 1):
            x = S[i]
            if x < v2:
                v2 = x
            b = _ftol(x * step + base)
            if 0 <= b < count:
                bands2[b] += 1
                hit += 1
        if hit <= 0:
            break
        faccum = 0.0
        for k in range(count):
            faccum += float(bands2[k]) / float(hit)
            if faccum >= 0.98:
                break
        v1 = float(bands1[k] + (bands1[1] - bands1[0]) // 2)
    if count > 50:
        count = 50
    count = max(10, min(k, 50))

    # 0xab7e: trim low bands (<5% cumulative mass)
    total_b = float(sum(bands2[1:count]))
    if total_b > 0.0:
        acc = 0.0
        kk = 0
        for i in range(1, count):
            kk = i
            acc += float(bands2[i]) / total_b
            if acc >= 0.05:
                break
        if kk > 0:
            for i in range(0, 50 - kk):
                if i + kk < len(bands1) and i < len(bands1):
                    bands1[i] = bands1[i + kk]
                if i + kk < len(bands2) and i < len(bands2):
                    bands2[i] = bands2[i + kk]
            count -= kk
            count = max(10, count)

    # 0xac91: final assembly
    cnt = count
    bands1c = bands1[:cnt]
    bands2c = bands2[:cnt]
    t_low = float(bands1c[0])
    t_hi = 3.0 * float(bands1c[cnt - 1])
    if t_hi >= peak_max:
        t_hi = 0.75 * peak_max
    t_hi = t_hi / 20.0
    cur_band = 0
    if t_hi > t_low:
        for i in range(1, cnt // 8 + 1):
            if bands2c[i] <= bands2c[cur_band]:
                break
            cur_band = i
            t_low = float(bands1c[i])
    pos = cbgn
    best_bgn = -1
    last_good = -1
    best_end2 = -1
    near_end = -1
    if pos < rng_end:
        ok = 0
        if _b6db(S, rng_end, cbgn, scanl + 1, int(bands1c[cnt - 1])):
            if rng_end - cbgn > 200:
                sum_pre = 0.0
                cnt_pre = 0.0
                sum_post = 0.0
                cnt_post = 0.0
                for i in range(cbgn, rng_end - 30):
                    if float(bands1c[0]) > S[i] or float(bands1c[cnt - 1]) < S[i]:
                        continue
                    sum_pre += S[i]
                    cnt_pre += 1.0
                for i in range(rng_end + 30, scanl + 1):
                    if float(bands1c[0]) > S[i] or float(bands1c[cnt - 1]) < S[i]:
                        continue
                    sum_post += S[i]
                    cnt_post += 1.0
                if sum_pre < sum_post:
                    ok = 1
            else:
                ok = 1
        if ok == 1:
            pos = rng_end + 1
            cur_val = float(bands1c[cnt - 1])
            run_val = S[rng_end]
            for i in range(pos, min(rng_end + 150, scanl + 1)):
                if run_val <= S[i]:
                    continue
                if S[i] <= 0.0:
                    continue
                run_val = S[i]
            cur_val = run_val if t_low < run_val else t_low
            while pos < min(rng_end + 150, scanl + 1):
                if S[pos] > cur_val:
                    pos += 1
                    continue
                if math.isnan(S[pos]):
                    pos += 1
                    continue
                pos += 1
                if pos >= rng_end + 150:
                    break
                if S[pos] <= S[pos - 1]:
                    break
                pos -= 1
                break
    # Phase D: per-bin classification
    w = 51
    if pos >= scanl:
        pos = scanl - 1
    nb = (scanl - pos + 25) // w
    if nb < 1:
        nb = 1
    a_slope = float(nb - 1) / ((cnt - 1) / 2.0 - (cnt - 1)) if cnt > 1 else 0.0
    a_int = (cnt - 1) / 2.0 - a_slope * float(nb - 1)
    b_slope = (0.0 - float(cur_band)) / float(nb - 1) if nb > 1 else 0.0
    b_int = float(cur_band)
    i = pos
    for kk in range(nb):
        n_ok = 0
        n_high = 0
        found = 0
        end_idx = i + w
        if end_idx >= scanl:
            end_idx = scanl
        length = end_idx - i + 1
        b_slot = _ftol(b_slope * float(kk) + b_int)
        a_slot = _ftol(a_slope * float(kk) + a_int)
        if b_slot < 0:
            b_slot = 0
        if b_slot >= cnt:
            b_slot = cnt - 1
        if a_slot < 0:
            a_slot = 0
        if a_slot >= cnt:
            a_slot = cnt - 1
        t_low_k = float(bands1c[b_slot])
        t_hi_k = float(bands1c[a_slot])
        for j in range(i, end_idx):
            val = float(S[j])
            if val < t_low_k:
                continue
            n_ok += 1
            if 3.0 * t_hi_k > val:
                continue
            n_high += 1
            if found == 0:
                found = 1 if _b6db(S, j, cbgn, scanl + 1, _ftol(t_hi_k)) else 0
        if n_ok >= length // 2:
            if best_bgn == -1:
                best_bgn = kk
            last_good = kk
        if found != 0 or n_high >= (length + 3) // 4:
            if best_end2 == -1:
                best_end2 = kk
            if near_end == -1 and nb - kk < kk:
                near_end = kk
        i = end_idx
        if i >= scanl:
            break
    # Phase E: assemble + clamps
    bgn = pos
    end = scanl
    if best_bgn != -1:
        bgn = pos + w * best_bgn
        end = pos + w * (last_good + 1)
        if best_end2 != -1:
            if best_end2 <= best_bgn + 3:
                bgn = pos + w * (best_end2 + 1)
            if nb - near_end < near_end:
                end = pos + w * (near_end - 1)
        if bgn < 1:
            bgn = 1
        elif bgn > scanl:
            bgn = scanl
        if end < 1:
            end = 1
        elif end > scanl:
            end = scanl
        if end <= bgn:
            bgn = 1
            end = 2
    # Phase F: micro-refine bgn
    if bgn >= 1 and bgn < scanl:
        if float(bands1c[cnt - 1]) < S[bgn]:
            i = bgn
            while i < bgn + w and i < scanl:
                if float(bands1c[cnt - 1]) <= S[i]:
                    i += 1
                    continue
                if S[i - 1] <= S[i]:
                    i += 1
                    continue
                if S[i] < S[i + 1]:
                    i += 1
                    continue
                break
            bgn = i
        else:
            i = bgn
            while i < bgn + w and i < scanl:
                if float(bands1c[cnt - 1] if cnt - 1 < cnt else cnt - 1) > S[i]:
                    i += 1
                    continue
                i -= 1
                break
            bgn = i
    # ctor epilogue: end-bgn >= 0x801, clamp end
    if end - bgn < 0x801:
        end = bgn + 0x801
        if end > scanl:
            end = scanl
    return (max(1, bgn), max(bgn, min(scanl, end)))


def _perbase_bgn_end(trace: np.ndarray, scanl: int, bgni: int, endi: int
                     ) -> Tuple[int, int]:
    """Per-base CV-run path (0x9a67 for d=1..4, opts[0]&1 == 1)."""
    win = 200
    nbins = scanl // win
    if nbins < 3:
        return (bgni, endi)
    best_bgn = nbins
    best_end = 1
    found = 0
    run_start = 0
    cand_bgn = 0
    streak = 0
    max_val = 0.0

    def cv_of(v: np.ndarray, lo: int, hi: int) -> float:
        """0x9fa0: coefficient of variation sd/mean over v[lo..hi] (1-based)."""
        n = hi - lo + 1
        seg = v[lo:hi + 1]
        mean = float(seg.mean())
        if mean <= 0.0:
            return 0.0
        sd = float(seg.std())
        return sd / mean

    result_bgn, result_end = bgni, endi
    for d in range(1, 5):
        vec = np.zeros(scanl + 1)
        for j in range(1, scanl + 1):
            vec[j] = float(trace[j - 1, d - 1])
        best_bgn = nbins
        best_end = 1
        found = 0
        run_start = 0
        cand_bgn = 0
        streak = 0
        max_val = 0.0
        for bin_i in range(1, nbins + 1):
            lo = (bin_i - 1) * win + 1
            hi = lo + win - 1
            min_w = float(vec[lo:hi + 1].min())
            seg = vec[lo:hi + 1] - min_w
            seg = np.where(seg > 6000.0, 6000.0, seg)
            vec[lo:hi + 1] = seg
            mv = float(seg.max())
            if mv > max_val:
                max_val = mv
            cv = cv_of(vec, lo, hi)
            if not found:
                if cv >= 0.5:
                    streak += 1
                    if streak >= 3:
                        cand_bgn = bin_i - streak + 1
                        run_start = cand_bgn
                        found = 1
                        streak = 0
                else:
                    if streak > 0:
                        streak -= 1
            else:
                cand_bgn = bin_i
                if cv < 0.5:
                    streak += 1
                    if streak >= 3:
                        found = 0
                        cand_bgn = cand_bgn - streak - 1
                        streak = 0
                        if cand_bgn - run_start > best_end - best_bgn:
                            best_bgn = run_start
                            best_end = cand_bgn
                else:
                    if streak > 0:
                        streak -= 1
        if found:
            cand_bgn -= streak
            if cand_bgn - run_start > best_end - best_bgn:
                best_bgn = run_start
                best_end = cand_bgn
        bgn = (best_bgn - 1) * win + 1
        end = best_end * win
        thr2 = max_val / 8.0
        bound = bgn + 200
        if d == 1 or bgn < bgni:
            while bgn < bound:
                if vec[bgn] < thr2:
                    bgn += 1
                    continue
                bgn += 1
                while bgn < bound and vec[bgn] >= thr2:
                    bgn += 1
                while bgn < bound and vec[bgn] < vec[bgn - 1]:
                    bgn += 1
                bgn -= 1
                break
        bound = end - 200
        if d == 1 or end > endi:
            while end > bound and end > 0:
                if vec[end] < thr2:
                    end -= 1
                    continue
                end -= 1
                while end > bound and vec[end] >= thr2:
                    end -= 1
                while end > bound and vec[end] < vec[end + 1]:
                    end -= 1
                end += 1
                break
        if d == 1:
            result_bgn, result_end = bgn, end
        else:
            result_bgn = min(result_bgn, bgn)
            result_end = max(result_end, end)
    if result_end - result_bgn < 0x801:
        result_end = result_bgn + 0x801
        if result_end > scanl:
            result_end = scanl
    return (max(1, result_bgn), max(result_bgn, min(scanl, result_end)))


def pc_call_bases_greedy(separated: np.ndarray, shifts,
                         window: int = GREEDY_WINDOW,
                         min_frac: float = GREEDY_MIN_FRAC,
                         norm_window: int = GREEDY_NORM_WINDOW,
                         region: Optional[Tuple[int, int]] = None,
                         base_letters: Tuple[str, ...] = DEFAULT_BASE_OF_DYE,
                         ) -> Tuple[np.ndarray, str, List]:
    """Greedy max-intensity peak caller on the per-channel-normalized
    combined envelope (port of V15 pc_call_bases_greedy; proven ~88-90% NW
    identity on the M13 plate).

    Each channel is divided by its rolling local max (``norm_window`` scans),
    the four normalized channels are combined with a pointwise max, then the
    caller repeatedly takes the global maximum, calls the dominant channel
    there, and excises +/-``window`` scans so the next iteration finds the
    next base.  Stops below ``min_frac`` of the region maximum.

    Returns (positions, sequence, intensities) with positions sorted by scan."""
    n = len(separated)
    shifted_all = [dsp_shift_channel(separated[:, ch], int(shifts[ch]))
                   for ch in range(4)]
    normed = np.empty_like(separated)
    for ch in range(4):
        shifted = shifted_all[ch]
        rolled = maximum_filter1d(np.clip(shifted, 0, None),
                                  size=max(3, int(norm_window)),
                                  mode='nearest')
        rolled = np.where(rolled > 0, rolled, 1.0)
        normed[:, ch] = shifted / rolled
    comb = normed.max(axis=1)
    start, stop = 0, n
    if region is not None and int(region[1]) > int(region[0]):
        start, stop = max(0, int(region[0])), min(n, int(region[1]))
    else:
        start = pc_signal_onset(separated, onset_frac=0.05, smooth=40)
    if start >= stop:
        return np.array([], dtype=np.int64), '', []
    threshold = max(float(comb[start:stop].max()) * float(min_frac), 1e-9)
    work = comb.copy()
    work[:start] = -1.0
    work[stop:] = -1.0
    picks: List[int] = []
    letters: List[str] = []
    inten: List[float] = []
    while True:
        i = int(np.argmax(work))
        if work[i] < threshold:
            break
        ch = int(np.argmax(normed[i]))
        picks.append(i)
        letters.append(base_letters[ch])
        inten.append(float(shifted_all[ch][i]))
        lo, hi = max(0, i - int(window)), min(n, i + int(window) + 1)
        work[lo:hi] = -1.0
    order = np.argsort(picks)
    positions = np.array(picks, dtype=np.int64)[order]
    sequence = ''.join(letters[k] for k in order)
    intensities = [inten[k] for k in order]
    return positions, sequence, intensities


# --------------------------------------------------------------------------- #
# CFuzzySet engine (csibq030012.dll RVA 0x12ad0) -- piecewise-linear fuzzy sets
# --------------------------------------------------------------------------- #
def _lerp(xs, ys, x):
    """1-D piecewise-linear interpolation of ys over xs, endpoint-clamped."""
    if not xs:
        return 0.0
    if x <= xs[0]:
        return ys[0]
    if x >= xs[-1]:
        return ys[-1]
    lo, hi = 0, len(xs) - 1
    while hi - lo > 1:
        mid = (lo + hi) // 2
        if xs[mid] <= x:
            lo = mid
        else:
            hi = mid
    x0, x1, y0, y1 = xs[lo], xs[hi], ys[lo], ys[hi]
    t = (x - x0) / (x1 - x0) if x1 != x0 else 0.0
    return y0 + t * (y1 - y0)


def _fset_transform(kind: int, v: float) -> float:
    """Functor shape transforms (f30/f34 jump table by kind).
    type0: identity; type1: x^2 (f30) / sqrt (f34); type2: sqrt (f30) / x^2."""
    if kind == 0:
        return v
    if kind == 1:
        return v * v
    if kind == 2:
        return math.sqrt(v) if v >= 0.0 else 0.0
    return v


class _CFuzzySet:
    """0x38-byte CFuzzySet from RVA 0x12ad0: X/Y knot arrays + shape kind."""

    __slots__ = ('x', 'y', 'kind')

    def __init__(self, X, Y, kind: int = 0):
        self.x = list(map(float, X))
        self.y = list(map(float, Y))
        self.kind = int(kind)

    def eval(self, x: float) -> float:
        """+0xc: piecewise-linear interp of y over x, then f30 transform."""
        return _fset_transform(self.kind, _lerp(self.x, self.y, x))

    def scale(self, c: float) -> None:
        """+0x1c: y[i] *= c."""
        self.y = [yy * c for yy in self.y]

    def max_y(self) -> float:
        """+0x10: max of Y knots, then f30 (fitted height)."""
        return _fset_transform(self.kind, max(self.y))

    def centroid(self) -> float:
        """+0x00 compute_centroid: first moment; needs count >= 2."""
        if len(self.x) < 2:
            return 0.0
        s = sum(self.y)
        if s == 0.0:
            return 0.0
        return sum(xx * yy for xx, yy in zip(self.x, self.y)) / s

    def merge(self, other: '_CFuzzySet') -> None:
        """+0x4: union of breakpoints; each side's Y f34-transformed then
        interpolated at the shared breakpoints and added (in-place into this)."""
        xs = sorted(set(self.x) | set(other.x))
        ys = [_fset_transform(self.kind, _lerp(self.x, self.y, x)) +
              _fset_transform(other.kind, _lerp(other.x, other.y, x))
              for x in xs]
        self.x, self.y = xs, ys


def cimarron_peakfit_12140(pos, arg2, arg3, arg4, arg5, arg6):
    """Faithful port of csibq030012.dll RVA 0x12140 -- the per-base 1-vs-2
    classifier (peak-fit core; FINDINGS.md section 0x12140).

    Args (mirror the DLL's call at 0x1a8c0, all arrays length n, 1-indexed):
      pos : peak scan positions (1-based; pos[i] <= 0 fails the whole call)
      arg2: signal at each peak (DLL: Wvfm[0xc8][recs[4][i]])
      arg3: per-peak neighbor/valley values (DLL: min of Wvfm[0xc8][recs[8][i]],
            Wvfm[0xc8][recs[8][i+1]]); mean over i caps the signal scales
      arg4: period P1 per peak (DLL recs[0xc])
      arg5: period P2 per peak (DLL recs[0xc]+4)
      arg6: per-scan trace value at each peak (DLL: per-scan trace copy)

    Returns (col1, col2) float arrays: col1 = centroid (single -> ~0.5-1.5,
    double -> ~1.5-2.5), col2 = maxY.  Caller rounds col1 +/- 0.5 -> 1 or 2."""
    n = len(pos)
    if n == 0:
        return np.array([], dtype=float), np.array([], dtype=float)
    if any(p <= 0 for p in pos):
        return np.array([1.0] * n, dtype=float), np.array([0.5] * n, dtype=float)
    mean = float(np.mean(arg3[:n]))
    if mean > 0.05:
        mean = 0.05

    def Pnorm(P, p):
        """Normalize a period P against peak position p (0x124aa..0x125b2)."""
        if P < p / 2.0:
            v = p / 2.0
        elif P < p:
            v = P
        else:
            v = math.fmod(P, p)          # shipped build: fmod(P, pos)
        return v / p

    poly1 = _CFuzzySet([0.2, 0.5, 0.8], [1.0, 0.0, 1.0], 0)       # valley @0.5
    poly2 = _CFuzzySet([0.2, 0.4, 0.6, 0.8], [0.0, 1.0, 1.0, 0.0], 2)  # plateau
    poly3 = _CFuzzySet([1.0, 1.4, 1.8], [1.0, 0.5, 0.0], 0)       # arg6 small
    poly4 = _CFuzzySet([1.2, 1.4], [0.0, 1.0], 0)                 # arg6 large
    poly5 = _CFuzzySet([mean, 0.07], [1.0, 0.0], 0)               # sig high
    poly6 = _CFuzzySet([mean, 1.24 * mean], [0.0, 1.0], 1)        # sig low

    col1 = np.zeros(n, dtype=float)
    col2 = np.zeros(n, dtype=float)
    for i in range(n):
        p = float(pos[i])
        v7c = Pnorm(float(arg4[i]), p)
        v94 = Pnorm(float(arg5[i]), p)
        m1 = min(poly1.eval(v7c), poly1.eval(v94))
        v3 = poly3.eval(float(arg6[i]))
        v4 = poly4.eval(float(arg6[i]))
        v5 = poly5.eval(float(arg2[i]))
        v6 = poly6.eval(float(arg2[i]))
        v6 = max(v6, m1)
        val1 = max(v4, v6)                 # -> scale setA
        val2 = max(v3, v6)                 # -> scale setB
        acc = _CFuzzySet([0.4596, 3.554], [0.0, 0.0], 0)
        setA = _CFuzzySet([0.4596, 1.3797, 1.6864], [1.0, 1.0, 0.0], 0)
        setB = _CFuzzySet([1.3797, 1.6864, 2.2998, 2.6065],
                          [0.0, 1.0, 1.0, 0.0], 0)
        setC = _CFuzzySet([2.2998, 2.6065, 3.554], [0.0, 1.0, 1.0], 0)
        setA.scale(val1)
        setB.scale(val2)
        setC.scale(v5)
        acc.merge(setA)
        acc.merge(setB)
        acc.merge(setC)
        xbar = acc.centroid()
        maxY = acc.max_y()
        if xbar == 0.0 and maxY == 0.0:
            xbar, maxY = 1.0, 0.5          # degenerate default
        col1[i] = xbar
        col2[i] = maxY
    return col1, col2


def cimarron_gapcheck(vals, vals2, loc, base, codes, n, out):
    """Faithful port of csibq030012.dll RVA 0x11150 `gapcheck` (fgapcheck.c),
    the A-pass sub-scan peak fitter.  See notes/pkfit2.md.

    7-arg cdecl, returns 1 on success / 0 on error.  ``out`` is an (n,2)
    numpy float array filled with (pos, height) sub-scan fits per peak.
    ``codes`` is a byte array of base letters (0x43='C', 0x47='G')."""
    priors = np.zeros(n, dtype=float)
    for i in range(n):                       # phase 1: per-scan priors
        start = max(0, i - 5)
        cnt = i - start
        acc = 0.0
        prevC = 0
        prevG = 0
        for j in range(start, i):
            acc += float(loc[j])
            if codes[j] == ord('C'):
                prevC += 1
            if codes[j] == ord('G'):
                prevG += 1
        acc2 = float(vals2[i]) * cnt
        if acc2 == 0.0 or acc < acc2:
            acc2 = 1.0
        if acc == 0.0:
            ratio = 0.0
        else:
            ratio = acc2 / acc
        priors[i] = gauss_fun(5, prevG, prevC, 2, 2) * ratio

    def fun(code, X, Y, kind):
        return _CFuzzySet(X, Y, kind)

    funC = fun(2, [0.0, 0.4], [0.0, 1.0], 3)
    funB = fun(2, [0.3, 0.7], [0.0, 1.0], 2)
    funA = fun(3, [-0.5, 0.0, 0.5], [0.0, 1.0], 1)
    funD = fun(4, [0.25, 0.3, 0.45], [0.0, 1.0, 1.0], 0)
    funE = fun(2, [-0.5, 0.0], [1.0, 0.0], 3)

    for i in range(n):                       # phase 2: fit each peak
        if vals[i] == 0 or vals2[i] == 0:
            return 0
        x_cur = float(loc[i]) / vals[i] - 1.0
        y_cur = float(base[i]) / vals2[i] - 1.0
        if i == 0:
            x_prev, y_prev = 0.0, 0.0
        else:
            x_prev = float(loc[i - 1]) / vals[i] - 1.0
            y_prev = float(base[i - 1]) / vals2[i] - 1.0
        B_cur = funB.eval(x_cur); D_cur = funD.eval(x_cur)
        A_cur = funA.eval(x_cur); E_cur = funE.eval(x_cur)
        B_prev = funB.eval(x_prev); D_prev = funD.eval(x_prev)
        E_prev = funE.eval(x_prev)
        C_cur = funC.eval(y_cur); C_prev = funC.eval(y_prev)
        prior = priors[i]
        m1 = min(B_cur, prior)
        m2 = min(B_cur, E_prev, 1.0 - C_cur, 1.0 - C_prev)
        m3 = min(A_cur, E_cur)
        b0 = min(m1, m2, m3)
        m4 = min(B_cur, C_cur, C_prev)
        m5 = min(B_cur, 1.0 - E_prev, 1.0 - prior)
        m6 = max(B_cur, 1.0 - C_cur)
        b1 = min(m4, m5, m6)
        if C_cur >= 0.95 and b0 < 0.4 and b1 < 0.4 and i < n - 1:
            mid = (loc[i] + loc[i + 1]) // 4      # floor div (cdq/sar)
            x_cur = (float(loc[i]) + mid) / vals[i] - 1.0
            b1 = min(b1, min(funB.eval(x_cur), C_cur))
        funC_lo = _CFuzzySet([0.5079, 1.5002, 1.5069], [1.0, 1.0, 0.0], 0)
        funB_lo = _CFuzzySet([1.5002, 1.5069, 2.5063], [0.0, 1.0, 1.0], 0)
        funC_lo.scale(b0)
        funB_lo.scale(b1)
        # Composite fit: funA_lo connects funC_lo and funB_lo; the fitted x is
        # the crossing point of the two scaled ramps (their sum peaks there).
        xs = sorted(set(funC_lo.x) | set(funB_lo.x))
        best_x, best_y = 0.0, 0.0
        for x in xs:
            y = funC_lo.eval(x) + funB_lo.eval(x)
            if y > best_y:
                best_y, best_x = y, x
        if 0.0 < b0 < 1.0 and 0.0 < b1 < 1.0:
            lo, hi = xs[0], xs[-1]
            for _ in range(24):                # bisect funC_lo(x) == funB_lo(x)
                mid = (lo + hi) / 2.0
                if funC_lo.eval(mid) > funB_lo.eval(mid):
                    lo = mid
                else:
                    hi = mid
            best_x = (lo + hi) / 2.0
            best_y = funC_lo.eval(best_x) + funB_lo.eval(best_x)
        out[i, 0] = best_x
        out[i, 1] = best_y
    return 1


def gauss_fun(shape: int, prevG: int, prevC: int, w1: int, w2: int) -> float:
    """csibq030012.dll 0x1204b: gauss prior over the last 5 base calls."""
    n1 = (shape + 1) >> 1
    n2 = shape - n1
    w1 = w1 if w1 else n1
    w2 = w2 if w2 else n2
    r = _gauss_radial(shape, w1, w2)
    if r == 0.0:
        return 1.0
    g = _gauss_radial(shape, prevG, prevC) / r
    if g < 1.0:
        g = 1.0
    return g * g


def _gauss_radial(a: int, b: int, c: int) -> float:
    """0x120d3: 1 - sqrt(((a-b)^2 + (a-c)^2) / (2*a^2))."""
    if a == 0:
        return 1.0
    return 1.0 - math.sqrt(((a - b) ** 2 + (a - c) ** 2) / (2.0 * a * a))


def pc_call_bases_fuzzy(separated: np.ndarray, shifts,
                        window: int = GREEDY_WINDOW,
                        min_frac: float = GREEDY_MIN_FRAC,
                        norm_window: int = GREEDY_NORM_WINDOW,
                        region: Optional[Tuple[int, int]] = None,
                        base_letters: Tuple[str, ...] = DEFAULT_BASE_OF_DYE,
                        signal: str = 'area',
                        split: bool = True) -> Tuple[np.ndarray, str, List]:
    """Greedy caller + 0x12140 1-vs-2 double-base split refinement.

    Runs the proven greedy caller, then feeds the picked peaks to the
    faithful port of the DLL's per-base classifier (cimarron_peakfit_12140).
    Peaks whose rounded centroid == 2 (double band) with a strong per-scan
    signal (arg6 > 20/17, as in the DLL caller) are split into an extra base
    from the next shoulder peak of the normalized envelope.

    ``signal`` selects the per-peak intensity feature ('area' = integrated
    peak area, stable across the lane since height falls as width grows;
    'height' = raw peak value)."""
    n = len(separated)
    shifted_all = [dsp_shift_channel(separated[:, ch], int(shifts[ch]))
                   for ch in range(4)]
    normed = np.empty_like(separated)
    for ch in range(4):
        shifted = shifted_all[ch]
        rolled = maximum_filter1d(np.clip(shifted, 0, None),
                                  size=max(3, int(norm_window)),
                                  mode='nearest')
        rolled = np.where(rolled > 0, rolled, 1.0)
        normed[:, ch] = shifted / rolled
    comb = normed.max(axis=1)
    start, stop = 0, n
    if region is not None and int(region[1]) > int(region[0]):
        start, stop = max(0, int(region[0])), min(n, int(region[1]))
    else:
        start = pc_signal_onset(separated, onset_frac=0.05, smooth=40)
    if start >= stop:
        return np.array([], dtype=np.int64), '', []

    def _pick_signal(ch, p):
        if signal == 'area':
            w = max(int(_peak_halfmax_width(shifted_all[ch], int(p))), 2)
            lo, hi = max(0, int(p) - w), min(n, int(p) + w + 1)
            base = float(np.min(shifted_all[ch][lo:hi]))
            return float(np.sum(shifted_all[ch][lo:hi]) - base * (hi - lo))
        return float(shifted_all[ch][int(p)])

    positions, sequence, _ = pc_call_bases_greedy(
        separated, shifts, window=window, min_frac=min_frac,
        norm_window=norm_window, region=region, base_letters=base_letters)
    if len(positions) == 0:
        return positions, sequence, []

    # Classifier inputs from the greedy picks.
    m = len(positions)
    arg2 = np.empty(m, dtype=float)
    arg3 = np.empty(m, dtype=float)
    arg4 = np.empty(m, dtype=float)
    arg5 = np.empty(m, dtype=float)
    arg6 = np.empty(m, dtype=float)
    for i in range(m):
        p = int(positions[i])
        ch = int(np.argmax(normed[p]))
        arg2[i] = _pick_signal(ch, p)
        arg6[i] = float(shifted_all[ch][p])
    for i in range(m):
        arg3[i] = min(arg2[i], arg2[min(i + 1, m - 1)],
                      arg2[min(i + 2, m - 1)])
        arg4[i] = float(positions[min(i + 1, m - 1)] - positions[i])
        arg5[i] = float(positions[i] - positions[max(0, i - 1)])
    col1, col2 = cimarron_peakfit_12140(
        positions.astype(float) + 1.0, arg2, arg3, arg4, arg5, arg6)

    # DLL caller: v = col1 +/- 0.5 (sign of col1), rounded = ftol(v).
    picks = list(map(int, positions))
    letters = list(sequence)
    inten = list(arg2)
    insert: List[Tuple[int, int, str, float]] = []
    for i in range(m):
        v = col1[i] + (0.5 if col1[i] > 0 else -0.5)
        rnd = _ftol(v)
        if rnd == 2 and arg6[i] > 20.0 / 17.0 and split:
            lo, hi = max(0, picks[i] - int(window)), min(n, picks[i] + int(window) + 1)
            band = comb[lo:hi].copy()
            pk = int(np.argmax(band)) + lo
            if pk == picks[i]:                 # find next shoulder
                band2 = band.copy()
                band2[pk - lo] = -1.0
                pk = int(np.argmax(band2)) + lo
            if pk != picks[i] and comb[pk] >= min_frac * comb[picks[i]]:
                ch2 = int(np.argmax(normed[pk]))
                insert.append((pk, ch2, base_letters[ch2],
                               _pick_signal(ch2, pk)))
    if insert:
        for pk, ch2, base, iv in insert:
            picks.append(pk)
            letters.append(base)
            inten.append(iv)
        order = np.argsort(picks)
        picks = [picks[k] for k in order]
        letters = [letters[k] for k in order]
        inten = [inten[k] for k in order]
    return (np.array(picks, dtype=np.int64), ''.join(letters),
            [float(x) for x in inten])


def pc_nw_identity(query: str, reference: str, match: int = 1,
                   mismatch: int = -1, gap: int = -2, max_len: int = 6000
                   ) -> float:
    """Global Needleman-Wunsch alignment identity (%) between two base-letter
    strings (vectorized port of V15 pc_nw_identity)."""
    q = query[:max_len]
    r = reference[:max_len]
    m, n = len(q), len(r)
    if m == 0 or n == 0:
        return 0.0
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


def pc_reference_accuracy(query: str, reference: str, match: int = 1,
                          mismatch: int = -1, gap: int = -2,
                          max_len: int = 6000) -> Tuple[int, int, float]:
    """Matched-bases / reference-length accuracy: (matched, total_ref, pct)
    where pct = 100 * matched / len(reference) after a global NW alignment
    (port of V15 pc_reference_accuracy)."""
    q = query[:max_len]
    r = reference[:max_len]
    m, n = len(q), len(r)
    if m == 0 or n == 0:
        return 0, n, 0.0
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
    return matched, n, (100.0 * matched / n if n else 0.0)


# --------------------------------------------------------------------------- #
# Smith-Waterman local alignment (SW / swwalk_) - used for 3.12a aligned variant
# --------------------------------------------------------------------------- #
def _smith_waterman(a: str, b: str, match: int = 2, mismatch: int = -3,
                    gap: int = -4) -> Tuple[str, str, int]:
    """Minimal SW local alignment (mirrors SW::sw_/swwalk_/concensus).

    Returns aligned a, aligned b (with gaps), best score.
    Used by the '3.12a' aligned variant to realign the called sequence to its
    highest-confidence template region and trim low-quality ends (SSNODE start/stop)."""
    n, m = len(a), len(b)
    H = np.zeros((n + 1, m + 1), dtype=int)
    tb = np.zeros((n + 1, m + 1), dtype=np.int8)  # 0 diag / 1 up / 2 left
    best, bi, bj = 0, 0, 0
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            diag = H[i - 1, j - 1] + (match if a[i - 1] == b[j - 1] else mismatch)
            up = H[i - 1, j] + gap
            left = H[i, j - 1] + gap
            if diag >= up and diag >= left:
                H[i, j], tb[i, j] = diag, 0
            elif up >= left:
                H[i, j], tb[i, j] = up, 1
            else:
                H[i, j], tb[i, j] = left, 2
            if H[i, j] >= best:
                best, bi, bj = H[i, j], i, j
    # trace back
    i, j = bi, bj
    a_, b_ = [], []
    while i > 0 and j > 0 and H[i, j] > 0:
        if tb[i, j] == 0:
            a_.append(a[i - 1]); b_.append(b[j - 1]); i -= 1; j -= 1
        elif tb[i, j] == 1:
            a_.append(a[i - 1]); b_.append('-'); i -= 1
        else:
            a_.append('-'); b_.append(b[j - 1]); j -= 1
    return ''.join(reversed(a_)), ''.join(reversed(b_)), best


# --------------------------------------------------------------------------- #
# Stage 3-4: peak detection + BandStat
# --------------------------------------------------------------------------- #
def _width_ratio_for_position(frac: float) -> float:
    """Peak width-to-spacing ratio at fractional lane position frac in [0,1)."""
    f = min(max(frac, 0.0), 1.0 - 1e-6)
    return float(np.interp(f, np.linspace(0, 1, len(_WIDTH_RATIOS)), _WIDTH_RATIOS))


def _detect_peaks(channel, signal_ref, snr_thresh=SNR_CALL_THRESHOLD,
                  min_distance=6):
    """Wvfm::putativePks + BandStat: detect peaks above SNR threshold.

    ``channel`` is the deconvolved peak signal; ``signal_ref`` is the baseline-
    subtracted trace used for the noise estimate (ObsInpSpec::widthStats).
    Mirrors V15 ``pc_detect_peaks_4ch``: per-channel ``find_peaks`` with an
    *absolute* `min_distance` (band-width scale, ~6 scans for MegaBACE) so
    closely spaced real bands are not culled."""
    noise = _noise_floor(signal_ref)
    spacing = len(channel)
    min_width = 4
    # Cimarron reject spikes narrower than a real band (FWHM >= ~4 scans).
    peaks, props = find_peaks(channel, height=snr_thresh * noise,
                              distance=max(1, int(min_distance)),
                              width=min_width)
    out: List[Peak] = []
    pw = props.get("peak_widths")
    heights = props.get("peak_heights")
    for k, p in enumerate(peaks):
        h = float(heights[k]) if heights is not None else float(channel[p])
        snr = h / noise
        w = int(pw[k]) if (pw is not None and k < len(pw)) else 4
        half = max(2, w // 2)
        lo, hi = max(0, p - half), min(len(channel), p + half + 1)
        lsum = float(channel[lo:p].sum()); rsum = float(channel[p:hi].sum())
        asym = abs(lsum - rsum) / max(lsum + rsum, 1e-9)
        bw = max(4, w)
        bl = channel[max(0, p - bw):p]; br = channel[p + 1:min(len(channel), p + bw + 1)]
        local_noise = max(_noise_floor(np.concatenate([bl, br])), 1e-9)
        buzz_snr = h / local_noise
        frac = p / max(spacing - 1, 1)
        wr = _width_ratio_for_position(frac)
        if asym > 0.55:
            continue
        if buzz_snr < snr_thresh * 1.6:
            continue
        width = float(w)
        out.append(Peak(
            idx=int(p), time=float(p), channel=-1, base='?',
            height=h, snr=snr, width=width, quality=0,
            widt_ratio=wr,
            lowv=0.0, xbnd=wr,
            ntnr=noise, insr=local_noise,
        ))
    return out


def _peak_halfmax_width(channel: np.ndarray, pos: int) -> float:
    """Full-width at half maximum (scans) around a peak at ``pos``."""
    n = len(channel)
    if n == 0:
        return 0.0
    pos = int(np.clip(pos, 0, n - 1))
    h = channel[pos]
    if h <= 0:
        return 0.0
    half = h / 2.0
    lo = pos
    while lo > 0 and channel[lo] > half:
        lo -= 1
    hi = pos
    while hi < n - 1 and channel[hi] > half:
        hi += 1
    return float(max(hi - lo, 1))


# --------------------------------------------------------------------------- #
# Mobility table (lower-bound lookup over a size ladder)
# --------------------------------------------------------------------------- #
def mobility_lookup(time: float, times: np.ndarray, sizes: np.ndarray) -> Tuple[float, int]:
    """Mobility::search: lower-bound match of a migration time onto the size
    standard ladder (70-entry table; matches largest standard <= time)."""
    if len(times) == 0:
        return float(time), -1
    if time <= times[0]:
        return float(sizes[0]), 0
    if time >= times[-1]:
        return float(sizes[-1]), len(sizes) - 1
    i = int(np.searchsorted(times, time, side='right')) - 1
    return float(sizes[i]), i


# --------------------------------------------------------------------------- #
# Stage 8: Staden-Phred quality (QualCtrl::StadenQual / bspac)
# --------------------------------------------------------------------------- #
def _phred_quality(snr: float) -> int:
    """Approximate Cimarron Staden-quality from SNR.

    Cimarron's bspac maps a signal/noise ratio to a phred scale q in [0,90].
    Empirically q ~= round(10*log10(snr)) for the MegaBACE instruments; we
    clamp to the Phred+33 printable range and floor at 0."""
    if snr <= 0:
        return 0
    q = int(round(10.0 * math.log10(snr)))
    return max(0, min(QUAL_CAP, q))


# --------------------------------------------------------------------------- #
# Stage 8: RdrOut::Beautify(1,1,0,0,0)  (notes/beautify_edit.md)
# --------------------------------------------------------------------------- #
def _beautify_fft_envelope(sep: np.ndarray, bgn: int = 0, end: int = None):
    """Faithful port of csibq030012.dll RVA 0x23166 -- per-scan envelope
    normalization.

    The per-scan total signal (sum over channels) is FFT low-pass filtered
    with a 1/129 boxcar kernel (width ~257), then every channel at scan t is
    multiplied by ``NN / filtered(t)`` (NN = 2^ceil(log2(span+128))).  This
    removes the lane-wide intensity decay (bands broaden / peak height falls
    while integrated area ~ constant), i.e. normalizes to dye mole fraction.
    Outputs <= 1.0 are soft-saturated through atan(1.5574*x).

    Returns a modified copy of ``sep``.  Because the per-scan factor is common
    to all channels, per-scan argmax (and thus greedy calls) are unchanged."""
    sep = np.asarray(sep, dtype=float).copy()
    n = len(sep)
    if end is None:
        end = n - 1
    bgn = max(0, int(bgn))
    end = min(n - 1, int(end))
    span = end - bgn + 1
    if span <= 0:
        return sep
    nn = 2 ** math.ceil(math.log2(span + 128))
    wave = sep[bgn:end + 1].sum(axis=1)          # per-scan total signal
    w = np.zeros(nn, dtype=complex)
    w[:span] = wave
    c = 1.0 / 129.0
    kern = np.zeros(nn, dtype=complex)
    kern[:129] = c
    kern[-128:] = c
    flt = np.real(np.fft.ifft(np.fft.fft(w) * np.fft.fft(kern)))
    eps = 2.220446049250313e-16
    for k in range(span):
        env = nn / (eps + flt[k])
        t = bgn + k
        for ch in range(4):
            v2 = sep[t, ch] * env
            if v2 <= 1.0:
                v2 = math.atan(1.5574 * v2)
            sep[t, ch] = v2
    return sep


def _beautify_neg_floor(sep: np.ndarray, bgn: int = 0, end: int = None):
    """Faithful port of csibq030012.dll RVA 0x2346c -- per-channel negative
    floor: if a channel dips below 0, scale all its negative values so the
    deepest trough is pinned at -0.02 (suppresses baseline undershoot)."""
    sep = np.asarray(sep, dtype=float).copy()
    n = len(sep)
    if end is None:
        end = n - 1
    bgn = max(0, int(bgn))
    end = min(n - 1, int(end))
    for ch in range(4):
        seg = sep[bgn:end + 1, ch]
        mn = float(seg.min())
        if mn < 0.0:
            scale = -0.02 / mn
            neg = seg < 0.0
            seg[neg] = seg[neg] * scale
    return sep


# --------------------------------------------------------------------------- #
# Core engine
# --------------------------------------------------------------------------- #
class Cimarron312:
    """Pure-Python Cimarron 3.12 base-caller.

    Parameters
    ----------
    variant : {'3.12','3.12a','3.12e'}
        3.12   - base call (noPuff)
        3.12a  - aligned (beautify): run Smith-Waterman template-region trimming
        3.12e  - even spacing (printify): resample peaks to even spacing
    spec_sep_matrix : 4x4 np.ndarray or None
        Spectral Separation (crosstalk) matrix to invert internally
        (detected channels = M @ pure dyes; mirrors Wvfm::specSep /
        dsp_separate_channels).  Defaults to identity = "already separated".
     snr_threshold : float
        Call SNR cutoff (>= 3.0 by default).
     base_letters : tuple[str] len 4
        Map of channel index -> called base.  Defaults to the MegaBACE/ESD
        colour convention (T/G/C/A on channels 0..3); pass V15's BASE_LETTERS
        for pixel-identical comparison.
    """

    def __init__(self, variant: str = "3.12",
                 spec_sep_matrix: Optional[np.ndarray] = None,
                 snr_threshold: float = SNR_CALL_THRESHOLD,
                 base_letters: Tuple[str, ...] = DEFAULT_BASE_OF_DYE,
                 min_distance: int = 6,
                 baseline_method: str = PIPELINE_BASELINE_METHOD,
                 baseline_window: float = PIPELINE_BASELINE_WINDOW,
                 baseline_window2: Optional[float] = None,
                 smooth_method: str = PIPELINE_SMOOTH_METHOD,
                 smooth_window: int = PIPELINE_SMOOTH_WINDOW,
                 smooth_order: int = PIPELINE_SMOOTH_ORDER,
                 matrix_apply_point: str = PIPELINE_MATRIX_APPLY_POINT,
                 mobility_shifts=PIPELINE_MOBILITY_SHIFTS,
                 caller: str = 'greedy',
                 greedy_window: int = GREEDY_WINDOW,
                 greedy_min_frac: float = GREEDY_MIN_FRAC,
                 greedy_norm_window: int = GREEDY_NORM_WINDOW,
                 cluster_min_distance: int = 1,
                 cluster_prominence_frac: float = 0.026,
                 cluster_tolerance: int = 4,
                 cluster_min_signal_frac: float = 0.95,
                 cluster_norm_window: int = 400,
                 bgn_end_method: str = "legacy",
                 hybrid_tail_trim: int = 120,
                 fuzzy_signal: str = 'area',
                 fuzzy_split: bool = True,
                 beautify: bool = False,
                 current_fix: bool = True):
        if variant not in ("3.12", "3.12a", "3.12e"):
            raise ValueError(f"unknown Cimarron variant {variant!r}")
        if caller not in ('greedy', 'cluster', 'fuzzy'):
            raise ValueError(f"unknown caller {caller!r}")
        self.variant = variant
        # ``self.ssm`` holds the *crosstalk/bleed* matrix (detected = M @ pure
        # dyes) exactly as loaded from the run's settings.json.  It is never
        # pre-inverted here: dsp_separate_channels inverts it internally so
        # __init__ and set_spec_sep_matrix stay consistent with each other.
        self.ssm = np.asarray(spec_sep_matrix if spec_sep_matrix is not None
                              else DEFAULT_SSM.copy(), dtype=float)
        self.snr_threshold = snr_threshold
        self.base_letters = tuple(base_letters)
        self.min_distance = min_distance
        self.baseline_method = baseline_method
        self.baseline_window = baseline_window
        self.baseline_window2 = baseline_window2
        self.smooth_method = smooth_method
        self.smooth_window = smooth_window
        self.smooth_order = smooth_order
        self.matrix_apply_point = matrix_apply_point
        self.mobility_shifts = tuple(int(s) for s in mobility_shifts)
        self.caller = caller
        self.greedy_window = int(greedy_window)
        self.greedy_min_frac = float(greedy_min_frac)
        self.greedy_norm_window = int(greedy_norm_window)
        self.cluster_min_distance = int(cluster_min_distance)
        self.cluster_prominence_frac = float(cluster_prominence_frac)
        self.cluster_tolerance = int(cluster_tolerance)
        self.cluster_min_signal_frac = float(cluster_min_signal_frac)
        self.cluster_norm_window = int(cluster_norm_window)
        self.bgn_end_method = bgn_end_method
        self.hybrid_tail_trim = int(hybrid_tail_trim)
        self.fuzzy_signal = fuzzy_signal
        self.fuzzy_split = bool(fuzzy_split)
        self.beautify = bool(beautify)
        self.current_fix = bool(current_fix)
        self.current_sag_segments = 0
        self._current: Optional[np.ndarray] = None
        self.is_annotated = False
        self.separated: Optional[np.ndarray] = None   # (N,4), mobility-unshifted
        self.baseline: Optional[np.ndarray] = None    # (N,4)

    # -- 3.12 procedural API parity ---------------------------------------- #
    def set_spec_sep_matrix(self, m: np.ndarray) -> None:
        """Wvfm::ssm setter / ObsInpSpec Annotate::setCFixSts.

        ``m`` is the crosstalk (bleed) matrix (detected = M @ pure dyes); it is
        inverted internally by the separation stage, mirroring
        dsp_separate_channels / Wvfm::specSep.  (Fixed: the previous code
        inverted here *and* multiplied in _run, so __init__ and
        set_spec_sep_matrix disagreed about whether ``m`` was the matrix or its
        inverse.)"""
        m = np.asarray(m, dtype=float).reshape(4, 4)
        self.ssm = m.copy()

    def set_raw_data(self, channels: np.ndarray, time: Optional[np.ndarray] = None) -> 'Cimarron312':
        """procedural SetRawData - store 4-channel (4,N) trace."""
        self._raw = np.asarray(channels, dtype=float)
        self._time = time if time is not None else np.arange(self._raw.shape[1], dtype=float)
        return self

    def set_num_samples(self, n: int) -> None:
        self._n = int(n)

    def set_current(self, current: Optional[np.ndarray]) -> 'Cimarron312':
        """CSIBQWrap::setCurrent parity - feed the run-current trace (per .rsd
        record col 0, ~66 uA decaying).  Used by Wvfm::fixCurrent for the
        current-sag migration correction when ``current_fix`` is enabled."""
        self._current = None if current is None else np.asarray(current, dtype=np.float64)
        return self

    # -- core run ---------------------------------------------------------- #
    def call(self, channels: np.ndarray,
             time: Optional[np.ndarray] = None,
             current: Optional[np.ndarray] = None) -> CallResult:
        if current is not None:
            self.set_current(current)
        return self._run(np.asarray(channels, dtype=float), time)

    def call_separated(self, separated: np.ndarray,
                       time: Optional[np.ndarray] = None) -> CallResult:
        """Peak-call an *already deconvolved* trace, skipping the DSP pipeline.

        Accepts the separated trace in either (4,N) or (N,4) orientation; the
        per-channel mobility shifts are still applied (self.mobility_shifts)
        exactly as in the full pipeline.  Returns a CallResult whose peak
        positions are in the scan coordinate frame of ``separated``."""
        sep = np.asarray(separated, dtype=float)
        if sep.ndim != 2 or min(sep.shape) < 4:
            raise ValueError("need a separated trace of shape (4,N) or (N,4)")
        if sep.shape[0] == 4 and sep.shape[1] >= 4:
            sep = sep.T                       # -> (N,4)
        if time is None:
            time = np.arange(sep.shape[0], dtype=float)
        self._raw = sep.T
        self._time = time
        self.separated = sep
        self.baseline = np.zeros_like(sep)
        return self._call_peaks(sep, time)

    def _run(self, raw: np.ndarray, time: Optional[np.ndarray]) -> CallResult:
        if raw.ndim != 2 or min(raw.shape) < 4:
            raise ValueError("need a (4,N) or (N,4) array of 4 dye channels")
        if raw.shape[0] == 4 and raw.shape[1] >= 4:
            raw = raw.T                       # -> (N,4) for the pipeline
        if time is None:
            time = np.arange(raw.shape[0], dtype=float)

        # Wvfm::fixCurrent runs FIRST, on the raw trace (before baseline/SSM),
        # using the run-current recorded in the .rsd (stage 0 of the DLL's
        # basecall procedure at 0x1fa4d).  No-op on well-behaved runs.
        if self.current_fix and self._current is not None \
                and len(self._current) == raw.shape[0]:
            raw_c, cur_c, n_sag = wvfm_fix_current(raw, self._current)
            self.current_sag_segments = int(n_sag)
            if n_sag:
                raw = raw_c
                self._current = cur_c

        self.set_raw_data(raw.T, time)

        # Stage 1+2: baseline subtract -> smooth -> SSM-deconvolve (the proven
        # V15 order).  Mobility shifts are applied only at peak-call time so
        # baseline/smoothing/matrix all operate on the aligned signal.
        bl, corr, sm, separated = dsp_full_pipeline(
            raw, self.mobility_shifts,
            baseline_method=self.baseline_method,
            baseline_window=self.baseline_window,
            smooth_method=self.smooth_method,
            smooth_window=self.smooth_window,
            smooth_order=self.smooth_order,
            matrix=self.ssm,
            baseline_window2=self.baseline_window2,
            matrix_apply_point=self.matrix_apply_point)
        self.baseline = bl
        self.separated = separated
        return self._call_peaks(separated, time, raw)

    def _call_peaks(self, separated: np.ndarray,
                    time: np.ndarray, raw: Optional[np.ndarray] = None
                    ) -> CallResult:
        """Stages 3-9 on the (N,4) separated trace: peak call -> BandStat ->
        quality -> variants (3.12a trim / 3.12e spacing / beautify)."""
        if self.bgn_end_method in ("cimarron", "perbase", "histogram", "hybrid"):
            src = raw if raw is not None else separated
            method = "perbase" if self.bgn_end_method in ("cimarron", "hybrid") \
                else self.bgn_end_method
            bgn, end = cimarron_bgn_end(src, method=method)
            if self.bgn_end_method == "hybrid":
                # Best-of-both region: legacy onset (DLL basefinder start) with
                # the perbase end trimmed by hybrid_tail_trim scans.  The
                # perbase tail detector never cuts real bases (mean ~186 scans
                # past the last ref peak) but is ~60 scans looser than the
                # optimal per-well cut; trimming recovers most of that slack.
                leg_start = pc_signal_region(separated)[0]
                start = int(leg_start)
                end = max(start, int(end) - self.hybrid_tail_trim)
                bgn, end = start, end
            region = (max(0, bgn - 1), max(bgn, min(len(separated), end)))
        else:
            region = pc_signal_region(separated)
        if self.beautify:
            bl = region if (region is not None and region[1] > region[0]) else (0, len(separated) - 1)
            separated = _beautify_fft_envelope(separated, bl[0], bl[1] - 1)
            separated = _beautify_neg_floor(separated, bl[0], bl[1] - 1)
        if self.caller == 'cluster':
            positions, sequence, _ = self._cluster_call(separated, region)
        elif self.caller == 'fuzzy':
            positions, sequence, _ = pc_call_bases_fuzzy(
                separated, self.mobility_shifts,
                window=self.greedy_window,
                min_frac=self.greedy_min_frac,
                norm_window=self.greedy_norm_window,
                region=region,
                base_letters=self.base_letters,
                signal=self.fuzzy_signal,
                split=self.fuzzy_split)
        else:
            positions, sequence, _ = pc_call_bases_greedy(
                separated, self.mobility_shifts,
                window=self.greedy_window,
                min_frac=self.greedy_min_frac,
                norm_window=self.greedy_norm_window,
                region=region,
                base_letters=self.base_letters)

        shifted_all = [dsp_shift_channel(separated[:, ch],
                                         int(self.mobility_shifts[ch]))
                       for ch in range(4)]
        n = len(separated)
        lead_n = max(int(n * 0.02), 1)
        ch_noise = [max(_noise_floor(shifted_all[ch][:lead_n]), 1e-6)
                    if lead_n >= 5 else 1e-6 for ch in range(4)]

        allpk: List[Peak] = []
        for pos, base in zip(positions, sequence):
            vals = [float(shifted_all[ch][pos]) for ch in range(4)]
            ch = int(np.argmax(vals))
            height = max(vals[ch], 0.0)
            snr = height / ch_noise[ch] if ch_noise[ch] > 0 else 0.0
            allpk.append(Peak(
                idx=int(pos), time=float(pos), channel=ch, base=base,
                height=height, snr=snr,
                width=_peak_halfmax_width(shifted_all[ch], int(pos)),
                quality=_phred_quality(snr)))

        # Stage 6 (3.12a): SW template-region trimming of the consensus.
        if self.variant == "3.12a" and len(allpk) >= 6:
            al, _, score = _smith_waterman(sequence, sequence)
            lo, hi = 0, len(sequence)
            if score > 0:
                for i in range(len(sequence)):
                    if allpk[i].quality >= 20:
                        lo = i; break
                for i in range(len(sequence) - 1, -1, -1):
                    if allpk[i].quality >= 20:
                        hi = i + 1; break
                allpk = allpk[lo:hi]
                sequence = ''.join(p.base for p in allpk)

        # Stage 9 (RdrOut): build quality string, clip, beautify (N for low qual).
        quals = [p.quality for p in allpk]
        qual_str = ''.join(chr(max(0, min(126, q + 33))) for q in quals)

        # Beautify: mask bases with snr < threshold as 'N'.
        if self.variant in ("3.12a", "3.12e"):
            seq_chars = []
            for p, q in zip(allpk, quals):
                if p.snr < self.snr_threshold or q < 10:
                    seq_chars.append('N')
                else:
                    seq_chars.append(p.base)
            sequence = ''.join(seq_chars)

        # 3.12e (printify / even spacing): resample peak times to even grid.
        if self.variant == "3.12e" and len(allpk):
            for k, p in enumerate(allpk):
                p.time = float(k)  # uniform spacing

        self.is_annotated = True
        return CallResult(sequence=sequence, quality=qual_str, peaks=allpk,
                          trace_time=time)

    def _cluster_call(self, separated: np.ndarray, region
                      ) -> Tuple[np.ndarray, str, List]:
        """Per-channel find_peaks caller with IUPAC ambiguity merging
        (port of V15 pc_call_bases_with_shifts).  Exposed for parity with the
        DLL's per-channel semantics; the greedy caller is the default."""
        from scipy.signal import find_peaks as _fp
        n = len(separated)
        shifted_all = [dsp_shift_channel(separated[:, ch],
                                         int(self.mobility_shifts[ch]))
                       for ch in range(4)]
        channels: List[Tuple[int, int, float]] = []
        for ch in range(4):
            shifted = shifted_all[ch]
            rolled = maximum_filter1d(np.clip(shifted, 0, None),
                                      size=max(3, self.cluster_norm_window),
                                      mode='nearest')
            rolled = np.where(rolled > 0, rolled, 1.0)
            norm_ch = shifted / rolled
            scale = np.percentile(np.clip(norm_ch, 0, None), 99.5)
            prom = max(scale * self.cluster_prominence_frac, 1e-9) if scale > 0 else 1e-9
            peaks, _ = _fp(norm_ch, distance=max(1, self.cluster_min_distance),
                           prominence=prom)
            for p in peaks:
                channels.append((int(p), ch, float(shifted[p])))
        channels.sort(key=lambda c: c[0])
        start, stop = (0, n)
        if region is not None and int(region[1]) > int(region[0]):
            start, stop = max(0, int(region[0])), min(n, int(region[1]))
        channels = [c for c in channels if start <= c[0] < stop]
        positions: List[int] = []
        letters: List[str] = []
        inten: List[float] = []
        i = 0
        while i < len(channels):
            j = i
            cluster = [channels[i]]
            cluster_start = channels[i][0]
            while j + 1 < len(channels) and \
                    channels[j + 1][0] - cluster_start <= self.cluster_tolerance:
                j += 1
                cluster.append(channels[j])
            max_signal = max(c[2] for c in cluster)
            min_signal = max_signal * self.cluster_min_signal_frac
            valid = [c for c in cluster if c[2] >= min_signal]
            best = max(valid, key=lambda c: c[2])
            positions.append(best[0])
            letters.append(self.base_letters[best[1]])
            inten.append(best[2])
            i = j + 1
        return (np.array(positions, dtype=np.int64),
                ''.join(letters), inten)

    # -- procedural report parity (RdrOut / Mobility / Annotate) ----------- #
    def report_sequence(self) -> str:
        return self._last.sequence if hasattr(self, '_last') else ''

    __call__ = call  # convenience


def call_basecaller(channels: np.ndarray, time: Optional[np.ndarray] = None,
                    variant: str = "3.12", **kw) -> CallResult:
    """Module-level convenience mirroring CSIBQWrap::call()."""
    eng = Cimarron312(variant=variant, **kw)
    return eng.call(channels, time)


# --------------------------------------------------------------------------- #
# Raw IO: .rsd (MegBACE binary) + .esd (reference basecall)
# --------------------------------------------------------------------------- #
RSD_RECORD = struct.Struct("<IIIII")  # Current, Ch1, Ch2, Ch3, Ch4 (uint32)


def read_rsd(path: str, with_current: bool = False):
    """Read a MegBACE .rsd binary file -> (channels[4,N], scans[0..N-1]) or,
    when ``with_current`` is True, (channels[4,N], scans, current[N]) with the
    run-current trace (record col 0, ~66 uA decaying under constant voltage).

    Mirrors extract_training_data.parse_rsd: 20-byte records of
    (Current, Channel1..4) as little-endian uint32, truncated at the first
    record whose any field exceeds 200000 (the metadata tail).  Channel1..4
    map to the T/G/C/A dyes (BASE_OF_DYE) per the instrument's "Base order:
    TGCA" header."""
    with open(path, 'rb') as fh:
        blob = fh.read()
    n = len(blob) // RSD_RECORD.size
    recs = np.frombuffer(blob[:n * RSD_RECORD.size],
                         dtype=np.dtype([("cur", "<u4"),
                                         ("ch1", "<u4"), ("ch2", "<u4"),
                                         ("ch3", "<u4"), ("ch4", "<u4")]))
    # boundary: first record with any field > MAX_DATA_VALUE (metadata tail)
    big = (recs["ch1"] > 200000) | (recs["ch2"] > 200000) | (recs["ch3"] > 200000) \
        | (recs["ch4"] > 200000)
    if big.any():
        recs = recs[:int(np.argmax(big))]
    channels = np.vstack([recs["ch1"], recs["ch2"],
                          recs["ch3"], recs["ch4"]]).astype(np.float64)
    scans = np.arange(len(channels[0]), dtype=np.float64)
    if with_current:
        current = recs["cur"].astype(np.float64)
        return channels, scans, current
    return channels, scans


def read_esd(path: str) -> dict:
    """Read an Abbott/CSR .esd reference basecall using the project's
    extract_training_data parser (verified against MegaBACE DLL output)."""
    from extract_training_data import parse_esd
    d = parse_esd(path)
    out = {}
    out["sequence"] = d["sequence"]
    out["peak_positions"] = d["peak_positions"].copy()
    out["quality_scores"] = d["quality_scores"].copy()
    out["fwhm_values"] = d.get("fwhm_values", d.get("quality_index", np.array([]))).copy()
    return out


def _match_sequences(calls: str, ref: str):
    """Greedy 1:1 positional match fraction (matches the ESD/M13 accuracy
    metric in sequencing_gui_V15 `pc_reference_accuracy`)."""
    a, b = calls.upper().replace('N', ''), (ref or '').upper()
    matches = sum(1 for x, y in zip(a, b) if x == y)
    return matches, len(b), (100.0 * matches / len(b) if b else 0.0)


def compare_to_esd(rsd_path: str, esd_path: str, matrix=None,
                   variant: str = "3.12", snr=SNR_CALL_THRESHOLD,
                   base_letters=DEFAULT_BASE_OF_DYE, **pipeline_kw) -> dict:
    """Run Cimarron 3.12 on a raw .rsd and compare against the DLL's .esd
    reference.  Returns {sequence, ref_sequence, nw_identity_pct,
    ref_accuracy_pct, positional_pct, matched, total, n_called, n_ref,
    matrix_used}.  ``pipeline_kw`` are forwarded to Cimarron312 (baseline /
    smoothing / caller tuning)."""
    channels, scans, cur = read_rsd(rsd_path, with_current=True)
    eng = Cimarron312(variant=variant, base_letters=base_letters,
                      snr_threshold=snr, **pipeline_kw)
    if matrix is not None:
        eng.set_spec_sep_matrix(np.asarray(matrix, dtype=float))
    res = eng.call(channels, scans, current=cur)
    ref = read_esd(esd_path)
    ref_seq = ref.get("sequence", "")
    clean = res.sequence.upper().replace('N', '')
    m, t, pct = _match_sequences(clean, ref_seq)
    nw = pc_nw_identity(clean, ref_seq)
    _, ref_total, acc = pc_reference_accuracy(clean, ref_seq)
    # positional match of called peak positions vs the ESD peak positions
    # within a 6-scan tolerance (the DLL's own coordinate frame).
    esd_match = 0.0
    if res.peaks and ref.get("peak_positions") is not None:
        mine = sorted(float(p.time) for p in res.peaks)
        esd = sorted(float(x) for x in ref["peak_positions"])
        i = j = cnt = 0
        while i < len(mine) and j < len(esd):
            if abs(mine[i] - esd[j]) <= 6:
                cnt += 1; i += 1; j += 1
            elif mine[i] < esd[j]:
                i += 1
            else:
                j += 1
        esd_match = 100.0 * cnt / len(esd) if esd else 0.0
    return {
        "sequence": res.sequence, "ref_sequence": ref_seq,
        "nw_identity_pct": nw, "ref_accuracy_pct": acc,
        "positional_pct": pct, "esd_match_pct": esd_match,
        "matched": m, "total": ref_total, "n_called": len(res.peaks),
        "n_ref": len(ref.get("peak_positions", [])),
        "matrix_used": bool(matrix is not None),
    }


if __name__ == "__main__":
    # Smoke test.  Prefer the real M13 pair (this repo's A01.rsd/A01.esd) since
    # it exercises the full pipeline against the DLL's own basecall; otherwise
    # fall back to a synthetic crosstalk-bleed run.
    here = os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else '.'
    rsd = os.path.join(here, 'MB1000_M13_DT', 'A01.rsd')
    esd = os.path.join(here, 'Claude 030826',
                       'files/MB1000_M13_DT/MB1000_M13_DT_Cp1_530_MD1', 'A01.esd')
    if os.path.exists(rsd) and os.path.exists(esd):
        print(f"A01.rsd/A01.esd present - running real-data smoke test")
        channels, scans, cur = read_rsd(rsd, with_current=True)
        ref = read_esd(esd)["sequence"]
        # Prefer the per-run tuned matrix (A01_settings.json) over the generic
        # ET-dye bleed matrix - the tuned one separates this plate correctly.
        matrix = ETDYE_CROSSTALK
        sfile = os.path.join(here, 'A01_settings.json')
        if os.path.exists(sfile):
            import json as _json
            sdata = _json.load(open(sfile))
            if sdata.get("matrix") is not None:
                matrix = np.asarray(sdata["matrix"], dtype=float)
                eng = Cimarron312(
                    variant="3.12", spec_sep_matrix=matrix,
                    baseline_method=sdata.get("baseline_method", "AsyLS"),
                    baseline_window=sdata.get("baseline_window", 50000),
                    baseline_window2=sdata.get("baseline_window2"),
                    smooth_method=sdata.get("smooth_method", "Butterworth"),
                    smooth_window=sdata.get("smooth_window", 5),
                    smooth_order=sdata.get("smooth_order", 9),
                    matrix_apply_point=sdata.get("matrix_apply_point", "corrected"),
                    mobility_shifts=sdata.get("mobility_shifts", (5, 11, 10, 10)))
            else:
                eng = Cimarron312(variant="3.12", spec_sep_matrix=matrix)
        else:
            eng = Cimarron312(variant="3.12", spec_sep_matrix=matrix)
        r = eng.call(channels, scans, current=cur)
        clean = ''.join(c for c in r.sequence if c != 'N')
        nw = pc_nw_identity(clean, ref)
        _, _, acc = pc_reference_accuracy(clean, ref)
        print(f"3.12: peaks={len(r.peaks)} nw={nw:.1f}% acc={acc:.1f}% "
              f"(ref={len(ref)} bases) current_fix_sags={eng.current_sag_segments}")
        print(f"called[:60]={r.sequence[:60]!r}")
        print(f"ref   [:60]={ref[:60]!r}")
    else:
        # Synthetic fallback: bleed each dye into the other channels through the
        # canonical ET-dye crosstalk matrix and confirm separation recovers it.
        rng = np.random.default_rng(0)
        N = 2000
        t = np.arange(N, dtype=float)
        truth = "GACTGACTG"
        pos = [200, 340, 480, 620, 780, 920, 1060, 1240, 1400]
        ch = {b: np.zeros(N) for b in 'ACGT'}
        sigma = 3.5
        amp = 120.0
        for p, b in zip(pos, truth):
            ch[b] += amp * np.exp(-((t - p) ** 2) / (2 * sigma ** 2))
        pure = np.vstack([ch[base] for base in DEFAULT_BASE_OF_DYE])
        pure[:, :150] = 0.0
        pure[:, 1600:] = 0.0
        pure += rng.normal(0, 0.5, pure.shape)
        observed = (ETDYE_CROSSTALK @ pure).T
        observed = observed + rng.normal(0, 0.5, observed.shape)
        for variant in ("3.12", "3.12a", "3.12e"):
            r = call_basecaller(observed, t, variant=variant,
                                spec_sep_matrix=ETDYE_CROSSTALK)
            called = ''.join(c for c in r.sequence if c != 'N')
            nw = pc_nw_identity(called, truth)
            print(f"{variant}: seq={r.sequence!r} nw={nw:.0f}% peaks={len(r.peaks)}")
