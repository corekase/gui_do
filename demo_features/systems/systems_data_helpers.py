"""Data-tab helpers for the systems demo feature."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pygame import Rect

from gui_do import ButtonControl, DropdownControl, DropdownOption, LabelControl, ListViewControl, PanelControl
from gui_do.controls.data.list_view_control import ListItem

from .systems_models import _BacklogItem

if TYPE_CHECKING:
    from .systems_feature import SystemsFeature


def build_data_panel(feature: SystemsFeature, rect: Rect) -> PanelControl:
    panel = PanelControl("systems_data_panel", Rect(rect), draw_background=False)
    left_w = max(280, int(rect.width * 0.58))
    right_x = left_w + 20
    right_w = max(180, rect.width - right_x - feature.PANEL_PADDING_X)
    action_button_w = 120

    filter_label = LabelControl(
        "systems_data_filter_label",
        Rect(0, 0, 72, 28),
        "Status",
        align="left",
    )
    feature.data_filter_dropdown = DropdownControl(
        "systems_data_filter",
        Rect(0, 0, 180, 32),
        options=[
            DropdownOption("All", "All"),
            DropdownOption("Review", "Review"),
            DropdownOption("Ready", "Ready"),
            DropdownOption("Planned", "Planned"),
        ],
        selected_index=0,
        on_change=lambda value, _index: feature._on_backlog_filter_changed(value),
    )
    feature._place_compact_labeled_row(
        panel,
        left=feature.LEFT_SIDE_INSET_X,
        top=0,
        label=filter_label,
        field=feature.data_filter_dropdown,
        label_width=72,
        gap=8,
    )

    add_button = ButtonControl(
        "systems_add_review_item",
        Rect(0, 0, action_button_w, 32),
        "Queue Review",
        feature._add_backlog_item,
        style="round",
    )
    cache_button = ButtonControl(
        "systems_clear_cache",
        Rect(0, 0, action_button_w, 32),
        "Clear Cache",
        feature._clear_backlog_cache,
        style="round",
    )
    feature._add_button_rows(
        panel,
        rect,
        0,
        [add_button, cache_button],
        per_row=2,
        left=right_x,
        width=right_w,
    )

    feature.data_list = ListViewControl(
        "systems_backlog_list",
        Rect(0, 0, left_w, max(120, rect.height - 52)),
        row_height=28,
        on_select=feature._on_backlog_selected,
    )
    feature.data_list.set_accessibility(role="listbox", label="Deployment backlog")
    feature._place_vertical_grid_sequence(
        panel,
        Rect(
            feature.LEFT_SIDE_INSET_X,
            44,
            max(1, left_w),
            max(1, feature.data_list.rect.height),
        ),
        [(feature.data_list, int(feature.data_list.rect.height), 0)],
    )

    feature.data_summary_label = LabelControl(
        "systems_data_summary",
        Rect(0, 0, right_w, 28),
        "CollectionView keeps the release backlog filtered and sorted.",
        align="left",
    )
    feature.data_cache_label = LabelControl(
        "systems_data_cache",
        Rect(0, 0, right_w, 28),
        "DataCache is ready.",
        align="left",
    )
    feature.data_detail_label = LabelControl(
        "systems_data_detail",
        Rect(0, 0, right_w, 84),
        "Select a backlog item to inspect its cached deployment note.",
        align="left",
    )
    feature._place_vertical_label_stack(
        panel,
        Rect(right_x, 52, max(1, right_w), 164),
        [
            feature.data_summary_label,
            feature.data_cache_label,
            feature.data_detail_label,
        ],
        gap=8,
    )

    feature._backlog_unsub = feature.data_list.bind_collection_view(
        feature._backlog_view,
        on_refresh=feature._on_backlog_view_refreshed,
    )
    feature._refresh_backlog_view()
    return panel


def project_backlog_item(_feature: SystemsFeature, item: _BacklogItem) -> ListItem:
    return ListItem(
        label=f"[{item.status}] P{item.priority} {item.title}",
        value=item.title,
        data=item,
    )


def selected_backlog_filter(feature: SystemsFeature) -> str:
    selected = getattr(feature.data_filter_dropdown, "selected_option", None)
    if selected is None:
        return "All"
    return str(selected.value)


def refresh_backlog_view(feature: SystemsFeature) -> None:
    selected_filter = feature._selected_backlog_filter()
    feature._backlog_view.query.filters = []
    if selected_filter != "All":
        feature._backlog_view.query.filters.append(lambda item, status=selected_filter: item.status == status)
    feature._backlog_view.refresh()
    feature._refresh_backlog_labels()


def on_backlog_filter_changed(feature: SystemsFeature, value: str) -> None:
    _ = value
    feature._selected_backlog_item = None
    feature._refresh_backlog_view()


def on_backlog_view_refreshed(feature: SystemsFeature) -> None:
    if feature.data_list is None:
        return
    items = feature.data_list.items
    if items:
        feature.data_list.selected_index = 0
        feature._on_backlog_selected(0, items[0])
        return
    feature._selected_backlog_item = None
    feature._refresh_backlog_labels()


def on_backlog_selected(feature: SystemsFeature, _index: int, item: ListItem) -> None:
    data = item.data if isinstance(item.data, _BacklogItem) else None
    feature._selected_backlog_item = data
    if data is not None:
        feature._backlog_cache.get_or_load(data.title, lambda: feature._cache_payload_for_backlog_item(data))
    feature._refresh_backlog_labels()


def cache_payload_for_backlog_item(_feature: SystemsFeature, item: _BacklogItem) -> str:
    return f"{item.owner} owns the {item.title.lower()} handoff while the item is in {item.status.lower()} state."


def refresh_backlog_labels(feature: SystemsFeature) -> None:
    if feature.data_summary_label is not None:
        feature.data_summary_label.text = (
            f"CollectionView showing {feature._backlog_view.count()} items for {feature._selected_backlog_filter().lower()} routing."
        )
    if feature.data_cache_label is not None:
        stats = feature._backlog_cache.stats()
        feature.data_cache_label.text = (
            f"DataCache size {stats.size} | hits {stats.hits} | misses {stats.misses} | evictions {stats.evictions}"
        )
    if feature.data_detail_label is not None:
        if feature._selected_backlog_item is None:
            feature.data_detail_label.text = "Select a backlog item to inspect its cached deployment note."
        else:
            payload = feature._backlog_cache.get_or_load(
                feature._selected_backlog_item.title,
                lambda item=feature._selected_backlog_item: feature._cache_payload_for_backlog_item(item),
            )
            feature.data_detail_label.text = payload


def add_backlog_item(feature: SystemsFeature) -> None:
    templates = (
        ("Localization review", "Review", 2, "Nia"),
        ("Accessibility script", "Ready", 3, "Mira"),
        ("Telemetry snapshot", "Planned", 5, "Tao"),
    )
    title, status, priority, owner = templates[feature._next_backlog_index % len(templates)]
    feature._next_backlog_index += 1
    item = _BacklogItem(f"{title} {feature._next_backlog_index}", status, priority, owner)
    feature._backlog_items.append(item)
    feature._refresh_backlog_view()


def clear_backlog_cache(feature: SystemsFeature) -> None:
    feature._backlog_cache.invalidate_all()
    feature._refresh_backlog_labels()


__all__ = [
    "add_backlog_item",
    "build_data_panel",
    "cache_payload_for_backlog_item",
    "clear_backlog_cache",
    "on_backlog_filter_changed",
    "on_backlog_selected",
    "on_backlog_view_refreshed",
    "project_backlog_item",
    "refresh_backlog_labels",
    "refresh_backlog_view",
    "selected_backlog_filter",
]
