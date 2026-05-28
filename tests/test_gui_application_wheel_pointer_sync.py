import unittest
from unittest.mock import patch

import pygame

from gui_do.app.gui_application import GuiApplication
from gui_do.controls.chrome.window_control import WindowControl


pygame.init()


class TestGuiApplicationWheelPointerSync(unittest.TestCase):
    def test_mouse_wheel_syncs_logical_pointer_from_hardware_when_unlocked(self):
        app = GuiApplication(pygame.Surface((320, 240)))
        app.set_logical_pointer_position((0, 0), apply_constraints=False)

        wheel = pygame.event.Event(pygame.MOUSEWHEEL, {"x": 0, "y": 1})
        with patch("gui_do.app.gui_application.pygame.mouse.get_pos", return_value=(123, 77)):
            app.process_event(wheel)

        self.assertEqual((123, 77), app.logical_pointer_pos)

    def test_visibility_event_does_not_move_new_window_when_layout_disabled(self):
        app = GuiApplication(pygame.Surface((320, 240)))
        window = WindowControl("w", (100, 80), "Window")
        window.visible = True
        app.scene.add(window)
        app.set_window_tiling_enabled(False, relayout=False)

        app.tile_windows(newly_visible=(window,), as_visibility_event=True)

        self.assertEqual((0, 0), window.rect.topleft)

    def test_visibility_event_with_raised_windows_does_not_expand_newly_visible_snapshot(self):
        app = GuiApplication(pygame.Surface((320, 240)))
        raised = WindowControl("raised", (100, 80), "Raised")
        other = WindowControl("other", (100, 80), "Other")
        app.scene.add(raised)
        app.scene.add(other)

        with patch.object(app.window_tiling, "visible_windows_snapshot", return_value=(raised, other)):
            with patch.object(app.window_tiling, "arrange_windows") as arrange_mock:
                app.tile_windows(raised_windows=(raised,), as_visibility_event=True, force=True)

        arrange_mock.assert_called_once()
        kwargs = arrange_mock.call_args.kwargs
        self.assertIsNone(kwargs.get("newly_visible"))
        self.assertEqual((raised,), kwargs.get("raised_windows"))

    def test_force_tiling_does_not_snapshot_newly_visible_when_as_visibility_event(self):
        app = GuiApplication(pygame.Surface((320, 240)))
        first = WindowControl("first", (100, 80), "First")
        second = WindowControl("second", (100, 80), "Second")
        app.scene.add(first)
        app.scene.add(second)

        with patch.object(app.window_tiling, "visible_windows_snapshot", return_value=(first, second)):
            with patch.object(app.window_tiling, "arrange_windows") as arrange_mock:
                app.tile_windows(as_visibility_event=True, force=True)

        arrange_mock.assert_called_once()
        kwargs = arrange_mock.call_args.kwargs
        self.assertIsNone(kwargs.get("newly_visible"))
        self.assertEqual((second,), kwargs.get("raised_windows"))

    def test_raise_window_reorders_parent_before_relayout(self):
        app = GuiApplication(pygame.Surface((320, 240)))
        app.set_window_tiling_enabled(True, relayout=False)
        first = WindowControl("first", (100, 80), "First")
        second = WindowControl("second", (100, 80), "Second")
        app.scene.add(first)
        app.scene.add(second)

        observed_orders = []

        def _arrange_windows(**_kwargs):
            observed_orders.append(list(app.scene.nodes))

        with patch.object(app.window_tiling, "arrange_windows", side_effect=_arrange_windows):
            self.assertTrue(app.raise_window(first))

        self.assertEqual(1, len(observed_orders))
        self.assertIs(first, observed_orders[0][-1])

    def test_lower_window_reorders_parent_before_relayout(self):
        app = GuiApplication(pygame.Surface((320, 240)))
        app.set_window_tiling_enabled(True, relayout=False)
        first = WindowControl("first", (100, 80), "First")
        second = WindowControl("second", (100, 80), "Second")
        app.scene.add(first)
        app.scene.add(second)

        observed_orders = []

        def _arrange_drop(*_args, **_kwargs):
            observed_orders.append(list(app.scene.nodes))

        with patch.object(app.window_tiling, "arrange_windows_for_drop", side_effect=_arrange_drop):
            self.assertTrue(app.lower_window(second))

        self.assertEqual(1, len(observed_orders))
        self.assertIs(second, observed_orders[0][0])

    def test_raise_window_reorders_generic_parent_children_without_helper(self):
        app = GuiApplication(pygame.Surface((320, 240)))

        class _Parent:
            def __init__(self, children):
                self.children = list(children)

        class _Window:
            def __init__(self, parent):
                self.parent = parent

        first = _Window(None)
        second = _Window(None)
        parent = _Parent([first, second])
        first.parent = parent
        second.parent = parent

        self.assertTrue(app.raise_window(first, relayout=False))
        self.assertIs(first, parent.children[-1])

    def test_raise_window_updates_layout_registration_order_immediately(self):
        app = GuiApplication(pygame.Surface((320, 240)))
        first = WindowControl("first", (100, 80), "First")
        second = WindowControl("second", (100, 80), "Second")
        app.scene.add(first)
        app.scene.add(second)
        app.window_tiling.prime_registration()

        self.assertEqual((first, second), app.window_tiling.visible_windows_snapshot())

        self.assertTrue(app.raise_window(first, relayout=False))

        self.assertEqual((second, first), app.window_tiling.visible_windows_snapshot())

    def test_lower_window_updates_layout_registration_order_immediately(self):
        app = GuiApplication(pygame.Surface((320, 240)))
        first = WindowControl("first", (100, 80), "First")
        second = WindowControl("second", (100, 80), "Second")
        app.scene.add(first)
        app.scene.add(second)
        app.window_tiling.prime_registration()

        self.assertEqual((first, second), app.window_tiling.visible_windows_snapshot())

        self.assertTrue(app.lower_window(second, relayout=False))

        self.assertEqual((second, first), app.window_tiling.visible_windows_snapshot())

    def test_raise_and_lower_relayout_use_explicit_z_intent_hints(self):
        app = GuiApplication(pygame.Surface((320, 240)))
        app.set_window_tiling_enabled(True, relayout=False)
        first = WindowControl("first", (100, 80), "First")
        second = WindowControl("second", (100, 80), "Second")
        app.scene.add(first)
        app.scene.add(second)

        with (
            patch.object(app.window_tiling, "arrange_windows") as arrange_mock,
            patch.object(app.window_tiling, "arrange_windows_for_drop") as drop_mock,
        ):
            self.assertTrue(app.raise_window(first))
            self.assertTrue(app.lower_window(second))

        self.assertEqual(1, arrange_mock.call_count)
        self.assertEqual(1, drop_mock.call_count)
        first_kwargs = arrange_mock.call_args_list[0].kwargs
        second_kwargs = drop_mock.call_args_list[0].kwargs
        self.assertEqual({"raised_windows": (first,), "force": True}, first_kwargs)
        self.assertEqual({"force": True, "demoted_windows": (second,)}, second_kwargs)

    def test_layout_registration_tracks_live_scene_graph_order(self):
        app = GuiApplication(pygame.Surface((320, 240)))
        first = WindowControl("first", (100, 80), "First")
        second = WindowControl("second", (100, 80), "Second")
        third = WindowControl("third", (100, 80), "Third")
        app.scene.add(first)
        app.scene.add(second)
        app.scene.add(third)

        self.assertEqual((first, second, third), app.window_tiling.visible_windows_snapshot())

        app.scene.nodes[:] = [third, first, second]

        # The next snapshot must reflect live graph order, not stale metadata.
        self.assertEqual((third, first, second), app.window_tiling.visible_windows_snapshot())


if __name__ == "__main__":
    unittest.main()
