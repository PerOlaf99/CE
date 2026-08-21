import warnings, os, sys, glob, re
import numpy as np
import pandas as pd
from scipy.stats import skew, kurtosis
from scipy.signal import find_peaks
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.metrics import classification_report, confusion_matrix
import joblib

SCRIPT_DIR = os.path.dirname(__file__) or '.'

LABEL_MAP = {'fail': 0, 'hom1': 1, 'hom2': 2, 'het': 4}
LABEL_UNMAP = {v: k for k, v in LABEL_MAP.items()}

ch_names = ['Channel1', 'Channel2', 'Channel3', 'Channel4', 'Current']

def extract_features_from_trace(df, is_peaks=None):
    ch_names = ['Channel1', 'Channel2', 'Channel3', 'Channel4', 'Current']
    features = {}
    n_scans = len(df)

    for ch in ch_names:
        y = df[ch].values.astype(float)
        features[f'{ch}_mean'] = float(np.mean(y))
        features[f'{ch}_std'] = float(np.std(y))
        features[f'{ch}_max'] = float(np.max(y))
        features[f'{ch}_min'] = float(np.min(y))
        features[f'{ch}_median'] = float(np.median(y))
        features[f'{ch}_p25'] = float(np.percentile(y, 25))
        features[f'{ch}_p75'] = float(np.percentile(y, 75))
        features[f'{ch}_skew'] = float(skew(y))
        features[f'{ch}_kurtosis'] = float(kurtosis(y))
        features[f'{ch}_energy'] = float(np.sum(y ** 2))

        noise_std = np.std(y[:200]) if len(y) > 200 else np.std(y)
        threshold = max(50, 3 * noise_std)
        peaks, props = find_peaks(y, height=threshold, prominence=threshold * 0.5,
                                  distance=5, width=1)
        features[f'{ch}_n_peaks'] = len(peaks)
        if len(peaks) > 0:
            features[f'{ch}_peak_mean_height'] = float(np.mean(props['peak_heights']))
            features[f'{ch}_peak_max_height'] = float(np.max(props['peak_heights']))
            features[f'{ch}_peak_total_height'] = float(np.sum(props['peak_heights']))
            features[f'{ch}_peak_mean_prominence'] = float(np.mean(props['prominences']))
            features[f'{ch}_peak_mean_width'] = float(np.mean(props['widths']))
            features[f'{ch}_peak_first_scan'] = int(peaks[0])
            features[f'{ch}_peak_last_scan'] = int(peaks[-1])
            features[f'{ch}_peak_spread'] = int(peaks[-1] - peaks[0])
        else:
            for k in ['peak_mean_height', 'peak_max_height', 'peak_total_height',
                       'peak_mean_prominence', 'peak_mean_width']:
                features[f'{ch}_{k}'] = 0.0
            features[f'{ch}_peak_first_scan'] = 0
            features[f'{ch}_peak_last_scan'] = 0
            features[f'{ch}_peak_spread'] = 0

    region_start, region_end = 1500, min(2000, n_scans)
    region_len = region_end - region_start
    if region_len > 50:
        for ch in ch_names:
            y_region = df[ch].values[region_start:region_end].astype(float)
            prefix = f'{ch}_region'
            features[f'{prefix}_mean'] = float(np.mean(y_region))
            features[f'{prefix}_std'] = float(np.std(y_region))
            features[f'{prefix}_max'] = float(np.max(y_region))
            features[f'{prefix}_energy'] = float(np.sum(y_region ** 2))

            noise = np.std(y_region[:min(100, len(y_region))])
            threshold = max(20, 3 * noise)
            peaks, props = find_peaks(y_region, height=threshold,
                                      prominence=threshold * 0.5, distance=5, width=1)
            features[f'{prefix}_n_peaks'] = len(peaks)
            if len(peaks) > 0:
                features[f'{prefix}_mean_height'] = float(np.mean(props['peak_heights']))
                features[f'{prefix}_max_height'] = float(np.max(props['peak_heights']))
                features[f'{prefix}_mean_prominence'] = float(np.mean(props['prominences']))
                features[f'{prefix}_mean_width'] = float(np.mean(props['widths']))
            else:
                for k in ['mean_height', 'max_height', 'mean_prominence', 'mean_width']:
                    features[f'{prefix}_{k}'] = 0.0
    else:
        for ch in ch_names:
            for suffix in ['mean', 'std', 'max', 'energy']:
                features[f'{ch}_region_{suffix}'] = 0.0
            for suffix in ['n_peaks', 'mean_height', 'max_height', 'mean_prominence', 'mean_width']:
                features[f'{ch}_region_{suffix}'] = 0.0

    if region_len > 50:
        region_data = {ch: df[ch].values[region_start:region_end].astype(float)
                       for ch in ch_names}
        for i, ch1 in enumerate(ch_names):
            for ch2 in ch_names[i + 1:]:
                corr = np.corrcoef(region_data[ch1], region_data[ch2])[0, 1]
                features[f'corr_{ch1}_{ch2}'] = float(corr if not np.isnan(corr) else 0)

    for i, ch1 in enumerate(ch_names):
        for ch2 in ch_names[i + 1:]:
            y1 = df[ch1].values.astype(float)
            y2 = df[ch2].values.astype(float)
            corr = np.corrcoef(y1, y2)[0, 1]
            features[f'corr_full_{ch1}_{ch2}'] = float(corr if not np.isnan(corr) else 0)

    ch3 = df['Channel3'].values.astype(float)
    ch2 = df['Channel2'].values.astype(float)
    noise_ch3 = np.std(ch3[:200]) if len(ch3) > 200 else np.std(ch3)

    if is_peaks is not None:
        is_candidates = [(int(s), float(h), float(h / max(ch2[int(s)], 1)))
                         for s, h in is_peaks]
    else:
        is_peaks_raw = find_peaks(ch3, height=noise_ch3 * 10, prominence=noise_ch3 * 5,
                                  distance=15, width=3)[0]
        is_candidates = []
        for p in is_peaks_raw:
            c3, c2 = ch3[p], ch2[p]
            ratio = c3 / c2 if c2 > 10 else 999
            if ratio > 2.0 and c3 > noise_ch3 * 10:
                is_candidates.append((p, c3, ratio))

    features['IS_n_peaks'] = len(is_candidates)
    if is_candidates:
        scans = np.array([s for s, _, _ in is_candidates])
        heights = np.array([h for _, h, _ in is_candidates])
        features['IS_max_height'] = float(np.max(heights))
        features['IS_total_height'] = float(np.sum(heights))
        features['IS_mean_height'] = float(np.mean(heights))
        features['IS_first_scan'] = int(np.min(scans))
        features['IS_last_scan'] = int(np.max(scans))
        features['IS_spread'] = int(np.max(scans) - np.min(scans))

        # Sort by scan order for consistent feature ordering
        sorted_by_scan = sorted(is_candidates, key=lambda x: x[0])
        for i, (scan, height, _) in enumerate(sorted_by_scan[:4]):
            features[f'IS_peak_{i+1}_scan'] = scan
            features[f'IS_peak_{i+1}_height'] = height
        for i in range(len(sorted_by_scan[:4]), 4):
            features[f'IS_peak_{i+1}_scan'] = 0
            features[f'IS_peak_{i+1}_height'] = 0.0
    else:
        for k in ['IS_max_height', 'IS_total_height', 'IS_mean_height',
                   'IS_first_scan', 'IS_last_scan', 'IS_spread']:
            features[k] = 0.0
        for i in range(1, 5):
            features[f'IS_peak_{i}_scan'] = 0
            features[f'IS_peak_{i}_height'] = 0.0

    features['n_scans'] = n_scans
    return features


