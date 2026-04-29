from __future__ import annotations

from ..core.error_handling import logical_error
from ._hover_press_control_base import _HoverPressControlBase


class _TextButtonControlBase(_HoverPressControlBase):
    """Shared font-role and visual-cache state for text-labelled button controls."""

    def __init__(self, control_id: str, rect, font_role: str = "body") -> None:
        super().__init__(control_id, rect)
        self._font_role = "body"
        self.font_role = font_role
        self._visuals = None
        self._visual_key = None

    @property
    def font_role(self) -> str:
        return self._font_role

    @font_role.setter
    def font_role(self, value: str) -> None:
        next_role = str(value).strip()
        if not next_role:
            raise logical_error(
                "font_role must be a non-empty string",
                subsystem="gui.controls",
                operation="font_role",
                source_skip_frames=1,
            )
        self._font_role = next_role
