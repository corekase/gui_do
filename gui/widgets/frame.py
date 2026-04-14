from ..values.constants import WidgetKind, FrameState
from .utility.widget import Widget
from .utility.registry import register_widget

# Backward compatibility alias
FrState = FrameState

@register_widget("Frame")
class Frame(Widget):
    def __init__(self, gui, id, rect):
        super().__init__(gui, id, rect)
        self.WidgetKind = WidgetKind.Frame
        self.idle, self.hover, self.armed = self.gui.bitmap_factory.draw_frame_bitmaps(rect)
        self.state = FrameState.Idle

    def handle_event(self, _, _a):
        return False

    def draw(self):
        super().draw()
        if self.state == FrameState.Idle:
            self.surface.blit(self.idle, (self.draw_rect.x, self.draw_rect.y))
        elif self.state == FrameState.Hover:
            self.surface.blit(self.hover, (self.draw_rect.x, self.draw_rect.y))
        elif self.state == FrameState.Armed:
            self.surface.blit(self.armed, (self.draw_rect.x, self.draw_rect.y))