def normalize_plate_name(name):
    s = str(name).strip()
    s = re.sub(r'Run(\d)$', lambda m: f'Run0{m.group(1)}', s)
    return s


def parse_genotyping_xlsx(path):
    """Parse the Genotyping.xlsx file format.
    
    Structure: alternating plate header row then 12 well rows (01-12),
    each with 8 pairs of (well_name, genotype).
    """
    df = pd.read_excel(path, header=None)
    plates = {}
    i = 0
    while i < len(df):
        # Check if this row looks like a plate header (text, not a well name)
        val = df.iloc[i, 0]
        if pd.isna(val):
            i += 1
            continue
        val_str = str(val).strip()
        if re.match(r'^OY_', val_str):
            plate_name = normalize_plate_name(val_str)
            plate_data = {}
            for j in range(1, 13):
                if i + j >= len(df):
                    break
                row = df.iloc[i + j]
                for k in range(8):
                    well_col = 2 * k
                    geno_col = 2 * k + 1
                    well = row.iloc[well_col]
                    geno = row.iloc[geno_col]
                    if pd.notna(well) and pd.notna(geno):
                        try:
                            plate_data[str(well).strip()] = int(float(geno))
                        except (ValueError, TypeError):
                            pass
            if plate_data:
                plates[plate_name] = plate_data
            i += 13
        else:
            i += 1
    return plates


