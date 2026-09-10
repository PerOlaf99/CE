#!/usr/bin/env python3
"""Port the DLL's portition-adaptive quality/SNR gate (xbnd from
Wvfm::envelope 0x31976, returned by FUN_10024e47) and test it against the
fixed 0.05 floor — judged by the BLAST gold-standard metric (matched_bp).

xbnd[scan] (from envelope() decomp, stored in this+0xd0):
    v1>=v2>=v3>=v4 = sorted 4 channel (lane) values at scan
    min  = v4 ; v3 = third-largest
    if v3 < 8.9e-16: v3 = 2.2e-16
    if 0.1 <= min:  xbnd = min / v3
    else:           xbnd = min / sqrt(v3) + 1.0
    clamp to [1.0, 2.0]
Adaptive keep rule (weak tail peaks survive): keep candidate iff
    envv[scan] > xbnd[scan]   (env over the per-scan adaptive threshold)
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
MODELS = [__import__('tensorflow').keras.models.load_model(
    os.path.join(PAT, f), compile=False)
    for f in ['base_caller_model_v4_clean.keras',
              'base_caller_model_v4_pos.keras',
              'base_caller_model_v4_pos_b.keras']]


def xbnd_array(lanes):
    """Per-scan adaptive SNR threshold (Wvfm::envelope -> this+0xd0)."""
    v = np.sort(lanes, axis=1)          # ascending: v0=min ... v3=max
    vmin = v[:, 0]
    v3 = v[:, 2]                        # third-largest = 2nd smallest
    v3 = np.where(v3 < 8.9e-16, 2.2e-16, v3)
    x = np.where(vmin >= 0.1, vmin / v3, vmin / np.sqrt(v3) + 1.0)
    return np.clip(x, 1.0, 2.0)


def gated_peaks(lanes, mode):
    """Return candidate peak scans + their env, gated by mode."""
    env = lanes.max(axis=1)                    # detector envelope (empirical best)
    cand = dk.env_maxima(env, 2, lanes.shape[0])
    scans = np.array([c[0] for c in cand], dtype=np.int64)
    envs = np.array([c[1] for c in cand], dtype=np.float64)
    # width filter (FUN_10024f29) as in dll_peaks
    dom = lanes.argmax(axis=1)
    widths = np.array([dk.peak_width(lanes[:, int(dom[p])], int(p), e / 2.0)
                       for p, e in zip(scans, envs)])
    if len(widths) > 1:
        lim = 3.0 * ((len(widths) / 2.0 + float(widths.sum())) / len(widths))
        m = widths <= lim
        scans, envs = scans[m], envs[m]
    if mode == "fixed":
        keep = envs >= 0.05 * float(env.max())
    elif mode == "xbnd_abs":
        keep = envs > xbnd_array(lanes)[scans]
    elif mode == "xbnd_rel":
        xb = xbnd_array(lanes)[scans]
        keep = envs > 0.05 * float(env.max()) + (xb - 1.0) * 0.1 * float(env.max())
    elif mode == "flank":
        # FUN_10012140: local_6c = mean(flank-min env), floored 0.05;
        # threshold ~= 1.24 * local_6c  (0.93 * mean * 1.333)
        keep = np.zeros(len(scans), dtype=bool)
        n = len(scans)
        for i in range(n):
            lo = envs[i - 1] if i > 0 else envs[i]
            hi = envs[i + 1] if i + 1 < n else envs[i]
            fm = min(lo, hi)                       # min of two flanking bands
            mmean = fm                             # (single-neighbor approx)
            thr = 1.24 * max(mmean, 0.05)
            keep[i] = envs[i] > thr
    elif mode == "nofloor":
        keep = np.ones(len(scans), dtype=bool)
    else:
        keep = np.ones(len(scans), dtype=bool)
    return scans[keep], envs[keep]


def cnn_blast(well, mode):
    lanes = np.load(os.path.join(CACHE, well + ".npy"))
    pos, envs = gated_peaks(lanes, mode)
    if len(pos) == 0:
        print(f"  {mode:9s}: 0 peaks")
        return
    ch, scans = cs.read_rsd(os.path.join(PLT, well + ".rsd"))
    chw = np.asarray(ch, dtype=np.float64)
    if chw.ndim == 2 and chw.shape[0] == 4 and chw.shape[0] <= chw.shape[1]:
        chw = chw.T
    probs = pbc.cnn_probs(MODELS, chw, pos)
    pmax = probs.max(1); pred = probs.argmax(1)
    drop_hi, drop_lo = 0.55, 0.40
    s0, s1 = int(pos[0]), int(pos[-1]); sr = max(1, s1 - s0)
    thr = drop_hi + (drop_lo - drop_hi) * (pos - s0) / sr
    keep = pmax >= thr
    seq = ''.join(pbc.LABELS[pred[k]] for k in range(len(pos)) if keep[k])
    b = pb._blast_seq(seq)
    if b is None:
        print(f"  {mode:9s}: peaks={len(pos)} -> kept={int(keep.sum())} NO-ALIGN")
    else:
        print(f"  {mode:9s}: peaks={len(pos)} -> kept={int(keep.sum())} "
              f"bases={b['bases']} matched_bp={b['matched']} "
              f"fullid={b['full_ident']:.1f}% pident={b['pident']:.1f}%")


for well in ["A01", "A02"]:
    d = etd.parse_esd(os.path.join(GTD, well + ".esd"))
    g = pb._blast_seq(d["sequence"])
    print(f"\n===== {well} GOLD: bases={g['bases']} matched_bp={g['matched']} "
          f"fullid={g['full_ident']:.1f}% pident={g['pident']:.1f}% =====")
    for mode in ["fixed", "flank", "xbnd_rel"]:
        cnn_blast(well, mode)
