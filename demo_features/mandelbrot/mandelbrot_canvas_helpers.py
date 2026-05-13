"""Canvas and render helpers for the Mandelbrot demo feature."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pygame import PixelArray, Rect

from .mandelbrot_logic_feature import MandelbrotLogicFeature
from .mandelbrot_specs import MANDEL_SPLIT_KEYS, MANDEL_TASK_ID_ITERATIVE

if TYPE_CHECKING:
    from .mandelbrot_feature import MandelbrotFeature


def logic(feature: MandelbrotFeature, alias: str):
    name = feature.bound_logic_name(alias=alias)
    if name is None:
        return None
    provider = feature._feature_manager.get(name)
    return provider if isinstance(provider, MandelbrotLogicFeature) else None


def refresh_color_table(feature: MandelbrotFeature) -> None:
    current_logic = feature._logic("primary")
    if current_logic is None:
        feature._color_table = ((0, 0, 0),)
        feature._mapped_color_tables.clear()
        return

    max_iter = max(1, int(current_logic.max_iter))
    palette = tuple(current_logic.mandel_cols)
    if not palette:
        feature._color_table = tuple((0, 0, 0) for _ in range(max_iter))
        feature._mapped_color_tables.clear()
        return

    terminal = max_iter - 1
    feature._color_table = tuple((0, 0, 0) if i >= terminal else palette[i % len(palette)] for i in range(max_iter))
    feature._mapped_color_tables.clear()


def color_for_iteration(feature: MandelbrotFeature, value: int) -> tuple[int, int, int]:
    if value < 0:
        return feature._color_table[0]
    if value >= len(feature._color_table):
        return feature._color_table[-1]
    return feature._color_table[value]


def mapped_colors_for_canvas(feature: MandelbrotFeature, canvas) -> tuple[int, ...]:
    key = id(canvas)
    cached = feature._mapped_color_tables.get(key)
    if cached is not None:
        return cached
    mapped = tuple(canvas.map_rgb(color) for color in feature._color_table)
    feature._mapped_color_tables[key] = mapped
    return mapped


def viewport(feature: MandelbrotFeature, width: int, height: int) -> tuple:
    current_logic = feature._logic("primary")
    return current_logic.mandel_viewport(width, height) if current_logic else (0 + 0j, 1.0)


def canvas_for_task(feature: MandelbrotFeature, task_id: str):
    if task_id in MANDEL_SPLIT_KEYS:
        canvas_control = feature.split_canvases.get(task_id)
        return canvas_control.canvas if canvas_control else None
    return feature.primary_canvas.canvas if feature.primary_canvas else None


def apply_result(feature: MandelbrotFeature, task_id: str, payload) -> None:
    canvas = feature._canvas_for_task(task_id)
    if canvas is None:
        return
    cw, ch = canvas.get_size()
    color_for_iter = feature._color_for_iteration
    mapped_colors = feature._mapped_colors_for_canvas(canvas)
    mapped_count = len(mapped_colors)

    if task_id == MANDEL_TASK_ID_ITERATIVE:
        if len(payload) == 2:
            y, row = payload
            x_start = 0
        else:
            y, x_start, row = payload
        if 0 <= y < ch:
            draw_x = max(0, int(x_start))
            source_x = max(0, -int(x_start))
            limit = min(cw - draw_x, len(row) - source_x)
            if limit > 0:
                mapped_row = []
                append = mapped_row.append
                default_color = mapped_colors[-1]
                for x in range(source_x, source_x + limit):
                    value = int(row[x])
                    if 0 <= value < mapped_count:
                        append(mapped_colors[value])
                    else:
                        append(default_color)
                pixels = PixelArray(canvas)
                try:
                    pixels[draw_x:draw_x + limit, y] = mapped_row
                finally:
                    del pixels
        return

    x0, y0, w, h, values = payload
    if isinstance(values, int):
        rx, ry = max(0, x0), max(0, y0)
        rx1, ry1 = min(cw, x0 + w), min(ch, y0 + h)
        if rx1 > rx and ry1 > ry:
            canvas.fill(color_for_iter(values), Rect(rx, ry, rx1 - rx, ry1 - ry))
        return

    x_start = max(0, x0)
    y_start = max(0, y0)
    x_end = min(cw, x0 + w)
    y_end = min(ch, y0 + h)
    if x_end <= x_start or y_end <= y_start:
        return

    row_span = max(0, w)
    if row_span <= 0:
        return

    pixels = PixelArray(canvas)
    try:
        default_color = mapped_colors[-1]
        for yy in range(y_start, y_end):
            idx = (yy - y0) * row_span + (x_start - x0)
            row_colors = []
            append = row_colors.append
            for _ in range(x_start, x_end):
                value = int(values[idx])
                if 0 <= value < mapped_count:
                    append(mapped_colors[value])
                else:
                    append(default_color)
                idx += 1
            pixels[x_start:x_end, yy] = row_colors
    finally:
        del pixels


__all__ = [
    "apply_result",
    "canvas_for_task",
    "color_for_iteration",
    "logic",
    "mapped_colors_for_canvas",
    "refresh_color_table",
    "viewport",
]
