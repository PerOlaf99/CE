#!/usr/bin/env python3
"""Evaluate base caller outputs against M13mp18 reference sequence.

Loads .esd files (various variants), aligns to reference, computes accuracy.
Also runs the ML base caller and Cimarron Python implementation.
"""
import os, sys
import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
from extract_training_data import parse_rsd, parse_esd
from peak_detector import PeakDetector
from m13_reference import M13_REFERENCE, align_to_reference, print_alignment

BASE_DIR = '/media/per/Disk 2/electropherogram/MB1000_M13_DT'
CH_NAMES = ['Channel1', 'Channel2', 'Channel3', 'Channel4']
BASE_LABELS = ['A', 'C', 'G', 'T']


def load_esd_sequence(well, base_dir, variant):
    """Load the ESD base-called sequence for a well+variant."""
    esd_subdir = f"MB1000_M13_DT_{variant}_MD1"
    esd_path = os.path.join(base_dir, esd_subdir, f"{well}.esd")
    if not os.path.exists(esd_path):
        return None, None
    try:
        esd = parse_esd(esd_path)
        return esd.get('sequence', ''), esd.get('quality_scores')
    except Exception:
        return None, None


def evaluate_variant(wells, base_dir, variant):
    """Evaluate ESD variant against reference for all wells."""
    results = []
    for well in wells:
        seq, qual = load_esd_sequence(well, base_dir, variant)
        if not seq:
            continue
        seq_clean = ''.join(c for c in seq if c in 'ACGTNacgtn').upper()
        if len(seq_clean) < 50:
            continue
        align = align_to_reference(seq_clean)
        results.append({
            'well': well,
            'seq_len': len(seq_clean),
            'align_len': align['aligned_length'],
            'matches': align['matches'],
            'identity': align['identity'],
            'score': align['score'],
            'alignment': align,
        })
    return results


def call_ml_sequence(well, base_dir, model_path=None):
    """Run ML base caller on a well."""
    rsd_path = os.path.join(base_dir, f"{well}.rsd")
    if not os.path.exists(rsd_path):
        return None
    
    try:
        df = parse_rsd(rsd_path)
    except Exception:
        return None
    
    from basecaller import basecall_ml, _load_ml_model
    
    # Detect peaks first
    detector = PeakDetector()
    peaks, peak_channels = detector.detect(df[CH_NAMES].values)
    
    if len(peaks) == 0:
        return None
    
    # Call bases
    result = basecall_ml(df, peaks, peak_channels, None, chemistry="ML Base Caller")
    return result.get('sequence', '')


def call_cimarron_sequence(well, base_dir, spec_matrix=None):
    """Run Cimarron Python base caller on a well."""
    rsd_path = os.path.join(base_dir, f"{well}.rsd")
    if not os.path.exists(rsd_path):
        return None
    
    try:
        df = parse_rsd(rsd_path)
    except Exception:
        return None
    
    from basecaller import basecall_cimarron
    
    detector = PeakDetector()
    peaks, peak_channels = detector.detect(df[CH_NAMES].values)
    
    if len(peaks) == 0:
        return None
    
    result = basecall_cimarron(df, peaks, peak_channels, None,
                               chemistry="Cimarron 3.12 (Python)",
                               spectral_matrix=spec_matrix)
    return result.get('sequence', '')


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Evaluate base callers against reference')
    parser.add_argument('--wells', nargs='*',
                        help='Wells to evaluate (default: A01-H12)')
    parser.add_argument('--variant', default='Cp312',
                        help='ESD variant to compare (default: Cp312)')
    parser.add_argument('--top-n', type=int, default=5,
                        help='Show top N wells (default: 5)')
    parser.add_argument('--show-align', type=str, default=None,
                        help='Show alignment for a specific well')
    parser.add_argument('--ml', action='store_true',
                        help='Run ML base caller')
    parser.add_argument('--cimarron', action='store_true',
                        help='Run Cimarron Python base caller')
    args = parser.parse_args()
    
    base_dir = BASE_DIR
    if args.wells:
        wells = args.wells
    else:
        wells = [f"{r}{c:02d}" for r in 'ABCDEFGH' for c in range(1, 13)]
    
    # 1. Evaluate ESD variant
    print(f"\n=== Evaluating ESD variant: {args.variant} ===")
    esd_results = evaluate_variant(wells, base_dir, args.variant)
    
    if not esd_results:
        print("  No results!")
        return
    
    identities = [r['identity'] for r in esd_results]
    print(f"  Wells evaluated: {len(esd_results)}")
    print(f"  Identity vs reference:")
    print(f"    Mean:   {np.mean(identities):.4f}")
    print(f"    Median: {np.median(identities):.4f}")
    print(f"    Min:    {np.min(identities):.4f}")
    print(f"    Max:    {np.max(identities):.4f}")
    
    # Sort by identity
    esd_results.sort(key=lambda r: -r['identity'])
    print(f"\n  Top {args.top_n} wells:")
    for r in esd_results[:args.top_n]:
        base_calls = len(r['seq_len'])
        print(f"    {r['well']}: id={r['identity']:.4f} "
              f"({r['matches']}/{r['align_len']} aligned, "
              f"{base_calls} bases)")
    
    print(f"\n  Bottom {args.top_n} wells:")
    for r in esd_results[-args.top_n:]:
        print(f"    {r['well']}: id={r['identity']:.4f} "
              f"({r['matches']}/{r['align_len']} aligned)")
    
    # Show alignment for specific well
    if args.show_align:
        for r in esd_results:
            if r['well'] == args.show_align:
                print(f"\n  Alignment for {args.show_align}:")
                print_alignment(r['alignment'])
                break
    
    # 2. Evaluate ML base caller
    if args.ml:
        print(f"\n=== ML Base Caller (single well test) ===")
        test_well = args.show_align or wells[0]
        seq = call_ml_sequence(test_well, base_dir)
        if seq:
            seq_clean = ''.join(c for c in seq if c in 'ACGTN').upper()
            print(f"  {test_well}: {len(seq_clean)} bases")
            if len(seq_clean) >= 50:
                align = align_to_reference(seq_clean)
                print(f"  Identity vs reference: {align['identity']:.4f} "
                      f"({align['matches']}/{align['aligned_length']})")
                print_alignment(align)
    
    # 3. Evaluate Cimarron Python
    if args.cimarron:
        print(f"\n=== Cimarron Python Base Caller (single well test) ===")
        test_well = args.show_align or wells[0]
        seq = call_cimarron_sequence(test_well, base_dir)
        if seq:
            seq_clean = ''.join(c for c in seq if c in 'ACGTN').upper()
            print(f"  {test_well}: {len(seq_clean)} bases")
            if len(seq_clean) >= 50:
                align = align_to_reference(seq_clean)
                print(f"  Identity vs reference: {align['identity']:.4f} "
                      f"({align['matches']}/{align['aligned_length']})")
                print_alignment(align)


if __name__ == '__main__':
    main()
