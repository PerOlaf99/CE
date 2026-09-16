#!/usr/bin/env python3
"""cepstral.py - patent Steps 2-4: windowed nfeeder real-cepstral blind
deconvolution (Stockham/Ives) + envelope/zero-crossing FSM peak detect.

Implements the Cimarron patent pipeline for one trace:
  nfeeder window (2048 scans, step ~1900, overlap ~148)  ->
  per window: band-spacing estimate (40th percentile)     ->
             FBW (filter band width) from spacing          ->
             iterative real-cepstral blind deconvolution  ->
             extra-normalization (overshoot attenuation)  ->
  RdrOut overlap stitching                                     ->
  FSM peak detect (envelope / local-max state machine)         ->

Reference for scoring: ESD record list (peak_positions + sequence).

API:
  deconvolve(separated, window=2048, step=1900, iters=3,
             spacing_method="40pct") -> (N, C) sharpened lanes
  detect(separated_sharp, region=None) -> (positions, sequence, intensities)
  run(separated, ...) -> single-call: deconvolve + detect
"""
from typing import Optional, Sequence, Tuple

import numpy as np

# --------------------------------------------------------------------------- #
# Step 3a: band-spacing estimate (40th percentile of inter-band distances)
# --------------------------------------------------------------------------- #

def _envelope(lanes: np.ndarray) -> np.ndarray:
    """Cross-channel envelope = pointwise max over lanes (the DLL's detector
    envelope)."""
    return np.asarray(lanes, dtype=np.float64).max(axis=1)


def _minmax_norm(x: np.ndarray) -> np.ndarray:
    """Normalize to [0, 1] (decouples spacing from amplitude)."""
    x = np.asarray(x, dtype=np.float64)
    lo, hi = float(x.min()), float(x.max())
    if hi - lo < 1e-12:
        return np.zeros_like(x)
    return (x - lo) / (hi - lo)


def _smooth_env(env: np.ndarray, half: int = 2) -> np.ndarray:
    """Light moving-average over the envelope; variant of the DLL's band
    smoothing that removes single-scan noise before measuring spacing."""
    n = len(env)
    if half <= 0 or n < 2 * half + 1:
        return env.copy()
    out = np.empty_like(env)
    cs = np.concatenate([[env[0]] * half, env, [env[-1]] * half])
    csum = np.concatenate([[0.0], np.cumsum(cs)])
    k = 2 * half + 1
    for i in range(n):
        out[i] = (csum[i + k] - csum[i]) / k
    return out


def band_spacing(env: np.ndarray, quantile: float = 0.40,
                 min_dist: int = 2) -> float:
    """Patent Step 3a: local band spacing.

    Envelope local maxima (with a minimum separation) give inter-base band
    distances; the 40th percentile of those distances is the spacing used to
    set the filter bandwidth (robust to heterozygous doubled peaks that
    inflate the upper tail)."""
    e = _smooth_env(_minmax_norm(env), half=2)
    n = len(e)
    if n < 8:
        return 8.0
    maxima = []
    for i in range(1, n - 1):
        if e[i] >= e[i - 1] and e[i] > e[i + 1] and e[i] > 0.02:
            if maxima and i - maxima[-1] < min_dist:
                # keep the taller of the two within min_dist
                last = maxima[-1]
                if e[i] > e[last]:
                    maxima[-1] = i
                continue
            maxima.append(i)
    if len(maxima) < 3:
        return 8.0
    d = np.diff(np.asarray(maxima, dtype=np.float64))
    d = d[d >= 2]                      # ignore sub-scan jitter
    if len(d) < 2:
        return 8.0
    return float(np.percentile(d, quantile * 100.0))


# --------------------------------------------------------------------------- #
# Step 3b: FBW bandpass from spacing (frequency domain)
# --------------------------------------------------------------------------- #

