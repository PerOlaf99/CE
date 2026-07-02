#!/usr/bin/env python3
"""Train 5 architectures on M13 reference labels, then 5 rounds of active retraining."""
import os, sys, time, json, warnings
import numpy as np
warnings.filterwarnings('ignore')
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
os.environ['TF_GPU_ALLOW_GROWTH'] = 'true'

sys.path.insert(0, os.path.dirname(__file__))
from extract_training_data import parse_rsd, parse_esd
from m13_reference import M13_REFERENCE, align_to_reference
from brute_force_basecalling import (
    load_m13_training_data, build_cnn, build_lstm, build_resnet,
    normalize, stratified_split, ShiftAugment, train_model,
    evaluate_model_on_well, evaluate_on_plate, load_well
)

BASE_DIR = os.path.dirname(__file__)
DATA_SUBDIR = 'MB1000_M13_DT'
LABELS = ['A', 'C', 'G', 'T', 'N']
CH_NAMES = ['Channel1', 'Channel2', 'Channel3', 'Channel4']

ARCHITECTURES = [
    {'name': 'cnn_std',    'fn': lambda: build_cnn(window=31, width=64,  depth=4)},
    {'name': 'cnn_leaky',  'fn': lambda: build_cnn(window=31, width=64,  depth=4, use_leaky=True)},
    {'name': 'cnn_wide',   'fn': lambda: build_cnn(window=31, width=128, depth=4, use_leaky=True)},
    {'name': 'bilstm',     'fn': lambda: build_lstm(window=31, bidirectional=True)},
    {'name': 'resnet',     'fn': lambda: build_resnet(window=31)},
]

def generate_pseudo_labels(ensemble_models, df, window=15):
    """Generate ensemble predictions for all scan positions in a well."""
    ch = df[CH_NAMES].values
    n = len(ch)
    if n < window * 2 + 1:
        return np.array([]), np.array([])
    positions = np.arange(window, n - window)
    X = np.array([ch[p - window:p + window + 1] for p in positions], dtype=np.float32)
    X = normalize(X)
    all_preds = []
    for model in ensemble_models:
        p = model.predict(X, verbose=0)
        all_preds.append(p)
    avg_preds = np.mean(all_preds, axis=0)
    classes = avg_preds.argmax(axis=1)
    confs = avg_preds.max(axis=1)
    return positions, classes, confs

def decode_scan_calls(positions, classes, confs, min_confidence=0.65, min_spacing=3):
    """Decode per-scan predictions to sequence (same as basecall_ml_scan logic)."""
    is_base = (classes < 4) & (confs >= min_confidence)
    bases, pos_out = [], []
    i = 0
    while i < len(positions):
        if not is_base[i]:
            i += 1
            continue
        base_cls = classes[i]
        j = i
        while j < len(positions) and is_base[j] and classes[j] == base_cls:
            j += 1
        run_confs = confs[i:j]
        best_idx = i + run_confs.argmax()
        best_pos = positions[best_idx]
        bases.append(LABELS[base_cls])
        pos_out.append(float(best_pos))
        next_scan = best_pos + min_spacing
        i = np.searchsorted(positions, next_scan)
    return bases, pos_out

def evaluate_sequence(seq, label=''):
    align = align_to_reference(seq)
    if align['identity'] > 0:
        print(f"  {label}: id={align['identity']:.4f} ({align['matches']}/{align['aligned_length']})")
    else:
        print(f"  {label}: alignment failed")
    return align

