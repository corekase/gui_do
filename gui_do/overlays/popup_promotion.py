"""Popup z-order promotion utilities.

Provides helpers for detecting open transient popup state on any control and
for promoting open-popup controls to the top of a container's child list so
they render on top of siblings.

Usage::

    from gui_do import control_has_open_popup, promote_open_popup_controls

    # In on_update:
    promote_open_popup_controls(root_panel, registry.controls)
"""
from __future__ import annotations


def control_has_open_popup(control) -> bool:
    """Return ``True`` if *control* appears to have an open popup or dropdown.

    Inspects the conventional private-flag attributes that gui_do controls use
    to track open transient state.  Returns ``False`` for controls that expose
    none of these attributes.

    Recognised flags (in order):
        - ``_open``
        - ``_dropdown_open``
        - ``_is_open``
        - ``_open_index`` (open when ``>= 0``)
    """
    if bool(getattr(control, "_open", False)):
        return True
    if bool(getattr(control, "_dropdown_open", False)):
        return True
    if bool(getattr(control, "_is_open", False)):
        return True
    open_index = getattr(control, "_open_index", -1)
    return isinstance(open_index, int) and open_index >= 0


def promote_open_popup_controls(root, controls: list) -> bool:
    """Move controls with open popups to the end of *root*'s child list.

    Rendering order follows child order, so the last child renders on top.
    When a dropdown or menu is open its control must render above siblings to
    avoid being clipped.  Calls ``root.invalidate()`` if any reordering was
    done.

    Args:
        root: Parent container whose ``.children`` list is mutated in-place.
        controls: Subset of *root*'s children to inspect for open popup state.

    Returns:
        ``True`` if at least one control was reordered, ``False`` otherwise.
    """
    if root is None:
        return False
    children = getattr(root, "children", None)
    if not isinstance(children, list) or not children:
        return False
    open_controls = [
        c for c in controls
        if c in children and c.visible and c.enabled and control_has_open_popup(c)
    ]
    if not open_controls:
        return False
    changed = False
    for c in open_controls:
        idx = children.index(c)
        if idx != len(children) - 1:
            children.append(children.pop(idx))
            changed = True
    if changed:
        root.invalidate()
    return changed


__all__ = ["control_has_open_popup", "promote_open_popup_controls"]
