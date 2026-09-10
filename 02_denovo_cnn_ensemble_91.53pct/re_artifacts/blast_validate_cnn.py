#!/usr/bin/env python3
"""End-to-end BLAST validation: ported DLL envelope-peak positions -> CNN
re-call (the real perfect_basecaller path) -> BLAST vs M13 gold standard.
Compares ours vs the DLL-ESD call on the same blast metric.

This is the check the user asked for: verify the base-called peaks the way any
sequencing run is verified (blast against a known reference, M13 here).
The raw port over-detects (~1217 peaks), so it MUST be run through the CNN
re-call + confidence dropout (perfect_basecaller machinery) before BLASTing.
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
import perfect_basecaller as pbc
import cimarrontv_shim as cs

ROOT = "/media/tv/78B0C7DE1FA7081C1/electropherogram"
GTD = os.path.join(ROOT, "MB1000_M13_DT", "MB1000_M13_DT_Cp312_MD1")
PLT = os.path.join(ROOT, "MB1000_M13_DT")
CACHE = os.path.join(ROOT, "cache_sep")
PAT = os.path.join(ROOT, "02_denovo_cnn_ensemble_91.53pct")

# load CNN ensemble (v4 clean/pos/pos_b), same as plate_blast.load_models
MODELS = [__import__('tensorflow').keras.models.load_model(
    os.path.join(PAT, f), compile=False)
    for f in ['base_caller_model_v4_clean.keras',
              'base_caller_model_v4_pos.keras',
              'base_caller_model_v4_pos_b.keras']]


def cnn_recall_peaks(well):
    lanes = np.load(os.path.join(CACHE, well + ".npy"))
    pos, raw_seq, inten = dk.dll_peaks(lanes)  # ported peak positions
    ch, scans = cs.read_rsd(os.path.join(PLT, well + ".rsd"))
    chw = np.asarray(ch, dtype=np.float64)
    if chw.ndim == 2 and chw.shape[0] == 4 and chw.shape[0] <= chw.shape[1]:
        chw = chw.T
    # CNN re-call at ported peak positions
    probs = pbc.cnn_probs(MODELS, chw, pos)
    pmax = probs.max(1)
    pred = probs.argmax(1)
    # adaptive confidence dropout (mirror refine_denovo_v2 defaults)
    drop_hi, drop_lo = 0.55, 0.40
    s0, s1 = int(pos[0]), int(pos[-1])
    srange = max(1, s1 - s0)
    frac = (pos - s0) / srange
    thr = drop_hi + (drop_lo - drop_hi) * frac
    keep = pmax >= thr
    keep_scans = pos[keep]
    # dedupe: keep one peak per ~half peak-spacing (CNN broad peak splitting)
    # (skip aggressive dedupe for now; just report raw + dropped counts)
    seq = ''.join(pbc.LABELS[pred[k]] for k in range(len(pos)) if keep[k])
    return keep_scans, seq, len(pos), int(keep.sum())


def run(well):
    d = etd.parse_esd(os.path.join(GTD, well + ".esd"))
    dll_seq = d["sequence"]
    dllb = pb._blast_seq(dll_seq)

    pos, seq, npks, nkeep = cnn_recall_peaks(well)
    oursb = pb._blast_seq(seq)

    print(f"\n===== {well} — BLAST vs M13 (gold-standard) =====")
    print(f"  ported peaks={npks} -> after CNN+dropout={nkeep}  (DLL called={len(d['peak_positions'])})")
    for name, r in [("DLL-ESD", dllb), ("ours-port+CNN", oursb)]:
        if r is None:
            print(f"  {name:14s}: NO ALIGNMENT")
            continue
        print(f"  {name:14s}: bases={r['bases']:5d} matched_bp={r['matched']:5d} "
              f"full_ident={r['full_ident']:6.2f}% pident={r['pident']:6.2f}% "
              f"hsp_cov={r['hsp_cov']:6.2f}%")


for w in ["A01", "A02"]:
    run(w)
