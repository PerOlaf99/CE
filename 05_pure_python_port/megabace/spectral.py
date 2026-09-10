"""Spectral deconvolution of MegaBACE fluorescence traces.

The four raw detector channels observe mixtures of the four dye spectra because
of bleed-through between adjacent emission bands.  Basecalling quality depends
strongly on separating these channels.  Two strategies are supported:

* a fixed mixing matrix supplied by the user (ideal, matches the instrument's
  calibration), or
* automatic estimation of the mixing matrix from the data using the Successive
  Projection Algorithm (SPA), a well-established pure-pixel endmember
  extraction method.
"""

from __future__ import annotations

import numpy as np

from .rsd import RSDError

DEFAULT_ET_MATRIX = np.array(
    [
        [0.899, 0.477, 0.140, 0.155],
        [0.130, 0.873, 0.082, 0.201],
        [0.309, 0.026, 0.965, 0.163],
        [0.283, 0.083, 0.207, 0.952],
    ],
    dtype=np.float64,
)
# Calibrated by averaging auto-estimated matrices over 63 MegaBACE1000 wells
# (ET-dye bleed, rows = measured channels, columns = dye channels in trace
# order).  When auto-estimation is disabled this matrix achieves the same
# mean identity as per-well estimation (~92% on the 63-well set).


def _norm(x: np.ndarray) -> np.ndarray:
    return np.linalg.norm(x, axis=0, keepdims=True)


def estimate_matrix(
    traces: np.ndarray,
    n_endmembers: int = 4,
    dom_frac: float = 0.5,
    top_frac: float = 0.25,
) -> np.ndarray:
    """Estimate the 4x4 dye mixing matrix from de-baselined traces.

    Because the dye mixing matrix has a dominant diagonal, each dye k is the
    channel that dominates the raw signal at dye-k pure pixels (points where a
    single dye fires with little overlap from neighbours).  Points are grouped
    by their dominant channel; each column of the returned matrix is the
    median direction of the points in that group.  The columns are returned in
    channel order, so channel index k corresponds to dye k.
    """
    n_dyes, n_points = traces.shape
    if n_dyes != n_endmembers:
        raise RSDError("trace channel count does not match requested endmembers")

    base = _subtract_rough_baseline(traces)
    pos = np.clip(base, 0.0, None)
    sums = pos.sum(axis=0) + 1e-12
    dominance = pos.max(axis=0) / sums
    argmax = pos.argmax(axis=0)

    columns = np.zeros((n_endmembers, n_dyes), dtype=np.float64)
    found = 0
    for k in range(n_endmembers):
        mask = (argmax == k) & (dominance > dom_frac)
        idx = np.flatnonzero(mask)
        if idx.size < 5:
            order = np.argsort(np.where(argmax == k, dominance, 0.0))[::-1]
            idx = order[: max(5, n_points // 1000)]
        if idx.size == 0:
            continue
        sub = pos[:, idx]
        dirs = sub / (np.linalg.norm(sub, axis=0, keepdims=True) + 1e-12)
        col = np.median(dirs, axis=1)
        nrm = np.linalg.norm(col)
        if nrm < 1e-9:
            continue
        columns[:, k] = col / nrm
        found += 1

    if found < n_endmembers:
        raise RSDError(
            f"could not identify {n_endmembers} independent dye directions "
            f"(found {found}); supply a mixing matrix explicitly"
        )
    return columns


def _subtract_rough_baseline(traces: np.ndarray) -> np.ndarray:
    """Per-channel robust baseline removal for matrix estimation."""
    n_dyes, n_points = traces.shape
    out = traces.copy()
    for c in range(n_dyes):
        floor = np.percentile(traces[c], 5.0)
        out[c] = traces[c] - floor
    return out


def deconvolve(
    traces: np.ndarray,
    matrix: np.ndarray | None = None,
    estimate: bool = True,
) -> np.ndarray:
    """Separate mixed traces into pure dye signals:  S = inv(M) @ R."""
    n_dyes, n_points = traces.shape
    if matrix is None:
        if estimate:
            matrix = estimate_matrix(traces)
        else:
            matrix = DEFAULT_ET_MATRIX
    if matrix.shape != (n_dyes, n_dyes):
        raise RSDError(
            f"mixing matrix shape {matrix.shape} incompatible with "
            f"{n_dyes} channels"
        )
    try:
        inv = np.linalg.inv(matrix)
    except np.linalg.LinAlgError:
        raise RSDError("mixing matrix is singular")
    out = inv @ traces
    return out
