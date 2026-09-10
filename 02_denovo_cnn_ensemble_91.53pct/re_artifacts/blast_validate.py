#!/usr/bin/env python3
"""BLAST-validate the ported DLL peak detector the way real sequencing is
verified: take the bases called at the ported peak positions, blastn them vs
the M13 gold-standard reference, and compare against the DLL's ESD call and
our previous de-novo result.

Metrics (same as plate_blast /_blast_seq):
  bases      = qlen (number of detected bases fed to blast)
  matched_bp = aligned_length - mismatch - gapopen  (bases that truly match)
  full_ident = matched_bp / qlen   over ALL detected bases
  pident     = BLAST identity over the aligned HSP only
  hsp_cov    = HSP query coverage %
"""
import sys, os
sys.path.insert(0, "/media/tv/78B0C7DE1FA7081C1/electropherogram/sanger_toolkit")
sys.path.insert(0, "/media/tv/78B0C7DE1FA7081C1/electropherogram")
sys.path.insert(0, "/media/tv/78B0C7DE1FA7081C1/electropherogram/02_denovo_cnn_ensemble_91.53pct")
os.environ.setdefault('TF_CPP_MIN_LOG_LEVEL', '3')

import numpy as np
import extract_training_data as etd
import plate_blast as pb
import dll_peakdet as dk

ROOT = "/media/tv/78B0C7DE1FA7081C1/electropherogram"
GTD = os.path.join(ROOT, "MB1000_M13_DT", "MB1000_M13_DT_Cp312_MD1")
CACHE = os.path.join(ROOT, "cache_sep")


def run(well):
    lanes = np.load(os.path.join(CACHE, well + ".npy"))
    d = etd.parse_esd(os.path.join(GTD, well + ".esd"))
    dll_seq = d["sequence"]

    # ported raw detector: dominant-channel decode at ported peak positions
    pos, seq, inten = dk.dll_peaks(lanes)

    # DLL ESD call
    dllb = pb._blast_seq(dll_seq)

    rows = []
    rows.append(("DLL-ESD", dllb, dll_seq))

    # ported detector, raw vs with CNN re-call if models available
    oursb_raw = pb._blast_seq(seq)
    rows.append(("ours-port-raw", oursb_raw, seq))

    print(f"\n===== {well} — BLAST vs M13 (gold-standard) =====")
    for name, r, s in rows:
        if r is None:
            print(f"  {name:14s}: NO ALIGNMENT (seq too short)")
            continue
        print(f"  {name:14s}: bases={r['bases']:5d} matched_bp={r['matched']:5d} "
              f"full_ident={r['full_ident']:6.2f}% pident={r['pident']:6.2f}% "
              f"hsp_cov={r['hsp_cov']:6.2f}%")


for w in ["A01", "A02"]:
    run(w)
