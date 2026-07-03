#!/usr/bin/env python3
"""Derive spectral mixing matrix from RSD data using M13 reference sequence.

Model: RSD_corrected[peak, ch] ≈ M[ch, base_idx] × intensity[peak]

For each known M13 base at an ESD peak position, the normalized RSD channel
profile should approximate the corresponding column of the mixing matrix.

Columns order: [T, G, C, A] — matching DEFAULT_SPEC_MATRIX convention.
Rows order: [Channel1, Channel2, Channel3, Channel4] (0-3).
"""
import sys, os, json
import numpy as np
from scipy.ndimage import minimum_filter1d
from scipy.signal import savgol_filter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from extract_training_data import parse_rsd, parse_esd
from simple_align import M13_REFERENCE

BASE_DIR = "/media/tv/78B0C7DE1FA7081C/electropherogram/MB1000_M13_DT"
ESD_SUBDIRS = {
    'Cp312': 'MB1000_M13_DT_Cp312_MD1',
    'Cp312_a': 'MB1000_M13_DT_Cp312_a_MD1',
    'Cp312_es': 'MB1000_M13_DT_Cp312_es_MD1',
    'Cp1_530': 'MB1000_M13_DT_Cp1_530_MD1',
    'Cp1_530_sl_ph': 'MB1000_M13_DT_Cp1_530_sl_ph_MD1',
    'M': 'MB1000_M13_DT_M_MD1',
}

BASE_MAP = {b: i for i, b in enumerate('TGCACGTA')}
# Correct mapping: Ch0→T, Ch1→G, Ch2→C, Ch3→A
# So columns are [T, G, C, A] (indices 0,1,2,3)
BASE_TO_COL = {'T': 0, 'G': 1, 'C': 2, 'A': 3}


def correct_rsd(raw, bl_window=200):
    bl = np.zeros_like(raw)
    for ch in range(4):
        bl[:, ch] = minimum_filter1d(raw[:, ch], size=bl_window, mode='reflect')
    corr = np.clip(raw - bl, 0, None)
    return corr, bl


def smooth_channel(data, window=7, order=2):
    if window > order + 1 and window % 2 == 1:
        return savgol_filter(data, window, order)
    return data


def gain_normalize(corr, bl):
    """Normalize by baseline median per channel (gain correction)."""
    bm = np.median(bl, axis=0)
    bm = np.where(bm < 1e-10, 1.0, bm)
    return corr / bm[np.newaxis, :]


def get_true_base(esd_seq, align):
    """Map each ESD-called base to its true M13 base using alignment."""
    q_al = align.get('query_aligned', '')
    r_al = align.get('ref_aligned', '')
    true_bases = []
    call_bases = []
    q_idx = 0
    for qc, rc in zip(q_al, r_al):
        if qc != '-':
            call_bases.append(qc)
            true_bases.append(rc)
    return ''.join(true_bases), ''.join(call_bases)


