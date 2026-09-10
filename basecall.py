"""Peak detection and basecalling algorithms.

Pure functions extracted from sequencing_gui_V15.py.  No Qt, no widgets.
Each caller returns (positions, sequence, base_groups, intensities) so the
GUI can swap them interchangeably.

Dependencies: numpy, scipy (signal, ndimage), constants, dsp.
"""
import numpy as np
from scipy.signal import find_peaks
from scipy.ndimage import maximum_filter1d

from constants import BASE_LETTERS, CHEM_MAP, IUPAC_CODES
from dsp import dsp_shift_channel


# ── Normalization ──────────────────────────────────────────────────────

def pc_normalize_peaks(separated, mode='total_signal', window=800):
    """Normalize the 4-channel separated trace so peak heights are
    comparable across channels and across the run."""
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
    """Per-channel rolling-local normalization for display."""
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
            signal_max = float(ch_sig[r0:int(region[1])].max()) if int(region[1]) > r0 else float(ch_sig.max())
            floor = max(floor, min(2.5 * lead_floor, signal_max / 3.0 + 1e-9))
        denom = np.maximum(local_max, floor)
        out[:, ch] = ch_sig / denom
    scale = np.percentile(out, 99.5, axis=0)
    scale[scale <= 0] = 1.0
    return out / scale[np.newaxis, :]


# ── Peak detection ─────────────────────────────────────────────────────

def pc_detect_peaks_4ch(separated, min_distance=6, prominence_frac=0.02, width=None):
    """Run find_peaks independently on each of the 4 (normalized)
    separated channels, then merge into one ordered list."""
    x = np.clip(np.asarray(separated, dtype=np.float64), 0, None)
    candidates = []
    for ch in range(4):
        scale = np.percentile(x[:, ch], 99.5)
        if scale <= 0:
            continue
        prom = max(scale * prominence_frac, 1e-9)
        kwargs = dict(distance=max(1.0, float(min_distance)), prominence=prom)
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
    """End-to-end independent basecall: normalize -> detect -> merge -> assign."""
    norm = pc_normalize_peaks(separated, mode=normalize_mode)
    merged = pc_detect_peaks_4ch(norm, min_distance=min_distance,
                                 prominence_frac=prominence_frac)
    positions = np.array([m[0] for m in merged], dtype=np.int64)
    sequence = ''.join(BASE_LETTERS[m[1]] for m in merged)
    heights = np.array([m[2] for m in merged], dtype=np.float64)
    return positions, sequence, heights


# ── Signal region detection ────────────────────────────────────────────

def pc_signal_onset(separated, onset_frac=0.05, smooth=40, rise_sigma=4.0,
                    lead_frac=0.05, rise_window=None):
    """Find the scan index where the sample DNA signal first starts to
    *rise* above the instrument baseline."""
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


def pc_signal_region(separated, onset_frac=0.05, tail_frac=0.10,
                     smooth=40, tail_margin=10):
    """Detect the callable signal window [start, stop) of a CE run."""
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


# ── Per-channel cluster caller ─────────────────────────────────────────

def pc_call_bases_with_shifts(separated, shifts, min_distance=6,
                              prominence_frac=0.02, tolerance=4,
                              normalize=True, norm_window=800,
                              min_signal_frac=0.25, onset_frac=0.05,
                              signal_onset_smooth=40, min_height_ratio=2.0,
                              region=None):
    """Detect peaks on per-channel-shifted separated traces and merge with
    IUPAC ambiguity codes."""
    n = len(separated)
    shifted_all = [dsp_shift_channel(separated[:, ch], int(shifts[ch]))
                   for ch in range(4)]

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
        scale = np.percentile(np.clip(norm_ch, 0, None), 99.5)
        prom = max(scale * prominence_frac, 1e-9) if scale > 0 else 1e-9
        peaks, _ = find_peaks(norm_ch, distance=max(1, min_distance), prominence=prom)
        floor_ch = ch_floor[ch] * max(float(min_height_ratio), 0.0)
        for p in peaks:
            if shifted[p] >= floor_ch:
                channels.append((int(p), ch, float(shifted[p])))

    channels.sort(key=lambda c: c[0])

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


# ── Greedy caller ──────────────────────────────────────────────────────

