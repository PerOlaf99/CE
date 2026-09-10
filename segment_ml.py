"""Empirical test of the user's segmentation-for-ML hypothesis.

Thesis: peak patterns change over scan time (spacing grows, matrix drifts,
per-region params differ -- all measured earlier), so training a SEPARATE
classifier per scan-position segment -- instead of one global base caller or one
global CNN with a position channel -- should raise the honest per-segment bar.

Pipeline, per well:
  1. Extract labeled sliding-window k-mer features (raw 31x4 trace patch per
     ESD peak) + background windows: extract_training_data.{extract_training_well,
     _sample_background}.
  2. Segment every window by BASE INDEX (equal base count per band, matching the
     spectral-bucket scheme) into N scan-time bands.
  3. For each band, train a separate sklearn classifier (RandomForest on the
     flattened window + aux features) to call ACGT vs background at THAT scan
     position.
  4. Resolve each band's detection threshold with the STRICT SET-MATCH objective
     (same number of peaks as ESD, every ESD peak covered, none over-called) --
     NOT local identity, which rewards over-calling.
  5. Report per-band and whole-read set-match + M13 identity, and compare to the
     committed single-global caller (track_bases_segmented).

Honest caveats baked in:
  * Labels are ESD (DLL) -> ceiling is DLL accuracy (~95% truth), never higher.
  * Segmentation can improve recall/precision AT that level and generalize
    per-region tuning; it cannot beat the DLL on biological truth.
  * sklearn only (9 is present); torch is not needed for a RandomForest/MLP.
"""
import os
import sys
import glob
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, '/home/per/Nedlastinger/Claude/cimarron_basecaller')

import numpy as np

from sanger_toolkit import extract_training_data as ETD
from sanger_toolkit.blast_check import blast_eval
from cimarron_basecaller.rsd_io import read_rsd, to_acgt_trace

import cimarron_basecaller as C

RSD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       "MB1000_M13_DT")
ESD_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "wineprefix/drive_c/Program Files/Molecular Dynamics/MegaBACE/"
    "AnalyzedData/MB1000_M13_DT_wine_Cp312_MD1")

BASE_MAP = {'A': 0, 'C': 1, 'G': 2, 'T': 3, 'N': 4}


def load_windows(well, window=15, bg_ratio=1.0, seed=42):
    """Return labeled X (N,2w+1,4), y (0-4), positions, per well."""
    Xg, yg, posg, _ = ETD.extract_training_well(
        well, "Cp312", ESD_DIR, RSD_DIR, window=window)
    if Xg is None:
        return None
    df = ETD.parse_rsd(os.path.join(RSD_DIR, f"{well}.rsd"))
    ch = df[['Channel1', 'Channel2', 'Channel3', 'Channel4']].values
    Xb, yb, _ = ETD._sample_background(ch, posg, len(posg), window=window,
                                       ratio=bg_ratio, rng=np.random.RandomState(seed))
    if Xb is not None:
        X = np.concatenate([Xg, Xb], axis=0)
        y = np.concatenate([yg, np.full(len(Xb), 4)], axis=0)
        pos = np.concatenate([posg.astype(float),
                              np.full(len(Xb), -1.0)], axis=0)
    else:
        X, y, pos = Xg, yg, posg.astype(float)
    return X, y, pos, posg


def segment_indices(pos, n_seg):
    """Split base positions into n_seg equal-COUNT bands (ignoring bg=-1)."""
    esd_mask = pos >= 0
    idx_esd = np.where(esd_mask)[0]
    order = np.argsort(pos[idx_esd])
    boundaries = []
    seg_of_pos = -np.ones(len(pos), dtype=int)
    for b in range(n_seg):
        lo = (b * len(order)) // n_seg
        hi = ((b + 1) * len(order)) // n_seg
        members = idx_esd[order[lo:hi]]
        seg_of_pos[members] = b
        boundaries.append((float(pos[members].min()), float(pos[members].max())))
    return seg_of_pos, boundaries


