import unittest

from gui_do.features.feature_lifecycle import setup_standard_font_roles
from gui_do.theme.font_manager import FontManager
from gui_do.theme.font_role_registry import FontRoleRegistry


class TestFontRoleDefaultFallback(unittest.TestCase):
    def test_setup_seeds_title_role_from_window_font_with_size_18(self):
        registry = FontRoleRegistry()

        setup_standard_font_roles(
            registry,
            {
                "window": {"file": "demo_features/data/fonts/Ubuntu-B.ttf", "size": 27},
            },
            {},
        )

        self.assertIn("title", registry.defined_names())
        title_def = registry._defs["title"]
        self.assertEqual(18, title_def.size)
        self.assertTrue(str(title_def.file_path).endswith("demo_features/data/fonts/Ubuntu-B.ttf"))

    def test_setup_prefers_explicit_title_role_over_window_alias(self):
        registry = FontRoleRegistry()

        setup_standard_font_roles(
            registry,
            {
                "window": {"file": "demo_features/data/fonts/Ubuntu-B.ttf", "size": 27},
                "default": {"file": "demo_features/data/fonts/Gimbot.ttf", "size": 16},
            },
            {
                "title": {"font": "default", "size": 22},
            },
        )

        title_def = registry._defs["title"]
        self.assertEqual(22, title_def.size)
        self.assertTrue(str(title_def.file_path).endswith("demo_features/data/fonts/Gimbot.ttf"))

    def test_setup_uses_explicit_window_title_when_title_not_defined(self):
        registry = FontRoleRegistry()

        setup_standard_font_roles(
            registry,
            {
                "window": {"file": "demo_features/data/fonts/Ubuntu-B.ttf", "size": 27},
                "default": {"file": "demo_features/data/fonts/Gimbot.ttf", "size": 16},
            },
            {
                "window_title": {"font": "default", "size": 20},
            },
        )

        title_def = registry._defs["title"]
        self.assertEqual(20, title_def.size)
        self.assertTrue(str(title_def.file_path).endswith("demo_features/data/fonts/Gimbot.ttf"))

    def test_setup_registers_default_role_from_fonts_map(self):
        registry = FontRoleRegistry()

        setup_standard_font_roles(
            registry,
            {
                "default": {"file": "demo_features/data/fonts/Gimbot.ttf", "size": 15},
                "window": {"file": "demo_features/data/fonts/Ubuntu-B.ttf", "size": 18},
            },
            {
                "notification_panel.body": {},
            },
        )

        self.assertIn("default", registry.defined_names())
        self.assertIn("notification_panel.body", registry.defined_names())

    def test_setup_uses_default_font_size_when_role_size_missing(self):
        registry = FontRoleRegistry()

        setup_standard_font_roles(
            registry,
            {
                "default": {"file": "demo_features/data/fonts/Gimbot.ttf", "size": 17},
                "window": {"file": "demo_features/data/fonts/Ubuntu-B.ttf", "size": 18},
            },
            {
                "controls.label": {},
            },
        )

        role_def = registry._defs["controls.label"]
        self.assertEqual(17, role_def.size)

    def test_setup_raises_when_title_role_cannot_be_resolved(self):
        registry = FontRoleRegistry()

        with self.assertRaises(ValueError):
            setup_standard_font_roles(
                registry,
                {
                    "default": {"file": "demo_features/data/fonts/Gimbot.ttf", "size": 17},
                },
                {
                    "controls.label": {},
                },
            )

    def test_font_manager_resolves_unknown_role_to_default(self):
        manager = FontManager()
        manager.register_role("default", size=16)

        resolved = manager._resolve_role("role.that.is.not.defined")

        self.assertEqual("default", resolved.name)
        self.assertEqual(16, resolved.size)


if __name__ == "__main__":
    unittest.main()
