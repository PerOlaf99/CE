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

from peak_detector import PeakDetector

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
    MAX_DATA_VALUE = 200000  # metadata values are in the billions
    boundary = len(records)
    for i, rec in enumerate(records):
        if any(v > MAX_DATA_VALUE for v in rec):
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
    """Extract labeled training data for one well + variant (original mode).

    Returns:
        X: ndarray (N_bases, window*2+1, 4)
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

    n_bases = min(len(seq), len(positions), len(quality))
    if n_bases == 0:
        return None, None, None, None

    seq = seq[:n_bases]
    positions = positions[:n_bases].astype(int)
    quality = quality[:n_bases]

    ch = df[['Channel1', 'Channel2', 'Channel3', 'Channel4']].values
    n_scans = len(ch)

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


def extract_training_well_matched(well, variant, esd_folder, base_dir, window=15,
                                  match_tolerance=5, detector_params=None):
    """Extract labeled training data, centering windows on classic peak detector positions.

    For each ESD base, finds the nearest classic-detected peak. If within
    match_tolerance scans, uses that peak position as the window center.
    This eliminates train/inference position mismatch.

    Returns:
        Same as extract_training_well, but positions are detector-matched.
    """
    from peak_detector import PeakDetector

    rsd_path = os.path.join(base_dir, f"{well}.rsd")
    esd_path = os.path.join(base_dir, esd_folder, f"{well}.esd")
    if not os.path.exists(rsd_path) or not os.path.exists(esd_path):
        return None, None, None, None, None

    try:
        df = parse_rsd(rsd_path)
    except Exception:
        return None, None, None, None, None

    try:
        esd = parse_esd(esd_path)
    except Exception:
        return None, None, None, None, None

    seq = esd.get('sequence', '')
    esd_positions = esd.get('peak_positions')
    if esd_positions is None:
        esd_positions = esd.get('bases_positions')
    quality = esd.get('quality_scores')

    if not seq or esd_positions is None or quality is None:
        return None, None, None, None, None

    n_bases = min(len(seq), len(esd_positions), len(quality))
    if n_bases == 0:
        return None, None, None, None, None

    seq = seq[:n_bases]
    esd_positions = esd_positions[:n_bases].astype(int)
    quality = quality[:n_bases]

    # Run classic peak detector on all 4 channels
    params = dict(detector_params or {})
    params.setdefault('active_channels', {
        'Channel1': True, 'Channel2': True,
        'Channel3': True, 'Channel4': True, 'Current': False,
    })
    detector = PeakDetector(params)
    wd = detector.detect(df, df['Scan'])
    detected_peaks = wd['peaks']

    ch = df[['Channel1', 'Channel2', 'Channel3', 'Channel4']].values
    n_scans = len(ch)
    base_map = {'A': 0, 'C': 1, 'G': 2, 'T': 3, 'N': 4}

    X, y, valid_positions, valid_quality = [], [], [], []
    match_stats = {'matched': 0, 'unmatched': 0, 'avg_offset': 0.0}
    offsets = []

    for i, esd_pos in enumerate(esd_positions):
        if detected_peaks is None or len(detected_peaks) == 0:
            match_stats['unmatched'] += 1
            continue
        dist = np.abs(detected_peaks.astype(float) - esd_pos)
        closest_idx = np.argmin(dist)
        offset = int(detected_peaks[closest_idx] - esd_pos)
        if dist[closest_idx] <= match_tolerance:
            center = int(detected_peaks[closest_idx])
            match_stats['matched'] += 1
            offsets.append(offset)
        else:
            # Fall back to ESD position if no detector peak nearby
            center = esd_pos
            match_stats['unmatched'] += 1

        if center < window or center >= n_scans - window:
            continue
        window_data = ch[center - window:center + window + 1, :]
        X.append(window_data)
        y.append(base_map.get(seq[i], 4))
        valid_positions.append(center)
        valid_quality.append(quality[i])

    if offsets:
        match_stats['avg_offset'] = np.mean(offsets)
        match_stats['std_offset'] = np.std(offsets)

    if not X:
        return None, None, None, None, match_stats

    return (np.array(X, dtype=np.float32),
            np.array(y, dtype=np.uint8),
            np.array(valid_positions, dtype=np.uint32),
            np.array(valid_quality, dtype=np.float32),
            match_stats)


def _build_consensus_labels(well_data, variants):
    """Build consensus labels: keep only positions where >= min_vote callers agree."""
    if not well_data:
        return {}, {}
    n_wells = len(well_data)

    # For each well, find common positions across variants (within tolerance)
    # and record what each caller says at each position
    consensus_data = {}  # variant -> {X, y, positions, quality}

    # Build per-well position→caller_vote maps
    for well in well_data:
        # Collect all positions and their call assignments
        all_positions = []
        pos_to_votes = {}  # position -> {variant: base}

        for variant in variants:
            if variant not in well_data[well]:
                continue
            d = well_data[well][variant]
            for pos, base in zip(d['positions'], d['y']):
                if pos not in pos_to_votes:
                    pos_to_votes[pos] = {}
                    all_positions.append(pos)
                pos_to_votes[pos][variant] = base

        # Only keep positions where the majority of callers that have data agree
        # A "vote" is the base called at that position
        for pos in all_positions:
            votes = pos_to_votes[pos]
            base_counts = {}
            for v in variants:
                if v in votes:
                    b = int(votes[v])
                    base_counts.setdefault(b, 0)
                    base_counts[b] += 1
            if not base_counts:
                continue
            best_base = max(base_counts, key=base_counts.get)
            total_votes = sum(base_counts.values())
            consensus = best_base
            agreement = base_counts[best_base]
            # Store consensus info: position is kept if any caller has it
            # (we're just annotating, not filtering by agreement here)
            if pos not in pos_to_votes:
                pos_to_votes[pos] = {}
            pos_to_votes[pos]['_consensus'] = int(consensus)
            pos_to_votes[pos]['_agreement'] = agreement
            pos_to_votes[pos]['_total_votes'] = total_votes

    # Now annotate each variant's data with consensus info
    # and filter to where >= min_consensus agree
    return pos_to_votes


def _filter_consensus_variant(d, pos_to_votes, min_consensus):
    """Filter a variant's data to positions meeting consensus threshold."""
    if d is None:
        return None
    keep = []
    for i, pos in enumerate(d['positions']):
        pos = int(pos)
        if pos in pos_to_votes:
            info = pos_to_votes[pos]
            if info.get('_agreement', 0) >= min_consensus:
                keep.append(i)
    if not keep:
        return None
    keep = np.array(keep)
    return {
        'X': d['X'][keep],
        'y': d['y'][keep],
        'positions': d['positions'][keep],
        'quality': d['quality'][keep],
    }


