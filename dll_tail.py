"""dll_tail.py - DLL-style tail recovery for Sanger reads.

Two components:
  1. chan_detect_tail(): per-channel peak detection on spec-separated lanes
     for the tail region (scans >= split).  Replaces the GUI's raw-grid tail
     positions (which miss bases in the late read) with the DLL's detection
     recipe: per-channel local-maxima, merge within min-sep, re-center each
     call onto its winning channel's local maximum.

  2. fun10019280_snap(): faithful port of the DLL's FUN_10019280 "position
     massager" — quadratic-trend snap with z-outlier trim and monotonic
     enforcement.  Applied to tail positions to smooth the spacing curve
     and drop spurious detections.

Fold-in: SequencingGUI._dll_tail_recover() calls these two and is wired
into _run_basecall so that calls come out in DLL-tail form automatically.
"""
import math
import numpy as np

DYE = "TGCA"


# ---------------------------------------------------------------------------
# Z-score helper
# ---------------------------------------------------------------------------
def _zs(L):
    """Per-column z-score normalisation (used for cache_sep / separated)."""
    mu = L.mean(0, keepdims=True)
    sd = L.std(0, keepdims=True) + 1e-9
    return (L - mu) / sd


# ---------------------------------------------------------------------------
# 1.  Per-channel tail detector
# ---------------------------------------------------------------------------
def chan_detect_tail(Z, split=6000, end=None, min_sep=4, snap_r=2):
    """Detect peaks in the tail region (scans [split, end)) by looking at each
    separated channel independently (the DLL's FUN_1002511d recipe).

    Parameters
    ----------
    Z : (N, 4) float  — z-scored separated lanes
    split : int        — first scan of tail region
    end : int or None  — exclusive upper scan (default N)
    min_sep : int      — minimum scan distance between detected peaks
    snap_r : int       — re-center each candidate within ±snap_r scans

    Returns
    -------
    pos : int ndarray  — detected tail positions (sorted, monotone)
    """
    n = Z.shape[0]
    if end is None:
        end = n
    end = min(end, n)

    # Phase 1: collect local-maxima per channel
    all_peaks = []
    for ch in range(4):
        sig = Z[split:end, ch]
        if len(sig) < 3:
            continue
        rising = sig[1:-1] > sig[:-2]
        falling = sig[1:-1] >= sig[2:]
        m = rising & falling
        for i in np.where(m)[0] + split + 1:
            all_peaks.append((int(i), float(sig[i - split]), ch))
    all_peaks.sort()
    if not all_peaks:
        return np.array([], dtype=np.int64)

    # Phase 2: merge within min_sep (keep highest value)
    keep = [all_peaks[0]]
    for scan, val, ch in all_peaks[1:]:
        if scan - keep[-1][0] >= min_sep:
            keep.append((scan, val, ch))
        elif val > keep[-1][1]:
            keep[-1] = (scan, val, ch)

    # Phase 3: re-center onto winning channel's local max
    out = []
    for scan, val, ch in keep:
        lo = max(0, scan - snap_r)
        hi = min(n - 1, scan + snap_r + 1)
        cand = int(lo + np.argmax(Z[lo:hi, ch]))
        cand = max(cand, (out[-1] + 1) if out else split - 1)
        if cand >= n - 2:
            break
        out.append(cand)

    return np.array(out, dtype=np.int64)


