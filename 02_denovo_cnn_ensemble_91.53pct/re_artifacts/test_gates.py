#!/usr/bin/env python3
"""Test the FUN_10019ef2 env-floor + region-window gating on the ported
detector, judged by the BLAST gold-standard metric (matched_bp) - the only
valid arbiter, per the user's rule."""
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


def run(well, env_floor_fracs, region_window):
    lanes = np.load(os.path.join(CACHE, well + ".npy"))
    d = etd.parse_esd(os.path.join(GTD, well + ".esd"))
    dll_seq = d["sequence"]
    dllb = pb._blast_seq(dll_seq)
    print(f"\n===== {well} (gold: bases={dllb['bases']} matched_bp={dllb['matched']} "
          f"fullid={dllb['full_ident']:.1f}% pident={dllb['pident']:.1f}%) =====")
    for frac in env_floor_fracs:
        pos, seq, inten = dk.dll_peaks(lanes, env_floor_frac=frac,
                                       region_window=region_window)
        b = pb._blast_seq(seq)
        if b is None:
            print(f"  floor={frac:.2f} reg={int(region_window)}: peaks={len(pos)} NO-ALIGN")
            continue
        print(f"  floor={frac:.2f} reg={int(region_window)}: peaks={len(pos)} "
              f"bases={b['bases']} matched_bp={b['matched']} "
              f"fullid={b['full_ident']:.1f}% pident={b['pident']:.1f}% "
              f"hsp={b['hsp_cov']:.1f}%")


for well in ["A01", "A02"]:
    run(well, [0.02, 0.05, 0.08, 0.10, 0.15], region_window=False)
    run(well, [0.02, 0.05, 0.08, 0.10, 0.15], region_window=True)
