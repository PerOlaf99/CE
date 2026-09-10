"""GapCheck: fuzzy-logic peak refinement for Sanger basecalling.

Implements the GapCheck algorithm from patent EP0944739A1 (Marks, U. of Utah)
to insert missing peaks in homopolymer runs and remove false peaks.

Pipeline:
  1. Putative peak detection on envelope
  2. OmitOkN filter (remove false peaks)
  3. Quadratic spacing model fit
  4. GapCheck (insert missing peaks)
  5. OmitOkN filter (clean up insertions)

Dependencies: numpy only.
"""
import numpy as np

# ═══════════════════════════════════════════════════════════════════════
# Fuzzy operators (min/max/NOT as per patent)
# ═══════════════════════════════════════════════════════════════════════

def _and(a, b):
    return min(a, b)

def _or(a, b):
    return max(a, b)

def _not(v):
    return 1.0 - v


# ═══════════════════════════════════════════════════════════════════════
# Piecewise-linear membership functions
# ═══════════════════════════════════════════════════════════════════════

def _interp(x, xs, ys):
    """Piecewise-linear membership: returns value in [0, 1]."""
    if x <= xs[0]:
        return ys[0]
    if x >= xs[-1]:
        return ys[-1]
    for i in range(1, len(xs)):
        if x <= xs[i]:
            t = (x - xs[i - 1]) / (xs[i] - xs[i - 1])
            return ys[i - 1] + t * (ys[i] - ys[i - 1])
    return ys[-1]


def _hedge_contint(y):
    """CONTINT hedge: sqrt for y>=0.5, square for y<0.5."""
    return np.sqrt(y) if y >= 0.5 else y * y


def _hedge_very(y):
    """VERY hedge: square."""
    return y * y


def _hedge_somewhat(y):
    """SOMEWHAT hedge: sqrt."""
    return np.sqrt(y)


# ═══════════════════════════════════════════════════════════════════════
# Membership functions for GapCheck
# ═══════════════════════════════════════════════════════════════════════

def mbig_gap(raw_gap):
    """BigGap: gap is large relative to expected spacing.
    Input: raw_gap = (observed / expected) - 1.0, range [-1, inf].
    VERY hedge applied (squared)."""
    y = _interp(raw_gap, [0.42, 0.6, 1.0], [0.0, 1.0, 1.0])
    return _hedge_very(y)


def msmall_gap(raw_gap):
    """SmallGap: gap is small relative to expected spacing.
    CONTINT hedge applied."""
    y = _interp(raw_gap, [-1.0, -0.5, 0.0], [1.0, 1.0, 0.0])
    return _hedge_contint(y)


def mbig_width(raw_wid):
    """BigWidth: band is wider than expected.
    Input: raw_wid = (observed_width / expected_width) - 1.0.
    CONTINT hedge applied."""
    y = _interp(raw_wid, [0.0, 1.0], [0.0, 1.0])
    return _hedge_contint(y)


def mgc_richness(gc_val):
    """GC-richness: already computed, just clamp to [0, 1]."""
    return max(0.0, min(1.0, gc_val))


# ═══════════════════════════════════════════════════════════════════════
# Membership functions for OmitOkN
# ═══════════════════════════════════════════════════════════════════════

def mok_spacing(norm_sp):
    """OK spacing: V-shape accepting integer multiples of expected.
    norm_sp in [0, 1] = modular spacing / expected_spacing."""
    return _interp(norm_sp, [0.2, 0.5, 0.8], [1.0, 0.0, 1.0])


def mbad_spacing(norm_sp):
    """Bad spacing: inverted trapezoid, VERY hedge."""
    y = _interp(norm_sp, [0.2, 0.4, 0.6, 0.8], [0.0, 1.0, 1.0, 0.0])
    return _hedge_very(y)


def mtiny_height(ht, median_plo):
    """Tiny height: dynamic breakpoints based on median intersect."""
    x0 = 0.4 * median_plo
    x1 = 1.1 * median_plo
    if x1 <= x0:
        x1 = x0 + 1e-9
    return _interp(ht, [x0, x1], [1.0, 0.0])


def mok_height(ht, median_plo):
    """OK height: SOMEWHAT hedge."""
    x0 = 0.5 * median_plo
    x1 = 1.5 * median_plo
    if x1 <= x0:
        x1 = x0 + 1e-9
    y = _interp(ht, [x0, x1], [0.0, 1.0])
    return _hedge_somewhat(y)


