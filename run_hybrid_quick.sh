#!/bin/bash
# Quick sanity check - 3 wells only (~3 min)
cd "$(dirname "$0")"
python3 perfect_basecaller.py --eval --hybrid 0.70 --wells A01 B06 H12 2>&1
