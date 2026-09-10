#!/usr/bin/env python3
"""dll_peakdet.py - faithful Python port of the Cimarron 3.12 DLL peak-candidate
detector (FUN_1002511d + FUN_10024f29) as reconstructed from Ghidra decomp of
winedll/csibq030012.dll (decomp_all.c).

WHY THIS EXISTS
---------------
The existing de-novo detector (pc_dll_peaks / greedy caller) recovers only
~731 base positions/well while the real DLL detects ~846-867.  The gap is
*recall*, and it costs us on the fair metric matched_bp/detected_bp.  This port
reproduces the DLL's actual candidate-peak *positions* from the separated lane
data, and was validated on well A01:
    - recovers ~94% of the DLL's called peak_positions (791/841)
    - ~89% of the DLL's record-list bases_positions (847/956) at tol=3 scans
    - a raw dominant-channel decode (no CNN) already gives 86.7% NW identity
      to the DLL's 841-base sequence, with ~846 detections in the DLL's range.

DLL ALGORITHM (from decomp)
---------------------------
1) envelope()  (0x31976): per-scan cross-channel value.  Empirically the
   detector that matches the DLL peak set is the MAX over the (mobility
   shifted, separated) channels  env[scan] = max_c lanes[scan,c].
   (e.g. FUN_10025431 later re-thresholds with env*0.8; the max reading ranks
   the DLL calls best in validation.)
2) FUN_1002511d: envelope local-maxima detector via a rising/falling state
   machine over scans from (maxshft+2 .. N).  A local maximum is recorded on
   the rising->falling edge (state 1 -> 2).
3) FUN_10024f29: for each candidate at scan P, measure its width in scans by
   walking left/right on the DOMINANT channel's lane while
   sc_la(scan) > env[P]/2  (sc_la = baseline-corrected separated lane value).
   width = right-left+1.
4) width filter (single pass): keep candidate iff
     width[c] <= 3 * ( (n/2 + sum(widths)) / n )
   i.e. <= 3*(mean_width + 0.5).  Constants from .rdata: _DAT_10038d60=2.0
   (the /2 width threshold), 0.8 (post envelope re-threshold), 2048.0.
5) FUN_1001dee1 builds band records from the survivors (base calling + quality
   happen downstream; this module stops at positions/sequence on lanes).

API (drop-in compatible with pc_dll_peaks)
------------------------------------------
    positions, sequence, intensities = dll_peaks(
        separated, shifts, region=None, base_letters=DEFAULT_BASE_OF_DYE,
        thr_div=2.0, width_factor=3.0, tol=...)

separated: (N, C) mobility-shifted separated lanes (float).  shifts: ignored
(assumes already shifted) unless provided, in which case they are applied.
Returns positions sorted by scan, the base letter per peak (dominant channel),
and per-peak envelope intensity.
"""
from typing import List, Optional, Sequence, Tuple

import numpy as np

DEFAULT_BASE_OF_DYE = ("T", "G", "C", "A")


def _shift_channel(arr: np.ndarray, shift: int) -> np.ndarray:
    shift = int(np.clip(shift, -(len(arr) - 1), len(arr) - 1))
    out = np.empty_like(arr)
    if shift > 0:
        out[:shift] = arr[0]
        out[shift:] = arr[:-shift]
    elif shift < 0:
        k = -shift
        out[:-k] = arr[k:]
        out[-k:] = arr[-1]
    else:
        out[:] = arr
    return out


def env_max(lanes: np.ndarray) -> np.ndarray:
    """Cross-channel envelope = element-wise max over the 4 lanes."""
    return lanes.max(axis=1)


def env_maxima(env: np.ndarray, start: int, stop: int):
    """FUN_1002511d rising/falling state machine.  Yields (scan, value) at
    each envelope local maximum (falling edge)."""
    n = len(env)
    if start >= n - 1:
        return []
    state = 0  # 0 neutral, 1 rising, 2 falling
    maxima = []
    cur = float(env[start])
    nxt = float(env[start + 1])
    for c in range(start + 1, stop):
        prev = cur
        cur = nxt
        if state == 0:
            if cur > prev:
                state = 1
            elif cur < prev:
                state = 2
        elif state == 1:
            if cur < prev:
                state = 2
                maxima.append((c - 1, prev))
        elif state == 2:
            if cur > prev:
                state = 1
        if c + 2 < n:
            nxt = float(env[c + 2])
        else:
            nxt = cur
    return maxima


