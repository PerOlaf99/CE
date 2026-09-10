"""ABI (ABIF) and SCF file format reader for Sanger sequencing traces.

Provides a unified interface to read chromatogram data from:
- ABI (.ab1) — Applied Biosystems ABIF binary format (most common)
- SCF (.scf) — Staden chromatogram format

Returns a standardized dict compatible with the existing RSD/ESD pipeline.
"""
import struct
import numpy as np
import os


# ── ABI (ABIF) format ─────────────────────────────────────────────────

# ABIF tag names we need
_ABI_TAGS = {
    'DATA': 9,    # Raw trace data (1002-1005 = A, C, G, T channels)
    'FWO_1': 12,  # Base order for DATA tags
    'PBAS': 13,   # Base calls (ASCII)
    'PCON': 12,   # Quality values (Phred-like)
    'PLOC': 10,   # Peak locations
    'PhCH': 31,   # Chemistry type
    'SMPL': 15,   # Sample name
    'DyeN': 18,   # Dye names
    'DATA1': 9,   # Same as DATA, tag number 1002-1005
    'RUND': 4,    # Run date
    'RUNT': 5,    # Run time
    'LNTG': 1,    # Lane number
    'SpTab': 30,  # Mobility table
}

# Channel indices for DATA tags: tag numbers 1002-1005
_ABI_DATA_TAGS = {1002: 0, 1003: 1, 1004: 2, 1005: 3}


def _read_abi_tags(f):
    """Parse ABIF header and read all tags. Returns dict of tag_name -> [(element, par, num, size, dtype, data)]."""
    f.seek(0)
    magic = f.read(4)
    if magic != b'ABIF':
        raise ValueError(f'Not an ABI file (magic: {magic!r})')
    
    version = struct.unpack('>H', f.read(2))[0]
    # Skip padding
    f.read(6)
    
    # First directory entry
    dir_offset = struct.unpack('>I', f.read(4))[0]
    n_dir_entries = struct.unpack('>I', f.read(4))[0]
    
    tags = {}
    f.seek(dir_offset)
    
    for _ in range(n_dir_entries):
        tag_name = f.read(4).decode('ascii', errors='replace')
        element = struct.unpack('>H', f.read(2))[0]
        par = struct.unpack('>H', f.read(2))[0]
        num = struct.unpack('>I', f.read(4))[0]
        size = struct.unpack('>I', f.read(4))[0]
        dtype = struct.unpack('>H', f.read(2))[0]
        # Skip reserved bytes
        f.read(6)
        data_offset = struct.unpack('>I', f.read(4))[0]
        
        # Read data if small enough (inline) or from offset
        if size <= 4:
            # Data is inline in the offset field
            raw_data = f.read(4)
            f.read(4)  # padding
        else:
            f.read(4)  # padding
            saved_pos = f.tell()
            f.seek(data_offset)
            raw_data = f.read(size)
            f.seek(saved_pos)
        
        if tag_name not in tags:
            tags[tag_name] = []
        tags[tag_name].append({
            'element': element,
            'par': par,
            'num': num,
            'size': size,
            'dtype': dtype,
            'data': raw_data,
        })
    
    return tags, version


def _decode_abi_data(entry, dtype_code):
    """Decode a DATA tag entry into a numpy array."""
    raw = entry['data']
    if dtype_code == 2:  # int8
        return np.frombuffer(raw, dtype=np.int8)
    elif dtype_code == 3:  # int16
        return np.frombuffer(raw, dtype=np.int16)
    elif dtype_code == 4:  # int32
        return np.frombuffer(raw, dtype=np.int32)
    elif dtype_code == 1:  # byte (unsigned)
        return np.frombuffer(raw, dtype=np.uint8)
    elif dtype_code == 5:  # float
        return np.frombuffer(raw, dtype=np.float32)
    elif dtype_code == 18:  # tagged array
        return np.frombuffer(raw, dtype=np.uint8)
    else:
        return np.frombuffer(raw, dtype=np.int32)