# ---------------------------------------------------------------------------
# 2.  FUN_10019280 — current-fix position massager (quadratic snap)
# ---------------------------------------------------------------------------
def fun10019280(positions, z_trim=1.5):
    """Faithful port of FUN_10019280 from the Cimarron 3.12 DLL.

    Takes a sorted int[] of peak positions and returns a new int[] snapped
    onto a smooth quadratic trend (scan = a*idx^2 + b*idx + c), with
    z-outlier rejection (threshold 1.5 = _DAT_10038aa0) and strict
    monotonic enforcement (floor >= 1).

    Parameters
    ----------
    positions : (K,) int   — sorted peak positions
    z_trim : float          — z-score outlier cutoff (DLL constant = 1.5)

    Returns
    -------
    snapped : (K,) int64   — smoothed, monotone-increasing positions
    """
    p = np.asarray(positions, dtype=np.float64)
    n = len(p)
    if n == 0:
        return np.array([], dtype=np.int64)
    if n == 1:
        return np.array([max(1, int(p[0]))], dtype=np.int64)

    idx = np.arange(n, dtype=np.float64)

    # --- pass 1: z-score outlier trim on the *raw positions*
    mu = float(p.mean())
    sd = float(p.std())
    if sd < 1e-12:
        sd = 1.0
    z = np.abs(p - mu) / sd
    keep1 = z <= z_trim
    if keep1.sum() < 3:
        keep1[:] = True  # fall back to no rejection

    # quadratic fit position vs index on kept points
    A1 = np.vstack([idx[keep1] ** 2, idx[keep1], np.ones(keep1.sum())]).T
    try:
        coeffs1 = np.linalg.lstsq(A1, p[keep1], rcond=None)[0]
    except np.linalg.LinAlgError:
        return np.maximum(np.round(p).astype(np.int64), 1)

    a1, b1, c1 = coeffs1
    fitted1 = a1 * idx ** 2 + b1 * idx + c1
    resid1 = np.abs(fitted1 - p)
    dvar5 = float(resid1.std())  # per DLL: sqrt(local_1c) = resid std

    # --- pass 2: re-snap loop — keep points whose residual < dvar5
    snapped = np.round(fitted1).astype(np.int64)
    keep2 = resid1 < dvar5 if dvar5 > 0 else np.ones(n, dtype=bool)
    if keep2.sum() >= 3:
        A2 = np.vstack([idx[keep2] ** 2, idx[keep2], np.ones(keep2.sum())]).T
        try:
            coeffs2 = np.linalg.lstsq(A2, p[keep2], rcond=None)[0]
            a1, b1, c1 = coeffs2
        except np.linalg.LinAlgError:
            pass

    final_fit = a1 * idx ** 2 + b1 * idx + c1
    snapped = np.round(final_fit).astype(np.int64)

    # --- monotonic enforcement: ensure strictly increasing
    for i in range(1, n):
        if snapped[i] <= snapped[i - 1]:
            snapped[i] = snapped[i - 1] + 1

    # --- floor >= 1
    snapped = np.maximum(snapped, 1)

    return snapped


# ---------------------------------------------------------------------------
# 3.  Full DLL-tail recovery: head + tail detect + optional snap
# ---------------------------------------------------------------------------
def dll_tail_positions(gui_pos, Z, split=6000, min_sep=4, snap_r=2,
                       apply_snap=False, end=None):
    """Merge GUI head positions with DLL-detected tail.

    Parameters
    ----------
    gui_pos : (M,) int   — full GUI position grid
    Z : (N, 4) float     — z-scored separated lanes
    split : int           — scan boundary for tail
    min_sep, snap_r       — chan_detect_tail parameters
    apply_snap : bool     — also apply FUN_10019280 quadratic snap to tail?
    end : int or None     — end scan for detection

    Returns
    -------
    merged : (L,) int64  — head + tail positions, sorted
    seq : str             — decoded sequence (argmax on Z at merged)
    """
    gui_pos = np.asarray(gui_pos, dtype=np.int64)
    head = gui_pos[gui_pos < split]

    tail = chan_detect_tail(Z, split=split, end=end, min_sep=min_sep,
                            snap_r=snap_r)

    if apply_snap and len(tail) > 3:
        tail = fun10019280(tail)

    if len(tail) > 0 and len(head) > 0:
        # ensure head[-1] < tail[0]
        if tail[0] <= head[-1]:
            tail = tail[tail > head[-1]]
        merged = np.concatenate([head, tail])
    elif len(tail) > 0:
        merged = tail
    else:
        merged = head

    merged = np.sort(merged)

    # decode sequence
    n = Z.shape[0]
    idx = np.clip(merged, 0, n - 1)
    seq = ''.join(DYE[c] for c in Z[idx].argmax(axis=1))

    return merged, seq
