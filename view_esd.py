#!/usr/bin/env python3
"""View an .esd basecall as aligned text columns: one row per called base
with its scan position, quality, FWHM, spacing, and the 4 raw channel
intensities at that scan (from the matching .rsd, when found).

Usage:
    python3 view_esd.py A01.esd
    python3 view_esd.py A01.esd --rsd ../A01.rsd
    python3 view_esd.py A01.esd --rows 20        # limit rows printed
"""
import argparse
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from extract_training_data import parse_esd, parse_rsd


def load_rsd(esd_path, rsd_arg):
    if rsd_arg:
        return parse_rsd(rsd_arg)
    sibling = os.path.splitext(esd_path)[0] + '.rsd'
    if os.path.exists(sibling):
        return parse_rsd(sibling)
    in_base = os.path.join(BASE_DIR, os.path.splitext(os.path.basename(esd_path))[0] + '.rsd')
    if os.path.exists(in_base):
        return parse_rsd(in_base)
    return None


def print_metadata(d):
    print('== ESD metadata ==')
    for k in ('sample_name', 'well_id', 'chemistry', 'dye_set',
              'plate_id', 'instrument', 'bar_code'):
        v = d.get(k)
        if v:
            print(f'  {k:12s}: {v.rstrip(chr(0))}')
    print()


def print_trace_summary(rsd):
    if rsd is None:
        return
    print('== Trace summary ==')
    print(f'  scans        : {len(rsd)}')
    for i in range(1, 5):
        col = f'Channel{i}'
        v = rsd[col].values
        print(f'  {col:12s}: min={v.min():.0f} max={v.max():.0f} mean={v.mean():.0f}')
    print()


def print_base_table(d, rsd, rows):
    positions = d.get('peak_positions')
    if positions is None:
        positions = d.get('bases_positions')
    seq = d.get('sequence', '')
    quals = d.get('quality_scores')
    fwhm = d.get('fwhm_values')

    n = len(positions)
    header = (f"{'#':>4} {'Scan':>6} {'Base':>4} {'Qual':>5} {'FWHM':>6} "
              f"{'Spac':>4}")
    chan_hdrs = ''.join(f' {c:>7}' for c in ('Ch1', 'Ch2', 'Ch3', 'Ch4'))
    header += chan_hdrs + '   RawDom'
    print(header)
    print('-' * len(header))

    prev_scan = None
    for i in range(n):
        scan = int(positions[i])
        base = seq[i] if i < len(seq) else '?'
        q = f'{quals[i]:.1f}' if quals is not None and i < len(quals) else ''
        fw = f'{fwhm[i]:.1f}' if fwhm is not None and i < len(fwhm) else ''
        sp = f'{scan - prev_scan}' if prev_scan is not None else ''
        prev_scan = scan
        line = f'{i:>4} {scan:>6} {base:>4} {q:>5} {fw:>6} {sp:>4}'
        dom = ''
        if rsd is not None and 0 <= scan < len(rsd):
            sig = [rsd.loc[scan, f'Channel{k}'] for k in (1, 2, 3, 4)]
            line += ''.join(f' {v:>7.0f}' for v in sig)
            dom = 'Ch%d' % (int(np.argmax(sig)) + 1)
        line += f'   {dom}'
        print(line)
        if rows and i + 1 >= rows:
            print('...')
            break

    print()
    print(f'{n} bases; {len(seq)} letters in ESD sequence; '
          f'{"no " if positions is None else ""}peak positions found.')
    print('Note: RawDom is the argmax of the RAW channel signals at that scan; '
          'it often differs from the Base because of dye-bleed '
          '(matrix separation is applied before calling).')


BASE_DIR = "/media/tv/78B0C7DE1FA7081C/electropherogram/MB1000_M13_DT"


def resolve_esd_path(esd_arg, well):
    """Resolve a positional arg into an .esd path. Accepts a full path, a
    plain well name (A01), or nothing (defaults to well A01 in the first
    *_MD1 variant dir found under BASE_DIR)."""
    if esd_arg and os.path.exists(esd_arg):
        return esd_arg
    if esd_arg and os.path.exists(os.path.join(BASE_DIR, esd_arg)):
        return os.path.join(BASE_DIR, esd_arg)
    subdirs = sorted(d for d in os.listdir(BASE_DIR)
                     if os.path.isdir(os.path.join(BASE_DIR, d)) and d.endswith('_MD1'))
    if not subdirs:
        return esd_arg or ''
    variant = next((d for d in subdirs if 'Cp312' in d), subdirs[0])
    candidate = os.path.join(BASE_DIR, variant, f'{well}.esd')
    if os.path.exists(candidate):
        return candidate
    return esd_arg or ''


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('esd', nargs='?', default=None,
                    help='path to the .esd file, or a well name like A01')
    ap.add_argument('--well', default='A01',
                    help='well name to use when resolving a short path')
    ap.add_argument('--rsd', default=None, help='path to the .rsd trace file')
    ap.add_argument('--rows', type=int, default=0,
                    help='limit printed base rows (0 = all)')
    args = ap.parse_args()

    esd_path = resolve_esd_path(args.esd, args.well)
    if not esd_path or not os.path.exists(esd_path):
        print(f'No .esd file found (tried: {esd_path or "<none>"}). '
              f'Pass a path or a well name, e.g. view_esd.py A03')
        sys.exit(1)

    d = parse_esd(esd_path)
    rsd = load_rsd(esd_path, args.rsd)
    print_metadata(d)
    print_trace_summary(rsd)
    print_base_table(d, rsd, args.rows)


if __name__ == '__main__':
    main()
