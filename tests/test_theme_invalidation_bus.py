"""Tests for gui_do.theme.theme_invalidation_bus (S5)."""
import unittest
from unittest.mock import MagicMock

from gui_do.data.presentation_model import ObservableValue
from gui_do.theme.theme_invalidation_bus import ThemeInvalidationBus


def _make_theme_manager():
    """Return a minimal theme manager mock with active_tokens observable."""
    tm = MagicMock()
    tokens = ObservableValue({"primary": "#000000"})
    tm.active_tokens = tokens
    return tm, tokens


class TestThemeInvalidationBusRegistration(unittest.TestCase):

    def setUp(self):
        self.tm, self.tokens = _make_theme_manager()
        self.bus = ThemeInvalidationBus(theme_manager=self.tm)

    def tearDown(self):
        self.bus.dispose()

    def test_initial_count(self):
        self.assertEqual(self.bus.registered_count, 0)

    def test_register_increments_count(self):
        widget = object()
        self.bus.register(widget, lambda: None)
        self.assertEqual(self.bus.registered_count, 1)

    def test_unregister_decrements(self):
        widget = object()
        self.bus.register(widget, lambda: None)
        self.bus.unregister(widget)
        self.assertEqual(self.bus.registered_count, 0)

    def test_unregister_unknown_noop(self):
        self.bus.unregister(object())  # Should not raise

    def test_clear_removes_all(self):
        for _ in range(5):
            self.bus.register(object(), lambda: None)
        self.bus.clear()
        self.assertEqual(self.bus.registered_count, 0)

    def test_register_replaces_fn_for_same_widget(self):
        widget = object()
        old_fn = MagicMock()
        new_fn = MagicMock()
        self.bus.register(widget, old_fn)
        self.bus.register(widget, new_fn)
        self.assertEqual(self.bus.registered_count, 1)
        # Trigger — only new_fn should be called
        self.tokens.value = {"primary": "#ffffff"}
        new_fn.assert_called_once()
        old_fn.assert_not_called()


class TestThemeInvalidationBusOnChange(unittest.TestCase):

    def setUp(self):
        self.tm, self.tokens = _make_theme_manager()

    def tearDown(self):
        if hasattr(self, "bus"):
            self.bus.dispose()

    def test_invalidate_fn_called_on_theme_change(self):
        self.bus = ThemeInvalidationBus(theme_manager=self.tm)
        fn = MagicMock()
        widget = object()
        self.bus.register(widget, fn)
        self.tokens.value = {"primary": "#ffffff"}
        fn.assert_called_once()

    def test_multiple_controls_all_called(self):
        self.bus = ThemeInvalidationBus(theme_manager=self.tm)
        fns = [MagicMock() for _ in range(4)]
        for fn in fns:
            self.bus.register(object(), fn)
        self.tokens.value = {"primary": "#ff0000"}
        for fn in fns:
            fn.assert_called_once()

    def test_graphics_factory_flush_called(self):
        factory = MagicMock()
        factory.flush_cache = MagicMock()
        self.bus = ThemeInvalidationBus(
            theme_manager=self.tm,
            graphics_factory=factory,
        )
        self.tokens.value = {"primary": "#eee"}
        factory.flush_cache.assert_called_once()

    def test_font_manager_flush_called(self):
        fonts = MagicMock()
        fonts.flush_cache = MagicMock()
        self.bus = ThemeInvalidationBus(
            theme_manager=self.tm,
            font_manager=fonts,
        )
        self.tokens.value = {"primary": "#eee"}
        fonts.flush_cache.assert_called_once()

    def test_dirty_tracker_mark_all_dirty_called(self):
        dirty = MagicMock()
        dirty.mark_all_dirty = MagicMock()
        rect = MagicMock()
        self.bus = ThemeInvalidationBus(
            theme_manager=self.tm,
            dirty_tracker=dirty,
            screen_rect=rect,
        )
        self.tokens.value = {"primary": "#eee"}
        dirty.mark_all_dirty.assert_called_once_with(rect)

    def test_dirty_tracker_not_called_without_screen_rect(self):
        dirty = MagicMock()
        dirty.mark_all_dirty = MagicMock()
        self.bus = ThemeInvalidationBus(
            theme_manager=self.tm,
            dirty_tracker=dirty,
            screen_rect=None,
        )
        self.tokens.value = {"primary": "#eee"}
        dirty.mark_all_dirty.assert_not_called()

    def test_invalidate_fn_exception_does_not_propagate(self):
        def bad():
            raise RuntimeError("explode")
        self.bus = ThemeInvalidationBus(theme_manager=self.tm)
        self.bus.register(object(), bad)
        # Should not raise
        self.tokens.value = {"primary": "#abc"}

    def test_set_screen_rect(self):
        dirty = MagicMock()
        dirty.mark_all_dirty = MagicMock()
        self.bus = ThemeInvalidationBus(
            theme_manager=self.tm,
            dirty_tracker=dirty,
        )
        new_rect = MagicMock()
        self.bus.set_screen_rect(new_rect)
        self.tokens.value = {"primary": "#eee"}
        dirty.mark_all_dirty.assert_called_once_with(new_rect)

    def test_trigger_invalidation_manual(self):
        self.bus = ThemeInvalidationBus(theme_manager=self.tm)
        fn = MagicMock()
        self.bus.register(object(), fn)
        self.bus.trigger_invalidation()
        fn.assert_called_once()

    def test_dispose_unregisters_and_stops_notifications(self):
        self.bus = ThemeInvalidationBus(theme_manager=self.tm)
        fn = MagicMock()
        self.bus.register(object(), fn)
        self.bus.dispose()
        self.tokens.value = {"primary": "#ffffff"}
        fn.assert_not_called()  # Bus disposed — no more callbacks


class TestThemeInvalidationBusExports(unittest.TestCase):

    def test_importable_from_gui_do(self):
        import gui_do
        self.assertTrue(hasattr(gui_do, "ThemeInvalidationBus"))


if __name__ == "__main__":
    unittest.main()
