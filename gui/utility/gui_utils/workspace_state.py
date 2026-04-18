from __future__ import annotations

from typing import List, Optional

from ...widgets.window import Window as Window


class WorkspaceState:
    """Mutable workspace state shared by object registry and workspace coordinator."""

    def __init__(self) -> None:
        """Create WorkspaceState."""
        self.task_panel_capture: bool = False
        self.active_object: Optional[Window] = None

    def resolve_active_object(self, windows: List[Window]) -> Optional[Window]:
        """Resolve active object."""
        if self.active_object is None:
            return None
        if self.active_object not in windows:
            self.active_object = None
            return None
        return self.active_object
