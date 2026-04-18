from typing import Callable, Iterable, Tuple

from pygame.event import Event as PygameEvent


class InputProviders:
    """Runtime input provider callbacks used by event and pointer flows."""

    def __init__(
        self,
        event_getter: Callable[[], Iterable[PygameEvent]],
        mouse_get_pos: Callable[[], Tuple[int, int]],
        mouse_set_pos: Callable[[Tuple[int, int]], None],
        mouse_set_visible: Callable[[bool], None],
    ) -> None:
        self.event_getter = event_getter
        self.mouse_get_pos = mouse_get_pos
        self.mouse_set_pos = mouse_set_pos
        self.mouse_set_visible = mouse_set_visible
