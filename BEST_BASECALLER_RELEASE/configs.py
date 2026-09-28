"""
Instrument × mode configuration for the unified MegaBACE ET basecaller.

  instrument: mb1000 | mb4000
  mode:       accuracy | length

accuracy  — maximize longest error-free run while keeping identity high (≥95% gate)
length    — maximize usable read length under the same ID ≥95% gate

One library (track_bases); four resolved config dicts — not four codebases.
"""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

import numpy as np

_ASSETS = Path(__file__).resolve().parent / "assets"

_BASE: dict[str, Any] = dict(
    use_gaussian_reconstruction=True,
    gaussian_recon_segment_size=384,
    gaussian_recon_noise_reg=0.06,
    gaussian_recon_sigma_scale=1.05,
    auto_trim=True,
    trim_method="percentile",
    trim_quality_percentile=10.0,
    use_combined_channel_score=True,
    window_frac=(0.70, 1.30),
    local_norm_window=1800,
    channel_peak_bonus=0.7,
    pullback_weight=0.008,
    ema_alpha=0.08,
    baseline_window=151,
    position_adaptive_spectral=True,
    pullback_profile=(0.33, 0.008, 0.001),
    local_hardzone_deconv=False,
    use_multipass_wiener=False,
    mobility_shifts=[-2, -1, -2, 2],
    base_order="TGCA",
)

_MODE_ACCURACY: dict[str, Any] = dict(
    # Precision-oriented (MonkeyCode plate result): strong Wiener + deep Q-trim
    # → high %ID and long error-free runs; fewer matched bases after trim.
    channel_peak_bonus=0.7,
    pullback_weight=0.008,
    pullback_profile=(0.33, 0.008, 0.001),
    window_frac=(0.70, 1.30),
    ema_alpha=0.08,
    gaussian_recon_noise_reg=0.128,  # was ~0.06; longest rises to ~0.128
    gaussian_recon_sigma_scale=1.05,
    auto_trim=True,
    trim_method="percentile",
    trim_quality_percentile=38.0,  # deep trim lifts %ID + longest_run
)

_MODE_LENGTH: dict[str, Any] = dict(
    # Length-oriented: keep more bases; softer reg/trim than accuracy/precision
    channel_peak_bonus=1.0,
    pullback_weight=0.006,
    pullback_profile=(0.28, 0.010, 0.002),
    window_frac=(0.65, 1.35),
    ema_alpha=0.10,
    gaussian_recon_noise_reg=0.06,
    gaussian_recon_sigma_scale=1.05,
    auto_trim=True,
    trim_method="percentile",
    trim_quality_percentile=12.0,
    local_hardzone_deconv=True,
    hardzone_frac=(0.28, 0.55),
    hardzone_noise_reg=0.12,
    hardzone_spacing_scale=1.12,
    hardzone_blend=0.30,
    hardzone_segment_size=384,
)


def _load_mb4000_chm() -> np.ndarray | None:
    path = _ASSETS / "MB4000_CHM.npz"
    if not path.is_file():
        return None
    z = np.load(path)
    if "supervised" in z:
        return np.asarray(z["supervised"], dtype=float)
    if "blend" in z:
        return np.asarray(z["blend"], dtype=float)
    return None


def _instrument_overlay(instrument: str) -> dict[str, Any]:
    inst = instrument.lower().strip()
    if inst in ("mb1000", "1000", "megabace1000"):
        return dict(
            instrument="mb1000",
            spectral_separation_matrix="default",
            position_adaptive_spectral=True,
        )
    if inst in ("mb4000", "4000", "megabace4000"):
        chm = _load_mb4000_chm()
        ov: dict[str, Any] = dict(
            instrument="mb4000",
            position_adaptive_spectral=False,
            mobility_shifts=[-2, -1, -2, 2],
        )
        if chm is not None:
            ov["spectral_separation_matrix"] = chm
        else:
            ov["spectral_separation_matrix"] = "default"
            ov["_warn_missing_mb4000_chm"] = True
        return ov
    raise ValueError(f"Unknown instrument {instrument!r}; use mb1000 or mb4000")


def _mode_overlay(mode: str) -> dict[str, Any]:
    m = mode.lower().strip()
    if m in ("accuracy", "acc", "error_free", "longest_error_free"):
        return dict(mode="accuracy", **_MODE_ACCURACY)
    if m in ("length", "len", "long", "longest_read"):
        return dict(mode="length", **_MODE_LENGTH)
    raise ValueError(f"Unknown mode {mode!r}; use accuracy or length")


def resolve_config(
    instrument: str = "mb1000",
    mode: str = "accuracy",
    **overrides: Any,
) -> dict[str, Any]:
    """Merge base + instrument + mode + optional overrides into track_bases kwargs."""
    cfg = deepcopy(_BASE)
    inst = _instrument_overlay(instrument)
    mod = _mode_overlay(mode)
    cfg.update(inst)
    cfg.update(mod)
    for k in ("instrument", "mode", "_warn_missing_mb4000_chm"):
        cfg.pop(k, None)
    for k, v in overrides.items():
        if v is not None:
            cfg[k] = v
    if cfg.get("mobility_shifts") is not None:
        cfg["mobility_shifts"] = tuple(int(round(x)) for x in cfg["mobility_shifts"])
    return cfg


def describe(instrument: str = "mb1000", mode: str = "accuracy") -> str:
    inst = _instrument_overlay(instrument)
    mod = _mode_overlay(mode)
    lines = [
        f"instrument={inst.get('instrument', instrument)}  mode={mod.get('mode', mode)}",
        f"  spectral: {'MB4000 supervised CHM' if inst.get('instrument') == 'mb4000' else 'DEFAULT_CHM (MB1000)'}",
        f"  channel_peak_bonus={mod.get('channel_peak_bonus')}",
        f"  window_frac={mod.get('window_frac')}",
        f"  hardzone={mod.get('local_hardzone_deconv', False)}",
        "  quality gate (eval): identity >= 95% vs reference",
    ]
    if inst.get("_warn_missing_mb4000_chm"):
        lines.append("  WARNING: assets/MB4000_CHM.npz missing — using default CHM")
    return "\n".join(lines)


CONFIGS = {
    "pos_bonus07": resolve_config("mb1000", "accuracy"),
    "pos_profile": resolve_config("mb1000", "length"),
    # Legacy tuning variant: mild mid hard-zone deconv on the accuracy base,
    # with the lighter (pre-deep-trim) quality cut.
    "hz_soften": resolve_config(
        "mb1000", "accuracy",
        trim_quality_percentile=10.0,
        local_hardzone_deconv=True,
        hardzone_frac=(0.28, 0.55),
        hardzone_noise_reg=0.12,
        hardzone_spacing_scale=1.12,
        hardzone_blend=0.30,
        hardzone_segment_size=384,
    ),
    "mb1000_accuracy": resolve_config("mb1000", "accuracy"),
    "mb1000_length": resolve_config("mb1000", "length"),
    "mb4000_accuracy": resolve_config("mb4000", "accuracy"),
    "mb4000_length": resolve_config("mb4000", "length"),
}

PRESETS = ("mb1000_accuracy", "mb1000_length", "mb4000_accuracy", "mb4000_length")
