"""Main scene feature extracted from the gui_do demo entrypoint."""

from __future__ import annotations

from gui_do import (
    Feature,
    ShortcutHelpOverlay,
)
from gui_do.features.data_driven_runtime import (
    bind_feature_runtime,
    shutdown_feature_runtime,
)

from .main_build_helpers import (
    build_main_scene as build_main_scene_helper,
    toggle_help_overlay as toggle_help_overlay_helper,
)
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
        bind_feature_runtime(
            self,
            host,
            runtime_spec=_MAIN_RUNTIME_SPEC,
            runtime_spec_attr_name="",
            bind_escape_to_exit_scene="main",
        )


    def shutdown_runtime(self, host) -> None:
        shutdown_feature_runtime(
            self,
            host,
            runtime_spec=_MAIN_RUNTIME_SPEC,
            runtime_spec_attr_name="",
            bind_escape_to_exit_scene="main",
        )

    def _toggle_help_overlay(self) -> None:
        toggle_help_overlay_helper(self)
