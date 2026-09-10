"""Per-window GUI-style tuning loop backed by the ESD as a labeled target.

Implements the user's workflow from sequencing_gui_V15.py in automated form:

  1. You pick a *call region* as a SCAN-INDEX window [from_scan, to_scan].
  2. The tool runs the caller over that window with a candidate parameter set.
  3. Similarity is computed ONLY within the window: my called bases whose peak
     scan position falls in the range are compared against the ESD bases whose
     peak scan position falls in the same range (position-based, matching the
     GUI's "Call region From/To" cursors).  The metric is the local
     (Smith-Waterman) alignment / normalized-length identity.
  4. The tool searches the parameter space (normalization window/percentile,
     baseline window, smoothing, spectral matrix global-vs-position-adaptive,
     peak-detect prominence/threshold) to MAXIMIZE the in-window identity to
     the ESD -- the user's "get 100% match for that region" target.
  5. Each region's winning settings are SAVED to a persistent per-region map
     (JSON) so they can later be folded into a position-adaptive preprocessor.
     This is the "save the setting" step of the GUI loop.

Because no parameter is globally right (a winner for one window rarely fits
another -- the GUI observation), the map is inherently per-region.  It is also
inherently fit-to-ESD: that is the labeled truth target here (DLL replication),
which on M13 is ~95% correct against biological truth -- so a warning is
recorded alongside when that caveat applies.
"""
import json
import os
import sys
from dataclasses import dataclass, field

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, '/home/per/Nedlastinger/Claude/cimarron_basecaller')

import numpy as np

from sanger_toolkit.align import pc_nw_identity, ref_local_identity
from cimarron_basecaller.rsd_io import read_rsd, to_acgt_trace

try:
    import cimarron_basecaller as C
    _has_segmented = True
    SEGMENTED = C.track_bases_segmented
except Exception:  # pragma: no cover
    _has_segmented = False
    SEGMENTED = None


# ---------------------------------------------------------------------------
# Windowed (position-based) similarity vs the ESD
# ---------------------------------------------------------------------------

@dataclass
class WindowResult:
    """Similarity of a call to the ESD restricted to a scan window."""
    from_scan: int
    to_scan: int
    call_seq: str                 # my bases whose peak scan is in-window
    esd_seq: str                  # ESD bases whose peak scan is in-window
    identity_pct: float           # local-alignment normalized identity
    nw_identity_pct: float        # global NW alignment identity of the windows
    matches: int
    mismatches: int
    indels: int
    aligned: int
    n_call: int                   # bases I called in-window
    n_esd: int                    # ESD bases in-window
    details: dict = field(default_factory=dict)


def _in_window_bases(call_positions, call_seq, esd_positions, esd_seq,
                     from_scan, to_scan):
    """Select, by peak scan position, the called bases and ESD bases that fall
    in [from_scan, to_scan).  Both lists must be parallel to their sequences
    (positions[i] is the scan of sequence[i])."""
    mask = (call_positions >= from_scan) & (call_positions < to_scan)
    sub_call = "".join(b for b, m in zip(call_seq, mask) if m)
    esd_mask = (esd_positions >= from_scan) & (esd_positions < to_scan)
    sub_esd = "".join(b for b, m in zip(esd_seq, esd_mask) if m)
    return sub_call, sub_esd


def _positional_match_one_to_one(call_positions, esd_positions, from_scan,
                                 to_scan, tol=6.0):
    """Strict set-match in the window: how many of the ESD peaks are matched by
    a distinct call within `tol` scans (one-to-one, two-pointer), and how many
    calls are left unmatched.  Returns (matched_esd, unmatched_calls, n_esd,
    n_call).  'Same peaks as ESD' = matched_esd == n_esd AND unmatched_calls == 0,
    i.e. every ESD peak covered and no extra over-called peaks."""
    mine = sorted(float(p) for p in call_positions
                  if from_scan <= p < to_scan)
    esd = sorted(float(p) for p in esd_positions
                 if from_scan <= p < to_scan)
    i = j = matched = 0
    while i < len(mine) and j < len(esd):
        if abs(mine[i] - esd[j]) <= tol:
            matched += 1; i += 1; j += 1
        elif mine[i] < esd[j]:
            i += 1
        else:
            j += 1
    # unmatched calls = total calls not consumed by a match
    # (greedy two-pointer consumes at most the matched ones)
    unmatched_calls = len(mine) - matched
    return matched, unmatched_calls, len(esd), len(mine)


