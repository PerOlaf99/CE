"""Reader for GE Healthcare MegaBACE RSD (raw signal data) files.

Real MegaBACE ``.rsd`` files observed in the wild do not follow the
length-prefixed ASCII-record layout described in community notes.  Instead a
single-lane file is laid out as:

    offset 0 .. meta_start-1
        raw signal data: one frame of ``n_columns`` little-endian uint32
        values per sampling point.  The first column is a slowly varying
        reference signal; columns 1..4 are the four dye detector channels.
    offset meta_start .. end
        header/metadata: a length-prefixed string tree (``05``/``01`` tagged)
        describing the run, chemistry, channel-to-base assignment and sample,
        followed by filter/gain tables and an ``ESD1`` descriptor block.

``meta_start`` is located by scanning for the fixed ``BAR CODE`` key that
begins the metadata.  The number of data points is ``meta_start // 20``.

The channel-to-base assignment is read from the ``CHANNEL<n>`` entries in the
chemistry tree; typical ET-terminator files use the order ``TGCA``.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import numpy as np

META_MARKER = b"\x05\x09BAR CODE\x00"
FRAME_UINT32 = 5
DYE_COLUMNS = slice(1, 5)

_DYE_NAMES = {
    "ET-R6G",
    "ET-R110",
    "ET-ROX",
    "ET-TAMRA",
    "ET-FAM",
    "ET-HEX",
    "dR6G",
    "dR110",
    "dROX",
    "dTAMRA",
}


class RSDError(Exception):
    """Raised when an RSD file cannot be parsed."""


@dataclass
class RSDMeta:
    bar_code: str = ""
    sample_name: str = ""
    well_id: str = ""
    plate_id: str = ""
    base_caller: str = ""
    chemistry: str = ""
    machine_id: str = ""
    n_points: int = 0
    channel_bases: list = None  # base letter per detector channel
    channel_dyes: list = None  # dye name per detector channel
    raw: bytes = b""

    def __post_init__(self) -> None:
        if self.channel_bases is None:
            self.channel_bases = []
        if self.channel_dyes is None:
            self.channel_dyes = []

    @property
    def channel_order(self) -> str:
        order = "".join(
            b for b in self.channel_bases if b in "ACGT"
        )
        return order if len(order) == 4 else "TGCA"


def _parse_string_tokens(buf: bytes):
    """Yield the string values of a ``05``/``01`` tagged token stream.

    Returns a nested structure: every element is either a ``str`` (for a
    ``05 <len> <string>`` token, with the trailing NUL stripped) or a
    ``list`` (for a ``01 <count>`` group containing exactly ``count``
    elements).
    """
    pos = 0
    n = len(buf)
    stack: list[tuple[int, list]] = []
    roots: list = []

    def close_lists():
        while stack and len(stack[-1][1]) == stack[-1][0]:
            _cnt, items = stack.pop()
            if stack:
                stack[-1][1].append(items)
            else:
                roots.append(items)

    while pos < n:
        tag = buf[pos]
        if tag == 0x05 and pos + 2 <= n:
            ln = buf[pos + 1]
            end = pos + 2 + ln
            if end > n:
                break
            s = buf[pos + 2:end].decode("latin-1", "replace").rstrip("\x00")
            if stack:
                stack[-1][1].append(s)
                close_lists()
            else:
                roots.append(s)
            pos = end
        elif tag == 0x01 and pos + 2 <= n:
            cnt = buf[pos + 1]
            stack.append((cnt, []))
            pos += 2
        else:
            pos += 1
    return roots


def _find_key(items, key: str):
    """Return the value following ``key`` in a flat key/value list, else None."""
    for i, item in enumerate(items):
        if item == key and i + 1 < len(items):
            return items[i + 1]
    return None


class RsdFile:
    """Parsed representation of a MegaBACE RSD file."""

    def __init__(self, path):
        self.path = Path(path)
        self.data = self.path.read_bytes()
        self.meta_start = _locate_metadata(self.data)
        n = len(self.data)
        self.n_points = self.meta_start // (FRAME_UINT32 * 4)
        if self.meta_start % (FRAME_UINT32 * 4) != 0:
            self.n_points = (self.meta_start // (FRAME_UINT32 * 4))
        if self.n_points <= 0:
            raise RSDError(
                f"could not determine data length in {self.path} "
                f"(meta_start={self.meta_start}, file size {n})"
            )
        self.metadata = RSDMeta(
            n_points=self.n_points,
            raw=self.data[self.meta_start:],
        )
        self._parse_metadata()

    def _parse_metadata(self) -> None:
        tokens = _parse_string_tokens(self.metadata.raw)
        meta = self.metadata
        meta.bar_code = _find_key(tokens, "BAR CODE") or ""
        meta.base_caller = _find_key(tokens, "BASE CALLER") or ""
        meta.sample_name = _find_key(tokens, "SAMPLE NAME") or ""
        meta.well_id = _find_key(tokens, "WELL ID") or ""
        meta.plate_id = _find_key(tokens, "PLATE ID") or ""
        meta.machine_id = _find_key(tokens, "MACHINE ID") or ""

        chem = _find_key(tokens, "CHEMISTRY")
        if isinstance(chem, list):
            meta.chemistry = (
                _find_key(chem, "NAME") if not isinstance(_find_key(chem, "NAME"), list) else ""
            ) or ""
            for ch_name in ("CHANNEL1", "CHANNEL2", "CHANNEL3", "CHANNEL4"):
                ch = _find_key(chem, ch_name)
                if not isinstance(ch, list):
                    continue
                base = _find_key(ch, "BASE")
                dye = _find_key(ch, "DYE")
                meta.channel_bases.append(str(base) if base is not None else "")
                meta.channel_dyes.append(str(dye) if dye is not None else "")

    def extract_traces(self, channel_order: str | None = None) -> np.ndarray:
        """Return the four dye channels as a float64 (4, n_points) array.

        Rows are in detector order 1..4.  If ``channel_order`` is supplied the
        rows are reordered to match it (row i corresponds to
        ``channel_order[i]``); otherwise detector order is kept.
        """
        if self.n_points * FRAME_UINT32 * 4 > self.meta_start:
            raise RSDError("declared data length exceeds file contents")
        u = np.frombuffer(self.data[:self.meta_start], dtype=np.uint32)
        frames = u[: self.n_points * FRAME_UINT32].reshape(-1, FRAME_UINT32)
        traces = frames[:, DYE_COLUMNS].astype(np.float64).T.copy()
        if channel_order and len(channel_order) == 4:
            order = self.metadata.channel_order
            if len(order) == 4:
                perm = [order.index(c) for c in channel_order]
                traces = traces[perm]
        return traces

    def summary(self) -> str:
        m = self.metadata
        lines = [
            f"file: {self.path}",
            f"size: {len(self.data)} bytes",
            f"data points: {self.n_points}",
            f"bar code: {m.bar_code or '-'}",
            f"sample name: {m.sample_name or '-'}",
            f"well id: {m.well_id or '-'}",
            f"plate id: {m.plate_id or '-'}",
            f"base caller: {m.base_caller or '-'}",
            f"machine id: {m.machine_id or '-'}",
            f"chemistry: {m.chemistry or '-'}",
        ]
        if m.channel_bases:
            chans = ", ".join(
                f"CH{i + 1}={b}({d or '?'})"
                for i, (b, d) in enumerate(zip(m.channel_bases, m.channel_dyes))
            )
            lines.append(f"channels: {chans}")
            lines.append(f"channel order: {m.channel_order}")
        return "\n".join(lines)


def _locate_metadata(data: bytes) -> int:
    idx = data.find(META_MARKER)
    if idx < 0:
        # Tolerate files whose metadata begins at a fixed small header.
        raise RSDError("not a MegaBACE RSD file (BAR CODE metadata not found)")
    return idx


def extract_traces(rsd: RsdFile, lane: Optional[int] = None) -> np.ndarray:
    """Return the raw dye signal as a float64 array shaped (4, n_points).

    Rows are in detector channel order 1..4 (see ``RsdFile.metadata`` for the
    channel-to-base assignment).  ``lane`` is accepted for API compatibility;
    these files hold a single lane.
    """
    return rsd.extract_traces()
