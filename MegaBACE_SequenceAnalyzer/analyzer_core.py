"""
Core data loading, processing and export for the MegaBACE Sequence Analyzer.

Wraps best_basecaller configs and Cimarron-style DSP stages, plus loaders
for the MegaBACE raw (.rsd) and analyzed (.esd) containers and writers for
the manual's export formats (FASTA/.seq, SCF, ABD, text).

Stages mirror the Molecular Dynamics incremental base-calling process from
the Sequence Analyzer User's Guide v2.0:
    1. Baseline Subtraction
    2. Spectral Separation
    3. Normalization
    4. Band Filter
    5. Mobility Shift Correction
    6. Quality Assessment
"""
from __future__ import annotations

import sys
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict, Any, Tuple

import numpy as np

# Locate best_basecaller package (release + in-repo candidate paths)
_ROOT = Path(__file__).resolve().parent
for _p in (
    _ROOT.parent / "BEST_BASECALLER_RELEASE",
    Path("/home/per/Nedlastinger/BEST_BASECALLER_RELEASE"),
    _ROOT.parent / "best_basecaller" / "best_basecaller",
    _ROOT.parent / "best_basecaller",
    Path("/home/workdir/artifacts/BEST_BASECALLER_RELEASE"),
    Path("/home/workdir/artifacts/best_basecaller/best_basecaller"),
):
    if (_p / "cimarron_basecaller").is_dir() or (_p / "cimarron_basecaller").exists():
        sys.path.insert(0, str(_p))
        break

try:
    from cimarron_basecaller.rsd_io import read_rsd, to_acgt_trace as rsd_to_acgt
except ImportError:  # pragma: no cover
    read_rsd = rsd_to_acgt = None  # type: ignore

try:
    from cimarron_basecaller.spacing_caller import track_bases
except ImportError:  # pragma: no cover
    track_bases = None  # type: ignore

try:
    from cimarron_basecaller.scf_io import write_scf
except ImportError:  # pragma: no cover
    write_scf = None  # type: ignore

try:
    from cimarron_basecaller.abd_io import read_abd, to_acgt_trace as abd_to_acgt
except ImportError:  # pragma: no cover
    read_abd = abd_to_acgt = None  # type: ignore

try:
    from configs import CONFIGS as BB_CONFIGS
except ImportError:  # pragma: no cover
    BB_CONFIGS = {}


def _track_signature() -> set:
    """Parameter names accepted by the vendored track_bases (robust to
    either the repository or BEST_BASECALLER_RELEASE copy being found)."""
    if track_bases is None:
        return set()
    try:
        import inspect
        return set(inspect.signature(track_bases).parameters)
    except Exception:
        return set()


def _filter_track_kwargs(kw: Dict[str, Any]) -> Dict[str, Any]:
    """Drop kwargs the installed track_bases does not accept."""
    ok = _track_signature()
    if not ok:
        return kw
    return {k: v for k, v in kw.items() if k in ok}


# ---------------------------------------------------------------------------
# Analysis parameter set (Sequence Analyzer "knobs")
# ---------------------------------------------------------------------------
@dataclass
class AnalysisSettings:
    """Mirrors typical MegaBACE Sequence Analyzer / basecall settings."""

    # Basecaller version
    basecaller: str = "pos_bonus07"  # pos_bonus07 | pos_profile | hz_soften | raw_peaks

    # Channel / dye
    base_order: str = "TGCA"  # instrument dye order -> ACGT columns

    # Baseline
    baseline_method: str = "percentile"  # percentile | none
    baseline_window: int = 151

    # Smoothing / band filter
    smooth_enable: bool = True
    smooth_window: int = 5

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
    view_mode: str = "processed"  # raw | baseline | spectral | normalize | band | mobility | called

    def to_track_kwargs(self) -> Dict[str, Any]:
        """Map settings -> track_bases kwargs (best_basecaller)."""
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
            base.setdefault("local_hardzone_deconv", False)
            base.setdefault("use_multipass_wiener", self.use_multipass_wiener)
            return base
        return _filter_track_kwargs(kw)


BASECALLER_VERSIONS = {
    "pos_bonus07": "Best dual-aware (recommended)",
    "pos_profile": "Max matched_bp (longer tail)",
    "hz_soften": "Mild mid-zone less deconv",
    "raw_peaks": "Minimal processing + envelope peaks",
}

