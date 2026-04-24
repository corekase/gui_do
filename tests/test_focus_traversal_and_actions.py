import unittest

import pygame
from pygame import Rect, Surface

from gui.app.gui_application import GuiApplication
from gui.controls.button_group_control import ButtonGroupControl
from gui.controls.panel_control import PanelControl
from gui.controls.window_control import WindowControl
from gui.core.ui_node import UiNode


class _FocusableProbe(UiNode):
    def __init__(self, control_id: str, rect: Rect, tab_index: int) -> None:
        super().__init__(control_id, rect)
        self.set_tab_index(tab_index)
        self.key_hits = 0

    def handle_event(self, event, _app) -> bool:
        if event.is_key_down(pygame.K_RETURN):
            self.key_hits += 1
            return True
        return False


class FocusTraversalAndActionsTests(unittest.TestCase):
    def test_tab_cycles_focus_within_active_window(self) -> None:
        pygame.init()
        try:
            app = GuiApplication(Surface((320, 180)))
            root = app.add(PanelControl("root", Rect(0, 0, 320, 180)))
            win = root.add(WindowControl("win", Rect(10, 10, 240, 140), "Win"))
            first = win.add(_FocusableProbe("first", Rect(20, 40, 80, 20), tab_index=0))
            second = win.add(_FocusableProbe("second", Rect(20, 70, 80, 20), tab_index=1))
            win.active = True

            app.process_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_TAB, "mod": 0}))
            self.assertIs(app.focus.focused_node, first)

            app.process_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_TAB, "mod": 0}))
            self.assertIs(app.focus.focused_node, second)

            app.process_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_TAB, "mod": pygame.KMOD_SHIFT}))
            self.assertIs(app.focus.focused_node, first)
        finally:
            pygame.quit()

    def test_keyboard_manager_marks_tab_event_as_prevented(self) -> None:
        pygame.init()
        try:
            app = GuiApplication(Surface((320, 180)))
            root = app.add(PanelControl("root", Rect(0, 0, 320, 180)))
            win = root.add(WindowControl("win", Rect(10, 10, 240, 140), "Win"))
            win.add(_FocusableProbe("first", Rect(20, 40, 80, 20), tab_index=0))
            win.active = True

            event = app.event_manager.to_gui_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_TAB, "mod": 0}))
            consumed = app.keyboard.route_key_event(app.scene, event, app, None)

            self.assertTrue(consumed)
            self.assertTrue(event.default_prevented)
            self.assertTrue(event.propagation_stopped)
        finally:
            pygame.quit()

    def test_shift_tab_with_no_prior_focus_sets_first_focus(self) -> None:
        pygame.init()
        try:
            app = GuiApplication(Surface((320, 180)))
            root = app.add(PanelControl("root", Rect(0, 0, 320, 180)))
            win = root.add(WindowControl("win", Rect(10, 10, 240, 140), "Win"))
            first = win.add(_FocusableProbe("first", Rect(20, 40, 80, 20), tab_index=0))
            win.add(_FocusableProbe("second", Rect(20, 70, 80, 20), tab_index=1))
            win.active = True

            self.assertIsNone(app.focus.focused_node)
            consumed = app.process_event(
                pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_TAB, "mod": pygame.KMOD_SHIFT})
            )

            self.assertTrue(consumed)
            self.assertIs(app.focus.focused_node, first)
            self.assertTrue(first.focused)
        finally:
            pygame.quit()

    def test_tab_with_no_prior_focus_starts_at_first(self) -> None:
        pygame.init()
        try:
            app = GuiApplication(Surface((320, 180)))
            root = app.add(PanelControl("root", Rect(0, 0, 320, 180)))
            win = root.add(WindowControl("win", Rect(10, 10, 240, 140), "Win"))
            first = win.add(_FocusableProbe("first", Rect(20, 40, 80, 20), tab_index=0))
            win.add(_FocusableProbe("second", Rect(20, 70, 80, 20), tab_index=1))
            win.active = True

            self.assertIsNone(app.focus.focused_node)
            consumed = app.process_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_TAB, "mod": 0}))

            self.assertTrue(consumed)
            self.assertIs(app.focus.focused_node, first)
        finally:
            pygame.quit()

    def test_focus_clears_when_owning_window_becomes_inactive(self) -> None:
        pygame.init()
        try:
            app = GuiApplication(Surface((320, 180)))
            root = app.add(PanelControl("root", Rect(0, 0, 320, 180)))
            win = root.add(WindowControl("win", Rect(10, 10, 240, 140), "Win"))
            first = win.add(_FocusableProbe("first", Rect(20, 40, 80, 20), tab_index=0))
            win.active = True

            app.process_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_TAB, "mod": 0}))
            self.assertIs(app.focus.focused_node, first)

            win.active = False
            app.update(0.016)

            self.assertIsNone(app.focus.focused_node)
        finally:
            pygame.quit()

    def test_focus_scope_switch_restores_previous_window_and_screen_targets(self) -> None:
        pygame.init()
        try:
            app = GuiApplication(Surface((320, 180)))
            root = app.add(PanelControl("root", Rect(0, 0, 320, 180)))

            screen_first = root.add(_FocusableProbe("screen_first", Rect(5, 5, 40, 20), tab_index=0))
            screen_second = root.add(_FocusableProbe("screen_second", Rect(50, 5, 40, 20), tab_index=1))

            win = root.add(WindowControl("win", Rect(10, 30, 240, 140), "Win"))
            win_first = win.add(_FocusableProbe("win_first", Rect(20, 40, 80, 20), tab_index=0))
            win_second = win.add(_FocusableProbe("win_second", Rect(20, 70, 80, 20), tab_index=1))
            win.active = True

            app.process_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_TAB, "mod": 0}))
            self.assertIs(app.focus.focused_node, win_first)
            app.process_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_TAB, "mod": 0}))
            self.assertIs(app.focus.focused_node, win_second)

            win.active = False
            app.update(0.016)
            self.assertIsNone(app.focus.focused_node)

            app.process_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_TAB, "mod": 0}))
            self.assertIs(app.focus.focused_node, screen_first)
            app.process_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_TAB, "mod": 0}))
            self.assertIs(app.focus.focused_node, screen_second)

            win.active = True
            app.process_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_TAB, "mod": 0}))
            self.assertIs(app.focus.focused_node, win_second)

            win.active = False
            app.update(0.016)
            app.process_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_TAB, "mod": 0}))
            self.assertIs(app.focus.focused_node, screen_second)
        finally:
            pygame.quit()

    def test_screen_scope_memory_restored_after_mouse_click_outside_window(self) -> None:
        """Clicking on screen background (outside window) then Tab restores last screen-scope focus."""
        pygame.init()
        try:
            app = GuiApplication(Surface((400, 300)))
            root = app.add(PanelControl("root", Rect(0, 0, 400, 300)))

            # Screen-level controls at the top of the surface
            screen_first = root.add(_FocusableProbe("screen_first", Rect(5, 5, 40, 20), tab_index=0))
            screen_second = root.add(_FocusableProbe("screen_second", Rect(50, 5, 40, 20), tab_index=1))

            # Window occupying a lower region that doesn't overlap the background click target
            win = root.add(WindowControl("win", Rect(10, 50, 240, 200), "Win"))
            win_first = win.add(_FocusableProbe("win_first", Rect(20, 70, 80, 20), tab_index=0))
            win.add(_FocusableProbe("win_second", Rect(20, 100, 80, 20), tab_index=1))

            # Tab to screen_second so screen-scope memory is set
            app.process_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_TAB, "mod": 0}))
            self.assertIs(app.focus.focused_node, screen_first)
            app.process_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_TAB, "mod": 0}))
            self.assertIs(app.focus.focused_node, screen_second)

            # Activate window via mouse click on its interior (but not on a focusable probe)
            # Win rect is Rect(10, 50, 240, 200) - titlebar area around (10, 55)
            app.process_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"button": 1, "pos": (15, 55)}))
            self.assertTrue(win.active)

            # Tab within window scope
            app.process_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_TAB, "mod": 0}))
            self.assertIs(app.focus.focused_node, win_first)

            # Click on screen background (outside window rect) — position (350, 10) has nothing
            app.process_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"button": 1, "pos": (350, 10)}))
            self.assertFalse(win.active)
            self.assertIs(app.focus.focused_node, win_first)
            self.assertTrue(app.focus_visualizer.has_active_hint())

            # Tab should restore the last screen-scope focus (screen_second)
            app.process_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_TAB, "mod": 0}))
            self.assertIs(app.focus.focused_node, screen_second)
            self.assertTrue(app.focus_visualizer.has_active_hint())
        finally:
            pygame.quit()

    def test_screen_button_group_memory_restored_after_exiting_window_scope(self) -> None:
        """Returning from a window scope restores a remembered screen-level ButtonGroup target."""
        pygame.init()
        try:
            app = GuiApplication(Surface((420, 280)))
            root = app.add(PanelControl("root", Rect(0, 0, 420, 280)))

            screen_btn = root.add(_FocusableProbe("screen_btn", Rect(10, 10, 60, 22), tab_index=0))
            screen_group_a = root.add(ButtonGroupControl("screen_group_a", Rect(90, 10, 70, 24), "screen_g", "A", selected=True))
            screen_group_b = root.add(ButtonGroupControl("screen_group_b", Rect(170, 10, 70, 24), "screen_g", "B", selected=False))
            screen_group_a.set_tab_index(1)
            screen_group_b.set_tab_index(2)

            win = root.add(WindowControl("styles_like_win", Rect(20, 60, 300, 200), "Styles"))
            win_probe = win.add(_FocusableProbe("win_probe", Rect(40, 90, 100, 24), tab_index=0))

            # Seed screen scope memory on the ButtonGroup target.
            app.process_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_TAB, "mod": 0}))
            self.assertIs(app.focus.focused_node, screen_btn)
            app.process_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_TAB, "mod": 0}))
            self.assertIs(app.focus.focused_node, screen_group_a)

            # Enter window lifecycle and focus inside the window.
            app.process_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"button": 1, "pos": win.title_bar_rect().center}))
            self.assertTrue(win.active)
            app.process_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_TAB, "mod": 0}))
            self.assertIs(app.focus.focused_node, win_probe)

            # Exit to screen lifecycle with a background click (outside any focusable object).
            app.process_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"button": 1, "pos": (390, 20)}))
            self.assertFalse(win.active)

            # First Tab should resume screen lifecycle at remembered ButtonGroup target.
            app.process_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_TAB, "mod": 0}))
            self.assertIs(app.focus.focused_node, screen_group_a)
            self.assertTrue(app.focus_visualizer.has_active_hint())
        finally:
            ButtonGroupControl.clear_group_registry()
            pygame.quit()

    def test_screen_scope_entry_restores_remembered_target_even_if_occluded(self) -> None:
        """Screen scope entry should preserve remembered accessibility order regardless of overlap."""
        pygame.init()
        try:
            app = GuiApplication(Surface((500, 280)))
            root = app.add(PanelControl("root", Rect(0, 0, 500, 280)))

            # Three screen controls: first two clear, third sits behind the window.
            screen_a = root.add(_FocusableProbe("screen_a", Rect(10, 10, 60, 24), tab_index=0))
            screen_b = root.add(_FocusableProbe("screen_b", Rect(80, 10, 60, 24), tab_index=1))
            screen_behind = root.add(ButtonGroupControl("screen_behind", Rect(120, 80, 90, 24), "screen_g3", "Behind", selected=True))
            screen_behind.set_tab_index(2)
            # screen_after is to the right of the window — not occluded.
            screen_after = root.add(_FocusableProbe("screen_after", Rect(430, 80, 60, 24), tab_index=3))

            # Window covers only screen_behind.
            win = root.add(WindowControl("styles_like_win", Rect(100, 60, 260, 180), "Styles"))
            win.add(_FocusableProbe("win_probe", Rect(130, 90, 100, 24), tab_index=0))

            # Seed screen scope memory on the occluded screen control.
            app.process_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_TAB, "mod": 0}))
            app.process_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_TAB, "mod": 0}))
            app.process_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_TAB, "mod": 0}))
            self.assertIs(app.focus.focused_node, screen_behind)

            # Enter window lifecycle.
            app.process_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"button": 1, "pos": win.title_bar_rect().center}))
            self.assertTrue(win.active)
            app.process_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_TAB, "mod": 0}))

            # Exit to screen lifecycle; window stays visible and covers screen_behind.
            app.process_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"button": 1, "pos": (10, 250)}))
            self.assertFalse(win.active)
            self.assertTrue(win.visible)

            # First Tab: remembered screen target is restored even when visually covered.
            app.process_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_TAB, "mod": 0}))
            self.assertIs(app.focus.focused_node, screen_behind)
            self.assertTrue(app.focus_visualizer.has_active_hint())
        finally:
            ButtonGroupControl.clear_group_registry()
            pygame.quit()

    def test_tab_keeps_initiation_gate_when_current_screen_focus_is_occluded(self) -> None:
        """Occlusion must not bypass first-Tab initiation hint gate."""
        pygame.init()
        try:
            app = GuiApplication(Surface((500, 280)))
            root = app.add(PanelControl("root", Rect(0, 0, 500, 280)))

            screen_a = root.add(_FocusableProbe("screen_a", Rect(10, 10, 60, 24), tab_index=0))
            screen_behind = root.add(_FocusableProbe("screen_behind", Rect(120, 80, 90, 24), tab_index=1))
            screen_after = root.add(_FocusableProbe("screen_after", Rect(430, 80, 60, 24), tab_index=2))

            win = root.add(WindowControl("styles_like_win", Rect(100, 60, 260, 180), "Styles"))
            win.active = False

            # Seed focus to an occluded screen control without keyboard hint.
            app.focus.set_focus(screen_behind)
            self.assertIs(app.focus.focused_node, screen_behind)
            self.assertFalse(app.focus_visualizer.has_active_hint())

            # First Tab still applies initiation gate: reveal hint only, no movement.
            app.process_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_TAB, "mod": 0}))
            self.assertIs(app.focus.focused_node, screen_behind)
            self.assertTrue(app.focus_visualizer.has_active_hint())

            # Next traversal event cycles in canonical order.
            app.process_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_TAB, "mod": 0}))
            self.assertIs(app.focus.focused_node, screen_after)

            # Backward traversal returns to the previous control.
            app.process_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_TAB, "mod": pygame.KMOD_SHIFT}))
            self.assertIs(app.focus.focused_node, screen_behind)
        finally:
            pygame.quit()

    def test_bound_action_executes_before_screen_handler(self) -> None:
        pygame.init()
        try:
            app = GuiApplication(Surface((320, 180)))
            seen = {"action": 0, "screen": 0}

            def action_handler(_event) -> bool:
                seen["action"] += 1
                return True

            def screen_handler(_event) -> bool:
                seen["screen"] += 1
                return True

            app.actions.register_action("quit", action_handler)
            app.actions.bind_key(pygame.K_ESCAPE, "quit")
            app.set_screen_lifecycle(event_handler=screen_handler)

            consumed = app.process_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_ESCAPE}))

            self.assertTrue(consumed)
            self.assertEqual(seen["action"], 1)
            self.assertEqual(seen["screen"], 0)
        finally:
            pygame.quit()

    def test_key_action_prevent_default_blocks_screen_handler(self) -> None:
        pygame.init()
        try:
            app = GuiApplication(Surface((320, 180)))
            seen = {"action": 0, "screen": 0}

            def action_handler(event) -> bool:
                seen["action"] += 1
                event.prevent_default()
                return False

            def screen_handler(_event) -> bool:
                seen["screen"] += 1
                return True

            app.actions.register_action("noop", action_handler)
            app.actions.bind_key(pygame.K_ESCAPE, "noop")
            app.set_screen_lifecycle(event_handler=screen_handler)

            consumed = app.process_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_ESCAPE}))

            self.assertTrue(consumed)
            self.assertEqual(seen["action"], 1)
            self.assertEqual(seen["screen"], 0)
        finally:
            pygame.quit()

    def test_active_window_keyboard_ownership_marks_event_prevented(self) -> None:
        pygame.init()
        try:
            app = GuiApplication(Surface((320, 180)))
            root = app.add(PanelControl("root", Rect(0, 0, 320, 180)))

            def window_handler(_event) -> bool:
                return False

            win = root.add(WindowControl("win", Rect(20, 20, 180, 120), "A", event_handler=window_handler))
            win.active = True
            event = app.event_manager.to_gui_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_ESCAPE}))

            consumed = app.keyboard.route_key_event(app.scene, event, app, None)

            self.assertTrue(consumed)
            self.assertTrue(event.default_prevented)
            self.assertTrue(event.propagation_stopped)
        finally:
            pygame.quit()


if __name__ == "__main__":
    unittest.main()
