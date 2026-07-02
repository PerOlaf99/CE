"""Extract labeled training windows from TraceTuner-separated traces.
Applies spectral separation first, then extracts 31x4 windows at ESD peak positions."""
import sys, os, argparse, time
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from extract_training_data import parse_rsd, parse_esd, DEFAULT_BASE_DIR, DEFAULT_ESD_DIRS
from tracetuner_separation import trace_tuner_separate


def extract_separated_well(well, variant, esd_folder, base_dir, window=15):
    rsd_path = os.path.join(base_dir, f"{well}.rsd")
    esd_path = os.path.join(base_dir, esd_folder, f"{well}.esd")
    if not os.path.exists(rsd_path) or not os.path.exists(esd_path):
        return None, None, None, None

    try:
        df = parse_rsd(rsd_path)
    except Exception:
        return None, None, None, None
    try:
        esd = parse_esd(esd_path)
    except Exception:
        return None, None, None, None

    seq = esd.get('sequence', '')
    positions = esd.get('peak_positions')
    if positions is None:
        positions = esd.get('bases_positions')
    quality = esd.get('quality_scores')
    if not seq or positions is None or quality is None:
        return None, None, None, None

    n_bases = min(len(seq), len(positions), len(quality))
    if n_bases == 0:
        return None, None, None, None

    seq = seq[:n_bases]
    positions = positions[:n_bases].astype(int)
    quality = quality[:n_bases]

    ch = df[['Channel1', 'Channel2', 'Channel3', 'Channel4']].values.T.astype(np.float64)
    separated = trace_tuner_separate(ch)

    n_scans = separated.shape[1]
    X, y, valid_positions, valid_quality = [], [], [], []
    base_map = {'A': 0, 'C': 1, 'G': 2, 'T': 3, 'N': 4}

    for i, pos in enumerate(positions):
        if pos < window or pos >= n_scans - window:
            continue
        window_data = separated[:, pos - window:pos + window + 1]
        X.append(window_data.T)
        y.append(base_map.get(seq[i], 4))
        valid_positions.append(pos)
        valid_quality.append(quality[i])

    if not X:
        return None, None, None, None

    return (np.array(X, dtype=np.float32),
            np.array(y, dtype=np.uint8),
            np.array(valid_positions, dtype=np.uint32),
            np.array(valid_quality, dtype=np.float32))


def main():
    parser = argparse.ArgumentParser(description="Extract training windows from separated traces")
    parser.add_argument('--wells', nargs=2, default=['A01', 'H12'],
                        help='Well range (e.g., A01 H12)')
    parser.add_argument('--window', type=int, default=15,
                        help='Window radius (default 15 = 31 pts)')
    parser.add_argument('--output', default='training_data_separated',
                        help='Output directory for .npz files')
    parser.add_argument('--data-dir', default=DEFAULT_BASE_DIR,
                        help='Root directory containing .rsd and .esd folders')
    parser.add_argument('--esd-dirs', nargs='+', default=[],
                        help='ESD folder mappings: Variant=folder_name')
    parser.add_argument('--rows', type=int, default=8,
                        help='Plate rows (default 8)')
    parser.add_argument('--cols', type=int, default=12,
                        help='Plate columns (default 12)')
    args = parser.parse_args()

    if args.esd_dirs:
        esd_dirs = {}
        for kv in args.esd_dirs:
            k, v = kv.split('=', 1)
            esd_dirs[k] = v
    elif args.data_dir == DEFAULT_BASE_DIR:
        esd_dirs = DEFAULT_ESD_DIRS.copy()
    else:
        print("Error: --esd-dirs required for non-default --data-dir")
        sys.exit(1)

    variants = list(esd_dirs.keys())
    rows = [chr(ord('A') + i) for i in range(args.rows)]
    cols = [f'{i:02d}' for i in range(1, args.cols + 1)]
    all_wells = [f'{r}{c}' for r in rows for c in cols]

    start_idx = all_wells.index(args.wells[0])
    end_idx = all_wells.index(args.wells[1])
    if start_idx > end_idx:
        start_idx, end_idx = end_idx, start_idx
    wells = all_wells[start_idx:end_idx + 1]

    os.makedirs(args.output, exist_ok=True)

    print(f"Extracting {len(wells)} wells from {args.data_dir}")
    print(f"  Variants: {', '.join(variants)}")
    print(f"  Window: {args.window} pts ({args.window * 2 + 1} total)")
    print(f"  Output: {args.output}/")

    # Per-variant accumulation
    variant_data = {v: {'X': [], 'y': [], 'pos': [], 'qual': [], 'well': []}
                    for v in variants}
    merged_X, merged_y, merged_pos, merged_qual, merged_var, merged_well = \
        [], [], [], [], [], []

    t_start = time.time()
    for wi, well in enumerate(wells):
        t_w = time.time()
        for variant in variants:
            esd_folder = esd_dirs[variant]
            result = extract_separated_well(well, variant, esd_folder,
                                            args.data_dir, window=args.window)
            if result is None or result[0] is None:
                continue
            X, y, pos, qual = result
            d = variant_data[variant]
            d['X'].append(X)
            d['y'].append(y)
            d['pos'].append(pos)
            d['qual'].append(qual)
            d['well'].extend([well] * len(y))

            merged_X.append(X)
            merged_y.append(y)
            merged_pos.append(pos)
            merged_qual.append(qual)
            merged_var.extend([variant] * len(y))
            merged_well.extend([well] * len(y))

        elapsed = time.time() - t_w
        print(f"  [{wi + 1}/{len(wells)}] {well}: {elapsed:.1f}s", flush=True)

    # Save per-variant
    for variant in variants:
        d = variant_data[variant]
        if not d['X']:
            print(f"    {variant}: no data")
            continue
        X_all = np.concatenate(d['X'], axis=0)
        y_all = np.concatenate(d['y'], axis=0)
        pos_all = np.concatenate(d['pos'], axis=0)
        qual_all = np.concatenate(d['qual'], axis=0)

        path = os.path.join(args.output, f"{variant}.npz")
        np.savez_compressed(path,
                            X=X_all, y=y_all,
                            positions=pos_all,
                            quality=qual_all,
                            wells=np.array(d['well'], dtype=object))
        n = len(y_all)
        print(f"    {variant}: {n} positions, X {X_all.shape}")

    # Merged
    if merged_X:
        path = os.path.join(args.output, "all_variants.npz")
        np.savez_compressed(path,
                            X=np.concatenate(merged_X, axis=0),
                            y=np.concatenate(merged_y, axis=0),
                            positions=np.concatenate(merged_pos, axis=0),
                            quality=np.concatenate(merged_qual, axis=0),
                            variant=np.array(merged_var, dtype=object),
                            well=np.array(merged_well, dtype=object))
        print(f"    Merged: {len(merged_y)} positions")

    total = sum(len(d['y']) for d in variant_data.values())
    print(f"\nDone in {time.time() - t_start:.0f}s. Total: {total} positions.")


if __name__ == '__main__':
    main()
