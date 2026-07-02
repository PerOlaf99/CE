#!/usr/bin/env python3
"""Batch validate genotyping pipeline against Genotyping.xlsx reference.

For each plate in the Excel reference:
  1. Find matching folder with .rsd files
  2. Load manual IS refs from is_ref_positions.json (gene-specific)
  3. Find IS peaks using raw-trace argmax (same as gui.py predict_genotypes)
  4. Extract features, per-plate normalize, predict with model
  5. Compare to reference calls and report accuracy
"""

import os, sys, glob, warnings, json, struct
import numpy as np
import pandas as pd
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

# ── Parse Genotyping.xlsx ──────────────────────────────────────────────────

def parse_genotyping_xlsx(path):
    """Parse Genotyping.xlsx into dict of plate_name -> {well: call}."""
    df = pd.read_excel(path, sheet_name='Ark1', header=0)
    plates = {}
    current_plate = None
    for _, row in df.iterrows():
        vals = row.values
        if pd.isna(vals[0]):
            continue
        first = str(vals[0]).strip()
        # Check if this is a plate name header (contains OY_)
        if 'OY_' in first:
            current_plate = first
            plates[current_plate] = {}
            continue
        if current_plate is None:
            continue
        # Row of well->call pairs: [well1, call1, well2, call2, ...]
        for i in range(0, len(vals) - 1, 2):
            well = str(vals[i]).strip()
            call = vals[i + 1]
            if well and not pd.isna(call):
                plates[current_plate][well] = int(call)
    return plates

# ── Load manual IS refs ────────────────────────────────────────────────────

def load_manual_refs(prefix):
    """Load IS reference positions from is_ref_positions.json for this prefix."""
    refs_path = os.path.join(SCRIPT_DIR, 'is_ref_positions.json')
    if not os.path.exists(refs_path):
        return None
    with open(refs_path) as f:
        all_refs = json.load(f)
    for key in sorted(all_refs.keys(), key=len, reverse=True):
        if key in prefix or prefix in key:
            return all_refs[key]
    return None

# ── Find IS peaks (raw-trace argmax, same as gui.py) ──────────────────────

def find_is_peaks_raw_argmax(df, ref_positions, window=150, min_height_factor=5):
    """Find IS peaks using raw (unsmoothed) Ch3 argmax in windows around refs.
    
    Same logic as gui.py predict_genotypes() lines 3670-3711.
    Returns list of (position, height) sorted by scan, or empty list.
    """
    ch3 = df['Channel3'].values.astype(float)
    noise = np.std(ch3[:200]) if len(ch3) > 200 else max(np.std(ch3), 1e-10)
    min_is_height = max(100, min_height_factor * noise)
    pairs = []  # (distance, ref_idx, position, height)
    for ri, rp in enumerate(ref_positions):
        lo = max(0, int(rp) - window)
        hi = min(len(ch3), int(rp) + window)
        if hi - lo < 3:
            continue
        pos = lo + int(np.argmax(ch3[lo:hi]))
        h = float(ch3[pos])
        if h < min_is_height:
            continue
        pairs.append((abs(pos - rp), ri, pos, h))
    if not pairs:
        return []
    # Greedy: assign each peak to its closest ref, each used at most once
    pairs.sort(key=lambda x: x[0])
    assigned_peaks = set()
    assigned_refs = set()
    is_list = []
    for dist, ri, pos, h in pairs:
        if ri in assigned_refs or pos in assigned_peaks:
            continue
        assigned_refs.add(ri)
        assigned_peaks.add(pos)
        is_list.append((pos, h))
    return sorted(is_list, key=lambda x: x[0])

# ── Main validation loop ───────────────────────────────────────────────────

def normalize_run_name(name):
    """Normalize Run1→Run01, Run2→Run02 etc for consistent matching."""
    import re
    def _fix_run(m):
        num = int(m.group(1))
        return f'Run{num:02d}'
    return re.sub(r'Run(\d+)$', _fix_run, name)

