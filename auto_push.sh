#!/bin/bash
# Auto-push watcher: commits and pushes changes to GitHub on file save
# Run: ./auto_push.sh &
DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR" || exit 1

WATCH_PATTERNS="--include '.*\.py$' --include '.*\.json$' --include '.*\.sh$' --include '.*\.md$' --include '.*\.txt$'"
COOLDOWN=10  # seconds to wait after last change before committing

echo "Watching $DIR for changes (cooldown=${COOLDOWN}s)..."
last_commit=0
while true; do
    inotifywait -q -r -e modify,create,delete,move \
        --exclude '(env/|__pycache__|\.git/|OY/|MB[0-9].*|base_callers/|training_data/|\.pyc)' \
        "$DIR" 2>/dev/null
    now=$(date +%s)
    if (( now - last_commit < COOLDOWN )); then
        continue
    fi
    sleep 2
    if git status --porcelain | grep -q .; then
        git add -A 2>/dev/null
        git commit -m "auto: $(date '+%Y-%m-%d %H:%M:%S')" 2>/dev/null
        git push 2>/dev/null
        last_commit=$(date +%s)
        echo "auto-pushed at $(date)"
    fi
done