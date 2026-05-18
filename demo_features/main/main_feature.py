"""Main scene feature extracted from the gui_do demo entrypoint."""

from __future__ import annotations

import pygame

from gui_do import (
    Feature,
    ShortcutHelpOverlay,
)
from gui_do.features.data_driven_runtime import (
    shutdown_routed_runtime,
    setup_routed_runtime,
)

from .main_build_helpers import build_main_scene as build_main_scene_helper, toggle_help_overlay as toggle_help_overlay_helper
from .main_specs import (
    MAIN_RUNTIME_SPEC as _MAIN_RUNTIME_SPEC,
)


class MainFeature(Feature):
    """Build the demo's main scene surface and dock controls."""

    HOST_REQUIREMENTS = {
        "build": (
            "app",
            "screen_rect",
            "scene_presentation",
            "window_presentation",
            "action_registry",
        ),
        "bind_runtime": ("app",),
    }

    def __init__(self) -> None:
        super().__init__("main_demo", scene_name="main")
        self._help_overlay: ShortcutHelpOverlay | None = None

    def build(self, host) -> None:
        build_main_scene_helper(self, host)

    def bind_runtime(self, host) -> None:
        """Wire runtime overlays and hotkeys from the declarative runtime spec."""
        setup_routed_runtime(self, host, _MAIN_RUNTIME_SPEC)
        app_actions = getattr(host.app, "actions", None)
        bind_global_key = getattr(app_actions, "bind_global_key", None)
        if callable(bind_global_key):
            bind_global_key(pygame.K_ESCAPE, "exit", scene="main")


    def shutdown_runtime(self, host) -> None:
        shutdown_routed_runtime(self, host, _MAIN_RUNTIME_SPEC)
        app_actions = getattr(host.app, "actions", None)
        unbind_global_key = getattr(app_actions, "unbind_global_key", None)
        if callable(unbind_global_key):
            unbind_global_key(pygame.K_ESCAPE, "exit", scene="main")

    def _toggle_help_overlay(self) -> None:
        toggle_help_overlay_helper(self)
