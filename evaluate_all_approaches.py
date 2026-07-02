#!/usr/bin/env python3
"""Evaluate ALL base calling approaches against M13 reference:
  1. All 6 ESD base callers (baselines)
  2. Existing trained ML models (peak-based, per-scan)
  3. Python Cimarron reimplementation
  4. Simple chemistry-based calling
  5. Consensus/ensemble across callers

Outputs comprehensive accuracy table.
"""
import os, sys, json
import numpy as np

BASE_DIR = '/media/tv/78B0C7DE1FA7081C/electropherogram'
sys.path.insert(0, BASE_DIR)

from extract_training_data import parse_rsd, parse_esd
from peak_detector import PeakDetector
from m13_reference import M13_REFERENCE, align_to_reference, print_alignment
from basecaller import (basecall_ml, basecall_ml_scan, basecall_cimarron,
                        basecall, _load_ml_model, BASE_QUAL_CHANNELS)
import tensorflow as tf

CH_NAMES = ['Channel1', 'Channel2', 'Channel3', 'Channel4']
VARIANTS = ['Cp312', 'Cp312_a', 'Cp312_es', 'Cp1_530', 'Cp1_530_sl_ph', 'MD']
VARIANT_NAMES = {
    'Cp312': 'Cimarron 3.12',
    'Cp312_a': 'Cimarron 3.12 Aligned',
    'Cp312_es': 'Cimarron 3.12 Even Spacing',
    'Cp1_530': 'Cimarron 1.53',
    'Cp1_530_sl_ph': 'Cimarron 1.53 Slim Phredify',
    'MD': 'Molecular Dynamics',
}

def load_esd_sequence(well, base_dir, variant, data_subdir='MB1000_M13_DT'):
    esd_dir = f"{data_subdir}_{variant}_MD1"
    esd_path = os.path.join(base_dir, data_subdir, esd_dir, f"{well}.esd")
    if not os.path.exists(esd_path):
        return None, None
    try:
        esd = parse_esd(esd_path)
        return esd.get('sequence', ''), esd.get('quality_scores')
    except:
        return None, None

def evaluate_well_esd(well, base_dir, variant, data_subdir='MB1000_M13_DT'):
    seq, qual = load_esd_sequence(well, base_dir, variant, data_subdir)
    if not seq:
        return None
    seq_clean = ''.join(c for c in seq if c in 'ACGTNacgtn').upper()
    if len(seq_clean) < 50:
        return None
    align = align_to_reference(seq_clean)
    return {
        'well': well, 'variant': variant,
        'seq_len': len(seq_clean),
        'align_len': align['aligned_length'],
        'matches': align['matches'],
        'identity': align['identity'],
        'score': align['score'],
        'n_count': seq_clean.count('N'),
    }

def evaluate_well_ml(well, base_dir, model, approach='peak',
                     data_subdir='MB1000_M13_DT', **kwargs):
    rsd_path = os.path.join(base_dir, data_subdir, f"{well}.rsd")
    if not os.path.exists(rsd_path):
        return None
    try:
        df = parse_rsd(rsd_path)
    except:
        return None

    detector = PeakDetector()
    ch_data = df[CH_NAMES]

    if approach == 'peak':
        peaks, peak_channels = detector.detect(ch_data.values)
        if len(peaks) == 0:
            return None
        result = basecall_ml(df, peaks, peak_channels, None,
                            chemistry="ML Base Caller", model=model,
                            auto_threshold=kwargs.get('auto_threshold', False),
                            target_accuracy=kwargs.get('target_accuracy', 0.98))
    elif approach == 'scan':
        result = basecall_ml_scan(df, None, chemistry="ML Scan Caller",
                                  model=model,
                                  min_confidence=kwargs.get('min_confidence', 0.5),
                                  min_spacing=kwargs.get('min_spacing', 3))
    else:
        return None

    seq = result.get('sequence', '')
    if len(seq) < 50:
        return None
    align = align_to_reference(seq)
    return {
        'well': well, 'variant': approach,
        'seq_len': len(seq),
        'align_len': align['aligned_length'],
        'matches': align['matches'],
        'identity': align['identity'],
        'score': align['score'],
        'n_count': seq.count('N'),
        'n_rate': seq.count('N') / len(seq) if seq else 0,
        'avg_qual': result.get('avg_quality', 0),
    }

def evaluate_well_cimarron_python(well, base_dir, variant=None,
                                   data_subdir='MB1000_M13_DT'):
    rsd_path = os.path.join(base_dir, data_subdir, f"{well}.rsd")
    if not os.path.exists(rsd_path):
        return None
    try:
        df = parse_rsd(rsd_path)
    except:
        return None
    detector = PeakDetector()
    peaks, peak_channels = detector.detect(df[CH_NAMES].values)
    if len(peaks) == 0:
        return None
    result = basecall_cimarron(df, peaks, peak_channels, None,
                               chemistry="Cimarron 3.12 (Python)",
                               variant=variant)
    seq = result.get('sequence', '')
    if len(seq) < 50:
        return None
    align = align_to_reference(seq)
    return {
        'well': well, 'variant': f'Cimarron_Py_{variant or "std"}',
        'seq_len': len(seq),
        'align_len': align['aligned_length'],
        'matches': align['matches'],
        'identity': align['identity'],
        'score': align['score'],
        'n_count': seq.count('N'),
    }

