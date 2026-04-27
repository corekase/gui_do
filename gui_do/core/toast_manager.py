"""ToastManager — app-level toast notifications."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Tuple, TYPE_CHECKING

import pygame
from pygame import Rect

if TYPE_CHECKING:
    from ..theme.color_theme import ColorTheme
    from ..core.tween_manager import TweenManager


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
    elapsed: float = 0.0
    alpha: float = 1.0


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
        self._toasts: List[_ToastEntry] = []
        self._next_id: int = 1

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
        icon: Optional[str] = None,
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
        )
        self._toasts.append(entry)
        # Trim to max visible (oldest removed first)
        while len(self._toasts) > self._max_visible:
            self._toasts.pop(0)
        return ToastHandle(toast_id, self)

    def show_persistent(
        self,
        message: str,
        *,
        title: Optional[str] = None,
        severity: ToastSeverity = ToastSeverity.INFO,
    ) -> ToastHandle:
        toast_id = self._next_id
        self._next_id += 1
        entry = _ToastEntry(
            toast_id=toast_id,
            message=message,
            title=title,
            severity=severity,
            duration_seconds=None,  # persistent
        )
        self._toasts.append(entry)
        while len(self._toasts) > self._max_visible:
            self._toasts.pop(0)
        return ToastHandle(toast_id, self)

    def dismiss(self, handle: ToastHandle) -> None:
        self._toasts = [t for t in self._toasts if t.toast_id != handle.toast_id]

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
            self._toasts = [t for t in self._toasts if t.toast_id not in expired]

    def draw(self, surface: "pygame.Surface", theme: "ColorTheme") -> None:
        if not self._toasts:
            return
        font = pygame.font.SysFont(None, 18)
        w = self._toast_width
        h = self._row_height
        gap = self._gap
        margin = self._margin
        sr = self._screen_rect

        severity_colors: Dict[ToastSeverity, Tuple[int, int, int]] = {
            ToastSeverity.INFO: (50, 120, 200),
            ToastSeverity.SUCCESS: (50, 180, 80),
            ToastSeverity.WARNING: (200, 160, 40),
            ToastSeverity.ERROR: (200, 60, 60),
        }

        for i, entry in enumerate(reversed(self._toasts)):
            color = severity_colors.get(entry.severity, (80, 80, 80))
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
            text_color = (240, 240, 240)
            if entry.title:
                title_surf = font.render(entry.title, True, text_color)
                surface.blit(title_surf, (rect.x + 8, rect.y + 6))
            msg_surf = font.render(entry.message, True, text_color)
            surface.blit(msg_surf, (rect.x + 8, rect.y + h // 2))

    def on_event_bus_message(self, payload: Any) -> None:
        """Handle event bus messages with keys: message, title, severity, duration."""
        if not isinstance(payload, dict):
            return
        message = payload.get("message", "")
        title = payload.get("title")
        severity_name = payload.get("severity", "INFO").upper()
        severity = getattr(ToastSeverity, severity_name, ToastSeverity.INFO)
        duration = payload.get("duration_seconds")
        self.show(message, title=title, severity=severity, duration_seconds=duration)