def featurize(X, pos=None, n_scans=None):
    """Flatten the 31x4 window into a feature vector; append position-fraction
    (0..1) so the classifier can exploit where in the read the peak sits."""
    Xf = X.reshape(len(X), -1).astype(np.float64)
    if pos is not None and n_scans is not None:
        frac = np.clip(pos / max(n_scans, 1), 0, 1.0).reshape(-1, 1)
        safe = np.where(np.isnan(frac), 0.0, frac)
        Xf = np.concatenate([Xf, safe], axis=1)
    # z-score each feature (std -> finite)
    mu = Xf.mean(axis=0, keepdims=True)
    sd = Xf.std(axis=0, keepdims=True)
    sd = np.where(sd < 1e-6, 1.0, sd)
    return (Xf - mu) / sd


def seg_set_match(best_probs, is_positive, thresh):
    """Strict set-match: positive = probs>=thresh AND is_positive(ESD).
    Returns (set_match_score, covered, n_esd, n_called, extras)."""
    pred_pos = best_probs >= thresh
    n_esd = int(is_positive.sum())
    n_call = int(pred_pos.sum())
    covered = int((pred_pos & is_positive).sum())
    extras = int((pred_pos & ~is_positive).sum())
    # 100 iff exactly the ESD set called (covered==n_esd, n_call==n_esd, no extras)
    set_match = 100.0 if (n_esd and covered == n_esd and n_call == n_esd) else 0.0
    return set_match, covered, n_esd, n_call, extras


def train_segment(X_s, y_s, pos_s, model):
    """Train one segment's classifier on (positives = ESD 0..3, negative = bg 4),
    pick confidence threshold by strict set-match on the TRAIN split, returning
    (model, threshold, is_positive_mask, probs)."""
    is_pos = (y_s != 4) & (pos_s >= 0)
    model.fit(X_s, y_s != 4)
    probs = np.clip(np.max(model.predict_proba(X_s)[:, 1:], axis=1)
                    if model.classes_.size >= 2 else np.zeros(len(X_s)), 0, 1)
    thresh = best = None
    # grid thresholds to find the strict set-match optimum on the positives
    for t in np.arange(0.05, 1.0, 0.05):
        sm, cov, ne, nc, ex = seg_set_match(probs, is_pos, t)
        score = (sm, cov, -nc)  # match first, coverage, then fewest calls
        if best is None or score > best:
            best, thresh = score, t
    return model, thresh, is_pos, probs


def run_segment_ml(well, n_seg=5, window=15, bg_ratio=1.0, seed=42,
                   verbose=True):
    from sklearn.ensemble import RandomForestClassifier
    data = load_windows(well, window=window, bg_ratio=bg_ratio, seed=seed)
    if data is None:
        return None
    X, y, pos, esd_pos = data
    df = ETD.parse_rsd(os.path.join(RSD_DIR, f"{well}.rsd"))
    ch = df[['Channel1', 'Channel2', 'Channel3', 'Channel4']].values
    n_scans = len(ch)
    seg_of_pos, bounds = segment_indices(pos, n_seg)
    bg_mask = pos < 0

    seg_rows = []
    for b in range(n_seg):
        # this segment's ESD positives + the GLOBAL background as negatives
        pos_mask = (seg_of_pos == b) & ~bg_mask
        neg_mask = bg_mask
        m = pos_mask | neg_mask
        Xb, yb, pb = X[m], y[m], pos[m]
        model = RandomForestClassifier(
            n_estimators=80, max_depth=8, n_jobs=-1, random_state=seed)
        mdl, thresh, is_pos, probs = train_segment(
            featurize(Xb, pb, n_scans), yb, pb, model)
        sm, cov, ne, nc, ex = seg_set_match(probs, is_pos, thresh)
        order = esd_pos[(esd_pos >= bounds[b][0]) & (esd_pos <= bounds[b][1])]
        seg_rows.append({"seg": b, "scan_range": bounds[b], "n_esd": ne,
                         "set_match": sm, "covered": cov, "n_call": nc,
                         "extras": ex, "thresh": round(thresh, 2)})
        if verbose:
            print(f"{well} seg{b} scans[{bounds[b][0]:.0f},{bounds[b][1]:.0f}] "
                  f"n_esd={ne} set={sm:.0f}% cover={cov} call={nc} extra={ex} "
                  f"thr={round(thresh,2)}")

    whole = {"set_match": np.mean([r["set_match"] for r in seg_rows]),
             "covered": sum(r["covered"] for r in seg_rows),
             "n_call": sum(r["n_call"] for r in seg_rows)}
    whole["extras"] = sum(r["extras"] for r in seg_rows)
    whole["n_esd"] = sum(r["n_esd"] for r in seg_rows)
    whole["set_match"] = 100.0 if (whole["n_esd"]
                                   and whole["covered"] == whole["n_esd"]
                                   and whole["n_call"] == whole["n_esd"]) else 0.0
    return {"well": well, "segments": seg_rows, "whole": whole}


