#!/usr/bin/env python3
"""Compare our de-novo peak caller (cimarron_basecaller.track_bases) run on
the trace stored in each container -- RSD, ABD (raw DATA1-4), ABD
(processed DATA9-12), SCF -- against the Cimarron DLL's own ground truth.

Ground truth comes from the .esd file produced by the DLL (sequence +
absolute peak_positions). ESD itself stores NO trace (verified: no channel
data, no correlation with RSD); the underlying trace lives in RSD/SCF/ABD.

Coordinate systems:
  - ESD peak_positions   : absolute RSD scan indices (e.g. first base ~2082)
  - RSD / ABD DATA1-4    : full-length raw axis == RSD axis (offset 0)
  - ABD DATA9-12 / SCF   : cropped PROCESSED axis; DLL's PLOC2/peak_indices
                           are expressed in this axis (e.g. first base ~75)
                           -> absolute = local + (ESD.pp[0] - PLOC2[0]).

Metrics per container:
  recall:  %% of ESD peaks that have a called peak within +/-3 scans
  prec:    %% of called peaks that hit an ESD peak within +/-3 scans
  id:      %% global-alignment identity of the called sequence vs ESD seq
  dv_recall: on containers that carry their OWN DLL peak list (SCF, ABD
                           processed), %% of the DLL's peaks hit by our call
                           -- the cleanest "same as the ESD" check.

Usage:
  python3 compare_traces.py            # all 96 wells
  python3 compare_traces.py A          # A01..A12
  python3 compare_traces.py A01 B09    # specific wells (>=2 args when mixed)
"""
import os
import sys
from multiprocessing import Pool

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(HERE, "MB1000_M13_DT", "Analyzed Data",
                        "MB1000_M13_DT_Cp312_MD1")
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "best_basecaller"))

from cimarron_basecaller import track_bases
from cimarron_basecaller.rsd_io import read_rsd, to_acgt_trace as rsd_acgt
from cimarron_basecaller.scf_io import read_scf
from cimarron_basecaller.abd_io import read_abd, to_acgt_trace as abd_acgt
from extract_training_data import parse_esd
from Bio import Align

WIN_CONFIG = dict(
    use_gaussian_reconstruction=True,
    gaussian_recon_segment_size=384,
    use_combined_channel_score=True,
    window_frac=(0.75, 1.25),
    local_norm_window=1800,
    channel_peak_bonus=1.6,
    pullback_weight=0.019,
    ema_alpha=0.10,
)

_ALIGNER = Align.PairwiseAligner()
_ALIGNER.mode = "global"
_ALIGNER.match_score = 1
_ALIGNER.mismatch_score = -2
_ALIGNER.open_gap_score = -3
_ALIGNER.extend_gap_score = -1


def run_caller(trace_acgt, auto_trim=False):
    cfg = dict(WIN_CONFIG)
    cfg["auto_trim"] = auto_trim
    seq, quals, bands = track_bases(trace_acgt, base_order="ACGT", **cfg)
    return seq, np.array([b.position for b in bands])


def compare_peaks(called, gt, tol=3):
    called_pos = np.sort(np.asarray(called, dtype=np.int64))
    gt_pos = np.sort(np.asarray(gt, dtype=np.int64))
    if len(gt_pos) == 0:
        return 0.0, 0.0
    j = 0
    hit = 0
    for g in gt_pos:
        while j < len(called_pos) and called_pos[j] < g - tol:
            j += 1
        k = j
        while k < len(called_pos) and called_pos[k] <= g + tol:
            if abs(called_pos[k] - g) <= tol:
                hit += 1
                break
            k += 1
    recall = hit / len(gt_pos)
    chit = 0
    j = 0
    for c in called_pos:
        while j < len(gt_pos) and gt_pos[j] < c - tol:
            j += 1
        if j < len(gt_pos) and abs(gt_pos[j] - c) <= tol:
            chit += 1
    precision = chit / len(called_pos) if len(called_pos) else 0.0
    return recall, precision


def seq_identity(call, ref):
    a, b = _ALIGNER.align(call, ref)[0]
    non_gap = sum(1 for x, y in zip(a, b) if x != "-" and y != "-")
    ident = sum(1 for x, y in zip(a, b) if x == y and x != "-")
    return (100.0 * ident / non_gap) if non_gap else 0.0