def _sample_background(ch, esd_positions, n_positive, window=15,
                       margin=5, ratio=1.0, rng=None):
    """Sample background (non-ESD) positions as negative training examples.

    Randomly selects scan positions that are at least `margin` scans away
    from any ESD position. Returns windows labeled as class 4 (N/bakground).
    
    Args:
        ch: (n_scans, 4) channel data array
        esd_positions: array of ESD peak positions
        n_positive: number of positive examples (controls sample count)
        window: window radius (must match model input)
        margin: min distance from any ESD position (default 5)
        ratio: background examples as fraction of n_positive (default 1.0)
        rng: numpy RandomState for reproducibility
    Returns:
        X_bg: (n, window*2+1, 4) background windows
        y_bg: (n,) array of 4 (N class)
        qual_bg: (n,) array of zeros
    """
    if rng is None:
        rng = np.random.RandomState(42)
    
    n_scans = len(ch)
    n_bg = int(n_positive * ratio)
    if n_bg == 0:
        return None, None, None
    
    # Mark positions forbidden (too close to ESD)
    forbidden = np.zeros(n_scans, dtype=bool)
    for pos in esd_positions:
        lo = max(0, int(pos) - window - margin)
        hi = min(n_scans, int(pos) + window + margin + 1)
        forbidden[lo:hi] = True
    
    # Also forbid edges (can't extract a window)
    forbidden[:window] = True
    forbidden[-window:] = True
    
    valid = np.where(~forbidden)[0]
    if len(valid) == 0:
        return None, None, None
    
    sampled = rng.choice(valid, size=min(n_bg, len(valid)), replace=False)
    sampled.sort()
    
    X_bg = np.array([ch[p - window:p + window + 1] for p in sampled], dtype=np.float32)
    y_bg = np.full(len(sampled), 4, dtype=np.uint8)
    qual_bg = np.zeros(len(sampled), dtype=np.float32)
    
    return X_bg, y_bg, qual_bg


