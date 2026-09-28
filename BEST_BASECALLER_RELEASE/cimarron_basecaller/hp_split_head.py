"""
Phase A: supervised mid-zone A/C peak-split head.

Looks for a second same-dye peak near an existing A/C call (partner search),
labels using ESD peaks in the neighborhood, trains logistic regression,
inserts high-confidence partners after track_bases.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

ORDER = "ACGT"
CH_A, CH_C = 0, 1


@dataclass
class SplitCandidate:
    position: int
    channel: int
    height: float
    features: np.ndarray
    anchor_pos: int


def _valley_depth(y: np.ndarray, a: int, b: int) -> float:
    if b <= a + 1:
        return 0.0
    lo = min(float(y[a]), float(y[b]))
    if lo <= 1e-12:
        return 0.0
    return float((lo - float(y[a : b + 1].min())) / lo)


def extract_candidates(
    norm_trace: np.ndarray,
    bands: list,
    spacing: float,
    zone: tuple[float, float] = (0.25, 0.60),
    channels: tuple[int, ...] = (CH_A, CH_C),
) -> list[SplitCandidate]:
    """Partner candidates: secondary max near each mid-zone A/C peak."""
    if not bands or spacing <= 0:
        return []
    n = norm_trace.shape[0]
    pos = np.array([b.position for b in bands], dtype=int)
    chs = np.array([b.channel for b in bands], dtype=int)
    hts = np.array([b.height for b in bands], dtype=float)
    nscan = max(int(pos[-1]), 1)
    occupied = set(zip(pos.tolist(), chs.tolist()))
    cands: list[SplitCandidate] = []

    for i, b in enumerate(bands):
        ch = int(chs[i])
        if ch not in channels:
            continue
        p = int(pos[i])
        frac = p / nscan
        if not (zone[0] <= frac < zone[1]):
            continue
        h0 = float(hts[i])
        y = norm_trace[:, ch].astype(float)
        half = int(0.85 * spacing)
        lo, hi = max(0, p - half), min(n - 1, p + half)
        if hi <= lo + 3:
            continue
        seg = y[lo : hi + 1].copy()
        # suppress primary neighborhood
        c = p - lo
        w = max(1, int(0.18 * spacing))
        seg[max(0, c - w) : min(len(seg), c + w + 1)] = -1.0
        j_rel = int(np.argmax(seg))
        if seg[j_rel] < 0:
            continue
        j = lo + j_rel
        h = float(y[j])
        sep = abs(j - p)
        if sep < 0.35 * spacing or sep > 0.90 * spacing:
            continue
        if h < 0.18 * h0:
            continue
        if (j, ch) in occupied:
            continue
        # also skip if another band already within 3 scans same channel
        if any(abs(j - pos[k]) < 3 and chs[k] == ch for k in range(len(bands))):
            continue
        a, b2 = (p, j) if p < j else (j, p)
        v = _valley_depth(y, a, b2)
        feat = np.array(
            [
                sep / spacing,
                h / max(h0, 1e-9),
                v,
                float(ch == CH_A),
                float(ch == CH_C),
                frac,
                h0,
                float(j > p),  # partner after anchor
            ],
            dtype=float,
        )
        cands.append(
            SplitCandidate(position=j, channel=ch, height=h, features=feat, anchor_pos=p)
        )
    return cands


def label_candidates_from_esd(
    cands: list[SplitCandidate],
    esd_seq: str,
    esd_peaks: np.ndarray,
    base_order: str = ORDER,
    match_radius: int = 4,
) -> np.ndarray:
    """Positive if an ESD peak of the same base lies near the candidate."""
    labels = np.zeros(len(cands), dtype=int)
    if not cands or len(esd_peaks) == 0:
        return labels
    esd_peaks = np.asarray(esd_peaks, dtype=int).ravel()
    esd_bases = np.array([c for c in esd_seq if c in "ACGT"])
    n = min(len(esd_peaks), len(esd_bases))
    esd_peaks, esd_bases = esd_peaks[:n], esd_bases[:n]
    for i, c in enumerate(cands):
        letter = base_order[c.channel]
        m = (np.abs(esd_peaks - c.position) <= match_radius) & (esd_bases == letter)
        labels[i] = 1 if np.any(m) else 0
    return labels


def train_logistic(X: np.ndarray, y: np.ndarray) -> np.ndarray:
    d = int(X.shape[1]) if X.ndim == 2 else 0
    if d == 0 or len(y) == 0 or int(y.sum()) == 0 or int(y.sum()) == len(y):
        return np.concatenate([np.zeros(max(d, 1)), np.zeros(max(d, 1)), np.ones(max(d, 1)), [-10.0]])
    mu = X.mean(axis=0)
    sd = X.std(axis=0) + 1e-8
    Xn = (X - mu) / sd
    w = np.zeros(d)
    b = 0.0
    lr = 0.12
    pos = max(int(y.sum()), 1)
    neg = max(len(y) - pos, 1)
    sw = np.where(y > 0, float(neg) / pos, 1.0)
    sw = sw / sw.mean()
    for _ in range(600):
        z = Xn @ w + b
        p = 1.0 / (1.0 + np.exp(-np.clip(z, -30, 30)))
        err = (p - y.astype(float)) * sw
        w -= lr * (Xn.T @ err / len(y) + 0.02 * w)
        b -= lr * float(err.mean())
    return np.concatenate([w, mu, sd, [b]])


def predict_proba(feat: np.ndarray, model: np.ndarray) -> float:
    d = (len(model) - 1) // 3
    w, mu, sd, b = model[:d], model[d : 2 * d], model[2 * d : 3 * d], float(model[-1])
    x = (np.asarray(feat, float) - mu) / (sd + 1e-8)
    z = float(np.dot(x, w) + b)
    return float(1.0 / (1.0 + np.exp(-np.clip(z, -30, 30))))


def apply_splits(
    bands: list,
    norm_trace: np.ndarray,
    model: np.ndarray,
    spacing: float,
    threshold: float = 0.55,
    zone: tuple[float, float] = (0.25, 0.60),
    max_inserts: int = 30,
) -> list:
    from cimarron_basecaller.spacing_caller import TrackedBase

    cands = extract_candidates(norm_trace, bands, spacing, zone=zone)
    if not cands:
        return bands
    scored = [(predict_proba(c.features, model), c) for c in cands]
    scored = [(pr, c) for pr, c in scored if pr >= threshold]
    scored.sort(key=lambda t: -t[0])
    existing = {(int(b.position), int(b.channel)) for b in bands}
    new_bands = list(bands)
    inserted = 0
    for pr, c in scored:
        if inserted >= max_inserts:
            break
        if any(abs(c.position - p) < 3 and ch == c.channel for p, ch in existing):
            continue
        new_bands.append(
            TrackedBase(
                position=int(c.position),
                channel=int(c.channel),
                height=float(c.height),
                expected_position=float(c.position),
                spacing_used=float(spacing),
            )
        )
        existing.add((c.position, c.channel))
        inserted += 1
    new_bands.sort(key=lambda b: b.position)
    return new_bands


def bands_to_sequence(bands: list, base_order: str = ORDER) -> str:
    return "".join(base_order[b.channel] for b in bands)


def save_model(path: Path, model: np.ndarray, meta: dict[str, Any] | None = None) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    np.savez(path, model=model, **{k: np.asarray(v) for k, v in (meta or {}).items()})


def load_model(path: Path) -> np.ndarray:
    return np.load(path)["model"]
