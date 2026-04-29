"""Tests for focus visualization -- hint is keyboard-driven, not mouse-driven."""
import unittest
from unittest.mock import patch

import pygame
from pygame import Rect, Surface

from gui_do.app.gui_application import GuiApplication
from gui_do.controls.input.button_control import ButtonControl
from gui_do.controls.display.label_control import LabelControl
from gui_do.controls.composite.panel_control import PanelControl
from gui_do.controls.chrome.window_control import WindowControl
from gui_do.focus.focus_manager import FocusManager
from gui_do.focus.focus_visualizer import FocusVisualizer
from gui_do.focus.focus_hint_constants import FOCUS_TRAVERSAL_HINT_TIMEOUT_SECONDS
from gui_do.app.scene import Scene
from gui_do.controls.base.ui_node import UiNode


class FocusVisualizerKeyboardHintTests(unittest.TestCase):
    """Hint visibility is keyboard-driven even when focus exists."""

    def _make(self):
        manager = FocusManager()
        app = type("App", (), {"focus": manager})()
        return FocusVisualizer(app), manager

    def test_cycle_focus_makes_hint_active(self) -> None:
        vis, mgr = self._make()
        n1 = UiNode("n1", Rect(0, 0, 100, 100))
        n1.set_tab_index(0)
        scene = Scene()
        scene.add(n1)
        mgr.cycle_focus(scene, forward=True)
        self.assertIs(mgr.focused_node, n1)
        self.assertTrue(vis.has_active_hint())

    def test_set_focus_from_non_keyboard_does_not_show_hint(self) -> None:
        vis, mgr = self._make()
        mgr.set_focus(UiNode("n", Rect(0, 0, 100, 100)))
        self.assertFalse(vis.has_active_hint())

    def test_set_focus_via_keyboard_makes_hint_active(self) -> None:
        vis, mgr = self._make()
        mgr.set_focus(UiNode("n", Rect(0, 0, 100, 100)), via_keyboard=True)
        self.assertTrue(vis.has_active_hint())

    def test_clear_focus_deactivates_hint(self) -> None:
        vis, mgr = self._make()
        mgr.set_focus(UiNode("n", Rect(0, 0, 100, 100)))
        mgr.clear_focus()
        self.assertFalse(vis.has_active_hint())


