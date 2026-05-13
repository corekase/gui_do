"""Tests for OffscreenBackend — headless render target."""
import unittest

import gui_do
from gui_do import (
    RenderTarget,
    OffscreenRenderTarget,
    create_render_target,
    create_surface,
)

import pygame


class TestCreateSurface(unittest.TestCase):
    def test_returns_surface_without_display(self):
        # pygame.display is NOT initialised in this test
        surf = create_surface(100, 80)
        self.assertIsInstance(surf, pygame.Surface)
        self.assertEqual(surf.get_size(), (100, 80))

    def test_supports_per_pixel_alpha(self):
        surf = create_surface(50, 50)
        # SRCALPHA flag should be set
        self.assertTrue(surf.get_flags() & pygame.SRCALPHA)


class TestOffscreenRenderTarget(unittest.TestCase):
    def setUp(self):
        self.target = OffscreenRenderTarget(200, 150)

    def test_size(self):
        self.assertEqual(self.target.size, (200, 150))

    def test_surface_is_pygame_surface(self):
        self.assertIsInstance(self.target.surface, pygame.Surface)

    def test_fill_sets_pixels(self):
        self.target.fill((255, 0, 0))
        r, g, b, _ = self.target.get_at((0, 0))
        self.assertEqual((r, g, b), (255, 0, 0))

    def test_fill_with_rect(self):
        self.target.fill((0, 0, 0))
        rect = pygame.Rect(10, 10, 20, 20)
        self.target.fill((0, 255, 0), rect)
        r, g, b, _ = self.target.get_at((15, 15))
        self.assertEqual((r, g, b), (0, 255, 0))
        # Outside rect is still black
        r, g, b, _ = self.target.get_at((0, 0))
        self.assertEqual((r, g, b), (0, 0, 0))

    def test_blit(self):
        src = create_surface(30, 30)
        src.fill((0, 0, 255))
        self.target.fill((0, 0, 0))
        self.target.blit(src, (5, 5))
        r, g, b, _ = self.target.get_at((5, 5))
        self.assertEqual((r, g, b), (0, 0, 255))

    def test_flip_is_noop(self):
        self.target.flip()  # Should not raise

    def test_to_png_bytes_returns_bytes(self):
        self.target.fill((128, 64, 32))
        data = self.target.to_png_bytes()
        self.assertIsInstance(data, bytes)
        self.assertGreater(len(data), 0)
        # PNG magic bytes
        self.assertTrue(data[:4] == b'\x89PNG', "Expected PNG magic bytes")

    def test_satisfies_render_target_protocol(self):
        self.assertIsInstance(self.target, RenderTarget)


class TestCreateRenderTarget(unittest.TestCase):
    def test_returns_offscreen_when_no_display(self):
        from unittest.mock import patch
        with patch("pygame.display.get_init", return_value=False):
            target = create_render_target(100, 100)
        self.assertIsInstance(target, OffscreenRenderTarget)

    def test_exports_from_gui_do(self):
        for name in ("RenderTarget", "LiveRenderTarget", "OffscreenRenderTarget",
                     "create_render_target", "create_surface"):
            self.assertTrue(hasattr(gui_do, name), msg=f"Missing export: {name}")