def fbw_filter(n: int, spacing: float, fbw_factor: float = 1.0,
               low_frac: float = 0.25, high_frac: float = 2.5) -> np.ndarray:
    """Patent Step 3b: filter band width from spacing.

    Base rate f_base = 1/spacing (cycles/scan).  The band-pass keeps a band of
    width (low_frac..high_frac)*f_base and suppresses both baseline drift
    (very low freq) and noise (above the band).  Returns a real (n,) mask for
    the magnitude spectrum (0..Nyquist), f=0 and f=Nyquist ends zeroed."""
    f = np.fft.rfftfreq(n, d=1.0)
    f0 = 1.0 / max(spacing, 1e-6)
    lo, hi = low_frac * f0, high_frac * f0
    mask = np.zeros(len(f))
    if hi <= lo:
        return mask
    sigma = (hi - lo) / 4.0 * max(fbw_factor, 0.05)
    mid = 0.5 * (lo + hi)
    mask = np.exp(-0.5 * ((f - mid) ** 2) / (sigma ** 2))
    # smooth rolloff down to DC
    mask[:int(np.argmax(f >= lo))] *= 0.0
    mask[f > high_frac * f0] = 0.0
    return mask.astype(np.float64)


# --------------------------------------------------------------------------- #
# Step 3c: iterative real-cepstral blind deconvolution (Stockham/Ives)
# --------------------------------------------------------------------------- #

def _smooth_logmag(logmag: np.ndarray, kernel: int) -> np.ndarray:
    """Moving-average (window ``kernel`` in spectrum bins) of the log
    magnitude spectrum -- the Stockham estimate of the point-spread log
    spectrum.  Kernel width ~ (spacing-dependent) so the PSF (broad, smooth
    in frequency) is captured while the spike-train ripple is left out."""
    k = max(3, int(kernel) | 1)
    if len(logmag) < k:
        k = len(logmag) // 2 * 2 + 1 if len(logmag) >= 3 else 1
    pad = k // 2
    x = np.concatenate([[logmag[0]] * pad, logmag, [logmag[-1]] * pad])
    csum = np.concatenate([[0.0], np.cumsum(x)])
    out = np.empty(len(logmag))
    for i in range(len(logmag)):
        out[i] = (csum[i + k] - csum[i]) / float(k)
    return out


def _overshoot_attenuate(sharp: np.ndarray, orig_env: np.ndarray,
                         gain: float = 1.0) -> np.ndarray:
    """Extra-normalization: clamp the deconvolved signal's overshoot to the
    original positive envelope scaled by ``gain``, zero any sign reversal."""
    s = np.asarray(sharp, dtype=np.float64)
    s = s * (float(orig_env.max()) / max(float(s.max()), 1e-12)) * gain
    np.clip(s, 0.0, max(float(orig_env.max()) * gain, 1e-9), out=s)
    return s


