#!/usr/bin/env sh
set -eu

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
python "$SCRIPT_DIR/check_merge_readiness.py" "$@"
echo "check_merge_readiness completed."
