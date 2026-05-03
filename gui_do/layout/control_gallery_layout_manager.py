"""Reusable grouped-gallery layout behaviors for control showcase style screens."""

from __future__ import annotations

from pygame import Rect

from .cell_caret_layout import CellCaretLayout


class ControlGalleryLayoutManager:
    """Apply grouped and grid relayout rules for mixed control galleries."""

    def __init__(self, *, inner_gap: int, label_height: int, label_gap: int) -> None:
        self.inner_gap = int(inner_gap)
        self.label_height = int(label_height)
        self.label_gap = int(label_gap)

    def relayout_basics(self, bounds: Rect, items: list, *, ensure_aux_label) -> None:
        items_by_name = {str(item.name): item for item in items}
        col_gap = 8
        row_gap = 8

        arrow_names = ["arrow_up", "arrow_down", "arrow_left", "arrow_right"]
        horizontal_names = ["horizontal_scrollbar", "horizontal_slider"]
        vertical_names = ["vertical_scrollbar", "vertical_slider"]
        button_names = ["button", "button_2", "button_3"]
        toggle_names = ["toggle", "toggle_2", "toggle_3"]
        group_names = sorted(
            [str(item.name) for item in items if str(item.name).startswith("button_group_")],
            key=lambda name: (
                name.split("_")[-1][0] if name.split("_")[-1] else "",
                int(name.split("_")[-1][1:]) if name.split("_")[-1][1:].isdigit() else 0,
            ),
        )
        special_names = set(arrow_names + horizontal_names + vertical_names + button_names + toggle_names + group_names)

        top_cols = 3
        top_cell_w = max(140, (bounds.width - (col_gap * (top_cols - 1))) // top_cols)
        top_y = bounds.top

        arrow_x = bounds.left
        arrow_side = max(24, min(30, (top_cell_w - col_gap) // 2))
        arrow_grid_w = (arrow_side * 2) + col_gap
        arrow_start_x = arrow_x + max(0, (top_cell_w - arrow_grid_w) // 2)
        arrow_positions = {
            "arrow_up": (arrow_start_x, top_y),
            "arrow_down": (arrow_start_x + arrow_side + col_gap, top_y),
            "arrow_left": (arrow_start_x, top_y + arrow_side + row_gap),
            "arrow_right": (arrow_start_x + arrow_side + col_gap, top_y + arrow_side + row_gap),
        }
        for name in arrow_names:
            placed = items_by_name.get(name)
            if placed is None:
                continue
            x, y = arrow_positions[name]
            placed.control.set_rect(Rect(x, y, arrow_side, arrow_side))
            if placed.label is not None:
                placed.label.visible = False
                placed.label.enabled = False

        top_block_h = (arrow_side * 2) + row_gap
        section_y = top_y + top_block_h + row_gap

        grouped_families: list[tuple[str, list]] = []
        button_family = [items_by_name[name] for name in button_names if name in items_by_name]
        if button_family:
            grouped_families.append(("Buttons", button_family))
        toggle_family = [items_by_name[name] for name in toggle_names if name in items_by_name]
        if toggle_family:
            grouped_families.append(("Toggles", toggle_family))

        group_families: list[tuple[str, list]] = []
        for family_key in ("a", "b", "c"):
            family_items = [
                items_by_name[name]
                for name in group_names
                if name in items_by_name and name.split("_")[-1].startswith(family_key)
            ]
            if family_items:
                group_families.append((f"Group {family_key.upper()}", family_items))

        if grouped_families:
            group_bounds = Rect(bounds.left, section_y, bounds.width, max(1, bounds.height - (section_y - bounds.top)))
            section_y = self.relayout_basics_group_cells(group_bounds, grouped_families, col_count=max(1, len(grouped_families)))

        if group_families:
            group_bounds = Rect(bounds.left, section_y, bounds.width, max(1, bounds.height - (section_y - bounds.top)))
            section_y = self.relayout_basics_group_cells(group_bounds, group_families, col_count=3)

        scroll_section_h = 184
        flow_bounds = Rect(bounds.left, section_y, bounds.width, max(1, bounds.height - (section_y - bounds.top) - scroll_section_h - row_gap))

        remaining = [item for item in items if str(item.name) not in special_names]
        bottom_y = section_y
        if remaining:
            bottom_y = self.relayout_grid_items("basics", flow_bounds, remaining)

        scroll_bounds = Rect(bounds.left, bottom_y, bounds.width, scroll_section_h)
        self.relayout_basics_scroll_cells(
            scroll_bounds,
            items_by_name,
            horizontal_names,
            vertical_names,
            ensure_aux_label=ensure_aux_label,
        )

    def relayout_basics_scroll_cells(
        self,
        bounds: Rect,
        items_by_name: dict,
        horizontal_names: list[str],
        vertical_names: list[str],
        *,
        ensure_aux_label,
    ) -> None:
        col_gap = 8
        row_gap = 8
        label_h = 16
        label_gap = 2
        columns = CellCaretLayout.split_columns(
            bounds,
            count=2,
            gap=col_gap,
            min_width=180,
            align="center",
        )
        left_col, right_col = columns[0], columns[1]
        cell_w = left_col.width
        horiz_x = left_col.left
        vert_x = right_col.left
        top_y = bounds.top

        horiz_control_h = 24
        horiz_slot_h = label_h + label_gap + horiz_control_h
        for idx, name in enumerate(horizontal_names):
            placed = items_by_name.get(name)
            if placed is None:
                continue
            y = top_y + idx * (horiz_slot_h + row_gap)
            if placed.label is not None:
                placed.label.set_rect(Rect(horiz_x, y, cell_w, label_h))
                placed.label.visible = True
                placed.label.enabled = True
                control_y = y + label_h + label_gap
            else:
                control_y = y
            placed.control.set_rect(Rect(horiz_x, control_y, cell_w, horiz_control_h))

        vert_bar_w = 22
        vert_bar_h = 146
        label_w = max(54, (cell_w // 2) - 24)
        inner_gap = 4
        per_control_w = vert_bar_w + 6 + label_w
        content_w = (per_control_w * 2) + inner_gap
        vert_start_x = vert_x + max(0, (cell_w - content_w) // 2)
        for idx, name in enumerate(vertical_names):
            placed = items_by_name.get(name)
            if placed is None:
                continue
            x = vert_start_x + idx * (per_control_w + inner_gap)
            control_y = top_y + 12
            placed.control.set_rect(Rect(x, control_y, vert_bar_w, vert_bar_h))
            label = placed.label
            if label is None:
                label = ensure_aux_label(name)
            if label is not None:
                label_x = x + vert_bar_w + 6
                label_y = control_y + (vert_bar_h - label_h) // 2
                label.set_rect(Rect(label_x, label_y, label_w, label_h))
                label.visible = True
                label.enabled = True

    def relayout_basics_group_cells(self, bounds: Rect, families: list[tuple[str, list]], *, col_count: int) -> int:
        col_gap = 8
        row_gap = 8
        label_h = 16
        label_gap = 2
        col_count = max(1, int(col_count))
        y = bounds.top

        for _title, placed_items in families:
            for placed in placed_items:
                if placed.label is not None:
                    placed.label.visible = False
                    placed.label.enabled = False

        for start in range(0, len(families), col_count):
            row_families = families[start:start + col_count]
            row_bounds = Rect(bounds.left, y, bounds.width, max(1, bounds.height - (y - bounds.top)))
            row_cols = CellCaretLayout.split_columns(
                row_bounds,
                count=max(1, len(row_families)),
                gap=col_gap,
                min_width=140,
            )
            row_h = 0
            family_metrics: list[tuple[str, list, int]] = []
            for title, placed_items in row_families:
                col_w = row_cols[len(family_metrics)].width
                control_heights = [self.target_control_size("basics", placed, col_w)[1] for placed in placed_items]
                family_h = label_h + label_gap + sum(control_heights) + (max(0, len(control_heights) - 1) * 4)
                family_metrics.append((title, placed_items, family_h))
                row_h = max(row_h, family_h)

            for col, (title, placed_items, _family_h) in enumerate(family_metrics):
                col_rect = row_cols[col]
                x = col_rect.left
                col_w = col_rect.width
                header_label = placed_items[0].label if placed_items and placed_items[0].label is not None else None
                if header_label is not None:
                    header_label.text = title
                    header_label.set_rect(Rect(x, y, col_w, label_h))
                    header_label.visible = True
                    header_label.enabled = True

                control_y = y + label_h + label_gap
                for placed in placed_items:
                    target_w, control_h = self.target_control_size("basics", placed, col_w)
                    control_x = x + max(0, (col_w - target_w) // 2)
                    placed.control.set_rect(Rect(control_x, control_y, target_w, control_h))
                    control_y += control_h + 4
            y += row_h + row_gap

        return y

    def relayout_grid_items(self, category_key: str, bounds: Rect, items: list) -> int:
        is_basics = category_key == "basics"
        col_gap = 6 if is_basics else max(4, self.inner_gap * 2)
        row_gap = 6 if is_basics else max(6, self.inner_gap * 2)
        label_h = 16 if is_basics else self.label_height
        label_gap = 2 if is_basics else self.label_gap
        min_col_w = 160 if is_basics else 220
        max_cols = 5 if is_basics else 4

        if is_basics:
            items.sort(key=lambda p: (int(p.row_index), int(p.column_index), str(p.name)))
        fit_cols = max(1, (bounds.width + col_gap) // (min_col_w + col_gap))
        col_count = max(1, min(max_cols, fit_cols))

        y = bounds.top
        for start in range(0, len(items), col_count):
            row_items = items[start:start + col_count]
            row_bounds = Rect(bounds.left, y, bounds.width, max(1, bounds.height - (y - bounds.top)))
            row_cols = CellCaretLayout.split_columns(
                row_bounds,
                count=max(1, len(row_items)),
                gap=col_gap,
                min_width=140,
            )
            slot_heights = []
            for idx, item in enumerate(row_items):
                col_w = row_cols[idx].width
                _, ch = self.target_control_size(category_key, item, col_w)
                slot_heights.append(ch + (label_h + label_gap if item.label is not None else 0))
            row_h = max(slot_heights) if slot_heights else 0

            for col, item in enumerate(row_items):
                col_rect = row_cols[col]
                x = col_rect.left
                col_w = col_rect.width
                cw, ch = self.target_control_size(category_key, item, col_w)
                cx = x + max(0, (col_w - cw) // 2)
                if item.label is not None:
                    item.label.set_rect(Rect(x, y, col_w, label_h))
                    item.label.visible = True
                    item.label.enabled = True
                    item.control.set_rect(Rect(cx, y + label_h + label_gap, cw, ch))
                else:
                    item.control.set_rect(Rect(cx, y, cw, ch))
            y += row_h + row_gap

        return y

    @staticmethod
    def target_control_size(category_key: str, placed, column_width: int) -> tuple[int, int]:
        control = placed.control
        name = str(getattr(placed, "name", ""))
        current_h = max(1, int(control.rect.height))

        if category_key != "basics":
            return (column_width, current_h)

        compact_w = max(140, column_width)

        if name.startswith("arrow_"):
            side = max(24, min(column_width, 30))
            return (side, side)
        if name in {"vertical_scrollbar", "vertical_slider"}:
            width = max(18, min(column_width, 24))
            return (width, 84)
        if name in {"horizontal_scrollbar", "horizontal_slider"}:
            return (compact_w, 24)
        if name in {"text_input", "dropdown", "spinner", "range_slider", "split_button", "date_picker", "time_picker"}:
            return (compact_w, 32)
        if name in {"button", "button_2", "button_3", "toggle", "toggle_2", "toggle_3"} or name.startswith("button_group_"):
            return (compact_w, 30)
        if name == "text_area":
            return (compact_w, 96)
        if name == "data_grid":
            return (compact_w, 132)
        if name == "tab":
            width = max(180, min(column_width, 230))
            height = max(160, min(current_h if current_h > 0 else 180, 220))
            return (width, height)
        if name == "image":
            side = max(112, min(column_width, 144))
            return (side, side)
        if name == "notification_panel":
            return (compact_w, 168)

        return (compact_w, max(min(current_h, 144), 36))
