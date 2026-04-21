from __future__ import annotations

import pygame
from pygame import Rect
from pygame.event import Event as PygameEvent
from pygame.surface import Surface
from typing import Callable, Optional, Tuple, TYPE_CHECKING
from ..events import Event, GuiError
from ..geometry import point_in_rect

if TYPE_CHECKING:
    from ..gui_utils.gui_event import GuiEvent
    from ..gui_manager import GuiManager
    from ...widgets.window import Window

class Widget:
    """Base widget contract used by all concrete widgets."""

    @property
    def disabled(self) -> bool:
        """Return True when this widget should draw dimmed and ignore input."""
        return self._disabled

    @disabled.setter
    def disabled(self, value: bool) -> None:
        """Enable or disable this widget's interaction."""
        if not isinstance(value, bool):
            raise GuiError('widget disabled must be a bool')
        if self._disabled == value:
            return
        self._disabled = value
        self._on_disabled_changed(value)

    @property
    def visible(self) -> bool:
        """Visible."""
        return self._visible

    @visible.setter
    def visible(self, value: bool) -> None:
        """Visible."""
        if not isinstance(value, bool):
            raise GuiError('widget visible must be a bool')
        self._visible = value

    @property
    def position(self) -> Tuple[int, int]:
        """Widget draw position as an (x, y) tuple."""
        return self.draw_rect.x, self.draw_rect.y

    @position.setter
    def position(self, pos: Tuple[int, int]) -> None:
        """Move the widget without changing size."""
        if not isinstance(pos, tuple) or len(pos) != 2:
            raise GuiError(f'widget pos must be a tuple of (x, y), got: {pos}')
        old_x, old_y = self.draw_rect.x, self.draw_rect.y
        hit_offset_x: Optional[int] = None
        hit_offset_y: Optional[int] = None
        if self.hit_rect is not None:
            hit_offset_x = self.hit_rect.x - old_x
            hit_offset_y = self.hit_rect.y - old_y
        self.draw_rect.x, self.draw_rect.y = pos
        if self.hit_rect is not None and hit_offset_x is not None and hit_offset_y is not None:
            self.hit_rect.x = self.draw_rect.x + hit_offset_x
            self.hit_rect.y = self.draw_rect.y + hit_offset_y

    def __init__(self, gui: "GuiManager", id: str, rect: Rect) -> None:
        """Create Widget."""
        self.gui: "GuiManager" = gui
        self.surface: Optional[Surface] = None
        self.window: Optional["Window"] = None
        self.id: str = id
        self.draw_rect: Rect = Rect(rect)
        self.hit_rect: Optional[Rect] = None
        self.pristine: Optional[Surface] = None
        self._visible: bool = True
        self._disabled: bool = False
        self.on_activate: Optional[Callable[[], None]] = None
        self.auto_restore_pristine: bool = False

    def _on_disabled_changed(self, _: bool) -> None:
        """Hook for subclasses to react to disabled-state changes."""
        return

    def on_added_to_gui(self) -> None:
        """Hook invoked after successful registration in a GUI container."""
        return

    def _build_disabled_surface(self, source: Surface) -> Surface:
        """Return a 75% intensity copy of `source`."""
        dimmed = source.copy()
        dimmed.fill((191, 191, 191, 255), special_flags=pygame.BLEND_RGBA_MULT)
        return dimmed

    def _blit_disabled_overlay(self) -> None:
        """Overlay the widget draw rect with a 25% black tint."""
        if self.surface is None:
            return
        overlay = Surface((self.draw_rect.width, self.draw_rect.height), pygame.SRCALPHA).convert_alpha()
        overlay.fill((0, 0, 0, 64))
        self.surface.blit(overlay, (self.draw_rect.x, self.draw_rect.y))

    def leave(self) -> None:
        """Hook called when focus leaves this widget."""
        return

    def get_collide(self, window: Optional["Window"] = None) -> bool:
        """Return True when the current mouse position is inside this widget."""
        mouse_point = self.gui._convert_to_window(self.gui._get_mouse_pos(), window)
        if self.hit_rect is None:
            return point_in_rect(mouse_point, self.draw_rect)
        return point_in_rect(mouse_point, self.hit_rect)

    def handle_event(self, _: PygameEvent, _a: Optional["Window"]) -> bool:
        """Handle an input event. Subclasses return True on activation."""
        return False

    def build_gui_event(self, window: Optional["Window"] = None) -> "GuiEvent":
        """Create the GUI event emitted when this widget activates."""
        return self.gui.event(Event.Widget, widget_id=self.id, window=window)

    def should_handle_outside_collision(self) -> bool:
        """Return True when this widget should still process events off-collision."""
        return False

    def draw(self) -> None:
        """Draw the widget. Subclasses should call this first when needed."""
        if self.surface is None:
            raise GuiError(f'widget "{self.id}" is not bound to a surface')
        if self.auto_restore_pristine:
            self.gui.restore_pristine(self.draw_rect, self.window)