def run_extraction(base_dir, esd_dirs, variants, wells, window, output_dir,
                   match_peaks=False, match_tolerance=5, min_consensus=0,
                   detector_params=None, include_background=False,
                   background_ratio=1.0):
    """Run extraction for one dataset configuration.

    Args:
        match_peaks: If True, center windows on classic detector peaks instead of ESD positions.
        match_tolerance: Max scan distance between ESD and detector position.
        min_consensus: Minimum number of callers that must agree (0=no filtering).
    """
    os.makedirs(output_dir, exist_ok=True)

    print(f"Extracting {len(wells)} wells from {base_dir}")
    print(f"  Window: {window} pts ({window * 2 + 1} total)")
    print(f"  Variants: {', '.join(variants)}")
    print(f"  Mode: {'peak-matched' if match_peaks else 'ESD-centered'}")
    if match_peaks:
        print(f"  Match tolerance: {match_tolerance} scans")
    if min_consensus > 0:
        print(f"  Consensus filter: >= {min_consensus} callers agree")

    total_positions = 0
    well_data = {}
    all_match_stats = []

    for well in wells:
        well_data[well] = {}
        for variant in variants:
            esd_folder = esd_dirs[variant]
            if match_peaks:
                result = extract_training_well_matched(
                    well, variant, esd_folder, base_dir,
                    window=window, match_tolerance=match_tolerance,
                    detector_params=detector_params)
                if result and len(result) == 5:
                    X, y, pos, qual, stats = result
                    if stats:
                        all_match_stats.append(stats)
                else:
                    X, y, pos, qual = None, None, None, None
            else:
                X, y, pos, qual = extract_training_well(
                    well, variant, esd_folder, base_dir, window=window)

            if X is not None:
                # Add background samples if requested
                if include_background:
                    try:
                        bg_df = parse_rsd(os.path.join(base_dir, f"{well}.rsd"))
                        bg_ch = bg_df[['Channel1','Channel2','Channel3','Channel4']].values
                        # Get ESD positions for this variant
                        bg_esd = parse_esd(os.path.join(base_dir, esd_folder, f"{well}.esd"))
                        bg_positions = bg_esd.get('peak_positions')
                        if bg_positions is None:
                            bg_positions = bg_esd.get('bases_positions')
                        if bg_positions is not None:
                            X_bg, y_bg, qual_bg = _sample_background(
                                bg_ch, bg_positions, len(y),
                                window=window, ratio=background_ratio)
                            if X_bg is not None:
                                # Append background to positive samples
                                X = np.concatenate([X, X_bg], axis=0)
                                y = np.concatenate([y, y_bg], axis=0)
                                pos = np.concatenate([pos, np.full(len(X_bg), 0)])
                                qual = np.concatenate([qual, qual_bg])
                    except Exception:
                        pass
                well_data[well][variant] = {'X': X, 'y': y, 'positions': pos, 'quality': qual}
                total_positions += len(y)

    # Report match stats
    if all_match_stats:
        avg_match = np.mean([s['matched'] for s in all_match_stats]) if all_match_stats else 0
        avg_unmatch = np.mean([s['unmatched'] for s in all_match_stats]) if all_match_stats else 0
        avg_offset = np.mean([s['avg_offset'] for s in all_match_stats]) if all_match_stats else 0
        avg_std = np.mean([s['std_offset'] for s in all_match_stats]) if all_match_stats else 0
        print(f"  Match stats: avg {avg_match:.0f} matched, "
              f"{avg_unmatch:.0f} unmatched per well")
        print(f"  Avg offset: {avg_offset:.2f} +/- {avg_std:.2f} scans")

    print(f"  Total: {total_positions} positions")

    # Build consensus labels if requested
    if min_consensus > 0 and len(variants) >= 2:
        pos_to_votes = _build_consensus_labels(well_data, variants)
        # Apply consensus filter to each variant
        for well in wells:
            for variant in variants:
                if variant in well_data.get(well, {}):
                    d = well_data[well][variant]
                    filtered = _filter_consensus_variant(d, pos_to_votes, min_consensus)
                    if filtered is not None:
                        well_data[well][variant] = filtered
                    else:
                        del well_data[well][variant]

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
    parser.add_argument('--match-peaks', action='store_true', default=False,
                        help='Center windows on classic detector peaks instead of ESD positions')
    parser.add_argument('--match-tolerance', type=int, default=5,
                        help='Max scan distance for peak matching (default 5)')
    parser.add_argument('--min-consensus', type=int, default=0,
                        help='Minimum callers that must agree on base (0=no filter, 3=recommended)')
    parser.add_argument('--detector-height', type=int, default=100,
                        help='Peak detector minimum height')
    parser.add_argument('--detector-prominence', type=int, default=50,
                        help='Peak detector minimum prominence')
    parser.add_argument('--include-background', action='store_true', default=False,
                        help='Add background (non-peak) samples as N class training data')
    parser.add_argument('--background-ratio', type=float, default=1.0,
                        help='Background samples as fraction of positive count (default 1.0)')
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

    # Detector params for peak matching
    detector_params = {
        'min_height': args.detector_height,
        'prominence': args.detector_prominence,
    } if args.match_peaks else None

    # Run extraction
    run_extraction(args.data_dir, esd_dirs, variants, wells,
                   args.window, args.output,
                   match_peaks=args.match_peaks,
                   match_tolerance=args.match_tolerance,
                   min_consensus=args.min_consensus,
                   detector_params=detector_params,
                   include_background=args.include_background,
                   background_ratio=args.background_ratio)

    print(f"\nDone. Output in '{args.output}/'")
    print(f"  Files: {[f'{v}.npz' for v in variants]} + all_variants.npz")


if __name__ == '__main__':
    main()
