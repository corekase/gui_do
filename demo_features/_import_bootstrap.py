"""Import-path bootstrap for running demo feature modules from subdirectories."""

from __future__ import annotations

import sys
from pathlib import Path


def ensure_repo_root_on_path() -> None:
    """Ensure the repository root is importable for gui_do/demo_features packages."""
    repo_root = Path(__file__).resolve().parent.parent
    repo_root_str = str(repo_root)
    if repo_root_str not in sys.path:
        sys.path.insert(0, repo_root_str)
