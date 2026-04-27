"""FileDialogManager — modal file-open and file-save dialogs."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, List, Optional, Tuple, TYPE_CHECKING

import pygame
from pygame import Rect

from ..controls.overlay_panel_control import OverlayPanelControl
from ..controls.list_view_control import ListViewControl, ListItem
from ..controls.text_input_control import TextInputControl
from ..controls.button_control import ButtonControl
from ..controls.label_control import LabelControl
from ..core.gui_event import EventType, GuiEvent

if TYPE_CHECKING:
    from ..app.gui_application import GuiApplication
    from ..theme.color_theme import ColorTheme


@dataclass
class FileDialogOptions:
    """Configuration for a file dialog.

    Attributes:
        title: Dialog window title text.
        start_dir: Initial directory to display.  Defaults to CWD.
        filters: List of ``(label, [ext, ...])`` pairs, e.g.
            ``[("Images", [".png", ".jpg"]), ("All", ["*"])]``.
        allow_new_file: When ``True`` the filename field is editable (save
            dialogs).  When ``False`` the user must pick an existing file
            (open dialogs).
        multi_select: Allow selecting multiple files (open dialogs only).
    """

    title: str = "Open File"
    start_dir: Optional[str] = None
    filters: List[Tuple[str, List[str]]] = field(default_factory=list)
    allow_new_file: bool = False
    multi_select: bool = False


class FileDialogHandle:
    """Handle to an open file dialog.

    *result* is ``None`` until the dialog closes.  If the user cancelled,
    *result* is an empty list.  On confirmation *result* contains the
    selected paths as strings.
    """

    def __init__(self) -> None:
        self.result: Optional[List[str]] = None
        self._on_close: Optional[Callable[[List[str]], None]] = None
        self._dismissed = False

    @property
    def is_open(self) -> bool:
        return self.result is None and not self._dismissed

    def _resolve(self, paths: List[str]) -> None:
        self.result = paths
        self._dismissed = True
        if self._on_close:
            try:
                self._on_close(paths)
            except Exception:
                pass

    def _cancel(self) -> None:
        self._resolve([])


_BTN_H = 30
_BTN_W = 90
_PAD = 8
_FONT_SIZE = 17
_INPUT_H = 28
_FILTER_H = 24
_BREADCRUMB_H = 22


def _c(theme: "ColorTheme", name: str, fallback: tuple) -> tuple:
    v = getattr(theme, name, fallback)
    return v.value if hasattr(v, "value") else v


class _FileDialogPanel(OverlayPanelControl):
    """Internal overlay panel implementing the file dialog UI."""

    def __init__(
        self,
        control_id: str,
        rect: Rect,
        opts: FileDialogOptions,
        handle: FileDialogHandle,
        app: "GuiApplication",
    ) -> None:
        super().__init__(control_id, rect, draw_background=True)
        self._opts = opts
        self._handle = handle
        self._app = app
        self._current_dir = Path(opts.start_dir or os.getcwd()).resolve()
        self._selected_paths: List[Path] = []
        self._filter_index: int = 0
        self._entries: List[Path] = []
        self._list_items: List[ListItem] = []
        self._font_size = _FONT_SIZE

        # Sub-controls (laid out in _layout)
        inner_w = rect.width - _PAD * 2
        inner_h = rect.height - _PAD * 2
        inner_x = rect.x + _PAD
        inner_y = rect.y + _PAD

        # Breadcrumb label area
        breadcrumb_rect = Rect(inner_x, inner_y, inner_w, _BREADCRUMB_H)
        inner_y += _BREADCRUMB_H + _PAD

        # File list
        list_h = inner_h - _BREADCRUMB_H - _PAD - _INPUT_H - _PAD - _BTN_H - _PAD * 2
        list_rect = Rect(inner_x, inner_y, inner_w, max(60, list_h))
        inner_y += list_rect.height + _PAD

        # Filename input
        input_rect = Rect(inner_x, inner_y, inner_w, _INPUT_H)
        inner_y += _INPUT_H + _PAD

        # Buttons
        ok_rect = Rect(rect.right - _PAD - _BTN_W, inner_y, _BTN_W, _BTN_H)
        cancel_rect = Rect(rect.right - _PAD * 2 - _BTN_W * 2, inner_y, _BTN_W, _BTN_H)

        self._breadcrumb_rect = breadcrumb_rect
        self._list_view = ListViewControl(
            f"{control_id}_list",
            list_rect,
            row_height=24,
            on_select=self._on_list_select,
            multi_select=opts.multi_select,
        )
        self._filename_input = TextInputControl(
            f"{control_id}_input",
            input_rect,
            placeholder="filename",
        )
        ok_label = "Save" if opts.allow_new_file else "Open"
        self._ok_btn = ButtonControl(
            f"{control_id}_ok",
            ok_rect,
            ok_label,
            on_click=self._on_ok,
        )
        self._cancel_btn = ButtonControl(
            f"{control_id}_cancel",
            cancel_rect,
            "Cancel",
            on_click=self._on_cancel,
        )
        self._refresh_directory()

    # ------------------------------------------------------------------
    # Directory navigation
    # ------------------------------------------------------------------

    def _refresh_directory(self) -> None:
        try:
            raw = sorted(self._current_dir.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
        except PermissionError:
            raw = []
        self._entries = raw
        filters = self._opts.filters
        active_exts: Optional[List[str]] = None
        if filters and 0 <= self._filter_index < len(filters):
            exts = filters[self._filter_index][1]
            if "*" not in exts:
                active_exts = [e.lower().lstrip("*") for e in exts]

        items: List[ListItem] = []
        # Parent directory entry
        if self._current_dir.parent != self._current_dir:
            items.append(ListItem("..", value=str(self._current_dir.parent), data=self._current_dir.parent))
        for p in self._entries:
            if p.is_dir():
                items.append(ListItem(f"[{p.name}]", value=str(p), data=p))
            else:
                if active_exts is not None:
                    if not any(p.suffix.lower() == ext for ext in active_exts):
                        continue
                items.append(ListItem(p.name, value=str(p), data=p))
        self._list_items = items
        self._list_view.set_items(items)
        self._filename_input.set_value("")
        self._selected_paths = []

    def _on_list_select(self, idx: int, item: ListItem) -> None:
        p: Path = item.data
        if isinstance(p, Path) and p.is_dir():
            self._current_dir = p.resolve()
            self._refresh_directory()
        else:
            self._selected_paths = [p]
            self._filename_input.set_value(p.name if isinstance(p, Path) else str(item.value))

    def _on_ok(self) -> None:
        if self._opts.allow_new_file:
            name = self._filename_input.value.strip()
            if name:
                self._handle._resolve([str(self._current_dir / name)])
            else:
                return
        else:
            if self._selected_paths:
                self._handle._resolve([str(p) for p in self._selected_paths])
            else:
                text = self._filename_input.value.strip()
                if text:
                    self._handle._resolve([str(self._current_dir / text)])
                else:
                    return
        self._app.overlay.hide(self.control_id)

    def _on_cancel(self) -> None:
        self._handle._cancel()
        self._app.overlay.hide(self.control_id)

    # ------------------------------------------------------------------
    # UiNode overrides
    # ------------------------------------------------------------------

    def handle_event(self, event: GuiEvent, app: "GuiApplication") -> bool:
        if not self.visible:
            return False
        if event.kind == EventType.KEY_DOWN and event.key == pygame.K_ESCAPE:
            self._on_cancel()
            return True
        if event.kind == EventType.KEY_DOWN and event.key == pygame.K_RETURN:
            self._on_ok()
            return True
        # Route to sub-controls
        for ctrl in (self._filename_input, self._list_view, self._ok_btn, self._cancel_btn):
            if ctrl.handle_event(event, app):
                return True
        return self.rect.collidepoint(event.pos) if hasattr(event, "pos") and event.pos else False

    def draw(self, surface: "pygame.Surface", theme: "ColorTheme") -> None:
        if not self.visible:
            return

        bg = _c(theme, "panel", (40, 40, 50))
        text_col = _c(theme, "text", (220, 220, 220))
        border_col = _c(theme, "border", (80, 80, 95))
        title_bg = _c(theme, "accent", (0, 70, 140))

        # Dialog background + border
        pygame.draw.rect(surface, bg, self.rect)
        pygame.draw.rect(surface, border_col, self.rect, 1)

        # Title bar
        title_rect = Rect(self.rect.x, self.rect.y, self.rect.width, 24)
        pygame.draw.rect(surface, title_bg, title_rect)
        try:
            font = pygame.font.SysFont(None, _FONT_SIZE)
            txt = font.render(self._opts.title, True, text_col)
            surface.blit(txt, (title_rect.x + _PAD, title_rect.y + (title_rect.height - txt.get_height()) // 2))
        except Exception:
            pass

        # Breadcrumb
        try:
            font_sm = pygame.font.SysFont(None, 14)
            crumb = str(self._current_dir)
            ct = font_sm.render(crumb, True, text_col)
            surface.blit(ct, (self._breadcrumb_rect.x, self._breadcrumb_rect.y + (self._breadcrumb_rect.height - ct.get_height()) // 2))
        except Exception:
            pass

        self._list_view.draw(surface, theme)
        self._filename_input.draw(surface, theme)
        self._ok_btn.draw(surface, theme)
        self._cancel_btn.draw(surface, theme)


class FileDialogManager:
    """Provides modal file-open and file-save dialogs.

    Usage::

        fd = FileDialogManager(app)
        handle = fd.show_open(
            FileDialogOptions(
                title="Open Image",
                filters=[("Images", [".png", ".jpg"]), ("All", ["*"])],
            ),
            on_close=lambda paths: print("selected", paths),
        )
    """

    def __init__(self, app: "GuiApplication") -> None:
        self._app = app
        self._next_id = 1

    def _dialog_rect(self) -> Rect:
        """Return a centered dialog rect sized at 60% x 70% of the screen."""
        sr = self._app.surface.get_rect()
        w = int(sr.width * 0.60)
        h = int(sr.height * 0.70)
        return Rect((sr.width - w) // 2, (sr.height - h) // 2, w, h)

    def show_open(
        self,
        opts: Optional[FileDialogOptions] = None,
        *,
        on_close: Optional[Callable[[List[str]], None]] = None,
    ) -> FileDialogHandle:
        """Show a file-open dialog.  Returns a :class:`FileDialogHandle`."""
        if opts is None:
            opts = FileDialogOptions(title="Open File")
        opts = FileDialogOptions(
            title=opts.title,
            start_dir=opts.start_dir,
            filters=opts.filters,
            allow_new_file=False,
            multi_select=opts.multi_select,
        )
        return self._show(opts, on_close)

    def show_save(
        self,
        opts: Optional[FileDialogOptions] = None,
        *,
        on_close: Optional[Callable[[List[str]], None]] = None,
    ) -> FileDialogHandle:
        """Show a file-save dialog.  Returns a :class:`FileDialogHandle`."""
        if opts is None:
            opts = FileDialogOptions(title="Save File", allow_new_file=True)
        opts = FileDialogOptions(
            title=opts.title,
            start_dir=opts.start_dir,
            filters=opts.filters,
            allow_new_file=True,
            multi_select=False,
        )
        return self._show(opts, on_close)

    def _show(
        self,
        opts: FileDialogOptions,
        on_close: Optional[Callable[[List[str]], None]],
    ) -> FileDialogHandle:
        owner = f"_file_dialog_{self._next_id}"
        self._next_id += 1
        handle = FileDialogHandle()
        if on_close is not None:
            handle._on_close = on_close
        rect = self._dialog_rect()
        panel = _FileDialogPanel(owner, rect, opts, handle, self._app)
        self._app.overlay.show(
            owner,
            panel,
            dismiss_on_outside_click=False,
            dismiss_on_escape=False,
            on_dismiss=handle._cancel,
        )
        return handle
