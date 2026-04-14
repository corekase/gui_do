from pygame.locals import MOUSEMOTION, MOUSEBUTTONDOWN, MOUSEBUTTONUP
from ..values.constants import GType
from .utility.interactive import BaseInteractive, State
from .utility.registry import register_widget

@register_widget("Button")
class Button(BaseInteractive):
    def __init__(self, gui, id, rect, style, text, button_callback=None, skip_factory=False):
        # initialize common widget values
        super().__init__(gui, id, rect)
        self.GType = GType.Button
        # this object's timer
        self.timer_id = None
        if not skip_factory:
            factory = self.gui.get_bitmapfactory()
            (self.idle, self.hover, self.armed), self.hit_rect = \
                factory.get_styled_bitmaps(style, text, rect)
        # button specific callback, this callback is separate from the add() callback
        self.button_callback = button_callback

    def handle_event(self, event, window):
        if event.type not in (MOUSEMOTION, MOUSEBUTTONDOWN, MOUSEBUTTONUP):
            return False

        # Call base interactive logic first
        if not super().handle_event(event, window):
            if self.timer_id is not None:
                self.gui.timers.remove_timer(self.timer_id)
                self.timer_id = None
            return False

        # manage the state of the button
        if self.state == State.Hover:
            if event.type == MOUSEBUTTONDOWN:
                if event.button == 1:
                    self.state = State.Armed
                    if self.button_callback is not None:
                        self.button_callback()
                        if self.timer_id is None:
                            self.gui.timers.add_timer(f'{self.id}.timer', 150, self.button_callback)
                            self.timer_id = f'{self.id}.timer'
                    return False
        if self.state == State.Armed:
            if event.type == MOUSEBUTTONUP:
                if event.button == 1:
                    if self.timer_id is not None:
                        self.gui.timers.remove_timer(f'{self.id}.timer')
                        self.timer_id = None
                    self.state = State.Hover
                    if self.button_callback is not None:
                        return False
                    return True
        return False

    def leave(self):
        if self.timer_id is not None:
            self.gui.timers.remove_timer(f'{self.id}.timer')
            self.timer_id = None
        super().leave()
