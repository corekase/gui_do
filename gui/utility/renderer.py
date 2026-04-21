from __future__ import annotations

from pygame import Rect
from pygame.surface import Surface
from typing import List, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from .gui_manager import GuiManager

class Renderer:
    """Draws widgets/windows and restores previous pixels when buffered."""

    def __init__(self, gui: "GuiManager") -> None:
        """Bind the renderer to a gui manager."""
        self.gui: "GuiManager" = gui
        self._bitmaps: List[Tuple[Surface, Rect]] = []

    def _capture_bitmap(self, rect: Rect) -> None:
        """Capture bitmap."""
        if not self.gui.buffered:
            return
        if rect.width <= 0 or rect.height <= 0:
            return
        self._bitmaps.append((self.gui.copy_graphic_area(self.gui.surface, rect), rect))

    @staticmethod
    def _iter_visible_widgets(widgets):
        """Iter visible widgets."""
        for widget in tuple(widgets):
            if widget.visible:
                yield widget

    def _draw_widget_collection(self, widgets) -> None:
        """Draw widget collection."""
        for widget in self._iter_visible_widgets(widgets):
            widget.draw()

    def _resolve_cursor_pos(self) -> Tuple[int, int]:
        """Resolve cursor pos."""
        if self.gui.mouse_point_locked and self.gui.lock_point_pos is not None:
            return self.gui.lock_point_pos
        return self.gui.mouse_pos

    def _draw_root_widgets(self) -> None:
        """Draw root widgets."""
        for widget in self._iter_visible_widgets(self.gui.widgets):
            self._capture_bitmap(Rect(widget.draw_rect))
            widget.draw()

    def _draw_windows(self) -> None:
        """Draw windows."""
        windows_snapshot = tuple(self.gui.windows)
        active_window = self.gui.active_window
        highlighted_window = active_window if active_window in windows_snapshot and active_window.visible else None
        for window in windows_snapshot:
            if window.visible:
                self._capture_bitmap(window.get_window_rect())
                if window is highlighted_window:
                    window.draw_title_bar_active()
                else:
                    window.draw_title_bar_inactive()
                window.draw_window()
                self._draw_widget_collection(window.widgets)
                self.gui.surface.blit(window.surface, (window.x, window.y))

    def _draw_task_panel(self) -> None:
        """Draw task panel."""
        task_panel = self.gui.task_panel
        if task_panel is None or not task_panel.visible:
            return
        panel_rect = task_panel.get_rect()
        self._capture_bitmap(panel_rect)
        task_panel.draw_background()
        self._draw_widget_collection(task_panel.widgets)
        self.gui.surface.blit(task_panel.surface, (task_panel.left, task_panel.y))

    def _draw_cursor(self) -> None:
        """Draw cursor."""
        if self.gui.mouse_locked:
            clamped_pos = self.gui.lock_area(self.gui.mouse_pos)
            self.gui._set_mouse_pos(clamped_pos, False)
        if self.gui.cursor_image is None or self.gui.cursor_hotspot is None:
            return
        cursor_pos = self._resolve_cursor_pos()
        cursor_rect = self.gui.pointer._finalize_cursor_rect(cursor_pos)
        self._capture_bitmap(cursor_rect)
        self.gui.surface.blit(self.gui.cursor_image, cursor_rect)

    def draw(self) -> None:
        """Render one frame. Cursor is drawn last."""
        if self.gui.buffered:
            self._bitmaps.clear()
        self._draw_root_widgets()
        self._draw_windows()
        self._draw_task_panel()
        self._draw_cursor()

    def undraw(self) -> None:
        """Restore the pixels captured by draw when buffering is enabled."""
        for bitmap, rect in reversed(self._bitmaps):
            self.gui.surface.blit(bitmap, rect)
        self._bitmaps.clear()
