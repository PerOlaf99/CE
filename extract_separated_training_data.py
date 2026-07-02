"""Extract labeled training windows from TraceTuner-separated traces.
Separates once per well, then extracts windows for all variants."""
import sys, os, argparse, time
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from extract_training_data import parse_rsd, parse_esd, DEFAULT_BASE_DIR, DEFAULT_ESD_DIRS
from tracetuner_separation import trace_tuner_separate


def extract_well_variants(well, variants_data, base_dir, window=15):
    """Separate traces once, extract windows for all variants."""
    rsd_path = os.path.join(base_dir, f"{well}.rsd")
    if not os.path.exists(rsd_path):
        return None

    try:
        df = parse_rsd(rsd_path)
    except Exception:
        return None

    ch = df[['Channel1', 'Channel2', 'Channel3', 'Channel4']].values.T.astype(np.float64)
    separated = trace_tuner_separate(ch)
    n_scans = separated.shape[1]

    results = {}
    base_map = {'A': 0, 'C': 1, 'G': 2, 'T': 3, 'N': 4}

    for variant, esd_folder in variants_data:
        esd_path = os.path.join(base_dir, esd_folder, f"{well}.esd")
        if not os.path.exists(esd_path):
            continue
        try:
            esd = parse_esd(esd_path)
        except Exception:
            continue

        seq = esd.get('sequence', '')
        positions = esd.get('peak_positions')
        if positions is None:
            positions = esd.get('bases_positions')
        quality = esd.get('quality_scores')
        if not seq or positions is None or quality is None:
            continue

        n_bases = min(len(seq), len(positions), len(quality))
        if n_bases == 0:
            continue

        seq = seq[:n_bases]
        positions = positions[:n_bases].astype(int)
        quality = quality[:n_bases]

        X, y, pos_list, qual_list = [], [], [], []
        for i, pos in enumerate(positions):
            if pos < window or pos >= n_scans - window:
                continue
            win = separated[:, pos - window:pos + window + 1]
            X.append(win.T)
            y.append(base_map.get(seq[i], 4))
            pos_list.append(pos)
            qual_list.append(quality[i])

        if X:
            results[variant] = {
                'X': np.array(X, dtype=np.float32),
                'y': np.array(y, dtype=np.uint8),
                'positions': np.array(pos_list, dtype=np.uint32),
                'quality': np.array(qual_list, dtype=np.float32),
            }

    return results


def main():
    parser = argparse.ArgumentParser(description="Extract separated training windows")
    parser.add_argument('--wells', nargs=2, default=['A01', 'H12'],
                        help='Well range (e.g., A01 H12)')
    parser.add_argument('--window', type=int, default=15,
                        help='Window radius (default 15 = 31 pts)')
    parser.add_argument('--output', default='training_data_separated',
                        help='Output directory')
    parser.add_argument('--data-dir', default=DEFAULT_BASE_DIR)
    parser.add_argument('--esd-dirs', nargs='+', default=[])
    parser.add_argument('--rows', type=int, default=8)
    parser.add_argument('--cols', type=int, default=12)
    args = parser.parse_args()

    if args.esd_dirs:
        esd_dirs = {kv.split('=', 1)[0]: kv.split('=', 1)[1] for kv in args.esd_dirs}
    elif args.data_dir == DEFAULT_BASE_DIR:
        esd_dirs = DEFAULT_ESD_DIRS.copy()
    else:
        print("Error: --esd-dirs required")
        sys.exit(1)

    data_dir = args.data_dir
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

    variant_data = {v: {'X': [], 'y': [], 'pos': [], 'qual': [], 'well': []}
                    for v in variants}
    merged_X, merged_y = [], []
    merged_var, merged_well = [], []

    t_start = time.time()
    for wi, well in enumerate(wells):
        t_w = time.time()
        results = extract_well_variants(
            well, list(esd_dirs.items()), data_dir, window=args.window)
        elapsed = time.time() - t_w

        if results:
            msg = f'  [{wi+1}/{len(wells)}] {well}: {elapsed:.0f}s'
            for variant, d in results.items():
                vd = variant_data[variant]
                vd['X'].append(d['X'])
                vd['y'].append(d['y'])
                vd['pos'].append(d['positions'])
                vd['qual'].append(d['quality'])
                vd['well'].extend([well] * len(d['y']))
                merged_X.append(d['X'])
                merged_y.append(d['y'])
                merged_var.extend([variant] * len(d['y']))
                merged_well.extend([well] * len(d['y']))
                msg += f' {variant}={len(d["y"])}'
            print(msg, flush=True)
        else:
            print(f'  [{wi+1}/{len(wells)}] {well}: {elapsed:.0f}s (no data)', flush=True)

    # Save per-variant
    for variant in variants:
        d = variant_data[variant]
        if not d['X']:
            print(f'    {variant}: no data')
            continue
        X_all = np.concatenate(d['X'], axis=0)
        y_all = np.concatenate(d['y'], axis=0)
        pos_all = np.concatenate(d['pos'], axis=0)
        qual_all = np.concatenate(d['qual'], axis=0)

        path = os.path.join(args.output, f'{variant}.npz')
        np.savez_compressed(path, X=X_all, y=y_all,
                            positions=pos_all, quality=qual_all,
                            wells=np.array(d['well'], dtype=object))
        print(f'    {variant}: {len(y_all)} positions, X {X_all.shape}')

    # Merged
    if merged_X:
        path = os.path.join(args.output, 'all_variants.npz')
        np.savez_compressed(path,
                            X=np.concatenate(merged_X, axis=0),
                            y=np.concatenate(merged_y, axis=0),
                            variant=np.array(merged_var, dtype=object),
                            well=np.array(merged_well, dtype=object))
        print(f'    Merged: {len(merged_y)} positions')

    total = sum(len(d['y']) for d in variant_data.values())
    print(f'\nDone in {time.time()-t_start:.0f}s. Total: {total} positions.')


if __name__ == '__main__':
    main()
