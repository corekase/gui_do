from __future__ import annotations

from typing import Optional, Tuple

from pygame import Rect


def _anchor_adjusted_lock_rect(axis: str, track_rect: Rect, handle_rect: Rect, anchor: int, pointer_pos: tuple) -> Rect:
    """Compute a pointer lock rect that is anchor-offset so the logical pointer
    stops moving when the thumb reaches either end of the track.

    The valid pointer range is [track.start + anchor, track.end - handle_size + anchor].
    Subtracting *anchor* from the clamped pointer always yields a valid handle_top/left
    in [track.start, track.end - handle_size] — identical to how ScrollbarControl does it.
    """
    if axis == "y":
        min_py = int(track_rect.y) + anchor
        max_py = int(track_rect.bottom) - int(handle_rect.height) + anchor
        if max_py < min_py:
            max_py = min_py
        lock_x = int(track_rect.x + (track_rect.width // 2))
        return Rect(lock_x, min_py, 1, max(1, (max_py - min_py) + 1))
    else:  # x
        min_px = int(track_rect.x) + anchor
        max_px = int(track_rect.right) - int(handle_rect.width) + anchor
        if max_px < min_px:
            max_px = min_px
        lock_y = int(track_rect.y + (track_rect.height // 2))
        return Rect(min_px, lock_y, max(1, (max_px - min_px) + 1), 1)


def begin_thumb_drag(app, owner_id: str, axis: str, track_rect: Rect, pointer_pos: tuple[int, int], handle_rect: Rect) -> int:
    """Begin pointer-captured thumb drag and return the anchor offset.

    The lock rect is anchor-adjusted (matching ScrollbarControl._lock_rect) so that
    the logical pointer clamps exactly when the thumb reaches either track end — the
    cursor stops moving when the handle can go no further.

    Returns the anchor value (pointer_axis_pos - handle_axis_pos) that callers should
    store and pass back as *anchor* to ``refresh_thumb_drag_lock``.
    """
    axis_name = str(axis).lower()
    if axis_name not in ("x", "y"):
        raise ValueError("axis must be 'x' or 'y'")

    if axis_name == "y":
        anchor = int(pointer_pos[1]) - int(handle_rect.y)
    else:
        anchor = int(pointer_pos[0]) - int(handle_rect.x)

    lock_rect = _anchor_adjusted_lock_rect(axis_name, track_rect, handle_rect, anchor, pointer_pos)
    app.pointer_capture.begin(str(owner_id), lock_rect, use_relative_motion=True)
    return anchor


def captured_pointer_pos(app, owner_id: str, axis: str) -> Optional[Tuple[int, int]]:
    """Return the logical pointer clamped to the current capture lock rect.

    Clamps on the drag axis only (matching ScrollbarControl motion handler) and calls
    set_logical_pointer_position so the rendered cursor stays within bounds without
    hardware warping.  Returns None when this owner does not hold capture.
    """
    if not app.pointer_capture.is_owned_by(str(owner_id)):
        return None

    pointer_pos = app.logical_pointer_pos
    if not (isinstance(pointer_pos, tuple) and len(pointer_pos) == 2):
        return None
    px, py = int(pointer_pos[0]), int(pointer_pos[1])

    lock = app.pointer_capture.lock_rect
    if lock is None:
        return (px, py)

    axis_name = str(axis).lower()
    if axis_name == "y":
        clamped_py = min(max(py, int(lock.top)), int(lock.bottom) - 1)
        clamped = (int(lock.left), clamped_py)
    elif axis_name == "x":
        clamped_px = min(max(px, int(lock.left)), int(lock.right) - 1)
        clamped = (clamped_px, int(lock.top))
    else:
        raise ValueError("axis must be 'x' or 'y'")

    app.set_logical_pointer_position(clamped, apply_constraints=False)
    return clamped


def end_thumb_drag(app, owner_id: str, *, sync_pointer: bool = True, release_pos=None) -> None:
    """End pointer capture for a thumb drag and optionally sync hardware pointer."""
    if app.pointer_capture.is_owned_by(str(owner_id)):
        app.pointer_capture.end(str(owner_id))

    if not sync_pointer:
        return

    final_pos = release_pos if release_pos is not None else app.logical_pointer_pos
    if isinstance(final_pos, tuple) and len(final_pos) == 2:
        app.sync_pointer_to_logical_position((int(final_pos[0]), int(final_pos[1])))
