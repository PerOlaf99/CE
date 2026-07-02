#!/usr/bin/env python3
"""Train a Random Forest base caller on ESD peak data with M13 reference labels.

Bypasses the spectral separation matrix entirely — learns the mapping from
raw 4-channel signal at peak positions directly to A/C/G/T.
"""
import sys, os, time, json, warnings, pickle
import numpy as np
from collections import Counter
warnings.filterwarnings('ignore')

sys.path.insert(0, os.path.dirname(__file__))
from extract_training_data import parse_rsd, parse_esd
from m13_reference import M13_REFERENCE, align_to_reference
from peak_detector import PeakDetector

BASE_DIR = os.path.dirname(__file__)
DATA_SUBDIR = 'MB1000_M13_DT'
CH_NAMES = ['Channel1', 'Channel2', 'Channel3', 'Channel4']
LABELS = ['A', 'C', 'G', 'T']
BASE_MAP = {b: i for i, b in enumerate(LABELS)}

def extract_features(ch, peak_idx, window=15):
    """Extract features from raw 4-channel signal at peak position ± window."""
    n = len(ch)
    start = max(0, peak_idx - window)
    end = min(n, peak_idx + window + 1)
    win = ch[start:end]
    # Pad if near edges
    if len(win) < window * 2 + 1:
        pad_before = max(0, window - peak_idx)
        pad_after = max(0, (peak_idx + window + 1) - n)
        win = np.pad(win, ((pad_before, pad_after), (0, 0)), mode='edge')
    return win.flatten()

def build_training_data(wells, window=15):
    """Build X, y from ESD peak positions + M13 reference labels."""
    X, y, well_names = [], [], []
    base_map_rev = {'A': 0, 'C': 1, 'G': 2, 'T': 3, 'N': 4}
    
    for well in wells:
        # Load RSD data
        rsd_path = os.path.join(BASE_DIR, DATA_SUBDIR, f"{well}.rsd")
        if not os.path.exists(rsd_path):
            continue
        df = parse_rsd(rsd_path)
        ch = df[CH_NAMES].values.astype(np.float64)
        
        # Load ESD (Cp312 — most reliable)
        esd_path = os.path.join(BASE_DIR, DATA_SUBDIR,
                                f"{DATA_SUBDIR}_Cp312_MD1", f"{well}.esd")
        if not os.path.exists(esd_path):
            continue
        esd = parse_esd(esd_path)
        seq = ''.join(c for c in esd.get('sequence','') if c in 'ACGTNacgtn').upper()
        positions = esd.get('peak_positions')
        if positions is None or len(positions) == 0 or len(seq) < 50:
            continue
        
        # Align ESD sequence to M13 reference
        aln = align_to_reference(seq)
        if aln['identity'] < 0.5:
            continue
        
        q_aln = aln['query_aligned']
        r_aln = aln['ref_aligned']
        
        # Walk alignment: ESD position i → base from M13
        esd_idx = 0
        for qb, rb in zip(q_aln, r_aln):
            if qb == '-' or rb == '-':
                continue
            ref_base = rb
            if ref_base not in base_map_rev or esd_idx >= len(positions):
                esd_idx += 1
                continue
            peak_idx = int(positions[esd_idx])
            if peak_idx < 0 or peak_idx >= len(ch):
                esd_idx += 1
                continue
            feat = extract_features(ch, peak_idx, window)
            X.append(feat)
            y.append(base_map_rev[ref_base])
            well_names.append(well)
            esd_idx += 1
    
    return np.array(X, dtype=np.float32), np.array(y, dtype=np.uint8), well_names

def predict_well(model, df, detector, window=15):
    """Run basecalling on a well: detect peaks, predict bases with RF."""
    peaks_dict = detector.detect_basecalling(df, df['Scan'])
    peaks = peaks_dict['peaks']
    if len(peaks) == 0:
        return ''
    
    ch = df[CH_NAMES].values.astype(np.float64)
    features = []
    valid_peaks = []
    for p in peaks:
        if p < 0 or p >= len(ch):
            continue
        feat = extract_features(ch, p, window)
        features.append(feat)
        valid_peaks.append(p)
    
    if not features:
        return ''
    
    X = np.array(features, dtype=np.float32)
    preds = model.predict(X)
    # Sort by peak position
    sorted_idx = np.argsort(valid_peaks)
    seq = ''.join(LABELS[preds[i]] for i in sorted_idx)
    return seq

