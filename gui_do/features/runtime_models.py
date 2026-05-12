from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Sequence


@dataclass(frozen=True)
class NotificationSpec:
    """Declarative descriptor for a pre-seeded notification record."""

    message: str
    title: str = ""
    severity: object = None


@dataclass(frozen=True)
class TabbedPresenterSpec:
    """Declarative descriptor for presenter-hosted tab layout and setup."""

    control_id: str
    selected_key: str
    tab_height: int = 36
    tab_rows: int = 2
    padding: int = 0
    min_content_height: int = 60


def build_notification_center(
    specs: Sequence["NotificationSpec"],
    *,
    max_records: int = 6,
) -> object:
    """Return a pre-populated NotificationCenter instance."""
    from ..overlays.notification_center import NotificationCenter, NotificationRecord
    from ..overlays.toast_manager import ToastSeverity as _Sev

    center = NotificationCenter(None, max_records=max(1, int(max_records)))
    for spec in specs:
        severity = spec.severity if spec.severity is not None else _Sev.INFO
        center.add(NotificationRecord(spec.message, title=str(spec.title), severity=severity))
    return center


class ActiveTabUpdateRouter:
    """Route per-frame update callbacks by active tab key."""

    def __init__(self) -> None:
        self._handlers: dict[str, Callable[..., object]] = {}

    def register(self, tab_key: str, handler: Callable[..., object]) -> None:
        self._handlers[str(tab_key)] = handler

    def unregister(self, tab_key: str) -> bool:
        key = str(tab_key)
        if key in self._handlers:
            del self._handlers[key]
            return True
        return False

    def run(self, active_tab_key: str, *args, **kwargs) -> bool:
        handler = self._handlers.get(str(active_tab_key))
        if handler is None:
            return False
        handler(*args, **kwargs)
        return True

    def keys(self) -> tuple[str, ...]:
        return tuple(self._handlers.keys())


@dataclass
class TelemetryConfig:
    """Telemetry settings for the application."""

    enabled: bool = False
    live_analysis_enabled: bool = True
    file_logging_enabled: bool = False


@dataclass
class HostApplicationConfig:
    """Complete declarative configuration for bootstrapping a host application."""

    display_size: tuple[int, int]
    window_title: str
    fonts: dict
    font_role_specs: tuple[dict, ...]
    cursors: tuple
    scene_specs: tuple
    feature_specs: tuple
    window_specs: tuple
    runtime_scene_specs: tuple
    action_specs: tuple
    static_accessibility_specs: tuple
    initial_scene_name: str
    scene_roots: tuple = field(default_factory=tuple)
    telemetry: TelemetryConfig = field(default_factory=TelemetryConfig)
    target_fps: int = 120
    palette_spec: object | None = None
