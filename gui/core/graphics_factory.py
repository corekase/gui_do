from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional, Tuple

import pygame
from pygame import Rect, Surface
from pygame.draw import circle, line, polygon, rect as draw_rect


@dataclass
class InteractiveVisuals:
    idle: Surface
    hover: Surface
    armed: Surface
    disabled: Surface
    hit_rect: Rect


@dataclass
class WindowChromeVisuals:
    title_bar_inactive: Surface
    title_bar_active: Surface
    lower_widget: Surface


class LegacyGraphicsFactory:
    """Built-in adapted graphics factory from the legacy gui_do style system."""

    def __init__(self, theme) -> None:
        self.theme = theme
        self._fonts: Dict[str, pygame.font.Font] = {
            "normal": theme.get_font(16, title=False),
            "titlebar": theme.get_font(14, title=True),
            "gui_do": theme.get_font(72, title=True),
        }
        self._font_stack = ["normal"]

    def get_current_font_name(self) -> str:
        return self._font_stack[-1]

    def set_font(self, name: str) -> None:
        if name not in self._fonts:
            raise ValueError(f"unknown font name: {name}")
        self._font_stack.append(name)

    def set_last_font(self) -> None:
        if len(self._font_stack) > 1:
            self._font_stack.pop()

    def render_text(self, text: str, colour=None, shadow: bool = False) -> Surface:
        text_colour = self.theme.text if colour is None else colour
        font = self._fonts[self._font_stack[-1]]
        text_bitmap = font.render(text, True, text_colour)
        if not shadow:
            return text_bitmap
        shadow_bitmap = font.render(text, True, self.theme.shadow)
        out = Surface((text_bitmap.get_width() + 1, text_bitmap.get_height() + 1), pygame.SRCALPHA)
        out.blit(shadow_bitmap, (1, 1))
        out.blit(text_bitmap, (0, 0))
        return out

    def build_disabled_bitmap(self, idle_bitmap: Surface) -> Surface:
        out = idle_bitmap.copy()
        wash = Surface(out.get_size(), pygame.SRCALPHA)
        wash.fill((50, 50, 50, 120))
        out.blit(wash, (0, 0))
        return out

    def build_interactive_visuals(self, style: str, text: str, rect: Rect) -> InteractiveVisuals:
        style_key = (style or "box").lower()
        idle = Surface((rect.width, rect.height), pygame.SRCALPHA)
        hover = Surface((rect.width, rect.height), pygame.SRCALPHA)
        armed = Surface((rect.width, rect.height), pygame.SRCALPHA)

        if style_key in ("round", "angle", "radio", "check"):
            idle_fill = self.theme.medium
            hover_fill = self.theme.light
            armed_fill = self.theme.dark
            for surf, fill in ((idle, idle_fill), (hover, hover_fill), (armed, armed_fill)):
                draw_rect(surf, fill, Rect(0, 0, rect.width, rect.height), 0)
                draw_rect(surf, self.theme.dark, Rect(0, 0, rect.width, rect.height), 2)
            if style_key == "angle":
                # Slanted accent strip.
                polygon(idle, self.theme.dark, [(0, 0), (8, 0), (0, 8)])
                polygon(hover, self.theme.dark, [(0, 0), (8, 0), (0, 8)])
                polygon(armed, self.theme.light, [(0, 0), (8, 0), (0, 8)])
            if style_key == "radio":
                r = min(rect.width, rect.height) // 4
                for surf in (idle, hover, armed):
                    circle(surf, self.theme.text, (r + 4, rect.height // 2), r, 1)
            if style_key == "check":
                for surf in (idle, hover, armed):
                    line(surf, self.theme.text, (6, rect.height // 2), (10, rect.height - 8), 2)
                    line(surf, self.theme.text, (10, rect.height - 8), (16, 6), 2)
        else:
            # Classic boxed button style.
            for surf, fill in ((idle, self.theme.medium), (hover, self.theme.light), (armed, self.theme.dark)):
                draw_rect(surf, fill, Rect(0, 0, rect.width, rect.height), 0)
                draw_rect(surf, self.theme.dark, Rect(0, 0, rect.width, rect.height), 2)
                line(surf, self.theme.light, (1, 1), (rect.width - 2, 1), 1)
                line(surf, self.theme.light, (1, 1), (1, rect.height - 2), 1)

        text_bitmap = self.render_text(text, colour=self.theme.text, shadow=True)
        text_rect = text_bitmap.get_rect(center=(rect.width // 2, rect.height // 2))
        for surf in (idle, hover, armed):
            surf.blit(text_bitmap, text_rect)
        disabled = self.build_disabled_bitmap(idle)
        return InteractiveVisuals(idle=idle, hover=hover, armed=armed, disabled=disabled, hit_rect=Rect(rect))

    def build_toggle_visuals(self, style: str, pushed_text: str, raised_text: Optional[str], rect: Rect):
        raised = pushed_text if raised_text is None else raised_text
        idle_set = self.build_interactive_visuals(style, raised, rect)
        armed_set = self.build_interactive_visuals(style, pushed_text, rect)
        return InteractiveVisuals(
            idle=idle_set.idle,
            hover=idle_set.hover,
            armed=armed_set.armed,
            disabled=idle_set.disabled,
            hit_rect=Rect(rect),
        )

    def build_frame_visuals(self, rect: Rect) -> InteractiveVisuals:
        idle = Surface((rect.width, rect.height), pygame.SRCALPHA)
        hover = Surface((rect.width, rect.height), pygame.SRCALPHA)
        armed = Surface((rect.width, rect.height), pygame.SRCALPHA)

        draw_rect(idle, self.theme.medium, Rect(0, 0, rect.width, rect.height), 0)
        draw_rect(hover, self.theme.light, Rect(0, 0, rect.width, rect.height), 0)
        draw_rect(armed, self.theme.dark, Rect(0, 0, rect.width, rect.height), 0)

        for surf in (idle, hover, armed):
            draw_rect(surf, self.theme.dark, Rect(0, 0, rect.width, rect.height), 2)

        return InteractiveVisuals(idle=idle, hover=hover, armed=armed, disabled=self.build_disabled_bitmap(idle), hit_rect=Rect(rect))

    def draw_radio_bitmap(self, size: int, col1, col2) -> Surface:
        out = Surface((size, size), pygame.SRCALPHA)
        circle(out, col1, (size // 2, size // 2), max(1, size // 2 - 1), 1)
        circle(out, col2, (size // 2, size // 2), max(1, size // 4), 0)
        return out

    def build_window_chrome_visuals(self, width: int, titlebar_height: int, title: str) -> WindowChromeVisuals:
        inactive = Surface((width, titlebar_height), pygame.SRCALPHA)
        active = Surface((width, titlebar_height), pygame.SRCALPHA)

        draw_rect(inactive, self.theme.medium, Rect(0, 0, width, titlebar_height), 0)
        draw_rect(active, self.theme.dark, Rect(0, 0, width, titlebar_height), 0)
        draw_rect(inactive, self.theme.dark, Rect(0, 0, width, titlebar_height), 2)
        draw_rect(active, self.theme.dark, Rect(0, 0, width, titlebar_height), 2)

        old = self.get_current_font_name()
        self.set_font("titlebar")
        try:
            inactive_text = self.render_text(title, colour=self.theme.highlight, shadow=True)
            active_text = self.render_text(title, colour=self.theme.text, shadow=True)
        finally:
            while self.get_current_font_name() != old:
                self.set_last_font()

        inactive.blit(inactive_text, (8, 2))
        active.blit(active_text, (8, 2))

        lower = Surface((14, 14), pygame.SRCALPHA)
        draw_rect(lower, self.theme.medium, Rect(0, 0, 14, 14), 0)
        draw_rect(lower, self.theme.dark, Rect(0, 0, 14, 14), 1)

        return WindowChromeVisuals(
            title_bar_inactive=inactive,
            title_bar_active=active,
            lower_widget=lower,
        )

    def draw_arrow_visuals(self, rect: Rect, direction: int):
        visuals = self.build_frame_visuals(rect)
        for surf in (visuals.idle, visuals.hover, visuals.armed):
            cx, cy = rect.width // 2, rect.height // 2
            deg = int(direction) % 360
            if deg in (90, 270):
                points = [(cx - 4, cy - 6), (cx + 4, cy - 6), (cx, cy + 6)]
                if deg == 270:
                    points = [(cx - 4, cy + 6), (cx + 4, cy + 6), (cx, cy - 6)]
            else:
                points = [(cx - 6, cy - 4), (cx - 6, cy + 4), (cx + 6, cy)]
                if deg == 180:
                    points = [(cx + 6, cy - 4), (cx + 6, cy + 4), (cx - 6, cy)]
            polygon(surf, self.theme.text, points)
        return visuals