def mtiny_xb(ratio):
    """Tiny cross-banding: ratio close to 1.0 means high cross-banding."""
    return _interp(ratio, [1.0, 1.4, 1.8], [1.0, 0.5, 0.0])


def mok_xb(ratio):
    """OK cross-banding: ratio > 1.4 is negligible."""
    return _interp(ratio, [1.2, 1.4], [0.0, 1.0])


# ═══════════════════════════════════════════════════════════════════════
# Quadratic fit (least-squares with outlier rejection)
# ═══════════════════════════════════════════════════════════════════════

def fit_quadratic(xs, ys):
    """Fit y = a + b*x + c*x^2 via least squares.
    Two-pass: fit all, reject outliers > 1sigma, re-fit.
    Returns (a, b, c) coefficients, or None if too few points."""
    xs = np.asarray(xs, dtype=np.float64)
    ys = np.asarray(ys, dtype=np.float64)
    if len(xs) < 3:
        return None
    A = np.column_stack([np.ones_like(xs), xs, xs ** 2])
    try:
        coeffs, _, _, _ = np.linalg.lstsq(A, ys, rcond=None)
    except np.linalg.LinAlgError:
        return None
    pred = A @ coeffs
    resid = ys - pred
    sigma = max(float(np.std(resid)), 1e-9)
    mask = np.abs(resid) <= sigma
    if mask.sum() < 3:
        return coeffs
    A2 = np.column_stack([np.ones_like(xs[mask]), xs[mask], xs[mask] ** 2])
    try:
        coeffs2, _, _, _ = np.linalg.lstsq(A2, ys[mask], rcond=None)
        return coeffs2
    except np.linalg.LinAlgError:
        return coeffs


def eval_quadratic(coeffs, x):
    """Evaluate quadratic at point x."""
    a, b, c = coeffs
    return a + b * x + c * x * x


# ═══════════════════════════════════════════════════════════════════════
# GC-richness
# ═══════════════════════════════════════════════════════════════════════

def gc_richness(seq, idx, n_prev=5):
    """Compute GC-richness for upstream context at position idx.
    Uses Euclidean distance weighting over n_prev bases."""
    start = max(0, idx - n_prev)
    window = seq[start:idx]
    if len(window) == 0:
        return 0.0
    n = len(window)
    gs = sum(1 for b in window if b in ('G', 'C'))
    cs = gs  # same as gs for GC count
    lh = (n + 1) // 2
    sh = n - lh
    mx = lh
    my = sh
    def weight(nn, g, c, mmx, mmy):
        return 1.0 - np.sqrt(
            ((nn - g) ** 2 + (nn - c) ** 2) / (2.0 * nn * nn))
    normalize = weight(n, mx, my, mx, my)
    if normalize <= 0:
        return 0.0
    rv = weight(n, gs, cs, mx, my) / normalize
    return min(1.0, rv) ** 2


# ═══════════════════════════════════════════════════════════════════════
# Putative peak detection (envelope-based)
# ═══════════════════════════════════════════════════════════════════════

def detect_putative_peaks(envelope):
    """Detect putative peaks: samples taller than both neighbors.
    Returns array of peak indices."""
    env = np.asarray(envelope, dtype=np.float64)
    n = len(env)
    if n < 3:
        return np.array([], dtype=np.int64)
    peaks = []
    for i in range(1, n - 1):
        if env[i] > env[i - 1] and env[i] > env[i + 1]:
            peaks.append(i)
    return np.array(peaks, dtype=np.int64)


# ═══════════════════════════════════════════════════════════════════════
# OmitOkN fuzzy filter
# ═══════════════════════════════════════════════════════════════════════

