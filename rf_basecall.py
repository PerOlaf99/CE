#!/usr/bin/env python3
"""End-to-end RF basecalling pipeline using pre-separated training data."""
import sys, os, argparse, time, json
import numpy as np
from sklearn.ensemble import RandomForestClassifier

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from extract_training_data import parse_rsd, parse_esd
from tracetuner_separation import trace_tuner_separate
from simple_align import align_to_m13

BASE_DIR = "/media/tv/78B0C7DE1FA7081C/electropherogram/MB1000_M13_DT"
ESD_DIR = "MB1000_M13_DT_Cp312_MD1"
NPZ_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "training_data_separated")

WINDOW = 15
BASE_MAP = {'A': 0, 'C': 1, 'G': 2, 'T': 3, 'N': 4}
INV_MAP = {0: 'A', 1: 'C', 2: 'G', 3: 'T'}
RF_PARAMS = dict(n_estimators=500, max_depth=12, class_weight='balanced',
                 n_jobs=-1, random_state=42)


def load_separate(well):
    rsd_path = os.path.join(BASE_DIR, f"{well}.rsd")
    df = parse_rsd(rsd_path)
    ch = df[['Channel1','Channel2','Channel3','Channel4']].values.T.astype(np.float64)
    return trace_tuner_separate(ch)


def per_well_zscore_trace(sep):
    result = sep.copy()
    for c in range(4):
        mu, sd = result[c].mean(), result[c].std()
        if sd > 1e-8:
            result[c] = (result[c] - mu) / sd
    return result


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


def train_from_npz(npz_path, drop_n=True):
    d = np.load(npz_path, allow_pickle=True)
    X = d['X'].astype(np.float32)
    y = d['y'].copy()
    wells = d['wells']
    if drop_n:
        keep = y != 4
        X, y, wells = X[keep], y[keep], wells[keep]
    for w in np.unique(wells):
        mask = wells == w
        for ch in range(4):
            data = X[mask, :, ch]
            mu, sd = data.mean(), data.std()
            if sd > 1e-8:
                X[mask, :, ch] = (data - mu) / sd
    rf = RandomForestClassifier(**RF_PARAMS)
    rf.fit(X.reshape(X.shape[0], -1), y)
    return rf


def basecall_well(rf, well, use_esd_positions=True):
    sep = load_separate(well)
    sep_norm = per_well_zscore_trace(sep)
    if use_esd_positions:
        esd = parse_esd(os.path.join(BASE_DIR, ESD_DIR, f"{well}.esd"))
        positions = esd.get('peak_positions')
        if positions is None:
            positions = esd.get('bases_positions')
        seq_esd = esd.get('sequence', '')
        if positions is not None:
            n = min(len(positions), len(seq_esd))
            positions = positions[:n].astype(int)
    else:
        from peak_detector import PeakDetector
        df = parse_rsd(os.path.join(BASE_DIR, f"{well}.rsd"))
        detector = PeakDetector({'min_height': 100, 'prominence': 50,
                                 'active_channels': {'Channel1':True,'Channel2':True,
                                                     'Channel3':True,'Channel4':True,'Current':False}})
        wd = detector.detect(df, df['Scan'])
        detected = wd.get('peaks')
        if detected is None or len(detected) == 0:
            return '', np.array([])
        positions = detected.astype(int)
    X_w, valid = extract_windows(sep_norm, positions)
    if len(X_w) == 0:
        return '', np.array([])
    pred = rf.predict(X_w.reshape(len(X_w), -1))
    seq = ''.join(INV_MAP.get(int(p), 'N') for p in pred)
    return seq, valid


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest='command')

    tp = sub.add_parser('train', help='Train RF from pre-separated NPZ')
    tp.add_argument('--data', default=os.path.join(NPZ_DIR, 'Cp312.npz'))
    tp.add_argument('--output', default='/tmp/rf_model.pkl')

    cp = sub.add_parser('basecall', help='Basecall one well')
    cp.add_argument('well')
    cp.add_argument('--model', default='/tmp/rf_model.pkl')
    cp.add_argument('--no-esd-positions', action='store_true')

    ep = sub.add_parser('evaluate', help='Evaluate vs M13 on one well')
    ep.add_argument('well', nargs='?', default='A01')
    ep.add_argument('--model', default='/tmp/rf_model.pkl')
    ep.add_argument('--no-esd-positions', action='store_true')

    bp = sub.add_parser('batch', help='Evaluate all wells')
    bp.add_argument('--model', default='/tmp/rf_model.pkl')
    bp.add_argument('--output', default='rf_batch_results.json')

    args = parser.parse_args()

    if args.command == 'train':
        print(f"Training RF from {args.data}...")
        t0 = time.time()
        model = train_from_npz(args.data)
        import joblib
        joblib.dump(model, args.output)
        print(f"Saved to {args.output} in {time.time()-t0:.0f}s")

    elif args.command == 'basecall':
        import joblib
        model = joblib.load(args.model)
        seq, pos = basecall_well(model, args.well, use_esd_positions=not args.no_esd_positions)
        print(f">{args.well}")
        for i in range(0, len(seq), 80):
            print(seq[i:i+80])

    elif args.command == 'evaluate':
        import joblib
        model = joblib.load(args.model)
        seq, pos = basecall_well(model, args.well, use_esd_positions=not args.no_esd_positions)
        print(f"Called {len(seq)} bases")
        res = align_to_m13(seq)
        if res:
            print(f"RF M13: identity={res['identity']:.1f}% matches={res['matches']}/{res['alignment_length']}")
        else:
            print("Alignment failed")
        esd = parse_esd(os.path.join(BASE_DIR, ESD_DIR, f"{args.well}.esd"))
        cp_seq = esd.get('sequence', '')
        if cp_seq:
            res_cp = align_to_m13(cp_seq)
            if res_cp:
                print(f"Cp312 M13: identity={res_cp['identity']:.1f}%")

    elif args.command == 'batch':
        import joblib
        model = joblib.load(args.model)
        rows = [chr(ord('A')+i) for i in range(8)]
        cols = [f'{i:02d}' for i in range(1, 13)]
        all_wells = [f'{r}{c}' for r in rows for c in cols]
        results = {}
        for well in all_wells:
            rsd_path = os.path.join(BASE_DIR, f"{well}.rsd")
            if not os.path.exists(rsd_path):
                continue
            seq, _ = basecall_well(model, well)
            res = align_to_m13(seq)
            cp_seq = parse_esd(os.path.join(BASE_DIR, ESD_DIR, f"{well}.esd")).get('sequence', '')
            cp_res = align_to_m13(cp_seq) if cp_seq else None
            results[well] = {
                'rf_identity': res['identity'] if res else 0,
                'rf_length': res['alignment_length'] if res else 0,
                'cp312_identity': cp_res['identity'] if cp_res else 0,
            }
            sys.stdout.write(f"{well}: RF={results[well]['rf_identity']:.1f}% Cp312={results[well]['cp312_identity']:.1f}%\n")
            sys.stdout.flush()
        mean_rf = np.mean([r['rf_identity'] for r in results.values()])
        mean_cp = np.mean([r['cp312_identity'] for r in results.values()])
        print(f"\nMean RF: {mean_rf:.1f}%, Mean Cp312: {mean_cp:.1f}%")
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"Saved to {args.output}")

    else:
        parser.print_help()


if __name__ == '__main__':
    main()