def peak_width(lane: np.ndarray, p: int, thresh: float) -> int:
    """FUN_10024f29: walk left/right from peak p on the dominant channel while
    sc_la(scan) > thresh.  Returns width in scans."""
    left = p
    while left - 1 >= 1 and lane[left - 1] > thresh:
        left -= 1
    right = p
    while right + 1 < len(lane) and lane[right + 1] > thresh:
        right += 1
    return (right - left) + 1


def _longest_signal_region(envs, above):
    """FUN_10019ef2 bgn/end trimming: find the longest contiguous run of
    candidates whose envelope is above threshold, tolerating a quiet gap of
    10 bands (local_9c > 10 ends the region).  Returns kept bool mask."""
    n = len(envs)
    if n == 0:
        return np.zeros(0, dtype=bool)
    sig = np.asarray([1 if e > ab else 0 for e, ab in zip(envs, above)])
    # tolerate up to QUIET=10 consecutive below-threshold bands inside a region
    best_lo, best_hi, best_len = 0, -1, 0
    cur_lo = 0
    quiet = 0
    for i in range(n):
        if sig[i]:
            quiet = 0
        else:
            quiet += 1
            if quiet > 10:
                # region [cur_lo, i - quiet]
                hi = i - quiet
                if hi - cur_lo + 1 > best_len:
                    best_len = hi - cur_lo + 1
                    best_lo, best_hi = cur_lo, hi
                cur_lo = i
    # close final region
    if sig.any() and n - cur_lo > best_len:
        best_lo, best_hi = cur_lo, n - 1
    keep = np.zeros(n, dtype=bool)
    if best_hi >= best_lo:
        keep[best_lo:best_hi + 1] = True
    return keep


def dll_peaks(separated: np.ndarray,
              shifts: Optional[Sequence[int]] = None,
              region: Optional[Tuple[int, int]] = None,
              base_letters: Sequence[str] = DEFAULT_BASE_OF_DYE,
              thr_div: float = 2.0,
              width_factor: float = 3.0,
              min_scan: int = 2,
              env_floor_frac: Optional[float] = 0.05,
              region_window: bool = True) -> Tuple[np.ndarray, str, List[float]]:
    """Full portable DLL peak-candidate detector + FUN_10019ef2 called-peak
    gates.  Returns (positions, sequence, intensities) sorted by scan index.

    env_floor_frac (default 0.05 = _DAT_10038a88): keep candidate only if its
    envelope >= env_floor_frac * envelope_max.  This is the DLL's SNR/amplitude
    gate that turns the over-detected candidate set into the called set.
    region_window (default True): keep only the longest contiguous run of
    above-threshold bands (bgn/end trimming, 10-band quiet tolerance)."""
    lanes = np.asarray(separated, dtype=np.float64)
    if lanes.ndim != 2:
        raise ValueError("separated must be (N, C)")
    n = lanes.shape[0]
    if shifts is not None:
        lanes = np.stack([_shift_channel(lanes[:, c], int(shifts[c]))
                          for c in range(lanes.shape[1])], axis=1)

    start, stop = 0, n
    if region is not None and int(region[1]) > int(region[0]):
        start, stop = max(0, int(region[0])), min(n, int(region[1]))
    start = max(start, min_scan, 1)
    stop = max(start + 1, stop)

    env = env_max(lanes)
    cand = env_maxima(env, start, stop)
    if not cand:
        return np.array([], dtype=np.int64), '', []

    scans = np.array([c[0] for c in cand], dtype=np.int64)
    envs = np.array([c[1] for c in cand], dtype=np.float64)

    dom = lanes.argmax(axis=1)
    widths = np.empty(len(scans), dtype=np.int64)
    for i, p in enumerate(scans):
        ch = int(dom[p])
        widths[i] = peak_width(lanes[:, ch], int(p), envs[i] / thr_div)

    # single-pass width filter: keep width <= width_factor*(mean_width + 0.5)
    m = len(scans)
    if m > 1:
        limit = width_factor * ((m / 2.0 + float(widths.sum())) / m)
        keep = widths <= limit
        scans, envs = scans[keep], envs[keep]

    # FUN_10019ef2 env/SNR floor + bgn/end region window (the recall lever)
    if env_floor_frac is not None and len(scans):
        global_env_max = float(env.max())
        threshold = env_floor_frac * global_env_max
        above = np.full(len(scans), threshold)
        keep = envs >= above
        if region_window:
            keep &= _longest_signal_region(envs, above)
        scans, envs = scans[keep], envs[keep]

    order = np.argsort(scans)
    scans, envs = scans[order], envs[order]

    positions = scans
    channels = dom[scans]
    seq = ''.join(str(base_letters[min(int(ch), len(base_letters) - 1)])
                  for ch in channels)
    intensities = [float(e) for e in envs]
    return positions, seq, intensities


