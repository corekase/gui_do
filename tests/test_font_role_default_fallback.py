import unittest

from gui_do.features.feature_lifecycle import setup_standard_font_roles
from gui_do.theme.font_manager import FontManager
from gui_do.theme.font_role_registry import FontRoleRegistry


class TestFontRoleDefaultFallback(unittest.TestCase):
    def test_setup_registers_default_role_from_fonts_map(self):
        registry = FontRoleRegistry()

        setup_standard_font_roles(
            registry,
            {
                "default": {"file": "demo_features/data/fonts/Gimbot.ttf", "size": 15},
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
            },
            {
                "controls.label": {},
            },
        )

        role_def = registry._defs["controls.label"]
        self.assertEqual(17, role_def.size)

    def test_font_manager_resolves_unknown_role_to_default(self):
        manager = FontManager()
        manager.register_role("default", size=16)

        resolved = manager._resolve_role("role.that.is.not.defined")

        self.assertEqual("default", resolved.name)
        self.assertEqual(16, resolved.size)


if __name__ == "__main__":
    unittest.main()
