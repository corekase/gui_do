"""Controls showcase part with columnar block layout for mirrored enabled/disabled control presentation."""

from __future__ import annotations

import pygame
from pathlib import Path
from pygame import Rect

from shared.part_lifecycle import Part


class ControlsShowcasePart(Part):
    """Render all core controls in columnar blocks with mirrored enabled/disabled halves."""

    HOST_REQUIREMENTS = {
        "build": ("app", "control_showcase_root"),
    }

    # Section layout constants
    SECTION_TITLE_TEXT_ENABLED = "Enabled Controls"
    SECTION_TITLE_TEXT_DISABLED = "Disabled Controls"
    PART_MARGIN_X = 24
    PART_MARGIN_TOP = 144
    PART_MARGIN_BOTTOM = 76
    OUTER_PADDING_X = 16
    OUTER_PADDING_Y = 16
    SECTION_SPLIT_GAP = 12
    SECTION_TITLE_HEIGHT = 22
    SECTION_TITLE_GAP = 10

    # Block layout constants (parametric - adjustable for layout tuning)
    BLOCK_PADDING_X = 12
    BLOCK_PADDING_Y = 10
    BLOCK_INTERNAL_SPACING = 8
    BLOCK_LABEL_HEIGHT = 14
    BLOCK_LABEL_GAP = 6
    COLUMN_GAP = 16
    CONTROL_GRID_GAP = 6
    # Control constants
    LABEL_ALIGN = "center"
    ARROW_UP_DEGREES = 90
    ARROW_DOWN_DEGREES = 270
    ARROW_LEFT_DEGREES = 180
    ARROW_RIGHT_DEGREES = 0
    FRAME_BORDER_WIDTH = 2
    IMAGE_PATH = "data/images/realize.png"
    IMAGE_BLOCK_HEIGHT_FALLBACK = 120

    SLIDER_MINIMUM = 0.0
    SLIDER_MAXIMUM = 100.0
    SLIDER_DEFAULT_VALUE = 0.0

    SCROLLBAR_CONTENT_SIZE = 1000
    SCROLLBAR_VIEWPORT_SIZE = 240
    SCROLLBAR_DEFAULT_OFFSET = 0
    SCROLLBAR_STEP = 24

    PANEL_DRAW_BACKGROUND = True

    # Block definitions - define structure of blocks
    BLOCK_DEFINITIONS = [
        "arrow_cluster",
        "button_groups",
        "buttons_and_indicators",
        "horizontal_sliders",
        "vertical_sliders",
        "image_block",
        "canvas_panel_block",
    ]

    def __init__(self, rect: Rect | None = None) -> None:
        super().__init__("controls_showcase", scene_name="control_showcase")
        self.rect = Rect(rect) if rect is not None else Rect(0, 0, 0, 0)
        self.section_top_rect = Rect(0, 0, 0, 0)
        self.section_bottom_rect = Rect(0, 0, 0, 0)
        self.enabled_controls = []
        self.disabled_controls = []
        self.enabled_control_labels = []
        self.disabled_control_labels = []
        self.enabled_blocks = []
        self.disabled_blocks = []
        self.enabled_title = None
        self.disabled_title = None
        self._image_natural_size: tuple[int, int] | None = None

    def build(self, host) -> None:
        ui = host.app.read_part_ui_types()
        if self.rect.width <= 0 or self.rect.height <= 0:
            self.rect = self._default_part_rect(host)
        self._load_image_natural_size()
        self.section_top_rect, self.section_bottom_rect = self._split_rect(self.rect)

        # Create section titles
        self.enabled_title = host.control_showcase_root.add(
            ui.label_control_cls(
                "controls_showcase_enabled_title",
                self._title_rect(self.section_top_rect),
                self.SECTION_TITLE_TEXT_ENABLED,
                align=self.LABEL_ALIGN,
            )
        )
        self.enabled_title.font_size = 22

        self.disabled_title = host.control_showcase_root.add(
            ui.label_control_cls(
                "controls_showcase_disabled_title",
                self._title_rect(self.section_bottom_rect),
                self.SECTION_TITLE_TEXT_DISABLED,
                align=self.LABEL_ALIGN,
            )
        )
        self.disabled_title.font_size = 22

        # Build enabled blocks
        self.enabled_controls = []
        self.enabled_control_labels = []
        self.enabled_blocks = []
        content_rect_top = self._content_rect(self.section_top_rect)
        block_rects_top = self._calculate_block_layout(content_rect_top)
        for block_name, block_rect in zip(self.BLOCK_DEFINITIONS, block_rects_top):
            controls, labels = self._build_block(host, ui, block_name, block_rect, enabled=True)
            self.enabled_controls.extend(controls)
            self.enabled_control_labels.extend(labels)
            self.enabled_blocks.append({"name": block_name, "controls": controls, "labels": labels})
            for control in controls:
                host.control_showcase_root.add(control)
            for label in labels:
                host.control_showcase_root.add(label)

        # Build disabled blocks (controls disabled, labels enabled)
        self.disabled_controls = []
        self.disabled_control_labels = []
        self.disabled_blocks = []
        content_rect_bottom = self._content_rect(self.section_bottom_rect)
        block_rects_bottom = self._calculate_block_layout(content_rect_bottom)
        for block_name, block_rect in zip(self.BLOCK_DEFINITIONS, block_rects_bottom):
            controls, labels = self._build_block(host, ui, block_name, block_rect, enabled=False)
            self.disabled_controls.extend(controls)
            self.disabled_control_labels.extend(labels)
            self.disabled_blocks.append({"name": block_name, "controls": controls, "labels": labels})
            for control in controls:
                control.enabled = False
                host.control_showcase_root.add(control)
            for label in labels:
                # Labels in disabled section remain enabled
                host.control_showcase_root.add(label)

    def _default_part_rect(self, host) -> Rect:
        """Compute the showcase rect from host screen bounds for encapsulated layout."""
        screen_rect = getattr(host, "screen_rect", None)
        if screen_rect is None:
            screen = getattr(host, "screen", None)
            if screen is not None:
                screen_rect = screen.get_rect()
        if screen_rect is None:
            # Final fallback keeps build resilient in tests with minimal host stubs.
            return Rect(0, 0, 1, 1)

        left = int(self.PART_MARGIN_X)
        top = int(self.PART_MARGIN_TOP)
        width = max(1, int(screen_rect.width - (self.PART_MARGIN_X * 2)))
        height = max(1, int(screen_rect.height - self.PART_MARGIN_TOP - self.PART_MARGIN_BOTTOM))
        return Rect(left, top, width, height)

    def _split_rect(self, source: Rect) -> tuple[Rect, Rect]:
        """Split rect into top (enabled) and bottom (disabled) sections."""
        inset = Rect(source)
        inset.x += self.OUTER_PADDING_X
        inset.y += self.OUTER_PADDING_Y
        inset.width = max(1, inset.width - (self.OUTER_PADDING_X * 2))
        inset.height = max(1, inset.height - (self.OUTER_PADDING_Y * 2))

        top_height = max(1, (inset.height - self.SECTION_SPLIT_GAP) // 2)
        bottom_height = max(1, inset.height - self.SECTION_SPLIT_GAP - top_height)

        top = Rect(inset.left, inset.top, inset.width, top_height)
        bottom = Rect(inset.left, top.bottom + self.SECTION_SPLIT_GAP, inset.width, bottom_height)
        return top, bottom

    def _title_rect(self, section_rect: Rect) -> Rect:
        """Get rect for section title."""
        return Rect(
            section_rect.left,
            section_rect.top,
            section_rect.width,
            self.SECTION_TITLE_HEIGHT,
        )

    def _content_rect(self, section_rect: Rect) -> Rect:
        """Get rect for content area below title."""
        content_top = section_rect.top + self.SECTION_TITLE_HEIGHT + self.SECTION_TITLE_GAP
        content_height = max(1, section_rect.height - self.SECTION_TITLE_HEIGHT - self.SECTION_TITLE_GAP)
        return Rect(section_rect.left, content_top, section_rect.width, content_height)

    def _calculate_block_layout(self, content_rect: Rect) -> list[Rect]:
        """
        Calculate block positions for given content area.
        Returns list of block rects in column-first order.
        Image block occupies the last column exclusively, centered vertically.
        """
        block_heights_map = {
            "arrow_cluster": 70,
            "button_groups": 84,
            "buttons_and_indicators": 100,
            "horizontal_sliders": 100,
            "vertical_sliders": 100,
            "canvas_panel_block": 110,
        }

        available_width = max(1, content_rect.width)

        # Determine column count based on content
        num_columns = 2
        if available_width > 900:
            num_columns = 3
        elif available_width < 600:
            num_columns = 1

        column_width = max(1, (available_width - (num_columns - 1) * self.COLUMN_GAP) // num_columns)

        block_rects = {}

        if num_columns > 1:
            # Layout has three regions: (num_columns-1) greedy cols, 1 vertical_sliders col,
            # and 1 image col.  vertical_sliders width is derived so each vertical control can
            # sit side-by-side with width equal to horizontal control height (track_size).
            h_track_size = max(1, (block_heights_map["horizontal_sliders"] - self.BLOCK_INTERNAL_SPACING) // 2)
            # Column width accounts for: 10px left padding + track_size + 10px gap + track_size
            v_col_width = max(56, 10 + 2 * h_track_size + 10)

            # Recalculate column_width to fit all regions without overlap:
            #   num_columns * column_width + v_col_width + num_columns * COLUMN_GAP = available_width
            column_width = max(1, (available_width - v_col_width - num_columns * self.COLUMN_GAP) // num_columns)
            image_col = num_columns - 1
            other_cols = list(range(image_col))

            # X-positions for the two dedicated columns.
            v_col_x = content_rect.left + (num_columns - 1) * (column_width + self.COLUMN_GAP)
            image_col_x = v_col_x + v_col_width + self.COLUMN_GAP

            # Greedy-assign non-special blocks to greedy columns by lowest height.
            column_heights = [0] * num_columns
            for block_name in self.BLOCK_DEFINITIONS:
                if block_name in ("image_block", "vertical_sliders"):
                    continue
                if block_name == "arrow_cluster":
                    base_height = max(1, column_width // 8)
                else:
                    base_height = block_heights_map.get(block_name, 80)
                block_height = base_height + self.BLOCK_LABEL_HEIGHT + self.BLOCK_LABEL_GAP
                min_col = min(other_cols, key=lambda i: column_heights[i])
                col_x = content_rect.left + min_col * (column_width + self.COLUMN_GAP)
                col_y = content_rect.top + column_heights[min_col]
                block_rects[block_name] = Rect(col_x, col_y, column_width, block_height)
                column_heights[min_col] += block_height + self.BLOCK_INTERNAL_SPACING

            # Place vertical_sliders in its dedicated column spanning full section content height.
            # Its internal content area (below label) therefore uses the entire remaining column height.
            block_rects["vertical_sliders"] = Rect(
                v_col_x,
                content_rect.top,
                v_col_width,
                content_rect.height,
            )

            # Place image_block centered in its reserved column, constrained to section height.
            max_image_content_h = max(1, content_rect.height - self.BLOCK_LABEL_HEIGHT - self.BLOCK_LABEL_GAP)
            img_w, img_h = self._image_block_size_for_constraints(column_width, max_image_content_h)
            image_block_total_height = self.BLOCK_LABEL_HEIGHT + self.BLOCK_LABEL_GAP + img_h
            h_offset = (column_width - img_w) // 2  # center horizontally in column
            center_offset = max(0, (content_rect.height - image_block_total_height) // 2)
            block_rects["image_block"] = Rect(
                image_col_x + h_offset,
                content_rect.top + center_offset,
                img_w,
                image_block_total_height,
            )
        else:
            # Single column: stack all blocks including image_block
            col_y = content_rect.top
            for block_name in self.BLOCK_DEFINITIONS:
                base_height = (
                    self._image_block_size_for_constraints(column_width, content_rect.height)[1]
                    if block_name == "image_block"
                    else max(1, column_width // 8)
                    if block_name == "arrow_cluster"
                    else block_heights_map.get(block_name, self.IMAGE_BLOCK_HEIGHT_FALLBACK)
                )
                block_height = base_height + self.BLOCK_LABEL_HEIGHT + self.BLOCK_LABEL_GAP
                block_rects[block_name] = Rect(content_rect.left, col_y, column_width, block_height)
                col_y += block_height + self.BLOCK_INTERNAL_SPACING

        # Return rects in same order as BLOCK_DEFINITIONS
        return [block_rects[name] for name in self.BLOCK_DEFINITIONS]

    def _build_block(self, host, ui, block_name: str, block_rect: Rect, enabled: bool) -> tuple:
        """
        Build a single block of controls.
        Returns: (controls_list, labels_list)
        """
        controls = []
        labels = []

        # Image block uses full column width with a centered label; others use padding
        # vertical_sliders shares image_block's no-padding, centered-label treatment.
        # canvas_panel_block has no block label (uses full height for content)
        is_image_block = block_name in ("image_block", "vertical_sliders")
        has_no_block_label = block_name == "canvas_panel_block"

        # Create block label (always enabled, even in disabled section)
        if not has_no_block_label:
            if block_name == "vertical_sliders":
                # Center label above just the slider+scrollbar pair, not the full column
                v_left_pad = 10
                v_gap = 10
                v_track_size = (100 - self.BLOCK_INTERNAL_SPACING) // 2
                v_pair_width = 2 * v_track_size + v_gap
                label_rect = Rect(block_rect.left + v_left_pad, block_rect.top, v_pair_width, self.BLOCK_LABEL_HEIGHT)
                label_align = "center"
            elif is_image_block:
                label_rect = Rect(block_rect.left, block_rect.top, block_rect.width, self.BLOCK_LABEL_HEIGHT)
                label_align = "center"
            else:
                label_rect = Rect(
                    block_rect.left + self.BLOCK_PADDING_X,
                    block_rect.top,
                    block_rect.width - 2 * self.BLOCK_PADDING_X,
                    self.BLOCK_LABEL_HEIGHT,
                )
                label_align = "left"
            block_label = ui.label_control_cls(
                f"controls_showcase_block_label_{block_name}",
                label_rect,
                self._format_block_name(block_name),
                align=label_align,
            )
            labels.append(block_label)

        # Content rect for controls (below label, or full block if no label)
        if has_no_block_label:
            content_top = block_rect.top
            content_height = block_rect.height
        else:
            content_top = block_rect.top + self.BLOCK_LABEL_HEIGHT + self.BLOCK_LABEL_GAP
            content_height = max(1, block_rect.height - self.BLOCK_LABEL_HEIGHT - self.BLOCK_LABEL_GAP)
        if is_image_block:
            # Image spans full column width with no horizontal padding
            content_rect = Rect(block_rect.left, content_top, block_rect.width, content_height)
        else:
            content_rect = Rect(
                block_rect.left + self.BLOCK_PADDING_X,
                content_top,
                block_rect.width - 2 * self.BLOCK_PADDING_X,
                content_height,
            )

        # Build block-specific controls
        if block_name == "arrow_cluster":
            controls = self._build_arrow_cluster(ui, content_rect, enabled)
        elif block_name == "button_groups":
            controls = self._build_button_groups(ui, content_rect, enabled)
        elif block_name == "buttons_and_indicators":
            controls = self._build_buttons_and_indicators(ui, content_rect, enabled)
        elif block_name == "horizontal_sliders":
            controls = self._build_horizontal_sliders(ui, content_rect, enabled)
        elif block_name == "vertical_sliders":
            controls = self._build_vertical_sliders(ui, content_rect, enabled)
        elif block_name == "image_block":
            controls = self._build_image_block(ui, content_rect, enabled)
        elif block_name == "canvas_panel_block":
            controls = self._build_canvas_panel_block(ui, content_rect, enabled)

        return controls, labels

    def _build_arrow_cluster(self, ui, content_rect: Rect, enabled: bool) -> list:
        """Build a 2x2 arrow grid in the left-half square of the column."""
        column_width = content_rect.width + (2 * self.BLOCK_PADDING_X)
        grid_size = max(2, column_width // 8)
        cell = max(1, grid_size // 2)

        grid_left = content_rect.left
        grid_top = content_rect.top

        # Order: top-left, top-right, bottom-left, bottom-right
        specs = [
            ("up", self.ARROW_UP_DEGREES, Rect(grid_left, grid_top, cell, cell)),
            ("down", self.ARROW_DOWN_DEGREES, Rect(grid_left + cell, grid_top, grid_size - cell, cell)),
            ("left", self.ARROW_LEFT_DEGREES, Rect(grid_left, grid_top + cell, cell, grid_size - cell)),
            (
                "right",
                self.ARROW_RIGHT_DEGREES,
                Rect(grid_left + cell, grid_top + cell, grid_size - cell, grid_size - cell),
            ),
        ]

        arrows = []
        for name, direction, rect in specs:
            arrows.append(
                ui.arrow_box_control_cls(
                    f"arrow_{name}_{'enabled' if enabled else 'disabled'}",
                    rect,
                    direction,
                )
            )
        return arrows

    def _build_button_groups(self, ui, content_rect: Rect, enabled: bool) -> list:
        """Build a 3x3 grid of button group controls: 3 columns (independent groups),
        3 rows (buttons per group). Labels denote group letter and position: A1-A3, B1-B3, C1-C3.
        The first button in each group is auto-armed by on_mount."""
        section = "enabled" if enabled else "disabled"
        num_groups = 3
        num_rows = 3
        gap = self.CONTROL_GRID_GAP
        col_width = max(1, (content_rect.width - (num_groups - 1) * gap) // num_groups)
        row_height = max(1, (content_rect.height - (num_rows - 1) * gap) // num_rows)
        group_letters = ["A", "B", "C"]
        controls = []
        for g, letter in enumerate(group_letters):
            group_name = f"controls_showcase_{letter.lower()}_{section}"
            col_x = content_rect.left + g * (col_width + gap)
            for r in range(num_rows):
                row_y = content_rect.top + r * (row_height + gap)
                label = f"{letter}{r + 1}"
                btn = ui.button_group_control_cls(
                    f"btn_grp_{letter.lower()}{r + 1}_{section}",
                    Rect(col_x, row_y, col_width, row_height),
                    group_name,
                    label,
                    selected=False,
                    style="box",
                )
                controls.append(btn)
        return controls

    def _build_buttons_and_indicators(self, ui, content_rect: Rect, enabled: bool) -> list:
        """Build button and toggle."""
        controls = []

        # Divide content into 2 sections
        item_height = (content_rect.height - self.BLOCK_INTERNAL_SPACING) // 2

        # Button
        button_rect = Rect(content_rect.left, content_rect.top, content_rect.width, item_height)
        button = ui.button_control_cls(
            f"button_{'enabled' if enabled else 'disabled'}",
            button_rect,
            "Button",
        )
        controls.append(button)

        # Toggle
        toggle_rect = Rect(
            content_rect.left,
            content_rect.top + item_height + self.BLOCK_INTERNAL_SPACING,
            content_rect.width,
            item_height,
        )
        toggle = ui.toggle_control_cls(
            f"toggle_{'enabled' if enabled else 'disabled'}",
            toggle_rect,
            "On",
            "Off",
            pushed=False,
            style="round",
        )
        controls.append(toggle)

        return controls

    def _build_horizontal_sliders(self, ui, content_rect: Rect, enabled: bool) -> list:
        """Build horizontal slider and scrollbar with fixed 10px left/right padding, centered.

        Track size uses base block height (100px) for consistency with v_col_width calculation
        in _calculate_block_layout. This avoids the trap where content_rect.height has already
        subtracted label height, leading to dimension mismatches.
        """
        section = "enabled" if enabled else "disabled"
        # Fixed 10px padding on left and right, centered within content_rect
        h_pad = 10
        h_x = content_rect.left + h_pad
        h_width = max(1, content_rect.width - 2 * h_pad)

        # Use base block height (100px) for track_size to match h_track_size calculation
        # in _calculate_block_layout: (100 - 8) // 2 = 46px per track.
        base_block_height = 100
        track_size = (base_block_height - self.BLOCK_INTERNAL_SPACING) // 2

        slider = ui.slider_control_cls(
            f"slider_{section}",
            Rect(h_x, content_rect.top, h_width, track_size),
            ui.layout_axis_cls.HORIZONTAL,
            self.SLIDER_MINIMUM,
            self.SLIDER_MAXIMUM,
            self.SLIDER_DEFAULT_VALUE,
        )

        scrollbar = ui.scrollbar_control_cls(
            f"scrollbar_{section}",
            Rect(h_x, content_rect.top + track_size + self.BLOCK_INTERNAL_SPACING, h_width, track_size),
            ui.layout_axis_cls.HORIZONTAL,
            self.SCROLLBAR_CONTENT_SIZE,
            self.SCROLLBAR_VIEWPORT_SIZE,
            offset=self.SCROLLBAR_DEFAULT_OFFSET,
            step=self.SCROLLBAR_STEP,
        )

        return [slider, scrollbar]

    def _build_vertical_sliders(self, ui, content_rect: Rect, enabled: bool) -> list:
        """Build vertical slider and scrollbar left-aligned within the dedicated thin column,
        with 10px left padding and 10px spacing between controls.
        track_size matches horizontal_sliders' track_size since both blocks use the same base height."""
        section = "enabled" if enabled else "disabled"
        # Compute track_size from the standard block height (100px), not from content_rect.height
        # which spans the full column for vertical_sliders. This ensures consistent proportions
        # with the horizontal sliders: (100 - 8) // 2 = 46px per track.
        base_block_height = 100
        track_size = (base_block_height - self.BLOCK_INTERNAL_SPACING) // 2
        left_pad = 10
        gap = 10
        pair_x = content_rect.left + left_pad

        v_slider = ui.slider_control_cls(
            f"v_slider_{section}",
            Rect(pair_x, content_rect.top, track_size, content_rect.height),
            ui.layout_axis_cls.VERTICAL,
            self.SLIDER_MINIMUM,
            self.SLIDER_MAXIMUM,
            self.SLIDER_DEFAULT_VALUE,
        )

        v_scrollbar = ui.scrollbar_control_cls(
            f"v_scrollbar_{section}",
            Rect(pair_x + track_size + gap, content_rect.top, track_size, content_rect.height),
            ui.layout_axis_cls.VERTICAL,
            self.SCROLLBAR_CONTENT_SIZE,
            self.SCROLLBAR_VIEWPORT_SIZE,
            offset=self.SCROLLBAR_DEFAULT_OFFSET,
            step=self.SCROLLBAR_STEP,
        )

        return [v_slider, v_scrollbar]

    def _build_image_block(self, ui, content_rect: Rect, enabled: bool) -> list:
        """Build image control."""
        image = ui.image_control_cls(
            f"image_{'enabled' if enabled else 'disabled'}",
            content_rect,
            self.IMAGE_PATH,
            scale=True,
        )
        return [image]

    def _build_canvas_panel_block(self, ui, content_rect: Rect, enabled: bool) -> list:
        """Build canvas and panel side-by-side, each with its own label positioned above.

        Labels are left-justified to the control's left position and placed just above
        with BLOCK_LABEL_GAP spacing.
        """
        controls = []

        # Allocate space for labels above each control
        label_height = self.BLOCK_LABEL_HEIGHT
        label_gap = self.BLOCK_LABEL_GAP
        available_height = content_rect.height - label_height - label_gap

        # Divide content into 2 sections side-by-side
        item_width = (content_rect.width - self.CONTROL_GRID_GAP) // 2

        # Canvas: label + gap + control
        canvas_label_rect = Rect(content_rect.left, content_rect.top, item_width, label_height)
        canvas_rect = Rect(
            content_rect.left,
            content_rect.top + label_height + label_gap,
            item_width,
            available_height,
        )
        canvas_label = ui.label_control_cls(
            f"canvas_label_{'enabled' if enabled else 'disabled'}",
            canvas_label_rect,
            "Canvas",
            align="left",
        )
        canvas = ui.canvas_control_cls(
            f"canvas_{'enabled' if enabled else 'disabled'}",
            canvas_rect,
            max_events=64,
        )
        controls.append(canvas_label)
        controls.append(canvas)

        # Panel: label + gap + control
        panel_left = content_rect.left + item_width + self.CONTROL_GRID_GAP
        panel_label_rect = Rect(panel_left, content_rect.top, item_width, label_height)
        panel_rect = Rect(
            panel_left,
            content_rect.top + label_height + label_gap,
            item_width,
            available_height,
        )
        panel_label = ui.label_control_cls(
            f"panel_label_{'enabled' if enabled else 'disabled'}",
            panel_label_rect,
            "Panel",
            align="left",
        )
        panel = ui.panel_control_cls(
            f"panel_{'enabled' if enabled else 'disabled'}",
            panel_rect,
            draw_background=self.PANEL_DRAW_BACKGROUND,
        )
        controls.append(panel_label)
        controls.append(panel)

        return controls

    def _load_image_natural_size(self) -> None:
        """Load image to determine its natural pixel dimensions."""
        abs_path = Path(__file__).parent.parent / self.IMAGE_PATH
        try:
            surf = pygame.image.load(str(abs_path))
            self._image_natural_size = surf.get_size()
        except Exception:
            self._image_natural_size = None

    def _image_block_size_for_constraints(self, max_width: int, max_height: int) -> tuple[int, int]:
        """Return (width, height) fitting within max_width x max_height while preserving aspect ratio."""
        if self._image_natural_size and self._image_natural_size[0] > 0 and self._image_natural_size[1] > 0:
            nat_w, nat_h = self._image_natural_size
            h_for_width = int(max_width * nat_h / nat_w)
            if h_for_width <= max_height:
                return max_width, max(1, h_for_width)
            w_for_height = int(max_height * nat_w / nat_h)
            return max(1, w_for_height), max_height
        fallback = min(max_width, max_height, self.IMAGE_BLOCK_HEIGHT_FALLBACK)
        return fallback, fallback

    @staticmethod
    def _format_block_name(block_name: str) -> str:
        """Format block name for display as Title Case label."""
        # Custom labels for specific blocks
        custom_labels = {
            "buttons_and_indicators": "Button and Toggle Button",
            "horizontal_sliders": "Horizontal Slider and Scrollbar",
            "vertical_sliders": "Vertical",
            "image_block": "Image",
        }
        if block_name in custom_labels:
            return custom_labels[block_name]
        # Default: arrow_cluster -> Arrow Cluster
        return " ".join(piece.capitalize() for piece in block_name.split("_"))
