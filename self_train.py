#!/usr/bin/env python3
"""Self-training RF basecaller: train on ESD labels, pseudo-label new wells, retrain.

Strategy:
  1. Train initial RF on ESD-labeled data (Cp312 peak positions + labels)
  2. For unlabeled wells: peak detect → classify → filter high-confidence → pseudo-labels
  3. Retrain RF on original + pseudo-labels
  4. Iterate until matching Cp312 M13 accuracy
"""
import sys, os, time, json
import numpy as np
from scipy.signal import find_peaks
from sklearn.ensemble import RandomForestClassifier

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from extract_training_data import parse_rsd, parse_esd
from tracetuner_separation import trace_tuner_separate
from simple_align import align_to_m13

BASE_DIR = "/media/tv/78B0C7DE1FA7081C/electropherogram/MB1000_M13_DT"
ESD_DIR = "MB1000_M13_DT_Cp312_MD1"
WINDOW = 15
BASE_MAP = {'A':0,'C':1,'G':2,'T':3,'N':4}
INV_MAP = {0:'A',1:'C',2:'G',3:'T'}
RF_PARAMS = dict(n_estimators=500, max_depth=12, class_weight='balanced',
                 n_jobs=-1, random_state=42)


def load_separate(well):
    rsd_path = os.path.join(BASE_DIR, f"{well}.rsd")
    df = parse_rsd(rsd_path)
    ch = df[['Channel1','Channel2','Channel3','Channel4']].values.T.astype(np.float64)
    return trace_tuner_separate(ch)


def per_well_zscore_trace(sep):
    r = sep.copy()
    for c in range(4):
        mu, sd = r[c].mean(), r[c].std()
        if sd > 1e-8:
            r[c] = (r[c] - mu) / sd
    return r


def extract_windows(sep, positions):
    n = sep.shape[1]
    windows, valid = [], []
    for p in positions:
        if p < WINDOW or p >= n - WINDOW:
            continue
        windows.append(sep[:, p - WINDOW:p + WINDOW + 1].T)
        valid.append(p)
    if not windows:
        return np.array([]), np.array([], dtype=int)
    return np.array(windows, dtype=np.float32), np.array(valid)


def scan_classify(rf, sep_n, threshold=0.90, stride=1):
    """Use RF as sliding-window classifier: predict at every scan position,
    keep high-confidence predictions, merge nearby."""
    n = sep_n.shape[1]
    windows = []
    positions = []
    for p in range(WINDOW, n - WINDOW, stride):
        windows.append(sep_n[:, p - WINDOW:p + WINDOW + 1].T)
        positions.append(p)
    if not windows:
        return np.array([]), np.array([], dtype=int), np.array([])
    X = np.array(windows, dtype=np.float32).reshape(-1, (WINDOW*2+1)*4)
    probs = rf.predict_proba(X)
    max_p = probs.max(axis=1)
    preds = probs.argmax(axis=1)
    confident = max_p >= threshold
    if confident.sum() == 0:
        return np.array([]), np.array([], dtype=int), np.array([])
    # Merge nearby predictions (NMS)
    kept_pos, kept_pred, kept_conf = [], [], []
    order = np.argsort(-max_p[confident])  # highest confidence first
    cpos = np.array(positions)[confident]
    cpred = preds[confident]
    cconf = max_p[confident]
    used = np.zeros(len(cpos), dtype=bool)
    for i in order:
        if used[i]: continue
        # Mark all within nms_distance as used
        nms = 3
        cluster = np.abs(cpos - cpos[i]) <= nms
        used[cluster] = True
        kept_pos.append(cpos[i])
        kept_pred.append(cpred[i])
        kept_conf.append(cconf[i])
    return (np.array(kept_pos), np.array(kept_pred), np.array(kept_conf))


def pseudo_label_well(rf, well, threshold=0.95):
    """Generate pseudo-labels for one well using scanning RF classifier."""
    try:
        sep = load_separate(well)
    except Exception:
        return None
    sep_n = per_well_zscore_trace(sep)
    positions, preds, confs = scan_classify(rf, sep_n, threshold=threshold, stride=1)
    if len(positions) < 5:
        return None
    windows, valid = extract_windows(sep_n, positions)
    if len(windows) == 0:
        return None
    return {
        'X': windows.reshape(len(windows), -1),
        'y': preds,
        'positions': positions,
        'confidence': confs,
        'well': well,
        'total_peaks': len(positions),
        'confident_count': len(positions),
    }


