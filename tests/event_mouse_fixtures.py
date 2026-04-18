from types import SimpleNamespace
from typing import Any, Callable, Dict, Optional, Tuple


def build_mouse_gui_stub(
    mouse_pos: Tuple[int, int] = (0, 0),
    *,
    set_lock_area: Optional[Callable[[Any, Optional[Any]], None]] = None,
    extras: Optional[Dict[str, Any]] = None,
) -> Any:
    """Create a mutable gui-like stub with common mouse/coordinate helpers."""
    state: Dict[str, Tuple[int, int]] = {"mouse_pos": mouse_pos}

    gui = SimpleNamespace()
    gui.get_mouse_pos = lambda: state["mouse_pos"]
    gui.set_mouse_pos = lambda pos: state.__setitem__("mouse_pos", pos)
    gui.convert_to_window = lambda point, _window: point
    gui.convert_to_screen = lambda point, _window: point
    gui.windows = []

    if set_lock_area is not None:
        gui.set_lock_area = set_lock_area

    if extras:
        for key, value in extras.items():
            setattr(gui, key, value)

    return gui
