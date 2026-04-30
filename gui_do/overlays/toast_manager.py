"""ToastManager — app-level toast notifications."""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from enum import Enum, auto
from typing import Any, Deque, Dict, Optional, Tuple, TYPE_CHECKING

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
    elapsed: float = 0.0
    alpha: float = 1.0


_SEVERITY_COLORS: "Dict[ToastSeverity, Tuple[int, int, int]]" = {
    ToastSeverity.INFO: (50, 120, 200),
    ToastSeverity.SUCCESS: (50, 180, 80),
    ToastSeverity.WARNING: (200, 160, 40),
    ToastSeverity.ERROR: (200, 60, 60),
}


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
        row_height: int = 56,
        margin: int = 16,
        gap: int = 8,
    ) -> None:
        self._screen_rect = Rect(screen_rect)
        self._position = position
        self._max_visible = max(1, int(max_visible))
        self._default_duration = float(default_duration_seconds)
        self._toast_width = int(toast_width)
        self._row_height = int(row_height)
        self._margin = int(margin)
        self._gap = int(gap)
        self._toasts: Deque[_ToastEntry] = deque(maxlen=self._max_visible)
        self._next_id: int = 1
        self._draw_font: object = None  # cached from pygame.font.SysFont(None, 18)

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
        )
        self._toasts.append(entry)
        return ToastHandle(toast_id, self)

    def dismiss(self, handle: ToastHandle) -> None:
        self._toasts = deque(
            (t for t in self._toasts if t.toast_id != handle.toast_id),
            maxlen=self._max_visible,
        )

    def dismiss_all(self) -> int:
        count = len(self._toasts)
        self._toasts.clear()
        return count

    @property
    def visible_count(self) -> int:
        return len(self._toasts)

    def _has_toast(self, toast_id: int) -> bool:
        return any(t.toast_id == toast_id for t in self._toasts)

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
        if self._draw_font is None:
            if not hasattr(theme, "fonts"):
                raise RuntimeError("ToastManager requires theme with centralized font roles.")
            self._draw_font = theme.fonts.font_instance("toast.text", size=18)
        font = self._draw_font
        w = self._toast_width
        h = self._row_height
        gap = self._gap
        margin = self._margin
        sr = self._screen_rect

        default_background_color = getattr(theme, "medium", (0, 150, 150))
        default_outline_color = getattr(theme, "shadow", (0, 0, 0))
        # gui_do 'none' color is (0, 0, 0) by default, but can be changed if needed
        if hasattr(theme, "none"):
            default_outline_color = getattr(theme, "none")

        for i, entry in enumerate(reversed(self._toasts)):
            color = entry.background_color if entry.background_color is not None else default_background_color
            outline = entry.outline_color if entry.outline_color is not None else default_outline_color
            if "right" in self._position:
                x = sr.right - w - margin
            elif "left" in self._position:
                x = sr.left + margin
            else:
                x = sr.centerx - w // 2

            if "bottom" in self._position:
                y = sr.bottom - margin - (h + gap) * (i + 1) + gap
            else:
                y = sr.top + margin + (h + gap) * i

            rect = Rect(x, y, w, h)
            pygame.draw.rect(surface, color, rect, border_radius=4)
            pygame.draw.rect(surface, outline, rect, width=2, border_radius=4)
            text_color = (240, 240, 240)
            if entry.title:
                title_surf = theme.fonts.render_text(entry.title, text_color, role_name="toast.text", size=font.point_size)
                surface.blit(title_surf, (rect.x + 8, rect.y + 6))
            msg_surf = theme.fonts.render_text(entry.message, text_color, role_name="toast.text", size=font.point_size)
            surface.blit(msg_surf, (rect.x + 8, rect.y + h // 2))

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
