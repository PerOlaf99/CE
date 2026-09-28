"""Windowed / segmented calling on top of track_bases.

Folds per-window GUI JSON settings (matrix, mobility, baseline, norm,
prominence, …) into the global spacing tracker:

  1. Load ordered windows from A01_START_END.json (or any WELL_START_END.json).
  2. For each window, run track_bases with window-mapped kwargs on the full
     trace (padding context kept), then keep only bases whose peak scan falls
     inside [start, end).
  3. Stitch by scan position (earlier window wins on overlap).

When sanger_toolkit is available on sys.path, ``call_windows_gui_path``
replays the exact GUI DSP + greedy path (the ~98% non-gap gold path).
"""
from __future__ import annotations

import glob
import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Optional

import numpy as np

from .spacing_caller import track_bases, TrackedBase


@dataclass
class WindowSpec:
    start: int
    end: int
    path: str
    name: str
    cfg: dict


def discover_windows(
    json_dir: str | Path,
    well: str = "A01",
    min_width: int = 80,
) -> list[WindowSpec]:
    """Find WELL_START_END.json files and load them sorted by start scan."""
    json_dir = Path(json_dir)
    pattern = str(json_dir / f"{well}_*.json")
    found: list[WindowSpec] = []
    for path in glob.glob(pattern):
        name = os.path.basename(path)
        m = re.match(rf"{re.escape(well)}_(\d+)_(\d+)\.json$", name)
        if not m:
            continue
        a, b = int(m.group(1)), int(m.group(2))
        if b - a < min_width:
            continue
        with open(path) as fh:
            cfg = json.load(fh)
        found.append(WindowSpec(start=a, end=b, path=path, name=name, cfg=cfg))
    found.sort(key=lambda w: (w.start, w.end))
    return found


def _json_to_track_kwargs(cfg: dict, base: Optional[dict] = None) -> dict:
    """Map GUI JSON fields onto track_bases keyword arguments."""
    kw: dict[str, Any] = dict(base or {})

    # Mobility: GUI stores [ch0,ch1,ch2,ch3] in instrument channel order.
    # track_bases expects shifts aligned to ACGT columns after to_acgt_trace.
    # With base_order TGCA → ACGT remap, GUI shifts index the same raw channels
    # that to_acgt_trace permutes; pass as list in ACGT order by reordering
    # TGCA shifts → A,C,G,T = indices of A,C,G,T in "TGCA" = 3,2,1,0.
    if "mobility_shifts" in cfg:
        sh = [int(s) for s in cfg["mobility_shifts"]]
        if len(sh) == 4:
            # GUI channel order matches RSD dye order TGCA:
            # ch0=T, ch1=G, ch2=C, ch3=A  → ACGT shifts = [sh[3], sh[2], sh[1], sh[0]]
            kw["mobility_shifts"] = [sh[3], sh[2], sh[1], sh[0]]

    if "matrix" in cfg:
        M = np.asarray(cfg["matrix"], dtype=np.float64)
        if M.shape == (4, 4):
            # Reorder rows/cols from TGCA to ACGT
            # TGCA indices: T=0,G=1,C=2,A=3 → ACGT = [3,2,1,0]
            perm = [3, 2, 1, 0]
            kw["spectral_separation_matrix"] = M[np.ix_(perm, perm)]

    if "baseline_window" in cfg:
        bw = float(cfg["baseline_window"])
        # GUI sometimes uses huge airPLS windows (5e4); clamp for robust baseline
        if bw > 2000:
            bw = 201
        kw["baseline_window"] = int(max(51, bw if bw >= 51 else 151))

    if "norm_window" in cfg:
        kw["local_norm_window"] = int(cfg["norm_window"])
    if "smooth_window" in cfg:
        sw = int(cfg["smooth_window"])
        kw["smoothing_window"] = max(1, min(sw, 7))
    if "prominence_frac" in cfg:
        kw["min_prominence"] = float(cfg["prominence_frac"])

    # Prefer adaptive spectral when windows disagree on matrix
    kw.setdefault("position_adaptive_spectral", False)
    kw.setdefault("use_gaussian_reconstruction", True)
    kw.setdefault("gaussian_recon_segment_size", 384)
    kw.setdefault("use_combined_channel_score", True)
    kw.setdefault("channel_peak_bonus", 1.1)
    kw.setdefault("pullback_weight", 0.019)
    kw.setdefault("ema_alpha", 0.10)
    kw.setdefault("window_frac", (0.75, 1.25))
    # Disable auto_trim inside windows — outer stitch owns the range
    kw["auto_trim"] = False
    return kw


