import numpy as np
import struct
import os
from Bio import SeqIO

def read_rsd(filepath):
    """
    Read a MegaBACE .rsd file and return the four dye traces as a dict of numpy arrays.
    Assumes standard format: header (512 bytes) followed by interleaved 16-bit ints.
    """
    with open(filepath, 'rb') as f:
        # Read header (first 512 bytes)
        header = f.read(512)
        # Extract number of scans from header (example offset, adjust if needed)
        # In many MegaBACE files, the number of scans is at byte 36 (4 bytes)
        num_scans = struct.unpack('<I', header[36:40])[0]
        # Number of dyes is usually 4
        num_dyes = 4
        # Read the rest of the file as 16-bit unsigned ints
        data = np.frombuffer(f.read(), dtype='<u2')
        # Reshape: each scan has 4 values (A, C, G, T) interleaved
        # Usually order: A, C, G, T (but check your files)
        # We'll assume order is A, C, G, T
        data = data.reshape((num_scans, num_dyes))
        traces = {
            'A': data[:, 0].astype(np.float32),
            'C': data[:, 1].astype(np.float32),
            'G': data[:, 2].astype(np.float32),
            'T': data[:, 3].astype(np.float32)
        }
        return traces

def read_esd(filepath):
    """
    Read an .esd file (basecalled by Cimarron) and return the sequence and quality scores.
    Expected format: first line = sequence, second line = quality scores (space-separated integers).
    If quality scores are not present, return dummy qualities (all 40).
    """
    with open(filepath, 'r') as f:
        lines = [l.strip() for l in f if l.strip()]
    if not lines:
        raise ValueError(f"Empty .esd file: {filepath}")
    seq = lines[0]
    # Try to parse qualities from second line
    if len(lines) >= 2:
        try:
            quals = list(map(int, lines[1].split()))
            # if lengths don't match, fallback to dummy
            if len(quals) != len(seq):
                quals = [40] * len(seq)
        except:
            quals = [40] * len(seq)
    else:
        quals = [40] * len(seq)
    return seq, np.array(quals, dtype=np.int32)

def preprocess_traces(traces, target_len=None):
    """
    Apply basic preprocessing: subtract baseline, normalize, and optionally pad/truncate.
    Returns a numpy array of shape (time_steps, 4).
    """
    # Stack the four traces
    data = np.stack([traces['A'], traces['C'], traces['G'], traces['T']], axis=1)
    # Baseline correction: subtract moving minimum (or just global min)
    data = data - np.min(data, axis=0, keepdims=True)
    # Scale to [0,1]
    max_val = np.max(data, axis=0, keepdims=True)
    max_val[max_val == 0] = 1  # avoid division by zero
    data = data / max_val
    # Optionally truncate/pad to fixed length for batching (not needed for CTC)
    if target_len is not None:
        if data.shape[0] < target_len:
            pad = np.zeros((target_len - data.shape[0], 4))
            data = np.vstack([data, pad])
        elif data.shape[0] > target_len:
            data = data[:target_len, :]
    return data