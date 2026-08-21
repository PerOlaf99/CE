#!/usr/bin/env python3
"""call_cimarron.py - run the Cimarron 3.12 DLL basecaller on an RSD file.

This is the commercial baseline (90.72% per-base vs M13 on MB1000_M13_DT).
The DLL cluster (base_callers/, wineprefix/, winedll/) stays at the
electropherogram root - wineprefix embeds absolute paths and must not move.

Usage:
  python3 call_cimarron.py PATH.rsd [more.rsd ...]
Prints FASTA-ish records with the called sequence.
"""
import os, sys

__version__ = '1.0'
HERE = os.path.dirname(os.path.realpath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
os.environ.setdefault('TF_CPP_MIN_LOG_LEVEL', '3')

import cimarrontv as cim


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    for path in sys.argv[1:]:
        ch, scans = cim.read_rsd(path)
        res = cim.call_basecaller(ch, scans)
        name = os.path.splitext(os.path.basename(path))[0]
        print(f'>{name} cimarron312')
        for i in range(0, len(res.sequence), 60):
            print(res.sequence[i:i + 60])


if __name__ == '__main__':
    main()
