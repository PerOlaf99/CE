#!/usr/bin/env python3
"""Batch IS detection + genotyping using inter-well consistency for IS peaks.

Usage:
  ./env/bin/python3 run_is_genotyping.py --prefix=OY_ABCC2
  ./env/bin/python3 run_is_genotyping.py --prefix=OY_ABCC2 --min-clusters=4 --max-clusters=8
  ./env/bin/python3 run_is_genotyping.py --prefix=OY_ABCC2 --skip-genotyping
"""

import os, sys, glob, warnings, struct, json
import numpy as np
import pandas as pd
from scipy.signal import find_peaks
from itertools import combinations

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


def get_ch3_peaks(ch3, min_height_factor=5):
    noise = np.std(ch3[:200]) if len(ch3) > 200 else max(np.std(ch3), 1.0)
    candidates, _ = find_peaks(ch3, height=noise * min_height_factor, distance=5, width=1)
    return candidates, noise


def find_consistent_is_refs(folder_path, n_expected=4, min_well_frac=0.5,
                            max_std=10.0, match_tol=50,
                            min_scan=500):
    """Find IS reference positions using inter-well peak consistency + pattern matching.

    Steps:
    1. Find all consistent Ch3 peaks across wells
    2. Score each candidate by IS quality (Ch3 - 0.35*Ch2)
    3. Use pattern matching to find best 4 peaks matching size-standard elution pattern

    Returns list of (position, score) tuples sorted by scan position,
    or None if not enough peaks found.
    """
    rsd_files = sorted(glob.glob(os.path.join(folder_path, '*.rsd')))
    if not rsd_files:
        return None

    # Pre-parse all wells and cache Ch3 peaks
    all_peaks = []  # list of list of scan positions per well
    all_ch3 = []
    all_ch1 = []
    all_ch2 = []

    for rf in rsd_files:
        df = parse_rsd(rf)
        c3 = df['Channel3'].values.astype(float)
        c1 = df['Channel1'].values.astype(float)
        c2 = df['Channel2'].values.astype(float)
        nz = np.std(c3[:200]) if len(c3) > 200 else max(np.std(c3), 1.0)
        cand, _ = find_peaks(c3, height=nz * 5, distance=5, width=1)
        all_peaks.append(cand)
        all_ch3.append(c3)
        all_ch1.append(c1)
        all_ch2.append(c2)

    ch3_ref = all_ch3[0]
    ch1_ref = all_ch1[0]
    ch2_ref = all_ch2[0]
    cand_ref = all_peaks[0]

    if len(cand_ref) < 4:
        return None

    # Filter out injection peaks (early scans)
    mask = cand_ref >= min_scan
    cand_ref = cand_ref[mask]
    if len(cand_ref) < n_expected:
        return None

    # Sort candidates by height, take top 40
    heights = ch3_ref[cand_ref]
    top_candidates = [int(cand_ref[i]) for i in np.argsort(heights)[-40:]]

    # Check each candidate's consistency across all wells (using cached peaks)
    n_wells = len(rsd_files)
    min_matches = max(4, int(n_wells * min_well_frac))
    candidates = []  # (score, position, quality)

    for rp in top_candidates:
        matches = []
        for well_idx, cand in enumerate(all_peaks):
            if len(cand) == 0:
                continue
            nearest = cand[np.argmin(np.abs(cand - rp))]
            if abs(nearest - rp) <= match_tol:
                matches.append(nearest)
        if len(matches) >= min_matches:
            std = float(np.std(matches))
            if std <= max_std:
                mean_pos = float(np.mean(matches))
                quality = compute_is_quality(ch3_ref, ch1_ref, ch2_ref, mean_pos)
                if quality > 0:
                    score = quality / max(std, 0.1)
                    candidates.append((score, mean_pos, quality))

    if len(candidates) < n_expected:
        return None

    # Try pattern matching to find best 4 peaks matching size-standard pattern
    result = pattern_match_is_refs(candidates, n_expected=n_expected)
    if result:
        return result

    # Fallback: use farthest-spread from best-scored candidates
    candidates.sort(key=lambda x: -x[0])
    pool = [(c[1], c[0]) for c in candidates]  # (position, score)
    selected = [pool[0]]
    remaining = pool[1:]
    while len(selected) < n_expected and remaining:
        best = None
        best_val = -1e9
        best_idx = -1
        for i, (pos, sc) in enumerate(remaining):
            min_dist = min(abs(pos - s[0]) for s in selected)
            val = min_dist * sc
            if val > best_val:
                best_val = val
                best = (pos, sc)
                best_idx = i
        if best is None or best_val < 100:
            break
        selected.append(best)
        remaining.pop(best_idx)

    if len(selected) >= max(2, n_expected - 1):
        selected.sort(key=lambda x: x[0])
        return [(int(round(p)), 0) for p, _ in selected]
    return None