# Sequence Analyzer User's Guide base caller list (mapped onto our callers)
MANUAL_BASECALLERS = [
    "Cimarron 1.53 Slim Phredify",
    "Cimarron 1.53 Phat",
    "Cimarron 1.31",
    "Molecular Dynamics (incremental)",
]
GUILD_CALLER_TO_INTERNAL = {
    "Cimarron 1.53 Slim Phredify": "pos_bonus07",
    "Cimarron 1.53 Phat": "pos_profile",
    "Cimarron 1.31": "hz_soften",
    "Molecular Dynamics (incremental)": "raw_peaks",
}
INTERNAL_CALLER_TO_GUILD = {v: k for k, v in GUILD_CALLER_TO_INTERNAL.items()}

BASE_COLORS = {"A": "#00AA00", "C": "#0000DD", "G": "#111111", "T": "#DD0000"}


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
    # Incremental-stage intermediates (each (n,4) ACGT)
    stage_trace: Optional[np.ndarray] = None      # last computed stage
    baseline_trace: Optional[np.ndarray] = None
    spectral_trace: Optional[np.ndarray] = None
    normalized_trace: Optional[np.ndarray] = None
    band_trace: Optional[np.ndarray] = None
    mobility_trace: Optional[np.ndarray] = None

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
    seen = set()
    out = []
    for f in files:
        k = str(f.resolve())
        if k not in seen:
            seen.add(k)
            out.append(f)
    return out


def discover_esd(folders: List[Path]) -> List[Path]:
    """Find analyzed .esd files (sorted by well column first)."""
    files: List[Path] = []
    for folder in folders:
        if not folder.is_dir():
            continue
        files.extend(sorted(folder.glob("*.esd")))
        files.extend(sorted(folder.glob("*.ESD")))
    return files


def _col_to_int(col: str) -> int:
    return (ord(col[0].upper()) - ord("A")) * 12 + int(col[1:])


def load_rsd(path: Path, base_order: str = "TGCA") -> TraceDocument:
    if read_rsd is None or rsd_to_acgt is None:
        raise RuntimeError(
            "cimarron_basecaller not found. Place BEST_BASECALLER_RELEASE next to this app."
        )
    rsd = read_rsd(str(path))
    if isinstance(rsd, dict):
        ch = np.column_stack([rsd[f"ch{i}"] for i in range(1, 5)]) if "ch1" in rsd else rsd.get("channels")
        cur = rsd.get("current")
        acgt, order = rsd_to_acgt(np.asarray(ch, float), base_order=base_order)
        return TraceDocument(
            path=path, well=path.stem, raw=np.asarray(ch, float), base_order=order,
            acgt=acgt, current=None if cur is None else np.asarray(cur, float),
        )
    cur = getattr(rsd, "current", None)
    acgt, order = rsd_to_acgt(rsd, base_order=base_order)
    try:
        raw = acgt.copy()
    except Exception:
        raw = acgt
    return TraceDocument(
        path=path, well=path.stem, raw=raw, base_order=order, acgt=acgt,
        current=None if cur is None else np.asarray(cur, float),
    )


def load_esd(path: Path, base_order: str = "TGCA", rsd_fallback: Optional[Path] = None) -> TraceDocument:
    """Parse an analyzed .esd file (called sequence, qualities, positions).

    Trace data is not stored in the .esd; if the matching raw .rsd sits next
    to it (same well), load it so the electropherogram can be drawn.
    """
    try:
        sys.path.insert(0, str(_ROOT.parent))
        from extract_training_data import parse_esd
    except Exception:
        parse_esd = None  # type: ignore

    res: Dict[str, Any] = {}
    if parse_esd is not None:
        try:
            res = parse_esd(str(path))
        except Exception:
            res = {}

    well = path.stem if isinstance(path.stem, str) else str(path)
    acgt = np.empty((0, 4))
    cur = None
    if rsd_fallback is not None and rsd_fallback.exists():
        try:
            d = load_rsd(rsd_fallback, base_order=base_order)
            acgt, cur = d.acgt, d.current
        except Exception:
            pass

    seq = res.get("sequence", "")
    pos = res.get("peak_positions", res.get("bases_positions", np.array([])))
    q = res.get("quality_scores", np.array([]))
    q = np.atleast_1d(np.asarray(q, dtype=float)) if q is not None else np.array([])
    pos = np.atleast_1d(np.asarray(pos, dtype=float)) if pos is not None else np.array([])
    if len(pos) < len(seq):
        pos = np.arange(len(seq)).astype(float)
    if len(q) < len(seq):
        q = np.zeros(len(seq))

    d = TraceDocument(
        path=path, well=well, raw=acgt, base_order=base_order, acgt=acgt, current=cur,
        sequence=str(seq), peak_positions=[int(p) for p in pos[: len(seq)]],
        qualities=[float(x) for x in q[: len(seq)]],
    )
    return d


