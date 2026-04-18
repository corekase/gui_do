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
        ...


class BoxButtonStyleStrategy:
    def render(
        self,
        factory: "WidgetGraphicsFactory",
        text: Optional[str],
        rect: Rect,
    ) -> Tuple[Tuple[Surface, Surface, Surface], Rect]:
        return factory._draw_box_style_bitmaps(text, rect)


class RoundButtonStyleStrategy:
    def render(
        self,
        factory: "WidgetGraphicsFactory",
        text: Optional[str],
        rect: Rect,
    ) -> Tuple[Tuple[Surface, Surface, Surface], Rect]:
        return factory._draw_rounded_style_bitmaps(text, rect)


class AngleButtonStyleStrategy:
    def render(
        self,
        factory: "WidgetGraphicsFactory",
        text: Optional[str],
        rect: Rect,
    ) -> Tuple[Tuple[Surface, Surface, Surface], Rect]:
        return factory._draw_angle_style_bitmaps(text, rect)


class RadioButtonStyleStrategy:
    def render(
        self,
        factory: "WidgetGraphicsFactory",
        text: Optional[str],
        rect: Rect,
    ) -> Tuple[Tuple[Surface, Surface, Surface], Rect]:
        return factory._draw_radio_style_bitmaps(text, rect)


class CheckButtonStyleStrategy:
    def render(
        self,
        factory: "WidgetGraphicsFactory",
        text: Optional[str],
        rect: Rect,
    ) -> Tuple[Tuple[Surface, Surface, Surface], Rect]:
        return factory._draw_check_style_bitmaps(text, rect)


def build_default_button_style_strategies() -> Dict[ButtonStyle, ButtonStyleStrategy]:
    return {
        ButtonStyle.Box: BoxButtonStyleStrategy(),
        ButtonStyle.Round: RoundButtonStyleStrategy(),
        ButtonStyle.Angle: AngleButtonStyleStrategy(),
        ButtonStyle.Radio: RadioButtonStyleStrategy(),
        ButtonStyle.Check: CheckButtonStyleStrategy(),
    }