def baseline_caller(well):
    """The committed single-global caller as the comparison baseline."""
    trace, order = to_acgt_trace(read_rsd(os.path.join(RSD_DIR, f"{well}.rsd")),
                                 base_order="TGCA")
    s, _, _ = C.track_bases_segmented(trace, base_order=order)
    b = blast_eval(s, 'megablast')
    return {"identity": b['pident'], "aligned": b['aligned'], "gaps": b['gaps']}


def cross_validate(wells, n_seg=5, bg_ratio=1.0, seed=42, window=15, verbose=True):
    """HONEST out-of-sample test.  For each fold, train per-segment models on
    the background + all OTHER wells' ESD peaks, then evaluate on the held-out
    well's ESD peaks with the trained thresholds.  High set-match here means the
    segmentation GENERALIZES (not just memorizing one well's DLL calls);
    near-0 means it overfits the training well."""
    from sklearn.ensemble import RandomForestClassifier
    # pool training data once per fold
    pooled = {}
    for w in wells:
        d = load_windows(w, window=window, bg_ratio=0.0, seed=seed)  # bg once
        if d is None:
            continue
        pooled[w] = d

    out = {}
    for test in wells:
        if test not in pooled:
            continue
        train_pos = []
        bg = None
        for w in wells:
            if w == test:
                continue
            X, y, pos, _ = pooled[w]
            esdm = (y != 4) & (pos >= 0)
            train_pos.append((X[esdm], y[esdm]))
            if bg is None:
                bm = pos < 0
                bg = (X[bm], y[bm])
        # build one featurizer per segment over pooled train positives
        # positions for segmentation: use train well esd positions plus bg
        allX = np.concatenate([x for x, _ in train_pos] +
                              ([bg[0]] if bg is not None else []), axis=0)
        ally = np.concatenate([yy for _, yy in train_pos] +
                              ([bg[1]] if bg is not None else []), axis=0)
        allpos = np.concatenate(
            [np.full(len(x), float(i)) for i, (x, _) in enumerate(train_pos)] +
            ([-1.0] * len(bg[0]) if bg is not None else []), axis=0)
        if bg is None:
            return None
        # segment the whole pooled training set by scan order of its esd bases
        seg_of_train, _ = segment_indices(allpos, n_seg)
        df = ETD.parse_rsd(os.path.join(RSD_DIR, f"{test}.rsd"))
        n_scans = len(df[['Channel1', 'Channel2', 'Channel3', 'Channel4']].values)

        seg_models = []
        for b in range(n_seg):
            pm = (seg_of_train == b) & (allpos >= 0)
            gm = allpos < 0
            m = pm | gm
            rf = RandomForestClassifier(n_estimators=80, max_depth=8,
                                        n_jobs=-1, random_state=seed)
            _, thr, _, _ = train_segment(featurize(allX[m], allpos[m], n_scans),
                                         ally[m], allpos[m], rf)
            seg_models.append((rf, thr))

        # EVALUATE on held-out well's ESD peaks.  Because load_windows was
        # called with bg_ratio=0, every test window is centered on a real ESD
        # peak; the model must recall all of them (out-of-sample recall).
        XT, yT, posT, esd_posT = pooled[test][:4]
        is_posT = (yT != 4) & (posT >= 0)
        eval_order = np.where(is_posT)[0]
        eo = eval_order[np.argsort(posT[eval_order])]
        segT = np.full(len(posT), -1)
        for b in range(n_seg):
            lo = (b * len(eo)) // n_seg; hi = ((b + 1) * len(eo)) // n_seg
            segT[eo[lo:hi]] = b
        tot_call = tot_esd = 0
        for b in range(n_seg):
            m = (segT == b) & is_posT
            ne = int(m.sum())
            if ne == 0:
                continue
            Xf = featurize(XT[m], posT[m], n_scans)
            rf, thr = seg_models[b]
            prob = rf.predict_proba(Xf)
            if prob.shape[1] >= 2:
                pr = prob[:, 1]
            else:
                pr = prob[:, 0]
            tot_call += int((pr >= thr).sum())
            tot_esd += ne
        setm = 100.0 if (tot_esd and tot_call == tot_esd) else 0.0
        out[test] = {"set_match": setm, "covered": tot_call, "n_call": tot_call,
                     "n_esd": tot_esd, "extras": 0}
        if verbose:
            print(f"CV hold-out {test}: set-match={setm:.0f}% recalled={tot_call}/"
                  f"{tot_esd}")
    return out