def compute_is_quality(ch3, ch1, ch2, pos, half_window=2):
    """Compute IS quality at given scan position.
    
    Returns the mean Ch3 signal at the peak. IS peaks have high Ch3
    (the electropherogram's nominal size-standard dye channel).
    Ch2 bleed-through into Ch3 is negligible (~2.7% based on empirical
    measurement of strong Ch2 fragment peaks with weak Ch3).
    """
    i = int(round(pos))
    c3 = np.mean(ch3[max(0,i-half_window):min(len(ch3),i+half_window+1)])
    return float(c3)


def score_peak_set(positions, qualities):
    """Score a set of IS peak candidates by quality, spread, and evenness.

    Higher score = better IS set.
    """
    positions = np.array(sorted(positions))
    n = len(positions)
    if n < 3:
        return -1e9
    span = positions[-1] - positions[0]
    if span < 150:
        return -1e9

    # Penalize any pair of peaks closer than 10 scans (same IS peak duplicated)
    # ABCC2 refs 2728/2741 are only 13 scans apart so threshold must be <13
    spacings = np.diff(positions)
    min_spacing = np.min(spacings)
    if min_spacing < 10:
        return -1e9

    total_quality = sum(qualities[p] for p in positions if p in qualities)

    # Evenness: prefer equally-spaced peaks (size standard is log-linear)
    evenness = 1.0 / (1.0 + np.std(spacings) / max(np.mean(spacings), 1.0))

    # Coverage: prefer wide span
    coverage = span / 3000.0

    return total_quality * coverage * evenness


def pattern_match_is_refs(candidates, n_expected=4, min_peaks=3):
    """Find best set of IS peaks by combinatorial search.

    Scores all 4-peak combinations by quality × spread × evenness.

    Returns list of (position, 0) tuples sorted by scan position, or None.
    """
    if not candidates or len(candidates) < min_peaks:
        return None

    # Sort by scan position
    candidates_sorted = sorted(candidates, key=lambda x: x[1])
    positions = [c[1] for c in candidates_sorted]
    qualities = {c[1]: c[0] for c in candidates}  # position -> score

    best_set = None
    best_score = -1e9

    # Try all 4-peak combinations (or n_expected)
    n = len(positions)
    from itertools import combinations
    for combo in combinations(range(n), n_expected):
        combo_pos = [positions[i] for i in combo]
        score = score_peak_set(combo_pos, qualities)
        if score > best_score:
            best_score = score
            best_set = combo_pos

    if best_score > -1e8:
        return [(int(round(p)), 0) for p in sorted(best_set)]
    return None


def has_amplification(rsd_path, ref_positions, max_dist=30):
    """Check if well has real PCR product: Ch1/Ch2 peaks aligned just before IS.
    
    For each IS ref, scans a window [ref-max_dist, ref-1] looking for ANY
    Ch1 or Ch2 peak above a moderate threshold. This avoids missing valid
    amplification peaks that are dwarfed by taller fragment signals elsewhere.
    """
    df = parse_rsd(rsd_path)
    for ch_name in ['Channel1', 'Channel2']:
        vals = df[ch_name].values.astype(float)
        noise = np.std(vals[:200]) if len(vals) > 200 else max(np.std(vals), 1.0)
        cand, _ = find_peaks(vals, height=noise * 3, distance=5, width=1)
        if len(cand) < 2:
            continue
        cand_set = set(cand)
        for rp in ref_positions:
            window_start = max(0, int(rp) - max_dist)
            window_end = max(0, int(rp) - 1)
            if window_end <= window_start:
                continue
            # Check if any detected peak falls in the window before this ref
            for cp in cand:
                if window_start <= cp <= window_end:
                    return True
    return False


def find_is_peaks_for_well(rsd_path, ref_positions, match_tol=50):
    """Find IS peaks in a well by matching reference positions."""
    df = parse_rsd(rsd_path)
    c3 = df['Channel3'].values.astype(float)
    noise = np.std(c3[:200]) if len(c3) > 200 else max(np.std(c3), 1.0)
    cand, _ = find_peaks(c3, height=noise * 3, distance=3, width=1)
    if len(cand) == 0:
        return None
    result = []
    for rp in ref_positions:
        diffs = np.abs(cand - rp)
        nearest = cand[np.argmin(diffs)]
        if abs(nearest - rp) <= match_tol:
            result.append((int(nearest), float(c3[nearest])))
        else:
            result.append(None)
    n_found = sum(1 for r in result if r is not None)
    if n_found < max(2, len(ref_positions) - 1):
        return None
    return result


