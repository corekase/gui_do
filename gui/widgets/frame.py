from typing import Any
from ..utility.constants import WidgetKind, InteractiveState
from ..utility.widget import Widget

class Frame(Widget):
    def __init__(self, gui: Any, id: Any, rect: Any) -> None:
        super().__init__(gui, id, rect)
        self.WidgetKind = WidgetKind.Frame
        self.idle: Any
        self.hover: Any
        self.armed: Any
        self.idle, self.hover, self.armed = self.gui.bitmap_factory.draw_frame_bitmaps(rect)
        self.state: InteractiveState = InteractiveState.Idle

    def handle_event(self, _, _a) -> bool:
        return False

    def draw(self) -> None:
        super().draw()
        if self.state == InteractiveState.Idle:
            self.surface.blit(self.idle, (self.draw_rect.x, self.draw_rect.y))
        elif self.state == InteractiveState.Hover:
            self.surface.blit(self.hover, (self.draw_rect.x, self.draw_rect.y))
        elif self.state == InteractiveState.Armed:
            self.surface.blit(self.armed, (self.draw_rect.x, self.draw_rect.y))