def load_esd_labels(wells):
    """Load ESD-labeled training data for given wells."""
    X_all, y_all, w_all = [], [], []
    for well in wells:
        sep, sep_n = None, None
        try:
            sep = load_separate(well)
            sep_n = per_well_zscore_trace(sep)
        except Exception:
            continue
        try:
            esd = parse_esd(os.path.join(BASE_DIR, ESD_DIR, f"{well}.esd"))
        except Exception:
            continue
        seq = esd.get('sequence','')
        positions = esd.get('peak_positions')
        if positions is None:
            positions = esd.get('bases_positions')
        if not seq or positions is None:
            continue
        n = min(len(seq), len(positions))
        positions = positions[:n].astype(int)
        seq = seq[:n]
        X_w, pos_w = extract_windows(sep_n, positions)
        y_w = np.array([BASE_MAP.get(b, 4) for b in seq])
        keep = y_w != 4
        X_all.append(X_w[keep])
        y_all.append(y_w[keep])
        w_all.append(np.full(keep.sum(), well))
    if not X_all:
        return None, None, None
    return (np.concatenate(X_all, axis=0).reshape(-1, (WINDOW*2+1)*4),
            np.concatenate(y_all, axis=0),
            np.concatenate(w_all))


def load_esd_labels_from_npz(npz_path):
    """Load pre-separated ESD-labeled data from .npz."""
    d = np.load(npz_path, allow_pickle=True)
    X = d['X'].astype(np.float32)
    y = d['y'].copy()
    wells = d['wells']
    keep = y != 4
    X, y, wells = X[keep], y[keep], wells[keep]
    for w in np.unique(wells):
        mask = wells == w
        for ch in range(4):
            data = X[mask, :, ch]
            mu, sd = data.mean(), data.std()
            if sd > 1e-8:
                X[mask, :, ch] = (data - mu) / sd
    return X.reshape(X.shape[0], -1), y, wells


def pseudo_label_well(rf, well, threshold=0.95):
    """Generate pseudo-labels for one well using scanning RF classifier."""
    try:
        sep = load_separate(well)
    except Exception:
        return None
    sep_n = per_well_zscore_trace(sep)
    positions, preds, confs = scan_classify(rf, sep_n, threshold=threshold, stride=1)
    if len(positions) < 5:
        return None
    windows, valid = extract_windows(sep_n, positions)
    if len(windows) == 0:
        return None
    return {
        'X': windows.reshape(len(windows), -1),
        'y': preds,
        'positions': positions,
        'confidence': confs,
        'well': well,
        'total_peaks': len(positions),
        'confident_count': len(positions),
    }


def evaluate_well(model, well):
    """M13 evaluation using ESD positions (for benchmarking)."""
    try:
        sep = load_separate(well)
    except Exception:
        return 0, 0
    sep_n = per_well_zscore_trace(sep)
    try:
        esd = parse_esd(os.path.join(BASE_DIR, ESD_DIR, f"{well}.esd"))
    except Exception:
        return 0, 0
    positions = esd['peak_positions']
    seq = esd.get('sequence','')
    if not seq or positions is None:
        return 0, 0
    n = min(len(seq), len(positions))
    positions = positions[:n].astype(int)
    seq = seq[:n]
    windows, valid = extract_windows(sep_n, positions)
    if len(windows) == 0:
        return 0, 0
    pred = model.predict(windows.reshape(len(windows), -1))
    called = ''.join(INV_MAP.get(int(p),'N') for p in pred)
    res = align_to_m13(called)

    # Cp312 baseline
    cp_seq = seq[:len(valid)]
    cp_res = align_to_m13(cp_seq)
    rf_id = res['identity'] if res else 0
    cp_id = cp_res['identity'] if cp_res else 0
    return rf_id, cp_id


