"""Extract labeled training pairs from .rsd + .esd files.

Pairs .rsd raw trace files with .esd base-calling reference outputs
for all 6 base caller variants across any number of wells (96 or 384).
Produces .npz files for ML training.

Usage:
  # MB1000 (96-well, 6 variants):
  python extract_training_data.py

  # MB4000 (384-well, Cp312 only):
  python extract_training_data.py \
      --data-dir "/media/per/.../MB4000_DEMO_DATA" \
      --esd-dirs Cp312=MB4000_demo_data_Cp312_MD1 \
      --rows 16 --cols 24 --wells A01 A24 \
      --output training_data_mb4000
"""
import sys, os, struct, argparse
import numpy as np
import pandas as pd

# Default: MB1000 (96-well, all 6 variants)
DEFAULT_BASE_DIR = "/media/per/Disk 2/electropherogram/MB1000_M13_DT"
DEFAULT_ESD_DIRS = {
    'Cp312': 'MB1000_M13_DT_Cp312_MD1',
    'Cp312_a': 'MB1000_M13_DT_Cp312_a_MD1',
    'Cp312_es': 'MB1000_M13_DT_Cp312_es_MD1',
    'Cp1_530': 'MB1000_M13_DT_Cp1_530_MD1',
    'Cp1_530_sl_ph': 'MB1000_M13_DT_Cp1_530_sl_ph_MD1',
    'MD': 'MB1000_M13_DT_M_MD1',
}


def parse_rsd(path):
    """Parse .rsd -> DataFrame with Scan, Channel1-4, Current."""
    with open(path, 'rb') as f:
        raw = f.read()
    records = []
    for i in range(0, len(raw) - 19, 20):
        v = struct.unpack('<IIIII', raw[i:i + 20])
        records.append(v)
    MAX_CHANNEL_VALUE = 5000
    boundary = len(records)
    for i, rec in enumerate(records):
        if any(v > MAX_CHANNEL_VALUE for v in rec):
            boundary = i
            break
    data = records[:boundary]
    df = pd.DataFrame(data, columns=['Current', 'Channel1', 'Channel2', 'Channel3', 'Channel4'])
    df['Scan'] = np.arange(len(df))
    return df[['Scan', 'Channel1', 'Channel2', 'Channel3', 'Channel4', 'Current']]


def parse_esd(path):
    """Parse .esd -> dict with sequence, base_positions, quality_scores, etc."""
    with open(path, 'rb') as f:
        raw = f.read()
    result = {}

    # SEQUENCE  (type 0x06 with 2-byte length, or type 0x05 with 1-byte length)
    idx = -1
    while True:
        idx = raw.find(b'SEQUENCE', idx + 1)
        if idx < 0:
            break
        null_pos = idx + 8
        if null_pos + 3 >= len(raw) or raw[null_pos] != 0:
            continue
        type_b = raw[null_pos + 1]
        lo = raw[null_pos + 2]
        hi = raw[null_pos + 3]
        if type_b == 0x06 and 100 < (lo + (hi << 8)) < 5000:
            length = lo + (hi << 8)
            data_start = null_pos + 4
        elif type_b == 0x05 and 100 < lo < 1000:
            length = lo
            data_start = null_pos + 3
        else:
            continue
        seq_bytes = raw[data_start:data_start + length]
        seq = seq_bytes.decode('ascii', errors='replace')
        seq_clean = ''.join(c for c in seq if c in 'ACGTNacgtn').upper()
        result['sequence'] = seq_clean
        result['sequence_raw'] = seq
        break

    # Metadata strings (type 0x05)
    for lbl in ['SAMPLE NAME', 'WELL ID', 'CHEMISTRY', 'DYE SET',
                'PLATE ID', 'INSTRUMENT', 'BAR CODE']:
        idx = raw.find(lbl.encode())
        if idx < 0:
            continue
        null_pos = idx + len(lbl)
        if null_pos + 3 >= len(raw) or raw[null_pos] != 0:
            continue
        if raw[null_pos + 1] != 0x05:
            continue
        val_len = raw[null_pos + 2]
        val = raw[null_pos + 3:null_pos + 3 + val_len].decode('ascii', errors='replace')
        result[lbl.lower().replace(' ', '_')] = val

    # Numeric arrays - prefer PEAK POSITIONS over BASES POSITIONS
    numeric_labels = ['PEAK POSITIONS', 'BASES POSITIONS',
                      'QUALITY SCORES', 'QUALITY INDEX',
                      'FWHM VALUES', 'SPACING']
    seen_keys = set()
    for lbl in numeric_labels:
        idx = raw.find(lbl.encode())
        if idx < 0:
            continue
        null_pos = idx + len(lbl)
        if null_pos + 3 >= len(raw) or raw[null_pos] != 0:
            continue
        lo = raw[null_pos + 2]
        hi = raw[null_pos + 3]
        length = lo + (hi << 8)
        data = raw[null_pos + 4:null_pos + 4 + length]
        if len(data) % 4 != 0 or len(data) == 0:
            continue
        key = lbl.lower().replace(' ', '_')
        if key in seen_keys:
            continue  # Already got a better match (PEAK > BASES)
        if lbl in ('PEAK POSITIONS', 'BASES POSITIONS'):
            as_int = struct.unpack('<I', data[:4])[0]
            if 100 < as_int < 100000:
                result[key] = np.frombuffer(data, dtype=np.uint32).copy()
            else:
                result[key] = np.frombuffer(data, dtype=np.float32).copy()
        else:
            result[key] = np.frombuffer(data, dtype=np.float32).copy()
        seen_keys.add(key)

    return result


