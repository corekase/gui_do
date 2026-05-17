"""Generalized helpers for category-driven control visibility."""

from __future__ import annotations

from gui_do.features.feature_lifecycle import apply_category_visibility


class TabCategoryVisibilityManager:
    def __init__(self, *, category_fn):
        self._category_fn = category_fn

    def apply(
        self,
        *,
        active_category: str,
        placed_controls,
        control_labels,
        focus_controller=None,
        fallback_focus_target=None,
    ) -> None:
        apply_category_visibility(
            active_key=active_category,
            placed_controls=placed_controls,
            control_labels=control_labels,
            category_fn=self._category_fn,
        )

        if focus_controller is None:
            return
        focused = getattr(focus_controller, "focused", None)
        if focused is None:
            return
        if getattr(focused, "visible", True):
            return
        if fallback_focus_target is None:
            return
        if getattr(fallback_focus_target, "visible", False) and getattr(fallback_focus_target, "enabled", False):
            focus_controller.set_focus(fallback_focus_target)


__all__ = ["TabCategoryVisibilityManager"]