def omit_okn_filter(peaks, envelope, expected_spacing,
                    median_intersect=None):
    """Classify each peak as OK, AMBIGUOUS, or OMIT.

    Uses spacing (modular), cross-banding, and height.

    Returns list of (peak_index, classification) tuples.
    """
    env = np.asarray(envelope, dtype=np.float64)
    n = len(env)
    if len(peaks) == 0:
        return []

    if median_intersect is None:
        median_intersect = max(float(np.median(env[env > 0])), 1e-9)

    results = []
    for k, p in enumerate(peaks):
        p = int(p)
        ht = env[p] if 0 <= p < n else 0.0

        # Cross-banding ratio at this peak
        lo = max(0, p - 2)
        hi = min(n, p + 3)
        local = env[lo:hi]
        if len(local) >= 2:
            sorted_local = np.sort(local)[::-1]
            top1 = sorted_local[0]
            top2 = sorted_local[1] if len(sorted_local) > 1 else 1e-9
            xb_ratio = top1 / max(top2, 1e-9)
        else:
            xb_ratio = 5.0

        # Modular spacing normalized to expected
        insp = expected_spacing
        if k > 0:
            lsp = p - peaks[k - 1]
        else:
            lsp = insp
        if k < len(peaks) - 1:
            rsp = peaks[k + 1] - p
        else:
            rsp = insp

        mod_lsp = (lsp % insp) / insp if insp > 0 else 0.5
        mod_rsp = (rsp % insp) / insp if insp > 0 else 0.5
        if lsp < insp / 2.0:
            mod_lsp = 0.5
        if rsp < insp / 2.0:
            mod_rsp = 0.5

        oksp_l = mok_spacing(mod_lsp)
        oksp_r = mok_spacing(mod_rsp)
        absp_l = mbad_spacing(mod_lsp)
        absp_r = mbad_spacing(mod_rsp)
        oksp = _or(oksp_l, oksp_r)
        absp = _or(absp_l, absp_r)

        tixb = mtiny_xb(xb_ratio)
        okxb = mok_xb(xb_ratio)
        tiht = mtiny_height(ht, median_intersect)
        okht = mok_height(ht, median_intersect)

        # Rules
        r_ok = _and(okxb, _or(okht, oksp))
        r_amb = _and(tixb, _or(okht, _and(oksp, tiht)))
        r_omit = _and(tiht, absp)

        # Defuzzification via centroid of output sets
        # OK: centroid ~0.5, AMBIGUOUS: ~1.5, OMIT: ~2.5
        # Use weighted average as simple defuzzification
        score = (r_ok * 0.5 + r_amb * 1.5 + r_omit * 2.5) / max(r_ok + r_amb + r_omit, 1e-9)
        if score <= 0.8:
            cls = 'OK'
        elif score >= 1.8:
            cls = 'OMIT'
        else:
            cls = 'AMBIGUOUS'
        results.append((p, cls))

    return results


# ═══════════════════════════════════════════════════════════════════════
# GapCheck fuzzy logic
# ═══════════════════════════════════════════════════════════════════════

def gapcheck_classify(peaks, envelope, exp_spacing_coeffs, exp_width_coeffs,
                      seq, peak_widths=None):
    """Classify each gap between consecutive peaks as NORMAL or SPLIT.

    Returns list of (gap_index, classification, num_to_insert) tuples.
    gap_index i means the gap between peaks[i] and peaks[i+1].
    """
    env = np.asarray(envelope, dtype=np.float64)
    n = len(env)
    n_peaks = len(peaks)
    if n_peaks < 2:
        return []

    if peak_widths is None:
        peak_widths = _estimate_peak_widths(peaks, env)

    results = []
    for i in range(n_peaks - 1):
        p0, p1 = int(peaks[i]), int(peaks[i + 1])
        gap = p1 - p0
        if gap <= 0:
            results.append((i, 'NORMAL', 0))
            continue

        # Expected spacing at midpoint
        mid = (p0 + p1) / 2.0
        exp_sp = eval_quadratic(exp_spacing_coeffs, mid)
        exp_sp = max(exp_sp, 1.0)

        # Expected width at midpoint
        exp_wd = eval_quadratic(exp_width_coeffs, mid)
        exp_wd = max(exp_wd, 1.0)

        # Normalized gap and width
        raw_gap = gap / exp_sp - 1.0
        w0 = peak_widths[i] / exp_wd - 1.0
        w1 = peak_widths[i + 1] / exp_wd - 1.0

        # GC-richness of upstream context
        gc = gc_richness(seq, i) if seq else 0.0

        # Membership values
        bg = mbig_gap(raw_gap)
        sg = msmall_gap(raw_gap)
        bw0 = mbig_width(w0)
        bw1 = mbig_width(w1)

        # RULE NORMAL: don't split
        c1 = _and(bg, gc)
        c2 = _and(_and(_and(bg, sg), _not(bw0)), _not(bw1))
        r_norm = _or(_not(bg), _or(c1, c2))

        # RULE SPLIT: insert bands
        c3 = _and(bg, _or(bw0, bw1))
        c4 = _and(_and(bg, _not(sg)), _not(gc))
        r_split = _or(c3, c4)

        # Defuzzification
        if r_split > r_norm and r_split > 0.3:
            ratio = gap / max(exp_sp, 1.0)
            n_insert = max(0, int(0.7 + ratio) - 1)
            results.append((i, 'SPLIT', n_insert))
        else:
            results.append((i, 'NORMAL', 0))

    return results