def self_train_loop(initial_labeled_wells, eval_wells, n_iters=3, threshold=0.95,
                    npz_path=None):
    """Self-training loop. Returns history of iterations."""
    history = []

    train_wells = list(initial_labeled_wells)

    if npz_path:
        X_all, y_all, w_all = load_esd_labels_from_npz(npz_path)
        mask = np.isin(w_all, train_wells)
        X_base, y_base = X_all[mask], y_all[mask]
        print(f"Loaded {len(y_base)} samples from npz for {len(train_wells)} training wells")
    else:
        X_base, y_base, w_base = load_esd_labels(train_wells)

    for it in range(n_iters):
        print(f"\n{'='*60}")
        print(f"Iteration {it+1}/{n_iters}")
        print(f"{'='*60}")
        print(f"Training RF on {len(train_wells)} wells ({len(y_base)} samples)...")
        t0 = time.time()
        rf = RandomForestClassifier(**RF_PARAMS)
        rf.fit(X_base, y_base)
        print(f"  Trained in {time.time()-t0:.0f}s")

        # Evaluate on test wells (ESD-supervised M13 identity)
        rf_ids, cp_ids = [], []
        for well in eval_wells:
            rf_id, cp_id = evaluate_well(rf, well)
            rf_ids.append(rf_id)
            cp_ids.append(cp_id)

        mean_rf = np.mean(rf_ids) if rf_ids else 0
        mean_cp = np.mean(cp_ids) if cp_ids else 0
        print(f"  Supervised M13: RF={mean_rf:.1f}%  Cp312={mean_cp:.1f}%")

        # Pseudo-label: use training wells themselves (remove ESD, pretend unlabeled)
        new_pseudo = []
        for well in train_wells:
            pl = pseudo_label_well(rf, well, threshold=threshold)
            if pl is not None:
                new_pseudo.append(pl)
                if it == 0:
                    n_pos = pl['confident_count']
                    print(f"  {well}: {pl['total_peaks']} peaks, {n_pos} confident (≥{threshold})")

        total_pseudo = sum(p['confidence'].shape[0] for p in new_pseudo)
        print(f"  Total pseudo-labels added: {total_pseudo}")

        # Expand training set with pseudo-labels
        if new_pseudo:
            X_pseudo = np.concatenate([p['X'] for p in new_pseudo], axis=0)
            y_pseudo = np.concatenate([p['y'] for p in new_pseudo], axis=0)
            X_base = np.concatenate([X_base, X_pseudo], axis=0)
            y_base = np.concatenate([y_base, y_pseudo], axis=0)
            print(f"  Expanded training set: {len(y_base)} samples")

        # Self-training evaluation: full pipeline (scan+classify) on test wells
        print(f"  Full pipeline (scan RF + classify) on test wells...")
        pipe_ids = []
        for well in eval_wells:
            try:
                sep = load_separate(well)
                sep_n = per_well_zscore_trace(sep)
                positions, preds, _ = scan_classify(rf, sep_n, threshold=0.5, stride=1)
            except Exception:
                continue
            if len(positions) < 10:
                continue
            called = ''.join(INV_MAP.get(int(p),'N') for p in preds)
            res = align_to_m13(called)
            pipe_ids.append(res['identity'] if res else 0)

        mean_pipe = np.mean(pipe_ids) if pipe_ids else 0
        print(f"  Full pipeline M13: {mean_pipe:.1f}% (on {len(eval_wells)} wells)")

        history.append({
            'iteration': it + 1,
            'train_samples': len(y_base),
            'pseudo_labels': total_pseudo,
            'supervised_rf_mean': mean_rf,
            'cp312_mean': mean_cp,
            'full_pipeline_mean': mean_pipe,
        })

    return history, rf


def main():
    rows = [chr(ord('A')+i) for i in range(8)]
    cols = [f'{i:02d}' for i in range(1, 13)]
    all_wells = [f'{r}{c}' for r in rows for c in cols]

    # Use first 80 wells for training, 16 for evaluation
    train_wells = all_wells[:80]
    eval_wells = all_wells[80:]

    print(f"Train wells: {train_wells[0]}-{train_wells[-1]} ({len(train_wells)})")
    print(f"Eval wells:  {eval_wells[0]}-{eval_wells[-1]} ({len(eval_wells)})")

    npz_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            'training_data_separated', 'Cp312.npz')
    history, model = self_train_loop(train_wells, eval_wells, n_iters=3, threshold=0.95,
                                     npz_path=npz_path if os.path.exists(npz_path) else None)

    print(f"\n{'='*60}")
    print(f"HISTORY")
    print(f"{'='*60}")
    for h in history:
        print(f"  Iter {h['iteration']}: supervised RF={h['supervised_rf_mean']:.1f}% "
              f"Cp312={h['cp312_mean']:.1f}% "
              f"pipeline={h['full_pipeline_mean']:.1f}% "
              f"(+{h['pseudo_labels']} pseudo)")

    import joblib
    joblib.dump(model, '/tmp/self_trained_rf.pkl')
    print(f"\nModel saved to /tmp/self_trained_rf.pkl")


if __name__ == '__main__':
    main()
