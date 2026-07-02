#!/usr/bin/env python3
"""End-to-end RF basecalling pipeline.

Usage:
  # Train model + evaluate on A01 using ESD positions:
  python rf_basecall.py train --wells A01-H12 --output rf_model.npz

  # Basecall a specific well:
  python rf_basecall.py basecall A01 --model rf_model.npz

  # Evaluate against M13:
  python rf_basecall.py evaluate A01 --model rf_model.npz
"""

import sys, os, argparse, json, time
import numpy as np
from sklearn.ensemble import RandomForestClassifier

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from extract_training_data import parse_rsd, parse_esd
from tracetuner_separation import trace_tuner_separate
from simple_align import align_to_m13

BASE_DIR = "/media/tv/78B0C7DE1FA7081C/electropherogram/MB1000_M13_DT"
ESD_DIR = "MB1000_M13_DT_Cp312_MD1"

WINDOW = 15
N_FEATURES = (WINDOW * 2 + 1) * 4
BASE_MAP = {'A': 0, 'C': 1, 'G': 2, 'T': 3, 'N': 4}
INV_MAP = {0: 'A', 1: 'C', 2: 'G', 3: 'T'}

RF_PARAMS = dict(n_estimators=500, max_depth=12, class_weight='balanced',
                 n_jobs=-1, random_state=42)


def get_wells(well_range):
    rows = [chr(ord('A') + i) for i in range(8)]
    cols = [f'{i:02d}' for i in range(1, 13)]
    all_wells = [f'{r}{c}' for r in rows for c in cols]
    start, end = well_range
    si = all_wells.index(start)
    ei = all_wells.index(end)
    if si > ei:
        si, ei = ei, si
    return all_wells[si:ei + 1]


def load_separate(well):
    rsd_path = os.path.join(BASE_DIR, f"{well}.rsd")
    df = parse_rsd(rsd_path)
    ch = df[['Channel1', 'Channel2', 'Channel3', 'Channel4']].values.T.astype(np.float64)
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
    windows = []
    valid_pos = []
    for p in positions:
        if p < WINDOW or p >= n - WINDOW:
            continue
        w = sep[:, p - WINDOW:p + WINDOW + 1].T
        windows.append(w)
        valid_pos.append(p)
    return np.array(windows, dtype=np.float32), np.array(valid_pos)


def train_model(wells):
    X_all, y_all = [], []
    for well in wells:
        sep = load_separate(well)
        sep_norm = per_well_zscore_trace(sep)
        esd = parse_esd(os.path.join(BASE_DIR, ESD_DIR, f"{well}.esd"))
        seq = esd.get('sequence', '')
        positions = esd.get('peak_positions')
        if positions is None:
            positions = esd.get('bases_positions')
        if not seq or positions is None:
            continue
        n = min(len(seq), len(positions))
        positions = positions[:n].astype(int)
        seq = seq[:n]
        X_w, pos_w = extract_windows(sep_norm, positions)
        y_w = np.array([BASE_MAP.get(b, 4) for b in seq])
        keep = y_w != 4
        X_all.append(X_w[keep])
        y_all.append(y_w[keep])
    if not X_all:
        return None
    X = np.concatenate(X_all, axis=0).reshape(-1, N_FEATURES)
    y = np.concatenate(y_all, axis=0)
    rf = RandomForestClassifier(**RF_PARAMS)
    rf.fit(X, y)
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
        detector = PeakDetector({'min_height': 100, 'prominence': 50})
        wd = detector.detect(df, df['Scan'])
        detected = wd.get('peaks')
        if detected is None:
            return '', np.array([])
        positions = detected.astype(int)

    X_w, valid_pos = extract_windows(sep_norm, positions)
    if len(X_w) == 0:
        return '', np.array([])

    pred = rf.predict(X_w.reshape(len(X_w), -1))
    seq = ''.join(INV_MAP.get(int(p), 'N') for p in pred)
    return seq, valid_pos


def main():
    parser = argparse.ArgumentParser(description="RF basecall pipeline")
    sub = parser.add_subparsers(dest='command')

    train_p = sub.add_parser('train', help='Train RF model')
    train_p.add_argument('--wells', nargs=2, default=['A01', 'H12'])
    train_p.add_argument('--output', default='rf_model.npz')

    call_p = sub.add_parser('basecall', help='Basecall a well')
    call_p.add_argument('well')
    call_p.add_argument('--model', default='rf_model.npz')
    call_p.add_argument('--no-esd-positions', action='store_true')

    eval_p = sub.add_parser('evaluate', help='Evaluate against M13')
    eval_p.add_argument('well', nargs='?', default='A01')
    eval_p.add_argument('--model', default='rf_model.npz')
    eval_p.add_argument('--no-esd-positions', action='store_true')

    args = parser.parse_args()

    if args.command == 'train':
        wells = get_wells(args.wells)
        print(f"Training RF on {len(wells)} wells...")
        t0 = time.time()
        model = train_model(wells)
        if model is None:
            print("No training data found!")
            sys.exit(1)
        import joblib
        joblib.dump(model, args.output)
        print(f"Model saved to {args.output} in {time.time()-t0:.0f}s")

    elif args.command == 'basecall':
        import joblib
        model = joblib.load(args.model)
        seq, pos = basecall_well(model, args.well, use_esd_positions=not args.no_esd_positions)
        print(f">{args.well}")
        for i in range(0, len(seq), 80):
            print(seq[i:i+80])
        print(f"\n{len(seq)} bases")

    elif args.command == 'evaluate':
        import joblib
        model = joblib.load(args.model)
        print(f"Basecalling {args.well}...")
        seq, pos = basecall_well(model, args.well, use_esd_positions=not args.no_esd_positions)
        print(f"Called {len(seq)} bases (using {'ESD' if not args.no_esd_positions else 'peak detector'} positions)")
        res = align_to_m13(seq)
        if res:
            print(f"M13 identity: {res['identity']:.1f}%")
            print(f"  Matches: {res['matches']}/{res['alignment_length']}")
        else:
            print("Alignment failed")

        # Cp312 baseline
        esd = parse_esd(os.path.join(BASE_DIR, ESD_DIR, f"{args.well}.esd"))
        cp_seq = esd.get('sequence', '')[:len(seq)]
        if cp_seq:
            res_cp = align_to_m13(cp_seq)
            if res_cp:
                print(f"Cp312 identity: {res_cp['identity']:.1f}%")

    else:
        parser.print_help()


if __name__ == '__main__':
    main()
