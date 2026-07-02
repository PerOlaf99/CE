"""
Apply TraceTuner spectral separation to RSD data and evaluate
basecalling accuracy vs M13 reference.
"""

import sys, os, json
import numpy as np
from pathlib import Path

sys.path.insert(0, '/media/tv/78B0C7DE1FA7081C/electropherogram')
from tracetuner_separation import trace_tuner_separate
from m13_reference import M13Reference
from extract_training_data import parse_rsd, parse_esd

BASE_DIR = '/media/tv/78B0C7DE1FA7081C/electropherogram'
DATA_DIR = os.path.join(BASE_DIR, 'MB1000_M13_DT')
ESD_SUBDIR = 'MB1000_M13_DT_Cp312_MD1'
M13_REF_PATH = os.path.join(BASE_DIR, 'm13_ref.fasta')
MAX_WELLS = 96

# Chemistry: Channel 0-3 -> base after TraceTuner separation
# We'll try all 24 permutations and pick the best
CHEM_MAP = {0: 'A', 1: 'C', 2: 'G', 3: 'T'}


def get_raw_traces(rsd_path):
    df = parse_rsd(str(rsd_path))
    ch = df[['Channel1', 'Channel2', 'Channel3', 'Channel4']].values.T
    return ch.astype(np.float64)


def basecall_at_positions(separated, positions, chem_map=None):
    if chem_map is None:
        chem_map = CHEM_MAP
    seq_chars = []
    for pos in positions:
        pos = int(pos)
        if pos < 0 or pos >= separated.shape[1]:
            seq_chars.append('N')
        else:
            ch = int(np.argmax(separated[:, pos]))
            seq_chars.append(chem_map.get(ch, 'N'))
    return ''.join(seq_chars)


def evaluate_well(well, separated, esd, ref, chem_map=None):
    positions = esd.get('peak_positions')
    if positions is None:
        positions = esd.get('bases_positions')
    seq_esd = esd.get('sequence', '')

    if positions is None or not seq_esd:
        return None

    positions = positions.astype(int)
    n = min(len(positions), len(seq_esd))
    if n == 0:
        return None
    positions = positions[:n]

    called = basecall_at_positions(separated, positions, chem_map)
    result = ref.align(called)
    if result is None:
        return None

    identity = result['matches'] / result['alignment_length'] * 100
    return {
        'well': well,
        'identity': round(identity, 1),
        'matches': result['matches'],
        'aln_len': result['alignment_length'],
        'called_len': len(called),
        'esd_len': n,
    }


def try_all_chemistries(raw, esd, ref):
    """Try all 24 chemistry permutations and find the best."""
    import itertools
    bases = ['A', 'C', 'G', 'T']
    best = None
    best_map = None
    for perm in itertools.permutations(range(4)):
        chem_map = {i: bases[perm[i]] for i in range(4)}
        separated = trace_tuner_separate(raw.copy())
        result = evaluate_well('', separated, esd, ref, chem_map)
        if result and (best is None or result['identity'] > best['identity']):
            best = result
            best_map = chem_map
    return best, best_map


def main():
    ref = M13Reference(M13_REF_PATH)
    rsd_dir = Path(DATA_DIR)
    esd_dir = Path(DATA_DIR) / ESD_SUBDIR

    rsd_files = sorted(rsd_dir.glob('*.rsd'))
    if MAX_WELLS:
        rsd_files = rsd_files[:MAX_WELLS]

    print(f"Found {len(rsd_files)} RSD files in {DATA_DIR}")

    # First: determine chemistry mapping from first well
    print("\nDetermining best chemistry mapping from first well...")
    first_rsd = rsd_files[0]
    try:
        raw = get_raw_traces(first_rsd)
        esd = parse_esd(str(esd_dir / f"{first_rsd.stem}.esd"))
        best_result, best_map = try_all_chemistries(raw, esd, ref)
        print(f"  Best chemistry: {best_map}")
        print(f"  Identity: {best_result['identity']:.1f}%")
    except Exception as e:
        print(f"  Error: {e}")
        best_map = CHEM_MAP

    # Now evaluate all wells with best chemistry
    print(f"\nEvaluating all {len(rsd_files)} wells with best chemistry...")
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
        result = evaluate_well(well, separated, esd, ref, best_map)
        if result:
            all_results.append(result)

    if all_results:
        identities = [r['identity'] for r in all_results]
        print(f"\n{'='*60}")
        print(f"TraceTuner results ({len(all_results)} wells, Cp312 peak positions):")
        print(f"  Mean:  {np.mean(identities):.1f}%")
        print(f"  Stdev: {np.std(identities):.1f}%")
        print(f"  Min:   {np.min(identities):.1f}%")
        print(f"  Max:   {np.max(identities):.1f}%")

        json_path = os.path.join(BASE_DIR, 'tracetuner_results.json')
        with open(json_path, 'w') as f:
            json.dump(all_results, f, indent=2)
        print(f"\nSaved to {json_path}")
    else:
        print("\nNo results.")


if __name__ == '__main__':
    main()