def find_best_folder(plate_name):
    """Find the best matching folder for a plate name, with Run numbering normalization."""
    candidates = []
    # Try exact match first
    for d in os.listdir(OY_DIR):
        dp = os.path.join(OY_DIR, d)
        if not os.path.isdir(dp):
            continue
        if d == plate_name:
            return dp  # exact match, return immediately
        if d == normalize_run_name(plate_name):
            candidates.insert(0, dp)  # normalized match, prefer
        elif d.startswith(normalize_run_name(plate_name)):
            candidates.append(dp)
        elif normalize_run_name(d) == normalize_run_name(plate_name):
            candidates.insert(0, dp)
    if not candidates:
        # Fuzzy: check if any folder contains the plate name or vice versa
        norm_plate = normalize_run_name(plate_name)
        for d in os.listdir(OY_DIR):
            dp = os.path.join(OY_DIR, d)
            if not os.path.isdir(dp):
                continue
            norm_d = normalize_run_name(d)
            if norm_plate in norm_d or norm_d in norm_plate:
                candidates.append(dp)
    return candidates[0] if candidates else None


def get_is_refs_for_folder(folder_path, plate_name):
    """Get IS refs for a folder: try inter-well consistency first, fall back to gene-wide manual refs."""
    from run_is_genotyping import find_consistent_is_refs as find_refs
    refs_result = find_refs(folder_path, n_expected=4, min_well_frac=0.3)
    if refs_result:
        refs = [r[0] for r in refs_result]
        return refs
    manual = load_manual_refs(plate_name)
    if manual:
        return manual
    return None


