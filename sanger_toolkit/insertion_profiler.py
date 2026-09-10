#!/usr/bin/env python3
"""Profile insertion errors vs M13 reference for stutter classification.

For each insertion error, extracts:
  - position in read (quartile)
  - spacing from previous/next peak
  - spacing ratio vs local median
  - CNN pmax at that position
  - CNN runner-up probability
  - peak height
  - homopolymer context (in run? length? base?)
  - base identity

Output: CSV file for analysis.
"""
import os, sys, glob
HERE = os.path.dirname(os.path.realpath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, ROOT)
os.environ.setdefault('TF_CPP_MIN_LOG_LEVEL', '3')

import numpy as np
import csv
import cimarrontv as cim
from extract_training_data import parse_esd

PLATE = os.path.join(ROOT, 'MB1000_M13_DT')
GT_DIR = os.path.join(ROOT, 'ground_truth', 'MB1000_M13_DT_Cp312_MD1')
MODEL_PAT = os.path.join(ROOT, '02_denovo_cnn_ensemble_91.53pct', 'base_caller_model*.keras')


def load_ref():
    import json
    settings_path = os.path.join(ROOT, 'settingsV10.json')
    with open(settings_path) as f:
        s = json.load(f)
    ref = ''.join(c for c in s['reference_dna'] if c in 'ACGT')
    from extract_m13_clean_training import rc
    return rc(ref)


def find_homopolymerRuns(ref, min_len=2):
    """Find all homopolymer runs in reference. Returns list of (base, start, end, length)."""
    runs = []
    i = 0
    while i < len(ref):
        base = ref[i]
        j = i + 1
        while j < len(ref) and ref[j] == base:
            j += 1
        length = j - i
        if length >= min_len:
            runs.append((base, i, j, length))
        i = j
    return runs


def in_homopolymer(pos, runs):
    """Check if position falls in a homopolymer run. Returns (base, run_len) or None."""
    for base, start, end, length in runs:
        if start <= pos < end:
            return (base, length)
    return None


