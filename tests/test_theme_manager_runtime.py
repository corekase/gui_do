import os
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame

from gui_do import ThemeManager, DesignTokens


class DesignTokensTests(unittest.TestCase):

    def test_get_known_token(self) -> None:
        tokens = DesignTokens("t", {"primary": (10, 20, 30)})
        self.assertEqual(tokens.get("primary"), (10, 20, 30))

    def test_get_unknown_token_returns_fallback(self) -> None:
        tokens = DesignTokens("t", {})
        self.assertEqual(tokens.get("missing", (1, 2, 3)), (1, 2, 3))

    def test_get_default_fallback(self) -> None:
        tokens = DesignTokens("t", {})
        self.assertEqual(tokens.get("missing"), (128, 128, 128))

    def test_set_overrides_token(self) -> None:
        tokens = DesignTokens("t", {"primary": (0, 0, 0)})
        tokens.set("primary", (255, 0, 0))
        self.assertEqual(tokens.get("primary"), (255, 0, 0))

    def test_set_adds_new_token(self) -> None:
        tokens = DesignTokens("t", {})
        tokens.set("accent", (100, 150, 200))
        self.assertEqual(tokens.get("accent"), (100, 150, 200))

    def test_token_names_sorted(self) -> None:
        tokens = DesignTokens("t", {"z": (0, 0, 0), "a": (1, 1, 1)})
        names = tokens.token_names()
        self.assertEqual(names, sorted(names))
        self.assertIn("a", names)
        self.assertIn("z", names)

    def test_to_dict_returns_copy(self) -> None:
        tokens = DesignTokens("t", {"primary": (10, 20, 30)})
        d = tokens.to_dict()
        d["primary"] = (0, 0, 0)
        self.assertEqual(tokens.get("primary"), (10, 20, 30))

    def test_copy_creates_independent_instance(self) -> None:
        tokens = DesignTokens("t", {"primary": (10, 20, 30)})
        copy = tokens.copy("t2")
        copy.set("primary", (99, 99, 99))
        self.assertEqual(tokens.get("primary"), (10, 20, 30))
        self.assertEqual(copy.name, "t2")

    def test_from_dict(self) -> None:
        tokens = DesignTokens.from_dict("t", {"primary": [10, 20, 30]})
        self.assertEqual(tokens.get("primary"), (10, 20, 30))


class ThemeManagerRuntimeTests(unittest.TestCase):

    def setUp(self) -> None:
        pygame.init()
        self.mgr = ThemeManager()

    def tearDown(self) -> None:
        pygame.quit()

    # ------------------------------------------------------------------
    # Built-in themes
    # ------------------------------------------------------------------

    def test_dark_theme_registered_by_default(self) -> None:
        self.assertIn("dark", self.mgr.theme_names())

    def test_light_theme_registered_by_default(self) -> None:
        self.assertIn("light", self.mgr.theme_names())

    def test_default_active_theme_is_dark(self) -> None:
        self.assertEqual(self.mgr.active_theme.value, "dark")

    def test_active_tokens_is_design_tokens_instance(self) -> None:
        self.assertIsInstance(self.mgr.active_tokens.value, DesignTokens)

    # ------------------------------------------------------------------
    # register_theme
    # ------------------------------------------------------------------

    def test_register_custom_theme(self) -> None:
        self.mgr.register_theme("my_theme", {"primary": (200, 100, 50)})
        self.assertIn("my_theme", self.mgr.theme_names())

    def test_register_empty_name_raises(self) -> None:
        with self.assertRaises(ValueError):
            self.mgr.register_theme("", {"primary": (0, 0, 0)})

    def test_register_design_tokens_object(self) -> None:
        dt = DesignTokens("custom", {"text": (255, 255, 255)})
        self.mgr.register_theme("custom", dt)
        self.assertTrue(self.mgr.has_theme("custom"))

    def test_register_overwrites_existing(self) -> None:
        self.mgr.register_theme("my_theme", {"primary": (10, 10, 10)})
        self.mgr.register_theme("my_theme", {"primary": (99, 99, 99)})
        self.mgr.switch("my_theme")
        self.assertEqual(self.mgr.token("primary"), (99, 99, 99))

    # ------------------------------------------------------------------
    # switch
    # ------------------------------------------------------------------

    def test_switch_returns_true_on_success(self) -> None:
        result = self.mgr.switch("light")
        self.assertTrue(result)

    def test_switch_returns_false_on_unknown(self) -> None:
        result = self.mgr.switch("nonexistent")
        self.assertFalse(result)

    def test_switch_updates_active_theme(self) -> None:
        self.mgr.switch("light")
        self.assertEqual(self.mgr.active_theme.value, "light")

    def test_switch_updates_active_tokens(self) -> None:
        self.mgr.switch("light")
        self.assertEqual(self.mgr.active_tokens.value.name, "light")

    def test_switch_fires_active_theme_subscriber(self) -> None:
        received = []
        self.mgr.active_theme.subscribe(lambda v: received.append(v))
        self.mgr.switch("light")
        self.assertIn("light", received)

    def test_switch_fires_active_tokens_subscriber(self) -> None:
        received = []
        self.mgr.active_tokens.subscribe(lambda v: received.append(v.name))
        self.mgr.switch("light")
        self.assertIn("light", received)

    # ------------------------------------------------------------------
    # token resolution
    # ------------------------------------------------------------------

    def test_token_resolves_from_active_theme(self) -> None:
        dark_primary = self.mgr.token("primary")
        self.mgr.switch("light")
        light_primary = self.mgr.token("primary")
        # The two themes have different primary values
        self.assertNotEqual(dark_primary, light_primary)

    def test_token_unknown_returns_fallback(self) -> None:
        result = self.mgr.token("does_not_exist", (1, 2, 3))
        self.assertEqual(result, (1, 2, 3))

    # ------------------------------------------------------------------
    # Inspection
    # ------------------------------------------------------------------

    def test_has_theme_true_for_built_in(self) -> None:
        self.assertTrue(self.mgr.has_theme("dark"))

    def test_has_theme_false_for_unknown(self) -> None:
        self.assertFalse(self.mgr.has_theme("nope"))

    def test_get_theme_returns_design_tokens(self) -> None:
        dt = self.mgr.get_theme("dark")
        self.assertIsInstance(dt, DesignTokens)

    def test_get_theme_unknown_returns_none(self) -> None:
        self.assertIsNone(self.mgr.get_theme("nope"))

    def test_theme_names_sorted(self) -> None:
        names = self.mgr.theme_names()
        self.assertEqual(names, sorted(names))


if __name__ == "__main__":
    unittest.main()
