from pygame.locals import MOUSEMOTION, MOUSEBUTTONDOWN
from ..values.constants import WidgetKind
from .utility.interactive import BaseInteractive, InteractiveState
from .utility.registry import register_widget

@register_widget("Toggle")
class Toggle(BaseInteractive):
    def __init__(self, gui, id, rect, style, pushed, pressed_text, raised_text=None):
        super().__init__(gui, id, rect)
        self.WidgetKind = WidgetKind.Toggle
        self.pushed = pushed
        if raised_text is None:
            raised_text = pressed_text
        (_, _, self.armed), rect1 = \
            self.gui.bitmap_factory.get_styled_bitmaps(style, pressed_text, rect)
        (self.idle, self.hover, _), rect2 = \
            self.gui.bitmap_factory.get_styled_bitmaps(style, raised_text, rect)
        if rect1.width > rect2.width:
            self.hit_rect = rect1
        else:
            self.hit_rect = rect2

    def handle_event(self, event, window):
        if event.type not in (MOUSEMOTION, MOUSEBUTTONDOWN):
            return False

        # Call base logic
        if not super().handle_event(event, window):
            return False

        if self.state == InteractiveState.Hover:
            if event.type == MOUSEBUTTONDOWN and event.button == 1:
                self.pushed = not self.pushed
                return True
        return False

    def draw(self):
        if self.pushed:
            self.surface.blit(self.armed, self.draw_rect)
        else:
            super().draw()

    def set(self, pushed):
        self.pushed = pushed

    def read(self):
        return self.pushed