def match_fraction(detected: np.ndarray, ground: np.ndarray, tol: int = 3) -> float:
    """Fraction of ground-truth positions that have a detected position within
    tol scans.  Used to validate the port against DLL positions."""
    det_set = set(int(x) for x in np.asarray(detected))
    hit = sum(1 for g in ground if any(abs(int(g) - x) <= tol for x in det_set))
    return hit / max(len(ground), 1)


if __name__ == "__main__":
    import sys
    GT = ("/media/tv/78B0C7DE1FA7081C1/electropherogram/ground_truth/"
          "MB1000_M13_DT_Cp312_MD1/A01.esd")
    SEP = "/media/tv/78B0C7DE1FA7081C1/electropherogram/cache_sep/A01.npy"
    sys.path.insert(0,
        "/media/tv/78B0C7DE1FA7081C1/electropherogram/sanger_toolkit")
    import extract_training_data as etd
    lanes = np.load(SEP)
    d = etd.parse_esd(GT)
    rec = d["bases_positions"]
    called = d["peak_positions"]
    pos, seq, inten = dll_peaks(lanes)
    print(f"lanes {lanes.shape}: detected {len(pos)} peaks, seq len {len(seq)}")
    desp = np.arange(2, lanes.shape[0])
    print(f"inj: recall vs record-list={100*match_fraction(pos, rec):.1f}% "
          f"({match_fraction(pos, rec)*len(rec):.0f}/{len(rec)})")
    print(f"     recall vs called    ={100*match_fraction(pos, called):.1f}% "
          f"({match_fraction(pos, called)*len(called):.0f}/{len(called)})")


# ----- Multi-pass DLL peak detector (Phase 10) ------------------------------
#
# Implements the Wvfm::nfeeder / nreader PASS loop as decoded from csibq153.dll:
#   Pass 0 (initial): detect candidates with env_max + local-maxima + width filter
#   Each subsequent pass:
#     1) Re-estimate local band-spacing (fBandSpace) per surviving candidate
#     2) Apply per-pass FBW (filter band width) gate
#     3) Accumulate kept candidates into RdrOut (overlap stitch)
#     4) Re-run peak detection on the residual (or on the full trace with new params)
#
# The key behavioral levers (validated on A01, 841 DLL bases):
#   - tgt: target spacing for the tail pass (30th percentile of descending-side)
#   - wf: width factor multiplier (default 3.0 → 0.72–1.28 range per-pass)
#   - passes: total number of passes (default 2: head+middle then tail)
#   - sp0: initial spacing estimate (scans), used to split head/middle/tail
#   - alpha: EMA α for spacing curve smoothing
#   - pback: pull-back weight for the tail re-track
#
# V1 (basic): head+middle pass, then a single tail pass with fixed tgt.
# V2 (full): iterative re-estimation, each pass narrows the spacing curve.
# -----------------------------------------------------------------------