def main():
    from run_is_genotyping import parse_rsd, find_is_peaks_for_well
    
    OY_DIR = os.path.join(SCRIPT_DIR, 'OY')
    model_path = os.path.join(SCRIPT_DIR, 'genotyping_model.pkl')
    features_path = model_path.replace('.pkl', '_features.csv')

    # Load IS ref positions
    refs_json_path = os.path.join(SCRIPT_DIR, 'is_ref_positions.json')
    import json as _json
    if os.path.exists(refs_json_path):
        with open(refs_json_path) as _f:
            _all_refs = _json.load(_f)
    else:
        _all_refs = {}

    # Parse Genotyping.xlsx for ground truth
    xlsx_path = os.path.join(SCRIPT_DIR, 'Genotyping.xlsx')
    if not os.path.exists(xlsx_path):
        xlsx_path = '/media/tv/Data (ScanDisk)/Genotyping.xlsx'
    all_plates = parse_genotyping_xlsx(xlsx_path)
    print(f"Parsed {len(all_plates)} plates from Genotyping.xlsx")
    for pname, pdata in sorted(all_plates.items()):
        vals = list(pdata.values())
        print(f"  {pname}: {len(pdata)} wells, geno dist: {pd.Series(vals).value_counts().to_dict()}")

    # Extract features for every well in every plate
    # First pass: extract features from ALL wells per folder for normalization,
    # then labeled wells for training
    X_list, y_list, well_ids = [], [], []
    feature_cols = None
    plate_all_feats = {}  # pname -> list of feature rows (all wells in folder)
    plate_folder_map = {}  # pname -> folder_path
    plate_refs_map = {}    # pname -> ref_positions

    for plate_name in sorted(all_plates.keys()):
        # Find matching folder in OY/
        folder_path = None
        for d in os.listdir(OY_DIR):
            dpath = os.path.join(OY_DIR, d)
            if os.path.isdir(dpath) and normalize_plate_name(d) == plate_name:
                folder_path = dpath
                break
        if folder_path is None:
            prefix = plate_name.split('_Run')[0]
            for d in os.listdir(OY_DIR):
                if d.startswith(prefix) and os.path.isdir(os.path.join(OY_DIR, d)):
                    folder_path = os.path.join(OY_DIR, d)
                    break
        if folder_path is None:
            print(f"  Skipping {plate_name}: no matching OY folder")
            continue

        gene_key = None
        for key in sorted(_all_refs.keys(), key=len, reverse=True):
            if key in plate_name or plate_name in key:
                gene_key = key
                break
        ref_positions = _all_refs.get(gene_key) if gene_key else None
        if ref_positions is None:
            print(f"  Skipping {plate_name}: no IS ref positions for gene")
            continue

        plate_folder_map[plate_name] = folder_path
        plate_refs_map[plate_name] = ref_positions

        # Check for pre-exported IS peaks CSV (corrected by user in GUI)
        is_csv_path = os.path.join(SCRIPT_DIR, f'is_peaks_{plate_name}.csv')
        is_peaks_from_csv = {}
        if os.path.exists(is_csv_path):
            try:
                csv_df = pd.read_csv(is_csv_path)
                is_cols = [c for c in csv_df.columns if c.endswith('_scan')]
                for _, row in csv_df.iterrows():
                    well = str(row['well']).strip()
                    scans = []
                    for c in is_cols:
                        v = row.get(c)
                        if pd.notna(v):
                            try:
                                scans.append(int(float(v)))
                            except (ValueError, TypeError):
                                pass
                    if len(scans) >= 2:
                        is_peaks_from_csv[well] = sorted(scans)
                if is_peaks_from_csv:
                    print(f"    Loaded IS peaks from CSV for {len(is_peaks_from_csv)} wells")
            except Exception as e:
                print(f"    Error loading IS CSV {is_csv_path}: {e}")

        # Extract features for ALL .rsd files in this folder
        all_feats = []
        for fname in sorted(os.listdir(folder_path)):
            if not fname.endswith('.rsd'):
                continue
            well = fname[:-4]
            rsd_path = os.path.join(folder_path, fname)
            df = parse_rsd(rsd_path)
            if len(df) < 50:
                continue
            ch3 = df['Channel3'].values.astype(float)
            if well in is_peaks_from_csv:
                ispk = [(s, float(ch3[s])) for s in is_peaks_from_csv[well] if s < len(ch3)]
            else:
                res = find_is_peaks_for_well(rsd_path, ref_positions)
                if not res:
                    continue
                ispk = [(int(r[0]), float(ch3[int(r[0])])) for r in res if r]
            feats = extract_features_from_trace(df, is_peaks=ispk)
            if feature_cols is None:
                feature_cols = sorted([k for k in feats.keys() if k not in ('n_scans',)])
            row = [feats.get(f, 0.0) for f in feature_cols]
            all_feats.append((well, row))
        plate_all_feats[plate_name] = all_feats
        print(f"  {plate_name}: {len(all_feats)} total wells in folder")

    # Second pass: normalize per-plate (using ALL folder wells), then collect labeled
    print("\nNormalizing per-plate (using all wells per folder)...")
    for plate_name in sorted(plate_all_feats.keys()):
        all_feats = plate_all_feats[plate_name]
        if not all_feats:
            continue
        all_rows = np.array([r for _, r in all_feats])
        median = np.median(all_rows, axis=0)
        p75 = np.percentile(all_rows, 75, axis=0)
        p25 = np.percentile(all_rows, 25, axis=0)
        iqr = np.maximum(p75 - p25, 1e-8)

        plate_gt = all_plates[plate_name]
        n_ok = 0
        for well, row_vec in all_feats:
            if well not in plate_gt:
                continue
            gt_label = plate_gt[well]
            norm_row = (np.array(row_vec) - median) / iqr
            X_list.append(norm_row)
            y_list.append(gt_label)
            well_ids.append((plate_name, well))
            n_ok += 1
        print(f"  {plate_name}: {n_ok}/{len(plate_gt)} labeled wells in training set")

    if len(X_list) < 10:
        print(f"Only {len(X_list)} training samples — not enough to train.")
        return

    X = np.array(X_list)
    y = np.array(y_list)

    print(f"Training set: {len(X)} samples, {len(feature_cols)} features")
    print(f"Label distribution: {pd.Series(y).value_counts().to_dict()}")
    for lbl in sorted(set(y)):
        name = LABEL_UNMAP.get(lbl, lbl)
        print(f"  {name} ({lbl}): {(y == lbl).sum()}")

    # Train
    clf = RandomForestClassifier(n_estimators=300, max_depth=12, min_samples_leaf=3,
                                 class_weight='balanced', random_state=42, n_jobs=-1)
    clf.fit(X, y)

    # Cross-val score
    try:
        scores = cross_val_score(clf, X, y, cv=min(5, len(np.unique(y))))
        print(f"\nCross-val accuracy: {scores.mean():.3f} +/- {scores.std():.3f}")
    except Exception as e:
        print(f"Cross-val failed: {e}")

    # Feature importance
    importances = pd.Series(clf.feature_importances_, index=feature_cols).sort_values(ascending=False)
    print("\nTop 20 features:")
    print(importances.head(20).to_string())

    # Predict
    y_pred = clf.predict(X)
    print("\nPer-plate results:")
    for pname in sorted(all_plates.keys()):
        idxs = [i for i, (pn, w) in enumerate(well_ids) if pn == pname]
        if not idxs:
            continue
        y_true = y[idxs]
        y_p = y_pred[idxs]
        correct = (y_true == y_p).sum()
        print(f"  {pname}: {len(idxs)} wells, {correct}/{len(idxs)} correct")

    # Save model
    joblib.dump(clf, model_path)
    pd.DataFrame({'feature': feature_cols}).to_csv(features_path, index=False)
    print(f"\nModel saved to {model_path} ({len(feature_cols)} features)")


if __name__ == '__main__':
    main()
