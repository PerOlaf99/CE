"""
Core data loading and processing for MegaBACE Sequence Analyzer.
Wraps best_basecaller configs and optional Cimarron-style DSP stages.
"""
from __future__ import annotations

import sys
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict, Any, Tuple

import numpy as np

# Locate best_basecaller package
_ROOT = Path(__file__).resolve().parent
for _p in (
    _ROOT.parent / "BEST_BASECALLER_RELEASE",
    Path("/home/per/Nedlastinger/BEST_BASECALLER_RELEASE"),
    _ROOT.parent / "best_basecaller" / "best_basecaller",
    Path("/home/workdir/artifacts/BEST_BASECALLER_RELEASE"),
    Path("/home/workdir/artifacts/best_basecaller/best_basecaller"),
):
    if (_p / "cimarron_basecaller").is_dir() or (_p / "cimarron_basecaller").exists():
        sys.path.insert(0, str(_p))
        break

try:
    from cimarron_basecaller.rsd_io import read_rsd, to_acgt_trace
except ImportError:
    read_rsd = to_acgt_trace = None  # type: ignore

try:
    from cimarron_basecaller.spacing_caller import track_bases
except ImportError:
    track_bases = None  # type: ignore

try:
    from configs import CONFIGS as BB_CONFIGS
except ImportError:
    BB_CONFIGS = {}


# ---------------------------------------------------------------------------
# Analysis parameter set (Sequence Analyzer "knobs")
# ---------------------------------------------------------------------------
@dataclass
class AnalysisSettings:
    """Mirrors typical MegaBACE Sequence Analyzer / basecall settings."""

    # Basecaller version
    basecaller: str = "pos_bonus07"  # pos_bonus07 | pos_profile | hz_soften | raw_peaks

    # Channel / dye
    base_order: str = "TGCA"  # instrument dye order → ACGT columns

    # Baseline
    baseline_method: str = "percentile"  # percentile | none
    baseline_window: int = 151

    # Smoothing
    smooth_enable: bool = True
    smooth_window: int = 5  # odd Savitzky-Golay style window if used later

    # Spectral separation
    spectral_enable: bool = True
    position_adaptive_spectral: bool = True

    # Mobility
    mobility_enable: bool = True

    # Band filter / deconv
    use_gaussian_reconstruction: bool = True
    gaussian_recon_segment_size: int = 384
    gaussian_recon_noise_reg: float = 0.05
    use_multipass_wiener: bool = False

    # Spacing tracker
    use_combined_channel_score: bool = True
    channel_peak_bonus: float = 0.7
    pullback_weight: float = 0.008
    ema_alpha: float = 0.08
    window_frac_lo: float = 0.70
    window_frac_hi: float = 1.30
    local_norm_window: int = 1800
    pullback_profile_enable: bool = True
    pullback_frac: float = 0.33
    pullback_start: float = 0.008
    pullback_end: float = 0.001

    # Display / signal region
    signal_start: int = 0
    signal_end: int = 0  # 0 = full

    # View
    view_mode: str = "processed"  # raw | baseline | processed | called

    def to_track_kwargs(self) -> Dict[str, Any]:
        """Map settings → track_bases kwargs (best_basecaller)."""
        kw: Dict[str, Any] = dict(
            use_gaussian_reconstruction=self.use_gaussian_reconstruction,
            gaussian_recon_segment_size=self.gaussian_recon_segment_size,
            gaussian_recon_noise_reg=self.gaussian_recon_noise_reg,
            use_multipass_wiener=self.use_multipass_wiener,
            use_combined_channel_score=self.use_combined_channel_score,
            channel_peak_bonus=self.channel_peak_bonus,
            pullback_weight=self.pullback_weight,
            ema_alpha=self.ema_alpha,
            window_frac=(self.window_frac_lo, self.window_frac_hi),
            local_norm_window=self.local_norm_window,
            baseline_window=self.baseline_window,
            position_adaptive_spectral=self.position_adaptive_spectral and self.spectral_enable,
            local_hardzone_deconv=False,
        )
        if self.pullback_profile_enable:
            kw["pullback_profile"] = (
                self.pullback_frac,
                self.pullback_start,
                self.pullback_end,
            )
        # Merge named config defaults if present
        if self.basecaller in BB_CONFIGS:
            base = dict(BB_CONFIGS[self.basecaller])
            base.update({k: v for k, v in kw.items() if v is not None})
            # ensure flags
            base.setdefault("local_hardzone_deconv", False)
            base.setdefault("use_multipass_wiener", self.use_multipass_wiener)
            return base
        return kw


