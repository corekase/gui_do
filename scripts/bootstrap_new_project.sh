#!/usr/bin/env sh
set -eu

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
python "$SCRIPT_DIR/bootstrap_new_project.py" new --scaffold --verify
echo "bootstrap_new_project completed."