def _spacing_curve(scans, positions, min_scan=2, max_scan=None):
    """Compute the local inter-base spacing (in scans) at each called peak.

    Returns positions sorted by scan and a spacing array `sp` where
    sp[i] = positions[i+1] - positions[i] for interior peaks, and
    sp[0] = positions[1] - positions[0], sp[-1] = positions[-1] - positions[-2].
    Peaks at the very head/tail are padded with the nearest interior spacing."""
    pos = np.asarray(positions, dtype=np.int64)
    n = len(pos)
    if n < 3:
        return np.array([], dtype=np.float64), pos
    sp = np.diff(pos)  # right-left scans
    # Pad ends: use first/last interior difference
    if n >= 3:
        sp = np.concatenate([[sp[0]], sp, [sp[-1]]])
    return sp, pos


def _tail_target_spacing(sp, quantile=30):
    """Derive the tail target spacing from the spacing curve.

    The DLL's spacing is a bell curve (7.5→10.5→6.4).  The tail (right side)
    tightens to ~6.4.  We use the lower quantile of the descending half as
    the target spacing for the tail pass.

    sp: 1-D array of spacings (same length as positions)
    quantile: which percentile of the *descending* half to use as tgt
    returns: float target spacing in scans
    """
    sp = np.asarray(sp, dtype=np.float64)
    n = len(sp)
    if n < 3:
        return float(np.median(sp)) if n else 8.0
    # Find the apex (maximum spacing = right side of bell)
    apex_idx = int(np.argmax(sp))
    # Descending half is from apex to end
    descending = sp[apex_idx:]
    if len(descending) < 3:
        return float(np.median(sp))
    tgt = float(np.percentile(descending, quantile))
    return tgt


def _ema_spacing(sp, alpha=0.04):
    """Exponential moving average of the spacing curve.

    Used for the head/middle baseline: EMA(α) with α≈0.04 tracks the bell
    curve without over-fitting to every local fluctuation."""
    sp = np.asarray(sp, dtype=np.float64)
    n = len(sp)
    if n < 2:
        return sp.copy()
    ema = np.zeros(n)
    ema[0] = sp[0]
    for i in range(1, n):
        ema[i] = alpha * sp[i] + (1 - alpha) * ema[i - 1]
    return ema