def load_abd(path: Path, base_order: str = "CAGT") -> TraceDocument:
    """Load an analyzed .abd ABIF container (DLL basecall + processed trace)."""
    if read_abd is None:
        raise RuntimeError("abd_io not available")
    abd = read_abd(str(path))
    acgt = abd_to_acgt(abd.trace_processed, base_order=base_order)
    seq = abd.bases
    pos = np.asarray(abd.peak_positions, float)
    if len(pos) < len(seq):
        pos = np.arange(len(seq)).astype(float)
    return TraceDocument(
        path=path, well=path.stem, raw=acgt.copy(), base_order="ACGT", acgt=acgt,
        sequence=str(seq), peak_positions=[int(p) for p in pos[: len(seq)]],
        qualities=[0.0] * len(seq),
    )


def run_basecall(doc: TraceDocument, settings: AnalysisSettings) -> TraceDocument:
    """Run selected basecaller; updates sequence + peak_positions + stages."""
    if track_bases is None:
        raise RuntimeError("track_bases not available")

    order = "ACGT"
    kw = settings.to_track_kwargs()
    if not settings.mobility_enable:
        kw["mobility_shifts"] = (0, 0, 0, 0)
    if not settings.spectral_enable:
        kw["position_adaptive_spectral"] = False
        try:
            kw["spectral_separation_matrix"] = np.eye(4)
        except Exception:
            pass

    if settings.basecaller == "raw_peaks":
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
    doc.qualities = list(quals) if quals is not None else [] * len(seq)
    doc.settings_used = settings
    return doc


# ---------------------------------------------------------------------------
# Incremental DSP stages (Molecular Dynamics incremental base calling)
# ---------------------------------------------------------------------------
def _percentile_baseline(col: np.ndarray, window: int) -> np.ndarray:
    """Local rolling minimum percentile for a single channel."""
    from scipy.ndimage import minimum_filter1d
    w = max(3, int(window))
    return minimum_filter1d(col, min(w, len(col)), mode="nearest")


def stage_baseline(settings: AnalysisSettings) -> np.ndarray:
    """Stage 1 placeholder — actual per-doc work done in _stage_baseline below."""
    raise NotImplementedError


def stage_baseline_doc(doc: TraceDocument, settings: AnalysisSettings) -> np.ndarray:
    """Baseline subtraction: set baseline signal to zero for all four traces."""
    if settings.baseline_method == "none":
        return doc.acgt.copy()
    out = np.empty_like(doc.acgt)
    for c in range(doc.acgt.shape[1]):
        bl = _percentile_baseline(doc.acgt[:, c], settings.baseline_window)
        out[:, c] = np.clip(doc.acgt[:, c] - bl, 0, None)
    doc.baseline_trace = out
    doc.stage_trace = out
    return out


_DEFAULT_CHM = np.array([
    [1.00, 0.06, 0.02, 0.01],
    [0.05, 1.00, 0.05, 0.02],
    [0.02, 0.05, 1.00, 0.05],
    [0.01, 0.02, 0.06, 1.00],
])


def stage_spectral_doc(doc: TraceDocument, settings: AnalysisSettings,
                       base: Optional[np.ndarray] = None) -> np.ndarray:
    """Spectral separation: remove cross-talk between the four traces."""
    src = base if base is not None else (
        doc.baseline_trace if doc.baseline_trace is not None else doc.acgt)
    try:
        chm_inv = np.linalg.pinv(_DEFAULT_CHM)
        out = np.clip(src @ chm_inv.T, 0, None)
    except Exception:
        out = src.copy()
    doc.spectral_trace = out
    doc.stage_trace = out
    return out


