"""Overnight ML training: compare normalization strategies and models on MB1000_M13_DT."""
import sys, os, time, json, argparse
import numpy as np
from simple_align import align_to_m13

base_map = {'A':0,'C':1,'G':2,'T':3,'N':4}
inv_map = {0:'A',1:'C',2:'G',3:'T'}

RESULTS = {}

def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)

def per_well_zscore(X, wells, eps=1e-8):
    """Per-well per-channel z-score normalization."""
    Xn = X.astype(np.float64).copy()
    for w in np.unique(wells):
        mask = wells == w
        for ch in range(4):
            data = Xn[mask, :, ch]
            mu, sd = data.mean(), data.std()
            if sd < eps:
                sd = 1.0
            Xn[mask, :, ch] = (data - mu) / sd
    return Xn.astype(np.float32)

def per_well_minmax(X, wells):
    """Per-well per-channel min-max to [0,1]."""
    Xn = X.astype(np.float64).copy()
    for w in np.unique(wells):
        mask = wells == w
        for ch in range(4):
            data = Xn[mask, :, ch]
            lo, hi = data.min(), data.max()
            if hi > lo:
                Xn[mask, :, ch] = (data - lo) / (hi - lo)
            else:
                Xn[mask, :, ch] = 0.0
    return Xn.astype(np.float32)

def global_zscore(X, eps=1e-8):
    """Global per-channel z-score (no per-well)."""
    Xn = X.astype(np.float64).copy()
    for ch in range(4):
        data = Xn[:, :, ch]
        mu, sd = data.mean(), data.std()
        Xn[:, :, ch] = (data - mu) / max(sd, eps)
    return Xn.astype(np.float32)

def evaluate_model(name, model, X_test, y_test):
    from sklearn.metrics import accuracy_score, confusion_matrix
    pred = model.predict(X_test)
    acc = accuracy_score(y_test, pred)
    cm = confusion_matrix(y_test, pred, labels=[0,1,2,3])
    return acc, pred, cm

def loto_cv_rf(X, y, wells, n_estimators=500, max_depth=12):
    from sklearn.ensemble import RandomForestClassifier
    unique_wells = np.unique(wells)
    log(f"  LOTO RF: {len(unique_wells)} wells, X {X.shape}, {n_estimators} trees")
    accs = {}
    t0 = time.time()
    for test_well in unique_wells:
        test_mask = wells == test_well
        train_mask = ~test_mask
        rf = RandomForestClassifier(
            n_estimators=int(n_estimators), max_depth=int(max_depth),
            class_weight='balanced', n_jobs=-1, random_state=42)
        rf.fit(X[train_mask].reshape(train_mask.sum(), -1), y[train_mask])
        pred = rf.predict(X[test_mask].reshape(test_mask.sum(), -1))
        acc = (pred == y[test_mask]).mean()
        accs[test_well] = float(acc)
    t = time.time() - t0
    mean_acc = np.mean(list(accs.values()))
    log(f"  LOTO RF done in {t:.0f}s, mean acc={mean_acc*100:.1f}%")
    return {'accuracies': accs, 'mean_accuracy': mean_acc, 'time': t}

def loto_cv_xgb(X, y, wells, n_estimators=500, max_depth=8):
    import xgboost as xgb
    unique_wells = np.unique(wells)
    log(f"  LOTO XGB: {len(unique_wells)} wells, X {X.shape}, {n_estimators} rounds")
    accs = {}
    t0 = time.time()
    for test_well in unique_wells:
        test_mask = wells == test_well
        train_mask = ~test_mask
        X_train = X[train_mask].reshape(train_mask.sum(), -1)
        y_train = y[train_mask]
        X_test = X[test_mask].reshape(test_mask.sum(), -1)
        y_test = y[test_mask]
        model = xgb.XGBClassifier(
            n_estimators=n_estimators, max_depth=max_depth,
            learning_rate=0.1, subsample=0.8, colsample_bytree=0.8,
            n_jobs=-1, random_state=42, verbosity=0)
        model.fit(X_train, y_train)
        pred = model.predict(X_test)
        acc = (pred == y_test).mean()
        accs[test_well] = float(acc)
    t = time.time() - t0
    mean_acc = np.mean(list(accs.values()))
    log(f"  LOTO XGB done in {t:.0f}s, mean acc={mean_acc*100:.1f}%")
    return {'accuracies': accs, 'mean_accuracy': mean_acc, 'time': t}