def window_similarity(call_positions, call_seq, esd_positions, esd_seq,
                      from_scan, to_scan, tol=6.0):
    """Position-window similarity vs the ESD, scoring 'same peaks as ESD'.

    Restricts both calls and ESD bases to the scan window, then scores a strict
    one-to-one positional set-match (the 6-scan DLL coordinate frame).  The
    headline metric ``set_match_pct`` is 100.0 iff the window's call count
    equals the ESD count AND every ESD peak is matched by a distinct call within
    tolerance with none left over.  A secondary ``posmatch6`` (ESD coverage %)
    and the legacy local-identity are retained as diagnostics.  Unlike the GUI's
    local-alignment identity, this metric does NOT reward over-calling."""
    sub_call, sub_esd = _in_window_bases(
        call_positions, call_seq, esd_positions, esd_seq, from_scan, to_scan)
    matched, unmatched, n_esd, n_call = _positional_match_one_to_one(
        call_positions, esd_positions, from_scan, to_scan, tol=tol)
    set_match = 100.0 if (n_esd and matched == n_esd and unmatched == 0) else 0.0
    posmatch = (100.0 * matched / n_esd) if n_esd else 0.0
    ident, matches, mmis, ind, aligned, score, *_ = ref_local_identity(sub_call, sub_esd)
    return WindowResult(
        from_scan=from_scan, to_scan=to_scan,
        call_seq=sub_call, esd_seq=sub_esd,
        identity_pct=ident, nw_identity_pct=float(pc_nw_identity(sub_call, sub_esd)),
        matches=matches, mismatches=mmis, indels=ind, aligned=aligned,
        n_call=n_call, n_esd=n_esd,
        details={"score": score, "aligned_frac": (aligned / n_esd) if n_esd else 0.0,
                 "posmatch6": posmatch, "set_match_pct": set_match,
                 "matched": matched, "unmatched": unmatched, "params": {}},
    )


# ---------------------------------------------------------------------------
# Per-region parameter search
# ---------------------------------------------------------------------------

@dataclass
class SearchSpace:
    """Parallel arrays of the knobs to search per window.  Default covers the
    separators that most change region-to-region (normalization, baseline,
    smoothing, spectral matrix, peak-detect sensitivity)."""
    local_norm_window: list = field(default_factory=lambda: [200, 300, 500])
    local_norm_percentile: list = field(default_factory=lambda: [88, 92, 95])
    baseline_window: list = field(default_factory=lambda: [101, 151, 251])
    smoothing_window: list = field(default_factory=lambda: [1, 2, 4])
    position_adaptive_spectral: list = field(default_factory=lambda: [False, True])
    tail_min_prominence: list = field(default_factory=lambda: [0.025, 0.035, 0.05])
    head_min_prominence: list = field(default_factory=lambda: [0.04, 0.05])


def _iter_params(space: SearchSpace):
    """Yield dicts covering the (product of) knob options.  Too many knobs at
    full product is explosive, so a coarse outer grid is used: for the
    per-window search we random-sample a bounded number of combos by default
    (see `limit`), except the spectral matrix toggle which is always tried both
    ways at the top of each sample."""
    import random
    keys = ["local_norm_window", "local_norm_percentile", "baseline_window",
            "smoothing_window", "tail_min_prominence", "head_min_prominence"]
    combos = list(np.ndindex(*(len(getattr(space, k)) for k in keys)))
    for combo in combos:
        params = {k: getattr(space, k)[c] for k, c in zip(keys, combo)}
        for pad in space.position_adaptive_spectral:
            params["position_adaptive_spectral"] = pad
            yield params


