#!/bin/bash
# Run full 96-well hybrid evaluation (CNN+ESD t=0.70)
# Launch: ./run_hybrid_eval.sh
# Monitor: tail -f hybrid_96well_final.log
# Expected runtime: ~90 min on CPU (no GPU)
cd "$(dirname "$0")"
echo "Starting hybrid eval at $(date)" | tee hybrid_96well_final.log
python3 perfect_basecaller.py --eval --hybrid 0.70 >> hybrid_96well_final.log 2>&1
echo "Finished at $(date)" >> hybrid_96well_final.log