def _estimate_peak_widths(peaks, envelope):
    """Estimate width of each peak as distance to half-max on each side."""
    env = np.asarray(envelope, dtype=np.float64)
    n = len(env)
    widths = np.ones(len(peaks), dtype=np.float64) * 3.0
    for k, p in enumerate(peaks):
        p = int(p)
        ht = env[p] if 0 <= p < n else 0.0
        half = ht / 2.0
        # Left extent
        left = p
        while left > 0 and env[left] > half:
            left -= 1
        # Right extent
        right = p
        while right < n - 1 and env[right] > half:
            right += 1
        widths[k] = max(1.0, right - left)
    return widths


# ═══════════════════════════════════════════════════════════════════════
# Centroid placement for inserted peaks
# ═══════════════════════════════════════════════════════════════════════

def _centroid(bgn, end, envelope):
    """Compute intensity-weighted centroid of interval [bgn, end].
    Places insertion on the shoulder of a poorly defined band."""
    env = np.asarray(envelope, dtype=np.float64)
    n = len(env)
    bgn_i = max(0, int(bgn))
    end_i = min(n - 1, int(end))
    seg = env[bgn_i:end_i + 1]
    if len(seg) == 0:
        return (bgn + end) / 2.0
    idx = np.arange(bgn_i, end_i + 1, dtype=np.float64)
    total = seg.sum()
    if total <= 0:
        return (bgn + end) / 2.0
    return float(np.sum(idx * seg) / total)


# ═══════════════════════════════════════════════════════════════════════
# Main refinement pipeline
# ═══════════════════════════════════════════════════════════════════════

