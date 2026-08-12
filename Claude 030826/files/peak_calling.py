"""Independent peak-detection basecalling and mobility-shift estimation.

Everything the GUI previously reported as "ESD match %" reused ESD's own
called peak positions to sample the separated trace - that only tests
whether the right channel is on top *at a position ESD already told you
was a peak*. It can't fail on peak-count drift and doesn't exercise a real
peak finder at all.

`call_bases()` below is a genuine, self-contained caller: it finds its own
peaks from the separated trace and only afterwards gets compared against
the ESD sequence via alignment. That comparison is the fair one to
optimize against.
"""
import numpy as np
from scipy.signal import find_peaks

BASE_LETTERS = {0: 'T', 1: 'G', 2: 'C', 3: 'A'}


# ---------------------------------------------------------------------------
# Peak normalization
# ---------------------------------------------------------------------------
def normalize_peaks(separated, mode='total_signal', window=800):
    """Normalize the 4-channel separated trace so peak heights are
    comparable across channels and across the length of the run.

    mode:
      'channel_max'  - divide each channel by its own global max. Simple,
                       but does nothing about within-run signal decay.
      'total_signal' - divide each scan by the sum across all 4 channels
                       at that scan. Removes overall intensity drift while
                       preserving the *relative* dye ratio at each scan,
                       which is closer to what MegaBACE reports as
                       normalized peak height.
      'rolling_local' - divide by a rolling max (over `window` scans) of
                       the summed signal, so normalization tracks the slow
                       loss of signal amplitude late in a long run instead
                       of using one global scale for the whole trace.
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
        from scipy.ndimage import maximum_filter1d
        total = x.sum(axis=1)
        local_max = maximum_filter1d(total, size=max(int(window), 3), mode='nearest')
        local_max = np.clip(local_max, np.percentile(total, 50) * 0.05 + 1e-9, None)
        target = np.median(local_max)
        return x / local_max[:, np.newaxis] * target
    else:
        raise ValueError(f'Unknown normalization mode: {mode}')


# ---------------------------------------------------------------------------
# Independent peak detection + basecalling
# ---------------------------------------------------------------------------
def detect_peaks_4ch(separated, min_distance=6, prominence_frac=0.02, width=None):
    """Run find_peaks independently on each of the 4 channels of the
    (already normalized) separated trace, then merge into one ordered list
    of (position, channel) picking the tallest candidate within
    `min_distance` scans whenever two channels both claim a peak there -
    this is the actual base-calling step MegaBACE's own software performs;
    reusing ESD's positions (as the previous version did) skips it.

    prominence_frac is relative to each channel's own peak-height scale, so
    the detector adapts to signal amplitude instead of using one fixed
    absolute threshold for every channel/run.
    """
    x = np.clip(np.asarray(separated, dtype=np.float64), 0, None)
    candidates = []  # (position, channel, height)
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
        while j + 1 < len(candidates) and candidates[j + 1][0] - cluster[-1][0] <= min_distance:
            j += 1
            cluster.append(candidates[j])
        best = max(cluster, key=lambda c: c[2])
        merged.append(best)
        i = j + 1
    return merged  # list of (position, channel, height)


def call_bases(separated, min_distance=6, prominence_frac=0.02,
                normalize_mode='total_signal'):
    """End-to-end independent basecall: normalize -> detect peaks per
    channel -> merge -> assign letters. Returns (positions, sequence,
    heights) as (np.ndarray[int], str, np.ndarray[float])."""
    norm = normalize_peaks(separated, mode=normalize_mode)
    merged = detect_peaks_4ch(norm, min_distance=min_distance,
                               prominence_frac=prominence_frac)
    positions = np.array([m[0] for m in merged], dtype=np.int64)
    sequence = ''.join(BASE_LETTERS[m[1]] for m in merged)
    heights = np.array([m[2] for m in merged], dtype=np.float64)
    return positions, sequence, heights


# ---------------------------------------------------------------------------
# Alignment-based scoring (fair comparison, tolerant of peak-count drift)
# ---------------------------------------------------------------------------
def nw_identity(query, reference, match=1, mismatch=-1, gap=-2, max_len=6000):
    """Global (Needleman-Wunsch) alignment identity between two base-letter
    strings, in percent. Robust to insertions/deletions between the two
    calls, unlike position-indexed comparison, which is essential once the
    independent caller can find a different number of peaks than ESD did.
    Truncates very long sequences to keep the O(n*m) DP tractable inside an
    optimization loop; for full-length final reporting call with the whole
    read instead.
    """
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
    # Backtrack for identity count
    i, j = m, n
    matches = 0
    aligned = 0
    while i > 0 or j > 0:
        if i > 0 and j > 0 and dp[i, j] == dp[i - 1, j - 1] + (match if q[i - 1] == r[j - 1] else mismatch):
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


# ---------------------------------------------------------------------------
# Mobility shift auto-estimation
# ---------------------------------------------------------------------------
def estimate_mobility_shifts(raw, ref_channel=3, max_shift=60, smooth=15):
    """Cross-correlate each channel's smoothed envelope against a reference
    channel and return the integer scan shift (in dsp_core's convention,
    ready to feed straight into apply_mobility_shifts) that best aligns it.

    IMPORTANT PHYSICAL CAVEAT: this only recovers a meaningful shift when
    the channels actually share peak timing, i.e. on a mobility/matrix
    calibration standard run where the same DNA fragments are labeled with
    each of the 4 dyes so every channel sees a peak at (almost) the same
    physical positions, offset only by dye mobility. On an ordinary
    sequencing read, each channel encodes a *different* set of bases at
    different times - there's no reason channel-A's peaks and channel-T's
    peaks should line up at all, so cross-correlating them will converge
    on whatever spurious alignment happens to maximize overlap (often the
    search boundary) rather than the true dye-mobility lag. Only trust
    this on calibration-standard data; for ordinary reads, mobility shift
    is a fixed instrument/dye-chemistry constant better set once (from a
    calibration run, or MegaBACE's own mobility file if you have it) and
    left alone, which is why the GUI sliders default to persisting the
    last value rather than re-deriving it per read.
    """
    from scipy.ndimage import uniform_filter1d
    raw = np.asarray(raw, dtype=np.float64)
    n = len(raw)
    # Remove slow drift first (large-window rolling mean as a crude
    # baseline) - otherwise the correlation is dominated by the shared
    # low-frequency trend common to all channels rather than by the narrow
    # peaks that actually carry the mobility-lag information.
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
        # Full cross-correlation restricted to +/- max_shift lags.
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
        # best_lag satisfies ref[t] ~ sig[t - best_lag], i.e. sig already
        # equals ref shifted by -best_lag in dsp_core's shift_channel
        # convention - so best_lag itself is exactly the correction to
        # feed into apply_mobility_shifts to bring ch onto the reference.
        shifts[ch] = best_lag
    return shifts
