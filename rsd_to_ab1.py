#!/usr/bin/env python3
"""Convert RSD file (via TraceTuner separation) to AB1 formatted file.

Usage: python rsd_to_ab1.py A01 --base-dir /path/to/MB1000_M13_DT
"""

import sys, os, struct, argparse
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from extract_training_data import parse_rsd
from tracetuner_separation import trace_tuner_separate

CHEM_MAP = {0: 'T', 1: 'G', 2: 'C', 3: 'A'}

ABI_DIR_ENTRY_SIZE = 28


def int16(val):
    return struct.pack('>h', int(val))

def int32(val):
    return struct.pack('>i', int(val))

def pascal_str(s):
    encoded = s.encode('ascii', errors='replace')
    return bytes([len(encoded)]) + encoded


class DirEntry:
    def __init__(self, tag_name, tag_num, elem_type, elem_size, num_elem, data):
        self.tag_name = tag_name
        self.tag_num = tag_num
        self.elem_type = elem_type
        self.elem_size = elem_size
        self.num_elem = num_elem
        self.data = data

    @property
    def data_size(self):
        return len(self.data)

    @property
    def is_inline(self):
        return self.data_size <= 4

    def to_bytes(self, data_offset):
        tag = self.tag_name.encode('ascii')
        assert len(tag) == 4
        buf = tag
        buf += int32(self.tag_num)
        buf += int16(self.elem_type)
        buf += int16(self.elem_size)
        buf += int32(self.num_elem)
        buf += int32(self.data_size)
        if self.is_inline:
            buf += self.data.ljust(4, b'\x00')
        else:
            buf += int32(data_offset)
        buf += int32(0)
        return buf


def write_ab1(filename, trace_a, trace_c, trace_g, trace_t,
              base_order="GATC", sample_name="Sample", lane=1,
              basecalls="", peak_locations=None, quality_values=None):
    assert len(trace_a) == len(trace_c) == len(trace_g) == len(trace_t)

    FWO_MAP = {'G': trace_g, 'A': trace_a, 'T': trace_t, 'C': trace_c}
    data9 = FWO_MAP[base_order[0]]
    data10 = FWO_MAP[base_order[1]]
    data11 = FWO_MAP[base_order[2]]
    data12 = FWO_MAP[base_order[3]]

    n_scans = len(trace_a)

    dirs = [
        DirEntry("DATA", 9,  4, 2, n_scans,
                 struct.pack(f'>{n_scans}h', *data9.astype(np.int32).clip(-32768, 32767))),
        DirEntry("DATA", 10, 4, 2, n_scans,
                 struct.pack(f'>{n_scans}h', *data10.astype(np.int32).clip(-32768, 32767))),
        DirEntry("DATA", 11, 4, 2, n_scans,
                 struct.pack(f'>{n_scans}h', *data11.astype(np.int32).clip(-32768, 32767))),
        DirEntry("DATA", 12, 4, 2, n_scans,
                 struct.pack(f'>{n_scans}h', *data12.astype(np.int32).clip(-32768, 32767))),
        DirEntry("FWO_", 1,  2, 1, 4, base_order.encode('ascii')),
        DirEntry("LANE", 1,  4, 2, 1, int16(lane)),
        DirEntry("SMPL", 1, 18, 1, len(sample_name) + 1, pascal_str(sample_name)),
    ]

    if basecalls:
        bc = basecalls.encode('ascii')
        dirs.append(DirEntry("PBAS", 2, 2, 1, len(bc), bc))
        if quality_values is not None:
            qv = bytes(int(v) for v in quality_values)
            dirs.append(DirEntry("PCON", 2, 1, 1, len(qv), qv))
        if peak_locations is not None:
            pl = struct.pack(f'>{len(peak_locations)}h', *(int(p) for p in peak_locations))
            dirs.append(DirEntry("PLOC", 2, 4, 2, len(peak_locations), pl))

    data_dirs = [d for d in dirs if not d.is_inline]
    total_data_size = sum(d.data_size for d in data_dirs)
    dir_offset = 128 + total_data_size

    with open(filename, 'wb') as f:
        f.write(b'ABIF')
        f.write(int16(101))

        num_dirs = len(dirs)
        f.write(b'tdir')
        f.write(int32(1))
        f.write(int16(1023))
        f.write(int16(28))
        f.write(int32(num_dirs))
        f.write(int32(num_dirs * 28))
        f.write(int32(dir_offset))
        f.write(int32(0))
        f.write(b'\x00' * 94)

        offset = 128
        for d in dirs:
            if not d.is_inline:
                f.write(d.data)
                offset += d.data_size

        offset = 128
        for d in dirs:
            f.write(d.to_bytes(offset))
            if not d.is_inline:
                offset += d.data_size


def rsd_to_ab1(rsd_path, ab1_path, basecalls_path=None, remap_chemistry=True):
    df = parse_rsd(rsd_path)
    ch = df[['Channel1', 'Channel2', 'Channel3', 'Channel4']].values.T.astype(np.float64)
    separated = trace_tuner_separate(ch)

    if remap_chemistry:
        trace_t = separated[0]
        trace_g = separated[1]
        trace_c = separated[2]
        trace_a = separated[3]
    else:
        trace_a = separated[0]
        trace_c = separated[1]
        trace_g = separated[2]
        trace_t = separated[3]

    bc = ""
    peak_locs = None
    qual = None
    if basecalls_path and os.path.exists(basecalls_path):
        from extract_training_data import parse_esd
        esd = parse_esd(basecalls_path)
        seq = esd.get('sequence', '')
        positions = esd.get('peak_positions')
        if positions is None:
            positions = esd.get('bases_positions')
        quality = esd.get('quality_scores')
        if seq and positions is not None:
            n = min(len(seq), len(positions))
            bc = seq[:n]
            peak_locs = positions[:n]
            if quality is not None:
                qual = quality[:n]

    well_name = os.path.splitext(os.path.basename(rsd_path))[0]
    write_ab1(ab1_path, trace_a, trace_c, trace_g, trace_t,
              base_order="GATC", sample_name=well_name,
              basecalls=bc, peak_locations=peak_locs, quality_values=qual)
    return ab1_path


def main():
    parser = argparse.ArgumentParser(description="Convert RSD (through TraceTuner) to AB1")
    parser.add_argument('well', help="Well name (e.g. A01)")
    parser.add_argument('--base-dir', default='/media/per/Disk 2/electropherogram/MB1000_M13_DT',
                        help='Base directory with .rsd files')
    parser.add_argument('--esd-dir', default='MB1000_M13_DT_Cp312_MD1',
                        help='ESD folder name for basecalls (optional)')
    parser.add_argument('--no-basecalls', action='store_true',
                        help='Skip embedding ESD basecalls in AB1')
    parser.add_argument('--no-remap', action='store_true',
                        help='Skip chemistry remapping')
    parser.add_argument('--output', default=None,
                        help='Output AB1 path (default: well.ab1 in current dir)')
    args = parser.parse_args()

    rsd_path = os.path.join(args.base_dir, f"{args.well}.rsd")
    if not os.path.exists(rsd_path):
        print(f"Error: {rsd_path} not found")
        sys.exit(1)

    bc_path = os.path.join(args.base_dir, args.esd_dir, f"{args.well}.esd") if not args.no_basecalls else None

    out = args.output or f"{args.well}.ab1"
    rsd_to_ab1(rsd_path, out, basecalls_path=bc_path, remap_chemistry=not args.no_remap)
    print(f"Wrote {out}")


if __name__ == '__main__':
    main()
