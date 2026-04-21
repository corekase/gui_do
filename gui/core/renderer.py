import pygame


class Renderer:
    """Renderer that draws one scene with one color theme."""

    def render(self, surface, scene, theme, app=None) -> None:
        surface.fill(theme.background)
        if getattr(theme, "background_bitmap", None) is not None:
            scaled = pygame.transform.smoothscale(theme.background_bitmap, surface.get_size())
            surface.blit(scaled, (0, 0))
        scene.draw(surface, theme)
        if app is None:
            return
        cursor_asset = app.get_active_cursor() if hasattr(app, "get_active_cursor") else None
        if cursor_asset is None:
            return
        cursor_surface, hotspot = cursor_asset
        anchor = getattr(app, "lock_point_pos", None) if getattr(app, "mouse_point_locked", False) else None
        if anchor is None:
            anchor = getattr(app, "logical_pointer_pos", pygame.mouse.get_pos())
        draw_x = int(anchor[0]) - int(hotspot[0])
        draw_y = int(anchor[1]) - int(hotspot[1])
        surface.blit(cursor_surface, (draw_x, draw_y))
