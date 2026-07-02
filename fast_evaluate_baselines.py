#!/usr/bin/env python3
"""Fast evaluation of all ESD base callers against M13 reference.
Reads ESD sequences directly and aligns to M13. No ML models loaded.
"""
import sys, os, json, time
import numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from extract_training_data import parse_esd
from m13_reference import M13_REFERENCE, align_to_reference

BASE_DIR = '/media/tv/78B0C7DE1FA7081C/electropherogram'
DATA_SUBDIR = 'MB1000_M13_DT'

# Direct folder name mapping (from DEFAULT_ESD_DIRS in extract_training_data.py)
ESD_FOLDERS = {
    'Cp312': 'MB1000_M13_DT_Cp312_MD1',
    'Cp312_a': 'MB1000_M13_DT_Cp312_a_MD1',
    'Cp312_es': 'MB1000_M13_DT_Cp312_es_MD1',
    'Cp1_530': 'MB1000_M13_DT_Cp1_530_MD1',
    'Cp1_530_sl_ph': 'MB1000_M13_DT_Cp1_530_sl_ph_MD1',
    'MD': 'MB1000_M13_DT_M_MD1',
}

VARIANT_NAMES = {
    'Cp312': 'Cimarron 3.12',
    'Cp312_a': 'Cimarron 3.12 Aligned',
    'Cp312_es': 'Cimarron 3.12 Even Spacing',
    'Cp1_530': 'Cimarron 1.53',
    'Cp1_530_sl_ph': 'Cimarron 1.53 Slim Phredify',
    'MD': 'Molecular Dynamics',
}

def evaluate_well(well, esd_folder):
    esd_path = os.path.join(BASE_DIR, DATA_SUBDIR, esd_folder, f"{well}.esd")
    if not os.path.exists(esd_path):
        return None
    try:
        esd = parse_esd(esd_path)
    except:
        return None
    seq = esd.get('sequence', '')
    seq_clean = ''.join(c for c in seq if c in 'ACGTNacgtn').upper()
    if len(seq_clean) < 50:
        return None
    align = align_to_reference(seq_clean)
    return {
        'well': well,
        'seq_len': len(seq_clean),
        'align_len': align['aligned_length'],
        'matches': align['matches'],
        'identity': align['identity'],
        'n_count': seq_clean.count('N'),
    }

def evaluate_all_variants(wells):
    results = {}
    for variant, folder in ESD_FOLDERS.items():
        name = VARIANT_NAMES[variant]
        t0 = time.time()
        well_results = []
        for well in wells:
            r = evaluate_well(well, folder)
            if r:
                well_results.append(r)
        dt = time.time() - t0
        if well_results:
            ids = [r['identity'] for r in well_results]
            ns = [r['n_count'] for r in well_results]
            seq_lens = [r['seq_len'] for r in well_results]
            print(f"  {variant:15s} ({name:30s}): "
                  f"{len(well_results):3d} wells, "
                  f"id={np.mean(ids):.4f} ±{np.std(ids):.4f}, "
                  f"N={np.mean(ns):.1f}, "
                  f"len={np.mean(seq_lens):.0f}bp, "
                  f"time={dt:.1f}s")
            results[variant] = {
                'method': f'ESD {name}',
                'n_wells': len(well_results),
                'mean_identity': float(np.mean(ids)),
                'median_identity': float(np.median(ids)),
                'std_identity': float(np.std(ids)),
                'min_identity': float(np.min(ids)),
                'max_identity': float(np.max(ids)),
                'mean_n_count': float(np.mean(ns)),
                'mean_seq_len': float(np.mean(seq_lens)),
            }
    return results

def main():
    # Get all wells
    data_dir = os.path.join(BASE_DIR, DATA_SUBDIR)
    wells = sorted([f.replace('.rsd', '') for f in os.listdir(data_dir)
                   if f.endswith('.rsd')])
    print(f"Found {len(wells)} wells")
    print(f"M13 reference: {len(M13_REFERENCE)} bp\n")
    print(f"{'='*80}")
    print(f"  ESD CALLER EVALUATION VS M13 REFERENCE")
    print(f"{'='*80}\n")

    results = evaluate_all_variants(wells)

    # Print summary table
    print(f"\n{'='*80}")
    print(f"  SUMMARY (sorted by mean identity)")
    print(f"{'='*80}")
    print(f"{'Variant':15s} {'Method':30s} {'Wells':>6s} {'Mean Id':>8s} {'Std':>6s} "
          f"{'Max':>6s} {'Min':>6s} {'N/well':>7s} {'Len':>6s}")
    print('-' * 80)
    sorted_variants = sorted(results.items(),
                             key=lambda x: x[1]['mean_identity'], reverse=True)
    for variant, r in sorted_variants:
        print(f"{variant:15s} {r['method']:30s} {r['n_wells']:6d} "
              f"{r['mean_identity']:8.4f} {r['std_identity']:6.4f} "
              f"{r['max_identity']:6.4f} {r['min_identity']:6.4f} "
              f"{r['mean_n_count']:7.1f} {r['mean_seq_len']:6.0f}")

    # Save
    outpath = os.path.join(BASE_DIR, 'baseline_evaluation.json')
    with open(outpath, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\nResults saved to {outpath}")
    
    # Also print best well per variant
    for variant, folder in ESD_FOLDERS.items():
        best_id, best_well = 0, ''
        for well in wells[:24]:
            r = evaluate_well(well, folder)
            if r and r['identity'] > best_id:
                best_id = r['identity']
                best_well = well
        worst_id, worst_well = 1, ''
        for well in wells[:24]:
            r = evaluate_well(well, folder)
            if r and r['identity'] < worst_id:
                worst_id = r['identity']
                worst_well = well
        print(f"  {variant}: best={best_well} ({best_id:.4f}), "
              f"worst={worst_well} ({worst_id:.4f})")

if __name__ == '__main__':
    main()
