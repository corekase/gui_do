"""Runtime and view-update helpers for the Life feature."""

from __future__ import annotations

import math
from typing import TYPE_CHECKING, Any

from pygame import Rect

from gui_do.features.runtime_helpers import resolve_canvas_local_point

from .life_logic_feature import LifeLogicFeature
from .life_specs import LIFE_KEY_COMMAND, LIFE_KEY_TOPIC, LIFE_LOGIC_TOPIC

if TYPE_CHECKING:
    from .life_feature import LifeFeature


def normalize_life_cells_payload(_feature: LifeFeature, cells: Any) -> set[tuple[int, int]] | None:
    if isinstance(cells, set):
        return {(int(x), int(y)) for (x, y) in cells}
    if isinstance(cells, (tuple, list)):
        normalized: set[tuple[int, int]] = set()
        for candidate in cells:
            if isinstance(candidate, tuple) and len(candidate) == 2:
                normalized.add((int(candidate[0]), int(candidate[1])))
        return normalized
    return None


def send_life_logic_command(feature: LifeFeature, command: str, **extra: Any) -> bool:
    if feature._feature_manager is None:
        return False
    message: dict[str, Any] = {
        LIFE_KEY_TOPIC: LIFE_LOGIC_TOPIC,
        LIFE_KEY_COMMAND: str(command),
    }
    message.update(extra)
    return feature.send_logic_message(message, alias=feature.LOGIC_ALIAS)


def life_reset(feature: LifeFeature) -> None:
    feature.life_origin = [feature.canvas.rect.width / 2.0, feature.canvas.rect.height / 2.0]
    feature.life_cell_size = 12
    feature.zoom_slider.value = 5.0
    feature.life_zoom_slider_last_value = int(round(feature.zoom_slider.value))
    feature.toggle.pushed = False
    feature.life_cells = set(LifeLogicFeature.DEFAULT_SEED)
    feature._send_life_logic_command("reset")


def zoom_life_view_about(feature: LifeFeature, anchor_local: tuple[float, float], new_size: int) -> None:
    old_size = max(2, int(round(feature.life_cell_size)))
    clamped_size = max(2, min(24, int(new_size)))
    if clamped_size == old_size:
        return
    anchor_x, anchor_y = anchor_local
    feature.life_origin[0] = anchor_x - ((anchor_x - feature.life_origin[0]) / old_size) * clamped_size
    feature.life_origin[1] = anchor_y - ((anchor_y - feature.life_origin[1]) / old_size) * clamped_size
    feature.life_cell_size = clamped_size
    slider_value = max(0, min(11, (clamped_size // 2) - 1))
    feature.zoom_slider.value = float(slider_value)
    feature.life_zoom_slider_last_value = int(slider_value)


def on_life_zoom_slider_changed(feature: LifeFeature, value: float, _reason) -> None:
    sync_life_zoom_from_slider(feature, int(round(value)))


def sync_life_zoom_from_slider(feature: LifeFeature, slider_value: int) -> None:
    if slider_value == feature.life_zoom_slider_last_value:
        return
    old_size = max(2, int(round(feature.life_cell_size)))
    new_size = (slider_value + 1) * 2
    if new_size == old_size:
        feature.life_zoom_slider_last_value = slider_value
        return
    feature.life_zoom_slider_last_value = slider_value
    center_local = (feature.canvas.rect.width / 2.0, feature.canvas.rect.height / 2.0)
    zoom_life_view_about(feature, center_local, new_size)


def update_life(feature: LifeFeature) -> None:
    feature._update_life_frame_core(feature.demo, feature.canvas, feature.toggle)


def update_life_frame_core(feature: LifeFeature, demo, canvas, toggle) -> None:
    while True:
        packet = canvas.read_event()
        if packet is None:
            break
        if not packet.is_mouse_down(1):
            continue
        local_point = resolve_canvas_local_point(packet, canvas.rect)
        if local_point is None:
            continue
        local_x, local_y = local_point
        cell_size = max(2, int(round(feature.life_cell_size)))
        cell_x = math.floor((local_x - feature.life_origin[0]) / cell_size)
        cell_y = math.floor((local_y - feature.life_origin[1]) / cell_size)
        cell = (cell_x, cell_y)
        if cell in feature.life_cells:
            feature.life_cells.remove(cell)
        else:
            feature.life_cells.add(cell)
        feature._send_life_logic_command("toggle_cell", cell=cell)

    if toggle.pushed:
        feature.life_cells = LifeLogicFeature.next_life_cycle(feature.life_cells)
        feature._send_life_logic_command("next")

    cell_size = max(2, int(round(feature.life_cell_size)))
    canvas.canvas.fill(demo.app.theme.medium)
    trim = 0 if cell_size <= 2 else 1
    for cx, cy in feature.life_cells:
        px = int(feature.life_origin[0] + (cx * cell_size))
        py = int(feature.life_origin[1] + (cy * cell_size))
        if -cell_size <= px <= canvas.rect.width and -cell_size <= py <= canvas.rect.height:
            canvas.canvas.fill((255, 255, 255), Rect(px, py, max(1, cell_size - trim), max(1, cell_size - trim)))


__all__ = [
    "life_reset",
    "normalize_life_cells_payload",
    "on_life_zoom_slider_changed",
    "send_life_logic_command",
    "sync_life_zoom_from_slider",
    "update_life",
    "update_life_frame_core",
    "zoom_life_view_about",
]