def _call_with(params, trace, base_order, from_scan, to_scan):
    """Thread `params` into the segmented caller (the committed default),
    honoring the position-adaptive spectral knock as a per-region option."""
    s, q, bases = SEGMENTED(
        trace, base_order=base_order,
        position_adaptive_spectral=params.get("position_adaptive_spectral", False),
        local_norm_window=params["local_norm_window"],
        local_norm_percentile=params.get("local_norm_percentile", 95.0),
        baseline_window=params["baseline_window"],
        smoothing_window=params["smoothing_window"],
        # per-region sensitivity via the effective prominence knobs searched.
        tail_min_prominence=params["tail_min_prominence"],
        head_min_prominence=params["head_min_prominence"],
    )
    positions = np.array([b.position for b in bases], dtype=float)
    # The call sequence position frame: rely on the caller's per-base scan.
    return s, positions, bases


def tune_region(rsd_path, esd_data, from_scan, to_scan,
                space: SearchSpace | None = None, limit=64, verbose=True):
    """Search the parameter space for the window [from_scan, to_scan] and
    return the best (max in-window ESD identity) WindowResult + the params."""
    space = space or SearchSpace()
    trace, order = to_acgt_trace(read_rsd(rsd_path), base_order="TGCA")
    esd_positions = np.asarray(esd_data["peak_positions"], dtype=float)
    esd_seq = esd_data["sequence"]

    best = None
    n = 0
    for params in _iter_params(space):
        if n >= limit:
            break
        n += 1
        try:
            s, positions, bases = _call_with(params, trace, order, from_scan, to_scan)
        except Exception:
            continue
        r = window_similarity(positions, s, esd_positions, esd_seq, from_scan, to_scan)
        r.details["params"] = params
        # Rank by the strict set-match (same peaks as ESD): count must equal AND
        # every ESD peak covered with no over-called peaks. Ties broken by
        # positional coverage, then identity.
        def key(r):
            d = r.details
            return (d["set_match_pct"], d["posmatch6"], r.identity_pct)
        if best is None or key(r) > key(best):
            best = r
    if verbose and best is not None:
        d = best.details
        print(f"window [{from_scan},{to_scan}): set-match={d['set_match_pct']:.0f}% "
              f"({d['matched']}/{best.n_esd} ESD covered, {d['unmatched']} extra calls, "
              f"n_call={best.n_call}/n_esd={best.n_esd}, posmatch6={d['posmatch6']:.1f}%) "
              f"params={best.details.get('params')}")
    return best


# ---------------------------------------------------------------------------
# Persistence of the per-region parameter map
# ---------------------------------------------------------------------------

REGION_MAP_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "region_settings_map.json")


def save_region_map(regions, path=REGION_MAP_PATH):
    """Persist a list of (well, from_scan, to_scan, params) winning settings.

    The map is intentionally per-region: a given parameter set is only claimed
    to be optimal for the scan window it was tuned on, exactly matching the GUI
    observation that no global setting fits every region."""
    payload = [{"well": w, "from_scan": lo, "to_scan": hi, "params": p}
               for (w, lo, hi, p) in regions]
    existing = {}
    if os.path.exists(path):
        try:
            existing = json.load(open(path))
        except Exception:
            existing = {}
    for item in payload:
        key = f"{item['well']}:{item['from_scan']}:{item['to_scan']}"
        existing[key] = item["params"]
    with open(path, "w") as f:
        json.dump(existing, f, indent=2)
    return path


def load_region_map(path=REGION_MAP_PATH):
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return {}


def collect_region_map(rsd_path, esd_data, windows, space=None, limit=64):
    """Run tune_region over an ordered list of scan windows and accumulate a
    saved per-region map.  `windows` is a list of (from_scan, to_scan)."""
    well = os.path.basename(rsd_path)[: -len(".rsd")]
    saved = []
    for lo, hi in windows:
        best = tune_region(rsd_path, esd_data, lo, hi, space=space, limit=limit)
        if best is not None:
            saved.append((well, lo, hi, best.details.get("params")))
    path = save_region_map(saved)
    print(f"saved {len(saved)} region params to {path}")
    return saved


# ---------------------------------------------------------------------------
# Visual window verification (the plots the user tunes against)
# ---------------------------------------------------------------------------

