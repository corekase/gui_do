"""Graphics-tab helper routines for the systems demo feature."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pygame
from pygame import Rect, Surface

from gui_do import (
    ArrowBoxControl,
    ButtonControl,
    CanvasControl,
    GridLayout,
    GridPlacement,
    ImageControl,
    LabelControl,
    PanelControl,
    SurfaceEffects,
)

if TYPE_CHECKING:
    from .systems_feature import SystemsFeature


def build_graphics_panel(feature: SystemsFeature, rect: Rect) -> PanelControl:
    panel = PanelControl("systems_graphics_panel", Rect(rect), draw_background=False)
    tile_preview_h = 120

    # Two columns: left (particle systems), right (tile navigation + tilemap).
    top_padding = 8
    left_col_x = feature.PANEL_PADDING_X + feature.LEFT_SIDE_INSET_X
    left_col_width = max(160, rect.width // 2 - feature.PANEL_PADDING_X * 2)
    right_col_x = rect.width // 2 + feature.PANEL_PADDING_X
    right_col_width = max(160, rect.width - right_col_x - feature.PANEL_PADDING_X)

    nav_cluster = PanelControl(
        "systems_graphics_tile_nav_cluster",
        Rect(0, 0, 96, 96),
        draw_background=True,
    )
    nav_gap = 12
    tile_preview_nudge_x = 12
    tile_preview_width = min(
        360,
        max(160, right_col_width - nav_cluster.rect.width - nav_gap - tile_preview_nudge_x),
    )
    tile_preview_x = right_col_x + nav_cluster.rect.width + nav_gap + tile_preview_nudge_x
    nav_cluster_x = right_col_x

    buttons_top = top_padding
    feature._add_button_rows(
        panel,
        rect,
        buttons_top,
        [
            ButtonControl(
                "systems_graphics_burst",
                Rect(0, 0, 156, 32),
                "Burst Particles",
                feature._trigger_particle_burst,
                style="round",
            ),
            ButtonControl(
                "systems_graphics_reset",
                Rect(0, 0, 170, 32),
                "Reset Particle Layer",
                feature._reset_particle_layer,
                style="round",
            ),
        ],
        per_row=2,
        left=left_col_x,
        width=left_col_width,
    )

    preview_width = min(520, left_col_width)
    particle_layer_height = 180
    feature._graphics_compositor.resize((preview_width, 180))
    feature._graphics_camera.viewport_rect = Rect(0, 0, preview_width, 180)
    feature._graphics_tile_camera.size = (tile_preview_width, tile_preview_h)

    particle_layer_top = buttons_top + 32 + feature.BUTTON_ROW_SPACING
    feature._place_graphics_particle_layer(
        panel,
        left=left_col_x,
        top=particle_layer_top,
        width=preview_width,
        height=particle_layer_height,
    )
    labels_top = particle_layer_top + particle_layer_height + 12
    feature._sync_graphics_emitter_offsets(
        panel_rect=Rect(rect),
        left_col_x=left_col_x,
        left_col_width=left_col_width,
        labels_top=labels_top,
    )
    feature.graphics_particle_label = LabelControl(
        "systems_graphics_particle_status",
        Rect(0, 0, left_col_width, 28),
        "",
        align="left",
    )
    feature.graphics_layer_label = LabelControl(
        "systems_graphics_layer_status",
        Rect(0, 0, left_col_width, 28),
        "",
        align="left",
    )
    feature.graphics_scene_graph_label = LabelControl(
        "systems_graphics_scene_graph_status",
        Rect(0, 0, left_col_width, 28),
        "",
        align="left",
    )
    feature.graphics_compositor_label = LabelControl(
        "systems_graphics_compositor_status",
        Rect(0, 0, left_col_width, 28),
        "",
        align="left",
    )
    feature.graphics_tile_map_label = LabelControl(
        "systems_graphics_tile_map_status",
        Rect(0, 0, tile_preview_width, 28),
        "",
        align="left",
    )
    feature.graphics_tile_preview_canvas = CanvasControl(
        "systems_graphics_tile_map_preview",
        Rect(0, 0, tile_preview_width, tile_preview_h),
        max_events=32,
    )
    feature._surface_effect_source = feature._build_surface_effect_source((left_col_width, 104))
    feature._surface_effect_preview = ImageControl(
        "systems_graphics_surface_effect_preview",
        Rect(0, 0, left_col_width, 104),
        feature._surface_effect_source,
        scale=True,
    )
    feature._surface_effect_label = ButtonControl(
        "systems_graphics_surface_effect_cycle",
        Rect(0, 0, 220, 32),
        "Cycle Surface Effect",
        feature._cycle_surface_effect,
        style="round",
    )
    feature.graphics_surface_effects_label = LabelControl(
        "systems_graphics_surface_effects_status",
        Rect(0, 0, left_col_width, 28),
        "",
        align="left",
    )

    feature._place_vertical_label_stack(
        panel,
        Rect(left_col_x, labels_top, max(1, left_col_width), 172),
        [
            feature.graphics_particle_label,
            feature.graphics_layer_label,
            feature.graphics_scene_graph_label,
            feature.graphics_compositor_label,
            feature.graphics_surface_effects_label,
        ],
        gap=8,
    )
    feature._place_vertical_grid_sequence(
        panel,
        Rect(left_col_x, labels_top + 180, max(1, left_col_width), 144),
        [
            (feature._surface_effect_label, 32, 8),
            (feature._surface_effect_preview, 104, 0),
        ],
    )

    right_label_top = top_padding

    tile_preview_label = LabelControl(
        "systems_graphics_tile_map_preview_label",
        Rect(0, 0, tile_preview_width, 22),
        "Tilemap Output",
        align="left",
    )
    nav_cluster_label = LabelControl(
        "systems_graphics_tile_nav_label",
        Rect(0, 0, nav_cluster.rect.width, 22),
        "Tile Navigation",
        align="left",
    )
    feature._place_vertical_grid_sequence(
        panel,
        Rect(tile_preview_x, right_label_top, max(1, tile_preview_width), tile_preview_h + 62),
        [
            (tile_preview_label, 22, 4),
            (feature.graphics_tile_preview_canvas, tile_preview_h, 12),
            (feature.graphics_tile_map_label, 28, 0),
        ],
    )
    feature._place_vertical_grid_sequence(
        panel,
        Rect(nav_cluster_x, right_label_top, max(1, nav_cluster.rect.width), nav_cluster.rect.height + 26),
        [
            (nav_cluster_label, 22, 4),
            (nav_cluster, nav_cluster.rect.height, 0),
        ],
    )
    nav_left = ArrowBoxControl(
        "systems_graphics_nav_left",
        Rect(0, 0, 44, 44),
        180,
        on_activate=lambda: feature._pan_tile_camera(-24, 0),
    )
    nav_up = ArrowBoxControl(
        "systems_graphics_nav_up",
        Rect(0, 0, 44, 44),
        90,
        on_activate=lambda: feature._pan_tile_camera(0, -24),
    )
    nav_down = ArrowBoxControl(
        "systems_graphics_nav_down",
        Rect(0, 0, 44, 44),
        270,
        on_activate=lambda: feature._pan_tile_camera(0, 24),
    )
    nav_right = ArrowBoxControl(
        "systems_graphics_nav_right",
        Rect(0, 0, 44, 44),
        0,
        on_activate=lambda: feature._pan_tile_camera(24, 0),
    )
    nav_grid = GridLayout(
        row_tracks=[44, 44],
        col_tracks=[44, 44],
        gap=4,
        padding=0,
    )
    nav_grid.place(nav_left, GridPlacement(row=0, col=0))
    nav_grid.place(nav_up, GridPlacement(row=0, col=1))
    nav_grid.place(nav_down, GridPlacement(row=1, col=0))
    nav_grid.place(nav_right, GridPlacement(row=1, col=1))
    nav_grid.apply(Rect(2, 2, 92, 92))
    nav_cluster.add_at(nav_left, nav_left.rect.left, nav_left.rect.top)
    nav_cluster.add_at(nav_up, nav_up.rect.left, nav_up.rect.top)
    nav_cluster.add_at(nav_down, nav_down.rect.left, nav_down.rect.top)
    nav_cluster.add_at(nav_right, nav_right.rect.left, nav_right.rect.top)

    feature._render_tile_map_preview()
    feature._refresh_surface_effect_preview()
    feature._refresh_graphics_labels()
    return panel


def trigger_particle_burst(feature: SystemsFeature) -> None:
    feature._particle_layer.particle_system.burst(feature._particle_burst_emitter, count=150)
    feature._graphics_dirty_tracker.mark_dirty(
        Rect(0, 0, feature._particle_layer.rect.width, feature._particle_layer.rect.height)
    )
    feature._refresh_graphics_labels()


def build_surface_effect_source(_feature: SystemsFeature, size: tuple[int, int]) -> Surface:
    width = max(1, int(size[0]))
    height = max(1, int(size[1]))
    surface = Surface((width, height), pygame.SRCALPHA)
    for y in range(height):
        t = y / max(1, height - 1)
        base = int(34 + 78 * t)
        accent = int(92 + 100 * t)
        surface.fill((base, base + 10, accent), Rect(0, y, width, 1))
    pygame.draw.rect(surface, (255, 255, 255), Rect(8, 8, width // 2, height // 2), border_radius=10)
    pygame.draw.circle(surface, (255, 154, 87), (width - 30, 30), 18)
    pygame.draw.circle(surface, (90, 200, 166), (width - 54, height - 28), 16)
    pygame.draw.line(surface, (20, 22, 30), (12, height - 20), (width - 12, 18), 4)
    pygame.draw.rect(surface, (250, 240, 190), Rect(width // 2 - 18, height // 2 - 10, 36, 22), border_radius=8)
    return surface


def cycle_surface_effect(feature: SystemsFeature) -> None:
    if feature._surface_effect_source is None:
        return
    feature._surface_effect_index = (feature._surface_effect_index + 1) % len(feature._surface_effect_cycle)
    feature._refresh_surface_effect_preview()


def refresh_surface_effect_preview(feature: SystemsFeature) -> None:
    if feature._surface_effect_source is None:
        return
    effect = feature._surface_effect_cycle[feature._surface_effect_index]
    source = feature._surface_effect_source
    if effect == "blur":
        preview = SurfaceEffects.blur(source, 6)
    elif effect == "greyscale":
        preview = SurfaceEffects.greyscale(source)
    elif effect == "tint":
        preview = SurfaceEffects.tint(source, (255, 168, 92), alpha=110)
    elif effect == "brightness":
        preview = SurfaceEffects.brightness(source, 1.25)
    elif effect == "vignette":
        preview = SurfaceEffects.vignette(source, 0.7)
    else:
        preview = SurfaceEffects.pixelate(source, 8)
    if feature._surface_effect_preview is not None:
        feature._surface_effect_preview.set_image(preview)
    if feature.graphics_surface_effects_label is not None:
        feature.graphics_surface_effects_label.text = (
            f"SurfaceEffects preview uses {effect} on a generated scene card; click to cycle effects."
        )


def reset_particle_layer(feature: SystemsFeature) -> None:
    feature._particle_layer.particle_system.clear()
    feature._particle_layer.particle_system.add_emitter(feature._particle_ambient_emitter)
    feature._particle_layer.particle_system.add_emitter(feature._particle_burst_emitter)
    feature._graphics_dirty_tracker.mark_dirty(
        Rect(0, 0, feature._particle_layer.rect.width, feature._particle_layer.rect.height)
    )
    feature._refresh_graphics_labels()


def advance_graphics_runtime(feature: SystemsFeature) -> None:
    feature._graphics_runtime_step += 1
    phase = feature._graphics_runtime_step % 4
    release_node = feature._graphics_scene_graph.find("release_stage")
    if release_node is not None:
        release_node.pos = (84.0 + phase * 24.0, 56.0 + (phase % 2) * 14.0)
    feature._graphics_camera.pan_screen(10.0, 0.0)
    next_zoom = 1.0 + 0.08 * phase
    feature._graphics_camera.set_zoom(next_zoom, anchor_screen=(36.0, 36.0))
    feature._graphics_compositor.set_layer_visible("particles", phase != 1)
    feature._graphics_compositor.set_layer_opacity("ui", 0.86 if phase in {2, 3} else 1.0)
    feature._pan_tile_camera(24, 12, refresh=False)
    feature._graphics_dirty_tracker.mark_dirty(
        Rect(0, 0, feature._particle_layer.rect.width, feature._particle_layer.rect.height)
    )
    feature._render_tile_map_preview()
    feature._refresh_graphics_labels()


def pan_tile_camera(feature: SystemsFeature, dx: int, dy: int, *, refresh: bool = True) -> None:
    max_x = max(0, feature._graphics_tile_map.pixel_width - feature._graphics_tile_camera.width)
    max_y = max(0, feature._graphics_tile_map.pixel_height - feature._graphics_tile_camera.height)
    feature._graphics_tile_camera.x = max(0, min(max_x, feature._graphics_tile_camera.x + int(dx)))
    feature._graphics_tile_camera.y = max(0, min(max_y, feature._graphics_tile_camera.y + int(dy)))
    if refresh:
        feature._render_tile_map_preview()
        feature._refresh_graphics_labels()


def advance_graphics_demo(feature: SystemsFeature, dt: float) -> None:
    graphics_panel = feature._tab_panels.get("graphics")
    if graphics_panel is not None:
        bx, by = feature._burst_emitter_panel_offset
        ax, ay = feature._ambient_emitter_panel_offset
        feature._particle_burst_emitter.x = graphics_panel.rect.left + bx
        feature._particle_burst_emitter.y = graphics_panel.rect.top + by
        feature._particle_ambient_emitter.x = graphics_panel.rect.left + ax
        feature._particle_ambient_emitter.y = graphics_panel.rect.top + ay
    feature._particle_layer.update_particles(dt)
    feature._graphics_dirty_tracker.mark_dirty(
        Rect(0, 0, feature._particle_layer.rect.width, feature._particle_layer.rect.height)
    )
    feature._render_tile_map_preview()
    feature._refresh_graphics_labels()


def render_tile_map_preview(feature: SystemsFeature) -> None:
    canvas_control = feature.graphics_tile_preview_canvas
    if canvas_control is None:
        return
    canvas_surface = canvas_control.get_canvas_surface()
    canvas_surface.fill((24, 28, 33))
    camera_rect = Rect(feature._graphics_tile_camera)
    camera_rect.width = max(1, min(camera_rect.width, feature._graphics_tile_map.pixel_width))
    camera_rect.height = max(1, min(camera_rect.height, feature._graphics_tile_map.pixel_height))
    feature._graphics_tile_map.draw(canvas_surface, camera_rect, offset=(0, 0))

    marker_world_x = camera_rect.left + camera_rect.width // 2
    marker_world_y = camera_rect.top + camera_rect.height // 2
    marker_screen_x = max(0, min(canvas_surface.get_width() - 1, marker_world_x - camera_rect.left))
    marker_screen_y = max(0, min(canvas_surface.get_height() - 1, marker_world_y - camera_rect.top))
    canvas_surface.fill((255, 240, 140), Rect(marker_screen_x - 2, marker_screen_y - 2, 5, 5))
    canvas_control.invalidate()


def refresh_graphics_labels(feature: SystemsFeature) -> None:
    if feature.graphics_particle_label is not None:
        feature.graphics_particle_label.text = (
            f"ParticleSystem emitters={feature._particle_layer.particle_system.emitter_count} "
            f"active_particles={feature._particle_layer.particle_system.active_particle_count}"
        )
    if feature.graphics_layer_label is not None:
        feature.graphics_layer_label.text = (
            "ParticleLayer hosts an ambient release trail plus on-demand burst confetti preview."
        )
    if feature.graphics_scene_graph_label is not None:
        release_node = feature._graphics_scene_graph.find("release_stage")
        if release_node is None:
            feature.graphics_scene_graph_label.text = "SceneGraph2D has no release nodes."
        else:
            world_x, world_y, _, _ = release_node.world_transform()
            screen_x, screen_y = feature._graphics_camera.world_to_screen(world_x, world_y)
            visible_nodes = len(feature._graphics_scene_graph.find_all(visible_only=True))
            feature.graphics_scene_graph_label.text = (
                f"SceneGraph2D/Camera2D nodes={visible_nodes} release_stage_screen=({int(screen_x)}, {int(screen_y)}) "
                f"zoom={feature._graphics_camera.zoom:.2f}"
            )
    if feature.graphics_compositor_label is not None:
        dirty_union = feature._graphics_dirty_tracker.dirty_union()
        dirty_text = f"{dirty_union.width}x{dirty_union.height}" if dirty_union is not None else "none"
        feature.graphics_compositor_label.text = (
            f"SurfaceCompositor layers={feature._graphics_compositor.layer_names()} dirty_union={dirty_text}"
        )
    if feature.graphics_tile_map_label is not None:
        col_start, col_end, row_start, row_end = feature._graphics_tile_map.visible_range(feature._graphics_tile_camera)
        visible_tiles = max(0, col_end - col_start) * max(0, row_end - row_start)
        sample_col, sample_row = feature._graphics_tile_map.world_to_tile(
            feature._graphics_tile_camera.left + 24,
            feature._graphics_tile_camera.top + 24,
        )
        sample_tile = feature._graphics_tile_map.tile_at(sample_col, sample_row)
        feature.graphics_tile_map_label.text = (
            f"TileMap camera=({feature._graphics_tile_camera.left},{feature._graphics_tile_camera.top}) "
            f"visible_tiles={visible_tiles} sample_tile={sample_tile}"
        )
    if feature.graphics_surface_effects_label is not None and not feature.graphics_surface_effects_label.text:
        feature.graphics_surface_effects_label.text = (
            "SurfaceEffects preview applies image post-processing to a generated scene card."
        )


__all__ = [
    "advance_graphics_demo",
    "advance_graphics_runtime",
    "build_graphics_panel",
    "build_surface_effect_source",
    "cycle_surface_effect",
    "pan_tile_camera",
    "refresh_graphics_labels",
    "refresh_surface_effect_preview",
    "render_tile_map_preview",
    "reset_particle_layer",
    "trigger_particle_burst",
]