BASECALLER_VERSIONS = {
    "pos_bonus07": "Best dual-aware (recommended)",
    "pos_profile": "Max matched_bp (longer tail)",
    "hz_soften": "Mild mid-zone less deconv",
    "raw_peaks": "Minimal processing + envelope peaks",
}


@dataclass
class TraceDocument:
    """One loaded well / file."""

    path: Path
    well: str
    raw: np.ndarray  # (n, 4) instrument order before map
    base_order: str
    acgt: np.ndarray  # (n, 4) A,C,G,T
    current: Optional[np.ndarray] = None
    sequence: str = ""
    peak_positions: List[int] = field(default_factory=list)
    qualities: List[float] = field(default_factory=list)
    settings_used: Optional[AnalysisSettings] = None

    @property
    def n_scans(self) -> int:
        return int(self.acgt.shape[0])


def discover_rsd(folders: List[Path]) -> List[Path]:
    files: List[Path] = []
    for folder in folders:
        if not folder.is_dir():
            continue
        files.extend(sorted(folder.glob("*.rsd")))
        files.extend(sorted(folder.glob("*.RSD")))
    # unique
    seen = set()
    out = []
    for f in files:
        k = str(f.resolve())
        if k not in seen:
            seen.add(k)
            out.append(f)
    return out


def load_rsd(path: Path, base_order: str = "TGCA") -> TraceDocument:
    if read_rsd is None or to_acgt_trace is None:
        raise RuntimeError(
            "cimarron_basecaller not found. Place BEST_BASECALLER_RELEASE next to this app."
        )
    rsd = read_rsd(str(path))
    # rsd may be dict or object
    if isinstance(rsd, dict):
        ch = np.column_stack([rsd[f"ch{i}"] for i in range(1, 5)]) if "ch1" in rsd else rsd.get("channels")
        cur = rsd.get("current")
    else:
        # try attributes
        try:
            acgt, order = to_acgt_trace(rsd, base_order=base_order)
            cur = getattr(rsd, "current", None)
            return TraceDocument(
                path=path,
                well=path.stem,
                raw=acgt.copy(),
                base_order=order,
                acgt=acgt,
                current=cur,
            )
        except Exception:
            pass
        acgt, order = to_acgt_trace(rsd, base_order=base_order)
        return TraceDocument(
            path=path, well=path.stem, raw=acgt.copy(), base_order=order, acgt=acgt
        )

    acgt, order = to_acgt_trace(rsd, base_order=base_order)
    return TraceDocument(
        path=path,
        well=path.stem,
        raw=np.asarray(acgt, float),
        base_order=order,
        acgt=np.asarray(acgt, float),
        current=None if cur is None else np.asarray(cur, float),
    )


def run_basecall(doc: TraceDocument, settings: AnalysisSettings) -> TraceDocument:
    """Run selected basecaller; updates sequence + peak_positions."""
    if track_bases is None:
        raise RuntimeError("track_bases not available")

    order = "ACGT"
    kw = settings.to_track_kwargs()
    # mobility / spectral off if disabled
    if not settings.mobility_enable:
        kw["mobility_shifts"] = (0, 0, 0, 0)
    if not settings.spectral_enable:
        kw["position_adaptive_spectral"] = False
        # identity matrix if supported
        try:
            kw["spectral_separation_matrix"] = np.eye(4)
        except Exception:
            pass

    if settings.basecaller == "raw_peaks":
        # minimal: local maxima on envelope
        env = doc.acgt.max(axis=1)
        peaks = []
        for i in range(2, len(env) - 2):
            if env[i] >= env[i - 1] and env[i] > env[i + 1] and env[i] > 0.05 * env.max():
                if not peaks or i - peaks[-1] >= 5:
                    peaks.append(i)
        seq = "".join(order[int(np.argmax(doc.acgt[p]))] for p in peaks)
        doc.sequence = seq
        doc.peak_positions = peaks
        doc.qualities = [float(env[p]) for p in peaks]
        doc.settings_used = settings
        return doc

    seq, quals, bands = track_bases(doc.acgt, base_order=order, **kw)
    doc.sequence = seq
    doc.peak_positions = [int(b.position) for b in bands]
    doc.qualities = list(quals) if quals is not None else []
    doc.settings_used = settings
    return doc


def display_trace(doc: TraceDocument, settings: AnalysisSettings) -> np.ndarray:
    """Return (n,4) array for plotting according to view_mode."""
    if settings.view_mode == "raw":
        return doc.raw
    # For baseline/processed without full intermediate API, show acgt
    # (full pipeline intermediates would need deeper hooks)
    return doc.acgt
