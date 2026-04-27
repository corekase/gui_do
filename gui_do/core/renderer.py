import pygame


class Renderer:
    """Renderer that draws one scene with one color theme."""

    def __init__(self) -> None:
        # Cache for scaled background bitmap: (source_bitmap_id, target_size) → scaled_surface
        self._bg_cache: tuple | None = None

    def render(self, surface, scene, theme, app=None) -> None:
        if app is not None:
            app.invalidation.begin_frame()
        restored = False
        if app is not None:
            restored = bool(app.restore_pristine(surface=surface))
        if not restored:
            surface.fill(theme.background)
            if theme.background_bitmap is not None:
                target_size = surface.get_size()
                bitmap = theme.background_bitmap
                cache = self._bg_cache
                if cache is None or cache[0] is not bitmap or cache[1] != target_size:
                    scaled = pygame.transform.smoothscale(bitmap, target_size)
                    self._bg_cache = (bitmap, target_size, scaled)
                    cache = self._bg_cache
                surface.blit(cache[2], (0, 0))
        if app is not None:
            app.draw_screen_features(surface, theme)
        scene.draw(surface, theme, app=app)
        if app is None:
            return
        cursor_asset = app.get_active_cursor()
        if cursor_asset is None:
            return
        cursor_surface, hotspot = cursor_asset
        anchor = app.lock_point_pos if app.mouse_point_locked else None
        if anchor is None:
            anchor = app.logical_pointer_pos
        draw_x = int(anchor[0]) - int(hotspot[0])
        draw_y = int(anchor[1]) - int(hotspot[1])
        surface.blit(cursor_surface, (draw_x, draw_y))
        app.invalidation.end_frame()
