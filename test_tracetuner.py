"""
Apply TraceTuner spectral separation to RSD data and evaluate
basecalling accuracy vs M13 reference.
"""

import sys, os, json, itertools
import numpy as np
from pathlib import Path

sys.path.insert(0, '/media/tv/78B0C7DE1FA7081C/electropherogram')
from tracetuner_separation import trace_tuner_separate
from extract_training_data import parse_rsd, parse_esd
from simple_align import align_to_m13

BASE_DIR = '/media/tv/78B0C7DE1FA7081C/electropherogram'
DATA_DIR = os.path.join(BASE_DIR, 'MB1000_M13_DT')
ESD_SUBDIR = 'MB1000_M13_DT_Cp312_MD1'
MAX_WELLS = 96


def get_raw_traces(rsd_path):
    df = parse_rsd(str(rsd_path))
    ch = df[['Channel1', 'Channel2', 'Channel3', 'Channel4']].values.T
    return ch.astype(np.float64)


def basecall_at_positions(separated, positions, chem_map):
    seq_chars = []
    for pos in positions:
        pos = int(pos)
        if pos < 0 or pos >= separated.shape[1]:
            seq_chars.append('N')
        else:
            ch = int(np.argmax(separated[:, pos]))
            seq_chars.append(chem_map.get(ch, 'N'))
    return ''.join(seq_chars)


def evaluate_well(separated, esd, chem_map):
    positions = esd.get('peak_positions')
    if positions is None:
        positions = esd.get('bases_positions')
    if positions is None or not esd.get('sequence', ''):
        return None

    positions = positions.astype(int)
    n = min(len(positions), len(esd['sequence']))
    if n == 0:
        return None
    positions = positions[:n]

    called = basecall_at_positions(separated, positions, chem_map)
    result = align_to_m13(called)
    if result is None:
        return None
    return result['identity']


def find_best_chemistry(raw, esd):
    """Try all 24 chemistry permutations. Separate once, try all maps."""
    bases = ['A', 'C', 'G', 'T']
    best_identity = 0
    best_map = None
    separated = trace_tuner_separate(raw.copy())
    for perm in itertools.permutations(range(4)):
        chem_map = {i: bases[perm[i]] for i in range(4)}
        identity = evaluate_well(separated, esd, chem_map)
        if identity and identity > best_identity:
            best_identity = identity
            best_map = chem_map
    return best_map, best_identity


def main():
    rsd_dir = Path(DATA_DIR)
    esd_dir = Path(DATA_DIR) / ESD_SUBDIR

    rsd_files = sorted(rsd_dir.glob('*.rsd'))
    if MAX_WELLS:
        rsd_files = rsd_files[:MAX_WELLS]

    print(f"Found {len(rsd_files)} RSD files")

    # Determine chemistry from first well
    first = rsd_files[0]
    well = first.stem
    esd = parse_esd(str(esd_dir / f"{well}.esd"))
    raw = get_raw_traces(first)
    print(f"Determining chemistry from {well}...")
    best_map, best_id = find_best_chemistry(raw, esd)
    print(f"  Best chemistry: {best_map}  ({best_id:.1f}%)")

    # Evaluate all wells
    print(f"\nEvaluating all wells with best chemistry...")
    all_results = []
    for rsd_path in rsd_files:
        well = rsd_path.stem
        esd_path = esd_dir / f"{well}.esd"
        if not esd_path.exists():
            continue
        try:
            raw = get_raw_traces(rsd_path)
            esd = parse_esd(str(esd_path))
        except Exception:
            continue

        separated = trace_tuner_separate(raw)
        identity = evaluate_well(separated, esd, best_map)
        if identity is not None:
            all_results.append({'well': well, 'identity': round(identity, 1)})

    if all_results:
        ids = [r['identity'] for r in all_results]
        print(f"\n{'='*55}")
        print(f"TraceTuner vs M13 ({len(all_results)} wells, Cp312 peaks):")
        print(f"  Mean: {np.mean(ids):.1f}%  Stdev: {np.std(ids):.1f}%")
        print(f"  Min: {np.min(ids):.1f}%   Max: {np.max(ids):.1f}%")

        json_path = os.path.join(BASE_DIR, 'tracetuner_result.json')
        with open(json_path, 'w') as f:
            json.dump(all_results, f, indent=2)
        print(f"Saved to {json_path}")
    else:
        print("No results.")


if __name__ == '__main__':
    main()
