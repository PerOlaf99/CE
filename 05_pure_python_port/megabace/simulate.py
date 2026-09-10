"""Synthetic MegaBACE trace generator.

Generates realistic 4-dye capillary traces (Gaussian peaks, baseline drift,
noise, mobility shifts, dye bleed-through) and writes them out as genuine RSD
files using the real MegaBACE layout implemented in :mod:`megabace.rsd`.  This
lets the full round trip (writer -> parser -> basecaller) be validated end to
end without instrument data.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

DEFAULT_MATRIX = np.array(
    [
        [1.00, 0.18, 0.04, 0.02],
        [0.15, 1.00, 0.20, 0.05],
        [0.05, 0.22, 1.00, 0.18],
        [0.03, 0.06, 0.20, 1.00],
    ],
    dtype=np.float64,
)


def random_sequence(n: int, seed: int = 0) -> str:
    rng = np.random.default_rng(seed)
    return "".join(rng.choice(list("ACGT"), size=n))


def simulate_traces(
    sequence: str,
    matrix: np.ndarray | None = None,
    spacing_start: float = 18.0,
    spacing_end: float = 7.0,
    peak_amp: float = 8000.0,
    amp_var: float = 0.25,
    width_frac: float = 0.25,
    decay: float = 0.15,
    noise_sigma: float = 120.0,
    baseline: np.ndarray | None = None,
    mobility_shift: float = 2.5,
    seed: int = 0,
) -> tuple[np.ndarray, np.ndarray]:
    """Return (traces, peak_positions) where traces has shape (4, n_points)."""
    rng = np.random.default_rng(seed)
    if matrix is None:
        matrix = DEFAULT_MATRIX
    matrix = np.asarray(matrix, dtype=np.float64)

    n = len(sequence)
    spacing = np.linspace(spacing_start, spacing_end, n)
    pos = np.cumsum(spacing)
    pos = pos - pos[0]
    n_points = int(np.ceil(pos[-1]) + spacing_end * 4) + 1

    chan = {"A": 0, "C": 1, "G": 2, "T": 3}
    pure = np.zeros((4, n_points), dtype=np.float64)
    for i, base in enumerate(sequence.upper()):
        c = chan[base]
        sigma = max(1.0, width_frac * spacing[i])
        amp = peak_amp * rng.uniform(1 - amp_var, 1 + amp_var)
        amp *= 1.0 - decay * (i / n)
        x = np.arange(n_points, dtype=np.float64)
        pure[c] += amp * np.exp(-0.5 * ((x - pos[i]) / sigma) ** 2)

    if baseline is None:
        baseline = np.array([160.0, 150.0, 170.0, 140.0])
    baseline = np.asarray(baseline, dtype=np.float64).reshape(4, 1)
    drift = 80.0 * np.sin(np.linspace(0, 2 * np.pi, n_points))[None, :]
    pure = pure + baseline + drift

    mixed = matrix @ pure
    noise = rng.normal(0.0, noise_sigma, size=mixed.shape)
    mixed = mixed + noise

    lags = np.linspace(0.0, mobility_shift, 4) - mobility_shift / 2.0
    for c in range(4):
        if abs(lags[c]) > 1e-6:
            t = np.arange(n_points, dtype=np.float64)
            src = np.clip(t - lags[c], 0, n_points - 1)
            mixed[c] = np.interp(t, src, mixed[c])

    low = float(np.percentile(mixed, 0.05))
    mixed = np.clip(mixed - low, 0.0, None)
    peak_positions = pos
    return mixed, peak_positions


def _str_tok(s: str) -> bytes:
    """Encode a ``05 <len> <string>`` metadata token (length includes NUL)."""
    b = s.encode("latin-1")
    return b"\x05" + bytes([len(b) + 1]) + b + b"\x00"


def _group_tok(items) -> bytes:
    """Encode a ``01 <count>`` metadata group of pre-encoded tokens."""
    inner = b"".join(items)
    return b"\x01" + bytes([len(items)]) + inner


_ET_DYES = {"A": "ET-TAMRA", "C": "ET-ROX", "G": "ET-R110", "T": "ET-R6G"}
_ET_FILTERS = ["555DF20", "520DF20", "610LP", "585DF20"]


def write_rsd(
    path,
    traces: np.ndarray,
    sequence: str = "",
    lane: int = 1,
    version: int = 47,
    channel_order: str = "ACGT",
    sample_name: str = "sample",
    well_id: str = "A01",
) -> None:
    """Write a single-lane RSD file in the real MegaBACE layout.

    ``traces`` must be shaped (4, n_points) with rows ordered as
    ``channel_order``.  The file stores one reference column plus the four dye
    channels as uint32 frames followed by the ``BAR CODE`` metadata tree.
    """
    traces = np.asarray(traces, dtype=np.float64)
    n_dyes, n_points = traces.shape
    if n_dyes != 4:
        raise ValueError("write_rsd expects 4 dye channels")
    order = "".join(c for c in channel_order.upper() if c in "ACGT")
    if len(order) != 4:
        raise ValueError("channel_order must contain four base letters")

    frames = np.zeros((n_points, 5), dtype=np.uint32)
    frames[:, 0] = 66
    vals = np.clip(np.round(traces.T), 0, 4294967295).astype(np.uint32)
    frames[:, 1:] = vals

    chem_items = [
        _str_tok("APPLICATION"),
        _str_tok("Sequencing"),
        _str_tok("BEAMSPLITTER A"),
        _str_tok("540DRLP"),
        _str_tok("BEAMSPLITTER B"),
        _str_tok("595DRLP"),
    ]
    for i, base in enumerate(order):
        chem_items.append(_str_tok(f"CHANNEL{i + 1}"))
        chem_items.append(
            _group_tok(
                [
                    _str_tok("BASE"),
                    _str_tok(base),
                    _str_tok("DYE"),
                    _str_tok(_ET_DYES[base]),
                    _str_tok("FILTER"),
                    _str_tok(_ET_FILTERS[i]),
                ]
            )
        )
    chem_items += [
        _str_tok("LASER MODE"),
        _str_tok("Blue"),
        _str_tok("NAME"),
        _str_tok("ET Terminators"),
    ]

    metadata = b"".join(
        [
            _str_tok("BAR CODE"),
            _str_tok(f"synthetic_{sample_name}"),
            _str_tok("BASE CALLER"),
            _str_tok("Cimarron 2.19.12 Slim Phredify"),
            _str_tok("CHEMISTRY"),
            _group_tok(chem_items),
            _str_tok("COMMENT"),
            _str_tok("Synthetic round-trip fixture"),
            _str_tok("MACHINE ID"),
            _str_tok("SIM1"),
            _str_tok("PLATE ID"),
            _str_tok("Synthetic"),
            _str_tok("SAMPLE NAME"),
            _str_tok(sample_name),
            _str_tok("WELL ID"),
            _str_tok(well_id),
        ]
    )

    out = frames.tobytes() + metadata
    Path(path).write_bytes(out)
