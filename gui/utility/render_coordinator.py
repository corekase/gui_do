from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .gui_manager import GuiManager


class RenderCoordinator:
    """Owns top-level draw and undraw orchestration wrappers."""

    def __init__(self, gui_manager: "GuiManager") -> None:
        self.gui: "GuiManager" = gui_manager

    def draw_gui(self) -> None:
        self.gui.renderer.draw()

    def undraw_gui(self) -> None:
        self.gui.renderer.undraw()