def main():
    from train_genotyping import extract_features_from_trace, LABEL_UNMAP

    prefix = None
    skip_geno = False
    min_clusters = 4
    max_clusters = 8
    ref_positions_arg = None

    for arg in sys.argv[1:]:
        if arg.startswith('--prefix='):
            prefix = arg.split('=', 1)[1]
        elif arg == '--skip-genotyping':
            skip_geno = True
        elif arg.startswith('--min-clusters='):
            min_clusters = int(arg.split('=', 1)[1])
        elif arg.startswith('--max-clusters='):
            max_clusters = int(arg.split('=', 1)[1])
        elif arg.startswith('--ref-positions='):
            ref_positions_arg = [int(x) for x in arg.split('=', 1)[1].split(',')]

    if not prefix:
        print("Usage: run_is_genotyping.py --prefix=OY_ABCC2 [--ref-positions=2438,2510,2728,2741] [--skip-genotyping]")
        sys.exit(1)

    # Load reference positions from JSON if available (gene-specific manual refs)
    refs_json_path = os.path.join(SCRIPT_DIR, 'is_ref_positions.json')
    gene_name = prefix.replace('OY_', '').rstrip('_')
    if ref_positions_arg:
        manual_refs = ref_positions_arg
        print(f"Using command-line IS ref positions: {manual_refs}")
    elif os.path.exists(refs_json_path):
        import json as _json
        with open(refs_json_path) as _f:
            _all_refs = _json.load(_f)
        # Try exact gene name, or any key contained in prefix
        manual_refs = None
        for key in sorted(_all_refs.keys(), key=len, reverse=True):
            if key in prefix or prefix in key:
                manual_refs = _all_refs[key]
                break
        if manual_refs:
            print(f"Using saved IS ref positions from is_ref_positions.json ({gene_name}): {manual_refs}")
        else:
            manual_refs = None
    else:
        manual_refs = None

    # Find matching folders
    oy_folders = sorted(d for d in os.listdir(OY_DIR)
                        if os.path.isdir(os.path.join(OY_DIR, d)) and d.startswith(prefix))
    print(f"Found {len(oy_folders)} folders matching '{prefix}'")
    if not oy_folders:
        sys.exit(1)

    if manual_refs:
        print(f"\n--- Step 1: Finding IS peaks using saved manual reference ---")
    else:
        print(f"\n--- Step 1: Finding IS peaks (inter-well consistency) ---")

    all_is_peaks = {}
    failed_folders = []

    for folder_name in oy_folders:
        folder_path = os.path.join(OY_DIR, folder_name)

        if manual_refs:
            ref_positions = manual_refs
            print(f"  {folder_name}: Using manual refs={ref_positions}")
        else:
            refs = find_consistent_is_refs(folder_path, n_expected=min_clusters)
            if refs is None:
                print(f"  {folder_name}: SKIP (could not find {min_clusters} consistent peaks)")
                failed_folders.append(folder_name)
                continue
            ref_positions = [r[0] for r in refs]
            print(f"  {folder_name}: IS refs={ref_positions}")

        rsd_files = sorted(glob.glob(os.path.join(folder_path, '*.rsd')))
        folder_peaks = {}
        for rsd_path in rsd_files:
            well = os.path.splitext(os.path.basename(rsd_path))[0]
            res = find_is_peaks_for_well(rsd_path, ref_positions)
            if res:
                folder_peaks[well] = [r[0] if r else None for r in res]
            else:
                folder_peaks[well] = None

        n_with_is = sum(1 for v in folder_peaks.values() if v is not None)
        print(f"           IS found: {n_with_is}/{len(rsd_files)} wells")
        if folder_peaks:
            all_is_peaks[folder_name] = {'refs': ref_positions, 'wells': folder_peaks}

    # Save IS peaks CSV
    is_rows = []
    for folder_name in sorted(all_is_peaks):
        wells = all_is_peaks[folder_name]['wells']
        for well in sorted(wells):
            peaks = wells[well]
            if peaks:
                for i, s in enumerate(peaks):
                    if s is not None:
                        is_rows.append({'folder': folder_name, 'well': well,
                                        f'is_peak_{i+1}_scan': s})
    if is_rows:
        is_csv = os.path.join(SCRIPT_DIR, f'is_peaks_{prefix}.csv')
        pd.DataFrame(is_rows).to_csv(is_csv, index=False)
        print(f"\n  Saved: {is_csv} ({len(is_rows)} peaks)")
    else:
        print("\n  No IS peaks found. Exiting.")
        sys.exit(1)

    if skip_geno:
        print("\nSkipping genotyping (--skip-genotyping)")
        sys.exit(0)

    # Step 2: Genotyping with per-plate normalization
    print(f"\n--- Step 2: Genotyping {prefix} (per-plate normalized) ---")
    gen_model = None
    ref_features = None
    try:
        import joblib
        gen_model = joblib.load(os.path.join(SCRIPT_DIR, 'genotyping_model.pkl'))
        ref_features = pd.read_csv(os.path.join(SCRIPT_DIR, 'genotyping_model_features.csv'))['feature'].tolist()
    except Exception as e:
        print(f"  Error loading genotyping model: {e}")
        sys.exit(1)

    geno_results = []
    skipped_no_is = 0
    skipped_no_amp = 0
    for folder_name in sorted(all_is_peaks):
        folder_info = all_is_peaks[folder_name]
        folder_path = os.path.join(OY_DIR, folder_name)
        ref_positions = folder_info['refs']
        wells = folder_info['wells']

        # Pass 1: extract features for all wells in this folder
        well_features = {}  # well -> (feature vector, raw_feats dict)
        for well in sorted(wells):
            peaks = wells[well]
            if peaks is None or sum(1 for p in peaks if p is not None) < 2:
                skipped_no_is += 1
                continue
            rsd_path = os.path.join(folder_path, f"{well}.rsd")
            if not os.path.exists(rsd_path):
                continue
            if not has_amplification(rsd_path, ref_positions):
                skipped_no_amp += 1
                geno_results.append({
                    'folder': folder_name, 'well': well,
                    'prediction': 'FAIL', 'confidence': 0.0,
                    'prob_fail': 1.0, 'prob_hom1': 0.0,
                    'prob_hom2': 0.0, 'prob_het': 0.0,
                })
                continue
            try:
                df = parse_rsd(rsd_path)
                if len(df) < 50:
                    continue
                ch3 = df['Channel3'].values.astype(float)
                ispk = [(float(s), float(ch3[int(s)])) for s in peaks if s is not None and int(s) < len(ch3)]
                feats = extract_features_from_trace(df, is_peaks=ispk)
                row_vec = np.array([feats.get(f, 0.0) for f in ref_features])
                well_features[well] = (row_vec, feats)
            except Exception:
                continue

        if not well_features:
            continue

        # Compute per-plate median + IQR for normalization
        feat_matrix = np.array([wf[0] for wf in well_features.values()])
        median = np.median(feat_matrix, axis=0)
        p75 = np.percentile(feat_matrix, 75, axis=0)
        p25 = np.percentile(feat_matrix, 25, axis=0)
        iqr = np.maximum(p75 - p25, 1e-8)

        # Pass 2: normalize and predict
        for well, (row_vec, feats) in sorted(well_features.items()):
            try:
                X_norm = (row_vec.reshape(1, -1) - median) / iqr
                y_prob = gen_model.predict_proba(X_norm)
                y_pred = gen_model.predict(X_norm)
                pred_orig = LABEL_UNMAP.get(int(y_pred[0]), int(y_pred[0]))
                conf = float(np.max(y_prob[0]))
                prob_map = dict(zip(gen_model.classes_, y_prob[0]))
                result = {
                    'folder': folder_name, 'well': well,
                    'prediction': pred_orig, 'confidence': round(conf, 3),
                    'prob_fail': round(float(prob_map.get(0, 0)), 4),
                    'prob_hom1': round(float(prob_map.get(1, 0)), 4),
                    'prob_hom2': round(float(prob_map.get(2, 0)), 4),
                    'prob_het': round(float(prob_map.get(4, 0)), 4),
                }
                for fname in ('Ch1_mean', 'Ch2_mean', 'Ch3_mean', 'Ch1_max',
                              'Ch2_max', 'Ch3_max', 'Ch1_peak_n_peaks',
                              'Ch2_peak_n_peaks', 'Ch3_peak_n_peaks',
                              'Ch4_peak_n_peaks', 'IS_spread'):
                    if fname in feats:
                        result[f'raw_{fname}'] = round(float(feats[fname]), 2)
                geno_results.append(result)
            except Exception:
                continue

    if geno_results:
        out_path = os.path.join(SCRIPT_DIR, f'genotypes_{prefix}.csv')
        detail_path = os.path.join(SCRIPT_DIR, f'genotypes_{prefix}_detail.csv')
        df_out = pd.DataFrame(geno_results)
        df_out.to_csv(out_path, index=False)
        df_out.to_csv(detail_path, index=False)
        counts = df_out['prediction'].value_counts()
        print(f"\n  Saved: {out_path} ({len(geno_results)} wells)")
        print(f"  Saved: {detail_path} (with per-class probabilities + raw features)")
        print(f"  Skipped (no IS): {skipped_no_is}, Skipped (no amp): {skipped_no_amp}")
        for k, v in counts.items():
            names = {0: 'fail', 1: 'hom1', 2: 'hom2', 4: 'het'}
            print(f"    {names.get(k, k)}: {v}")
    else:
        print("  No genotyping results.")


if __name__ == '__main__':
    main()
