#!/usr/bin/env python3
"""Empirically derive the spectral emission matrix from raw .rsd + .esd data.

At each ESD-called base position, extract raw channel intensities (Ch1-4),
group by base (A/C/G/T), and compute the mean per-channel profile.
This gives the dye emission matrix columns, which we invert to get the
spectral separation matrix.
"""
import os, sys, argparse
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
from extract_training_data import parse_rsd, parse_esd

BASE_MAP = {'A': 0, 'C': 1, 'G': 2, 'T': 3}
BASE_LABELS = ['A', 'C', 'G', 'T']
CH_NAMES = ['Channel1', 'Channel2', 'Channel3', 'Channel4']


def extract_channel_profiles(well, base_dir, esd_subdir=None):
    """Extract raw channel intensities at each ESD base position for one well.
    
    Returns: list of dicts {base, ch1, ch2, ch3, ch4, pos, quality}
    """
    rsd_path = os.path.join(base_dir, f"{well}.rsd")
    if esd_subdir:
        esd_path = os.path.join(base_dir, esd_subdir, f"{well}.esd")
    else:
        esd_path = os.path.join(base_dir, f"{well}.esd")
    if not os.path.exists(rsd_path) or not os.path.exists(esd_path):
        return None

    df = parse_rsd(rsd_path)
    esd = parse_esd(esd_path)

    seq = esd.get('sequence', '')
    positions = esd.get('peak_positions')
    if positions is None:
        positions = esd.get('bases_positions')
    quality = esd.get('quality_scores')

    if not seq or positions is None or quality is None:
        return None

    n = min(len(seq), len(positions), len(quality))
    seq = seq[:n]
    positions = np.asarray(positions[:n]).astype(int)
    quality = np.asarray(quality[:n])

    ch = df[CH_NAMES].values
    n_scans = len(ch)

    window = 7  # look ±7 scans around ESD position for peak
    results = []
    for i, pos in enumerate(positions):
        if pos < 0 or pos >= n_scans:
            continue
        if quality[i] < 10:
            continue
        base = seq[i].upper()
        if base not in BASE_MAP:
            continue
        # Single-point at ESD position
        results.append({
            'well': well,
            'base': BASE_MAP[base],
            'base_char': base,
            'Channel1': ch[pos, 0],
            'Channel2': ch[pos, 1],
            'Channel3': ch[pos, 2],
            'Channel4': ch[pos, 3],
            'total': float(ch[pos].sum()),
            'position': int(pos),
            'quality': float(quality[i]),
            'mode': 'single',
        })
        # Peak-max over a window: find scan with max total signal around pos
        lo = max(0, pos - window)
        hi = min(n_scans, pos + window + 1)
        window_total = ch[lo:hi].sum(axis=1)
        peak_offset = np.argmax(window_total)
        peak_pos = lo + peak_offset
        results.append({
            'well': well,
            'base': BASE_MAP[base],
            'base_char': base,
            'Channel1': ch[peak_pos, 0],
            'Channel2': ch[peak_pos, 1],
            'Channel3': ch[peak_pos, 2],
            'Channel4': ch[peak_pos, 3],
            'total': float(ch[peak_pos].sum()),
            'position': int(peak_pos),
            'quality': float(quality[i]),
            'mode': 'peak',
        })
    return results