def main():
    import time
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.metrics import accuracy_score, classification_report
    import warnings
    warnings.filterwarnings('ignore')
    
    # Get all wells
    data_dir = os.path.join(BASE_DIR, DATA_SUBDIR)
    all_wells = sorted([f.replace('.rsd', '') for f in os.listdir(data_dir) if f.endswith('.rsd')])
    print(f"Found {len(all_wells)} wells")
    
    # Split: 72 train, 12 val, 12 test
    rng = np.random.RandomState(42)
    rng.shuffle(all_wells)
    train_wells = all_wells[:72]
    val_wells = all_wells[72:84]
    test_wells = all_wells[84:96]
    
    # Test different window sizes
    for window in [7, 11, 15, 21]:
        print(f"\n{'='*60}")
        print(f"  Window = {window} (feature dim = {window*2+1} × 4 = {(window*2+1)*4})")
        print(f"{'='*60}")
        
        t0 = time.time()
        X_train, y_train, _ = build_training_data(train_wells, window)
        dt = time.time() - t0
        print(f"  Training data: {len(X_train)} samples from {len(train_wells)} wells ({dt:.1f}s)")
        print(f"  Class distribution: {np.bincount(y_train, minlength=4)}")
        
        # Train RF
        rf = RandomForestClassifier(
            n_estimators=300,
            max_depth=30,
            min_samples_leaf=2,
            class_weight='balanced',
            n_jobs=-1,
            random_state=42,
        )
        t0 = time.time()
        rf.fit(X_train, y_train)
        dt = time.time() - t0
        print(f"  Training: {dt:.1f}s")
        
        # Test on validation wells
        X_val, y_val, _ = build_training_data(val_wells, window)
        if len(X_val) > 0:
            y_pred = rf.predict(X_val)
            val_acc = accuracy_score(y_val, y_pred)
            print(f"  Validation accuracy: {val_acc:.4f} ({len(X_val)} samples)")
            
        # Evaluate full pipeline on test wells
        print(f"\n  Evaluating on {len(test_wells)} test wells...")
        detector = PeakDetector()
        identities = []
        for well in test_wells:
            rsd_path = os.path.join(BASE_DIR, DATA_SUBDIR, f"{well}.rsd")
            if not os.path.exists(rsd_path):
                continue
            df = parse_rsd(rsd_path)
            seq = predict_well(rf, df, detector, window)
            if len(seq) < 50:
                continue
            aln = align_to_reference(seq)
            if aln['identity'] > 0:
                identities.append((well, aln['identity'], len(seq)))
        
        if identities:
            ids = [x[1] for x in identities]
            print(f"  RF basecaller vs M13: "
                  f"mean id={np.mean(ids):.4f} ± {np.std(ids):.4f} "
                  f"({len(identities)} wells)")
            # Show best and worst
            best = max(identities, key=lambda x: x[1])
            worst = min(identities, key=lambda x: x[1])
            print(f"    Best: {best[0]} ({best[1]:.4f}, {best[2]}bp)")
            print(f"    Worst: {worst[0]} ({worst[1]:.4f}, {worst[2]}bp)")
            
            # Save best model
            if window == 15:  # default window
                best_rf = rf
                best_window = window
                best_val_id = np.mean(ids)
    
    # Save the best model (window=15)
    print(f"\n{'='*60}")
    print(f"  Saving best model")
    print(f"{'='*60}")
    
    # Retrain on all wells with best window
    window = 15
    X_all, y_all, _ = build_training_data(all_wells, window)
    print(f"  Full training: {len(X_all)} samples from {len(all_wells)} wells")
    
    final_rf = RandomForestClassifier(
        n_estimators=500,
        max_depth=30,
        min_samples_leaf=2,
        class_weight='balanced',
        n_jobs=-1,
        random_state=42,
    )
    t0 = time.time()
    final_rf.fit(X_all, y_all)
    dt = time.time() - t0
    print(f"  Training: {dt:.1f}s")
    
    # Save
    model_path = os.path.join(BASE_DIR, 'rf_basecaller.pkl')
    with open(model_path, 'wb') as f:
        pickle.dump({'model': final_rf, 'window': window, 'labels': LABELS}, f)
    print(f"  Saved to {model_path}")
    
    # Evaluate on all wells
    print(f"\n  Final evaluation on all {len(all_wells)} wells...")
    detector = PeakDetector()
    all_ids = []
    for well in all_wells:
        rsd_path = os.path.join(BASE_DIR, DATA_SUBDIR, f"{well}.rsd")
        if not os.path.exists(rsd_path):
            continue
        df = parse_rsd(rsd_path)
        seq = predict_well(final_rf, df, detector, window)
        if len(seq) < 50:
            continue
        aln = align_to_reference(seq)
        if aln['identity'] > 0:
            all_ids.append((well, aln['identity'], len(seq)))
    
    if all_ids:
        ids = [x[1] for x in all_ids]
        print(f"  Mean id = {np.mean(ids):.4f} ± {np.std(ids):.4f} ({len(all_ids)} wells)")
        print(f"  Min = {np.min(ids):.4f}, Max = {np.max(ids):.4f}")
        
        # Summary table
        print(f"\n{'='*60}")
        print(f"  BASELINE COMPARISON")
        print(f"{'='*60}")
        # Compare with ESD callers
        for variant in ['Cp312', 'Cp312_a', 'Cp312_es', 'Cp1_530', 'Cp1_530_sl_ph', 'MD']:
            ids_v = []
            for well in all_wells:
                esd_path = os.path.join(BASE_DIR, DATA_SUBDIR,
                                        f"{DATA_SUBDIR}_{variant}_MD1", f"{well}.esd")
                if not os.path.exists(esd_path):
                    continue
                esd = parse_esd(esd_path)
                seq_esd = ''.join(c for c in esd.get('sequence','') if c in 'ACGTNacgtn').upper()
                if len(seq_esd) < 50:
                    continue
                aln = align_to_reference(seq_esd)
                if aln['identity'] > 0:
                    ids_v.append(aln['identity'])
            if ids_v:
                print(f"  {variant:20s}: {np.mean(ids_v):.4f} ± {np.std(ids_v):.4f}")
        
        print(f"  {'RF Basecaller':20s}: {np.mean(ids):.4f} ± {np.std(ids):.4f}")

if __name__ == '__main__':
    main()
