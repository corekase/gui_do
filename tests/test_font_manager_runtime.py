import os
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame

from gui import FontManager, GuiApplication
from shared.feature_lifecycle import Feature


class FontManagerRoleTests(unittest.TestCase):
    def setUp(self) -> None:
        pygame.init()

    def tearDown(self) -> None:
        pygame.quit()

    def test_register_role_and_query(self) -> None:
        manager = FontManager()
        manager.register_role("body", size=16)
        manager.register_role("title", size=20, bold=True)

        self.assertEqual(manager.role_names(), ("body", "title"))
        self.assertTrue(manager.has_role("body"))
        self.assertFalse(manager.has_role("missing"))

    def test_reconfigure_role_increments_revision_and_drops_cache(self) -> None:
        manager = FontManager()
        manager.register_role("body", size=16)
        rev_before = manager.revision

        manager.register_role("body", size=20)

        self.assertGreater(manager.revision, rev_before)
        self.assertEqual(manager.role_names(), ("body",), "role_order must not duplicate")

    def test_render_text_and_shadow_return_surfaces(self) -> None:
        manager = FontManager()
        manager.register_role("body", size=16)

        plain = manager.render_text("Hello", (255, 255, 255), role_name="body")
        shaded = manager.render_text_with_shadow("Hello", (255, 255, 255), (0, 0, 0), role_name="body")

        self.assertGreater(plain.get_width(), 0)
        self.assertGreater(plain.get_height(), 0)
        self.assertGreaterEqual(shaded.get_width(), plain.get_width())
        self.assertGreaterEqual(shaded.get_height(), plain.get_height())

    def test_register_role_updates_cached_font_instance(self) -> None:
        manager = FontManager()
        manager.register_role("body", size=16)
        rev_before = manager.revision
        font_before = manager.get_font("body")

        manager.register_role("body", size=24)

        self.assertGreater(manager.revision, rev_before)
        font_after = manager.get_font("body")
        self.assertIsNot(font_before, font_after)

    def test_font_instance_exposes_size_properties(self) -> None:
        manager = FontManager()
        manager.register_role("body", size=16)

        instance = manager.font_instance("body")

        self.assertEqual(instance.role_name, "body")
        self.assertEqual(instance.point_size, 16)
        self.assertGreater(instance.line_height, 0)

    def test_font_instance_text_surface_size_includes_shadow_padding(self) -> None:
        manager = FontManager()
        manager.register_role("body", size=16)

        instance = manager.font_instance("body")
        plain_w, plain_h = instance.text_surface_size("Hello", shadow=False)
        shadow_w, shadow_h = instance.text_surface_size("Hello", shadow=True)

        self.assertGreater(plain_w, 0)
        self.assertGreater(plain_h, 0)
        self.assertGreaterEqual(shadow_w, plain_w)
        self.assertGreaterEqual(shadow_h, plain_h)

    def test_unknown_role_raises(self) -> None:
        manager = FontManager()
        manager.register_role("body", size=16)

        with self.assertRaises(ValueError):
            manager.get_font("missing")

        with self.assertRaises(ValueError):
            manager.render_text("x", (0, 0, 0), role_name="missing")


class _FontFeature(Feature):
    def __init__(self) -> None:
        super().__init__("sample")


class GuiApplicationFontRegistrationTests(unittest.TestCase):
    def setUp(self) -> None:
        pygame.init()
        self.surface = pygame.display.set_mode((320, 240))

    def tearDown(self) -> None:
        pygame.quit()

    def test_register_font_role_updates_theme_and_increments_revision(self) -> None:
        app = GuiApplication(self.surface)
        app.create_scene("main")
        app.switch_scene("main")

        rev_before = app.theme.fonts.revision
        app.register_font_role("body", size=22, scene_name="main")

        self.assertGreater(app.theme.fonts.revision, rev_before)

    def test_part_register_font_role_namespaces_role_name(self) -> None:
        app = GuiApplication(self.surface)
        app.create_scene("main")
        app.switch_scene("main")
        feature = _FontFeature()

        registered = feature.register_font_role(app, "window_title", size=18, scene_name="main")

        self.assertEqual("feature.sample.window_title", registered)
        self.assertTrue(app.theme.fonts.has_role("feature.sample.window_title"))
        self.assertEqual("feature.sample.window_title", feature.font_role("window_title"))

    def test_part_register_font_roles_registers_multiple_roles(self) -> None:
        app = GuiApplication(self.surface)
        app.create_scene("main")
        app.switch_scene("main")
        feature = _FontFeature()

        names = feature.register_font_roles(
            app,
            {
                "window_title": {"size": 18},
                "control": {"size": 16},
            },
            scene_name="main",
        )

        self.assertEqual("feature.sample.window_title", names["window_title"])
        self.assertEqual("feature.sample.control", names["control"])
        self.assertTrue(app.theme.fonts.has_role("feature.sample.window_title"))
        self.assertTrue(app.theme.fonts.has_role("feature.sample.control"))

    def test_font_roles_returns_registered_role_names(self) -> None:
        app = GuiApplication(self.surface)
        app.create_scene("main")
        app.switch_scene("main")

        roles = app.font_roles(scene_name="main")
        self.assertIn("body", roles)
        self.assertIn("title", roles)
        self.assertIn("display", roles)


if __name__ == "__main__":
    unittest.main()
