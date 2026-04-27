"""DialogManager — modal dialog system built on OverlayManager."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, List, Optional, TYPE_CHECKING

from pygame import Rect

if TYPE_CHECKING:
    from ..app.gui_application import GuiApplication


@dataclass
class DialogHandle:
    dialog_id: int
    _manager: "DialogManager"

    def dismiss(self) -> None:
        self._manager.dismiss(self)

    @property
    def is_open(self) -> bool:
        return self._manager._is_open(self.dialog_id)


_SCRIM_ID_PREFIX = "__dialog_scrim__"
_DIALOG_ID_PREFIX = "__dialog_box__"
_DEFAULT_WIDTH = 320


class DialogManager:
    """Creates and manages modal dialogs using OverlayManager."""

    def __init__(self, app: "GuiApplication") -> None:
        self._app = app
        self._next_id: int = 1
        self._open_ids: List[int] = []

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def show_alert(
        self,
        title: str,
        message: str,
        *,
        button_label: str = "OK",
        on_close: Optional[Callable[[], None]] = None,
        width: int = _DEFAULT_WIDTH,
    ) -> DialogHandle:
        dialog_id = self._alloc_id()
        self._open_ids.append(dialog_id)

        def _handle_close():
            self._dismiss_id(dialog_id)
            if on_close is not None:
                try:
                    on_close()
                except Exception:
                    pass

        self._show_modal(dialog_id, title, message, [
            (button_label, _handle_close, False),
        ], width=width)
        return DialogHandle(dialog_id, self)

    def show_confirm(
        self,
        title: str,
        message: str,
        *,
        confirm_label: str = "Confirm",
        cancel_label: str = "Cancel",
        on_confirm: Optional[Callable[[], None]] = None,
        on_cancel: Optional[Callable[[], None]] = None,
        width: int = _DEFAULT_WIDTH,
        dangerous: bool = False,
    ) -> DialogHandle:
        dialog_id = self._alloc_id()
        self._open_ids.append(dialog_id)

        def _confirm():
            self._dismiss_id(dialog_id)
            if on_confirm is not None:
                try:
                    on_confirm()
                except Exception:
                    pass

        def _cancel():
            self._dismiss_id(dialog_id)
            if on_cancel is not None:
                try:
                    on_cancel()
                except Exception:
                    pass

        self._show_modal(dialog_id, title, message, [
            (confirm_label, _confirm, dangerous),
            (cancel_label, _cancel, False),
        ], width=width)
        return DialogHandle(dialog_id, self)

    def show_prompt(
        self,
        title: str,
        prompt: str,
        *,
        default_value: str = "",
        placeholder: str = "",
        max_length: Optional[int] = None,
        masked: bool = False,
        on_submit: Optional[Callable[[str], None]] = None,
        on_cancel: Optional[Callable[[], None]] = None,
        width: int = _DEFAULT_WIDTH,
    ) -> DialogHandle:
        dialog_id = self._alloc_id()
        self._open_ids.append(dialog_id)

        def _submit(value: str):
            self._dismiss_id(dialog_id)
            if on_submit is not None:
                try:
                    on_submit(value)
                except Exception:
                    pass

        def _cancel():
            self._dismiss_id(dialog_id)
            if on_cancel is not None:
                try:
                    on_cancel()
                except Exception:
                    pass

        self._show_prompt_modal(dialog_id, title, prompt, default_value, placeholder, max_length, masked, _submit, _cancel, width)
        return DialogHandle(dialog_id, self)

    def dismiss(self, handle: DialogHandle) -> bool:
        return self._dismiss_id(handle.dialog_id)

    def dismiss_all(self) -> int:
        count = len(self._open_ids)
        ids = list(self._open_ids)
        for did in ids:
            self._dismiss_id(did)
        return count

    def active_count(self) -> int:
        return len(self._open_ids)

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _alloc_id(self) -> int:
        did = self._next_id
        self._next_id += 1
        return did

    def _is_open(self, dialog_id: int) -> bool:
        return dialog_id in self._open_ids

    def _dismiss_id(self, dialog_id: int) -> bool:
        if dialog_id not in self._open_ids:
            return False
        self._open_ids.remove(dialog_id)
        self._app.overlay.hide(f"{_SCRIM_ID_PREFIX}{dialog_id}")
        self._app.overlay.hide(f"{_DIALOG_ID_PREFIX}{dialog_id}")
        return True

    def _show_modal(
        self,
        dialog_id: int,
        title: str,
        message: str,
        buttons: list,
        *,
        width: int,
    ) -> None:
        from ..controls.overlay_panel_control import OverlayPanelControl

        app = self._app
        screen = app.surface.get_rect()

        # Scrim overlay (no dismiss on outside click)
        scrim = OverlayPanelControl(f"{_SCRIM_ID_PREFIX}{dialog_id}", screen)
        app.overlay.show(
            f"{_SCRIM_ID_PREFIX}{dialog_id}",
            scrim,
            dismiss_on_outside_click=False,
            dismiss_on_escape=False,
        )

        # Dialog box
        height = 160
        x = (screen.width - width) // 2
        y = (screen.height - height) // 2
        box = OverlayPanelControl(f"{_DIALOG_ID_PREFIX}{dialog_id}", Rect(x, y, width, height))
        app.overlay.show(
            f"{_DIALOG_ID_PREFIX}{dialog_id}",
            box,
            dismiss_on_outside_click=False,
            dismiss_on_escape=False,
        )

    def _show_prompt_modal(
        self,
        dialog_id: int,
        title: str,
        prompt: str,
        default_value: str,
        placeholder: str,
        max_length: Optional[int],
        masked: bool,
        on_submit: Callable[[str], None],
        on_cancel: Callable[[], None],
        width: int,
    ) -> None:
        from ..controls.overlay_panel_control import OverlayPanelControl

        app = self._app
        screen = app.surface.get_rect()

        scrim = OverlayPanelControl(f"{_SCRIM_ID_PREFIX}{dialog_id}", screen)
        app.overlay.show(
            f"{_SCRIM_ID_PREFIX}{dialog_id}",
            scrim,
            dismiss_on_outside_click=False,
            dismiss_on_escape=False,
        )

        height = 180
        x = (screen.width - width) // 2
        y = (screen.height - height) // 2
        box = OverlayPanelControl(f"{_DIALOG_ID_PREFIX}{dialog_id}", Rect(x, y, width, height))
        app.overlay.show(
            f"{_DIALOG_ID_PREFIX}{dialog_id}",
            box,
            dismiss_on_outside_click=False,
            dismiss_on_escape=False,
        )
