"""
Apply TraceTuner spectral separation to RSD data and evaluate
basecalling accuracy vs M13 reference.
"""

import sys, os, json, struct
import numpy as np
import pandas as pd
from pathlib import Path

sys.path.insert(0, '/media/tv/78B0C7DE1FA7081C/electropherogram')
from tracetuner_separation import trace_tuner_separate
from m13_reference import M13Reference
from extract_training_data import parse_rsd, parse_esd

RSD_DIR = '/media/tv/78B0C7DE1FA7081C/MiSeq_ABCC2_N1'
ESD_DIR = '/media/tv/78B0C7DE1FA7081C/MiSeq_ABCC2_N1/CpG_Cp310_ESD'
M13_REF_PATH = '/media/tv/78B0C7DE1FA7081C/electropherogram/m13_ref.fasta'
PLATE_NAME = 'ABCC2_N1'
MAX_WELLS = None  # None = all

# Chemistry: Channel1-4 -> base
# From RSD: Ch1=ET-R6G, Ch2=ET-R110, Ch3=ET-ROX, Ch4=ET-TAMRA
# Mapping determined empirically from ESD peak channel assignments
# Let's try all 24 permutations and pick the best
CHEM_MAP = {0: 'A', 1: 'C', 2: 'G', 3: 'T'}


def get_raw_traces(rsd_path):
    df = parse_rsd(str(rsd_path))
    ch = df[['Channel1', 'Channel2', 'Channel3', 'Channel4']].values.T
    return ch.astype(np.float64)


def basecall_at_positions(separated, positions):
    """Call base at each position using max channel."""
    seq_chars = []
    for pos in positions:
        pos = int(pos)
        if pos < 0 or pos >= separated.shape[1]:
            seq_chars.append('N')
        else:
            vals = separated[:, pos]
            ch = int(np.argmax(vals))
            seq_chars.append(CHEM_MAP.get(ch, 'N'))
    return ''.join(seq_chars)


def evaluate(separated, esd, ref, well):
    """Evaluate basecalling accuracy vs M13 at ESD peak positions."""
    positions = esd.get('peak_positions')
    if positions is None:
        positions = esd.get('bases_positions')
    seq_esd = esd.get('sequence', '')

    if positions is None or not seq_esd:
        return None

    positions = positions.astype(int)
    n = min(len(positions), len(seq_esd))
    positions = positions[:n]
    seq_esd = seq_esd[:n]

    # Call bases at ESD peak positions
    called = basecall_at_positions(separated, positions)

    # Align to M13
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
        'esd_len': len(seq_esd),
        'n_positions': n,
    }


def main():
    ref = M13Reference(M13_REF_PATH)
    rsd_dir = Path(RSD_DIR)

    rsd_files = sorted(rsd_dir.glob('*.rsd'))
    if MAX_WELLS:
        rsd_files = rsd_files[:MAX_WELLS]

    print(f"Found {len(rsd_files)} RSD files")

    all_results = []
    for rsd_path in rsd_files:
        well = rsd_path.stem

        # Find matching ESD
        esd_path = Path(ESD_DIR) / f"{well}.esd"
        if not esd_path.exists():
            print(f"  {well}: no ESD file")
            continue

        try:
            raw = get_raw_traces(rsd_path)
            esd = parse_esd(str(esd_path))
        except Exception as e:
            print(f"  {well}: error reading: {e}")
            continue

        # Apply TraceTuner separation
        separated = trace_tuner_separate(raw)

        result = evaluate(separated, esd, ref, well)
        if result:
            all_results.append(result)
            print(f"  {well}: {result['identity']:.1f}% "
                  f"({result['matches']}/{result['aln_len']}) "
                  f"peaks={result['n_positions']}")
        else:
            print(f"  {well}: no alignment")

    if all_results:
        identities = [r['identity'] for r in all_results]
        print(f"\n{'='*50}")
        print(f"TraceTuner results ({len(all_results)} wells):")
        print(f"  Mean: {np.mean(identities):.1f}%  "
              f"Min: {np.min(identities):.1f}%  "
              f"Max: {np.max(identities):.1f}%")

        json_path = f'tracetuner_results_{PLATE_NAME}.json'
        with open(json_path, 'w') as f:
            json.dump(all_results, f, indent=2)
        print(f"  Saved to {json_path}")


if __name__ == '__main__':
    main()