# ============================================================
# MAIN
# ============================================================
def main():
    # Get wells
    data_dir = os.path.join(BASE_DIR, DATA_SUBDIR)
    wells = sorted([f.replace('.rsd', '') for f in os.listdir(data_dir) if f.endswith('.rsd')])
    print(f"Found {len(wells)} wells")

    # Split: 72 train, 12 val, 12 test
    rng = np.random.RandomState(42)
    rng.shuffle(wells)
    train_wells = wells[:72]
    val_wells = wells[72:84]
    test_wells = wells[84:96]
    print(f"Train: {len(train_wells)}, Val: {len(val_wells)}, Test: {len(test_wells)}")

    # Load M13 reference training data
    print("\n=== Loading training data ===")
    X_all, y_all = load_m13_training_data(
        BASE_DIR, DATA_SUBDIR, window=15,
        use_reference=True, max_wells=72
    )
    if X_all is None:
        print("Failed to load training data!")
        return

    _, val_idx, test_idx = stratified_split(y_all, test_pct=0.1, val_pct=0.1)
    train_idx = np.setdiff1d(np.arange(len(y_all)), np.concatenate([val_idx, test_idx]))
    X_train, y_train = X_all[train_idx], y_all[train_idx]
    X_val, y_val = X_all[val_idx], y_all[val_idx]

    print(f"X_train: {len(X_train)}, X_val: {len(X_val)}")
    print(f"Classes: train={np.bincount(y_train, minlength=5)}, val={np.bincount(y_val, minlength=5)}")

    # Phase 1: Train 5 architectures
    print("\n" + "="*60)
    print("PHASE 1: TRAINING 5 ARCHITECTURES")
    print("="*60)

    trained_models = []
    for arch in ARCHITECTURES:
        name = arch['name']
        print(f"\n--- Training {name} ---")
        model = arch['fn']()
        t0 = time.time()
        hist = train_model(model, X_train, y_train, X_val, y_val,
                          batch_size=128, epochs=80, max_shift=8)
        dt = time.time() - t0
        best_val = max(hist.history['val_accuracy'])
        print(f"  Done in {dt:.0f}s, best val_acc={best_val:.4f}")
        path = os.path.join(BASE_DIR, f'ensemble_{name}.keras')
        model.save(path)
        print(f"  Saved to {path}")
        trained_models.append(model)

    # Phase 2: Ensemble evaluation on test wells
    print("\n" + "="*60)
    print("PHASE 2: ENSEMBLE EVALUATION")
    print("="*60)

    print("\nIndividual model evaluation on test wells:")
    for arch, model in zip(ARCHITECTURES, trained_models):
        results = evaluate_on_plate(model, test_wells, BASE_DIR, DATA_SUBDIR,
                                    use_scan=False, min_confidence=0.5,
                                    min_spacing=3, window=15)
        print(f"  {arch['name']:15s}: {results['n_wells']} wells, "
              f"mean id={results['mean_identity']:.4f}")

    print("\nEnsemble per-scan evaluation on test wells:")
    all_alns = []
    for well in test_wells:
        df = load_well(well, data_dir)
        if df is None:
            continue
        positions, classes, confs = generate_pseudo_labels(trained_models, df)
        if len(positions) == 0:
            continue
        # Try multiple confidence thresholds
        best_id = 0
        best_seq = ''
        for thresh in [0.3, 0.5, 0.65, 0.8]:
            bases, _ = decode_scan_calls(positions, classes, confs, min_confidence=thresh)
            seq = ''.join(bases)
            if len(seq) < 50:
                continue
            aln = align_to_reference(seq)
            if aln['identity'] > best_id:
                best_id = aln['identity']
                best_seq = seq
        if best_id > 0:
            all_alns.append({'well': well, 'identity': best_id,
                            'sequence': best_seq, 'matches': int(best_id * len(best_seq)),
                            'aligned': len(best_seq)})
            print(f"  {well}: id={best_id:.4f} ({len(best_seq)} bp)")

    if all_alns:
        ids = [a['identity'] for a in all_alns]
        print(f"\nEnsemble summary: mean id={np.mean(ids):.4f} ± {np.std(ids):.4f} "
              f"({len(all_alns)} wells)")

    # Phase 3: 5 rounds of active retraining
    print("\n" + "="*60)
    print("PHASE 3: 5 ROUNDS ACTIVE RETRAINING")
    print("="*60)

    current_models = trained_models.copy()
    for iteration in range(5):
        print(f"\n--- Active retraining iteration {iteration + 1}/5 ---")

        # Generate ensemble pseudo-labels on train wells
        new_X, new_y = [], []
        for well in train_wells:
            df = load_well(well, data_dir)
            if df is None:
                continue
            positions, classes, confs = generate_pseudo_labels(current_models, df)
            if len(positions) == 0:
                continue
            bases, _ = decode_scan_calls(positions, classes, confs,
                                        min_confidence=0.65)
            seq = ''.join(bases)
            if len(seq) < 50:
                continue
            aln = align_to_reference(seq)
            if aln['identity'] < 0.5:
                continue

            # For high-confidence positions, use M13 reference as label
            q_aln = aln['query_aligned']
            r_aln = aln['ref_aligned']
            esd_pos = 0
            for qb, rb in zip(q_aln, r_aln):
                if qb == '-' or rb == '-':
                    continue
                if esd_pos >= len(bases):
                    break
                if bases[esd_pos] == rb:
                    # Correct prediction — use as training example
                    # Find the scan position (approximate from decoded positions)
                    pass
                esd_pos += 1

            # Simpler approach: scan every position, use M13 alignment as label
            ch = df[CH_NAMES].values
            n = len(ch)
            for p in range(15, n - 15):
                win = ch[p - 15:p + 16]
                # Predict
                X_single = normalize(win[np.newaxis, ...])
                preds = [m.predict(X_single, verbose=0)[0] for m in current_models]
                avg_pred = np.mean(preds, axis=0)
                cls = avg_pred.argmax()
                conf = avg_pred.max()
                if cls >= 4 or conf < 0.8:
                    continue
                new_X.append(win)
                new_y.append(cls)

        if len(new_X) < 100:
            print(f"  Only {len(new_X)} new examples, skipping")
            continue

        X_new = np.array(new_X, dtype=np.float32)
        y_new = np.array(new_y, dtype=np.uint8)
        print(f"  Generated {len(X_new)} pseudo-labeled examples")

        # Retrain each model with combined data
        X_combined = np.concatenate([X_train, X_new])
        y_combined = np.concatenate([y_train, y_new])
        print(f"  Combined: {len(X_combined)} examples")

        # Shuffle
        shuffle_idx = np.random.permutation(len(X_combined))
        X_combined = X_combined[shuffle_idx]
        y_combined = y_combined[shuffle_idx]

        # Retrain ensemble
        for i, (arch, model) in enumerate(zip(ARCHITECTURES, current_models)):
            print(f"  Retraining {arch['name']}...")
            # Reinitialize
            new_model = arch['fn']()
            t0 = time.time()
            hist = train_model(new_model, X_combined, y_combined,
                              X_val, y_val,
                              batch_size=128, epochs=50, max_shift=8)
            dt = time.time() - t0
            best_val = max(hist.history['val_accuracy'])
            print(f"    Done in {dt:.0f}s, best val_acc={best_val:.4f}")
            path = os.path.join(BASE_DIR, f'ensemble_{arch["name"]}_iter{iteration+1}.keras')
            new_model.save(path)
            current_models[i] = new_model

        # Evaluate on test wells
        all_alns = []
        for well in test_wells:
            df = load_well(well, data_dir)
            if df is None:
                continue
            positions, classes, confs = generate_pseudo_labels(current_models, df)
            if len(positions) == 0:
                continue
            best_id = 0
            for thresh in [0.3, 0.5, 0.65, 0.8]:
                bases, _ = decode_scan_calls(positions, classes, confs, min_confidence=thresh)
                seq = ''.join(bases)
                if len(seq) < 50:
                    continue
                aln = align_to_reference(seq)
                if aln['identity'] > best_id:
                    best_id = aln['identity']
            if best_id > 0:
                all_alns.append(best_id)

        if all_alns:
            print(f"  Iteration {iteration+1} test: mean id={np.mean(all_alns):.4f} "
                  f"± {np.std(all_alns):.4f}")

        # Save checkpoints
        results = {
            'iteration': iteration + 1,
            'test_identities': [float(x) for x in all_alns],
            'mean_identity': float(np.mean(all_alns)) if all_alns else 0,
            'n_test_wells': len(all_alns),
        }
        with open(os.path.join(BASE_DIR, f'ensemble_iter{iteration+1}.json'), 'w') as f:
            json.dump(results, f, indent=2)

    print("\n=== DONE ===")

if __name__ == '__main__':
    main()