def read_abi(path):
    """Read an ABI (.ab1) file and return a dict:
    
    Returns:
        {
            'format': 'abi',
            'traces': np.ndarray of shape (n_scans, 4) — raw trace data [A, C, G, T],
            'sequence': str — base-called sequence,
            'positions': np.ndarray — peak positions (scan indices),
            'qualities': np.ndarray — per-base Phred quality scores,
            'sample_name': str,
            'dye_names': list of str,
            'n_scans': int,
            'channel_order': list of 4 single-letter base labels,
        }
    """
    with open(path, 'rb') as f:
        tags, version = _read_abi_tags(f)
    
    # Determine channel order from FWO_1 tag
    channel_order = ['A', 'C', 'G', 'T']  # default
    if 'FWO_1' in tags:
        fwo = tags['FWO_1'][0]['data'][:4]
        if len(fwo) >= 4:
            channel_order = [chr(b) for b in fwo if 32 <= b < 127]
    
    # Read trace data (DATA1002-1005 or DATA9-12)
    traces = np.zeros((0, 4), dtype=np.float64)
    for tag_num in [1002, 1003, 1004, 1005]:
        if 'DATA' in tags:
            for entry in tags['DATA']:
                if entry['num'] == tag_num - 1001 or entry['par'] == tag_num:
                    arr = _decode_abi_data(entry, entry['dtype'])
                    col = _ABI_DATA_TAGS.get(tag_num, tag_num - 1002)
                    if traces.shape[0] == 0:
                        traces = np.zeros((len(arr), 4), dtype=np.float64)
                    traces[:, min(col, 3)] = arr[:traces.shape[0]].astype(np.float64)
    
    # Fallback: try direct tag numbers
    if traces.shape[0] == 0:
        for tag_name in ['DATA9', 'DATA10', 'DATA11', 'DATA12']:
            tag_num = int(tag_name[4:]) - 9
            if tag_name in tags:
                entry = tags[tag_name][0]
                arr = _decode_abi_data(entry, entry['dtype'])
                if traces.shape[0] == 0:
                    traces = np.zeros((len(arr), 4), dtype=np.float64)
                traces[:, min(tag_num, 3)] = arr[:traces.shape[0]].astype(np.float64)
    
    if traces.shape[0] == 0:
        raise ValueError('No trace data found in ABI file')
    
    # Read base calls
    sequence = ''
    if 'PBAS' in tags:
        for entry in tags['PBAS']:
            raw = entry['data']
            bases = ''.join(chr(b) for b in raw if 32 <= b < 127 and chr(b) in 'ACGTNacgtn')
            if len(bases) > len(sequence):
                sequence = bases
    sequence = sequence.upper()
    
    # Read peak positions
    positions = np.array([], dtype=np.int64)
    if 'PLOC' in tags:
        for entry in tags['PLOC']:
            arr = _decode_abi_data(entry, entry['dtype'])
            positions = np.union1d(positions, arr.astype(np.int64))
    
    # Read quality scores
    qualities = np.zeros(len(sequence), dtype=np.int8)
    if 'PCON' in tags:
        for entry in tags['PCON']:
            arr = _decode_abi_data(entry, entry['dtype'])
            q = np.clip(arr[:len(sequence)], 0, 93).astype(np.int8)
            qualities[:len(q)] = q
    
    # Sample name
    sample_name = os.path.basename(path)
    if 'SMPL' in tags:
        raw = tags['SMPL'][0]['data']
        sample_name = ''.join(chr(b) for b in raw if 32 <= b < 127).strip('\x00')
    
    # Dye names
    dye_names = []
    if 'DyeN' in tags:
        for entry in tags['DyeN']:
            raw = entry['data']
            name = ''.join(chr(b) for b in raw if 32 <= b < 127).strip('\x00')
            if name:
                dye_names.append(name)
    
    n_scans = traces.shape[0]
    
    return {
        'format': 'abi',
        'traces': traces,
        'sequence': sequence,
        'positions': positions,
        'qualities': qualities,
        'sample_name': sample_name,
        'dye_names': dye_names,
        'n_scans': n_scans,
        'channel_order': channel_order,
    }


# ── SCF format ────────────────────────────────────────────────────────

def read_scf(path):
    """Read an SCF file and return a dict with the same keys as read_abi.
    
    SCF format: header + trace data (float32) + base data.
    """
    with open(path, 'rb') as f:
        magic = f.read(4)
        if magic not in (b'.SCF', b'scf1', b'Univ'):
            raise ValueError(f'Not an SCF file (magic: {magic!r})')
        
        # SCF header
        n_samples, n_bases, comments_offset = struct.unpack('>III', f.read(12))
        peaks_offset, bases_offset, comments_length = struct.unpack('>III', f.read(12))
        version, sample_rate, primer_size, num_spares = struct.unpack('>IIII', f.read(16))
        
        # Read trace data
        f.seek(peaks_offset)
        traces = np.zeros((n_samples, 4), dtype=np.float64)
        for ch in range(4):
            data = struct.unpack(f'>{n_samples}f', f.read(n_samples * 4))
            traces[:, ch] = data
        
        # Read base data
        f.seek(bases_offset)
        bases = []
        positions = []
        qualities = []
        for _ in range(n_bases):
            pos, peak_area, call, qual = struct.unpack('>IIhh', f.read(12))
            bases.append(chr(call & 0xFF) if 32 <= (call & 0xFF) < 127 else 'N')
            positions.append(pos)
            qualities.append(qual)
        
        sequence = ''.join(b for b in bases if b in 'ACGTNacgtn').upper()
        positions = np.array(positions, dtype=np.int64)
        qualities = np.array(qualities[:len(sequence)], dtype=np.int8)
    
    return {
        'format': 'scf',
        'traces': traces,
        'sequence': sequence,
        'positions': positions,
        'qualities': qualities,
        'sample_name': os.path.basename(path),
        'dye_names': [],
        'n_scans': n_samples,
        'channel_order': ['A', 'C', 'G', 'T'],
    }


def read_chromatogram(path):
    """Unified reader: detect format from extension and return standardized dict."""
    ext = os.path.splitext(path)[1].lower()
    if ext in ('.ab1', '.abi'):
        return read_abi(path)
    elif ext in ('.scf',):
        return read_scf(path)
    else:
        raise ValueError(f'Unknown chromatogram format: {ext}')


def abi_to_rsd_traces(chrom_data):
    """Convert chromatogram data to the (N, 4) float64 trace format used by
    the existing DSP pipeline (same layout as parse_rsd output).
    
    Returns (traces, x_axis, channel_order) where traces is (N, 4) float64.
    """
    traces = chrom_data['traces'].astype(np.float64)
    # Ensure non-negative (ABI traces can be unsigned or signed)
    traces = np.clip(traces, 0, None)
    x = np.arange(len(traces))
    return traces, x, chrom_data['channel_order']