def loto_cv_mlp(X, y, wells, hidden=(128, 64)):
    from sklearn.neural_network import MLPClassifier
    unique_wells = np.unique(wells)
    log(f"  LOTO MLP: {len(unique_wells)} wells, hidden={hidden}")
    accs = {}
    t0 = time.time()
    for test_well in unique_wells:
        test_mask = wells == test_well
        train_mask = ~test_mask
        X_train = X[train_mask].reshape(train_mask.sum(), -1)
        y_train = y[train_mask]
        X_test = X[test_mask].reshape(test_mask.sum(), -1)
        y_test = y[test_mask]
        mlp = MLPClassifier(
            hidden_layer_sizes=hidden, activation='relu',
            max_iter=200, early_stopping=True,
            random_state=42, verbose=False)
        mlp.fit(X_train, y_train)
        pred = mlp.predict(X_test)
        acc = (pred == y_test).mean()
        accs[test_well] = float(acc)
    t = time.time() - t0
    mean_acc = np.mean(list(accs.values()))
    log(f"  LOTO MLP done in {t:.0f}s, mean acc={mean_acc*100:.1f}%")
    return {'accuracies': accs, 'mean_accuracy': mean_acc, 'time': t}

def train_cnn(X, y, test_well, wells):
    """Train a 1D CNN on 31×4 input, evaluate on held-out well."""
    import tensorflow as tf
    tf.get_logger().setLevel('ERROR')
    from tensorflow import keras
    tf.random.set_seed(42)

    test_mask = wells == test_well
    train_mask = ~test_mask
    X_train, y_train = X[train_mask], y[train_mask]
    X_test, y_test = X[test_mask], y[test_mask]

    n_classes = 5
    inp = keras.layers.Input(shape=(31, 4))
    x = keras.layers.Conv1D(64, 5, padding='same', activation='relu')(inp)
    x = keras.layers.MaxPool1D(2)(x)
    x = keras.layers.Conv1D(128, 3, padding='same', activation='relu')(x)
    x = keras.layers.MaxPool1D(2)(x)
    x = keras.layers.Flatten()(x)
    x = keras.layers.Dense(128, activation='relu')(x)
    x = keras.layers.Dropout(0.3)(x)
    x = keras.layers.Dense(n_classes, activation='softmax')(x)
    model = keras.Model(inp, x)
    model.compile(optimizer='adam', loss='sparse_categorical_crossentropy',
                  metrics=['accuracy'])
    callbacks = [keras.callbacks.EarlyStopping(patience=5, restore_best_weights=True)]
    model.fit(X_train, y_train, epochs=30, batch_size=128,
              validation_split=0.1, callbacks=callbacks, verbose=0)
    loss, acc = model.evaluate(X_test, y_test, verbose=0)
    return acc, model

def train_all_cnn(X, y):
    """Train CNN on all data, return model and accuracy."""
    import tensorflow as tf
    tf.get_logger().setLevel('ERROR')
    from tensorflow import keras
    tf.random.set_seed(42)
    n_classes = 5
    inp = keras.layers.Input(shape=(31, 4))
    x = keras.layers.Conv1D(64, 5, padding='same', activation='relu')(inp)
    x = keras.layers.BatchNormalization()(x)
    x = keras.layers.MaxPool1D(2)(x)
    x = keras.layers.Conv1D(128, 3, padding='same', activation='relu')(x)
    x = keras.layers.BatchNormalization()(x)
    x = keras.layers.MaxPool1D(2)(x)
    x = keras.layers.Conv1D(256, 3, padding='same', activation='relu')(x)
    x = keras.layers.GlobalAvgPool1D()(x)
    x = keras.layers.Dense(128, activation='relu')(x)
    x = keras.layers.Dropout(0.3)(x)
    x = keras.layers.Dense(n_classes, activation='softmax')(x)
    model = keras.Model(inp, x)
    model.compile(optimizer='adam', loss='sparse_categorical_crossentropy',
                  metrics=['accuracy'])
    callbacks = [keras.callbacks.EarlyStopping(patience=8, restore_best_weights=True)]
    model.fit(X, y, epochs=50, batch_size=256,
              validation_split=0.1, callbacks=callbacks, verbose=0)
    return model