class MouseClickFocusIntegrationTests(unittest.TestCase):
    """Integration tests: mouse focus does not activate hint; keyboard does."""

    def setUp(self) -> None:
        pygame.init()
        self.surface = Surface((400, 300))
        self.app = GuiApplication(self.surface)
        self.root = self.app.add(PanelControl("root", Rect(0, 0, 400, 300)))
        self.window = self.root.add(WindowControl("main_win", Rect(20, 20, 360, 260), "Main"))
        self.window.active = True
        self.button1 = self.window.add(ButtonControl("btn1", Rect(50, 50, 100, 40), "Button 1"))
        self.button1.set_tab_index(0)
        self.button2 = self.window.add(ButtonControl("btn2", Rect(200, 50, 100, 40), "Button 2"))
        self.button2.set_tab_index(1)

    def tearDown(self) -> None:
        pygame.quit()

    def test_mouse_click_focuses_without_showing_hint(self) -> None:
        """Clicking a button focuses it but does not activate the keyboard hint."""
        self.assertFalse(self.app.focus_visualizer.has_active_hint())

        self.app.process_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"pos": (100, 70), "button": 1}))

        self.assertIs(self.app.focus.focused_node, self.button1)
        self.assertFalse(self.app.focus_visualizer.has_active_hint())

    def test_keyboard_tab_focuses_and_shows_hint(self) -> None:
        """Tab key focuses a button; hint is active."""
        self.assertFalse(self.app.focus_visualizer.has_active_hint())

        self.app.process_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_TAB}))

        self.assertIs(self.app.focus.focused_node, self.button1)
        self.assertTrue(self.app.focus_visualizer.has_active_hint())

    def test_tab_after_mouse_click_first_shows_hint_then_advances(self) -> None:
        """After mouse focus, first Tab reveals hint; second Tab advances focus."""
        self.app.process_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"pos": (100, 70), "button": 1}))
        self.assertIs(self.app.focus.focused_node, self.button1)
        self.assertFalse(self.app.focus_visualizer.has_active_hint())

        self.app.process_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_TAB}))
        self.assertIs(self.app.focus.focused_node, self.button1)
        self.assertTrue(self.app.focus_visualizer.has_active_hint())

        self.app.process_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_TAB}))
        self.assertIs(self.app.focus.focused_node, self.button2)
        self.assertTrue(self.app.focus_visualizer.has_active_hint())

    def test_tab_initiation_gate_expires_then_requires_hint_reinit(self) -> None:
        """If second Tab is late (after timeout), first-Tab hint gate is required again."""
        self.app.process_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"pos": (100, 70), "button": 1}))
        self.assertIs(self.app.focus.focused_node, self.button1)

        self.app.process_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_TAB}))
        self.assertIs(self.app.focus.focused_node, self.button1)
        self.assertTrue(self.app.focus_visualizer.has_active_hint())

    def test_shift_tab_after_mouse_focus_applies_same_two_step_gate(self) -> None:
        """After mouse focus, first Shift+Tab only shows hint; second Shift+Tab cycles."""
        self.app.process_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"pos": (100, 70), "button": 1}))
        self.assertIs(self.app.focus.focused_node, self.button1)
        self.assertFalse(self.app.focus_visualizer.has_active_hint())

        self.app.process_event(
            pygame.event.Event(
                pygame.KEYDOWN,
                {"key": pygame.K_TAB, "mod": pygame.KMOD_SHIFT},
            )
        )
        self.assertIs(self.app.focus.focused_node, self.button1)
        self.assertTrue(self.app.focus_visualizer.has_active_hint())

        self.app.process_event(
            pygame.event.Event(
                pygame.KEYDOWN,
                {"key": pygame.K_TAB, "mod": pygame.KMOD_SHIFT},
            )
        )
        self.assertIs(self.app.focus.focused_node, self.button2)
        self.assertTrue(self.app.focus_visualizer.has_active_hint())

    def test_direction_change_from_tab_to_shift_tab_cycles_when_hint_active(self) -> None:
        """Switching from Tab to Shift+Tab cycles when the hint is still active."""
        self.app.process_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_TAB}))
        self.app.process_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_TAB}))
        self.assertIs(self.app.focus.focused_node, self.button2)

        self.app.process_event(
            pygame.event.Event(
                pygame.KEYDOWN,
                {"key": pygame.K_TAB, "mod": pygame.KMOD_SHIFT},
            )
        )
        self.assertIs(self.app.focus.focused_node, self.button1)
        self.assertTrue(self.app.focus_visualizer.has_active_hint())

        self.app.update(FOCUS_TRAVERSAL_HINT_TIMEOUT_SECONDS + 0.01)
        self.assertFalse(self.app.focus_visualizer.has_active_hint())

        self.app.process_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_TAB}))
        self.assertIs(self.app.focus.focused_node, self.button1)
        self.assertTrue(self.app.focus_visualizer.has_active_hint())

    def test_shift_keydown_before_tab_does_not_bypass_traversal_gate(self) -> None:
        """SHIFT KEYDOWN preceding Shift+Tab must not bypass the traversal-initiation gate.

        In real pygame usage Shift+Tab generates two events: a bare SHIFT KEYDOWN then
        TAB+KMOD_SHIFT KEYDOWN.  The SHIFT KEYDOWN must not pre-arm ``_hint_visible``
        so that the TAB+KMOD_SHIFT still applies the gate (show hint first, cycle on the
        second Shift+Tab within the timeout).
        """
        self.app.process_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"pos": (100, 70), "button": 1}))
        self.assertIs(self.app.focus.focused_node, self.button1)
        self.assertFalse(self.app.focus_visualizer.has_active_hint())

        # Real Shift+Tab: SHIFT key arrives first, then TAB+KMOD_SHIFT.
        self.app.process_event(
            pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_LSHIFT, "mod": pygame.KMOD_LSHIFT})
        )
        # SHIFT alone must not pre-arm the hint.
        self.assertFalse(self.app.focus_visualizer.has_active_hint())

        # First actual Shift+Tab: gate applies — show hint, do not cycle.
        self.app.process_event(
            pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_TAB, "mod": pygame.KMOD_SHIFT})
        )
        self.assertIs(self.app.focus.focused_node, self.button1)
        self.assertTrue(self.app.focus_visualizer.has_active_hint())

        # Simulate key-up events between the two Shift+Tab presses.
        self.app.process_event(
            pygame.event.Event(pygame.KEYUP, {"key": pygame.K_TAB, "mod": pygame.KMOD_SHIFT})
        )
        self.app.process_event(
            pygame.event.Event(pygame.KEYUP, {"key": pygame.K_LSHIFT, "mod": 0})
        )

        # Second Shift+Tab (SHIFT↓ then TAB+SHIFT↓): hint is active so cycling must occur.
        self.app.process_event(
            pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_LSHIFT, "mod": pygame.KMOD_LSHIFT})
        )
        self.app.process_event(
            pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_TAB, "mod": pygame.KMOD_SHIFT})
        )
        self.assertIs(self.app.focus.focused_node, self.button2)
        self.assertTrue(self.app.focus_visualizer.has_active_hint())

    def test_space_activation_resets_hint_timer_so_subsequent_space_shows_hint(self) -> None:
        """Space activation on a focused button must restart the hint timer.

        The hint should still be active immediately after activation, and a
        second Space before the timeout fires should again be visible (i.e. the
        elapsed counter was reset, not left advancing from before the first press).
        """
        self.app.process_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_TAB}))
        self.assertIs(self.app.focus.focused_node, self.button1)
        self.assertTrue(self.app.focus_visualizer.has_active_hint())

        # Advance time so hint would expire without a reset.
        self.app.update(FOCUS_TRAVERSAL_HINT_TIMEOUT_SECONDS * 0.9)
        self.assertTrue(self.app.focus_visualizer.has_active_hint())

        # Space activates the button; should reset the timer.
        self.app.process_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_SPACE}))
        self.assertTrue(self.app.focus_visualizer.has_active_hint())

        # Advance past what would have been the original expiry — hint is still live.
        self.app.update(FOCUS_TRAVERSAL_HINT_TIMEOUT_SECONDS * 0.2)
        self.assertTrue(self.app.focus_visualizer.has_active_hint())

    def test_space_activation_resets_cycle_mode_so_next_tab_shows_hint_first(self) -> None:
        """After Tab-cycling then Space-activating, the next Tab must re-apply the
        initiation gate: it shows the hint on the current node rather than cycling."""
        # Tab once to show hint, Tab again to cycle to button2.
        self.app.process_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_TAB}))
        self.app.process_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_TAB}))
        self.assertIs(self.app.focus.focused_node, self.button2)
        self.assertTrue(self.app.focus_visualizer.has_active_hint())

        # Space activates button2 — continuous-cycle mode must be reset.
        self.app.process_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_SPACE}))
        self.assertIs(self.app.focus.focused_node, self.button2)
        self.assertTrue(self.app.focus_visualizer.has_active_hint())

        # Allow hint to expire.
        self.app.update(FOCUS_TRAVERSAL_HINT_TIMEOUT_SECONDS + 0.01)
        self.assertFalse(self.app.focus_visualizer.has_active_hint())

        # Next Tab must show hint on button2 (initiation gate), not advance to button1.
        self.app.process_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_TAB}))
        self.assertIs(self.app.focus.focused_node, self.button2)
        self.assertTrue(self.app.focus_visualizer.has_active_hint())

    def test_titlebar_click_does_not_focus_screen_control_under_window(self) -> None:
        """Mouse focus selection must not fall through top window titlebar to screen controls."""
        app = GuiApplication(Surface((400, 300)))
        root = app.add(PanelControl("root", Rect(0, 0, 400, 300)))
        under = root.add(ButtonControl("under", Rect(30, 30, 100, 20), "Under"))
        under.set_tab_index(0)
        win = root.add(WindowControl("overlay", Rect(20, 20, 260, 180), "Styles"))

        screen_events = []
        app.set_screen_lifecycle(event_handler=lambda _event: (screen_events.append("screen") or False))

        app.process_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"pos": win.title_bar_rect().center, "button": 1}))

        self.assertTrue(win.active)
        self.assertIsNone(app.focus.focused_node)
        self.assertEqual(screen_events, [])

    def test_clicking_label_does_not_clear_existing_focus(self) -> None:
        """Mouse clicking labels must not change active focus."""
        label = self.window.add(LabelControl("lbl", Rect(40, 130, 180, 40), "Info"))
        label.set_tab_index(2)

        self.app.focus.set_focus(self.button1)
        self.assertIs(self.app.focus.focused_node, self.button1)

        self.app.process_event(
            pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"pos": label.rect.center, "button": 1})
        )

        self.assertIs(self.app.focus.focused_node, self.button1)

    def test_clicking_label_with_no_focus_keeps_focus_none(self) -> None:
        """Clicking labels with no existing focus should not establish focus."""
        label = self.window.add(LabelControl("lbl", Rect(40, 130, 180, 40), "Info"))
        label.set_tab_index(2)

        self.assertIsNone(self.app.focus.focused_node)

        self.app.process_event(
            pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"pos": label.rect.center, "button": 1})
        )

        self.assertIsNone(self.app.focus.focused_node)

    def test_keyboard_focus_cycle_clears_hover_when_pointer_moved_off_without_motion_event(self) -> None:
        """Tab cycling must clear stale hover state using live pointer position."""
        self.app.process_event(
            pygame.event.Event(pygame.MOUSEMOTION, {"pos": self.button1.rect.center, "rel": (0, 0), "buttons": (0, 0, 0)})
        )
        self.assertTrue(self.button1.hovered)

        self.app.process_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_TAB}))
        self.assertIs(self.app.focus.focused_node, self.button1)

        off_pos = (self.window.rect.right + 20, self.window.rect.bottom + 20)
        with patch("pygame.mouse.get_pos", return_value=off_pos):
            self.app.process_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_TAB}))

        self.assertFalse(self.button1.hovered)
        self.assertIs(self.app.focus.focused_node, self.button2)

    def test_screen_hint_drawn_before_window_so_window_implicitly_occludes(self) -> None:
        """Screen focus hint should be emitted before windows, so windows can overdraw it."""
        app = GuiApplication(Surface((400, 300)))
        root = app.add(PanelControl("root", Rect(0, 0, 400, 300), draw_background=False))
        screen_btn = root.add(ButtonControl("screen_btn", Rect(40, 40, 120, 30), "Screen"))
        screen_btn.set_tab_index(0)
        win = root.add(WindowControl("styles", Rect(20, 20, 260, 180), "Styles"))

        # Seed screen-scope keyboard hint directly.
        app.focus.set_focus(screen_btn, via_keyboard=True)
        self.assertIs(app.focus.focused_node, screen_btn)
        self.assertTrue(app.focus_visualizer.has_active_hint())

        call_order = []
        def _record_button_draw(_button_self, _surface, _theme):
            call_order.append("screen")

        def _record_window_draw(_window_self, _surface, _theme):
            call_order.append("window")

        with patch.object(ButtonControl, "draw", new=_record_button_draw):
            with patch.object(WindowControl, "draw", new=_record_window_draw):
                original_screen_hint = app.focus_visualizer.draw_hint_for_scene_root

                def _record_screen_hint(*args, **kwargs):
                    call_order.append("hint")
                    return original_screen_hint(*args, **kwargs)

                with patch.object(app.focus_visualizer, "draw_hint_for_scene_root", side_effect=_record_screen_hint) as mock_screen_hint:
                    app.scene.draw(app.surface, app.theme, app=app)
                    self.assertGreaterEqual(mock_screen_hint.call_count, 1)

        self.assertIn("hint", call_order)
        self.assertIn("window", call_order)
        self.assertLess(call_order.index("hint"), call_order.index("window"))

    def test_window_focus_hint_draws_in_window_phase(self) -> None:
        """Window-scoped focus hint remains visible by drawing after its window draw."""
        app = GuiApplication(Surface((400, 300)))
        root = app.add(PanelControl("root", Rect(0, 0, 400, 300), draw_background=False))
        win = root.add(WindowControl("styles", Rect(20, 20, 260, 180), "Styles"))
        win.active = True
        win_btn = win.add(ButtonControl("win_btn", Rect(50, 60, 100, 30), "InWin"))
        win_btn.set_tab_index(0)

        # First Tab focuses first candidate in window scope and shows hint.
        app.process_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_TAB}))
        self.assertIs(app.focus.focused_node, win_btn)
        self.assertTrue(app.focus_visualizer.has_active_hint())

        with patch.object(WindowControl, "draw", return_value=None):
            with patch.object(app.focus_visualizer, "draw_hint_for_window", wraps=app.focus_visualizer.draw_hint_for_window) as mock_window_hint:
                app.scene.draw(app.surface, app.theme, app=app)
                self.assertGreaterEqual(mock_window_hint.call_count, 1)


