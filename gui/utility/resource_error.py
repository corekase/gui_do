from __future__ import annotations

import os
from .events import GuiError


class DataResourceErrorHandler:
    """Normalize and surface data-path load failures as framework-native errors.

    The helper centralizes path presentation so resource failures consistently
    report a display path rooted at `data/` when possible, regardless of the
    process working directory.
    """

    @staticmethod
    def data_display_path(path: str) -> str:
        """Return a normalized path, preferring a `data/...`-relative display form."""
        # Normalize once so marker checks behave consistently across separators.
        full_path = os.path.normpath(os.path.abspath(path))
        data_marker = f'{os.sep}data{os.sep}'
        lowered_path = full_path.lower()
        lowered_marker = data_marker.lower()
        marker_index = lowered_path.find(lowered_marker)
        # Prefer a concise data-rooted path when the marker appears in the path.
        if marker_index >= 0:
            return full_path[marker_index:]
        data_suffix = f'{os.sep}data'
        # Handle the edge case where the path itself ends at the data directory.
        if lowered_path.endswith(data_suffix.lower()):
            return full_path[len(full_path) - len(data_suffix):]
        # Fall back to the normalized absolute path when no data marker exists.
        return full_path

    @staticmethod
    def raise_load_error(action: str, path: str, exc: Exception) -> None:
        """Raise a `GuiError` with a normalized resource path and original cause."""
        # Wrap low-level load failures in a project-level exception contract.
        raise GuiError(f'{action}: {DataResourceErrorHandler.data_display_path(path)}') from exc
