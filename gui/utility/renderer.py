from pygame import Rect
from pygame.surface import Surface
from typing import List, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from .guimanager import GuiManager

class Renderer:
    """Draws widgets/windows and restores previous pixels when buffered."""

    def __init__(self, gui: "GuiManager") -> None:
        """Bind the renderer to a gui manager."""
        self.gui: "GuiManager" = gui
        self._bitmaps: List[Tuple[Surface, Rect]] = []

    def draw(self) -> None:
        """Render one frame. Cursor is drawn last."""
        if self.gui.buffered:
            self._bitmaps.clear()
        for widget in self.gui.widgets:
            if widget.visible:
                if self.gui.buffered:
                    self._bitmaps.append((self.gui.copy_graphic_area(self.gui.surface, widget.get_rect()), widget.get_rect()))
                widget.draw()
        for window in self.gui.windows:
            if window.visible:
                if self.gui.buffered:
                    self._bitmaps.append((self.gui.copy_graphic_area(self.gui.surface, window.get_window_rect()), window.get_window_rect()))
                if window is self.gui.windows[-1]:
                    window.draw_title_bar_active()
                else:
                    window.draw_title_bar_inactive()
                window.draw_window()
                for widget in window.widgets:
                    if widget.visible:
                        widget.draw()
                self.gui.surface.blit(window.surface, (window.x, window.y))
        if self.gui.mouse_locked:
            self.gui.mouse_pos = self.gui.lock_area(self.gui.mouse_pos)
        if self.gui.cursor_image and self.gui.cursor_hotspot:
            if self.gui.mouse_point_locked and self.gui.lock_point_pos is not None:
                cursor_pos = self.gui.lock_point_pos
            else:
                cursor_pos = self.gui.mouse_pos
            cursor_rect = Rect(cursor_pos[0] - self.gui.cursor_hotspot[0], cursor_pos[1] - self.gui.cursor_hotspot[1],
                            self.gui.cursor_rect.width, self.gui.cursor_rect.height)
            self.gui.cursor_rect = cursor_rect
            if self.gui.buffered:
                self._bitmaps.append((self.gui.copy_graphic_area(self.gui.surface, cursor_rect), cursor_rect))
            self.gui.surface.blit(self.gui.cursor_image, cursor_rect)

    def undraw(self) -> None:
        """Restore the pixels captured by draw when buffering is enabled."""
        for bitmap, rect in reversed(self._bitmaps):
            self.gui.surface.blit(bitmap, rect)
        self._bitmaps.clear()
