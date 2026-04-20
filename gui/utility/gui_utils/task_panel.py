from __future__ import annotations

import pygame
from pygame import Rect
from pygame.surface import Surface
from typing import Callable, List, Optional, Tuple, Union, TYPE_CHECKING

from ..events import BaseEvent, GuiError, InteractiveState
from ..intermediates.widget import Widget
from ..lifecycle.lifecycle_callbacks import _noop, _noop_event
from ..events import ButtonStyle
from ...widgets.frame import Frame
from ...widgets.arrowbox import ArrowBox
from ...widgets.button import Button
from ...widgets.buttongroup import ButtonGroup
from ...widgets.canvas import Canvas
from ...widgets.image import Image
from ...widgets.label import Label
from ...widgets.scrollbar import Scrollbar
from ...widgets.slider import Slider
from ...widgets.toggle import Toggle

if TYPE_CHECKING:
    from ..gui_manager import GuiManager, ScrollbarStyle


class _ManagedTaskPanel:
    """GuiManager-owned bottom task panel container."""

    def __init__(
        self,
        gui: "GuiManager",
        panel_height: int,
        left: int,
        width: Optional[int],
        hidden_peek_pixels: int,
        auto_hide: bool,
        animation_interval_ms: float,
        animation_step_px: int,
        backdrop_image: Optional[str],
        preamble: Optional[Callable[[], None]],
        event_handler: Optional[Callable[[BaseEvent], None]],
        postamble: Optional[Callable[[], None]],
    ) -> None:
        """Validate configuration, allocate panel surfaces, and start animation timer."""
        # Validate all config up front so partial panel construction never leaks.
        if not isinstance(panel_height, int) or panel_height <= 0:
            raise GuiError(f'task_panel_panel_height must be a positive int, got: {panel_height}')
        if not isinstance(left, int):
            raise GuiError(f'task_panel_left must be an int, got: {left}')
        if width is not None and not isinstance(width, int):
            raise GuiError(f'task_panel_width must be an int or None, got: {width}')
        if not isinstance(hidden_peek_pixels, int) or hidden_peek_pixels < 1:
            raise GuiError(f'task_panel_hidden_peek_pixels must be >= 1, got: {hidden_peek_pixels}')
        if not isinstance(auto_hide, bool):
            raise GuiError('task_panel_auto_hide must be a bool')
        if not isinstance(animation_step_px, int) or animation_step_px <= 0:
            raise GuiError(f'task_panel_animation_step_px must be > 0, got: {animation_step_px}')
        if animation_interval_ms <= 0:
            raise GuiError(f'task_panel_animation_interval_ms must be > 0, got: {animation_interval_ms}')
        screen_rect = gui.surface.get_rect()
        if left < 0 or left >= screen_rect.width:
            raise GuiError(f'task_panel_left must be in range [0, {screen_rect.width - 1}], got: {left}')
        panel_width = (screen_rect.width - left) if width is None else width
        if panel_width <= 0:
            raise GuiError(f'task_panel_width must be > 0, got: {panel_width}')
        if left + panel_width > screen_rect.width:
            raise GuiError(
                f'task_panel_left + task_panel_width must be <= screen width ({screen_rect.width}), '
                f'got: left={left}, width={panel_width}'
            )
        if hidden_peek_pixels >= panel_height:
            raise GuiError(f'task_panel_hidden_peek_pixels must be < panel height ({panel_height}), got: {hidden_peek_pixels}')
        # Persist layout/state fields used by animation and rendering paths.
        self.gui: "GuiManager" = gui
        self.left: int = left
        self.width: int = panel_width
        self.panel_height: int = panel_height
        self.visible: bool = True
        self.widgets: List[Widget] = []
        self.surface: Surface = pygame.surface.Surface((self.width, self.panel_height)).convert()
        self.pristine: Optional[Surface] = None
        self.hidden_peek_pixels: int = hidden_peek_pixels
        self.auto_hide: bool = auto_hide
        self.animation_interval_ms: float = animation_interval_ms
        self.animation_step_px: int = animation_step_px
        self._shown_y: int = screen_rect.height - self.panel_height
        self._hidden_y: int = screen_rect.height - self.hidden_peek_pixels
        self.y: int = self._hidden_y if self.auto_hide else self._shown_y
        self._hovered: bool = False
        self._timer_id: Tuple[str, int] = ('task-panel-motion', id(self))
        self._preamble: Callable[[], None] = preamble if callable(preamble) else _noop
        self._event_handler: Callable[[BaseEvent], None] = event_handler if callable(event_handler) else _noop_event
        self._postamble: Callable[[], None] = postamble if callable(postamble) else _noop
        self.backdrop_image: Optional[str] = backdrop_image
        # Build pristine background either from default frame or supplied backdrop.
        if backdrop_image is None:
            frame = Frame(gui, 'task_panel_frame', Rect(0, 0, self.width, self.panel_height))
            frame.state = InteractiveState.Idle
            frame.surface = self.surface
            frame.draw()
            self.pristine = gui.copy_graphic_area(self.surface, self.surface.get_rect()).convert()
        else:
            gui.set_pristine(backdrop_image, self)
        # Drive smooth reveal/hide behavior with a recurring timer callback.
        gui.timers.add_timer(self._timer_id, self.animation_interval_ms, self.animate)

    def dispose(self) -> None:
        """Release timer resources owned by the panel."""
        self.gui.timers.remove_timer(self._timer_id)

    # Widget construction API mirrors GuiManager signatures for IDE IntelliSense parity.
    def arrow_box(self, id: str, rect: Rect, direction: float, on_activate: Optional[Callable[[], None]] = None) -> ArrowBox:
        return self.gui._task_panel_arrow_box(id, rect, direction, on_activate)

    def button(self, id: str, rect: Rect, style: ButtonStyle, text: Optional[str], on_activate: Optional[Callable[[], None]] = None) -> Button:
        return self.gui._task_panel_button(id, rect, style, text, on_activate)

    def button_group(self, group: str, id: str, rect: Rect, style: ButtonStyle, text: str) -> ButtonGroup:
        return self.gui._task_panel_button_group(group, id, rect, style, text)

    def canvas(self, id: str, rect: Rect, backdrop: Optional[str] = None, on_activate: Optional[Callable[[], None]] = None, automatic_pristine: bool = False) -> Canvas:
        return self.gui._task_panel_canvas(id, rect, backdrop, on_activate, automatic_pristine)

    def frame(self, id: str, rect: Rect) -> Frame:
        return self.gui._task_panel_frame(id, rect)

    def image(self, id: str, rect: Rect, image: str, automatic_pristine: bool = False, scale: bool = True) -> Image:
        return self.gui._task_panel_image(id, rect, image, automatic_pristine, scale)

    def label(self, position: Union[Tuple[int, int], Tuple[int, int, int, int]], text: str, shadow: bool = False, id: Optional[str] = None) -> Label:
        return self.gui._task_panel_label(position, text, shadow, id)

    def scrollbar(
        self,
        id: str,
        overall_rect: Rect,
        horizontal: bool,
        style: ScrollbarStyle,
        total_range: int,
        start_pos: int,
        bar_size: int,
        inc_size: int,
        wheel_positive_to_max: bool = False,
    ) -> Scrollbar:
        return self.gui._task_panel_scrollbar(
            id,
            overall_rect,
            horizontal,
            style,
            total_range,
            start_pos,
            bar_size,
            inc_size,
            wheel_positive_to_max,
        )

    def slider(
        self,
        id: str,
        rect: Rect,
        horizontal: bool,
        total_range: int,
        position: float = 0.0,
        integer_type: bool = False,
        notch_interval_percent: float = 5.0,
        wheel_positive_to_max: bool = False,
        wheel_step: Optional[float] = None,
    ) -> Slider:
        return self.gui._task_panel_slider(
            id,
            rect,
            horizontal,
            total_range,
            position,
            integer_type,
            notch_interval_percent,
            wheel_positive_to_max,
            wheel_step,
        )

    def toggle(self, id: str, rect: Rect, style: ButtonStyle, pushed: bool, pressed_text: str, raised_text: Optional[str] = None) -> Toggle:
        return self.gui._task_panel_toggle(id, rect, style, pushed, pressed_text, raised_text)

    def run_preamble(self) -> None:
        """Invoke panel preamble lifecycle callback."""
        self._preamble()

    def run_postamble(self) -> None:
        """Invoke panel postamble lifecycle callback."""
        self._postamble()

    def handle_event(self, event: BaseEvent) -> None:
        """Forward a GUI event to the configured panel event handler."""
        self._event_handler(event)

    def set_lifecycle(
        self,
        preamble: Optional[Callable[[], None]],
        event_handler: Optional[Callable[[BaseEvent], None]],
        postamble: Optional[Callable[[], None]],
    ) -> None:
        """Replace lifecycle callbacks, defaulting missing handlers to no-op."""
        self._preamble = preamble if preamble is not None else _noop
        self._event_handler = event_handler if event_handler is not None else _noop_event
        self._postamble = postamble if postamble is not None else _noop

    def get_rect(self) -> Rect:
        """Return current screen-space panel bounds."""
        return Rect(self.left, self.y, self.width, self.panel_height)

    def refresh_targets(self) -> None:
        """Recompute shown/hidden y targets and hover status from current screen state."""
        screen_rect = self.gui.surface.get_rect()
        self._shown_y = screen_rect.height - self.panel_height
        self._hidden_y = screen_rect.height - self.hidden_peek_pixels
        self._hovered = self.get_rect().collidepoint(self.gui._get_mouse_pos())

    def draw_background(self) -> None:
        """Restore panel background from pristine snapshot before drawing children."""
        if self.pristine is None:
            raise GuiError('task panel pristine is not initialized')
        self.gui.restore_pristine(self.surface.get_rect(), self)

    def animate(self) -> None:
        """Move panel toward shown/hidden target according to auto-hide rules."""
        if not self.visible:
            return
        self.refresh_targets()
        target_y = self._hidden_y
        # Hover or disabled auto-hide keeps the panel fully revealed.
        if not self.auto_hide or self._hovered:
            target_y = self._shown_y
        # Step movement gradually to avoid abrupt panel jumps.
        if self.y < target_y:
            self.y = min(target_y, self.y + self.animation_step_px)
        elif self.y > target_y:
            self.y = max(target_y, self.y - self.animation_step_px)

    def set_visible(self, visible: bool) -> None:
        """Enable or disable panel visibility and refresh targets when shown."""
        if not isinstance(visible, bool):
            raise GuiError('task panel visibility must be a bool')
        self.visible = visible
        if visible:
            self.refresh_targets()

    def set_auto_hide(self, auto_hide: bool) -> None:
        """Set auto-hide behavior and snap visible panel when disabling it."""
        if not isinstance(auto_hide, bool):
            raise GuiError('task panel auto_hide must be a bool')
        self.auto_hide = auto_hide
        if not auto_hide:
            self.refresh_targets()
            self.y = self._shown_y

    def set_hidden_peek_pixels(self, hidden_peek_pixels: int) -> None:
        """Configure how many panel pixels remain visible while hidden."""
        if not isinstance(hidden_peek_pixels, int):
            raise GuiError(f'task panel hidden_peek_pixels must be an int, got: {hidden_peek_pixels}')
        if hidden_peek_pixels < 1:
            raise GuiError(f'task panel hidden_peek_pixels must be >= 1, got: {hidden_peek_pixels}')
        if hidden_peek_pixels >= self.panel_height:
            raise GuiError(f'task panel hidden_peek_pixels must be < panel height ({self.panel_height}), got: {hidden_peek_pixels}')
        self.hidden_peek_pixels = hidden_peek_pixels
        self.refresh_targets()

    def set_animation_step_px(self, animation_step_px: int) -> None:
        """Configure per-animation-step vertical movement magnitude."""
        if not isinstance(animation_step_px, int):
            raise GuiError(f'task panel animation_step_px must be an int, got: {animation_step_px}')
        if animation_step_px <= 0:
            raise GuiError(f'task panel animation_step_px must be > 0, got: {animation_step_px}')
        self.animation_step_px = animation_step_px

    def set_animation_interval_ms(self, animation_interval_ms: float) -> None:
        """Update animation timer interval and re-register timer callback."""
        if animation_interval_ms <= 0:
            raise GuiError(f'task panel animation_interval_ms must be > 0, got: {animation_interval_ms}')
        self.animation_interval_ms = animation_interval_ms
        # Rebind timer so the new interval takes effect immediately.
        self.gui.timers.remove_timer(self._timer_id)
        self.gui.timers.add_timer(self._timer_id, self.animation_interval_ms, self.animate)