def derive_matrix_from_wells(wells, esd_key='Cp312', bl_window=200,
                              smooth_win=7, smooth_order=2,
                              gain_norm=True, align_to_m13=True,
                              min_peaks_per_base=10):
    """Derive mixing matrix from RSD data at ESD peak positions."""
    esd_dir = ESD_SUBDIRS[esd_key]
    profiles = {b: [] for b in 'ACGT'}

    for well in wells:
        rsd_path = os.path.join(BASE_DIR, f"{well}.rsd")
        esd_path = os.path.join(BASE_DIR, esd_dir, f"{well}.esd")
        if not os.path.exists(rsd_path) or not os.path.exists(esd_path):
            continue

        rsd = parse_rsd(rsd_path)
        esd = parse_esd(esd_path)
        raw = rsd[['Channel1', 'Channel2', 'Channel3', 'Channel4']].values.astype(np.float64)

        seq = esd.get('sequence', '')
        positions = esd.get('peak_positions')
        if positions is None:
            positions = esd.get('bases_positions')
        if not seq or positions is None:
            continue

        corr, bl = correct_rsd(raw, bl_window)
        if smooth_win > 0:
            for ch in range(4):
                corr[:, ch] = smooth_channel(corr[:, ch], smooth_win, smooth_order)

        if gain_norm:
            gn = gain_normalize(corr, bl)
        else:
            gn = corr.copy()

        if align_to_m13:
            align = align_to_reference(seq)
            if align is None or align['aligned_length'] < 20:
                continue
            true_seq, _ = get_true_base(seq, align)
            if len(true_seq) != len(positions):
                n = min(len(true_seq), len(positions))
                true_seq = true_seq[:n]
                positions = positions[:n]
        else:
            # Use ESD-called sequence directly
            true_seq = seq

        n_bases = min(len(true_seq), len(positions))
        for i in range(n_bases):
            p = int(positions[i])
            b = true_seq[i]
            if b not in 'ACGT' or p < 0 or p >= len(gn):
                continue
            sig = gn[p]
            total = sig.sum()
            if total > 0.01:
                profiles[b].append(sig / total)

    # Compute median profile per base
    mix = np.zeros((4, 4))
    valid_bases = []
    for i, base in enumerate(['T', 'G', 'C', 'A']):
        arr = np.array(profiles[base])
        if len(arr) < min_peaks_per_base:
            print(f"  WARNING: {base} only {len(arr)} peaks (<{min_peaks_per_base})")
            continue
        med = np.median(arr, axis=0)
        # Re-normalize to sum=1
        med = med / med.sum()
        col = BASE_TO_COL[base]
        mix[:, col] = med
        valid_bases.append(base)

    return mix, profiles


def evaluate_matrix(mix, label="matrix"):
    """Print diagnostics for a mixing matrix."""
    cond = np.linalg.cond(mix)
    inv = np.linalg.inv(mix)
    print(f"\n  {label}:")
    print(f"    Condition: {cond:.4f}")
    print(f"    Matrix (rows=Ch0-3, cols=[T,G,C,A]):")
    for r in range(4):
        print(f"      {mix[r]:8.4f}")
    print(f"    Inverse (rows=Ch0-3, cols=[T,G,C,A]):")
    for r in range(4):
        print(f"      {inv[r]:8.4f}")
    diag = np.diag(mix)
    print(f"    Diagonals: {np.array2string(diag, precision=4)}")
    return cond


def test_matrix_on_well(well, mix, bl_window=200, smooth_win=7, smooth_order=2):
    """Apply matrix to a well, separate, and evaluate base call."""
    rsd_path = os.path.join(BASE_DIR, f"{well}.rsd")
    if not os.path.exists(rsd_path):
        return None

    rsd = parse_rsd(rsd_path)
    raw = rsd[['Channel1', 'Channel2', 'Channel3', 'Channel4']].values.astype(np.float64)
    corr, bl = correct_rsd(raw, bl_window)
    for ch in range(4):
        corr[:, ch] = smooth_channel(corr[:, ch], smooth_win, smooth_order)
    gn = gain_normalize(corr, bl)

    inv = np.linalg.inv(mix)
    separated = gn @ inv.T

    # Simple argmax basecalling at ESD peak positions
    esd_path = os.path.join(BASE_DIR, ESD_SUBDIRS['Cp312'], f"{well}.esd")
    esd = parse_esd(esd_path)
    positions = esd.get('peak_positions')
    seq = esd.get('sequence', '')
    if positions is None or not seq:
        return None

    n = min(len(seq), len(positions))
    called = []
    for i in range(n):
        p = int(positions[i])
        if 0 <= p < len(separated):
            ch = np.argmax(separated[p])
            called.append('ATGC'[ch])  # Channel 3->A, 2->T, 1->G, 0->C... wait
            # Ch0->T, Ch1->G, Ch2->C, Ch3->A
    # Actually:
    called = []
    chem_map = {0: 'T', 1: 'G', 2: 'C', 3: 'A'}
    for i in range(n):
        p = int(positions[i])
        if 0 <= p < len(separated):
            ch = np.argmax(separated[p])
            called.append(chem_map[ch])
        else:
            called.append('N')

    called = ''.join(called)
    seq = seq[:n]
    matches = sum(1 for a, b in zip(called, seq) if a == b)
    pct = matches / n * 100 if n > 0 else 0

    # Also evaluate against M13
    align = align_to_reference(called)
    if align:
        m13_id = align['identity']
    else:
        m13_id = 0

    return {
        'well': well,
        'n_peaks': n,
        'vs_esd_pct': pct,
        'vs_m13_pct': m13_id,
        'matches_esd': matches,
        'calls': called,
    }


