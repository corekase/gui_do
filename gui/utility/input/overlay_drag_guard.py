from __future__ import annotations

from typing import Any, Callable, Optional

from ..geometry import point_in_rect


def cancel_drag_for_overlay_contact(
    gui: Any,
    is_dragging: bool,
    owner_window: Optional[Any],
    cancel_drag: Callable[[], None],
    on_cancel: Optional[Callable[[], None]] = None,
) -> bool:
    """Cancel drag when pointer enters an overlaid window region."""
    if not is_dragging:
        return False

    topmost_window = None
    mouse_pos = gui._get_mouse_pos()
    for candidate in tuple(gui.windows)[::-1]:
        if not candidate.visible:
            continue
        if point_in_rect(mouse_pos, candidate.get_window_rect()):
            topmost_window = candidate
            break

    if owner_window is None:
        blocked = topmost_window is not None
    else:
        blocked = topmost_window is not None and topmost_window is not owner_window

    if not blocked:
        return False
    cancel_drag()
    if on_cancel is not None:
        on_cancel()
    return True
