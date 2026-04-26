#!/usr/bin/env sh
set -eu

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
python "$SCRIPT_DIR/bootstrap_new_project.py" upgrade --verify
echo "upgrade_existing_project completed."