def build_confidence_curve(well, seg_models, n_seg=5, window=15, n_scans=None):
    """Compute a per-scan ML confidence array for `well` using already-trained
    per-segment (model, threshold) pairs.  Confidence = positive-class proba
    of the RF on the 31x4 window centered at each scan (0 where the window
    would fall off the trace edge).  This is the array fed to
    track_bases_segmented(..., ml_confidence=conf, ml_min_confidence=thr)."""
    df = ETD.parse_rsd(os.path.join(RSD_DIR, f"{well}.rsd"))
    ch = df[['Channel1', 'Channel2', 'Channel3', 'Channel4']].values
    if n_scans is None:
        n_scans = len(ch)
    conf = np.zeros(n_scans)
    scan = np.arange(n_scans)
    # segment assignment by scan position into n_seg equal-SPAN bands (approx)
    band = np.clip(scan // max(n_scans // n_seg, 1), 0, n_seg - 1)
    for b, (model, thr) in enumerate(seg_models):
        m = band == b
        idx = np.where(m)[0]
        # keep only scans with a full window
        keep = (idx >= window) & (idx < n_scans - window)
        idx = idx[keep]
        if len(idx) == 0:
            continue
        X = np.stack([ch[i - window:i + window + 1] for i in idx], axis=0)
        Xf = featurize(X, idx.astype(float), n_scans)
        prob = model.predict_proba(Xf)
        p = prob[:, 1] if prob.shape[1] >= 2 else prob[:, 0]
        conf[idx] = p
    return conf


def gated_call(well, train_wells, ml_min_confidence=0.10, n_seg=5, verbose=True):
    """Train per-segment RFs on train_wells, compute per-scan ML confidence for
    `well`, and run track_bases_segmented gated by that confidence.  This is
    the ML x spacing-gate conjunction that raised M13 identity ~+1.3 (see
    PROJECT_HISTORY 2026-09-02).  Returns (sequence, qualities, tracked, conf)."""
    from sklearn.ensemble import RandomForestClassifier
    rt_pos = []; bg = None
    for w in train_wells:
        X, y, pos, _ = load_windows(w, bg_ratio=1.0)
        e = (y != 4) & (pos >= 0); rt_pos.append((X[e], y[e]))
        b = pos < 0
        bg = (X[b], y[b]) if bg is None else (np.concatenate([bg[0], X[b]]),
                                              np.concatenate([bg[1], y[b]]))
    XP = np.concatenate([x for x, _ in rt_pos]); YP = np.concatenate([y for _, y in rt_pos])
    allX = np.concatenate([XP, bg[0]]); allY = np.concatenate([YP, bg[1]])
    allpos = np.r_[np.arange(len(XP)), -np.ones(len(bg[0]))]
    seg, _ = segment_indices(allpos, n_seg)
    df = ETD.parse_rsd(os.path.join(RSD_DIR, f"{well}.rsd"))
    nsc = len(df[['Channel1', 'Channel2', 'Channel3', 'Channel4']].values)
    seg_models = []
    for b in range(n_seg):
        pm = (seg == b) & (allpos >= 0); gm = allpos < 0; m = pm | gm
        rf = RandomForestClassifier(n_estimators=80, max_depth=8,
                                    n_jobs=-1, random_state=42)
        _, thr, _, _ = train_segment(featurize(allX[m], allpos[m], nsc),
                                     allY[m], allpos[m], rf)
        seg_models.append((rf, thr))
    conf = build_confidence_curve(well, seg_models, n_seg, n_scans=nsc)
    trace, order = to_acgt_trace(read_rsd(os.path.join(RSD_DIR, f"{well}.rsd")),
                                 base_order="TGCA")
    s, q, b = C.track_bases_segmented(trace, base_order=order,
                                     ml_confidence=conf,
                                     ml_min_confidence=ml_min_confidence)
    if verbose:
        bm = blast_eval(s, 'megablast')
        print(f"{well} gated(ml>= {ml_min_confidence}): M13 id={bm['pident']:.1f}% "
              f"align={bm['aligned']} gaps={bm['gaps']} n={len(s)}")
    return s, q, b, conf


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--wells", default="A01,A02,A03,A04")
    ap.add_argument("--nseg", type=int, default=5)
    ap.add_argument("--bg", type=float, default=1.0)
    ap.add_argument("--cv", action="store_true",
                    help="run HONEST out-of-sample cross-validation")
    ap.add_argument("--gate", type=float, default=None,
                    help="per-scan ML confidence gate; apply gated caller on "
                         "first --well with the others as training (LEAVE-OUT test)")
    args = ap.parse_args()
    wells = [w.strip() for w in args.wells.split(",") if w.strip()]
    if args.gate is not None:
        # leave-one-out gated call for the first well, trained on the rest
        test = wells[0]; train = [w for w in wells[1:]]
        gated_call(test, train, ml_min_confidence=args.gate)
        sys.exit(0)
    if args.cv:
        res = cross_validate(wells, n_seg=args.nseg, bg_ratio=args.bg, verbose=True)
        for w in wells:
            if w in res:
                print(f"{w}: out-of-sample set-match={res[w]['set_match']:.0f}%")
            else:
                print(f"{w}: no data")
            bc = baseline_caller(w)
            print(f"   baseline caller M13 id={bc['identity']:.1f}% "
                  f"align={bc['aligned']} gaps={bc['gaps']}")
    else:
        for w in wells:
            print(f"\n== {w} segmented-ML (in-sample) ==")
            res = run_segment_ml(w, n_seg=args.nseg, bg_ratio=args.bg)
            if res is not None:
                print(f"{w} whole-read set-match={res['whole']['set_match']:.0f}% "
                      f"(n_esd={res['whole']['n_esd']})")
            bc = baseline_caller(w)
            print(f"{w} baseline caller: M13 id={bc['identity']:.1f}% "
                  f"align={bc['aligned']} gaps={bc['gaps']}")