# ---------------------------------------------------------------------------
# WindowFocusManager — Ctrl+Tab window cycling
# ---------------------------------------------------------------------------

class WindowFocusManagerTests(unittest.TestCase):
    """WindowFocusManager: cycle list, hint timing, visibility revalidation."""

    def _scene_with_windows(self, *titles):
        from gui_do.focus.window_focus_manager import WindowFocusManager
        scene = Scene()
        root = PanelControl("root", Rect(0, 0, 800, 600), draw_background=False)
        scene.add(root)
        windows = []
        for i, title in enumerate(titles):
            w = WindowControl(f"win_{i}", Rect(i * 10, 0, 200, 150), title)
            w.visible = True
            w.enabled = True
            root.add(w)
            windows.append(w)
        return scene, WindowFocusManager(), windows

    # --- candidate list ----------------------------------------------------

    def test_no_windows_cycle_returns_false(self) -> None:
        from gui_do.focus.window_focus_manager import WindowFocusManager
        scene = Scene()
        wfm = WindowFocusManager()
        self.assertFalse(wfm.cycle(scene, forward=True))
        self.assertIsNone(wfm.focused_window)
        self.assertFalse(wfm.should_draw_window_focus_hint())

    def test_single_window_cycle_shows_hint(self) -> None:
        scene, wfm, (win,) = self._scene_with_windows("Solo")
        result = wfm.cycle(scene, forward=True)
        self.assertTrue(result)
        self.assertIs(wfm.focused_window, win)
        self.assertTrue(wfm.should_draw_window_focus_hint())

    def test_single_window_second_cycle_stays_on_same_window(self) -> None:
        scene, wfm, (win,) = self._scene_with_windows("Solo")
        wfm.cycle(scene, forward=True)
        wfm.cycle(scene, forward=True)
        self.assertIs(wfm.focused_window, win)

    def test_two_windows_cycle_forward(self) -> None:
        scene, wfm, (wa, wb) = self._scene_with_windows("A", "B")
        wfm.cycle(scene, forward=True)
        # First cycle: focus first candidate (sorted by control_id)
        first = wfm.focused_window
        wfm.cycle(scene, forward=True)
        second = wfm.focused_window
        self.assertIsNot(first, second)
        wfm.cycle(scene, forward=True)
        self.assertIs(wfm.focused_window, first)  # wrapped

    def test_two_windows_cycle_backward(self) -> None:
        scene, wfm, (wa, wb) = self._scene_with_windows("A", "B")
        wfm.cycle(scene, forward=True)
        first = wfm.focused_window
        wfm.cycle(scene, forward=False)
        # backward wraps to last
        self.assertIsNot(wfm.focused_window, first)

    # --- hint timer --------------------------------------------------------

    def test_hint_visible_immediately_after_cycle(self) -> None:
        scene, wfm, _ = self._scene_with_windows("A")
        wfm.cycle(scene, forward=True)
        self.assertTrue(wfm.should_draw_window_focus_hint())

    def test_hint_expires_after_timeout(self) -> None:
        from gui_do.focus.focus_hint_constants import FOCUS_TRAVERSAL_HINT_TIMEOUT_SECONDS
        scene, wfm, _ = self._scene_with_windows("A")
        wfm.cycle(scene, forward=True)
        wfm.update(FOCUS_TRAVERSAL_HINT_TIMEOUT_SECONDS + 0.01)
        self.assertFalse(wfm.should_draw_window_focus_hint())

    def test_hint_not_expired_before_timeout(self) -> None:
        from gui_do.focus.focus_hint_constants import FOCUS_TRAVERSAL_HINT_TIMEOUT_SECONDS
        scene, wfm, _ = self._scene_with_windows("A")
        wfm.cycle(scene, forward=True)
        wfm.update(FOCUS_TRAVERSAL_HINT_TIMEOUT_SECONDS - 0.1)
        self.assertTrue(wfm.should_draw_window_focus_hint())

    # --- first-cycle hint reveal (no cycle) --------------------------------

    def test_first_ctrl_tab_with_existing_focus_shows_hint_without_cycling(self) -> None:
        scene, wfm, (wa, wb) = self._scene_with_windows("A", "B")
        # Manually place focus on first window, hint off
        wfm.cycle(scene, forward=True)
        wfm.update(10.0)  # expire hint
        self.assertFalse(wfm.should_draw_window_focus_hint())
        focused_before = wfm.focused_window
        # Next Ctrl+Tab should just re-show hint, not move focus
        wfm.cycle(scene, forward=True)
        self.assertTrue(wfm.should_draw_window_focus_hint())
        self.assertIs(wfm.focused_window, focused_before)

    # --- revalidation on visibility change ---------------------------------

    def test_revalidate_clears_focus_when_no_windows_remain(self) -> None:
        scene, wfm, (win,) = self._scene_with_windows("A")
        wfm.cycle(scene, forward=True)
        win.visible = False
        wfm.revalidate(scene)
        self.assertIsNone(wfm.focused_window)
        self.assertFalse(wfm.should_draw_window_focus_hint())

    def test_revalidate_advances_focus_to_next_window(self) -> None:
        scene, wfm, (wa, wb) = self._scene_with_windows("A", "B")
        wfm.cycle(scene, forward=True)
        wfm.cycle(scene, forward=True)  # ensure hint visible; advance to second
        # Hide the currently focused window
        focused = wfm.focused_window
        focused.visible = False
        wfm.revalidate(scene)
        self.assertIsNotNone(wfm.focused_window)
        self.assertIsNot(wfm.focused_window, focused)

    def test_revalidate_noop_when_focus_still_valid(self) -> None:
        scene, wfm, (win,) = self._scene_with_windows("A")
        wfm.cycle(scene, forward=True)
        focused = wfm.focused_window
        wfm.revalidate(scene)
        self.assertIs(wfm.focused_window, focused)

    def test_invisible_windows_excluded_from_candidates(self) -> None:
        scene, wfm, (wa, wb) = self._scene_with_windows("A", "B")
        wa.visible = False
        wfm.cycle(scene, forward=True)
        self.assertIs(wfm.focused_window, wb)


