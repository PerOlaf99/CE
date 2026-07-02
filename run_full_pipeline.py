#!/usr/bin/env python3
"""Run the full IS + genotyping pipeline from the command line.

Usage:  ./env/bin/python3 run_full_pipeline.py [--prefix OY_ABCC2_N2]
"""

import os, sys, json, glob, struct, warnings
import numpy as np
import pandas as pd
from scipy.signal import find_peaks

warnings.filterwarnings('ignore')
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OY_DIR = os.path.join(SCRIPT_DIR, 'OY')

def parse_rsd(path):
    with open(path, 'rb') as f:
        raw = f.read()
    records = []
    for i in range(0, len(raw) - 19, 20):
        v = struct.unpack('<IIIII', raw[i:i + 20])
        records.append(v)
    MAX_DATA_VALUE = 200000
    boundary = len(records)
    for i, rec in enumerate(records):
        if any(v > MAX_DATA_VALUE for v in rec):
            boundary = i
            break
    data = records[:boundary]
    df = pd.DataFrame(data, columns=['Current','Channel1','Channel2','Channel3','Channel4'])
    df['Scan'] = np.arange(len(df))
    return df[['Scan','Channel1','Channel2','Channel3','Channel4','Current']]

def peak_features(p, ch3, ch2, noise):
    w = 8
    start = max(0, p - w)
    end = min(len(ch3), p + w + 1)
    window = ch3[start:end]
    window_ch2 = ch2[start:end]
    peak_h = ch3[p]
    ch2_h = ch2[p]
    ratio = peak_h / (ch2_h + 1.0)
    local_min = window.min()
    prominence = peak_h - local_min
    local_std = window.std()
    local_max_ch2 = window_ch2.max()
    offsets = [-7, -5, -3, -1, 0, 1, 3, 5, 7]
    samples = [ch3[max(0, min(len(ch3)-1, p+o))] for o in offsets]
    return np.array([
        peak_h / (noise + 1.0), ratio, prominence / (noise + 1.0),
        local_std / (noise + 1.0), peak_h / (local_max_ch2 + 1.0),
        *[s / (noise + 1.0) for s in samples],
    ])

def find_ch3_local_maxima(ch3, threshold):
    peaks, _ = find_peaks(ch3, height=threshold, distance=3, width=1)
    return peaks

def match_is_pattern(scored_candidates, n_expected, ref_spacing, tol=30):
    if len(scored_candidates) < n_expected:
        return []
    by_scan = sorted(scored_candidates, key=lambda x: x[0])
    scan_positions = [s for s,_ in by_scan]
    best_score = -1
    best_set = []
    for anchor_idx in range(min(20, len(scored_candidates))):
        anchor_scan, anchor_score = scored_candidates[anchor_idx]
        candidate_set = [int(anchor_scan)]
        cumul = anchor_score
        try:
            scan_idx = scan_positions.index(anchor_scan)
        except ValueError:
            continue
        for spacing in ref_spacing:
            expected = candidate_set[-1] + spacing
            best_dist = tol
            best_match = None
            best_match_score = 0
            best_j = scan_idx
            for j in range(scan_idx + 1, len(by_scan)):
                s, sc = by_scan[j]
                if s > expected + best_dist:
                    break
                dist = abs(s - expected)
                if dist < best_dist and s > candidate_set[-1]:
                    best_dist = dist
                    best_match = int(s)
                    best_match_score = sc
                    best_j = j
            if best_match is not None:
                candidate_set.append(best_match)
                cumul += best_match_score
                scan_idx = best_j
            else:
                break
        if len(candidate_set) >= n_expected * 0.7:
            spacing_penalty = 0
            for i in range(min(len(ref_spacing), len(candidate_set)-1)):
                spacing_penalty += abs(candidate_set[i+1]-candidate_set[i] - ref_spacing[i])
            total = cumul - spacing_penalty * 0.01
            if total > best_score:
                best_score = total
                best_set = candidate_set[:n_expected]
    return best_set

