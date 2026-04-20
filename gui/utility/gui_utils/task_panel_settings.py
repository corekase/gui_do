from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional

from ..events import BaseEvent


@dataclass(frozen=True)
class TaskPanelSettings:
    """Immutable task-panel configuration bundle for object-oriented configuration."""

    panel_height: int = 38
    left: int = 0
    width: Optional[int] = None
    hidden_peek_pixels: int = 4
    auto_hide: bool = True
    animation_interval_ms: float = 16.0
    animation_step_px: int = 4
    backdrop_image: Optional[str] = None
    preamble: Optional[Callable[[], None]] = None
    event_handler: Optional[Callable[[BaseEvent], None]] = None
    postamble: Optional[Callable[[], None]] = None
