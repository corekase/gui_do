import os
import pygame
from math import cos, sin, radians
from pygame.surface import Surface
from pygame.surfarray import blit_array
from collections import deque
from pygame import Rect, PixelArray, SRCALPHA
from pygame.draw import rect, line, polygon, circle
from pygame.transform import rotate, smoothscale
from typing import Dict, List, Optional, Tuple, TYPE_CHECKING
from ..events import colours, GuiError, ButtonStyle
from ..resource_error import DataResourceErrorHandler
from .button_style_strategies import build_default_button_style_strategies
from .cursor_asset import CursorAsset
from .interactive_visuals import InteractiveVisuals
from .window_chrome_visuals import WindowChromeVisuals

if TYPE_CHECKING:
    from ..gui_manager import GuiManager


class WidgetGraphicsFactory:
    _cursor_cache: Dict[str, CursorAsset] = {}
    _data_root: str = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'data'))

    def __init__(self) -> None:
        self._font: Optional[pygame.font.Font] = None
        self._current_font_name: Optional[str] = None
        self._last_font_name: Optional[str] = None
        self._fonts: Dict[str, pygame.font.Font] = {}
        self._style_strategies = build_default_button_style_strategies()

    def get_current_font_name(self) -> Optional[str]:
        return self._current_font_name

    def get_cursor(self, name: str) -> CursorAsset:
        if name not in WidgetGraphicsFactory._cursor_cache:
            raise GuiError(f'unknown cursor "{name}"')
        return WidgetGraphicsFactory._cursor_cache[name]

    def build_interactive_visuals(self, style: ButtonStyle, text: Optional[str], rect: Rect) -> InteractiveVisuals:
        bitmaps, hit_rect = self.get_styled_bitmaps(style, text, rect)
        idle, hover, armed = bitmaps
        return InteractiveVisuals(idle=idle, hover=hover, armed=armed, hit_rect=hit_rect)

    def build_toggle_visuals(
        self,
        style: ButtonStyle,
        pressed_text: str,
        raised_text: Optional[str],
        rect: Rect,
    ) -> InteractiveVisuals:
        if raised_text is None:
            raised_text = pressed_text
        pressed_visuals = self.build_interactive_visuals(style, pressed_text, rect)
        raised_visuals = self.build_interactive_visuals(style, raised_text, rect)
        hit_rect = raised_visuals.hit_rect
        if pressed_visuals.hit_rect.width > hit_rect.width:
            hit_rect = pressed_visuals.hit_rect
        return InteractiveVisuals(
            idle=raised_visuals.idle,
            hover=raised_visuals.hover,
            armed=pressed_visuals.armed,
            hit_rect=hit_rect,
        )

    def build_frame_visuals(self, rect: Rect) -> InteractiveVisuals:
        idle, hover, armed = self.draw_frame_bitmaps(rect)
        return InteractiveVisuals(idle=idle, hover=hover, armed=armed, hit_rect=rect)

    def build_window_chrome_visuals(self, gui: "GuiManager", title: str, width: int, titlebar_size: int) -> WindowChromeVisuals:
        inactive, active = self.draw_window_title_bar_bitmaps(gui, title, width, titlebar_size)
        lower = self.draw_window_lower_widget_bitmap(titlebar_size - 2, colours['full'], colours['medium'])
        return WindowChromeVisuals(
            title_bar_inactive=inactive,
            title_bar_active=active,
            lower_widget=lower,
        )

    def get_styled_bitmaps(self, style: ButtonStyle, text: Optional[str], rect: Rect) -> Tuple[Tuple[Surface, Surface, Surface], Rect]:
        strategy = self._style_strategies.get(style)
        if strategy is None:
            raise GuiError('style not implemented')
        return strategy.render(self, text, rect)

    def set_font(self, name: str) -> None:
        if name not in self._fonts:
            raise GuiError(f'unknown font "{name}"')
        self._last_font_name = self._current_font_name
        self._font = self._fonts[name]
        self._current_font_name = name

    def set_last_font(self) -> None:
        if self._last_font_name is not None:
            if self._last_font_name not in self._fonts:
                raise GuiError(f'unknown previous font "{self._last_font_name}"')
            self._font = self._fonts[self._last_font_name]
            self._current_font_name = self._last_font_name

    def get_font_height(self, name: str, shadow: bool = False) -> int:
        if name not in self._fonts:
            raise GuiError(f'unknown font "{name}"')
        height = self._fonts[name].get_linesize()
        if shadow:
            # render_text() offsets the optional shadow by one pixel in both axes.
            height += 1
        return height

    def get_titlebar_height(self, padding: int = 6) -> int:
        if not isinstance(padding, int) or padding < 0:
            raise GuiError(f'titlebar padding must be a non-negative int, got: {padding}')
        return self.get_font_height('titlebar', shadow=True) + padding

    def draw_arrow_state_bitmaps(self, rect: Rect, direction: float) -> List[Surface]:
        try:
            states = self.draw_frame_bitmaps(rect)
            glyph_set: List[Surface] = []
            if rect.width <= rect.height:
                size = rect.width
            else:
                size = rect.height
            glyph = Surface((400, 400), SRCALPHA).convert_alpha()
            points = ((350, 200), (100, 350), (100, 240), (50, 240), (50, 160), (100, 160), (100, 50), (350, 200))
            polygon(glyph, colours['full'], points, 0)
            polygon(glyph, colours['none'], points, 20)
            glyph = rotate(glyph, direction)
            glyph = smoothscale(glyph, (size, size))
            glyph_x = self.centre(rect.width, size)
            glyph_y = self.centre(rect.height, size)
            for state in states:
                state.blit(glyph, (glyph_x, glyph_y))
                glyph_set.append(state)
            return glyph_set
        except GuiError:
            raise
        except Exception as exc:
            raise GuiError(f'failed to draw arrow state bitmaps for rect={rect} direction={direction}') from exc

    def draw_frame_bitmaps(self, rect: Rect) -> Tuple[Surface, Surface, Surface]:
        try:
            _, _, w, h = rect
            saved: List[Surface] = []
            idle_surface = Surface((w, h)).convert()
            self._draw_box_bitmaps(idle_surface, 'idle')
            saved.append(idle_surface)
            hover_surface = Surface((w, h)).convert()
            self._draw_box_bitmaps(hover_surface, 'hover')
            saved.append(hover_surface)
            armed_surface = Surface((w, h)).convert()
            self._draw_box_bitmaps(armed_surface, 'armed')
            saved.append(armed_surface)
            return tuple(saved)  # type: ignore
        except GuiError:
            raise
        except Exception as exc:
            raise GuiError(f'failed to draw frame bitmaps for rect={rect}') from exc

    def draw_radio_bitmap(self, size: int, col1: Tuple[int, int, int], col2: Tuple[int, int, int]) -> Surface:
        try:
            radio_bitmap = Surface((400, 400), SRCALPHA).convert_alpha()
            centre_point = 200
            radius = 128
            points: List[Tuple[int, int]] = []
            for point in range(0, 360, 5):
                x1 = int(round(radius * cos(radians(point))))
                y1 = int(round(radius * sin(radians(point))))
                points.append((centre_point + x1, centre_point + y1))
            polygon(radio_bitmap, col1, points, 0)
            polygon(radio_bitmap, col2, points, 24)
            radio_bitmap = smoothscale(radio_bitmap, (size, size))
            return radio_bitmap
        except GuiError:
            raise
        except Exception as exc:
            raise GuiError(f'failed to draw radio bitmap for size={size}') from exc

    def draw_window_lower_widget_bitmap(self, size: int, col1: Tuple[int, int, int], col2: Tuple[int, int, int]) -> Surface:
        try:
            surface = Surface((size, size), SRCALPHA).convert_alpha()
            self._draw_box_bitmaps(surface, 'idle')
            gutter = int(size * 0.1) // 2
            panel_size = int(size * 0.45)
            offset = int(size * 0.2)
            offsetb = offset // 2
            base = self.centre(size, (panel_size + offset))
            panel1 = Rect(base, base - gutter, panel_size + offsetb, panel_size + gutter + offsetb)
            panel2 = Rect(base + offset, base + gutter + offsetb, panel_size + offsetb, panel_size + gutter + offsetb)
            rect(surface, col1, panel1)
            rect(surface, colours['none'], panel1, 1)
            rect(surface, col2, panel2)
            rect(surface, colours['none'], panel2, 1)
            return surface
        except GuiError:
            raise
        except Exception as exc:
            raise GuiError(f'failed to draw window lower widget bitmap for size={size}') from exc

    def draw_window_title_bar_bitmaps(self, gui: "GuiManager", title: str, width: int, size: int) -> Tuple[Surface, Surface]:
        try:
            saved: List[Surface] = []
            saved.append(self._draw_window_title_bar_bitmap(gui, title, width, size, colours['full']))
            saved.append(self._draw_window_title_bar_bitmap(gui, title, width, size, colours['highlight']))
            return tuple(saved)  # type: ignore
        except GuiError:
            raise
        except Exception as exc:
            raise GuiError(f'failed to draw window title bar bitmaps for title="{title}"') from exc

    def render_text(self, text: str, colour: Tuple[int, int, int] = colours['text'], shadow: bool = False, shadow_colour: Tuple[int, int, int] = colours['none']) -> Surface:
        try:
            if self._font is None:
                raise GuiError('no active font set; call set_font() before render_text()')
            text_bitmap = self._font.render(text, True, colour, None)
            text_rect = text_bitmap.get_rect()
            w, h = text_rect.width, text_rect.height
            if shadow:
                w += 1
                h += 1
            bitmap = pygame.Surface((w, h), pygame.SRCALPHA)
            if shadow:
                shadow_bitmap = self._font.render(text, True, shadow_colour, None)
                bitmap.blit(shadow_bitmap, (1, 1))
            bitmap.blit(text_bitmap, (0, 0))
            return bitmap
        except GuiError:
            raise
        except Exception as exc:
            raise GuiError(f'failed to render text: {text!r}') from exc
    def centre(self, bigger: int, smaller: int) -> int:
        return int((bigger / 2) - (smaller / 2))

    def file_resource(self, *names: str) -> str:
        if len(names) == 0:
            raise GuiError('resource path must include at least one path component')
        for name in names:
            if not isinstance(name, str) or name == '':
                raise GuiError(f'resource path components must be non-empty strings, got: {name!r}')
            if os.path.isabs(name):
                raise GuiError(f'resource path component cannot be absolute: {name!r}')
        resource_path = os.path.normpath(os.path.join(self._data_root, *names))
        try:
            common_root = os.path.commonpath([self._data_root, resource_path])
        except ValueError as exc:
            raise GuiError(f'invalid resource path: {names!r}') from exc
        if common_root != self._data_root:
            raise GuiError(f'resource path escapes data directory: {names!r}')
        return resource_path

    def image_alpha(self, *names: str) -> Surface:
        full_path = os.path.normpath(os.path.abspath(self.file_resource(*names)))
        try:
            return pygame.image.load(full_path).convert_alpha()
        except GuiError:
            raise
        except (pygame.error, FileNotFoundError, OSError, TypeError, ValueError, RuntimeError) as exc:
            DataResourceErrorHandler.raise_load_error('failed to load image resource', full_path, exc)

    def register_cursor(self, *, name: str, filename: str, hotspot: Tuple[int, int]) -> CursorAsset:
        if not isinstance(hotspot, tuple) or len(hotspot) != 2:
            raise GuiError(f'hotspot must be a tuple of (x, y), got: {hotspot}')
        if not isinstance(name, str) or name == '':
            raise GuiError('cursor name must be a non-empty string')
        if not isinstance(filename, str) or filename == '':
            raise GuiError('cursor filename must be a non-empty string')
        cursor_path = self.file_resource('cursors', filename)
        try:
            asset = CursorAsset(
                name=name,
                image=self.image_alpha('cursors', filename),
                hotspot=hotspot,
                source_path=cursor_path,
            )
            WidgetGraphicsFactory._cursor_cache[name] = asset
            return asset
        except GuiError:
            raise
        except (pygame.error, FileNotFoundError, OSError, TypeError, ValueError, RuntimeError) as exc:
            DataResourceErrorHandler.raise_load_error(f'failed to load cursor "{name}" from file', cursor_path, exc)

    def load_font(self, name: str, font: str, size: int) -> None:
        font_full_path = os.path.normpath(os.path.abspath(self.file_resource('fonts', font)))
        try:
            self._fonts[name] = pygame.font.Font(font_full_path, size)
        except GuiError:
            raise
        except (pygame.error, FileNotFoundError, OSError, TypeError, ValueError, RuntimeError) as exc:
            DataResourceErrorHandler.raise_load_error(
                f'failed to load font "{name}" from file with size={size}',
                font_full_path,
                exc,
            )

    def _draw_angle_state(self, size: Tuple[int, int], state: str) -> Surface:
        if state == 'idle':
            return self._draw_angle_style_bitmap(size, colours['light'], colours['medium'])
        elif state == 'hover':
            return self._draw_angle_style_bitmap(size, colours['light'], colours['light'])
        elif state == 'armed':
            return self._draw_angle_style_bitmap(size, colours['none'], colours['dark'])
        return self._draw_angle_style_bitmap(size, colours['light'], colours['medium'])

    def _draw_angle_style_bitmap(self, size: Tuple[int, int], border: Tuple[int, int, int], background: Tuple[int, int, int]) -> Surface:
        try:
            w_surface, h_surface = size
            angle_bitmap = Surface((w_surface * 10, h_surface * 10), SRCALPHA).convert_alpha()
            _, _, w, h = angle_bitmap.get_rect()
            dist = h // 3
            points = ((dist, 0), (w - dist, 0), (w - 1, dist), (w - 1, h - dist - 1), (w - dist, h - 1), (dist, h - 1), (0, h - dist), (0, dist), (dist, 0))
            polygon(angle_bitmap, background, points, 0)
            polygon(angle_bitmap, border, points, dist // 4)
            return smoothscale(angle_bitmap, (w_surface, h_surface))
        except GuiError:
            raise
        except Exception as exc:
            raise GuiError(f'failed to draw angle style bitmap for size={size}') from exc

    def _draw_angle_style_bitmaps(self, text: Optional[str], rect: Rect) -> Tuple[Tuple[Surface, Surface, Surface], Rect]:
        try:
            text = '' if text is None else text
            _, _, w, h = rect
            saved: List[Surface] = []
            text_bitmap = self.render_text(text, colours['text'], True)
            text_x = self.centre(w, text_bitmap.get_rect().width)
            text_y = self.centre(h, text_bitmap.get_rect().height)
            idle_surface = self._draw_angle_state((w, h), 'idle')
            idle_surface.blit(text_bitmap, (text_x, text_y))
            saved.append(idle_surface)
            hover_surface = self._draw_angle_state((w, h), 'hover')
            hover_surface.blit(text_bitmap, (text_x, text_y))
            saved.append(hover_surface)
            text_bitmap = self.render_text(text, colours['highlight'], True)
            text_x = self.centre(w, text_bitmap.get_rect().width)
            text_y = self.centre(h, text_bitmap.get_rect().height)
            armed_surface = self._draw_angle_state((w, h), 'armed')
            armed_surface.blit(text_bitmap, (text_x, text_y))
            saved.append(armed_surface)
            return tuple(saved), rect  # type: ignore
        except GuiError:
            raise
        except Exception as exc:
            raise GuiError(f'failed to draw angle style bitmaps for rect={rect} text={text!r}') from exc

    def _draw_box_bitmap(self, surface: Surface, ul: Tuple[int, int, int], lr: Tuple[int, int, int], ul_d: Tuple[int, int, int], lr_d: Tuple[int, int, int], background: Tuple[int, int, int]) -> None:
        locked = False
        try:
            _, _, width, height = surface.get_rect()
            if width <= 0 or height <= 0:
                return
            x = y = 0
            surface.lock()
            locked = True
            rect(surface, background, surface.get_rect(), 0)
            line(surface, ul, (x, y), (x + width - 1, y))
            line(surface, ul, (x, y), (x, y + height - 1))
            line(surface, lr, (x, y + height - 1), (x + width - 1, y + height - 1))
            line(surface, lr, (x + width - 1, y - 1), (x + width - 1, y + height - 1))
            if width > 1 and height > 1:
                surface.set_at((x + 1, y + 1), ul_d)
            if width > 2 and height > 2:
                surface.set_at((x + width - 2, y + height - 2), lr_d)
        except GuiError:
            raise
        except Exception as exc:
            raise GuiError('failed to draw box bitmap') from exc
        finally:
            if locked:
                surface.unlock()

    def _draw_box_bitmaps(self, surface: Surface, state: str) -> None:
        if state == 'idle':
            self._draw_box_bitmap(surface, colours['light'], colours['dark'], colours['full'], colours['none'], colours['medium'])
        elif state == 'hover':
            self._draw_box_bitmap(surface, colours['light'], colours['dark'], colours['full'], colours['none'], colours['light'])
        elif state == 'armed':
            self._draw_box_bitmap(surface, colours['none'], colours['light'], colours['none'], colours['full'], colours['dark'])

    def _draw_box_style_bitmaps(self, text: Optional[str], rect: Rect) -> Tuple[Tuple[Surface, Surface, Surface], Rect]:
        try:
            text = '' if text is None else text
            _, _, w, h = rect
            saved: List[Surface] = []
            text_bitmap = self.render_text(text, colours['text'], True)
            text_x = self.centre(w, text_bitmap.get_rect().width)
            text_y = self.centre(h, text_bitmap.get_rect().height)
            idle_surface = Surface((w, h)).convert()
            self._draw_box_bitmaps(idle_surface, 'idle')
            idle_surface.blit(text_bitmap, (text_x, text_y))
            saved.append(idle_surface)
            hover_surface = Surface((w, h)).convert()
            self._draw_box_bitmaps(hover_surface, 'hover')
            hover_surface.blit(text_bitmap, (text_x, text_y))
            saved.append(hover_surface)
            text_bitmap = self.render_text(text, colours['highlight'], True)
            text_x = self.centre(w, text_bitmap.get_rect().width)
            text_y = self.centre(h, text_bitmap.get_rect().height)
            armed_surface = Surface((w, h)).convert()
            self._draw_box_bitmaps(armed_surface, 'armed')
            armed_surface.blit(text_bitmap, (text_x, text_y))
            saved.append(armed_surface)
            return tuple(saved), rect  # type: ignore
        except GuiError:
            raise
        except Exception as exc:
            raise GuiError(f'failed to draw box style bitmaps for rect={rect} text={text!r}') from exc

    def _draw_check_bitmap(self, state: int, size: int) -> Surface:
        try:
            shrink = size * 0.65
            offset = int(self.centre(size, shrink))
            box_bitmap = Surface((int(shrink), int(shrink))).convert()
            check_bitmap = Surface((size, size), SRCALPHA).convert_alpha()
            if state == 0:
                self._draw_box_bitmaps(box_bitmap, 'idle')
            elif state == 1:
                self._draw_box_bitmaps(box_bitmap, 'hover')
            elif state == 2:
                self._draw_box_bitmaps(box_bitmap, 'armed')
            check_bitmap.blit(box_bitmap, (offset, offset))
            if state == 1 or state == 2:
                glyph = Surface((400, 400), SRCALPHA).convert_alpha()
                points = ((20, 200), (80, 140), (160, 220), (360, 0), (400, 60), (160, 320), (20, 200))
                polygon(glyph, colours['full'], points, 0)
                polygon(glyph, colours['none'], points, 20)
                glyph = smoothscale(glyph, (size, size))
                check_bitmap.blit(glyph, (0, 0))
            return check_bitmap
        except GuiError:
            raise
        except Exception as exc:
            raise GuiError(f'failed to draw check bitmap for state={state} size={size}') from exc

    def _draw_check_style_bitmap(self, rect: Rect, state: int, text: Optional[str]) -> Tuple[Surface, Rect]:
        try:
            text = '' if text is None else text
            text_bitmap = self.render_text(text, colours['text'], True)
            _, _, text_width, text_height = text_bitmap.get_rect()
            check_bitmap = self._draw_check_bitmap(state, text_height)
            y_offset = self.centre(rect.height, text_height)
            gutter = int(text_height * 0.1)
            x_size = text_height + text_width
            button_complete = Surface((rect.width, rect.height), SRCALPHA).convert_alpha()
            button_complete.blit(check_bitmap, (0, y_offset))
            button_complete.blit(text_bitmap, (text_height + 2, y_offset))
            return button_complete, Rect(rect.x + gutter, rect.y + y_offset, x_size + gutter, text_height)
        except GuiError:
            raise
        except Exception as exc:
            raise GuiError(f'failed to draw check style bitmap for rect={rect} state={state} text={text!r}') from exc

    def _draw_check_style_bitmaps(self, text: Optional[str], rect: Rect) -> Tuple[Tuple[Surface, Surface, Surface], Rect]:
        try:
            text = '' if text is None else text
            idle_bitmap, hit_rect = self._draw_check_style_bitmap(rect, 0, text)
            hover_bitmap, _ = self._draw_check_style_bitmap(rect, 1, text)
            armed_bitmap, _ = self._draw_check_style_bitmap(rect, 2, text)
            return (idle_bitmap, hover_bitmap, armed_bitmap), hit_rect
        except GuiError:
            raise
        except Exception as exc:
            raise GuiError(f'failed to draw check style bitmaps for rect={rect} text={text!r}') from exc

    def _draw_radio_style_bitmap(self, rect: Rect, text: Optional[str], col1: Tuple[int, int, int], col2: Tuple[int, int, int]) -> Tuple[Surface, Rect]:
        try:
            text = '' if text is None else text
            text_bitmap = self.render_text(text, colours['text'], True)
            _, _, text_width, text_height = text_bitmap.get_rect()
            gutter = int(text_height * 0.1)
            radio_bitmap = self.draw_radio_bitmap(text_height, col1, col2)
            button_complete = Surface((rect.width, rect.height), SRCALPHA).convert_alpha()
            y_offset = self.centre(rect.height, text_height)
            button_complete.blit(radio_bitmap, (0, y_offset))
            button_complete.blit(text_bitmap, (radio_bitmap.get_rect().width + 2, y_offset))
            return button_complete, Rect(rect.x + gutter, rect.y + y_offset, text_height + text_width + gutter, text_height)
        except GuiError:
            raise
        except Exception as exc:
            raise GuiError(f'failed to draw radio style bitmap for rect={rect} text={text!r}') from exc

    def _draw_radio_style_bitmaps(self, text: Optional[str], rect: Rect) -> Tuple[Tuple[Surface, Surface, Surface], Rect]:
        try:
            text = '' if text is None else text
            idle_bitmap, idle_rect = self._draw_radio_style_bitmap(rect, text, colours['light'], colours['dark'])
            hover_bitmap, _ = self._draw_radio_style_bitmap(rect, text, colours['full'], colours['none'])
            armed_bitmap, _ = self._draw_radio_style_bitmap(rect, text, colours['highlight'], colours['dark'])
            return (idle_bitmap, hover_bitmap, armed_bitmap), idle_rect
        except GuiError:
            raise
        except Exception as exc:
            raise GuiError(f'failed to draw radio style bitmaps for rect={rect} text={text!r}') from exc

    def _draw_round_style_bitmap(self, surface: Surface, border: Tuple[int, int, int], background: Tuple[int, int, int]) -> None:
        try:
            _, _, w, h = surface.get_rect()
            radius = h // 4
            circle(surface, border, (radius, radius), radius, 1, draw_top_left=True)
            circle(surface, border, (w - radius, radius), radius, 1, draw_top_right=True)
            line(surface, border, (radius, 0), (w - radius, 0), 1)
            circle(surface, border, (radius, h - radius), radius, 1, draw_bottom_left=True)
            circle(surface, border, (w - radius, h - radius), radius, 1, draw_bottom_right=True)
            line(surface, border, (radius, h - 1), (w - radius, h - 1), 1)
            line(surface, border, (0, radius), (0, h - radius), 1)
            line(surface, border, (w - 1, radius), (w - 1, h - radius), 1)
            self._flood_fill(surface, (w // 2, h // 2), background)
        except GuiError:
            raise
        except Exception as exc:
            raise GuiError('failed to draw round style bitmap') from exc

    def _draw_rounded_state(self, surface: Surface, state: str) -> None:
        if state == 'idle':
            self._draw_round_style_bitmap(surface, colours['light'], colours['medium'])
        elif state == 'hover':
            self._draw_round_style_bitmap(surface, colours['light'], colours['light'])
        elif state == 'armed':
            self._draw_round_style_bitmap(surface, colours['none'], colours['dark'])

    def _draw_rounded_style_bitmaps(self, text: Optional[str], rect: Rect) -> Tuple[Tuple[Surface, Surface, Surface], Rect]:
        try:
            text = '' if text is None else text
            _, _, w, h = rect
            saved: List[Surface] = []
            text_bitmap = self.render_text(text, colours['text'], True)
            text_x = self.centre(w, text_bitmap.get_rect().width)
            text_y = self.centre(h, text_bitmap.get_rect().height)
            idle_surface = Surface((w, h), SRCALPHA).convert_alpha()
            self._draw_rounded_state(idle_surface, 'idle')
            idle_surface.blit(text_bitmap, (text_x, text_y))
            saved.append(idle_surface)
            hover_surface = Surface((w, h), SRCALPHA).convert_alpha()
            self._draw_rounded_state(hover_surface, 'hover')
            hover_surface.blit(text_bitmap, (text_x, text_y))
            saved.append(hover_surface)
            text_bitmap = self.render_text(text, colours['highlight'], True)
            text_x = self.centre(w, text_bitmap.get_rect().width)
            text_y = self.centre(h, text_bitmap.get_rect().height)
            armed_surface = Surface((w, h), SRCALPHA).convert_alpha()
            self._draw_rounded_state(armed_surface, 'armed')
            armed_surface.blit(text_bitmap, (text_x, text_y))
            saved.append(armed_surface)
            return tuple(saved), rect  # type: ignore
        except GuiError:
            raise
        except Exception as exc:
            raise GuiError(f'failed to draw rounded style bitmaps for rect={rect} text={text!r}') from exc

    def _draw_window_title_bar_bitmap(self, gui: "GuiManager", title: str, width: int, size: int, colour: Optional[Tuple[int, int, int]] = None) -> Surface:
        titlebar_font_set = False
        try:
            from ...widgets.frame import Frame
            from ..events import InteractiveState
            self.set_font('titlebar')
            titlebar_font_set = True
            if colour is None:
                colour = colours['highlight']
            title_surface = Surface((width, size)).convert()
            frame = Frame(gui, 'titlebar_frame', Rect(0, 0, width, size))
            frame.state = InteractiveState.Armed
            frame.surface = title_surface
            frame.draw()
            text = self.render_text(title, colour, True)
            text_y = self.centre(size, text.get_rect().height)
            title_surface.blit(text, (5, text_y))
            return title_surface
        except GuiError:
            raise
        except Exception as exc:
            raise GuiError(f'failed to draw window title bar bitmap for title={title!r}') from exc
        finally:
            if titlebar_font_set:
                self.set_last_font()

    def _flood_fill(self, surface: Surface, position: Tuple[int, int], colour: Tuple[int, int, int]) -> None:
        pixels: Optional[PixelArray] = None
        try:
            pixels = PixelArray(surface)
            new_colour = surface.map_rgb(colour)
            old_colour = pixels[position]
            if old_colour == new_colour:
                return
            width, height = surface.get_size()
            locations = deque([position])
            while locations:
                x, y = locations.popleft()
                if pixels[x, y] == old_colour:
                    pixels[x, y] = new_colour
                    if x > 0: locations.append((x - 1, y))
                    if x < width - 1: locations.append((x + 1, y))
                    if y > 0: locations.append((x, y - 1))
                    if y < height - 1: locations.append((x, y + 1))
            blit_array(surface, pixels)
        except GuiError:
            raise
        except Exception as exc:
            raise GuiError(f'failed flood fill at position={position}') from exc
        finally:
            if pixels is not None:
                del pixels