def track_bases_windowed(
    trace: np.ndarray,
    windows: Iterable[WindowSpec],
    base_order: str = "ACGT",
    base_config: Optional[dict] = None,
    overlap_policy: str = "first",  # first window wins on conflict
) -> tuple[str, list[float], list[TrackedBase]]:
    """Run track_bases per window with mapped JSON params; stitch by scan.

    Returns (sequence, qualities, tracked_bases) over the union of windows.
    """
    windows = list(windows)
    if not windows:
        seq, quals, bands = track_bases(trace, base_order=base_order, **(base_config or {}))
        return seq, quals, bands

    claimed: dict[int, tuple[str, float, TrackedBase]] = {}
    for w in windows:
        kw = _json_to_track_kwargs(w.cfg, base_config)
        seq, quals, bands = track_bases(trace, base_order=base_order, **kw)
        for b, q, letter in zip(bands, quals, seq):
            pos = int(getattr(b, "position", getattr(b, "pos", -1)))
            if pos < w.start or pos >= w.end:
                continue
            if pos in claimed and overlap_policy == "first":
                continue
            claimed[pos] = (letter, float(q), b)

    ordered = sorted(claimed.items(), key=lambda kv: kv[0])
    sequence = "".join(letter for _, (letter, _, _) in ordered)
    qualities = [q for _, (_, q, _) in ordered]
    tracked = [tb for _, (_, _, tb) in ordered]
    return sequence, qualities, tracked


def call_windows_gui_path(
    raw_tgca: np.ndarray,
    windows: Iterable[WindowSpec],
) -> tuple[list[int], str]:
    """Exact GUI DSP + greedy path (requires sanger_toolkit on sys.path).

    ``raw_tgca`` is (n_scans, 4) in instrument TGCA channel order (as from
    parse_rsd Channel1..4), NOT ACGT-reordered.
    """
    from dsp import dsp_full_pipeline  # type: ignore
    from basecall import (  # type: ignore
        pc_call_bases_greedy,
        pc_call_bases_with_shifts,
        pc_fill_in_combined_peaks,
        pc_hybrid_greedy_lifetrace,
    )

    claimed: dict[int, str] = {}
    for w in windows:
        cfg = w.cfg
        matrix = np.asarray(cfg["matrix"], dtype=np.float64)
        shifts = [int(s) for s in cfg["mobility_shifts"]]
        bl_method = cfg.get("baseline_method", "airPLS")
        bl_win = float(cfg.get("baseline_window", 1e5))
        bl_win2 = cfg.get("baseline_window2", None)
        if bl_win2 is not None:
            bl_win2 = float(bl_win2)
        smooth_method = cfg.get("smooth_method", "Butterworth")
        smooth_window = int(cfg.get("smooth_window", 4))
        smooth_order = int(cfg.get("smooth_order", 5))
        apply_pt = cfg.get("matrix_apply_point", "smoothed")
        band_low = cfg.get("band_low", 0) or None
        band_high = cfg.get("band_high", 0) or None
        if band_low is not None and float(band_low) <= 1:
            band_low = None
        if band_high is not None and float(band_high) <= 1:
            band_high = None
        band_order = int(cfg.get("band_order", 2))

        _, _, _, _, separated, _ = dsp_full_pipeline(
            raw_tgca,
            shifts,
            bl_method,
            bl_win,
            smooth_method,
            smooth_window,
            smooth_order,
            matrix,
            baseline_window2=bl_win2,
            matrix_apply_point=apply_pt,
            band_low=band_low,
            band_high=band_high,
            band_order=band_order,
        )

        raw_method = cfg.get("basecall_method", 0)
        if isinstance(raw_method, str):
            key = raw_method.strip().lower()
            if key in ("0", "greedy"):
                method = 0
            elif key in ("1", "prominence", "fill"):
                method = 1
            elif key in ("2", "hybrid", "hybrid_lt"):
                method = 2
            else:
                try:
                    method = int(raw_method)
                except ValueError:
                    method = 0
        else:
            method = int(raw_method)

        min_distance = float(cfg.get("min_distance", 6))
        prom = float(cfg.get("prominence_frac", 0.1))
        norm_win = int(cfg.get("norm_window", 200))
        region = (w.start, w.end)

        if method == 2:
            pos, seq, *_ = pc_hybrid_greedy_lifetrace(
                separated, shifts,
                window=max(1, int(round(min_distance))),
                min_frac=prom,
                norm_window=max(1, norm_win),
                region=region,
            )
        elif method == 1:
            pos, seq, *_ = pc_call_bases_with_shifts(
                separated, shifts,
                min_distance=max(1, int(round(min_distance))),
                prominence_frac=prom,
                norm_window=max(1, norm_win),
                region=region,
            )
            if cfg.get("fill_in", False):
                try:
                    pos, seq, *_ = pc_fill_in_combined_peaks(
                        separated, shifts, positions=pos,
                        fill_gap=int(cfg.get("fill_gap", 4)),
                    )
                except TypeError:
                    pass
        else:
            pos, seq, *_ = pc_call_bases_greedy(
                separated, shifts,
                window=max(1, int(round(min_distance))),
                min_frac=prom,
                norm_window=max(1, norm_win),
                region=region,
            )

        for p, letter in zip(pos, seq):
            p = int(p)
            if p < w.start or p >= w.end:
                continue
            if p not in claimed:
                claimed[p] = letter

    ordered = sorted(claimed.items())
    positions = [p for p, _ in ordered]
    sequence = "".join(letter for _, letter in ordered)
    return positions, sequence
