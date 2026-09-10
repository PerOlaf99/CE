#!/usr/bin/env bash
# label_campaign.sh - produce consistent per-window matrix labels for ML training.
#   Matrix_apply_point is pinned ('corrected') so labels are comparable across
#   windows AND wells; window grid matches the A01 campaign (700bp/100 overlap).
#
# Usage:
#   bash label_campaign.sh "A02 B01 C01"          # run these wells (background)
#   WELLS="$(seq ...)" bash label_campaign.sh     # or set via env
#
# Each well logs to opt_windows_labels/<W>.log and writes JSONs there.
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
cd "$HERE"
OUTDIR=opt_windows_labels
mkdir -p "$OUTDIR"
WELLS="${WELLS:-$*}"
[ -n "$WELLS" ] || { echo "usage: $0 W1 W2 ..."; exit 1; }
WORKERS=${WORKERS:-2}

for W in $WELLS; do
  mkdir -p "$OUTDIR/$W"
  nohup python3 optimize_windows_esd.py \
      --well "$W" \
      --win-size 700 --overlap 100 --min-win 2050 --max-win 9332 \
      --method greedy --tune-matrix diag \
      --matrix-apply-point corrected \
      --workers "$WORKERS" \
      --outdir "$OUTDIR/$W" \
      > "$OUTDIR/$W.log" 2>&1 &
  echo "started $W -> pid $!  log $OUTDIR/$W.log"
done
echo "jobs running; watch with:  tail -f $OUTDIR/<W>.log"