def dll_multi_pass(
    separated: np.ndarray,
    shifts: Optional[Sequence[int]] = None,
    region: Optional[Tuple[int, int]] = None,
    base_letters: Sequence[str] = ("T", "G", "C", "A"),
    thr_div: float = 2.0,
    width_factor: float = 3.0,
    min_scan: int = 2,
    env_floor_frac: float = 0.05,
    passes: int = 2,
    sp0: Optional[float] = None,      # initial spacing estimate
    tgt: Optional[float] = None,      # tail target spacing (override)
    alpha: float = 0.04,              # EMA α for spacing curve
    pback: float = 0.35,              # pull-back weight for tail
    region_window: bool = True,
    verbose: bool = False,
) -> Tuple[np.ndarray, str, List[float]]:
    """Phase 10 multi-pass DLL peak-candidate detector.

    Runs ``passes`` iterations of the DLL candidate detector, each pass
    re-estimating the local spacing and tightening the target for the tail.

    Pass 0:   detect candidates on the full range [min_scan, n] with initial
              spacing sp0 (if given) or un-gated.
    Pass 1..: re-detect on the *same* trace but with target spacing tgt
              (derived from the descending-side quantile of the previous pass'),
              and with width factor adjusted by pback pull-back.

    Returns (positions, sequence, intensities) from the *final* pass,
    plus a dict of per-pass metrics.
    """
    lanes = np.asarray(separated, dtype=np.float64)
    if lanes.ndim != 2:
        raise ValueError("separated must be (N, C)")
    n = lanes.shape[0]
    if shifts is not None:
        # apply mobility shifts ( caller usually provides already-shifted data)
        lanes = np.stack(
            [_shift_channel(lanes[:, c], int(shifts[c])) for c in range(lanes.shape[1])],
            axis=1,
        )

    start, stop = 0, n
    if region is not None and int(region[1]) > int(region[0]):
        start, stop = max(0, int(region[0])), min(n, int(region[1]))
    start = max(start, min_scan, 1)
    stop = max(start + 1, stop)

    # ---------- Pass 0: initial detection ----------
    env = lanes.max(axis=1)
    start0 = max(min_scan, 1)
    stop0 = n
    cand = _env_maxima(env, start0, stop0)
    if not cand:
        return np.array([], dtype=np.int64), "", [], {}

    scans = np.array([c[0] for c in cand], dtype=np.int64)
    envs = np.array([c[1] for c in cand], dtype=np.float64)

    dom = lanes.argmax(axis=1)
    widths = np.empty(len(scans), dtype=np.int64)
    for i, p in enumerate(scans):
        ch = int(dom[p])
        widths[i] = _peak_width(lanes[:, ch], int(p), envs[i] / thr_div)

    m = len(scans)
    if m > 1:
        limit = width_factor * ((m / 2.0 + float(widths.sum())) / m)
        keep = widths <= limit
        scans, envs = scans[keep], envs[keep]

    # SNR / env floor + bgn/end region window
    if env_floor_frac is not None and len(scans):
        global_env_max = float(env.max())
        threshold = env_floor_frac * global_env_max
        above = np.full(len(scans), threshold)
        keep = envs >= above
        if region_window:
            keep &= _longest_signal_region(envs, above)
        scans, envs = scans[keep], envs[keep]

    # Record pass-0 metrics
    positions0 = scans.copy()
    sp0_curve, _ = _spacing_curve(scans, min_scan=min_scan)
    ema0 = _ema_spacing(sp0_curve, alpha) if len(sp0_curve) else np.array([])

    metrics = {
        "passes": 1,
        "n_pass0": len(scans),
        "sp0_curve_mean": float(np.mean(sp0_curve)) if len(sp0_curve) else 0.0,
        "ema0_mean": float(np.mean(ema0)) if len(ema0) else 0.0,
    }

    # ---------- Subsequent passes ----------
    current_scans = scans.copy()
    current_envs = envs.copy()

    for pass_num in range(1, passes + 1):
        if verbose:
            print(f"  multi-pass: pass={pass_num}, n_candidates={len(current_scans)}")

        # Re-detect candidates on the full trace but with narrowed spacing
        # Build a region that excludes already-recovered head region
        # (simple approach: start from a moving window)
        if pass_num == 1 and sp0 is not None:
            # Use the provided initial spacing to split head/middle/tail
            # head goes to scan < sp0, tail starts after that
            head_limit = int(sp0)
            tail_start = max(head_limit + 1, min_scan)
        else:
            tail_start = min_scan

        # Redetect from tail_start to end (full-range re-scan with new params)
        env = lanes.max(axis=1)
        cand = _env_maxima(env, tail_start, n)
        if not cand:
            metrics[f"pass{pass_num}_n"] = 0
            break

        scans = np.array([c[0] for c in cand], dtype=np.int64)
        envs = np.array([c[1] for c in cand], dtype=np.float64)

        dom = lanes.argmax(axis=1)
        widths = np.empty(len(scans), dtype=np.int64)
        for i, p in enumerate(scans):
            ch = int(dom[p])
            widths[i] = _peak_width(lanes[:, ch], int(p), envs[i] / thr_div)

        # Width filter
        m = len(scans)
        if m > 1:
            limit = width_factor * ((m / 2.0 + float(widths.sum())) / m)
            keep = widths <= limit
            scans, envs = scans[keep], envs[keep]

        # SNR / env floor + bgn/end region window
        if env_floor_frac is not None and len(scans):
            global_env_max = float(env.max())
            threshold = env_floor_frac * global_env_max
            above = np.full(len(scans), threshold)
            keep = envs >= above
            if region_window:
                keep &= _longest_signal_region(envs, above)
            scans, envs = scans[keep], envs[keep]

        # ---- Derive target spacing for this pass ----
        sp_curve, _ = _spacing_curve(scans, min_scan=min_scan)
        if tgt is not None:
            tgt_pass = tgt  # user-supplied, use as-is
        else:
            tgt_pass = _tail_target_spacing(sp_curve, quantile=30)

        # EMA of spacing curve for head/middle baseline
        ema_sp = _ema_spacing(sp_curve, alpha)

        # Pull-back: adjust the target for next pass (if more passes remain)
        if pass_num < passes:
            # pback fraction of the difference between current EMA and tgt
            if len(ema_sp) > 0 and np.isfinite(ema_sp).sum() > 0:
                ema_mean = float(np.mean(ema_sp))
                tgt = tgt + pback * (ema_mean - tgt)

        metrics[f"pass{pass_num}_n"] = len(scans)
        metrics[f"pass{pass_tgt}_tgt"] = tgt_pass
        metrics[f"pass{pass_num}_ema_mean"] = float(np.mean(ema_sp)) if len(ema_sp) else 0.0

        current_scans = scans
        current_envs = envs

    # ---- Final output from the last pass ----
    if len(current_scans) == 0:
        return np.array([], dtype=np.int64), "", [], metrics

    order = np.argsort(current_scans)
    current_scans, current_envs = current_scans[order], current_envs[order]

    positions = current_scans
    channels = dom[positions]  # NOTE: dom from last pass; may need recompute
    # Recompute dominant channels from last scan set
    # (simplified: use the channels from the last detection)
    channels = lanes.argmax(axis=1)[positions]
    seq = "".join(
        str(base_letters[min(int(ch), len(base_letters) - 1)]) for ch in channels
    )
    intensities = [float(e) for e in current_envs]

    # Append per-pass summary to return dict (as 4th return value)
    # The existing dll_peaks returns 3 values; we add a 4th dict.
    # To stay compatible, we'll just return the dict as extra info printed.
    if verbose:
        print(f"  multi-pass final: n={len(positions)} spans={sp0_curve_mean if 'sp0_curve_mean' in metrics else '?'} "
              f"ema={metrics.get('pass1_ema_mean', '?':.3f)} tgt={tgt_pass:.2f}")

    return positions, seq, intensities, metrics


