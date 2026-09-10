#!/usr/bin/env python3
"""Validate a Python port of the Cimarron 3.12 DLL peak-candidate detector
(FUN_1002511d + FUN_10024f29) against the DLL's own record-list and called
peak positions parsed from the .esd ground truth.

DLL algorithm (from Ghidra decomp of decomp_all.c):
  1. envelope  envv[scan] = cross-channel value (min/max/sum of the 4
     shifted-separated lanes) -- FUN_10031976 envelope()
  2. detect envelope local maxima via a rising/falling state machine
     from scans (maxshft+2 .. N):
       state chunks: neutral(0) -> rising(1) when env rises -> falling(2)
       when env falls.  Envelope max recorded at the falling edge.
  3. FUN_10024f29: for each candidate peak at scan P, measure its width in
     scans by walking left/right on the DOMINANT channel's separated lane
     (sc_la) while sc_la > envv[P]/2.  width = right-left+1.
  4. width filter: keep a candidate iff
     width <= 3 * ( (nfrac/2 + sum(widths)) / nfrac )   [nfrac = # kept frac
     in current pass, iterative]
  5. FUN_1001dee1: turn surviving candidates into band records.

The goal: reproduce the DLL's record-list PEAK POSITIONS (bases_positions,
956 for A01) so our called-base set gains the DLL's recall.
"""
import sys, numpy as np

GT = "/media/tv/78B0C7DE1FA7081C1/electropherogram/ground_truth/MB1000_M13_DT_Cp312_MD1/A01.esd"
SEP = "/media/tv/78B0C7DE1FA7081C1/electropherogram/cache_sep/A01.npy"


def env_minsum(lanes):
    """envelope = min of 4 shifted lanes (DLL stores the minimum)."""
    return lanes.min(axis=1)


def env_max(lanes):
    return lanes.max(axis=1)


def env_sum(lanes):
    return lanes.sum(axis=1)


def detect_envelope_maxima(env, start, stop):
    """Rising/falling state machine for envelope local maxima.  Returns list
    of (scan, value) at local maxima (falling edges).  Mirrors FUN_1002511d's
    loop: state 0 neutral, 1 rising, 2 falling."""
    maxima = []
    n = len(env)
    state = 0
    prev = env[start] if start < n else 0.0
    cur = env[start + 1] if start + 1 < n else 0.0
    for c in range(start + 1, stop):
        if state == 0:
            if cur > prev:
                state = 1
            elif cur < prev:
                state = 2
        elif state == 1:
            if cur < prev:
                state = 2
                maxima.append((c - 1, prev))  # local max at c-1
        elif state == 2:
            if cur > prev:
                state = 1
        prev = cur
        nxt = c + 2
        if nxt < n:
            cur = env[nxt]
        else:
            cur = prev
    return maxima


def width_of_peak(lanes_dom, p, thresh, rows):
    """FUN_10024f29: walk left/right on the dominant channel from p while
    sc_la(scan) > thresh.  Returns width in scans (right-left+1)."""
    left = p
    while left - 1 >= 1 and lanes_dom[left - 1] > thresh:
        left -= 1
    right = p
    while right + 1 < rows and lanes_dom[right + 1] > thresh:
        right += 1
    return (right - left) + 1


def dll_peak_detect(lanes, channel_idx_of_scan, start, stop,
                    envelope="min", thr_div=2.0):
    """Full port.  lanes: (N,4) separated mobility-shifted.  Returns list of
    candidate peak scans (arrays), positions only."""
    envfn = {"min": env_minsum, "max": env_max, "sum": env_sum}[envelope]
    env = envfn(lanes)
    chain = None
    maxima = detect_envelope_maxima(env, start, stop)
    cand_scans = [m[0] for m in maxima]
    cand_env = [m[1] for m in maxima]
    widths = []
    kept = []
    for i, p in enumerate(cand_scans):
        ch = channel_idx_of_scan(p) if callable(channel_idx_of_scan) else channel_idx_of_scan
        thresh = cand_env[i] / thr_div
        lanes_dom = lanes[:, ch] if isinstance(ch, int) else _dominant(lanes)
        w = width_of_peak(lanes_dom, p, thresh, lanes.shape[0])
        widths.append(w)
    # width filter (single pass, mirroring FUN_1002511d local_38/44/40):
    # keep peak c iff width[c] <= 3 * ( (n/2 + sum_widths) / n )  == 3*(mean+0.5)
    n = len(cand_scans)
    if n > 1:
        sumw = float(sum(widths))
        limit = 3.0 * ((n / 2.0 + sumw) / n)
        kept = [i for i in range(n) if widths[i] <= limit]
    else:
        kept = list(range(n))
    return np.array([cand_scans[i] for i in kept], dtype=np.int64), \
           np.array([cand_env[i] for i in kept])


def _dominant(lanes):
    return lanes.argmax(axis=1)


def main():
    lanes = np.load(SEP)
    print("lanes", lanes.shape, "dtype", lanes.dtype)
    d = None
    sys.path.insert(0, "/media/tv/78B0C7DE1FA7081C1/electropherogram/sanger_toolkit")
    import extract_training_data as etd
    d = etd.parse_esd(GT)
    rec_peaks = d["bases_positions"]   # 956 record-list peaks
    call_peaks = d["peak_positions"]   # 841 called
    print("GT record peaks:", len(rec_peaks), "called:", len(call_peaks))

    # map DLL scan index -> our array index: assume pass-through for now
    # (both are scan indices on the same grid)
    def match_detected(det, gt, tol):
        det_set = set(det)
        n = 0
        for g in gt:
            if any(abs(g - x) <= tol for x in det_set):
                n += 1
        return n

    combos = [
        ("min", 2.0), ("max", 2.0), ("sum", 2.0),
        ("min", None), ("max", None), ("sum", None),
    ]
    for envname, div in combos:
        det, _ = dll_peak_detect(lanes, None, 2, lanes.shape[0],
                                 envelope=envname, thr_div=div if div else 2.0)
        nrecm = match_detected(det, rec_peaks, 3)
        ncall = match_detected(det, call_peaks, 3)
        prec_rec = nrecm / max(len(det), 1)
        prec_call = ncall / max(len(det), 1)
        print(f"\nenv={envname:4s} thr={div}: detected={len(det):4d} "
              f"| recall vs rec=%5.1f%% ({nrecm}/~{len(rec_peaks)}) "
              f"| prec_rec=%4.1f%%", )
        print(f"        called-match={ncall}/{len(call_peaks)} "
              f"({100.0*ncall/len(call_peaks):.1f}%) prec_call={100*prec_call:.1f}%")


if __name__ == "__main__":
    main()
