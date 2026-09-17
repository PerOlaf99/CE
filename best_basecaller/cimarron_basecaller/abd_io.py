"""
Reader for MegaBACE .abd ABIF files.

The .abd exports from the MegaBACE software are ABIF (ABI Binary Format)
containers holding the obtained results for one well. The directory
layout of these particular files is non-standard: the record directory
starts at the offset stored in the ABIF header's tdir record (read here
from raw[26:30], not the spec's raw[24:28]), and many auxiliary records
(AEPt, ASPt, LANE, SMPL, ...) have corrupt/unpopulated data offsets --
only the trace and basecall records carry valid, in-file offsets.

Layout of the relevant records (decoded empirically; see dev notes):

  DATA1..DATA4 : 2-byte big-endian int16 trace, one channel per record,
                 9646 samples. Channel order is [C, A, G, T] on this
                 plate (dye/base-order calibration), i.e. DEDET/FWO order,
                 NOT genomic A,C,G,T. Verified against RSD + SCF by
                 cross-correlation (corr > 0.9999).
  DATA9..DATA12: 2-byte big-endian int16 PROCESSED trace, one channel per
                 record (~7198-7658 samples), cropped to the called signal
                 region (starts at the first real base, DLL peak #0 lands
                 near sample ~75-103, not scan ~2000 as on the full RSD
                 axis). Same [C,A,G,T] channel order. This is the axis the
                 DLL's own PLOC/PBAS coordinates are expressed in.
  PLOC2        : 2-byte big-endian int16 array, base N peak positions in
                 the DATA9-12 axis (i.e. ESD's peak_positions minus the
                 per-run crop offset, ~1992-2184).
  PBAS2        : ASCII called base string (same as ESD sequence).

This module provides read_abd() -> ABDFile and to_acgt_trace(), mirroring
the interfaces of rsd_io.py / scf_io.py so the same downstream callers
work on any container.
"""

from __future__ import annotations
from dataclasses import dataclass
import struct

import numpy as np

# Empirical channel order of DATA1-4 / DATA9-12 (dye/base-order calibration).
# ABD columns [0,1,2,3] map to bases [C,A,G,T] on this plate, i.e. the
# order string is "CAGT" (column0=C, column1=A, column2=G, column3=T).
ABD_BASE_ORDER = "CAGT"


@dataclass
class ABDFile:
    trace_raw: np.ndarray       # (n, 4) processed-DLL-axis trace? see fields below
    trace: np.ndarray           # (n_samples, 4) in ABD column order
    trace_processed: np.ndarray  # (n_processed, 4) DATA9-12 (called axis)
    bases: str                  # PBAS2 (DLL called base string)
    peak_positions: np.ndarray  # PLOC2 (DLL peak indices, DATA9-12 axis)
    entries: dict


def _read_dir(raw: bytes) -> dict:
    """Parse the ABIF record directory -> {name+num: (etype, esize, nelem, dsize, doff)}.

    Only records whose data actually falls inside the file are kept.
    """
    doff = struct.unpack(">I", raw[26:30])[0]
    nelem = struct.unpack(">I", raw[16:20])[0]
    entries = {}
    for i in range(min(nelem, 400)):
        off = doff + i * 28
        if off + 28 > len(raw):
            break
        name = raw[off:off + 4].decode("ascii", "replace")
        num, etype, esize, ne, dsize, d_off, _ = struct.unpack(
            ">IHHIIII", raw[off + 4:off + 28]
        )
        if not name.isidentifier():
            break
        if 0 <= d_off and d_off + dsize <= len(raw) and dsize > 0:
            entries[f"{name}{num}"] = (etype, esize, ne, dsize, d_off)
    return entries


def read_abd(path: str) -> ABDFile:
    """Parse a .abd ABIF file into its trace + DLL basecall records."""
    with open(path, "rb") as f:
        raw = f.read()

    if raw[:4] != b"ABIF":
        raise ValueError(f"{path}: not an ABIF file (magic {raw[:4]!r})")

    entries = _read_dir(raw)

    def payload(key: str) -> np.ndarray:
        etype, esize, ne, dsize, doff = entries[key]
        return np.frombuffer(
            raw[doff:doff + dsize],
            dtype={2: ">i1", 4: ">i2", 5: ">i4", 7: ">f4", 8: ">f8"}.get(etype, ">i2"),
        ).astype(np.float64)

    trace = np.column_stack(
        [payload(f"DATA{i}") for i in range(1, 5)]
    )
    trace_proc = np.column_stack(
        [payload(f"DATA{i}") for i in range(9, 13)]
    )
    bases = bytes(raw[entries["PBAS2"][4]: entries["PBAS2"][4] + entries["PBAS2"][3]]).decode(
        "ascii", "replace"
    )
    peak_positions = payload("PLOC2").astype(np.int64)

    return ABDFile(
        trace_raw=trace,
        trace=trace,
        trace_processed=trace_proc,
        bases=bases,
        peak_positions=peak_positions,
        entries=entries,
    )


def to_acgt_trace(trace: np.ndarray, base_order: str = ABD_BASE_ORDER) -> np.ndarray:
    """Reorder a trace's columns (ABD column order) into standard A,C,G,T.

    ABD columns follow the run's dye/base-order calibration; on this plate
    the order string is "CAGT" (see module docstring), so column0=C, col1=A,
    col2=G, col3=T.
    """
    if sorted(base_order.upper()) != ["A", "C", "G", "T"]:
        raise ValueError(f"Unexpected base_order {base_order!r}")
    base_to_col = {b: i for i, b in enumerate(base_order.upper())}
    out = np.empty_like(trace)
    for target, base in enumerate("ACGT"):
        out[:, target] = trace[:, base_to_col[base]]
    return out