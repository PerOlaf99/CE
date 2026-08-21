#!/usr/bin/env python3
"""run_polish.py - reference-guided polished calling (100.00% on MB1000_M13_DT).

Thin wrapper around 02_denovo_cnn_ensemble_91.53pct/perfect_basecaller.py
in its DEFAULT mode (polishing is on unless --no-ref). Requires the M13
reference - for reference-free calling use the de-novo folder instead.

Usage: same flags as perfect_basecaller.py, e.g.
  python3 run_polish.py --rsd ../MB1000_M13_DT/A01.rsd --fastq A01.fq
  python3 run_polish.py --eval --wells A01 B02 C03 D04
"""
import os, sys

__version__ = '1.0'
HERE = os.path.dirname(os.path.realpath(__file__))
TARGET = os.path.join(os.path.dirname(HERE),
                      '02_denovo_cnn_ensemble_91.53pct',
                      'perfect_basecaller.py')

if len(sys.argv) < 2:
    print(__doc__)
    sys.exit(1)
os.execv(sys.executable, [sys.executable, TARGET] + sys.argv[1:])
