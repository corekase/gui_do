from __future__ import annotations

from typing import Dict, Optional, Protocol, TYPE_CHECKING, Tuple

from pygame import Rect
from pygame.surface import Surface

from ...events import ButtonStyle

if TYPE_CHECKING:
    from ..widget_graphics_factory import WidgetGraphicsFactory


class ButtonStyleStrategy(Protocol):
    """Builds state bitmaps and hit rect for one button style."""

    def render(
        self,
        factory: "WidgetGraphicsFactory",
        text: Optional[str],
        rect: Rect,
    ) -> Tuple[Tuple[Surface, Surface, Surface], Rect]:
        """Run render and return the resulting value.

        This method encapsulates the main behavior for this operation."""
        ...


class BoxButtonStyleStrategy:
    """Render strategy for rectangular box-style buttons."""

    def render(
        self,
        factory: "WidgetGraphicsFactory",
        text: Optional[str],
        rect: Rect,
    ) -> Tuple[Tuple[Surface, Surface, Surface], Rect]:
        """Render box-style idle/hover/armed surfaces and hit rect."""
        return factory._draw_box_style_bitmaps(text, rect)


class RoundButtonStyleStrategy:
    """Render strategy for rounded button styling."""

    def render(
        self,
        factory: "WidgetGraphicsFactory",
        text: Optional[str],
        rect: Rect,
    ) -> Tuple[Tuple[Surface, Surface, Surface], Rect]:
        """Render rounded-style idle/hover/armed surfaces and hit rect."""
        return factory._draw_rounded_style_bitmaps(text, rect)


class AngleButtonStyleStrategy:
    """Render strategy for beveled angle-style buttons."""

    def render(
        self,
        factory: "WidgetGraphicsFactory",
        text: Optional[str],
        rect: Rect,
    ) -> Tuple[Tuple[Surface, Surface, Surface], Rect]:
        """Render angle-style idle/hover/armed surfaces and hit rect."""
        return factory._draw_angle_style_bitmaps(text, rect)


class RadioButtonStyleStrategy:
    """Render strategy for radio-indicator style buttons."""

    def render(
        self,
        factory: "WidgetGraphicsFactory",
        text: Optional[str],
        rect: Rect,
    ) -> Tuple[Tuple[Surface, Surface, Surface], Rect]:
        """Render radio-style idle/hover/armed surfaces and hit rect."""
        return factory._draw_radio_style_bitmaps(text, rect)


class CheckButtonStyleStrategy:
    """Render strategy for checkbox-style buttons."""

    def render(
        self,
        factory: "WidgetGraphicsFactory",
        text: Optional[str],
        rect: Rect,
    ) -> Tuple[Tuple[Surface, Surface, Surface], Rect]:
        """Render check-style idle/hover/armed surfaces and hit rect."""
        return factory._draw_check_style_bitmaps(text, rect)


def build_default_button_style_strategies() -> Dict[ButtonStyle, ButtonStyleStrategy]:
    """Return default mapping from `ButtonStyle` to rendering strategy instances."""
    return {
        ButtonStyle.Box: BoxButtonStyleStrategy(),
        ButtonStyle.Round: RoundButtonStyleStrategy(),
        ButtonStyle.Angle: AngleButtonStyleStrategy(),
        ButtonStyle.Radio: RadioButtonStyleStrategy(),
        ButtonStyle.Check: CheckButtonStyleStrategy(),
    }