def refine_with_gap_check(envelope, init_peaks, init_sequence=None,
                          min_peaks_for_fit=10, verbose=False):
    """Full GapCheck refinement pipeline.

    Parameters
    ----------
    envelope : 1-D array
        Combined envelope (max across channels) after DSP.
    init_peaks : 1-D array of int
        Initial peak positions from greedy caller.
    init_sequence : str or None
        Initial base sequence (for GC-richness).
    min_peaks_for_fit : int
        Minimum peaks needed for quadratic fit.
    verbose : bool
        Print diagnostics.

    Returns
    -------
    dict with keys:
        'peaks' : refined peak positions (int array)
        'sequence' : base sequence (str)
        'n_inserted' : number of peaks inserted
        'n_omitted' : number of peaks removed
        'classifications' : per-peak OK/AMBIGUOUS/OMIT
    """
    env = np.asarray(envelope, dtype=np.float64)
    n = len(env)
    peaks = np.array(sorted(set(int(p) for p in init_peaks
                                if 0 <= int(p) < n)), dtype=np.int64)

    if len(peaks) < 5:
        return dict(peaks=peaks, sequence=init_sequence or '',
                    n_inserted=0, n_omitted=0, classifications=[])

    # --- Step 1: Estimate initial spacing from median ---
    spacings = np.diff(peaks.astype(np.float64))
    spacings = spacings[spacings > 0]
    if len(spacings) == 0:
        return dict(peaks=peaks, sequence=init_sequence or '',
                    n_inserted=0, n_omitted=0, classifications=[])
    median_sp = float(np.median(spacings))

    # --- Step 2: OmitOkN first pass ---
    omit_cls = omit_okn_filter(peaks, env, median_sp)
    keep_mask = np.ones(len(peaks), dtype=bool)
    n_omit1 = 0
    for k, (p, cls) in enumerate(omit_cls):
        if cls == 'OMIT':
            keep_mask[k] = False
            n_omit1 += 1
    peaks_f = peaks[keep_mask]
    seq_f = ''.join(init_sequence[k] for k in range(len(init_sequence))
                    if keep_mask[k]) if init_sequence else ''

    if len(peaks_f) < min_peaks_for_fit:
        return dict(peaks=peaks_f, sequence=seq_f,
                    n_inserted=0, n_omitted=n_omit1, classifications=omit_cls)

    # --- Step 3: Quadratic spacing model ---
    xs = peaks_f.astype(np.float64)
    sp = np.diff(xs)
    sp_x = (xs[:-1] + xs[1:]) / 2.0
    sp_coeffs = fit_quadratic(sp_x, sp)
    if sp_coeffs is None:
        sp_coeffs = (median_sp, 0.0, 0.0)

    # Width model
    widths = _estimate_peak_widths(peaks_f, env)
    w_coeffs = fit_quadratic(xs, widths)
    if w_coeffs is None:
        w_coeffs = (float(np.median(widths)), 0.0, 0.0)

    # --- Step 4: GapCheck ---
    seq_for_gc = seq_f if seq_f else init_sequence or ''
    gc_results = gapcheck_classify(peaks_f, env, sp_coeffs, w_coeffs,
                                   seq_for_gc, widths)

    # Insert new peaks
    new_peaks = list(peaks_f)
    n_insert = 0
    for gap_idx, cls, n_to_add in gc_results:
        if cls != 'SPLIT' or n_to_add <= 0:
            continue
        p0 = int(peaks_f[gap_idx])
        p1 = int(peaks_f[gap_idx + 1])
        gap = p1 - p0
        exp_sp_val = eval_quadratic(sp_coeffs, (p0 + p1) / 2.0)
        exp_sp_val = max(exp_sp_val, 1.0)

        # Divide gap into (n_to_add + 1) intervals
        sub_gap = gap / (n_to_add + 1)
        for j in range(1, n_to_add + 1):
            bgn = p0 + sub_gap * j - sub_gap / 2.0
            end = p0 + sub_gap * j + sub_gap / 2.0
            mid = p0 + sub_gap * j
            # Place at centroid of sub-interval
            centroid = _centroid(bgn, end, env)
            new_peaks.append(int(round(centroid)))
            n_insert += 1

    new_peaks = sorted(set(new_peaks))
    peaks_g = np.array(new_peaks, dtype=np.int64)

    # --- Step 5: OmitOkN second pass (clean up insertions) ---
    if len(peaks_g) >= 5:
        sp2 = np.diff(peaks_g.astype(np.float64))
        sp2 = sp2[sp2 > 0]
        median_sp2 = float(np.median(sp2)) if len(sp2) > 0 else median_sp
        omit_cls2 = omit_okn_filter(peaks_g, env, median_sp2)
        keep2 = np.ones(len(peaks_g), dtype=bool)
        n_omit2 = 0
        for k, (p, cls) in enumerate(omit_cls2):
            if cls == 'OMIT':
                keep2[k] = False
                n_omit2 += 1
        peaks_g = peaks_g[keep2]
        n_omit1 += n_omit2

    # Assign bases to final peaks
    if init_sequence is not None:
        # Use channel information if available (fallback: keep init bases)
        seq_out = _assign_bases_from_envelope(peaks_g, env)
    else:
        seq_out = _assign_bases_from_envelope(peaks_g, env)

    if verbose:
        print(f'  GapCheck: {len(peaks)} -> {len(peaks_g)} peaks '
              f'(+{n_insert} inserted, -{n_omit1} omitted)')

    return dict(peaks=peaks_g, sequence=seq_out,
                n_inserted=n_insert, n_omitted=n_omit1,
                classifications=omit_cls)


def _assign_bases_from_envelope(peaks, envelope):
    """Assign ACGT base to each peak based on which channel dominates.
    Uses the envelope (max across channels) — this is a placeholder;
    the caller should use actual channel data for proper base calling."""
    # Without channel info, we can only mark peaks as present
    return 'N' * len(peaks)


def assign_bases_with_channels(peaks, channels_4ch):
    """Assign ACGT bases given 4-channel data (N x 4 array).
    Returns base string."""
    ch = np.asarray(channels_4ch, dtype=np.float64)
    bases = []
    LETTERS = 'ACGT'
    for p in peaks:
        p = int(p)
        if 0 <= p < len(ch):
            winner = int(np.argmax(ch[p]))
            bases.append(LETTERS[winner])
        else:
            bases.append('N')
    return ''.join(bases)