def consensus_sequence(well_results, variants):
    """Build consensus sequence from multiple callers."""
    # Collect all positions and their base calls
    pos_to_bases = {}
    for vr, r in well_results.items():
        if r is None:
            continue
        seq = r.get('sequence', '')
        positions = r.get('positions')
        if not seq or positions is None:
            continue
        for i, (pos, base) in enumerate(zip(positions, seq)):
            pos_i = int(pos)
            if pos_i not in pos_to_bases:
                pos_to_bases[pos_i] = []
            pos_to_bases[pos_i].append(base)
    
    if not pos_to_bases:
        return ""
    
    # Get majority vote at each position, keep positions with >= 2 callers
    consensus = []
    for pos in sorted(pos_to_bases.keys()):
        votes = pos_to_bases[pos]
        if len(votes) < 2:
            continue
        base_counts = {}
        for b in votes:
            if b in 'ACGT':
                base_counts[b] = base_counts.get(b, 0) + 1
        if not base_counts:
            consensus.append('N')
        else:
            winner = max(base_counts, key=base_counts.get)
            if base_counts[winner] >= 2:
                consensus.append(winner)
            else:
                consensus.append('N')
    return ''.join(consensus)


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Evaluate all base calling approaches')
    parser.add_argument('--base-dir', default=BASE_DIR)
    parser.add_argument('--data-subdir', default='MB1000_M13_DT')
    parser.add_argument('--wells', nargs='*', help='Specific wells (default: all)')
    parser.add_argument('--output', default='evaluation_results.json')
    parser.add_argument('--show-well', type=str, help='Show alignment for a well')
    args = parser.parse_args()

    base_dir = args.base_dir
    data_subdir = args.data_subdir
    data_dir = os.path.join(base_dir, data_subdir)

    # Get wells
    if args.wells:
        wells = args.wells
    else:
        wells = sorted([f.replace('.rsd', '') for f in os.listdir(data_dir)
                       if f.endswith('.rsd')])
    
    print(f"Evaluating {len(wells)} wells from {data_dir}")
    print(f"Reference: M13mp18 ({len(M13_REFERENCE)} bp)\n")

    all_results = {}

    # 1. Evaluate all 6 ESD callers
    print("=" * 70)
    print("  1. ESD BASELINE CALLERS")
    print("=" * 70)
    for variant in VARIANTS:
        print(f"\n  {variant} ({VARIANT_NAMES[variant]}):")
        results = []
        for well in wells:
            r = evaluate_well_esd(well, base_dir, variant, data_subdir)
            if r:
                results.append(r)
        if results:
            ids = [r['identity'] for r in results]
            ns = [r['n_count'] for r in results]
            print(f"    Wells: {len(results)}/{len(wells)}")
            print(f"    Identity: mean={np.mean(ids):.4f} median={np.median(ids):.4f} "
                  f"min={np.min(ids):.4f} max={np.max(ids):.4f}")
            print(f"    N count: mean={np.mean(ns):.1f}")
            all_results[f'esd_{variant}'] = {
                'method': f'ESD {VARIANT_NAMES[variant]}',
                'n_wells': len(results),
                'mean_identity': float(np.mean(ids)),
                'median_identity': float(np.median(ids)),
                'std_identity': float(np.std(ids)),
                'min_identity': float(np.min(ids)),
                'max_identity': float(np.max(ids)),
                'well_results': results,
            }

    # 2. Evaluate Python Cimarron implementation
    print(f"\n{'=' * 70}")
    print("  2. PYTHON CIMARRON REIMPLEMENTATION")
    print("=" * 70)
    for variant in [None, 'aligned', 'even_spacing']:
        vname = variant or 'standard'
        print(f"\n  Cimarron Python ({vname}):")
        results = []
        for well in wells[:24]:  # Limit to 24 for speed
            r = evaluate_well_cimarron_python(well, base_dir, variant, data_subdir)
            if r:
                results.append(r)
        if results:
            ids = [r['identity'] for r in results]
            print(f"    Wells: {len(results)}")
            print(f"    Identity: mean={np.mean(ids):.4f} median={np.median(ids):.4f}")
            all_results[f'cimarron_py_{vname}'] = {
                'method': f'Cimarron Python ({vname})',
                'n_wells': len(results),
                'mean_identity': float(np.mean(ids)),
                'median_identity': float(np.median(ids)),
                'std_identity': float(np.std(ids)),
                'well_results': results,
            }

    # 3. Evaluate existing ML models
    print(f"\n{'=' * 70}")
    print("  3. EXISTING ML MODELS")
    print("=" * 70)
    
    model_configs = [
        ('base_caller_model.keras', 'peak', {'auto_threshold': False}),
        ('base_caller_model_matched.keras', 'peak', {'auto_threshold': False}),
        ('base_caller_model_combined_checkpoint.keras', 'peak', {'auto_threshold': False}),
        ('base_caller_model_with_bg.keras', 'scan', {'min_confidence': 0.5, 'min_spacing': 3}),
        ('base_caller_model_with_bg.keras', 'scan', {'min_confidence': 0.3, 'min_spacing': 2}),
        ('base_caller_model_with_bg.keras', 'scan', {'min_confidence': 0.7, 'min_spacing': 4}),
    ]

    for model_fname, approach, params in model_configs:
        model_path = os.path.join(base_dir, model_fname)
        if not os.path.exists(model_path):
            print(f"\n  {model_fname} ({approach}): SKIP (not found)")
            continue
        
        print(f"\n  {model_fname} ({approach}, params={params}):")
        try:
            model = tf.keras.models.load_model(model_path)
        except Exception as e:
            print(f"    Error loading: {e}")
            continue
        
        results = []
        for well in wells[:24]:  # Limit to 24 for speed
            r = evaluate_well_ml(well, base_dir, model, approach,
                                data_subdir=data_subdir, **params)
            if r:
                results.append(r)
        
        if results:
            ids = [r['identity'] for r in results]
            ns = [r.get('n_rate', 0) for r in results]
            aq = [r.get('avg_qual', 0) for r in results]
            print(f"    Wells: {len(results)}")
            print(f"    Identity: mean={np.mean(ids):.4f} median={np.median(ids):.4f}")
            print(f"    N rate: {np.mean(ns)*100:.1f}%  Avg qual: {np.mean(aq):.0f}")
            all_results[f'ml_{model_fname.replace(".keras","")}_{approach}'] = {
                'method': f'ML {model_fname.replace(".keras","")} ({approach})',
                'n_wells': len(results),
                'mean_identity': float(np.mean(ids)),
                'median_identity': float(np.median(ids)),
                'std_identity': float(np.std(ids)),
                'well_results': results,
            }
        del model  # Free memory

    # 4. Consensus across all 6 callers
    print(f"\n{'=' * 70}")
    print("  4. CONSENSUS ACROSS ALL 6 CALLERS")
    print("=" * 70)
    print(f"\n  Consensus (majority vote, min 2 agreeing):")
    results = []
    for well in wells:
        well_results = {}
        for variant in VARIANTS:
            r = evaluate_well_esd(well, base_dir, variant, data_subdir)
            if r:
                well_results[variant] = r
        seq = consensus_sequence(well_results, VARIANTS)
        if len(seq) < 50:
            continue
        align = align_to_reference(seq)
        results.append({
            'well': well, 'variant': 'consensus',
            'seq_len': len(seq),
            'align_len': align['aligned_length'],
            'matches': align['matches'],
            'identity': align['identity'],
            'score': align['score'],
            'n_count': seq.count('N'),
        })
    if results:
        ids = [r['identity'] for r in results]
        print(f"    Wells: {len(results)}")
        print(f"    Identity: mean={np.mean(ids):.4f} median={np.median(ids):.4f}")
        all_results['consensus'] = {
            'method': 'Consensus (all 6 callers)',
            'n_wells': len(results),
            'mean_identity': float(np.mean(ids)),
            'median_identity': float(np.median(ids)),
            'std_identity': float(np.std(ids)),
            'well_results': results,
        }

    # Print summary table
    print(f"\n{'=' * 70}")
    print("  FINAL SUMMARY")
    print(f"{'=' * 70}")
    print(f"{'Method':40s} {'Wells':>6s} {'Mean Id':>8s} {'Median':>8s} {'Std':>8s}")
    print("-" * 70)
    sorted_methods = sorted(all_results.items(),
                           key=lambda x: x[1]['mean_identity'], reverse=True)
    for key, r in sorted_methods:
        print(f"{r['method']:40s} {r['n_wells']:6d} {r['mean_identity']:8.4f} "
              f"{r['median_identity']:8.4f} {r['std_identity']:8.4f}")

    # Show alignment for a specific well
    if args.show_well:
        well = args.show_well
        print(f"\n{'=' * 70}")
        print(f"  Alignments for {well}")
        print(f"{'=' * 70}")
        for variant in VARIANTS:
            r = evaluate_well_esd(well, base_dir, variant, data_subdir)
            if r:
                from m13_reference import print_alignment
                print(f"\n  {VARIANT_NAMES[variant]} (id={r['identity']:.4f}):")
        
        # Show ML
        for model_fname, approach, params in model_configs:
            model_path = os.path.join(base_dir, model_fname)
            if not os.path.exists(model_path):
                continue
            try:
                model = tf.keras.models.load_model(model_path)
                r = evaluate_well_ml(well, base_dir, model, approach,
                                    data_subdir=data_subdir, **params)
                if r:
                    print(f"\n  {model_fname} ({approach}) (id={r['identity']:.4f}):")
                del model
            except:
                pass

    # Save results
    with open(args.output, 'w') as f:
        json.dump(all_results, f, indent=2, default=str)
    print(f"\nResults saved to {args.output}")


if __name__ == '__main__':
    main()