def extract_training_well(well, variant, esd_folder, base_dir, window=15):
    """Extract labeled training data for one well + variant.

    Returns:
        X: ndarray (N_bases, window*2+1, 4)  -- channel signals around each base
        y: ndarray (N_bases,) -- 0=A,1=C,2=G,3=T,4=N
        positions: ndarray (N_bases,) -- scan positions
        quality: ndarray (N_bases,) -- quality scores
    """
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

    # Trim to shortest array
    n_bases = min(len(seq), len(positions), len(quality))
    if n_bases == 0:
        return None, None, None, None

    seq = seq[:n_bases]
    positions = positions[:n_bases].astype(int)
    quality = quality[:n_bases]

    ch = df[['Channel1', 'Channel2', 'Channel3', 'Channel4']].values
    n_scans = len(ch)

    # Extract windows around each base position
    X = []
    y = []
    valid_positions = []
    valid_quality = []
    base_map = {'A': 0, 'C': 1, 'G': 2, 'T': 3, 'N': 4}

    for i, pos in enumerate(positions):
        if pos < window or pos >= n_scans - window:
            continue
        window_data = ch[pos - window:pos + window + 1, :]
        X.append(window_data)
        y.append(base_map.get(seq[i], 4))
        valid_positions.append(pos)
        valid_quality.append(quality[i])

    if not X:
        return None, None, None, None

    return (np.array(X, dtype=np.float32),
            np.array(y, dtype=np.uint8),
            np.array(valid_positions, dtype=np.uint32),
            np.array(valid_quality, dtype=np.float32))