def pc_call_bases_greedy(separated, shifts, window=5, min_frac=0.20,
                         norm_window=800, region=None, min_distance_floor=1):
    """Greedy maximum-intensity peak caller on the combined envelope.

    min_distance_floor enforces a minimum inter-peak (scan) separation --
    passed as the DE-tunable 'min_distance_floor' knob so the optimizer cannot
    over-call by driving the blanking window ('window') down to ~1 scan. A call
    blanks +/-max(window, floor), so neighbouring spurious peaks within a single
    physical base's footprint are not emitted as separate bases.
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
        blank = max(int(window), int(min_distance_floor))
        lo, hi = max(0, i - blank), min(n, i + blank + 1)
        work[lo:hi] = -1.0
    order = np.argsort(picks)
    positions = np.array(picks, dtype=np.int64)[order]
    sequence = ''.join(letters[k] for k in order)
    base_groups = [frozenset([letters[k]]) for k in order]
    intensities = [{letters[k]: float(shifted_all[int(np.argmax(normed[picks[k]]))]
                                        [picks[k]])} for k in order]
    return positions, sequence, base_groups, intensities


# ── Fill-in (recover merged-away bases) ────────────────────────────────

def pc_fill_in_combined_peaks(separated, shifts, positions=None,
                              min_distance=1, prominence_frac=0.02,
                              norm_window=800, fill_gap=3, fill_margin=0.2,
                              onset_frac=0.05, signal_onset_smooth=40,
                              min_height_ratio=2.0, region=None):
    """Recover bases the per-channel cluster merge silently swallowed."""
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
    peaks, _ = find_peaks(norm, distance=max(1.0, float(min_distance)),
                          prominence=prom)

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


# ── Shoulder recovery ─────────────────────────────────────────────────

def pc_fill_in_shoulders(separated, shifts, positions=None,
                         norm_window=800, fill_gap=3, fill_margin=0.5,
                         onset_frac=0.05, signal_onset_smooth=40,
                         region=None):
    """Recover shoulder peaks the greedy caller's excision blanks out.

    The greedy caller (``pc_call_bases_greedy``) excises +/-window scans
    around every called peak, so a genuine base whose apex sits inside that
    band of a taller neighbor is silently dropped - even when it is a clean
    single-channel local maximum (a "shoulder" of that neighbor).

    Prominence-based detection can't find these: a flanking shoulder's
    contour to its higher neighbor lies at essentially its own height, so
    its prominence is squeezed toward zero by construction. This pass
    therefore uses three criteria that are structurally independent of
    prominence:

      * the candidate must be a true local maximum of the normalized
        combined envelope (keeps inflection/noise humps out),
      * it must sit at least ``fill_gap`` scans from every existing call
        (reuses the GUI's "Fill gap" knob),
      * its winning channel must dominate the runner-up by at least
        ``fill_margin`` (reuses the GUI's "Fill margin" knob). Real
        shoulders are clean single-channel bumps; multi-channel noise
        floods rarely reach 0.5 dominance.

    Returns the added (position, base) pairs, sorted by position,
    compatible with the existing fill-in flow (the GUI draws added bases
    in orange)."""
    n = len(separated)
    if n == 0:
        return []
    shifted_all = [dsp_shift_channel(separated[:, ch], int(shifts[ch]))
                   for ch in range(4)]
    normed = np.empty_like(separated)
    for ch in range(4):
        sh = shifted_all[ch]
        rolled = maximum_filter1d(np.clip(sh, 0, None),
                                  size=max(3, int(norm_window)), mode='nearest')
        rolled = np.where(rolled > 0, rolled, 1.0)
        normed[:, ch] = sh / rolled
    comb = normed.max(axis=1)

    start = 0
    stop = n
    if region is not None and int(region[1]) > int(region[0]):
        start = max(0, int(region[0]))
        stop = min(n, int(region[1]))
    elif onset_frac and onset_frac > 0:
        start = pc_signal_onset(separated, onset_frac=onset_frac,
                                smooth=signal_onset_smooth)

    peaks, _ = find_peaks(comb, distance=1)
    existing = set(int(p) for p in (positions or []))
    fill_gap = max(1, int(fill_gap))
    fill_margin = float(fill_margin)
    added = []
    for p in peaks:
        p = int(p)
        if p < start or p >= stop:
            continue
        if any(abs(p - q) < fill_gap for q in existing):
            continue
        vals = np.array([shifted_all[ch][p] for ch in range(4)])
        top = vals.max()
        if top <= 0:
            continue
        second = float(np.partition(vals, -2)[-2])
        if (top - second) / top < fill_margin:
            continue
        dom_ch = int(np.argmax(vals))
        added.append((p, BASE_LETTERS[dom_ch]))
        existing.add(p)
    return sorted(added, key=lambda t: t[0])


# ── LifeTrace basecalling ─────────────────────────────────────────────

def pc_lifetrace_peaks_shape(traces, window=7, sigma=3.5):
    """Peak-shape factor R[b,loc] per channel, via sliding Pearson
    correlation with an ideal Gaussian model peak."""
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
    return R


def pc_lifetrace_transform(separated, window=7, sigma=3.5, k=4.0):
    """LifeTrace combined peak-likeness trace LT(loc)."""
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
    """LifeTrace-style independent basecall."""
    sep = np.clip(np.asarray(separated, dtype=np.float64), 0, None)
    shifted = sep.copy()
    for ch in range(4):
        s = int(shifts[ch])
        if s != 0:
            shifted[:, ch] = dsp_shift_channel(shifted[:, ch], s)

    LT = pc_lifetrace_transform(shifted, window=window, sigma=sigma, k=k)
    n = len(LT)

    lt_p99 = float(np.percentile(LT, 99.5))
    floor = max(lt_p99 * floor_frac, 1e-9)
    dist = peak_dist if peak_dist and peak_dist > 0 else max(2, int(window * 0.5))
    peaks, _ = find_peaks(LT, distance=dist, height=floor)
    peaks = np.asarray(peaks, dtype=np.int64)

    start = 0
    if onset_frac and onset_frac > 0:
        start = pc_signal_onset(separated, onset_frac=onset_frac,
                                smooth=signal_onset_smooth)

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
        area = seg.sum(axis=0)
        atot = area.sum()
        if atot <= 1e-9:
            continue
        area_frac = area / atot
        score = area_frac * R01[p]
        winner = int(np.argmax(score))
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

    merged = []
    for p, letter, h in calls:
        if merged and merged[-1][1] == letter and \
                (p - merged[-1][0]) <= merge_same:
            prev_x, prev_let, prev_h = merged[-1]
            if h > prev_h:
                merged[-1] = (p, letter, h)
            continue
        merged.append((p, letter, h))

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
            peak_l = np.argmax(LT[max(0, p - 1):min(n, p + 2)]) + max(0, p - 1)
            thresh = max(LT[peak_l] / 10.0, 1e-9)
            left = peak_l
            while left > 0 and LT[left] > thresh:
                left -= 1
            right = peak_l
            while right < n - 1 and LT[right] > thresh:
                right += 1
            width = float(right - left)
            lo_i, hi_i = max(0, idx - 10), min(len(merged), idx + 11)
            local_sp = np.diff(xs[lo_i:hi_i]) if hi_i - lo_i >= 2 else np.array([gap])
            local_sp = local_sp[local_sp > 0]
            spacing = float(np.median(local_sp)) if len(local_sp) else float(gap)
            n_add = int(0.45 + width / max(spacing, 1.0))
            if n_add > 1 and gap >= spacing * 0.6:
                for _ in range(min(n_add - 1, add_broad_max)):
                    out.append((p, letter, h))
        merged = sorted(out, key=lambda t: t[0])

    positions = np.array([c[0] for c in merged], dtype=np.int64)
    sequence = ''.join(c[1] for c in merged)
    base_groups = [frozenset([l]) if l in 'ACGT' else frozenset()
                   for l in sequence]
    intensities = [{l: 1.0} if l in 'ACGT' else {} for l in sequence]
    return positions, sequence, base_groups, intensities


# ── Hybrid caller ──────────────────────────────────────────────────────

def pc_hybrid_basecall(separated, shifts, snap_rad=6, peak_floor=0.02,
                       **cur_kw):
    """Hybrid basecall: per-channel peaks for recall, snapped onto
    LifeTrace's combined-trace maxima for position accuracy."""
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


# ── Mobility-shift estimation ──────────────────────────────────────────

def pc_estimate_mobility_shifts(raw, ref_channel=3, max_shift=60, smooth=5,
                                tol=2, min_coinc_frac=0.55):
    """Estimate per-channel dye-mobility scan shifts by counting peak
    coincidences against a reference channel."""
    from scipy.ndimage import uniform_filter1d
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