def deconvolve_lane(x: np.ndarray, spacing: float, iters: int = 3,
                    fbw: Optional[np.ndarray] = None,
                    kernel_factor: float = 4.0,
                    overshoot_gain: float = 1.0) -> np.ndarray:
    """Real-cepstral blind deconvolution of one lane.

    log|S(f)| = log|PSF(f)| + log|spike-train(f)|: estimate the PSF log
    spectrum as a broad moving average of the observed log spectrum, subtract
    it (whiten), apply the FBW mask, keep phase, IFFT, iterate to refine the
    PSF estimate, then attenuate overshoot."""
    x = np.asarray(x, dtype=np.float64)
    n = len(x)
    if n < 16:
        return x.copy()
    spec = np.fft.rfft(x)
    mag = np.abs(spec) + 1e-12
    logmag = np.log(mag)
    if fbw is None or len(fbw) != len(logmag):
        fbw = fbw_filter(n, spacing)
    kernel = max(3, int(round(max(len(logmag) / (kernel_factor * max(spacing, 1.0)), 3))))
    kernel = kernel | 1 if kernel % 2 == 0 else kernel
    phase = np.exp(1j * np.angle(spec))
    psf_log = _smooth_logmag(np.concatenate([
        logmag[: max(1, len(logmag) // 8)][::-1],
        logmag,
        logmag[-max(1, len(logmag) // 8):][::-1]]), kernel)[max(0, len(logmag) // 8):
                                                               len(logmag) // 8 + len(logmag)]
    whitened = logmag - psf_log
    mag_new = np.exp(np.clip(whitened, -12.0, 12.0)) * fbw
    y = np.fft.irfft(mag_new * phase, n=n)
    for it in range(1, iters):
        spec = np.fft.rfft(y)
        logmag2 = np.log(np.abs(spec) + 1e-12)
        psf_log2 = _smooth_logmag(np.concatenate([
            logmag2[:max(1, len(logmag2) // 8)][::-1],
            logmag2,
            logmag2[-max(1, len(logmag2) // 8):][::-1]]), kernel)[
            max(0, len(logmag2) // 8): len(logmag2) // 8 + len(logmag2)]
        whitened = logmag2 - psf_log2
        mag_new = np.exp(np.clip(whitened, -12.0, 12.0)) * fbw
        y = np.fft.irfft(mag_new * np.exp(1j * np.angle(spec)), n=n)
    return y


# --------------------------------------------------------------------------- #
# Step 2 + RdrOut: nfeeder windowing + overlap stitching
# --------------------------------------------------------------------------- #

def _hann_ramp(n: int) -> np.ndarray:
    w = np.hanning(n)
    return w.astype(np.float64)


def deconvolve(separated: np.ndarray, window: int = 2048, step: int = 1900,
               iters: int = 3, spacing_quantile: float = 0.40,
               fbw_factor: float = 1.0, kernel_factor: float = 4.0,
               overshoot_gain: float = 1.0, min_dist: int = 2,
               fbw_low: float = 0.25, fbw_high: float = 2.5,
               verbose: bool = False) -> np.ndarray:
    """nfeeder windowed pass + RdrOut overlap stitch.

    separated: (N, C) lanes.  windows of ``window`` scans stepping ``step``
    (~148 scan overlap); each window is deconvolved independently (band
    spacing estimated per window) and the output blended with Hann weights
    so the pass is continuous at the boundaries (RdrOut)."""
    lanes = np.asarray(separated, dtype=np.float64)
    n, c = lanes.shape
    out = np.zeros((n, c), dtype=np.float64)
    wsum = np.zeros(n, dtype=np.float64)
    win = int(window)
    stp = int(step)
    starts = list(range(0, max(1, n - win + stp), stp))
    if not starts or starts[-1] + win < n:
        starts.append(max(0, n - win))
    ramp = _hann_ramp(win) if win > 1 else np.ones(win)
    for s0 in starts:
        s1 = min(n, s0 + win)
        seg = lanes[s0:s1].copy()
        if seg.shape[0] < 32:
            continue
        env = _envelope(seg)
        sp = band_spacing(env, quantile=spacing_quantile, min_dist=min_dist)
        fbw = fbw_filter(seg.shape[0], sp, fbw_factor=fbw_factor,
                         low_frac=fbw_low, high_frac=fbw_high)
        seg_sharp = np.stack([
            deconvolve_lane(seg[:, ch], sp, iters=iters, fbw=fbw,
                            kernel_factor=kernel_factor,
                            overshoot_gain=overshoot_gain)
            for ch in range(c)], axis=1)
        w = ramp[:seg.shape[0]]
        for ch in range(c):
            out[s0:s1, ch] += seg_sharp[:, ch] * np.clip(w, 0, None)
        wsum[s0:s1] += w
    wsum = np.where(wsum > 0, wsum, 1.0)
    return out / wsum[:, None]


# --------------------------------------------------------------------------- #
# Step 4: FSM peak detect on the sharpened lanes
# --------------------------------------------------------------------------- #

def detect(separated: np.ndarray, region: Optional[Tuple[int, int]] = None,
           env_floor_frac: float = 0.05,
           min_scan: int = 2) -> Tuple[np.ndarray, str]:
    """Envelope / local-maximum FSM peak detector (DLL-port, runs on the
    deconvolved lanes)."""
    lanes = np.asarray(separated, dtype=np.float64)
    # clip ringing before peak detect: real peaks are positive-only
    lanes = np.clip(lanes, 0, None)
    from dll_peakdet import dll_peaks
    pos, seq, _ = dll_peaks(lanes, region=region, env_floor_frac=env_floor_frac,
                            min_scan=min_scan)
    return pos, seq


def run(separated: np.ndarray, window: int = 2048, step: int = 1900,
        iters: int = 3, env_floor_frac: float = 0.05,
        region: Optional[Tuple[int, int]] = None,
        **kw) -> Tuple[np.ndarray, str]:
    sharp = deconvolve(separated, window=window, step=step, iters=iters, **kw)
    return detect(sharp, region=region, env_floor_frac=env_floor_frac)


if __name__ == '__main__':
    import sys, os
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    sep = np.load(sys.argv[1] if len(sys.argv) > 1 else '/tmp/opencode/demo_sep.npy')
    pos, seq = run(sep)
    print(f'{len(pos)} peaks')