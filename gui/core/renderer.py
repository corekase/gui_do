import pygame


class Renderer:
    """Renderer that draws one scene with one color theme."""

    def render(self, surface, scene, theme) -> None:
        surface.fill(theme.background)
        if getattr(theme, "background_bitmap", None) is not None:
            scaled = pygame.transform.smoothscale(theme.background_bitmap, surface.get_size())
            surface.blit(scaled, (0, 0))
        scene.draw(surface, theme)
