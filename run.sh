#!/bin/bash
DIR="$(cd "$(dirname "$0")" && pwd)"
exec "$DIR/env/bin/python3" "$DIR/gui.py" "$@"
