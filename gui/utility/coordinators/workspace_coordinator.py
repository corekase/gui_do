from __future__ import annotations

from typing import TYPE_CHECKING

from ...widgets.window import Window

if TYPE_CHECKING:
    from ..gui_manager import GuiManager


class WorkspaceCoordinator:
    """Owns workspace-level container orchestration and stacking rules."""

    def __init__(self, gui_manager: "GuiManager") -> None:
        """Bind workspace orchestration to a GUI manager."""
        self.gui: "GuiManager" = gui_manager

    def lower_window(self, window: Window) -> None:
        """Move a registered window to the bottom of z-order."""
        resolved_window = self.gui.object_registry.resolve_registered_window(window)
        if resolved_window is None:
            return
        self.gui.windows.remove(resolved_window)
        self.gui.windows.insert(0, resolved_window)

    def raise_window(self, window: Window) -> None:
        """Move a registered window to the top of z-order."""
        resolved_window = self.gui.object_registry.resolve_registered_window(window)
        if resolved_window is None:
            return
        self.gui.windows.remove(resolved_window)
        self.gui.windows.append(resolved_window)
