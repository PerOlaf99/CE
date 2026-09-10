#!/bin/bash
# Hourly status snapshot for the per-window optimizer (run by cron).
# Appends one line to STATUS_LOG. Safe to run any time; writes nothing else.
HERE=/media/per/78B0C7DE1FA7081C/electropherogram/sanger_toolkit
STATUS_LOG=$HERE/optimizer_status.log
cd "$HERE" || exit 1

ts=$(date '+%Y-%m-%d %H:%M:%S')

# stage
stage="?"
[ -f "$HERE/.watch_stage" ] && stage=$(cat "$HERE/.watch_stage")

# counts
c=$(ls -1 "$HERE/opt_windows_esd"/*.json 2>/dev/null | wc -l)
f=$(ls -1 "$HERE/opt_windows_fine"/*.json 2>/dev/null | wc -l)

# processes
opt=$(pgrep -f optimize_windows_esd.py | wc -l)
watch=$(pgrep -f watch_optimizer.py | wc -l)

# last progress line from whichever run is current
last=""
if [ "$stage" = "fine" ] && [ -f "$HERE/opt_fine_run.log" ]; then
  last=$(grep -E "INIT|BEST|saved|window [0-9]+/81" "$HERE/opt_fine_run.log" 2>/dev/null | tail -1)
elif [ -f "$HERE/opt_esd_run.log" ]; then
  last=$(grep -E "INIT|BEST|saved|window [0-9]+/12" "$HERE/opt_esd_run.log" 2>/dev/null | tail -1)
fi

# disk space (home)
disk=$(df -h /media/per | tail -1 | awk '{print $4" free"}')

printf '%s | stage=%s | coarse_json=%d fine_json=%d | opt_proc=%d watch_proc=%d | %s | %s\n' \
  "$ts" "$stage" "$c" "$f" "$opt" "$watch" "$disk" "$last" >> "$STATUS_LOG"