def stage_normalize_doc(doc: TraceDocument, settings: AnalysisSettings,
                        base: Optional[np.ndarray] = None) -> np.ndarray:
    """Normalization: uniform peak heights across channels and run."""
    src = base if base is not None else (
        doc.spectral_trace if doc.spectral_trace is not None else doc.acgt)
    out = np.empty_like(src)
    win = max(151, settings.local_norm_window)
    for c in range(src.shape[1]):
        col = src[:, c]
        from scipy.ndimage import uniform_filter1d
        pad = win // 2
        rolling_max = np.maximum.reduce(
            [np.roll(col, -i) for i in range(max(1, win // 16))])  # fast envelope
        s = np.percentile(col, 95) + 1e-9
        out[:, c] = np.clip(col / s, 0, None)
    doc.normalized_trace = out
    doc.stage_trace = out
    return out


def stage_band_doc(doc: TraceDocument, settings: AnalysisSettings,
                   base: Optional[np.ndarray] = None) -> np.ndarray:
    """Band filter: enhance real peaks, filter out noise peaks."""
    from scipy.ndimage import gaussian_filter1d
    src = base if base is not None else (
        doc.normalized_trace if doc.normalized_trace is not None else doc.acgt)
    sigma = max(1.0, settings.baseline_window / 30.0)
    out = np.empty_like(src)
    for c in range(src.shape[1]):
        smooth = gaussian_filter1d(src[:, c], sigma=sigma)
        out[:, c] = np.clip(smooth, 0, None) * 1.0
    doc.band_trace = out
    doc.stage_trace = out
    return out


def stage_mobility_doc(doc: TraceDocument, settings: AnalysisSettings,
                       base: Optional[np.ndarray] = None,
                       shifts: Optional[List[int]] = None) -> np.ndarray:
    """Mobility shift correction: compensate dye-specific run-off."""
    src = base if base is not None else (
        doc.band_trace if doc.band_trace is not None else doc.acgt)
    if shifts is None:
        # Estimate relative to channel 0 via cross-correlation
        shifts = [0, 0, 0, 0]
        try:
            ref = src[:, 0]
            for c in range(1, src.shape[1]):
                if ref.std() == 0 or src[:, c].std() == 0:
                    continue
                x = np.correlate(src[:, c], ref, mode="same")
                peak = int(np.argmax(x)) - len(ref) // 2
                shift = -int(round(peak * 0.5))
                shifts[c] = max(-20, min(20, shift))
        except Exception:
            pass
    out = np.empty_like(src)
    n = src.shape[0]
    for c in range(src.shape[1]):
        s = max(-n, min(n, int(shifts[c])))
        if s == 0:
            out[:, c] = src[:, c]
        elif s > 0:
            out[: n - s, c] = src[s:, c]
            out[n - s:, c] = 0
        else:
            out[-s:, c] = src[: n + s, c]
            out[: -s, c] = 0
    doc.mobility_trace = out
    doc.stage_trace = out
    return out


INCREMENTAL_STAGES = [
    ("baseline", "Baseline Subtraction"),
    ("spectral", "Spectral Separation"),
    ("normalize", "Normalization"),
    ("band", "Band Filter"),
    ("mobility", "Mobility Shift Correction"),
]


def stage_document(doc: TraceDocument, settings: AnalysisSettings,
                   stage: str) -> np.ndarray:
    """Run every stage up to and including `stage` (incremental semantics)."""
    cur = stage_baseline_doc(doc, settings)
    if stage == "baseline":
        return cur
    cur = stage_spectral_doc(doc, settings, cur)
    if stage == "spectral":
        return cur
    cur = stage_normalize_doc(doc, settings, cur)
    if stage == "normalize":
        return cur
    cur = stage_band_doc(doc, settings, cur)
    if stage == "band":
        return cur
    cur = stage_mobility_doc(doc, settings, cur)
    return cur


def display_trace(doc: TraceDocument, settings: AnalysisSettings) -> np.ndarray:
    """Return (n,4) ACGT array for plotting according to view_mode / stage."""
    mode = settings.view_mode
    if mode == "raw":
        return doc.raw if doc.raw.size else doc.acgt
    if mode == "baseline" and doc.baseline_trace is not None:
        return doc.baseline_trace
    if mode == "spectral" and doc.spectral_trace is not None:
        return doc.spectral_trace
    if mode == "normalize" and doc.normalized_trace is not None:
        return doc.normalized_trace
    if mode == "band" and doc.band_trace is not None:
        return doc.band_trace
    if mode == "mobility" and doc.mobility_trace is not None:
        return doc.mobility_trace
    return doc.acgt


# ---------------------------------------------------------------------------
# Quality assessment (per-base 0..100 + quality index)
# ---------------------------------------------------------------------------
def assess_quality(doc: TraceDocument, settings: AnalysisSettings) -> Tuple[List[float], float]:
    """Weighted per-base quality (peak height / spacing / symmetry) -> 0..100,
    plus a single quality index for the whole read (per SSM manual)."""
    n = len(doc.sequence)
    if n == 0:
        return [], 0.0
    pos = np.asarray(doc.peak_positions[:n], float)
    q = np.asarray(doc.qualities[:n], float) if len(doc.qualities) >= n else np.zeros(n)
    if pos.size < 2:
        spacing = np.full(n, 1.0)
    else:
        spacing = np.ones(n)
        if pos.size >= 2:
            d = np.diff(pos)
            pad = d[:1][0] if d.size else 1.0
            spacing = np.concatenate([[pad], d])
        spacing = np.clip(spacing, 1e-3, None)
    sp_med = float(np.median(spacing[: max(1, min(n, 50))]) or 1.0)
    sp_score = np.clip(1.0 - np.abs(spacing - sp_med) / (sp_med * 0.5), 0, 1)
    q_norm = q / (np.percentile(q, 95) + 1e-9) if (q.any() and np.percentile(q, 95) > 0) else q
    h_score = np.clip(q_norm, 0, 1)
    sym = np.ones(n)
    quality = 100.0 * np.clip(0.7 * h_score + 0.2 * sp_score + 0.1 * sym, 0, 1)
    # quality index: mean over the high-quality block
    good = quality >= 30.0
    if good.any():
        idx = float(np.mean(quality[good]))
    else:
        idx = float(np.mean(quality)) if n else 0.0
    return [float(x) for x in quality], idx


# ---------------------------------------------------------------------------
# Export writers (User's Guide ch. 5)
# ---------------------------------------------------------------------------
def export_fasta(doc: TraceDocument, out: Path, high_quality_only: bool = False,
                 min_quality: float = 30.0) -> None:
    seq = doc.sequence
    if high_quality_only and doc.qualities:
        seq = "".join(
            c for c, q in zip(seq, doc.qualities[: len(seq)]) if q >= min_quality)
    text = f">{doc.well} len={len(seq)} plate={doc.path.parent.name}\n"
    text += "\n".join(seq[i:i + 60] for i in range(0, len(seq), 60)) + "\n"
    out.write_text(text)


def export_scf(doc: TraceDocument, out: Path) -> None:
    """Write processed trace + called bases + peak indices to SCF v3.10."""
    if write_scf is None:
        raise RuntimeError("scf_io.write_scf not available")
    trace = doc.acgt if doc.acgt.size else np.empty((0, 4))
    n = len(doc.sequence)
    peak_idx = np.asarray(doc.peak_positions[:n], dtype=np.int64)
    if len(peak_idx) < n:
        peak_idx = np.concatenate([peak_idx, np.arange(len(peak_idx), n).astype(np.int64)])
    probs = np.full((n, 4), 10, dtype=np.uint8)  # placeholder confidence bytes
    comments = {
        "well": doc.well,
        "plate": str(doc.path.parent.name),
        "base_order": doc.base_order,
        "n_scans": str(int(doc.n_scans)),
    }
    write_scf(str(out), trace, doc.sequence, peak_idx, probs, comments=comments)


def export_abd(doc: TraceDocument, out: Path, base_order: str = "CAGT") -> None:
    """Write an ABIF (.abd) container with raw + processed traces and the
    called sequence (readable back with cimarron_basecaller.abd_io)."""
    _ABL_LETTER = {0: "C", 1: "A", 2: "G", 3: "T"}

    raw = doc.acgt if doc.acgt.size else np.empty((0, 4))
    # reorder ACGT -> ABD column order (C,A,G,T)
    src_col = {b: i for i, b in enumerate("ACGT")}
    order = ["C", "A", "G", "T"]
    raw_abd = np.column_stack([raw[:, src_col[b]] for b in order]) if raw.size else raw

    proc = doc.stage_trace if doc.stage_trace is not None else (
        doc.band_trace if doc.band_trace is not None else raw)
    proc_abd = np.column_stack([proc[:, src_col[b]] for b in order]) if proc.size else proc

    bases_bytes = doc.sequence.encode("ascii", "replace")
    pos = np.asarray(doc.peak_positions[: max(1, len(doc.sequence))], dtype=np.int32)

    records: List[bytes] = []          # (name, num) markers computed below
    from struct import pack

    def rec(name: str, num: int, etype: int, esize: int, nelem: int, data: bytes) -> bytes:
        dsize = len(data)
        doff = 0  # patched later
        return pack(">4sIHHIIII", name.encode(), num, etype, esize, nelem,
                    dsize, doff, 0)

    dir_entries = []  # (name,num,etype,esize,nelem,dsize,doff)
    blobs: List[bytes] = []
    for i in range(1, 5):
        col = raw_abd[:, i - 1] if raw_abd.size else np.zeros(0)
        arr = np.nan_to_num(col).astype(">i2")
        blob = arr.tobytes()
        dir_entries.append(("DATA", i, 2, 2, len(arr), blob))
        blobs.append(blob)
    for i in range(9, 13):
        col = proc_abd[:, i - 9] if proc_abd.size else np.zeros(0)
        arr = np.nan_to_num(col).astype(">i2")
        blob = arr.tobytes()
        dir_entries.append(("DATA", i, 2, 2, len(arr), blob))
        blobs.append(blob)
    dir_entries.append(("PLOC", 2, 4, 4, len(pos), pos.astype(">i4").tobytes()))
    blobs.append(dir_entries[-1][5])
    dir_entries.append(("PBAS", 2, 1, 1, len(bases_bytes), bases_bytes))
    blobs.append(dir_entries[-1][5])

    # layout: header (30 bytes: 4 magic + version + nelem + ...), pad to 30,
    # then tdir at offset 26 read by the reader. Build: magic 4 + 2 version +
    # 4 nelem? reader reads nelem at raw[16:20] and tdir at raw[26:30].
    header = bytearray(30)
    header[0:4] = b"ABIF"
    header[4:8] = b"3.0\x00"
    header[16:20] = pack(">I", len(dir_entries))
    tdir = 30
    header[26:30] = pack(">I", tdir)
    datastart = tdir + len(dir_entries) * 28
    off = datastart
    dir_b = bytearray()
    for (name, num, etype, esize, nelem, blob), dsize in [
        (e, len(e[5])) for e in dir_entries
    ]:
        _ = dsize  # (blob length already equals len(blob))
        dir_b += pack(">4sIHHIIII", name.encode(), num, etype, esize, nelem,
                      len(blob), off, 0)
        off += len(blob)
    body = bytes(header) + bytes(dir_b) + b"".join(blobs)
    out.write_bytes(body)


def export_text(doc: TraceDocument, out: Path) -> None:
    """Text format: electrical current intensities, scan rate, instrument
    parameters, number of bases called, and starting/ending points."""
    lines = []
    lines.append(f"FILE            : {doc.path.name}")
    lines.append(f"PLATE           : {doc.path.parent.name}")
    lines.append(f"WELL            : {doc.well}")
    lines.append(f"SCAN RATE       : 1.75 Hz")
    lines.append(f"BASE ORDER      : {doc.base_order}")
    lines.append(f"SAMPLES         : {doc.acgt.shape[0] if doc.acgt.size else 0}")
    lines.append(f"NUMBER OF BASES : {len(doc.sequence)}")
    starts = [doc.peak_positions[0]] if doc.peak_positions else 0
    ends = [doc.peak_positions[-1]] if doc.peak_positions else 0
    lines.append(f"STARTING POINT  : {starts}")
    lines.append(f"ENDING POINT    : {ends}")
    if doc.qualities:
        qi = float(np.mean(doc.qualities[: max(1, len(doc.qualities))]))
        lines.append(f"QUALITY INDEX   : {qi:.2f}")
    lines.append("CALLED SEQUENCE :")
    lines.append(doc.sequence)
    lines.append("")
    lines.append("SCAN\tCHANNEL_A\tCHANNEL_C\tCHANNEL_G\tCHANNEL_T")
    if doc.acgt.size:
        cols = {b: i for i, b in enumerate("ACGT")}
        for s in range(0, doc.acgt.shape[0], 1):
            v = doc.acgt[s]
            lines.append(
                f"{s}\t{v[cols['A']]:.2f}\t{v[cols['C']]:.2f}\t{v[cols['G']]:.2f}\t{v[cols['T']]:.2f}")
    out.write_text("\n".join(lines) + "\n")