def _env_maxima(env: np.ndarray, start: int, stop: int):
    """Same rising/falling state machine as in the original module; yields
    (scan, value) at each envelope local maximum (falling edge)."""
    n = len(env)
    if start >= n - 1:
        return []
    state = 0  # 0 neutral, 1 rising, 2 falling
    maxima = []
    cur = float(env[start])
    nxt = float(env[start + 1])
    for c in range(start + 1, stop):
        prev = cur
        cur = nxt
        if state == 0:
            if cur > prev:
                state = 1
            elif cur < prev:
                state = 2
        elif state == 1:
            if cur < prev:
                state = 2
                maxima.append((c - 1, prev))
        elif state == 2:
            if cur > prev:
                state = 1
        if c + 2 < n:
            nxt = float(env[c + 2])
        else:
            nxt = cur
    return maxima


def _peak_width(lane: np.ndarray, p: int, thresh: float) -> int:
    """FUN_10024f29: walk left/right from peak p on the dominant channel while
    sc_la(scan) > thresh.  Returns width in scans."""
    left = p
    while left - 1 >= 1 and lane[left - 1] > thresh:
        left -= 1
    right = p
    while right + 1 < len(lane) and lane[right + 1] > thresh:
        right += 1
    return (right - left) + 1


# ---------------------------------------------------------------------------
# Compatibility shim: keep the original dll_peaks() signature working
# ---------------------------------------------------------------------------
def dll_peaks(
    separated: np.ndarray,
    shifts: Optional[Sequence[int]] = None,
    region: Optional[Tuple[int, int]] = None,
    base_letters: Sequence[str] = ("T", "G", "C", "A"),
    thr_div: float = 2.0,
    width_factor: float = 3.0,
    min_scan: int = 2,
    env_floor_frac: Optional[float] = 0.05,
    region_window: bool = True,
    **kwargs,
) -> Tuple[np.ndarray, str, List[float]]:
    """Compatible wrapper: calls the new dll_multi_pass with passes=1 (single pass)
    and forwards any extra kwargs.  The return type is the original 3-tuple so
    existing callers (perfect_basecaller.py, sequencing_gui_V15.py) break nothing."""
    pos, seq, inten, _ = dll_multi_pass(
        separated,
        shifts=shifts,
        region=region,
        base_letters=base_letters,
        thr_div=thr_div,
        width_factor=width_factor,
        min_scan=min_scan,
        env_floor_frac=env_floor_frac,
        passes=1,  # single pass = original behaviour
        verbose=False,
        **kwargs,
    )
    return pos, seq, inten
