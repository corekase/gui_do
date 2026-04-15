from typing import Optional, Any, Callable
from pygame.locals import MOUSEMOTION, MOUSEBUTTONDOWN, MOUSEBUTTONUP
from ..utility.values.constants import WidgetKind
from ..utility.interactive import BaseInteractive, InteractiveState

class Button(BaseInteractive):
    def __init__(self, gui: Any, id: Any, rect: Any, style: Any, text: Optional[str], button_callback: Optional[Callable] = None, skip_factory: bool = False) -> None:
        # initialize common widget values
        super().__init__(gui, id, rect)
        self.WidgetKind = WidgetKind.Button
        # this object's timer
        self.timer_id: Optional[str] = None
        if not skip_factory:
            (self.idle, self.hover, self.armed), self.hit_rect = \
                self.gui.bitmap_factory.get_styled_bitmaps(style, text, rect)
        # button specific callback, this callback is separate from the add() callback
        self.button_callback: Optional[Callable] = button_callback

    def handle_event(self, event: Any, window: Any) -> bool:
        if event.type not in (MOUSEMOTION, MOUSEBUTTONDOWN, MOUSEBUTTONUP):
            return False

        # Call base interactive logic first
        if not super().handle_event(event, window):
            if self.timer_id is not None:
                self.gui.timers.remove_timer(self.timer_id)
                self.timer_id = None
            return False

        # manage the state of the button
        if self.state == InteractiveState.Hover:
            if event.type == MOUSEBUTTONDOWN:
                if event.button == 1:
                    self.state = InteractiveState.Armed
                    if self.button_callback is not None:
                        self.button_callback()
                        if self.timer_id is None:
                            self.gui.timers.add_timer(f'{self.id}.timer', 150, self.button_callback)
                            self.timer_id = f'{self.id}.timer'
                    return False
        if self.state == InteractiveState.Armed:
            if event.type == MOUSEBUTTONUP:
                if event.button == 1:
                    if self.timer_id is not None:
                        self.gui.timers.remove_timer(f'{self.id}.timer')
                        self.timer_id = None
                    self.state = InteractiveState.Hover
                    if self.button_callback is not None:
                        return False
                    return True
        return False

    def leave(self) -> None:
        if self.timer_id is not None:
            self.gui.timers.remove_timer(f'{self.id}.timer')
            self.timer_id = None
        super().leave()
        self.state = InteractiveState.Idle