def evaluate_m13(seq_called):
    """Align called sequence to M13 reference and return identity."""
    res = align_to_m13(seq_called)
    if res is None:
        return 0.0
    return res['identity']

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--data', default='training_data_separated/Cp312.npz')
    parser.add_argument('--output', default='overnight_results.json')
    parser.add_argument('--no-rf', action='store_true', help='Skip RF')
    parser.add_argument('--no-xgb', action='store_true', help='Skip XGBoost')
    parser.add_argument('--no-mlp', action='store_true', help='Skip MLP')
    parser.add_argument('--no-cnn', action='store_true', help='Skip CNN')
    parser.add_argument('--test-well', default='A01', help='Well for detailed eval')
    args = parser.parse_args()

    # --- Load data ---
    log("Loading Cp312.npz...")
    d = np.load(args.data, allow_pickle=True)
    X_raw = d['X']
    y = d['y']
    wells = d['wells']
    log(f"Loaded: X {X_raw.shape}, y distribution: {dict(zip(*np.unique(y, return_counts=True)))}")
    log(f"Wells: {len(np.unique(wells))} unique")

    # Filter to only A/C/G/T (drop N for cleaner evaluation)
    non_n = y != 4
    X_raw = X_raw[non_n]
    y = y[non_n]
    wells = wells[non_n]
    log(f"After dropping N: X {X_raw.shape}, y distribution: {dict(zip(*np.unique(y, return_counts=True)))}")

    # --- Prepare normalized versions ---
    log("Preparing normalized datasets...")
    t0 = time.time()
    datasets = {
        'raw': X_raw.copy(),
    }
    datasets['global_zscore'] = global_zscore(X_raw)
    datasets['well_zscore'] = per_well_zscore(X_raw, wells)
    datasets['well_minmax'] = per_well_minmax(X_raw, wells)
    log(f"Normalization done in {time.time()-t0:.0f}s")

    # --- Quick sanity check: RF on A01 only with well_zscore ---
    log("\n=== Quick sanity: RF on A01 with z-score ===")
    mask_a01 = wells == args.test_well
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.model_selection import StratifiedKFold
    from sklearn.metrics import accuracy_score
    rf = RandomForestClassifier(200, 12, class_weight='balanced', n_jobs=-1, random_state=42)
    Xz = datasets['well_zscore']
    scores = []
    skf = StratifiedKFold(5, shuffle=True, random_state=42)
    for tr, te in skf.split(Xz[mask_a01].reshape(mask_a01.sum(), -1), y[mask_a01]):
        rf.fit(Xz[mask_a01][tr].reshape(len(tr), -1), y[mask_a01][tr])
        pred = rf.predict(Xz[mask_a01][te].reshape(len(te), -1))
        scores.append(accuracy_score(y[mask_a01][te], pred))
    log(f"RF 5-fold CV on {args.test_well} (well_zscore): {np.mean(scores)*100:.1f}%")

    # --- Full leave-one-well-out CV ---
    results = {}

    if not args.no_rf:
        for name in ['raw', 'well_zscore', 'well_minmax', 'global_zscore']:
            log(f"\n=== RF LOTO: {name} ===")
            results[f'rf_{name}'] = loto_cv_rf(
                datasets[name], y, wells, n_estimators=500, max_depth=12)

    if not args.no_xgb:
        for name in ['raw', 'well_zscore', 'well_minmax']:
            log(f"\n=== XGB LOTO: {name} ===")
            results[f'xgb_{name}'] = loto_cv_xgb(
                datasets[name], y, wells, n_estimators=500, max_depth=8)

    if not args.no_mlp:
        for name in ['well_zscore', 'well_minmax']:
            log(f"\n=== MLP LOTO: {name} ===")
            results[f'mlp_{name}'] = loto_cv_mlp(
                datasets[name], y, wells, hidden=(256, 128, 64))

    if not args.no_cnn:
        log(f"\n=== CNN on {args.test_well} (well_zscore) ===")
        Xz = datasets['well_zscore']
        acc, model = train_cnn(Xz, y, args.test_well, wells)
        log(f"CNN test acc on {args.test_well}: {acc*100:.1f}%")
        results[f'cnn_{args.test_well}'] = {'test_accuracy': float(acc)}

        # Train CNN on all data
        log(f"\n=== CNN full training (well_zscore) ===")
        cnn_model = train_all_cnn(Xz, y)
        results['cnn_full'] = {'status': 'trained'}

        # Evaluate CNN on A01 vs M13
        log(f"\n=== CNN + M13 eval on {args.test_well} ===")
        from extract_training_data import parse_rsd, parse_esd
        from tracetuner_separation import trace_tuner_separate

        df = parse_rsd(f'MB1000_M13_DT/{args.test_well}.rsd')
        ch = df[['Channel1','Channel2','Channel3','Channel4']].values.T.astype(np.float64)
        sep = trace_tuner_separate(ch.copy())

        # Per-well normalize the full separated trace
        for c in range(4):
            mu, sd = sep[c].mean(), sep[c].std()
            sep[c] = (sep[c] - mu) / max(sd, 1e-8)

        esd = parse_esd(f'MB1000_M13_DT/MB1000_M13_DT_Cp312_MD1/{args.test_well}.esd')
        pos = esd.get('peak_positions')
        seq = esd.get('sequence','')
        pos = pos[:len(seq)].astype(int)

        window = 15
        X_test, y_test = [], []
        test_positions = []
        for i, p in enumerate(pos):
            if p < window or p >= sep.shape[1] - window:
                continue
            X_test.append(sep[:, p-window:p+window+1].T)  # (31, 4)
            y_test.append(base_map.get(seq[i], 4))
            test_positions.append(p)
        X_test = np.array(X_test)
        y_test = np.array(y_test)

        pred = cnn_model.predict(X_test, verbose=0).argmax(axis=1)
        cnn_called = ''.join(inv_map[int(p)] for p in pred)
        res = align_to_m13(cnn_called)
        log(f"CNN vs M13: {res['identity']:.1f}% (alen={res['alignment_length']})")
        results['cnn_m13'] = {
            'identity': res['identity'],
            'alignment_length': res['alignment_length'],
            'matches': res['matches'],
        }

        # Cp312 baseline for comparison
        cp_called = seq[:len(pred)]
        res_cp = align_to_m13(cp_called)
        log(f"Cp312 vs M13: {res_cp['identity']:.1f}% (alen={res_cp['alignment_length']})")
        results['cp312_m13'] = {
            'identity': res_cp['identity'],
            'alignment_length': res_cp['alignment_length'],
            'matches': res_cp['matches'],
        }

    # --- M13 evaluation for best RF and XGB models ---
    log(f"\n=== M13 Evaluation ===")
    for method in ['rf_well_zscore', 'xgb_well_zscore']:
        if method not in results:
            continue
        log(f"  Training final {method} model on all data...")
        Xz = datasets['well_zscore']
        X_flat = Xz.reshape(Xz.shape[0], -1)
        if method.startswith('rf'):
            from sklearn.ensemble import RandomForestClassifier
            model = RandomForestClassifier(500, 12, class_weight='balanced', n_jobs=-1, random_state=42)
        else:
            import xgboost as xgb
            model = xgb.XGBClassifier(500, 8, learning_rate=0.1, subsample=0.8, colsample_bytree=0.8, n_jobs=-1, random_state=42, verbosity=0)
        model.fit(X_flat, y)

        # Evaluate on test well
        from extract_training_data import parse_rsd, parse_esd
        from tracetuner_separation import trace_tuner_separate

        df = parse_rsd(f'MB1000_M13_DT/{args.test_well}.rsd')
        ch = df[['Channel1','Channel2','Channel3','Channel4']].values.T.astype(np.float64)
        sep = trace_tuner_separate(ch.copy())

        # Per-well z-score normalize the separated trace
        for c in range(4):
            mu, sd = sep[c].mean(), sep[c].std()
            sep[c] = (sep[c] - mu) / max(sd, 1e-8)

        esd = parse_esd(f'MB1000_M13_DT/MB1000_M13_DT_Cp312_MD1/{args.test_well}.esd')
        pos = esd.get('peak_positions')
        seq = esd.get('sequence','')
        pos = pos[:len(seq)].astype(int)
        quality = esd.get('quality_scores', np.ones(len(seq)))

        window = 15
        X_test, y_test = [], []
        test_positions = []
        test_qual = []
        for i, p in enumerate(pos):
            if p < window or p >= sep.shape[1] - window:
                continue
            X_test.append(sep[:, p-window:p+window+1].ravel())
            y_test.append(base_map.get(seq[i], 4))
            test_positions.append(p)
            test_qual.append(quality[i] if i < len(quality) else 0)
        X_test = np.array(X_test)
        y_test = np.array(y_test)
        test_qual = np.array(test_qual)

        pred = model.predict(X_test)
        acc = (pred == y_test).mean()
        called = ''.join(inv_map[int(p)] for p in pred)
        res = align_to_m13(called)
        log(f"  {method} on {args.test_well}: per-pos acc={acc*100:.1f}%, "
            f"M13 identity={res['identity']:.1f}%")
        results[f'{method}_m13'] = {
            'per_position_accuracy': float(acc),
            'identity': res['identity'],
            'alignment_length': res['alignment_length'],
            'matches': res['matches'],
        }

    # --- Summary ---
    log("\n" + "="*60)
    log("SUMMARY")
    log("="*60)
    for k, v in sorted(results.items()):
        if 'mean_accuracy' in v:
            log(f"  {k}: mean acc={v['mean_accuracy']*100:.1f}% (t={v['time']:.0f}s)")
        elif 'identity' in v:
            log(f"  {k}: M13 identity={v['identity']:.1f}%")
        elif 'test_accuracy' in v:
            log(f"  {k}: test acc={v['test_accuracy']*100:.1f}%")

    # Save results
    serializable = {}
    for k, v in results.items():
        if isinstance(v, dict):
            serializable[k] = {kk: float(vv) if isinstance(vv, (np.floating, np.integer)) else vv
                              for kk, vv in v.items()}
    with open(args.output, 'w') as f:
        json.dump(serializable, f, indent=2)
    log(f"\nResults saved to {args.output}")

if __name__ == '__main__':
    main()
