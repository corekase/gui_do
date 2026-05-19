"""ToastManager — app-level toast notifications."""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from enum import Enum, auto
from typing import Any, Callable, Optional, TYPE_CHECKING

import pygame
from pygame import Rect

if TYPE_CHECKING:
    from ..theme.color_theme import ColorTheme
    from ..scheduling.tween_manager import TweenManager


class ToastSeverity(Enum):
    INFO = auto()
    SUCCESS = auto()
    WARNING = auto()
    ERROR = auto()


@dataclass
class ToastHandle:
    toast_id: int
    _manager: "ToastManager"

    def dismiss(self) -> None:
        self._manager.dismiss(self)

    @property
    def is_visible(self) -> bool:
        return self._manager._has_toast(self.toast_id)


@dataclass
class _ToastEntry:
    toast_id: int
    message: str
    title: Optional[str]
    severity: ToastSeverity
    duration_seconds: Optional[float]  # None = persistent
    background_color: Optional[tuple] = None
    outline_color: Optional[tuple] = None
    on_click: Optional[Callable[[], None]] = None
    elapsed: float = 0.0
    alpha: float = 1.0


@dataclass
class _SuspendedToastState:
    scene_name: str
    entries: list[_ToastEntry]


class ToastManager:
    """App-level service for showing transient toast notifications."""

    def __init__(
        self,
        screen_rect: Rect,
        *,
        position: str = "bottom_right",
        max_visible: int = 5,
        default_duration_seconds: float = 3.0,
        toast_width: int = 280,
        margin: int = 16,
        gap: int = 8,
    ) -> None:
        self._screen_rect = Rect(screen_rect)
        self._position = position
        self._max_visible = max(1, int(max_visible))
        self._default_duration = float(default_duration_seconds)
        self._toast_width = int(toast_width)
        self._margin = int(margin)
        self._gap = int(gap)
        self._toasts: Deque[_ToastEntry] = deque(maxlen=self._max_visible)
        self._suspended_toasts: dict[str, _SuspendedToastState] = {}
        self._next_id: int = 1
        self._draw_font: object = None  # cached from pygame.font.SysFont(None, 18)
        self._draw_font_theme: object = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def show(
        self,
        message: str,
        *,
        title: Optional[str] = None,
        severity: ToastSeverity = ToastSeverity.INFO,
        duration_seconds: Optional[float] = None,
        background_color: Optional[tuple] = None,
        outline_color: Optional[tuple] = None,
        on_click: Optional[Callable[[], None]] = None,
    ) -> ToastHandle:
        toast_id = self._next_id
        self._next_id += 1
        duration = duration_seconds if duration_seconds is not None else self._default_duration
        entry = _ToastEntry(
            toast_id=toast_id,
            message=message,
            title=title,
            severity=severity,
            duration_seconds=duration,
            background_color=background_color,
            outline_color=outline_color,
            on_click=on_click,
        )
        self._toasts.append(entry)
        return ToastHandle(toast_id, self)

    def show_persistent(
        self,
        message: str,
        *,
        title: Optional[str] = None,
        severity: ToastSeverity = ToastSeverity.INFO,
        background_color: Optional[tuple] = None,
        outline_color: Optional[tuple] = None,
        on_click: Optional[Callable[[], None]] = None,
    ) -> ToastHandle:
        toast_id = self._next_id
        self._next_id += 1
        entry = _ToastEntry(
            toast_id=toast_id,
            message=message,
            title=title,
            severity=severity,
            duration_seconds=None,  # persistent
            background_color=background_color,
            outline_color=outline_color,
            on_click=on_click,
        )
        self._toasts.append(entry)
        return ToastHandle(toast_id, self)

    def dismiss(self, handle: ToastHandle) -> None:
        self._remove_toast(handle.toast_id)

    def dismiss_all(self) -> int:
        count = len(self._toasts)
        self._toasts.clear()
        return count

    def suspend_for_scene(self, scene_name: str) -> int:
        """Save the active toasts for *scene_name* and clear the visible list."""
        scene_name = str(scene_name)
        entries = list(self._toasts)
        if not entries:
            self._suspended_toasts.pop(scene_name, None)
            return 0
        self._suspended_toasts[scene_name] = _SuspendedToastState(scene_name=scene_name, entries=entries)
        count = len(entries)
        self._toasts.clear()
        return count

    def restore_for_scene(self, scene_name: str) -> int:
        """Restore any toasts previously suspended for *scene_name*."""
        scene_name = str(scene_name)
        state = self._suspended_toasts.pop(scene_name, None)
        if state is None or not state.entries:
            return 0
        self._toasts = deque(state.entries, maxlen=self._max_visible)
        return len(self._toasts)

    def discard_scene_state(self, scene_name: str) -> None:
        """Forget suspended toast state for a scene that is going away."""
        self._suspended_toasts.pop(str(scene_name), None)

    @property
    def visible_count(self) -> int:
        return len(self._toasts)

    def _has_toast(self, toast_id: int) -> bool:
        return any(t.toast_id == toast_id for t in self._toasts)

    def _remove_toast(self, toast_id: int) -> bool:
        removed = False
        filtered = [entry for entry in self._toasts if entry.toast_id != toast_id]
        if len(filtered) != len(self._toasts):
            self._toasts = deque(filtered, maxlen=self._max_visible)
            removed = True

        for scene_name, state in list(self._suspended_toasts.items()):
            entries = [entry for entry in state.entries if entry.toast_id != toast_id]
            if len(entries) == len(state.entries):
                continue
            removed = True
            if entries:
                self._suspended_toasts[scene_name] = _SuspendedToastState(scene_name=scene_name, entries=entries)
            else:
                self._suspended_toasts.pop(scene_name, None)
        return removed

    # ------------------------------------------------------------------
    # Update / draw
    # ------------------------------------------------------------------

    def update(self, dt_seconds: float, tweens: "Optional[TweenManager]" = None) -> None:
        """Advance toast timers and remove expired ones."""
        expired = []
        for entry in self._toasts:
            if entry.duration_seconds is not None:
                entry.elapsed += dt_seconds
                if entry.elapsed >= entry.duration_seconds:
                    expired.append(entry.toast_id)
        if expired:
            expired_ids = set(expired)
            self._toasts = deque(
                (t for t in self._toasts if t.toast_id not in expired_ids),
                maxlen=self._max_visible,
            )

    def draw(self, surface: "pygame.Surface", theme: "ColorTheme") -> None:
        if not self._toasts:
            return
        font = self._ensure_draw_font(theme)

        default_background_color = getattr(theme, "medium", (0, 150, 150))
        default_outline_color = getattr(theme, "shadow", (0, 0, 0))
        if hasattr(theme, "none"):
            default_outline_color = getattr(theme, "none")
        text_color = (240, 240, 240)
        layout = self._layout_toasts(font)

        # Draw each toast
        for entry, rect in layout:
            color = entry.background_color if entry.background_color is not None else default_background_color
            outline = entry.outline_color if entry.outline_color is not None else default_outline_color
            pygame.draw.rect(surface, color, rect, border_radius=4)
            pygame.draw.rect(surface, outline, rect, width=2, border_radius=4)
            draw_y = rect.y + 10
            if entry.title:
                title_surf = theme.render_text(
                    entry.title,
                    role="toast.text",
                    size=font.point_size,
                    color=text_color,
                )
                surface.blit(title_surf, (rect.x + 16, draw_y))
                draw_y += title_surf.get_height() + 6
            msg_surf = theme.render_text(
                entry.message,
                role="toast.text",
                size=font.point_size,
                color=text_color,
            )
            surface.blit(msg_surf, (rect.x + 16, draw_y))

    def route_event(self, event, app) -> bool:
        """Consume pointer events over toast bounds and invoke optional click callbacks."""
        if not self._toasts:
            return False
        from ..events.gui_event import EventType

        kind = getattr(event, "kind", None)
        if kind not in (
            pygame.MOUSEBUTTONDOWN,
            pygame.MOUSEBUTTONUP,
            pygame.MOUSEMOTION,
            pygame.MOUSEWHEEL,
            EventType.MOUSE_BUTTON_DOWN,
            EventType.MOUSE_BUTTON_UP,
            EventType.MOUSE_MOTION,
            EventType.MOUSE_WHEEL,
        ):
            return False
        pos = getattr(event, "pos", None)
        if not (isinstance(pos, tuple) and len(pos) == 2):
            return False

        theme = getattr(app, "theme", None)
        if theme is None:
            return False
        font = self._ensure_draw_font(theme)
        for entry, rect in self._layout_toasts(font):
            if rect.collidepoint(pos):
                if kind in (pygame.MOUSEBUTTONDOWN, EventType.MOUSE_BUTTON_DOWN) and int(getattr(event, "button", 0) or 0) == 1:
                    callback = entry.on_click
                    if callable(callback):
                        try:
                            callback()
                        except Exception:
                            pass
                return True
        return False

    def _ensure_draw_font(self, theme):
        if self._draw_font is not None and self._draw_font_theme is theme:
            return self._draw_font
        if not hasattr(theme, "fonts"):
            raise RuntimeError("ToastManager requires theme with centralized font roles.")
        self._draw_font = theme.fonts.font_instance("toast.text", size=18)
        self._draw_font_theme = theme
        return self._draw_font

    def _layout_toasts(self, font) -> list[tuple[_ToastEntry, Rect]]:
        gap = self._gap
        margin = self._margin
        sr = self._screen_rect
        padding_x = 16
        padding_y = 10
        min_width = 120
        min_height = 40

        toast_rects = []
        ordered_entries = list(reversed(self._toasts))
        for entry in ordered_entries:
            title_w = title_h = 0
            if entry.title:
                title_w, title_h = font.text_size(entry.title)
            msg_w, msg_h = font.text_size(entry.message)
            content_w = max(title_w, msg_w)
            content_h = title_h + msg_h if entry.title else msg_h
            w = max(content_w + 2 * padding_x, min_width, self._toast_width)
            h = max(content_h + 2 * padding_y + (6 if entry.title else 0), min_height)
            toast_rects.append((w, h))

        rects: list[Rect] = []
        y_offset = 0
        for w, h in toast_rects:
            if "right" in self._position:
                x = sr.right - w - margin
            elif "left" in self._position:
                x = sr.left + margin
            else:
                x = sr.centerx - w // 2

            if "bottom" in self._position:
                y = sr.bottom - margin - y_offset - h
            else:
                y = sr.top + margin + y_offset
            rects.append(Rect(int(x), int(y), int(w), int(h)))
            y_offset += h + gap

        return list(zip(ordered_entries, rects))

    def on_event_bus_message(self, payload: Any) -> None:
        """Handle event bus messages with keys: message, title, severity, duration, background_color, outline_color."""
        if not isinstance(payload, dict):
            return
        message = payload.get("message", "")
        title = payload.get("title")
        severity_name = payload.get("severity", "INFO").upper()
        severity = getattr(ToastSeverity, severity_name, ToastSeverity.INFO)
        duration = payload.get("duration_seconds")
        background_color = payload.get("background_color")
        outline_color = payload.get("outline_color")
        self.show(message, title=title, severity=severity, duration_seconds=duration, background_color=background_color, outline_color=outline_color)