def decompose_with_positions(query, ref):
    """Align query to ref and return detailed per-error info.
    Returns list of dicts for each insertion error."""
    from extract_m13_clean_training import seed_sw_align
    al = seed_sw_align(query, ref)
    if al is None:
        return None
    q, r = al

    insertions = []
    qi = 0  # query position (non-gap)
    ri = 0  # ref position (non-gap)
    n = len(q)

    for a, b in zip(q, r):
        if a == '-':
            # Insertion: extra base in query (over-call)
            insertions.append({
                'query_pos': qi,
                'ref_pos': ri,
                'quartile': min(4, 4 * qi // max(1, n - 1) + 1),
                'base': b if b != '-' else 'N',
                'type': 'insertion',
            })
            ri += 1
        elif b == '-':
            # Deletion: missing base in query
            qi += 1
        else:
            if a != b:
                pass  # mismatch - skip for now
            qi += 1
            ri += 1

    return insertions


def profile_well(w, models, ref, hp_runs):
    """Profile insertion errors for one well. Returns list of feature dicts."""
    rsd = os.path.join(PLATE, f'{w}.rsd')
    esd = os.path.join(GT_DIR, f'{w}.esd')
    if not os.path.isfile(rsd) or not os.path.isfile(esd):
        return []

    ch, scans = cim.read_rsd(rsd)
    chw = np.asarray(ch, dtype=np.float64)
    if chw.ndim == 2 and chw.shape[0] == 4 and chw.shape[0] <= chw.shape[1]:
        chw = chw.T

    # Get reference
    d = parse_esd(esd)
    dll_seq = ''.join(c for c in d.get('sequence', '') if c in 'ACGTN')

    # Call with CNN ensemble
    from perfect_basecaller import call_raw, cnn_probs
    result = call_raw(rsd, models=models, refine=True)
    our_seq = result['seq']
    our_scans = result['scans']
    our_conf = result['conf']

    # Get full CNN probabilities for all peak positions
    probs = cnn_probs(models, chw, our_scans)
    pmax = probs.max(1)
    runner_up = np.sort(probs, axis=1)[:, -2]  # second highest

    # Peak heights (from raw total intensity at each peak position)
    total_env = np.max(chw, axis=1)
    peak_heights = [total_env[min(int(s), len(total_env)-1)] for s in our_scans]

    # Find insertion errors
    insertions = decompose_with_positions(our_seq, ref)
    if not insertions:
        return []

    # Compute spacing features
    scan_diffs = np.diff(our_scans)
    local_medians = []
    for i in range(len(our_scans)):
        lo = max(0, i - 5)
        hi = min(len(scan_diffs), i + 5)
        if hi > lo + 1:
            local_medians.append(np.median(scan_diffs[lo:hi]))
        else:
            local_medians.append(np.median(scan_diffs) if len(scan_diffs) > 0 else 10.0)
    local_medians = np.array(local_medians)

    features = []
    for ins in insertions:
        qi = ins['query_pos']
        if qi >= len(our_scans):
            continue

        # Spacing from previous peak
        if qi > 0:
            gap_prev = our_scans[qi] - our_scans[qi - 1]
        else:
            gap_prev = local_medians[qi] if qi < len(local_medians) else 10.0

        # Spacing to next peak
        if qi < len(our_scans) - 1:
            gap_next = our_scans[qi + 1] - our_scans[qi]
        else:
            gap_next = local_medians[qi] if qi < len(local_medians) else 10.0

        # Spacing ratio vs local median
        local_med = local_medians[qi] if qi < len(local_medians) else 10.0
        ratio_prev = gap_prev / local_med if local_med > 0 else 1.0
        ratio_next = gap_next / local_med if local_med > 0 else 1.0

        # Homopolymer context
        hp = in_homopolymer(ins['ref_pos'], hp_runs)

        features.append({
            'well': w,
            'query_pos': qi,
            'ref_pos': ins['ref_pos'],
            'quartile': ins['quartile'],
            'base': ins['base'],
            'gap_prev': gap_prev,
            'gap_next': gap_next,
            'ratio_prev': ratio_prev,
            'ratio_next': ratio_next,
            'local_median': local_med,
            'pmax': pmax[qi],
            'runner_up': runner_up[qi],
            'peak_height': peak_heights[qi],
            'confidence': our_conf[qi],
            'in_homopolymer': hp is not None,
            'hp_base': hp[0] if hp else '',
            'hp_length': hp[1] if hp else 0,
            'read_len': len(our_seq),
        })

    return features


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--wells', nargs='*', default=None,
                        help='Wells to process (default: all 96)')
    parser.add_argument('--out', default='insertion_profile.csv')
    args = parser.parse_args()

    from perfect_basecaller import load_ensemble
    models = load_ensemble([MODEL_PAT])
    print(f'Loaded {len(models)} CNN models')

    ref = load_ref()
    print(f'Reference: {len(ref)} bp')

    hp_runs = find_homopolymerRuns(ref, min_len=2)
    print(f'Homopolymer runs: {len(hp_runs)} (min len 2)')

    if args.wells:
        wells = args.wells
    else:
        wells = [f'{r}{c:02d}' for r in 'ABCDEFGH' for c in range(1, 13)]

    all_features = []
    for i, w in enumerate(wells):
        try:
            feats = profile_well(w, models, ref, hp_runs)
            all_features.extend(feats)
            ins_count = len(feats)
            hp_count = sum(1 for f in feats if f['in_homopolymer'])
            print(f'  [{i+1}/{len(wells)}] {w}: {ins_count} insertions ({hp_count} in homopolymers)', flush=True)
        except Exception as e:
            print(f'  [{i+1}/{len(wells)}] {w}: ERR {e}', flush=True)

    if not all_features:
        print('No insertions found!')
        return

    # Write CSV
    fieldnames = list(all_features[0].keys())
    with open(args.out, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_features)

    print(f'\nWrote {len(all_features)} insertion records to {args.out}')

    # Summary statistics
    print(f'\n=== SUMMARY ===')
    hp_ins = [f for f in all_features if f['in_homopolymer']]
    non_hp = [f for f in all_features if not f['in_homopolymer']]
    print(f'Total insertions: {len(all_features)}')
    print(f'  In homopolymers: {len(hp_ins)} ({100*len(hp_ins)/len(all_features):.1f}%)')
    print(f'  Outside: {len(non_hp)} ({100*len(non_hp)/len(all_features):.1f}%)')

    if hp_ins:
        print(f'\nHomopolymer insertions:')
        hp_lens = [f['hp_length'] for f in hp_ins]
        print(f'  Run lengths: min={min(hp_lens)} max={max(hp_lens)} mean={np.mean(hp_lens):.1f}')
        hp_bases = {}
        for f in hp_ins:
            hp_bases[f['hp_base']] = hp_bases.get(f['hp_base'], 0) + 1
        for b, c in sorted(hp_bases.items()):
            print(f'  {b}: {c} ({100*c/len(hp_ins):.1f}%)')

    print(f'\nCNN scores:')
    hp_pmax = [f['pmax'] for f in hp_ins] if hp_ins else []
    non_pmax = [f['pmax'] for f in non_hp] if non_hp else []
    if hp_pmax:
        print(f'  In homopolymer:  pmax mean={np.mean(hp_pmax):.3f} median={np.median(hp_pmax):.3f}')
    if non_pmax:
        print(f'  Outside:         pmax mean={np.mean(non_pmax):.3f} median={np.median(non_pmax):.3f}')

    print(f'\nSpacing (gap_prev / local_median):')
    hp_ratios = [f['ratio_prev'] for f in hp_ins] if hp_ins else []
    non_ratios = [f['ratio_prev'] for f in non_hp] if non_hp else []
    if hp_ratios:
        print(f'  In homopolymer:  mean={np.mean(hp_ratios):.3f} median={np.median(hp_ratios):.3f}')
    if non_ratios:
        print(f'  Outside:         mean={np.mean(non_ratios):.3f} median={np.median(non_ratios):.3f}')

    print(f'\nQuartile distribution:')
    for q in range(1, 5):
        q_ins = [f for f in all_features if f['quartile'] == q]
        print(f'  Q{q}: {len(q_ins)} ({100*len(q_ins)/len(all_features):.1f}%)')


if __name__ == '__main__':
    main()
