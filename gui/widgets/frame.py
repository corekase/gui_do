from typing import Any
from ..utility.values.constants import WidgetKind, FrameState
from ..utility.widget import Widget
from ..utility.registry import register_widget

@register_widget("Frame")
class Frame(Widget):
    def __init__(self, gui: Any, id: Any, rect: Any) -> None:
        super().__init__(gui, id, rect)
        self.WidgetKind = WidgetKind.Frame
        self.idle: Any
        self.hover: Any
        self.armed: Any
        self.idle, self.hover, self.armed = self.gui.bitmap_factory.draw_frame_bitmaps(rect)
        self.state: FrameState = FrameState.Idle

    def handle_event(self, _, _a) -> bool:
        return False

    def draw(self) -> None:
        super().draw()
        if self.state == FrameState.Idle:
            self.surface.blit(self.idle, (self.draw_rect.x, self.draw_rect.y))
        elif self.state == FrameState.Hover:
            self.surface.blit(self.hover, (self.draw_rect.x, self.draw_rect.y))
        elif self.state == FrameState.Armed:
            self.surface.blit(self.armed, (self.draw_rect.x, self.draw_rect.y))
