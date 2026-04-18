from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .gui_manager import GuiManager


class RenderCoordinator:
    """Owns top-level draw and undraw orchestration wrappers."""

    def __init__(self, gui_manager: "GuiManager") -> None:
        """Initialize the RenderCoordinator instance."""
        self.gui: "GuiManager" = gui_manager

    def draw_gui(self) -> None:
        """Run draw gui and return the resulting value.

        This method encapsulates the main behavior for this operation."""
        self.gui.renderer.draw()

    def undraw_gui(self) -> None:
        """Run undraw gui and return the resulting value.

        This method encapsulates the main behavior for this operation."""
        self.gui.renderer.undraw()