def run_extraction(base_dir, esd_dirs, variants, wells, window, output_dir):
    """Run extraction for one dataset configuration."""
    os.makedirs(output_dir, exist_ok=True)

    print(f"Extracting {len(wells)} wells from {base_dir}")
    print(f"  Window: {window} pts ({window * 2 + 1} total)")
    print(f"  Variants: {', '.join(variants)}")

    total_positions = 0
    well_data = {}

    for well in wells:
        well_data[well] = {}
        for variant in variants:
            esd_folder = esd_dirs[variant]
            X, y, pos, qual = extract_training_well(
                well, variant, esd_folder, base_dir, window=window)
            if X is not None:
                well_data[well][variant] = {'X': X, 'y': y, 'positions': pos, 'quality': qual}
                total_positions += len(y)

    print(f"  Total: {total_positions} positions")

    # Save per-variant .npz files
    for variant in variants:
        X_list, y_list, pos_list, qual_list, well_list = [], [], [], [], []
        for well in wells:
            if variant in well_data.get(well, {}):
                d = well_data[well][variant]
                X_list.append(d['X'])
                y_list.append(d['y'])
                pos_list.append(d['positions'])
                qual_list.append(d['quality'])
                well_list.extend([well] * len(d['y']))

        if not X_list:
            print(f"    {variant}: no data")
            continue

        X_all = np.concatenate(X_list, axis=0)
        y_all = np.concatenate(y_list, axis=0)
        pos_all = np.concatenate(pos_list, axis=0)
        qual_all = np.concatenate(qual_list, axis=0)

        path = os.path.join(output_dir, f"{variant}.npz")
        np.savez_compressed(path,
                            X=X_all, y=y_all,
                            positions=pos_all,
                            quality=qual_all,
                            wells=np.array(well_list, dtype=object))
        n_total = len(y_all)
        n_A = int((y_all == 0).sum())
        n_C = int((y_all == 1).sum())
        n_G = int((y_all == 2).sum())
        n_T = int((y_all == 3).sum())
        n_N = int((y_all == 4).sum())
        print(f"    {variant}: {n_total} pos ({n_A}A/{n_C}C/{n_G}G/{n_T}T/{n_N}N), "
              f"X {X_all.shape}, Qmean {qual_all.mean():.1f}")

    # Merged dataset
    merged_X, merged_y, merged_pos, merged_qual, merged_var, merged_well = [], [], [], [], [], []
    for well in wells:
        for variant in variants:
            if variant in well_data.get(well, {}):
                d = well_data[well][variant]
                merged_X.append(d['X'])
                merged_y.append(d['y'])
                merged_pos.append(d['positions'])
                merged_qual.append(d['quality'])
                merged_var.extend([variant] * len(d['y']))
                merged_well.extend([well] * len(d['y']))

    if merged_X:
        path = os.path.join(output_dir, "all_variants.npz")
        np.savez_compressed(path,
                            X=np.concatenate(merged_X, axis=0),
                            y=np.concatenate(merged_y, axis=0),
                            positions=np.concatenate(merged_pos, axis=0),
                            quality=np.concatenate(merged_qual, axis=0),
                            variant=np.array(merged_var, dtype=object),
                            well=np.array(merged_well, dtype=object))
        print(f"    Merged (all): {sum(len(x) for x in merged_X)} positions")

    return total_positions


def main():
    parser = argparse.ArgumentParser(description="Extract labeled training pairs from .rsd + .esd")
    parser.add_argument('--wells', nargs=2, default=['A01', 'H12'],
                        help='Well range (e.g., A01 H12)')
    parser.add_argument('--window', type=int, default=15,
                        help='Window radius around each base (default 15 = 31 pts)')
    parser.add_argument('--output', default='training_data',
                        help='Output directory for .npz files')
    parser.add_argument('--data-dir', default=DEFAULT_BASE_DIR,
                        help='Root directory containing .rsd and .esd folders')
    parser.add_argument('--esd-dirs', nargs='+', default=[],
                        help='ESD folder mappings: Variant=folder_name (overrides defaults for --data-dir)')
    parser.add_argument('--rows', type=int, default=8,
                        help='Number of rows in plate (default 8 for 96-well)')
    parser.add_argument('--cols', type=int, default=12,
                        help='Number of columns in plate (default 12 for 96-well)')
    args = parser.parse_args()

    # Determine ESD folder config
    if args.esd_dirs:
        esd_dirs = {}
        for kv in args.esd_dirs:
            k, v = kv.split('=', 1)
            esd_dirs[k] = v
    elif args.data_dir == DEFAULT_BASE_DIR:
        esd_dirs = DEFAULT_ESD_DIRS.copy()
    else:
        # No explicit config and not the default path — user must specify
        print("Error: --esd-dirs required for non-default --data-dir")
        print("Example: --esd-dirs Cp312=MB4000_demo_data_Cp312_MD1")
        sys.exit(1)

    variants = list(esd_dirs.keys())

    # Generate well list
    rows = [chr(ord('A') + i) for i in range(args.rows)]
    cols = [f'{i:02d}' for i in range(1, args.cols + 1)]
    all_wells = [f'{r}{c}' for r in rows for c in cols]

    # Restrict to range
    start_idx = all_wells.index(args.wells[0])
    end_idx = all_wells.index(args.wells[1])
    if start_idx > end_idx:
        start_idx, end_idx = end_idx, start_idx
    wells = all_wells[start_idx:end_idx + 1]

    # Run extraction
    run_extraction(args.data_dir, esd_dirs, variants, wells,
                   args.window, args.output)

    print(f"\nDone. Output in '{args.output}/'")
    print(f"  Files: {[f'{v}.npz' for v in variants]} + all_variants.npz")


if __name__ == '__main__':
    main()