def plot_window(rsd_path, esd_data, call_positions, call_seq, from_scan,
                to_scan, out_png=None, trail=40, title_prefix=""):
    """Draw the window [from_scan, to_scan): the separated/trace envelope in
    that scan range with my called peaks (circles) and the ESD peak positions
    (triangles) overlaid, so the caller's peak PATTERN can be compared to the
    DLL's by eye.  Saves to `out_png` if given, else shows the plot."""
    import matplotlib
    matplotlib.use("Agg" if out_png else "TkAgg")
    import matplotlib.pyplot as plt
    trace, order = to_acgt_trace(read_rsd(rsd_path), base_order="TGCA")
    env = trace.max(axis=1)
    lo = max(0, from_scan - trail); hi = min(len(env), to_scan + trail)
    esd_p = np.asarray(esd_data["peak_positions"], float)
    my_p = np.array([p for p in call_positions if lo <= p <= hi], float)
    esd_w = esd_p[(esd_p >= lo) & (esd_p <= hi)]
    fig, ax = plt.subplots(figsize=(12, 4))
    ax.plot(np.arange(lo, hi), env[lo:hi], color="#888", lw=0.7)
    ax.plot(my_p, np.full_like(my_p, 0.02 * env[lo:hi].max()),
            "o", color="#1c7ed6", ms=5, label=f"my calls ({len(my_p)})")
    ax.plot(esd_w, np.full_like(esd_w, 0.3 * env[lo:hi].max()),
            "^", color="#d6336c", ms=7, label=f"ESD peaks ({len(esd_w)})")
    ax.axvspan(from_scan, to_scan, color="#ffd43b", alpha=0.15)
    ax.set_xlabel("scan")
    ax.set_title(f"{title_prefix} window [{from_scan},{to_scan})")
    ax.legend(loc="upper right", fontsize=8)
    ax.set_ylim(0, 1.1 * env[lo:hi].max())
    if out_png:
        fig.savefig(out_png, dpi=110); plt.close(fig); return out_png
    plt.show()


# ---------------------------------------------------------------------------
# REPL helper: tune a single region against its ESD and report the diagnostics
# ---------------------------------------------------------------------------

def _esd_for(well):
    """Locate the matching .esd for a well name (A01 -> A01.esd) under the
    repo's analyzed-data tree."""
    import glob
    esds = glob.glob(
        "wineprefix/drive_c/Program Files/Molecular Dynamics/MegaBACE/"
        "AnalyzedData/MB1000_M13_DT_wine_Cp312_MD1/*.esd")
    for e in esds:
        if os.path.basename(e).startswith(well + "."):
            from sanger_toolkit.cimarrontv import read_esd
            return read_esd(e)
    raise FileNotFoundError(well)


if __name__ == "__main__":
    # Usage:
    #   window_tuner.py A01                       -> tune default windows, save map
    #   window_tuner.py A01 5300 5800             -> tune ONE window, report, plot PNG
    #   window_tuner.py A01 5300 5800 --plot w   -> also write window A01_5300_5800.png
    import sys
    args = sys.argv[1:]
    well = args[0] if args else "A01"
    esd = _esd_for(well)
    from_scan = int(args[1]) if len(args) > 1 and args[1].isdigit() else None
    if from_scan is not None and len(args) > 2 and args[2].isdigit():
        to_scan = int(args[2])
        best = tune_region(f"MB1000_M13_DT/{well}.rsd", esd, from_scan, to_scan, limit=96)
        write_png = "--plot" in sys.argv or "w" in sys.argv
        if best is not None and write_png:
            trace, order = to_acgt_trace(read_rsd(f"MB1000_M13_DT/{well}.rsd"), base_order="TGCA")
            s, pos, bs = _call_with(best.details["params"], trace, order, from_scan, to_scan)
            out = f"{well}_{from_scan}_{to_scan}.png"
            plot_window(f"MB1000_M13_DT/{well}.rsd", esd, pos, s, from_scan,
                        to_scan, out_png=out, title_prefix=f"{well}")
            print(f"verification plot -> {out}")
    else:
        windows = [(5300, 5800), (5800, 6300), (6300, 6800)]
        collect_region_map(f"MB1000_M13_DT/{well}.rsd", esd, windows, limit=48)