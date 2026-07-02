"""
Apply TraceTuner spectral separation to RSD data and evaluate basecalling accuracy.
Uses edlib alignment to M13 reference for each well.
"""

import sys
import os
import json
import numpy as np
from pathlib import Path

sys.path.insert(0, '/media/tv/78B0C7DE1FA7081C/electropherogram')
from tracetuner_separation import trace_tuner_separate
from m13_reference import M13Reference

# Configuration
RSD_DIR = '/media/tv/78B0C7DE1FA7081C/MiSeq_ABCC2_N1'
M13_REF_PATH = '/media/tv/78B0C7DE1FA7081C/electropherogram/m13_ref.fasta'
PLATE_NAME = 'ABCC2_N1'
MAX_WELLS = 5  # quick test


def read_rsd_traces(rsd_path):
    """Read raw 4-channel traces from an RSD file.
    Returns (4, n_scans) numpy array."""
    from struct import unpack
    
    with open(rsd_path, 'rb') as f:
        data = f.read()
    
    # Find channel data markers (same as in gui.py/peak_detector.py)
    ch_markers = [b'Scans1', b'Scans2', b'Scans3', b'Scans4']
    traces = []
    
    for marker in ch_markers:
        idx = data.find(marker)
        if idx < 0:
            traces.append(np.zeros(10000, dtype=np.int16))
            continue
        
        # Find the data block after the marker
        # Usually stored as uint16/int16 after the tag
        header = data[idx:idx+200]
        
        # Try to find data length and offset
        # Typical RSD format: tag + 4-byte offset + 4-byte length + data
        data_offset = idx + 8  # skip tag + reserved
        data_len = len(data) - data_offset
        
        # Try int16
        try:
            ch_data = np.frombuffer(data[data_offset:data_offset + data_len], 
                                     dtype=np.int16)
            # Trim trailing zeros
            ch_data = ch_data[:np.where(ch_data != 0)[0][-1] + 1] if np.any(ch_data != 0) else ch_data
            traces.append(ch_data.astype(np.float64))
        except:
            traces.append(np.zeros(10000, dtype=np.float64))
    
    # Pad to same length
    max_len = max(len(t) for t in traces)
    padded = np.zeros((4, max_len), dtype=np.float64)
    for i, t in enumerate(traces):
        padded[i, :len(t)] = t
    
    return padded


def read_rsd_traces_proper(rsd_path):
    """Use the existing RSD reader from gui.py or peak_detector.py."""
    sys.path.insert(0, str(Path(rsd_path).parent))
    
    try:
        from rsd_reader import read_rsd
        return read_rsd(rsd_path)
    except ImportError:
        pass
    
    try:
        from peak_detector import read_rsd_file
        data = read_rsd_file(rsd_path)
        traces = np.zeros((4, len(data['scan_values'])), dtype=np.float64)
        for i, ch_name in enumerate(['Channel1', 'Channel2', 'Channel3', 'Channel4']):
            traces[i] = np.array(data[ch_name], dtype=np.float64)
        return traces
    except ImportError:
        pass
    
    # Fall back to manual read
    return read_rsd_traces(rsd_path)


def max_channel_basecall(separated, peak_positions):
    """Simple basecalling: at each peak position, pick channel with max signal.
    Channel order: [Ch1, Ch2, Ch3, Ch4] mapped to bases based on chemistry."""
    bases = []
    for pos in peak_positions:
        if pos < 0 or pos >= separated.shape[1]:
            bases.append('N')
            continue
        vals = separated[:, int(pos)]
        max_ch = np.argmax(vals)
        # Standard ET chemistry mapping from RSD reader
        mapping = {0: 'A', 1: 'C', 2: 'G', 3: 'T'}  # adjust as needed
        bases.append(mapping.get(max_ch, 'N'))
    return ''.join(bases)


def main():
    ref = M13Reference(M13_REF_PATH)
    rsd_dir = Path(RSD_DIR)
    
    # Find RSD files
    rsd_files = sorted(rsd_dir.glob('*.rsd'))
    print(f"Found {len(rsd_files)} RSD files")
    
    results = {}
    for rsd_path in rsd_files[:MAX_WELLS]:
        well = rsd_path.stem
        print(f"\nProcessing {well}...")
        
        try:
            traces = read_rsd_traces_proper(str(rsd_path))
            print(f"  Traces shape: {traces.shape}")
        except Exception as e:
            print(f"  Error reading: {e}")
            continue
        
        # Apply TraceTuner separation
        separated = trace_tuner_separate(traces)
        
        # Need peak positions for basecalling
        # Use simple peak detection on sum of all channels
        sum_trace = np.sum(separated, axis=0)
        
        # Simple peak detection
        from scipy.signal import find_peaks
        peaks, _ = find_peaks(sum_trace, 
                               distance=8,  # ~12 scan spacing
                               height=np.percentile(sum_trace[sum_trace > 0], 50))
        
        print(f"  Found {len(peaks)} peaks")
        
        # Basecall
        called_seq = max_channel_basecall(separated, peaks)
        
        # Align to M13
        result = ref.align(called_seq)
        
        if result:
            identity = result['matches'] / result['alignment_length'] * 100 if result['alignment_length'] > 0 else 0
            results[well] = {
                'identity': identity,
                'matches': result['matches'],
                'alignment_length': result['alignment_length'],
                'called_length': len(called_seq),
                'num_peaks': len(peaks)
            }
            print(f"  Identity vs M13: {identity:.1f}% "
                  f"({result['matches']}/{result['alignment_length']})")
        else:
            print(f"  No alignment found")
    
    # Summary
    if results:
        identities = [r['identity'] for r in results.values()]
        print(f"\n{'='*50}")
        print(f"Summary ({len(results)} wells):")
        print(f"  Mean identity: {np.mean(identities):.1f}%")
        print(f"  Min: {np.min(identities):.1f}%  Max: {np.max(identities):.1f}%")
        
        # Save results
        out_path = f'tracetuner_results_{PLATE_NAME}.json'
        with open(out_path, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"  Results saved to {out_path}")
    else:
        print("\nNo results to report")


if __name__ == '__main__':
    main()