def main():
    from train_genotyping import extract_features_from_trace, LABEL_UNMAP
    import joblib

    # Load model and feature template
    model_path = os.path.join(SCRIPT_DIR, 'genotyping_model.pkl')
    features_path = os.path.join(SCRIPT_DIR, 'genotyping_model_features.csv')
    if not os.path.exists(model_path) or not os.path.exists(features_path):
        print(f"Error: model or features file not found in {SCRIPT_DIR}")
        sys.exit(1)
    model = joblib.load(model_path)
    ref_features = pd.read_csv(features_path)['feature'].tolist()
    print(f"Loaded model: {model_path}")
    print(f"Feature template: {len(ref_features)} features\n")

    # Parse reference calls
    xlsx_path = os.path.join(SCRIPT_DIR, 'Genotyping.xlsx')
    ref_plates = parse_genotyping_xlsx(xlsx_path)
    print(f"Parsed {len(ref_plates)} plates from Genotyping.xlsx:\n")
    for pname in sorted(ref_plates):
        n_wells = len(ref_plates[pname])
        print(f"  {pname}: {n_wells} wells")

    # For each plate, try to find matching folder and run pipeline
    all_results = []  # list of dicts per well
    for plate_name in sorted(ref_plates):
        ref_calls = ref_plates[plate_name]
        print(f"\n{'='*70}")
        print(f"PLATE: {plate_name} ({len(ref_calls)} ref wells)")

        # Find matching folder
        folder_path = find_best_folder(plate_name)
        if not folder_path:
            print(f"  ⚠ No matching folder found in {OY_DIR}")
            continue

        folder_name = os.path.basename(folder_path)
        print(f"  Folder: {folder_name}")

        rsd_files = sorted(glob.glob(os.path.join(folder_path, '*.rsd')))
        if not rsd_files:
            print(f"  ⚠ No .rsd files in folder")
            continue
        print(f"  RSD files: {len(rsd_files)}")

        # Get IS refs: prefer inter-well consistency (per-folder), fallback to manual
        ref_positions = get_is_refs_for_folder(folder_path, plate_name)
        if not ref_positions:
            print(f"  ⚠ Could not find IS refs for this plate")
            continue
        print(f"  IS refs: {ref_positions}")

        # Process each well
        well_predictions = {}
        for rsd_path in rsd_files:
            well = os.path.splitext(os.path.basename(rsd_path))[0]
            if well not in ref_calls:
                continue
            try:
                df = parse_rsd(rsd_path)
                if len(df) < 50:
                    continue
                is_peaks = find_is_peaks_raw_argmax(df, ref_positions)
                if not is_peaks or len(is_peaks) < 2:
                    well_predictions[well] = 'NO_IS'
                    continue
                feats = extract_features_from_trace(df, is_peaks=is_peaks)
                row_vec = np.array([feats.get(f, 0.0) for f in ref_features])
                well_predictions[well] = ('FEATURES', row_vec, feats)
            except Exception as e:
                well_predictions[well] = f'ERROR: {e}'

        # Per-plate normalization
        feat_list = []
        well_order = []
        for well in sorted(well_predictions):
            val = well_predictions[well]
            if isinstance(val, tuple) and val[0] == 'FEATURES':
                feat_list.append(val[1])
                well_order.append(well)
        if not feat_list:
            print(f"  ⚠ No feature vectors extracted")
            continue

        feat_matrix = np.array(feat_list)
        median = np.median(feat_matrix, axis=0)
        p75 = np.percentile(feat_matrix, 75, axis=0)
        p25 = np.percentile(feat_matrix, 25, axis=0)
        iqr = np.maximum(p75 - p25, 1e-8)

        # Predict
        X_norm = (feat_matrix - median) / iqr
        y_prob = model.predict_proba(X_norm)
        y_pred = model.predict(X_norm)

        # Compare to reference
        correct = 0
        total_compared = 0
        missing = 0
        no_is_count = 0
        confusion = {}
        for i, well in enumerate(well_order):
            pred_int = int(y_pred[i])
            pred_name = LABEL_UNMAP.get(pred_int, str(pred_int))
            ref_call = ref_calls.get(well)
            status = 'OK' if ref_call == pred_int else 'MISMATCH'
            if ref_call is not None:
                total_compared += 1
                if ref_call == pred_int:
                    correct += 1
                key = (ref_call, pred_int)
                confusion[key] = confusion.get(key, 0) + 1
                all_results.append({
                    'plate': plate_name, 'well': well,
                    'ref': ref_call, 'pred': pred_int,
                    'pred_name': pred_name, 'status': status,
                })
            else:
                missing += 1
            # Print mismatches
            if ref_call is not None and ref_call != pred_int:
                print(f"    {well}: ref={ref_call} pred={pred_name}({pred_int}) ← MISMATCH")

        for well, val in well_predictions.items():
            if val == 'NO_IS':
                no_is_count += 1
                if well in ref_calls:
                    print(f"    {well}: NO_IS (ref={ref_calls[well]})")

        accuracy = correct / max(total_compared, 1) * 100
        print(f"  Results: {correct}/{total_compared} correct ({accuracy:.1f}%)")
        if missing:
            print(f"  Wells in prediction but not ref: {missing}")
        if no_is_count:
            print(f"  Wells with no IS peaks: {no_is_count}")
        if confusion:
            print(f"  Confusion (ref→pred):")
            for (r, p), cnt in sorted(confusion.items()):
                rn = LABEL_UNMAP.get(r, str(r))
                pn = LABEL_UNMAP.get(p, str(p))
                print(f"    ref={rn}({r}) → pred={pn}({p}): {cnt}")

    # Overall accuracy
    if all_results:
        total = len(all_results)
        correct = sum(1 for r in all_results if r['ref'] == r['pred'])
        print(f"\n{'='*70}")
        print(f"OVERALL: {correct}/{total} correct ({correct/max(total,1)*100:.1f}%)")
        df_out = pd.DataFrame(all_results)
        csv_path = os.path.join(SCRIPT_DIR, 'batch_validation_results.csv')
        df_out.to_csv(csv_path, index=False)
        print(f"Saved: {csv_path}")
    else:
        print("\nNo results to compare.")

if __name__ == '__main__':
    main()
