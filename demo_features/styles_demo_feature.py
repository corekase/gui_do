"""Styles showcase feature part for the control_showcase scene."""

from __future__ import annotations

from pygame import Rect

from gui_do import Feature


class StylesShowcaseFeature(Feature):
    """Build a window showcasing the built-in interactive control styles."""

    HOST_REQUIREMENTS = {
        "build": ("app", "control_showcase_root"),
        "prewarm": ("app",),
    }

    STYLE_NAMES = ("box", "radio", "round", "angle", "check")
    ROW_LABELS = ("Item 1", "Item 2", "Item 3", "Item 4", "Item 5")
    COLUMN_COUNT = 8

    WINDOW_TITLEBAR_HEIGHT = 28

    COLUMN_WIDTH = 90
    COLUMN_GAP = 4
    HEADING_HEIGHT = 24
    CONTROL_HEIGHT = 30
    CONTROL_GAP = 8
    FOOTER_HEIGHT = 22
    PADDING_X = 10
    TOP_PADDING_Y = 0
    BOTTOM_PADDING_Y = TOP_PADDING_Y + 4
    PADDING_Y = TOP_PADDING_Y
    HEADING_GAP = 4
    FOOTER_GAP = 4

    CENTERED_STYLES = ("radio", "check")
    CENTERED_STYLE_WIDTH = 90

    WINDOW_WIDTH = (COLUMN_COUNT * COLUMN_WIDTH) + ((COLUMN_COUNT - 1) * COLUMN_GAP) + (PADDING_X * 2)
    WINDOW_CONTENT_HEIGHT = (
        TOP_PADDING_Y
        + HEADING_HEIGHT
        + HEADING_GAP
        + (len(ROW_LABELS) * CONTROL_HEIGHT)
        + ((len(ROW_LABELS) - 1) * CONTROL_GAP)
        + FOOTER_GAP
        + FOOTER_HEIGHT
        + BOTTOM_PADDING_Y
    )
    WINDOW_HEIGHT = WINDOW_TITLEBAR_HEIGHT + WINDOW_CONTENT_HEIGHT

    def __init__(self) -> None:
        super().__init__("styles_showcase", scene_name="control_showcase")
        self.demo = None
        self.window = None
        self.group_controls = []
        self.button_controls = []
        self.toggle_controls = []
        self.footer_labels = []
        self._group_footer_bindings = []

    def build(self, host) -> None:
        ui = host.app.read_feature_ui_types()
        self.register_font_roles(
            host,
            {
                    "window_title": {"size": 14, "file_path": "demo_features/data/fonts/Gimbot.ttf", "system_name": "arial", "bold": True},
                    "heading": {"size": 18, "file_path": "demo_features/data/fonts/Ubuntu-B.ttf", "system_name": "arial", "bold": True},
                    "control": {"size": 15, "file_path": "demo_features/data/fonts/Ubuntu-B.ttf", "system_name": "arial"},
                    "footer": {"size": 14, "file_path": "demo_features/data/fonts/Ubuntu-B.ttf", "system_name": "arial"},
            },
            scene_name="control_showcase",
        )
        self.build_window(
            host,
            window_control_cls=ui.window_control_cls,
            label_control_cls=ui.label_control_cls,
            button_control_cls=ui.button_control_cls,
            toggle_control_cls=ui.toggle_control_cls,
            button_group_control_cls=ui.button_group_control_cls,
        )

    def build_window(
        self,
        host,
        *,
        window_control_cls,
        label_control_cls,
        button_control_cls,
        toggle_control_cls,
        button_group_control_cls,
    ) -> None:
        self.demo = host
        window_rect = host.app.layout.anchored((self.WINDOW_WIDTH, self.WINDOW_HEIGHT), anchor="top_center", margin=(0, 120), use_rect=True)
        self.window = host.control_showcase_root.add(
            window_control_cls(
                "styles_window",
                window_rect,
                "Styles",
                titlebar_height=28,
                title_font_role=self.font_role("window_title"),
                use_frame_backdrop=True,
            )
        )

        content_rect = self.window.content_rect()
        heading_y = content_rect.top + self.TOP_PADDING_Y
        controls_anchor_y = heading_y + self.HEADING_HEIGHT + self.HEADING_GAP
        footer_y = controls_anchor_y + (len(self.ROW_LABELS) * self.CONTROL_HEIGHT) + ((len(self.ROW_LABELS) - 1) * self.CONTROL_GAP) + self.FOOTER_GAP

        host.app.layout.set_grid_properties(
            anchor=(content_rect.left + self.PADDING_X, controls_anchor_y),
            item_width=self.COLUMN_WIDTH,
            item_height=self.CONTROL_HEIGHT,
            column_spacing=self.COLUMN_GAP,
            row_spacing=self.CONTROL_GAP,
            use_rect=True,
        )

        self.group_controls = []
        self.button_controls = []
        self.toggle_controls = []
        self.footer_labels = []
        self._group_footer_bindings = []
        focus_index = 0

        group_columns = [
            ("box", "Box", ("box",) * 5),
            ("radio", "Radio", ("radio",) * 5),
            ("round", "Round", ("round",) * 5),
            ("angle", "Angle", ("angle",) * 5),
            ("check", "Check", ("check",) * 5),
            ("mixed", "Mixed", self.STYLE_NAMES),
        ]
        button_column_index = len(group_columns)
        toggle_column_index = button_column_index + 1

        for column_index, (slug, heading_text, style_sequence) in enumerate(group_columns):
            heading = host.app.style_label(
                self.window.add(label_control_cls(f"styles_heading_{slug}", Rect(content_rect.left + self.PADDING_X + (column_index * (self.COLUMN_WIDTH + self.COLUMN_GAP)), heading_y, self.COLUMN_WIDTH, self.HEADING_HEIGHT), heading_text, align="center")),
                size=18,
                role=self.font_role("heading"),
            )
            footer = host.app.style_label(
                self.window.add(
                    label_control_cls(
                        f"styles_footer_{slug}",
                        Rect(
                            content_rect.left + self.PADDING_X + (column_index * (self.COLUMN_WIDTH + self.COLUMN_GAP)),
                            footer_y,
                            self.COLUMN_WIDTH,
                            self.FOOTER_HEIGHT,
                        ),
                        self._format_group_info(column_index, 0),
                        align="center",
                    )
                ),
                size=14,
                role=self.font_role("footer"),
            )
            self.footer_labels.append(footer)
            group_name = f"styles_group_{column_index + 1}"

            for row_index, row_label in enumerate(self.ROW_LABELS):
                footer_token = self._format_group_info(column_index, row_index)
                control = self.window.add(
                    button_group_control_cls(
                        f"styles_{slug}_{row_index + 1}",
                        self._styled_grid_rect(host, column_index, row_index, style_sequence[row_index]),
                        group_name,
                        row_label,
                        selected=False,
                        style=style_sequence[row_index],
                        on_activate=lambda target=footer, token=footer_token: self._update_footer_label(target, token),
                        font_role=self.font_role("control"),
                    )
                )
                control.set_tab_index(focus_index)
                focus_index += 1
                self.group_controls.append(control)
                self._group_footer_bindings.append((control, footer, footer_token))

        host.app.style_label(
            self.window.add(label_control_cls("styles_heading_buttons", Rect(content_rect.left + self.PADDING_X + (button_column_index * (self.COLUMN_WIDTH + self.COLUMN_GAP)), heading_y, self.COLUMN_WIDTH, self.HEADING_HEIGHT), "Buttons", align="center")),
            size=18,
            role=self.font_role("heading"),
        )
        for row_index, style_name in enumerate(self.STYLE_NAMES):
            control = self.window.add(
                button_control_cls(
                    f"styles_button_{style_name}",
                    self._styled_grid_rect(host, button_column_index, row_index, style_name),
                    style_name.capitalize(),
                    lambda: None,
                    style=style_name,
                    font_role=self.font_role("control"),
                )
            )
            control.set_tab_index(focus_index)
            focus_index += 1
            self.button_controls.append(control)

        host.app.style_label(
            self.window.add(label_control_cls("styles_heading_toggles", Rect(content_rect.left + self.PADDING_X + (toggle_column_index * (self.COLUMN_WIDTH + self.COLUMN_GAP)), heading_y, self.COLUMN_WIDTH, self.HEADING_HEIGHT), "Toggles", align="center")),
            size=18,
            role=self.font_role("heading"),
        )
        for row_index, style_name in enumerate(self.STYLE_NAMES):
            control = self.window.add(
                toggle_control_cls(
                    f"styles_toggle_{style_name}",
                    self._styled_grid_rect(host, toggle_column_index, row_index, style_name),
                    style_name.capitalize(),
                    style_name.capitalize(),
                    pushed=False,
                    on_toggle=lambda _pushed: None,
                    style=style_name,
                    font_role=self.font_role("control"),
                )
            )
            control.set_tab_index(focus_index)
            focus_index += 1
            self.toggle_controls.append(control)

        self.window.visible = False

    def _format_group_info(self, column_index: int, row_index: int) -> str:
        group_short = f"{int(column_index) + 1}"
        id_short = f"{int(row_index) + 1}"
        return f"Gr: {group_short} ID: {id_short}"

    def _styled_grid_rect(self, host, column_index: int, row_index: int, style_name: str) -> Rect:
        cell = Rect(host.app.layout.gridded(column_index, row_index))
        if str(style_name).lower() not in self.CENTERED_STYLES:
            return cell
        width = min(cell.width, self.CENTERED_STYLE_WIDTH)
        x = cell.left + ((cell.width - width) // 2)
        return Rect(x, cell.top, width, cell.height)

    def _update_footer_label(self, footer_label, token: str) -> None:
        footer_label.text = token

    def prewarm(self, host, surface, theme) -> None:
        """Prime styles window and child control visuals before first window open."""
        del host
        if self.window is None:
            return
        self.window.draw(surface, theme)
