from pygame import Rect
from pygame.surface import Surface
from typing import List, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from .guimanager import GuiManager

class Renderer:
    """Renders GUI widgets and manages display buffering.

    The Renderer handles all drawing of widgets, windows, and the cursor to the
    screen surface. When buffering is enabled, it saves the screen contents before
    drawing each object, allowing for efficient restoration via undraw().

    Attributes:
        gui: Reference to the GuiManager.
        bitmaps: List of (bitmap, rect) tuples saved for buffering. Used when
                 gui.buffered is True to efficiently restore screen contents.
    """
    def __init__(self, gui: "GuiManager") -> None:
        """Initialize the renderer.

        Args:
            gui: Reference to GuiManager for access to widgets and render state.
        """
        self.gui: "GuiManager" = gui
        self._bitmaps: List[Tuple[Surface, Rect]] = []

    def draw(self) -> None:
        """Render all GUI elements to the screen surface.

        Drawing order (front to back):
        1. Screen widgets (back)
        2. Windows (in z-order)
        3. Window widgets
        4. Mouse cursor (front)

        When buffering is enabled (gui.buffered=True), saves screen contents
        under each drawable element for later restoration via undraw().
        This allows for efficient animation and dynamic UI updates.
        """
        if self.gui.buffered:
            self._bitmaps.clear()
        for widget in self.gui.widgets:
            if widget.visible:
                # save the bitmap area under the widgets if buffered
                if self.gui.buffered:
                    self._bitmaps.insert(0, (self.gui.copy_graphic_area(self.gui.surface, widget.get_rect()), widget.get_rect()))
                # draw the widget
                widget.draw()
        for window in self.gui.windows:
            if window.visible:
                # save the bitmap area under the window if buffered
                if self.gui.buffered:
                    self._bitmaps.insert(0, (self.gui.copy_graphic_area(self.gui.surface, window.get_window_rect()), window.get_window_rect()))
                if window is self.gui.windows[-1]:
                    window.draw_title_bar_active()
                else:
                    window.draw_title_bar_inactive()
                window.draw_window()
                for widget in window.widgets:
                    # draw the widget
                    if widget.visible:
                        widget.draw()
                self.gui.surface.blit(window.surface, (window.x, window.y))
        # if locked mode is active always use the locked mode mouse position
        if self.gui.mouse_locked:
            self.gui.mouse_pos = self.gui.lock_area(self.gui.mouse_pos)
        # draw mouse cursor
        if self.gui.cursor_image and self.gui.cursor_hotspot:
            cursor_rect = Rect(self.gui.mouse_pos[0] - self.gui.cursor_hotspot[0], self.gui.mouse_pos[1] - self.gui.cursor_hotspot[1],
                            self.gui.cursor_rect.width, self.gui.cursor_rect.height)
            # save the bitmap area under the window if buffered
            if self.gui.buffered:
                self._bitmaps.insert(0, (self.gui.copy_graphic_area(self.gui.surface, cursor_rect), cursor_rect))
            self.gui.surface.blit(self.gui.cursor_image, cursor_rect)

    def undraw(self) -> None:
        """Restore screen contents to undo the previous draw() operation.

        This is only used when buffering is enabled (gui.buffered=True).
        Restores saved bitmap contents from draw() in reverse order,
        effectively clearing all drawn GUI elements from the screen.

        Must be called after pygame.display.flip() if using buffering.
        """
        # reverse the bitmaps that were under each gui object drawn, if buffered is false then
        # the client does not call this method at all
        for bitmap, rect in self._bitmaps:
            self.gui.surface.blit(bitmap, rect)
        self._bitmaps.clear()
