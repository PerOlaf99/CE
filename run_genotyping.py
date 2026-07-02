#!/usr/bin/env python3
"""Run genotyping only, using existing IS peak CSV. Faster than full pipeline."""

import os, sys, json, glob, struct, warnings
import numpy as np
import pandas as pd
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

def main():
    import joblib
    from train_genotyping import extract_features_from_trace, LABEL_UNMAP

    prefix = None
    for arg in sys.argv[1:]:
        if arg.startswith('--prefix='):
            prefix = arg.split('=', 1)[1]
    if not prefix:
        print("Usage: run_genotyping.py --prefix=OY_ABCC2")
        sys.exit(1)

    gmodel_path = os.path.join(SCRIPT_DIR, 'genotyping_model.pkl')
    gfeat_path = gmodel_path.replace('.pkl', '_features.csv')
    if not os.path.exists(gmodel_path):
        print(f"ERROR: {gmodel_path} not found")
        sys.exit(1)
    gen_model = joblib.load(gmodel_path)
    ref_features = pd.read_csv(gfeat_path)['feature'].tolist()

    # Load IS peaks
    is_csv = os.path.join(SCRIPT_DIR, f'is_peaks_{prefix}.csv')
    if not os.path.exists(is_csv):
        print(f"ERROR: {is_csv} not found")
        sys.exit(1)
    is_df = pd.read_csv(is_csv)
    is_cols = [c for c in is_df.columns if c.endswith('_scan')]

    # Group IS peaks by (folder, well)
    is_by_well = {}
    for _, row in is_df.iterrows():
        key = (row['folder'], row['well'])
        scans = sorted(int(row[c]) for c in is_cols if pd.notna(row[c]))
        if scans:
            is_by_well.setdefault(key, []).extend(scans)

    print(f"Loaded IS peaks for {len(is_by_well)} wells from {is_csv}")

    oy_folders = sorted(d for d in os.listdir(OY_DIR)
                        if os.path.isdir(os.path.join(OY_DIR, d)) and d.startswith(prefix))
    print(f"Matching folders: {len(oy_folders)}")

    results = []
    for folder_name in oy_folders:
        folder_path = os.path.join(OY_DIR, folder_name)
        rsd_files = sorted(glob.glob(os.path.join(folder_path, '*.rsd')))
        folder_wells = 0
        for rsd_path in rsd_files:
            well = os.path.splitext(os.path.basename(rsd_path))[0]
            key = (folder_name, well)
            scans = is_by_well.get(key, [])
            if not scans:
                continue
            try:
                df = parse_rsd(rsd_path)
                if len(df) < 50:
                    continue
                isp = [(s, float(df['Channel3'].values[s])) for s in scans if s < len(df)]
                feats = extract_features_from_trace(df, is_peaks=isp)
                row_vec = [feats.get(f, 0.0) for f in ref_features]
                X = np.array([row_vec])
                y_prob = gen_model.predict_proba(X)
                y_pred = gen_model.predict(X)
                pred_orig = LABEL_UNMAP.get(int(y_pred[0]), int(y_pred[0]))
                conf = float(np.max(y_prob[0]))
                results.append({
                    'folder': folder_name, 'well': well,
                    'prediction': pred_orig, 'confidence': round(conf, 3),
                })
                folder_wells += 1
            except Exception:
                continue
        print(f"  {folder_name}: {folder_wells}/{len(rsd_files)} wells")

    if results:
        out_path = os.path.join(SCRIPT_DIR, f'genotypes_{prefix}.csv')
        pd.DataFrame(results).to_csv(out_path, index=False)
        counts = pd.DataFrame(results)['prediction'].value_counts().to_dict()
        print(f"\nSaved: {out_path} ({len(results)} wells)")
        print(f"Predictions: {counts}")
    else:
        print("No results generated.")

if __name__ == '__main__':
    main()
