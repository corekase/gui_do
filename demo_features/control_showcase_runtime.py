"""Runtime helpers for control showcase scene behavior."""

from __future__ import annotations


def control_has_open_popup(control) -> bool:
    # Open-state conventions across controls in this demo:
    # - _open (date picker)
    # - _dropdown_open (split button)
    # - _is_open (dropdown control, overlay-backed)
    # - _open_index >= 0 (menu bar flyout)
    if bool(getattr(control, "_open", False)):
        return True
    if bool(getattr(control, "_dropdown_open", False)):
        return True
    if bool(getattr(control, "_is_open", False)):
        return True
    open_index = getattr(control, "_open_index", -1)
    return isinstance(open_index, int) and open_index >= 0


def promote_open_popup_controls(root, controls: list) -> bool:
    if root is None:
        return False
    children = getattr(root, "children", None)
    if not isinstance(children, list) or not children:
        return False

    open_controls = [
        control
        for control in controls
        if control in children and control.visible and control.enabled and control_has_open_popup(control)
    ]
    if not open_controls:
        return False

    changed = False
    for control in open_controls:
        idx = children.index(control)
        if idx != len(children) - 1:
            children.append(children.pop(idx))
            changed = True

    if changed:
        root.invalidate()
    return changed