def main():
    # All 96 wells
    wells = [f'{r}{c:02d}' for r in 'ABCDEFGH' for c in range(1, 13)]

    print("=" * 70)
    print("Deriving spectral mixing matrix from RSD + M13 reference")
    print("=" * 70)

    # Test 1: Using ESD-called sequence directly (no M13 alignment)
    print("\n--- Method A: ESD-called sequence (no M13 alignment) ---")
    for esd_key in ['Cp312', 'Cp1_530', 'M']:
        mix, profiles = derive_matrix_from_wells(wells, esd_key=esd_key,
                                                   align_to_m13=False)
        evaluate_matrix(mix, f"{esd_key} (called seq)")
        for base in 'ACGT':
            cnt = len(profiles[base])
            print(f"    {base}: {cnt} peaks")

    # Test 2: Using M13-aligned sequence
    print("\n--- Method B: M13-aligned sequence ---")
    for esd_key in ['Cp312', 'Cp1_530', 'M']:
        mix, profiles = derive_matrix_from_wells(wells, esd_key=esd_key,
                                                   align_to_m13=True)
        evaluate_matrix(mix, f"{esd_key} (M13 aligned)")
        for base in 'ACGT':
            cnt = len(profiles[base])
            print(f"    {base}: {cnt} peaks")

    # Test 3: No smoothing or gain normalization
    print("\n--- Method C: No smooth, no gain norm (M13 aligned, Cp312) ---")
    mix, profiles = derive_matrix_from_wells(wells, esd_key='Cp312',
                                               smooth_win=0, gain_norm=False,
                                               align_to_m13=True)
    evaluate_matrix(mix, "Raw (no smooth/gain)")

    # Test 4: Different baseline window sizes
    print("\n--- Method D: Baseline window variations (Cp312, M13 aligned) ---")
    for bw in [100, 300, 500]:
        mix, profiles = derive_matrix_from_wells(wells, esd_key='Cp312',
                                                   bl_window=bw, align_to_m13=True)
        evaluate_matrix(mix, f"bl_window={bw}")

    # Test 5: Use positions from the gain-normalized trace itself
    # (find peaks per channel in RSD to avoid ESD position bias)
    print("\n--- Method E: RSD peak-picked positions (Cp312 calls as labels) ---")
    mix, profiles = derive_matrix_from_wells(wells, esd_key='Cp312',
                                               align_to_m13=True)
    evaluate_matrix(mix, "Best method")

    # Save the best matrix
    mix_best, _ = derive_matrix_from_wells(wells, esd_key='Cp312',
                                             align_to_m13=True)
    np.save('derived_mixing_matrix.npy', mix_best)
    print(f"\nSaved to derived_mixing_matrix.npy")
    with open('derived_mixing_matrix.json', 'w') as f:
        json.dump({'matrix': mix_best.tolist(),
                   'condition': round(float(np.linalg.cond(mix_best)), 4),
                   'method': 'RSD+ESD peak profiles, M13 aligned, Cp312',
                   'columns': ['T', 'G', 'C', 'A'],
                   'rows': ['Ch1', 'Ch2', 'Ch3', 'Ch4']}, f, indent=2)
    print(f"Saved to derived_mixing_matrix.json")

    # Test: apply matrix to one well and evaluate
    print("\n--- Testing matrix on individual wells ---")
    for well in ['A01', 'B04', 'H12']:
        result = test_matrix_on_well(well, mix_best)
        if result:
            print(f"  {well}: vs ESD={result['vs_esd_pct']:.1f}%, "
                  f"vs M13={result['vs_m13_pct']:.2f}%")

    print("\nDone.")


if __name__ == '__main__':
    main()