def run_analysis(base_dir, wells, variant='Cp312'):
    """Collect all channel profiles and compute the emission matrix."""
    esd_subdir = f"MB1000_M13_DT_{variant}_MD1"
    all_rows = []
    for well in wells:
        profiles = extract_channel_profiles(well, base_dir, esd_subdir)
        if profiles:
            all_rows.extend(profiles)
            print(f"  {well}: {len(profiles)} bases")
    if not all_rows:
        print("No data collected!")
        return None

    df = pd.DataFrame(all_rows)
    print(f"\nTotal positions collected: {len(df)}")

    # Per-base stats
    print("\n--- Per-base channel intensity profiles ---")
    for base_char in ['A', 'C', 'G', 'T']:
        subset = df[df['base_char'] == base_char]
        if len(subset) == 0:
            continue
        means = subset[CH_NAMES].mean()
        stds = subset[CH_NAMES].std()
        print(f"\n{base_char} (n={len(subset)}):")
        for ch in CH_NAMES:
            ratio = (means / means.max()).round(3)
        print(f"  Mean: {means.round(1).to_dict()}")
        print(f"  Std:  {stds.round(1).to_dict()}")
        print(f"  Normalized (max=1): {ratio.to_dict()}")

    # Build emission matrix: columns = [A, C, G, T] dye profiles
    # Row = channel, col = base
    emission = np.zeros((4, 4), dtype=np.float64)
    for i, base_char in enumerate(['A', 'C', 'G', 'T']):
        subset = df[df['base_char'] == base_char]
        if len(subset) == 0:
            continue
        means = subset[CH_NAMES].mean().values
        # Normalize so max channel = 1 (or sum to 1)
        emission[:, i] = means / means.sum()

    print(f"\n--- Emission matrix (cols=[A,C,G,T], rows=Ch1-4) ---")
    print("       A      C      G      T")
    for i, ch in enumerate(CH_NAMES):
        print(f"  {ch}: {emission[i][0]:.4f} {emission[i][1]:.4f} {emission[i][2]:.4f} {emission[i][3]:.4f}")

    # Separation matrix = inverse
    try:
        sep = np.linalg.inv(emission)
        print(f"\n--- Separation matrix (inverse) ---")
        print("       A      C      G      T")
        for i, ch in enumerate(CH_NAMES):
            print(f"  {ch}: {sep[i][0]:.4f} {sep[i][1]:.4f} {sep[i][2]:.4f} {sep[i][3]:.4f}")
    except np.linalg.LinAlgError:
        print("Emission matrix is singular, cannot invert")
        sep = None

    y_true = df['base_char'].values

    for mode_name in ['single', 'peak']:
        mode_mask = df['mode'] == mode_name
        df_mode = df[mode_mask]
        y_mode = y_true[mode_mask]
        ch_mode = df_mode[CH_NAMES].values

        max_ch = np.argmax(ch_mode, axis=1)
        ch_to_base = {0: 'T', 1: 'G', 2: 'C', 3: 'A'}
        raw_max_pred = np.array([ch_to_base[c] for c in max_ch])

        if sep is not None and mode_name == 'single':
            raw = ch_mode
            clean = raw @ sep.T
            clean = np.maximum(clean, 0)
            unmixed_dominant = np.argmax(clean, axis=1)
            unmixed_pred = np.array([BASE_LABELS[d] for d in unmixed_dominant])
            unmixed_acc = (unmixed_pred == y_mode).mean()
        else:
            unmixed_pred = raw_max_pred
            unmixed_acc = (raw_max_pred == y_mode).mean()

        raw_acc = (raw_max_pred == y_mode).mean()
        n_tot = len(y_mode)

        print(f"\n--- {mode_name}-point: Raw max-channel accuracy ---")
        print(f"  Raw max-channel: {raw_acc:.4f} ({int(raw_acc * n_tot)}/{n_tot})")
        if sep is not None and mode_name == 'single':
            print(f"  Unmixed (spectral sep): {unmixed_acc:.4f} ({int(unmixed_acc * n_tot)}/{n_tot})")

        # Per-base
        for suffix, preds, acc in [('Raw max-channel', raw_max_pred, raw_acc),
                                    ('Unmixed', unmixed_pred, unmixed_acc)]:
            if suffix == 'Unmixed' and mode_name != 'single':
                continue
            for base_char in BASE_LABELS:
                mask = y_mode == base_char
                if mask.sum() == 0:
                    continue
                ba = (preds[mask] == base_char).mean()
                print(f"    {suffix} {base_char}: {ba:.4f} ({mask.sum():>4} samples)")

    # Also check what the user observed: 
    # "T when Ch1 biggest, C when Ch3 biggest,
    #  G when Ch2 >= Ch1, A when Ch4 ≈ 0.5×Ch3"
    positions = df['base_char'].values
    ch_vals = df[CH_NAMES].values
    max_idx = np.argmax(ch_vals, axis=1)
    ratios = {}
    for i in range(4):
        col_i = ch_vals[:, i]
        ratios[CH_NAMES[i]] = col_i / (ch_vals.sum(axis=1) + 1e-8)

    print(f"\n--- Heuristic rules (your observation) ---")
    # Rule: if Ch1 is max → T
    t_mask = (max_idx == 0)
    t_acc = (positions[t_mask] == 'T').mean() if t_mask.sum() > 0 else 0
    print(f"  Ch1 max → T: acc={t_acc:.4f} (n={t_mask.sum()})")

    # Rule: if Ch3 is max → C
    c_mask = (max_idx == 2)
    c_acc = (positions[c_mask] == 'C').mean() if c_mask.sum() > 0 else 0
    print(f"  Ch3 max → C: acc={c_acc:.4f} (n={c_mask.sum()})")

    # Rule: if Ch2 >= Ch1 (and Ch1 is NOT max) → G
    g_mask = (ch_vals[:, 1] >= ch_vals[:, 0]) & (max_idx != 0) & (max_idx != 2)
    g_acc = (positions[g_mask] == 'G').mean() if g_mask.sum() > 0 else 0
    print(f"  Ch2 >= Ch1 (and Ch1/Ch3 not max) → G: acc={g_acc:.4f} (n={g_mask.sum()})")

    a_mask = (max_idx == 3)  # Ch4 is max
    a_acc = (positions[a_mask] == 'A').mean() if a_mask.sum() > 0 else 0
    print(f"  Ch4 max → A: acc={a_acc:.4f} (n={a_mask.sum()})")

    # Ch4 ≈ 0.5×Ch3 rule for A
    ratio_ch4_ch3 = ch_vals[:, 3] / (ch_vals[:, 2] + 1e-8)
    a_rule = (0.2 < ratio_ch4_ch3) & (ratio_ch4_ch3 < 0.8) & (max_idx != 0) & (max_idx != 2)
    a_rule_acc = (positions[a_rule] == 'A').mean() if a_rule.sum() > 0 else 0
    print(f"  ch4/ch3 in (0.2, 0.8) & not Ch1/Ch3 max → A: acc={a_rule_acc:.4f} (n={a_rule.sum()})")

    # Build combined rule-based classifier
    rule_pred = np.full(len(positions), 'N', dtype='<U1')
    rule_pred[max_idx == 0] = 'T'
    rule_pred[max_idx == 2] = 'C'
    # G: Ch2 max or Ch2 ≈ Ch1 and Ch1 is not max
    g_cond = (max_idx == 1) | ((ch_vals[:, 1] >= ch_vals[:, 0] * 0.9) & (max_idx != 0) & (max_idx != 2) & (max_idx != 3))
    rule_pred[g_cond] = 'G'
    # A: left over with ch4/ch3 in range
    a_cond = (rule_pred == 'N') & (ratio_ch4_ch3 > 0.15) & (ratio_ch4_ch3 < 1.5)
    rule_pred[a_cond] = 'A'
    # Fill remaining Ns with max channel rule
    remaining = rule_pred == 'N'
    rule_pred[remaining] = raw_max_pred[remaining]

    rule_acc = (rule_pred == positions).mean()
    print(f"  Combined rule: acc={rule_acc:.4f} ({int((rule_pred == positions).sum())}/{len(positions)})")


    print(f"\n--- Summary ---")
    print(f"  Raw max-channel classifier: {raw_acc:.3f}")
    if sep is not None:
        print(f"  Unmixed (spectral sep):    {acc:.3f}")
    print(f"  Combined rule-based:        {rule_acc:.3f}")
    print(f"\nEmission matrix as numpy array:")
    print("DEFAULT_SPEC_MATRIX = np.array([")
    for i in range(4):
        row = ", ".join(f"{emission[i,j]:.4f}" for j in range(4))
        print(f"    [{row}],  # {CH_NAMES[i]}")
    print("], dtype=np.float64)")
    print(f"\nSeparation matrix as numpy array:")
    if sep is not None:
        print("SPEC_SEPARATION = np.array([")
        for i in range(4):
            row = ", ".join(f"{sep[i,j]:.4f}" for j in range(4))
            print(f"    [{row}],  # {CH_NAMES[i]}")
        print("], dtype=np.float64)")

    return df, emission, sep


def main():
    parser = argparse.ArgumentParser(description='Analyze spectral matrix empirically')
    parser.add_argument('--data-dir', default='/media/per/Disk 2/electropherogram/MB1000_M13_DT',
                        help='Base directory with .rsd and .esd files')
    parser.add_argument('--wells', nargs='*',
                        help='Well IDs (default: all A01-H12)')
    parser.add_argument('--rows', default='ABCDEFGH')
    parser.add_argument('--cols', type=int, default=12)
    parser.add_argument('--variant', default='Cp312',
                        help='Base caller variant (e.g. Cp312, MD, Cp1_530)')
    args = parser.parse_args()

    if args.wells:
        wells = args.wells
    else:
        wells = [f"{r}{c:02d}" for r in args.rows for c in range(1, args.cols + 1)]

    print(f"Analyzing {len(wells)} wells from {args.data_dir} (variant={args.variant})")
    df, emission, sep = run_analysis(args.data_dir, wells, args.variant)
    print("\nDone.")


if __name__ == '__main__':
    main()