def process_well(well):
    res = {"well": well}
    esd = parse_esd(os.path.join(DATA_DIR, f"{well}.esd"))
    esd_pp = esd["peak_positions"].astype(int)
    res["n_esd"] = len(esd_pp)

    # RSD (full raw axis; the "ESD trace")
    rsd = read_rsd(os.path.join(DATA_DIR, f"{well}.rsd"))
    tr_rsd, _ = rsd_acgt(rsd, base_order="TGCA")

    # ABD: raw DATA1-4 + processed DATA9-12 (+ DLL's own PLOC2/PBAS2)
    abd = read_abd(os.path.join(DATA_DIR, "ABD", f"{well}.abd"))
    tr_abdraw = abd_acgt(abd.trace_raw)
    tr_abdproc = abd_acgt(abd.trace_processed)
    ploc = abd.peak_positions
    off_abd = int(esd_pp[0] - ploc[0])

    # SCF (= processed trace, ACGT columns already)
    scf = read_scf(os.path.join(DATA_DIR, "SCF", f"{well}.scf"))
    tr_scf = scf.trace
    off_scf = int(esd_pp[0] - scf.peak_indices[0])

    res["off_abd"] = off_abd
    res["off_scf"] = off_scf

    for name, tr, off, dll_local in (
        ("RSD", tr_rsd, 0, None),
        ("ABD-raw", tr_abdraw, 0, None),
        ("ABD-proc", tr_abdproc, off_abd, ploc),
        ("SCF", tr_scf, off_scf, scf.peak_indices.astype(int)),
    ):
        seq, pos = run_caller(tr)
        abs_pos = pos + off
        recall, prec = compare_peaks(abs_pos, esd_pp)
        ident = seq_identity(seq, esd["sequence"])
        res[f"{name}_n"] = len(pos)
        res[f"{name}_recall"] = round(100 * recall, 1)
        res[f"{name}_prec"] = round(100 * prec, 1)
        res[f"{name}_id"] = round(ident, 1)
        if dll_local is not None:
            drec, _ = compare_peaks(pos, np.asarray(dll_local))
            res[f"{name}_dv_recall"] = round(100 * drec, 1)
    return res


def main():
    args = sys.argv[1:]
    if not args:
        wells = sorted(f[:-4] for f in os.listdir(DATA_DIR) if f.endswith(".esd"))
    elif all(len(a) <= 2 for a in args):
        pref = []
        for a in args:
            if len(a) == 1:
                pref += [f"{a}{c:02d}" for c in range(1, 13)]
            elif len(a) == 2:
                rows = "ABCDEFGH"
                col = int(a[1:])
                pref += [f"{rows[j]}{col:02d}" for j in range(8)]
            else:
                pref.append(a)
        wells = sorted(f[:-4] for f in os.listdir(DATA_DIR)
                       if f.endswith(".esd") and f[:-4] in pref)
    else:
        wells = args

    if not wells:
        print("no wells matched", file=sys.stderr)
        sys.exit(1)

    header = ("well,n_esd,off_abd,off_scf,"
              "RSD_n,RSD_recall,RSD_prec,RSD_id,"
              "ABD-raw_n,ABD-raw_recall,ABD-raw_prec,ABD-raw_id,"
              "ABD-proc_n,ABD-proc_recall,ABD-proc_prec,ABD-proc_id,ABD-proc_dv_recall,"
              "SCF_n,SCF_recall,SCF_prec,SCF_id,SCF_dv_recall")
    print(header)
    with Pool(8) as pool:
        for r in pool.imap_unordered(process_well, wells):
            row = [str(r[k]) for k in ("well", "n_esd", "off_abd", "off_scf")]
            for p in ("n", "recall", "prec", "id"):
                row.append(str(r.get(f"RSD_{p}", "")))
            for src in ("ABD-raw",):
                row += [str(r.get(f"{src}_n", "")), str(r.get(f"{src}_recall", "")),
                        str(r.get(f"{src}_prec", "")), str(r.get(f"{src}_id", ""))]
            for src in ("ABD-proc", "SCF"):
                row += [str(r.get(f"{src}_n", "")), str(r.get(f"{src}_recall", "")),
                        str(r.get(f"{src}_prec", "")), str(r.get(f"{src}_id", "")),
                        str(r.get(f"{src}_dv_recall", ""))]
            print(",".join(row), flush=True)


if __name__ == "__main__":
    main()