def analyze_well(clf, rsd_path, n_expected, ref_spacing=None, tol=30):
    """Find IS peaks in a single .rsd file. If ref_spacing is None, return top-N scorer peaks."""
    df = parse_rsd(rsd_path)
    ch3 = df['Channel3'].values.astype(float)
    ch2 = df['Channel2'].values.astype(float)
    noise = np.std(ch3[:200]) if len(ch3) > 200 else 1.0
    candidates = find_ch3_local_maxima(ch3, noise * 3)
    if len(candidates) == 0:
        return None
    X_cand = np.array([peak_features(p, ch3, ch2, noise) for p in candidates])
    scores = clf.predict_proba(X_cand)
    if scores.shape[1] < 2:
        return None
    pos_scores = scores[:, 1]
    scored = sorted(zip(candidates, pos_scores), key=lambda x: -x[1])
    if ref_spacing is not None:
        best_set = match_is_pattern(scored, n_expected, ref_spacing, tol)
        if not best_set:
            return None
        return [int(s) for s in best_set]
    else:
        # Just take top N scorer peaks
        return [int(s) for s,_ in scored[:n_expected]]

def main():
    import joblib

    model_path = os.path.join(SCRIPT_DIR, 'is_model.pkl')
    meta_path = model_path.replace('.pkl', '_meta.json')
    peaks_csv_path = model_path.replace('.pkl', '_peaks.csv')

    if not os.path.exists(model_path):
        print(f"ERROR: No saved model at {model_path}")
        sys.exit(1)

    clf = joblib.load(model_path)
    with open(meta_path) as f:
        meta = json.load(f)

    n_expected = meta.get('n_expected', 4)
    print(f"Loaded model: n_expected={n_expected}, meta={meta}")

    oy_folders = sorted(d for d in os.listdir(OY_DIR)
                        if os.path.isdir(os.path.join(OY_DIR, d)))
    print(f"Found {len(oy_folders)} folders in OY/")

    # Determine prefix from command line or auto-detect
    prefix = None
    for arg in sys.argv[1:]:
        if arg.startswith('--prefix='):
            prefix = arg.split('=', 1)[1]
    if not prefix and oy_folders:
        first = oy_folders[0]
        parts = first.split('_')
        prefix = '_'.join(parts[:4]) if first.startswith('OY_') and len(parts)>=4 else first.split('_Run')[0]
    print(f"Using prefix: {prefix}")

    # Filter folders by prefix
    matching = [f for f in oy_folders if f.startswith(prefix)]
    print(f"Matching folders: {len(matching)}")
    if not matching:
        print("ERROR: No matching folders!")
        sys.exit(1)

    # Step 1: Compute correct ref_spacing from a few wells in the matching folders
    print("\n--- Step 1: Computing IS peak spacing ---")
    all_diffs = []
    for folder_name in matching[:5]:  # First 5 folders
        folder_path = os.path.join(OY_DIR, folder_name)
        rsd_files = sorted(glob.glob(os.path.join(folder_path, '*.rsd')))[:4]  # 4 wells each
        for rsd_path in rsd_files:
            well = os.path.splitext(os.path.basename(rsd_path))[0]
            try:
                result = analyze_well(clf, rsd_path, n_expected, ref_spacing=None)
                if result and len(result) >= n_expected:
                    diffs = np.diff(sorted(result)[:n_expected])
                    all_diffs.extend(diffs.tolist())
            except Exception:
                continue
        print(f"  {folder_name}: {len(rsd_files)} wells, {len(all_diffs)} diffs so far")

    if not all_diffs:
        print("WARNING: Could not compute IS peak spacing. Using [50]")
        new_ref_spacing = [50]
    else:
        median_spacing = float(np.median(all_diffs))
        new_ref_spacing = [median_spacing] * (n_expected - 1)
        print(f"  Computed ref_spacing (n={len(all_diffs)} diffs): {new_ref_spacing}")
        print(f"  Range: {min(all_diffs):.1f} - {max(all_diffs):.1f}, median={median_spacing:.1f}")

    # Step 2: Run batch IS on ALL matching folders
    print(f"\n--- Step 2: Batch IS on {len(matching)} folders ---")
    all_results = {}
    total_wells = 0
    found_wells = 0
    for folder_name in matching:
        folder_path = os.path.join(OY_DIR, folder_name)
        rsd_files = sorted(glob.glob(os.path.join(folder_path, '*.rsd')))
        folder_results = {}
        for rsd_path in rsd_files:
            well = os.path.splitext(os.path.basename(rsd_path))[0]
            total_wells += 1
            try:
                result = analyze_well(clf, rsd_path, n_expected, new_ref_spacing, tol=30)
                if result:
                    folder_results[well] = result
                    found_wells += 1
            except Exception:
                continue
        if folder_results:
            all_results[folder_name] = folder_results
        sys.stdout.write(f"\r  {folder_name}: {len(folder_results)}/{len(rsd_files)} wells")
        sys.stdout.flush()
    print(f"\n  Total: {found_wells}/{total_wells} wells with IS peaks")

    # Save batch IS results
    out_path = os.path.join(SCRIPT_DIR, f'is_peaks_{prefix}.csv')
    rows = []
    for folder_name in sorted(all_results):
        for well in sorted(all_results[folder_name]):
            scans = all_results[folder_name][well]
            for i, s in enumerate(scans):
                rows.append({'folder': folder_name, 'well': well, f'is_peak_{i+1}_scan': s})
    if rows:
        pd.DataFrame(rows).to_csv(out_path, index=False)
        print(f"  Saved: {out_path} ({len(rows)} rows)")

    # Save to model peaks CSV too
    all_peaks_rows = []
    for folder_name in sorted(all_results):
        for well in sorted(all_results[folder_name]):
            scans = all_results[folder_name][well]
            row = {'folder': folder_name, 'well': well}
            for i, s in enumerate(scans):
                row[f'is_peak_{i+1}_scan'] = s
            all_peaks_rows.append(row)
    if all_peaks_rows:
        pd.DataFrame(all_peaks_rows).to_csv(peaks_csv_path, index=False)
        print(f"  Peak data: {peaks_csv_path} ({len(all_peaks_rows)} wells)")

    # Update meta
    meta['ref_spacing'] = new_ref_spacing
    meta['folders'] = sorted(all_results.keys())
    meta['n_total_wells'] = len(all_peaks_rows)
    with open(meta_path, 'w') as f:
        json.dump(meta, f, indent=2)
    print(f"  Meta: {meta_path}")

    # Step 3: Batch genotyping
    gmodel_path = os.path.join(SCRIPT_DIR, 'genotyping_model.pkl')
    gfeat_path = gmodel_path.replace('.pkl', '_features.csv')
    if not os.path.exists(gmodel_path):
        print(f"\n--- Step 3: Genotyping SKIPPED (model not found at {gmodel_path}) ---")
        print("  Train with: python3 train_genotyping.py")
        return

    print(f"\n--- Step 3: Batch genotyping ---")
    gen_model = joblib.load(gmodel_path)
    ref_features = pd.read_csv(gfeat_path)['feature'].tolist()
    from train_genotyping import extract_features_from_trace, LABEL_UNMAP

    geno_results = []
    for folder_name in sorted(all_results):
        folder_path = os.path.join(OY_DIR, folder_name)
        for well in sorted(all_results[folder_name]):
            is_scans = all_results[folder_name][well]
            rsd_path = os.path.join(folder_path, f"{well}.rsd")
            if not os.path.exists(rsd_path):
                continue
            try:
                df = parse_rsd(rsd_path)
                if len(df) < 50:
                    continue
                isp = [(s, float(df['Channel3'].values[s])) for s in is_scans if s < len(df)]
                feats = extract_features_from_trace(df, is_peaks=isp)
                row_vec = [feats.get(f, 0.0) for f in ref_features]
                X = np.array([row_vec])
                y_prob = gen_model.predict_proba(X)
                y_pred = gen_model.predict(X)
                pred_orig = LABEL_UNMAP.get(int(y_pred[0]), int(y_pred[0]))
                conf = float(np.max(y_prob[0]))
                geno_results.append({
                    'folder': folder_name, 'well': well,
                    'prediction': pred_orig, 'confidence': round(conf, 3),
                })
            except Exception:
                continue
        print(f"  {folder_name}: {sum(1 for g in geno_results if g['folder']==folder_name)} wells predicted")

    if geno_results:
        geno_df = pd.DataFrame(geno_results)
        geno_out = os.path.join(SCRIPT_DIR, f'genotypes_{prefix}.csv')
        geno_df.to_csv(geno_out, index=False)
        counts = geno_df['prediction'].value_counts().to_dict()
        print(f"\n  Saved: {geno_out} ({len(geno_df)} wells)")
        print(f"  Predictions: {counts}")
    else:
        print("  No genotyping results.")

if __name__ == '__main__':
    main()
