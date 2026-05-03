"""Category visibility and relayout policy for the controls showcase."""

from __future__ import annotations

from collections.abc import Callable

from pygame import Rect
from gui_do import LabelControl


BASICS_SUPPRESSED_LABEL_NAMES: frozenset[str] = frozenset({
    "button_2", "button_3",
    "toggle_2", "toggle_3",
    "button_group_a2", "button_group_a3",
    "button_group_b2", "button_group_b3",
    "button_group_c2", "button_group_c3",
})


def category_for_row(row_index: int) -> str:
    if row_index < 60:
        return "basics"
    if row_index < 100:
        return "data"
    if row_index < 140:
        return "advanced"
    return "extended"


def relayout_category(
    *,
    category_key: str,
    category_content_bounds: Rect,
    placed_controls: list,
    gallery_layout,
    ensure_basics_aux_label: Callable[[str], object | None],
) -> None:
    bounds = Rect(category_content_bounds)
    if bounds.width <= 0 or bounds.height <= 0:
        return

    items = [
        placed
        for placed in placed_controls
        if category_for_row(int(placed.row_index)) == category_key
    ]
    if not items:
        return

    if category_key == "basics":
        gallery_layout.relayout_basics(
            Rect(bounds),
            items,
            ensure_aux_label=ensure_basics_aux_label,
        )
        return

    gallery_layout.relayout_grid_items(category_key, Rect(bounds), items)


def apply_category_visibility(
    *,
    active_key: str,
    category_content_bounds: Rect,
    placed_controls: list,
    control_labels: list,
    basics_aux_labels: dict[str, object],
    gallery_layout,
    ensure_basics_aux_label: Callable[[str], object | None],
    basics_suppressed_label_names: frozenset[str],
) -> None:
    relayout_category(
        category_key=active_key,
        category_content_bounds=Rect(category_content_bounds),
        placed_controls=placed_controls,
        gallery_layout=gallery_layout,
        ensure_basics_aux_label=ensure_basics_aux_label,
    )

    matched_labels = {placed.label for placed in placed_controls if placed.label is not None}
    if active_key == "basics":
        matched_labels.update(basics_aux_labels.values())

    for placed in placed_controls:
        show = category_for_row(int(placed.row_index)) == active_key
        placed.control.visible = show
        placed.control.enabled = show
        if placed.label is not None:
            show_label = show and not (
                active_key == "basics"
                and str(placed.name) in basics_suppressed_label_names
            )
            placed.label.visible = show_label
            placed.label.enabled = show_label

    for label in control_labels:
        if label not in matched_labels:
            label.visible = False
            label.enabled = False


def ensure_basics_aux_label(
    *,
    name: str,
    basics_aux_labels: dict[str, LabelControl],
    root,
    control_labels: list[LabelControl],
) -> LabelControl | None:
    label = basics_aux_labels.get(name)
    if label is not None:
        return label

    text_map = {
        "vertical_scrollbar": "Vertical scrollbar",
        "vertical_slider": "Vertical slider",
    }
    text = text_map.get(name)
    if text is None or root is None:
        return None

    label = LabelControl(
        f"controls_showcase_aux_label_{name}",
        Rect(0, 0, 1, 1),
        text,
        align="left",
    )
    root.add(label)
    control_labels.append(label)
    basics_aux_labels[name] = label
    return label
