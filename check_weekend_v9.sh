#!/usr/bin/env bash
# Weekend v9 health check (run via cron).  Appends one status line to
# 02_denovo_cnn_ensemble_91.53pct/weekend_v9_monitor.log.
set -u
HERE="/media/per/78B0C7DE1FA7081C/electropherogram/02_denovo_cnn_ensemble_91.53pct"
LOG="$HERE/weekend_v9.log"
MON="$HERE/weekend_v9_monitor.log"
PID=$(pgrep -f 'weekend_v9\.sh|train_v9_weekend|train_corr|eval_v9_weekend|build_corr_v9' | head -1)
ts=$(date '+%Y-%m-%d %H:%M:%S')
if [ -n "${PID:-}" ]; then alive="ALIVE pid=$PID"; else alive="DEAD"; fi
best=$(grep -h 'BEST val_acc' "$LOG" 2>/dev/null | tail -3 | tr '\n' ' ')
last=$(tail -1 "$LOG" 2>/dev/null)
printf '%s  %s  %s last=%s\n' "$ts" "$alive" "$best" "$last" >> "$MON"