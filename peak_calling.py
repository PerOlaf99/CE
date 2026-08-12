"""Independent peak-detection basecalling and mobility-shift estimation.

Everything the GUI previously reported as "ESD match %" reused ESD's own
called peak positions to sample the separated trace - that only tests
whether the right channel is on top *at a position ESD already told you
was a peak*. It can't fail on peak-count drift and doesn't exercise a real
peak finder at all.

`call_bases()` and `pc_call_bases_with_shifts()` below are genuine,
self-contained callers: they find their own peaks from the separated trace
and only afterwards get compared against the ESD sequence via alignment.
That comparison is the fair one to optimize against.

`pc_call_bases_with_shifts` is the canonical implementation the GUI (V15)
displays and that ``optimize_params.py`` scores - it applies per-channel
mobility shifts, rolling-local normalization, a leading-baseline noise
floor, an onset cut, and IUPAC ambiguity codes. Keep this file in sync
with the GUI's copy if either changes.
"""
import numpy as np
from scipy.signal import find_peaks
from scipy.ndimage import maximum_filter1d

import dsp_core

BASE_LETTERS = {0: 'T', 1: 'G', 2: 'C', 3: 'A'}

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


def pc_signal_onset(separated, onset_frac=0.05, smooth=40, rise_sigma=4.0,
                    lead_frac=0.05, rise_window=None):
    """Find the scan index where the sample DNA signal first starts to
    *rise* above the instrument baseline, rather than where it merely
    crosses a fixed threshold. (Identical to the GUI's inlined helper.)

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
    IUPAC ambiguity codes. (Identical to the GUI's inlined copy.)

    Unlike ``call_bases``, this applies per-channel mobility shifts *after*
    baseline/smoothing/matrix, then runs ``find_peaks`` independently on
    each shifted channel. Peaks from different channels within
    ``tolerance`` scans of each other are at the same base position and
    combined using IUPAC single-letter codes (e.g. A+C -> M, A+G+T -> D).

    If ``normalize`` is True, each channel is divided by a rolling local
    maximum (window = ``norm_window`` scans) to compensate for the signal
    decay inherent in Sanger sequencing by CE - shorter fragments produce
    stronger signals, so later (longer) peaks are systematically weaker.
    Per-channel rolling normalization makes late peaks detectable at the
    same relative threshold as early ones.

    ``min_signal_frac`` sets the minimum fraction of the tallest peak's
    signal required for a channel to contribute to an ambiguous base call.
    For example, with min_signal_frac=0.25, a minor bump at 15% of the
    dominant peak's height is rejected - only genuinely overlapping signals
    (each >25% of the max) are combined into IUPAC codes. This prevents
    noise/artifact peaks under a large peak from being mis-called as
    ambiguous bases (e.g. falsely calling W instead of just A).

    Returns (positions, sequence, base_groups, intensities) where:
      positions  - scan index of each called position (midpoint of merged peaks)
      sequence   - IUPAC-coded base string
      base_groups - list of sets of base letters at each position
      intensities - dict {base_letter: height} at each position
    """
    n = len(separated)
    shifted_all = [dsp_core.shift_channel(separated[:, ch], int(shifts[ch]))
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
        peaks, _ = find_peaks(norm_ch, distance=max(1, min_distance), prominence=prom)
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


def pc_fill_in_combined_peaks(separated, shifts, positions=None,
                              min_distance=1, prominence_frac=0.02,
                              norm_window=800, fill_gap=3, fill_margin=0.2,
                              onset_frac=0.05, signal_onset_smooth=40,
                              min_height_ratio=2.0):
    """Recover bases the per-channel cluster merge silently swallowed.
    (Identical to the GUI's inlined copy.)

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
    shifted_all = [dsp_core.shift_channel(separated[:, ch], int(shifts[ch]))
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
    peaks, _ = find_peaks(norm, distance=max(1, int(min_distance)), prominence=prom)

    lead_n = max(int(n * 0.05), 1)
    ch_floor = [float(np.percentile(np.clip(shifted_all[ch][:lead_n], 0, None), 90))
                for ch in range(4)]

    start = 0
    if onset_frac and onset_frac > 0:
        start = pc_signal_onset(separated, onset_frac=onset_frac,
                                smooth=signal_onset_smooth)

    existing = set(int(p) for p in (positions or []))
    fill_gap = max(1, int(fill_gap))
    fill_margin = float(fill_margin)
    floor_mult = max(float(min_height_ratio), 0.0)
    added = []
    for p in peaks:
        p = int(p)
        if p < start:
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
