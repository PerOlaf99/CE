#!/usr/bin/env bash
# Hourly health check for ml_plate_run.py (run via cron).
# Appends one status line per invocation to ml_plate_results/monitor.log.
set -u
ROOT="/media/per/78B0C7DE1FA7081C/electropherogram"
OUT="$ROOT/ml_plate_results"
LOG="$OUT/progress.log"
MON="$OUT/monitor.log"
PID=$(pgrep -f 'ml_plate_run\.py' | head -1)
ts=$(date '+%Y-%m-%d %H:%M:%S')
if [ -n "$PID" ]; then alive="ALIVE pid=$PID"; else alive="DEAD"; fi
done=$(grep -c 'done=' "$LOG" 2>/dev/null || echo 0)
last=$(tail -1 "$LOG" 2>/dev/null)
printf '%s  %s  wells_done=%s  last=%s\n' "$ts" "$alive" "$done" "$last" >> "$MON"