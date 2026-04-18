import unittest
from types import SimpleNamespace
from unittest.mock import patch

from pygame import Rect

from gui.utility.constants import GuiError
from gui.utility.task_panel_config_coordinator import TaskPanelConfigCoordinator
from gui.utility import guimanager as gm


class OldPanelStub:
    def __init__(self, widgets=None, visible=True) -> None:
        self.widgets = [] if widgets is None else widgets
        self.visible = visible
        self.dispose_calls = 0

    def dispose(self) -> None:
        self.dispose_calls += 1


class NewPanelStub:
    def __init__(self) -> None:
        self.widgets = []
        self.visible = True
        self.surface = object()
        self.set_visible_calls = []

    def set_visible(self, visible: bool) -> None:
        self.set_visible_calls.append(visible)
        self.visible = visible


class TaskPanelConfigurationTests(unittest.TestCase):
    def _build_manager_stub(self):
        gui = gm.GuiManager.__new__(gm.GuiManager)
        gui.task_panel = None
        gui._task_panel_capture = True
        gui.task_panel_config = TaskPanelConfigCoordinator(gui)
        return gui

    def test_configure_task_panel_rejects_invalid_auto_hide_type(self) -> None:
        gui = self._build_manager_stub()

        with self.assertRaises(GuiError):
            gm.GuiManager.configure_task_panel(gui, auto_hide="yes")  # type: ignore[arg-type]

    def test_configure_task_panel_is_atomic_when_new_panel_creation_fails(self) -> None:
        gui = self._build_manager_stub()
        old_panel = OldPanelStub(widgets=[SimpleNamespace(window=None, surface=None)], visible=True)
        gui.task_panel = old_panel

        with patch.object(gm, "_ManagedTaskPanel", side_effect=GuiError("panel create failed")):
            with self.assertRaises(GuiError):
                gm.GuiManager.configure_task_panel(gui, height=40)

        self.assertIs(gui.task_panel, old_panel)
        self.assertEqual(old_panel.dispose_calls, 0)

    def test_configure_task_panel_reuses_widgets_and_visibility_on_success(self) -> None:
        gui = self._build_manager_stub()
        w1 = SimpleNamespace(window=None, surface=None)
        w2 = SimpleNamespace(window=None, surface=None)
        old_panel = OldPanelStub(widgets=[w1, w2], visible=False)
        gui.task_panel = old_panel

        created_panels = []

        def create_panel(*_args, **_kwargs):
            panel = NewPanelStub()
            created_panels.append(panel)
            return panel

        with patch.object(gm, "_ManagedTaskPanel", side_effect=create_panel):
            gm.GuiManager.configure_task_panel(gui, height=40)

        self.assertEqual(old_panel.dispose_calls, 1)
        self.assertEqual(len(created_panels), 1)
        new_panel = created_panels[0]
        self.assertIs(gui.task_panel, new_panel)
        self.assertEqual(new_panel.widgets, [w1, w2])
        self.assertEqual(new_panel.set_visible_calls, [False])
        self.assertFalse(gui._task_panel_capture)
        self.assertIs(w1.window, new_panel)
        self.assertIs(w2.window, new_panel)
        self.assertIs(w1.surface, new_panel.surface)
        self.assertIs(w2.surface, new_panel.surface)


class ManagedTaskPanelMethodTests(unittest.TestCase):
    def test_set_visible_validates_bool_and_refreshes_when_enabled(self) -> None:
        panel = gm._ManagedTaskPanel.__new__(gm._ManagedTaskPanel)
        panel.visible = False
        refresh_calls = []
        panel.refresh_targets = lambda: refresh_calls.append(True)

        with self.assertRaises(GuiError):
            panel.set_visible("yes")  # type: ignore[arg-type]

        panel.set_visible(True)

        self.assertTrue(panel.visible)
        self.assertEqual(refresh_calls, [True])

    def test_set_auto_hide_false_snaps_to_shown_y(self) -> None:
        panel = gm._ManagedTaskPanel.__new__(gm._ManagedTaskPanel)
        panel.auto_hide = True
        panel.y = 99
        panel._shown_y = 12
        refresh_calls = []
        panel.refresh_targets = lambda: refresh_calls.append(True)

        with self.assertRaises(GuiError):
            panel.set_auto_hide(1)  # type: ignore[arg-type]

        panel.set_auto_hide(False)

        self.assertFalse(panel.auto_hide)
        self.assertEqual(panel.y, 12)
        self.assertEqual(refresh_calls, [True])

    def test_set_reveal_pixels_and_movement_step_validate_inputs(self) -> None:
        panel = gm._ManagedTaskPanel.__new__(gm._ManagedTaskPanel)
        panel.height = 20
        panel.reveal_pixels = 4
        panel.movement_step = 2
        refresh_calls = []
        panel.refresh_targets = lambda: refresh_calls.append(True)

        with self.assertRaises(GuiError):
            panel.set_reveal_pixels("x")  # type: ignore[arg-type]
        with self.assertRaises(GuiError):
            panel.set_reveal_pixels(0)
        with self.assertRaises(GuiError):
            panel.set_reveal_pixels(20)

        panel.set_reveal_pixels(5)
        self.assertEqual(panel.reveal_pixels, 5)
        self.assertEqual(refresh_calls, [True])

        with self.assertRaises(GuiError):
            panel.set_movement_step("x")  # type: ignore[arg-type]
        with self.assertRaises(GuiError):
            panel.set_movement_step(0)

        panel.set_movement_step(7)
        self.assertEqual(panel.movement_step, 7)

    def test_set_timer_interval_replaces_timer_registration(self) -> None:
        panel = gm._ManagedTaskPanel.__new__(gm._ManagedTaskPanel)
        panel._timer_id = ("task-panel-motion", 123)
        panel.timer_interval = 10.0
        panel.animate = lambda: None
        timer_calls = []
        panel.gui = SimpleNamespace(
            timers=SimpleNamespace(
                remove_timer=lambda timer_id: timer_calls.append(("remove", timer_id)),
                add_timer=lambda timer_id, interval, callback: timer_calls.append(("add", timer_id, interval, callback)),
            )
        )

        with self.assertRaises(GuiError):
            panel.set_timer_interval(0)

        panel.set_timer_interval(3.5)

        self.assertEqual(panel.timer_interval, 3.5)
        self.assertEqual(timer_calls[0], ("remove", panel._timer_id))
        self.assertEqual(timer_calls[1][0:3], ("add", panel._timer_id, 3.5))

    def test_animate_moves_toward_target_and_draw_background_guards_pristine(self) -> None:
        panel = gm._ManagedTaskPanel.__new__(gm._ManagedTaskPanel)
        panel.visible = True
        panel.auto_hide = True
        panel._hovered = False
        panel._shown_y = 10
        panel._hidden_y = 30
        panel.y = 15
        panel.movement_step = 4
        panel.refresh_targets = lambda: None

        panel.animate()
        self.assertEqual(panel.y, 19)

        panel._hovered = True
        panel.animate()
        self.assertEqual(panel.y, 15)

        panel.visible = False
        panel.animate()
        self.assertEqual(panel.y, 15)

        panel.pristine = None
        panel.gui = SimpleNamespace(restore_pristine=lambda *_args, **_kwargs: None)
        panel.surface = SimpleNamespace(get_rect=lambda: Rect(0, 0, 5, 5))
        with self.assertRaises(GuiError):
            panel.draw_background()


if __name__ == "__main__":
    unittest.main()
