# Helper to get the main display size
import pygame

def get_screen_size():
    surface = pygame.display.get_surface()
    if surface is not None:
        return surface.get_size()
    # Fallback to display info if no surface
    info = pygame.display.Info()
    return (info.current_w, info.current_h)