# ---------------------------------------------------------------------------
# KeyboardManager Ctrl+Tab routing
# ---------------------------------------------------------------------------

class CtrlTabWindowCycleTests(unittest.TestCase):
    """Ctrl+Tab cycles window focus; Ctrl+Shift+Tab cycles backward."""

    def setUp(self) -> None:
        pygame.init()

    def tearDown(self) -> None:
        pygame.quit()

    def _app(self):
        app = GuiApplication(Surface((400, 300)))
        root = app.add(PanelControl("root", Rect(0, 0, 400, 300), draw_background=False))
        wa = root.add(WindowControl("win_a", Rect(0, 0, 200, 150), "A"))
        wb = root.add(WindowControl("win_b", Rect(10, 10, 200, 150), "B"))
        wa.visible = True; wb.visible = True
        wa.enabled = True; wb.enabled = True
        return app, root, wa, wb

    def test_ctrl_tab_cycles_window_focus(self) -> None:
        app, root, wa, wb = self._app()
        app.process_event(pygame.event.Event(
            pygame.KEYDOWN, {"key": pygame.K_TAB, "mod": pygame.KMOD_LCTRL, "unicode": ""}
        ))
        self.assertIsNotNone(app.window_focus.focused_window)
        self.assertTrue(app.window_focus.should_draw_window_focus_hint())
        self.assertIs(root.children[-1], wa)
        self.assertTrue(wa.active)

    def test_ctrl_tab_does_nothing_when_no_windows(self) -> None:
        from gui_do.focus.window_focus_manager import WindowFocusManager
        app = GuiApplication(Surface((400, 300)))
        app.process_event(pygame.event.Event(
            pygame.KEYDOWN, {"key": pygame.K_TAB, "mod": pygame.KMOD_LCTRL, "unicode": ""}
        ))
        self.assertIsNone(app.window_focus.focused_window)

    def test_ctrl_tab_blocked_while_command_palette_open(self) -> None:
        from unittest.mock import MagicMock
        app, root, wa, wb = self._app()
        # Fake the command palette overlay being open
        overlay_mock = MagicMock()
        overlay_mock.has_overlay.return_value = True
        overlay_mock.route_event.return_value = False
        overlay_mock.overlay_count.return_value = 1
        overlay_mock.draw.return_value = None
        app.overlay = overlay_mock

        app.process_event(pygame.event.Event(
            pygame.KEYDOWN, {"key": pygame.K_TAB, "mod": pygame.KMOD_LCTRL, "unicode": ""}
        ))
        self.assertIsNone(app.window_focus.focused_window)

    def test_ctrl_tab_is_not_regular_tab(self) -> None:
        """Regular Tab (no Ctrl) must NOT change window focus."""
        app, root, wa, wb = self._app()
        # Add a focusable control so Tab has something to do
        btn = wa.add(ButtonControl("b", Rect(10, 40, 80, 30), "X"))
        btn.set_tab_index(0)
        wa.active = True
        app.process_event(pygame.event.Event(
            pygame.KEYDOWN, {"key": pygame.K_TAB, "mod": 0, "unicode": ""}
        ))
        self.assertIsNone(app.window_focus.focused_window)

    def test_ctrl_tab_restores_remembered_focus_for_cycled_window(self) -> None:
        app, root, wa, wb = self._app()
        btn_a = wa.add(ButtonControl("a_btn", Rect(10, 40, 80, 30), "A"))
        btn_b = wb.add(ButtonControl("b_btn", Rect(10, 40, 80, 30), "B"))
        btn_a.set_tab_index(0)
        btn_b.set_tab_index(0)

        wa.active = True
        app.focus.set_focus(btn_a)
        wb.active = True
        app.focus.set_focus(btn_b)

        app.process_event(pygame.event.Event(
            pygame.KEYDOWN, {"key": pygame.K_TAB, "mod": pygame.KMOD_LCTRL, "unicode": ""}
        ))

        self.assertIs(app.window_focus.focused_window, wa)
        self.assertIs(app.focus.focused_node, btn_a)
        self.assertIs(root.children[-1], wa)

    def test_active_window_change_restores_remembered_focus_on_update(self) -> None:
        app, root, wa, wb = self._app()
        btn_a = wa.add(ButtonControl("a_btn", Rect(10, 40, 80, 30), "A"))
        btn_b = wb.add(ButtonControl("b_btn", Rect(10, 40, 80, 30), "B"))
        btn_a.set_tab_index(0)
        btn_b.set_tab_index(0)

        wa.active = True
        app.focus.set_focus(btn_a)
        wb.active = True
        app.focus.set_focus(btn_b)

        wa.active = True
        self.assertIs(app.focus.focused_node, btn_b)

        app.update(0.0)

        self.assertIs(app.focus.focused_node, btn_a)


if __name__ == "__main__":
    unittest.main()
