from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from math import cos, radians, sin
from time import perf_counter
from typing import Optional, Tuple

import pygame
from pygame import Rect, Surface
from pygame import PixelArray
from pygame.draw import circle, line, polygon, rect as draw_rect
from pygame.surfarray import blit_array
from pygame.transform import rotate, smoothscale

from ..core.first_frame_profiler import first_frame_profiler
from .built_in_definitions import BUILT_IN_COLOURS, draw_box_bitmap, draw_frame_bitmap


@dataclass
class InteractiveVisuals:
    idle: Surface
    hover: Surface
    armed: Surface
    disabled: Surface
    disabled_armed: Surface
    hidden: Surface
    hit_rect: Rect


@dataclass
class WindowChromeVisuals:
    title_bar_inactive: Surface
    title_bar_active: Surface
    lower_widget: Surface


class BuiltInGraphicsFactory:
    """Built-in bitmap factory for the control API."""

    def __init__(self, theme) -> None:
        self.theme = theme
        self.fonts = theme.fonts

    def font_revision(self) -> int:
        return self.fonts.revision

    def render_text(self, text: str, colour=None, shadow: bool = False, role_name: str = "body") -> Surface:
        text_colour = self.theme.text if colour is None else colour
        if not shadow:
            return self.fonts.render_text(text, text_colour, role_name=role_name)
        return self.fonts.render_text_with_shadow(text, text_colour, self.theme.shadow, role_name=role_name)

    @staticmethod
    def _centre(bigger: int, smaller: int) -> int:
        return int((bigger / 2) - (smaller / 2))

    def _flood_fill(self, surface: Surface, start: Tuple[int, int], colour: Tuple[int, int, int]) -> None:
        pixels: Optional[PixelArray] = None
        try:
            pixels = PixelArray(surface)
            new_colour = surface.map_rgb(colour)
            old_colour = pixels[start]
            if old_colour == new_colour:
                return
            width, height = surface.get_size()
            queue = deque([start])
            while queue:
                x, y = queue.popleft()
                if pixels[x, y] != old_colour:
                    continue
                pixels[x, y] = new_colour
                if x > 0:
                    queue.append((x - 1, y))
                if x < width - 1:
                    queue.append((x + 1, y))
                if y > 0:
                    queue.append((x, y - 1))
                if y < height - 1:
                    queue.append((x, y + 1))
            blit_array(surface, pixels)
        finally:
            if pixels is not None:
                del pixels

    def build_disabled_bitmap(self, idle_bitmap: Surface) -> Surface:
        out = idle_bitmap.copy()
        out.fill((160, 160, 160, 255), special_flags=pygame.BLEND_RGBA_MULT)
        return out

    def build_hidden_bitmap(self, size: Tuple[int, int]) -> Surface:
        return Surface(size, pygame.SRCALPHA)

    def resolve_visual_state(
        self,
        visuals: InteractiveVisuals,
        *,
        visible: bool,
        enabled: bool,
        armed: bool,
        hovered: bool,
    ) -> Surface:
        if not visible:
            return visuals.hidden
        if not enabled:
            return visuals.disabled_armed if armed else visuals.disabled
        if armed:
            return visuals.armed
        if hovered:
            return visuals.hover
        return visuals.idle

    def _draw_built_in_button_surface(self, text: str, rect: Rect, state: str, *, font_role: str = "body", highlight: bool = False) -> Surface:
        width, height = rect.size
        surface = Surface((width, height)).convert()
        draw_box_bitmap(surface, state, Rect(0, 0, width, height), BUILT_IN_COLOURS)
        text_bitmap = self.render_text(text, colour=self.theme.highlight if highlight else self.theme.text, shadow=True, role_name=font_role)
        text_rect = text_bitmap.get_rect(center=(width // 2, height // 2 - 1))
        surface.blit(text_bitmap, text_rect)
        return surface

    def _draw_angle_state(self, size: Tuple[int, int], state: str) -> Surface:
        if state == "hover":
            return self._draw_angle_style_bitmap(size, BUILT_IN_COLOURS["light"], BUILT_IN_COLOURS["light"])
        if state == "armed":
            return self._draw_angle_style_bitmap(size, BUILT_IN_COLOURS["none"], BUILT_IN_COLOURS["dark"])
        return self._draw_angle_style_bitmap(size, BUILT_IN_COLOURS["light"], BUILT_IN_COLOURS["medium"])

    def _draw_angle_style_bitmap(self, size: Tuple[int, int], border, background) -> Surface:
        width, height = size
        supersampled = Surface((width * 10, height * 10), pygame.SRCALPHA).convert_alpha()
        _, _, sw, sh = supersampled.get_rect()
        bevel = sh // 3
        points = (
            (bevel, 0),
            (sw - bevel, 0),
            (sw - 1, bevel),
            (sw - 1, sh - bevel - 1),
            (sw - bevel, sh - 1),
            (bevel, sh - 1),
            (0, sh - bevel),
            (0, bevel),
            (bevel, 0),
        )
        polygon(supersampled, background, points, 0)
        polygon(supersampled, border, points, max(1, bevel // 4))
        return smoothscale(supersampled, (width, height))

    def _draw_rounded_state(self, surface: Surface, state: str) -> None:
        if state == "hover":
            self._draw_round_style_bitmap(surface, BUILT_IN_COLOURS["light"], BUILT_IN_COLOURS["light"])
            return
        if state == "armed":
            self._draw_round_style_bitmap(surface, BUILT_IN_COLOURS["none"], BUILT_IN_COLOURS["dark"])
            return
        self._draw_round_style_bitmap(surface, BUILT_IN_COLOURS["light"], BUILT_IN_COLOURS["medium"])

    def _draw_round_style_bitmap(self, surface: Surface, border, background) -> None:
        _, _, width, height = surface.get_rect()
        radius = max(2, height // 4)
        circle(surface, border, (radius, radius), radius, 1, draw_top_left=True)
        circle(surface, border, (width - radius, radius), radius, 1, draw_top_right=True)
        line(surface, border, (radius, 0), (width - radius, 0), 1)
        circle(surface, border, (radius, height - radius), radius, 1, draw_bottom_left=True)
        circle(surface, border, (width - radius, height - radius), radius, 1, draw_bottom_right=True)
        line(surface, border, (radius, height - 1), (width - radius, height - 1), 1)
        line(surface, border, (0, radius), (0, height - radius), 1)
        line(surface, border, (width - 1, radius), (width - 1, height - radius), 1)
        self._flood_fill(surface, (width // 2, height // 2), background)

    def _draw_round_button_surface(self, text: str, rect: Rect, state: str, *, font_role: str = "body", highlight: bool = False) -> Surface:
        width, height = rect.size
        surface = Surface((width, height), pygame.SRCALPHA).convert_alpha()
        self._draw_rounded_state(surface, state)
        text_bitmap = self.render_text(text, colour=self.theme.highlight if highlight else self.theme.text, shadow=True, role_name=font_role)
        text_rect = text_bitmap.get_rect(center=(width // 2, height // 2))
        surface.blit(text_bitmap, text_rect)
        return surface

    def _draw_angle_button_surface(self, text: str, rect: Rect, state: str, *, font_role: str = "body", highlight: bool = False) -> Surface:
        width, height = rect.size
        surface = self._draw_angle_state((width, height), state)
        text_bitmap = self.render_text(text, colour=self.theme.highlight if highlight else self.theme.text, shadow=True, role_name=font_role)
        text_rect = text_bitmap.get_rect(center=(width // 2, height // 2))
        surface.blit(text_bitmap, text_rect)
        return surface

    def _draw_check_bitmap(self, state: int, size: int) -> Surface:
        shrink = int(size * 0.65)
        offset = self._centre(size, shrink)
        box_bitmap = Surface((shrink, shrink)).convert()
        if state == 2:
            draw_box_bitmap(box_bitmap, "armed", Rect(0, 0, shrink, shrink), BUILT_IN_COLOURS)
        elif state == 1:
            draw_box_bitmap(box_bitmap, "hover", Rect(0, 0, shrink, shrink), BUILT_IN_COLOURS)
        else:
            draw_box_bitmap(box_bitmap, "idle", Rect(0, 0, shrink, shrink), BUILT_IN_COLOURS)

        complete = Surface((size, size), pygame.SRCALPHA).convert_alpha()
        complete.blit(box_bitmap, (offset, offset))
        if state in (1, 2):
            glyph = Surface((400, 400), pygame.SRCALPHA).convert_alpha()
            points = ((20, 200), (80, 140), (160, 220), (360, 0), (400, 60), (160, 320), (20, 200))
            polygon(glyph, BUILT_IN_COLOURS["full"], points, 0)
            polygon(glyph, BUILT_IN_COLOURS["none"], points, 20)
            complete.blit(smoothscale(glyph, (size, size)), (0, 0))
        return complete

    def _draw_check_style_surface(self, text: str, rect: Rect, state: int, *, font_role: str = "body", highlight: bool = False) -> Surface:
        text_bitmap = self.render_text(text, colour=self.theme.highlight if highlight else self.theme.text, shadow=True, role_name=font_role)
        _, _, _, text_height = text_bitmap.get_rect()
        y_offset = self._centre(rect.height, text_height)
        complete = Surface((rect.width, rect.height), pygame.SRCALPHA).convert_alpha()
        complete.blit(self._draw_check_bitmap(state, text_height), (0, y_offset))
        complete.blit(text_bitmap, (text_height + 2, y_offset))
        return complete

    def _draw_radio_style_surface(self, text: str, rect: Rect, col1, col2, *, font_role: str = "body", highlight: bool = False) -> Surface:
        text_bitmap = self.render_text(text, colour=self.theme.highlight if highlight else self.theme.text, shadow=True, role_name=font_role)
        _, _, _, text_height = text_bitmap.get_rect()
        y_offset = self._centre(rect.height, text_height)
        complete = Surface((rect.width, rect.height), pygame.SRCALPHA).convert_alpha()
        radio_bitmap = self.draw_radio_bitmap(text_height, col1, col2)
        complete.blit(radio_bitmap, (0, y_offset))
        complete.blit(text_bitmap, (text_height + 2, y_offset))
        return complete

    def _draw_radio_pushbutton(self, text: str, rect: Rect, col1, col2, *, font_role: str = "body", highlight: bool = False) -> Surface:
        return self._draw_radio_style_surface(text, rect, col1, col2, font_role=font_role, highlight=highlight)

    def build_interactive_visuals(self, style: str, text: str, rect: Rect, *, font_role: str = "body") -> InteractiveVisuals:
        start = perf_counter()
        style_key = (style or "box").lower()
        if style_key == "radio":
            idle = self._draw_radio_style_surface(text, rect, BUILT_IN_COLOURS["light"], BUILT_IN_COLOURS["dark"], font_role=font_role, highlight=False)
            hover = self._draw_radio_style_surface(text, rect, BUILT_IN_COLOURS["full"], BUILT_IN_COLOURS["none"], font_role=font_role, highlight=False)
            armed = self._draw_radio_style_surface(text, rect, BUILT_IN_COLOURS["highlight"], BUILT_IN_COLOURS["dark"], font_role=font_role, highlight=False)
        elif style_key == "round":
            idle = self._draw_round_button_surface(text, rect, "idle", font_role=font_role, highlight=False)
            hover = self._draw_round_button_surface(text, rect, "hover", font_role=font_role, highlight=False)
            armed = self._draw_round_button_surface(text, rect, "armed", font_role=font_role, highlight=True)
        elif style_key == "angle":
            idle = self._draw_angle_button_surface(text, rect, "idle", font_role=font_role, highlight=False)
            hover = self._draw_angle_button_surface(text, rect, "hover", font_role=font_role, highlight=False)
            armed = self._draw_angle_button_surface(text, rect, "armed", font_role=font_role, highlight=True)
        elif style_key == "check":
            idle = self._draw_check_style_surface(text, rect, 0, font_role=font_role, highlight=False)
            hover = self._draw_check_style_surface(text, rect, 1, font_role=font_role, highlight=False)
            armed = self._draw_check_style_surface(text, rect, 2, font_role=font_role, highlight=False)
        else:
            idle = self._draw_built_in_button_surface(text, rect, "idle", font_role=font_role, highlight=False)
            hover = self._draw_built_in_button_surface(text, rect, "hover", font_role=font_role, highlight=False)
            armed = self._draw_built_in_button_surface(text, rect, "armed", font_role=font_role, highlight=True)

        disabled = self.build_disabled_bitmap(idle)
        disabled_armed = self.build_disabled_bitmap(armed)
        hidden = self.build_hidden_bitmap((idle.get_width(), idle.get_height()))
        first_frame_profiler().record_once(
            "visual.interactive",
            f"{style_key}:{font_role}:{rect.width}x{rect.height}:{text}",
            (perf_counter() - start) * 1000.0,
            detail="build_interactive_visuals",
        )
        return InteractiveVisuals(idle=idle, hover=hover, armed=armed, disabled=disabled, disabled_armed=disabled_armed, hidden=hidden, hit_rect=Rect(rect))

    def build_toggle_visuals(self, style: str, pushed_text: str, raised_text: Optional[str], rect: Rect, *, font_role: str = "body") -> InteractiveVisuals:
        start = perf_counter()
        raised = pushed_text if raised_text is None else raised_text
        idle_set = self.build_interactive_visuals(style, raised, rect, font_role=font_role)
        armed_set = self.build_interactive_visuals(style, pushed_text, rect, font_role=font_role)
        first_frame_profiler().record_once(
            "visual.toggle",
            f"{(style or 'box').lower()}:{font_role}:{rect.width}x{rect.height}:{raised}->{pushed_text}",
            (perf_counter() - start) * 1000.0,
            detail="build_toggle_visuals",
        )
        return InteractiveVisuals(
            idle=idle_set.idle,
            hover=idle_set.hover,
            armed=armed_set.armed,
            disabled=idle_set.disabled,
            disabled_armed=armed_set.disabled_armed,
            hidden=idle_set.hidden,
            hit_rect=Rect(rect),
        )

    def build_frame_visuals(self, rect: Rect) -> InteractiveVisuals:
        start = perf_counter()
        width, height = rect.size
        idle = Surface((width, height)).convert()
        hover = Surface((width, height)).convert()
        armed = Surface((width, height)).convert()
        draw_box_bitmap(idle, "idle", Rect(0, 0, width, height), BUILT_IN_COLOURS)
        draw_box_bitmap(hover, "hover", Rect(0, 0, width, height), BUILT_IN_COLOURS)
        draw_box_bitmap(armed, "armed", Rect(0, 0, width, height), BUILT_IN_COLOURS)
        disabled = self.build_disabled_bitmap(idle)
        disabled_armed = self.build_disabled_bitmap(armed)
        hidden = self.build_hidden_bitmap((width, height))
        first_frame_profiler().record_once(
            "visual.frame",
            f"{width}x{height}",
            (perf_counter() - start) * 1000.0,
            detail="build_frame_visuals",
        )
        return InteractiveVisuals(idle=idle, hover=hover, armed=armed, disabled=disabled, disabled_armed=disabled_armed, hidden=hidden, hit_rect=Rect(rect))

    def draw_radio_bitmap(self, size: int, col1, col2) -> Surface:
        supersampled = Surface((400, 400), pygame.SRCALPHA).convert_alpha()
        centre_point = 200
        radius = 128
        points = []
        for point in range(0, 360, 5):
            x1 = int(round(radius * cos(radians(point))))
            y1 = int(round(radius * sin(radians(point))))
            points.append((centre_point + x1, centre_point + y1))
        polygon(supersampled, col1, points, 0)
        polygon(supersampled, col2, points, 24)
        return smoothscale(supersampled, (size, size))

    def draw_window_lower_widget_bitmap(self, size: int, col1, col2) -> Surface:
        surface = Surface((size, size), pygame.SRCALPHA).convert_alpha()
        draw_box_bitmap(surface, "idle", Rect(0, 0, size, size), BUILT_IN_COLOURS)
        gutter = max(1, int(size * 0.1) // 2)
        panel_size = int(size * 0.45)
        offset = int(size * 0.2)
        offset_b = max(1, offset // 2)
        base = self._centre(size, panel_size + offset)
        panel1 = Rect(base, base - gutter, panel_size + offset_b, panel_size + gutter + offset_b)
        panel2 = Rect(base + offset, base + gutter + offset_b, panel_size + offset_b, panel_size + gutter + offset_b)
        draw_rect(surface, col1, panel1)
        draw_rect(surface, BUILT_IN_COLOURS["none"], panel1, 1)
        draw_rect(surface, col2, panel2)
        draw_rect(surface, BUILT_IN_COLOURS["none"], panel2, 1)
        return surface

    def build_window_chrome_visuals(self, width: int, titlebar_height: int, title: str, *, title_font_role: str = "title") -> WindowChromeVisuals:
        start = perf_counter()
        title_font = self.fonts.get_font(title_font_role)
        font_based_height = max(18, title_font.get_linesize() + 8)
        chrome_height = max(2, font_based_height)

        inactive = Surface((width, chrome_height)).convert()
        active = Surface((width, chrome_height)).convert()

        draw_frame_bitmap(
            inactive,
            BUILT_IN_COLOURS["none"],
            BUILT_IN_COLOURS["dark"],
            BUILT_IN_COLOURS["none"],
            BUILT_IN_COLOURS["full"],
            BUILT_IN_COLOURS["dark"],
            Rect(0, 0, width, chrome_height),
        )
        draw_frame_bitmap(
            active,
            BUILT_IN_COLOURS["light"],
            BUILT_IN_COLOURS["dark"],
            BUILT_IN_COLOURS["full"],
            BUILT_IN_COLOURS["none"],
            BUILT_IN_COLOURS["dark"],
            Rect(0, 0, width, chrome_height),
        )

        inactive_text = self.render_text(title, colour=self.theme.text, shadow=True, role_name=title_font_role)
        active_text = self.render_text(title, colour=self.theme.highlight, shadow=True, role_name=title_font_role)

        inactive_y = self._centre(chrome_height, inactive_text.get_rect().height)
        active_y = self._centre(chrome_height, active_text.get_rect().height)
        inactive.blit(inactive_text, (5, inactive_y))
        active.blit(active_text, (5, active_y))

        lower = self.draw_window_lower_widget_bitmap(chrome_height, BUILT_IN_COLOURS["full"], BUILT_IN_COLOURS["medium"])

        first_frame_profiler().record_once(
            "visual.window_chrome",
            f"{title_font_role}:{width}x{chrome_height}:{title}",
            (perf_counter() - start) * 1000.0,
            detail="build_window_chrome_visuals",
        )

        return WindowChromeVisuals(title_bar_inactive=inactive, title_bar_active=active, lower_widget=lower)

    def draw_arrow_visuals(self, rect: Rect, direction: int) -> InteractiveVisuals:
        visuals = self.build_frame_visuals(rect)
        size = min(rect.width, rect.height)
        glyph = Surface((400, 400), pygame.SRCALPHA).convert_alpha()
        points = ((350, 200), (100, 350), (100, 240), (50, 240), (50, 160), (100, 160), (100, 50), (350, 200))
        polygon(glyph, BUILT_IN_COLOURS["full"], points, 0)
        polygon(glyph, BUILT_IN_COLOURS["none"], points, 20)
        glyph = rotate(glyph, int(direction) % 360)
        glyph = smoothscale(glyph, (size, size))
        glyph_x = self._centre(rect.width, size)
        glyph_y = self._centre(rect.height, size)
        for surf in (visuals.idle, visuals.hover, visuals.armed):
            surf.blit(glyph, (glyph_x, glyph_y))
        # Disabled state should include the arrow glyph as a dimmed variant of idle.
        visuals.disabled = self.build_disabled_bitmap(visuals.idle)
        return visuals
