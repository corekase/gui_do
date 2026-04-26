import os
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame
from pygame import Rect

from gui_do import ArrowBoxControl, GuiApplication, PanelControl
from gui_do.core.focus_hint_constants import FOCUS_TRAVERSAL_HINT_TIMEOUT_SECONDS


class ArrowBoxRuntimeTests(unittest.TestCase):
    def setUp(self) -> None:
        pygame.init()
        self.surface = pygame.display.set_mode((240, 160))
        self.app = GuiApplication(self.surface)
        self.root = self.app.add(PanelControl("root", Rect(0, 0, 240, 160)))

    def tearDown(self) -> None:
        pygame.quit()

    def test_keyboard_activation_when_focused(self) -> None:
        fired = []
        control = self.root.add(ArrowBoxControl("arr", Rect(20, 20, 40, 30), 0, on_activate=lambda: fired.append(True), repeat_interval_seconds=0.05))
        control.set_tab_index(0)
        self.app.focus.set_focus(control)

        consumed_return = self.app.process_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_RETURN}))
        consumed_space = self.app.process_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_SPACE}))

        self.assertTrue(consumed_return)
        self.assertTrue(consumed_space)
        self.assertEqual(len(fired), 2)

    def test_keyboard_activation_sets_cosmetic_focus_armed_until_shared_timeout(self) -> None:
        fired = []
        control = self.root.add(ArrowBoxControl("arr", Rect(20, 20, 40, 30), 0, on_activate=lambda: fired.append(True)))
        control.set_tab_index(0)
        self.app.focus.set_focus(control)

        consumed = self.app.process_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_RETURN}))

        self.assertTrue(consumed)
        self.assertEqual(fired, [True])
        self.assertTrue(control._focus_activation_armed)
        self.assertFalse(control._pressed)

        self.app.update(FOCUS_TRAVERSAL_HINT_TIMEOUT_SECONDS - 0.01)
        self.assertTrue(control._focus_activation_armed)

        self.app.update(0.02)
        self.assertFalse(control._focus_activation_armed)

    def test_keyboard_activation_ignored_when_not_focused(self) -> None:
        fired = []
        control = self.root.add(ArrowBoxControl("arr", Rect(20, 20, 40, 30), 0, on_activate=lambda: fired.append(True), repeat_interval_seconds=0.05))
        control.set_tab_index(0)

        consumed_return = self.app.process_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_RETURN}))
        consumed_space = self.app.process_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_SPACE}))

        self.assertFalse(consumed_return)
        self.assertFalse(consumed_space)
        self.assertEqual(fired, [])

    def test_repeat_cancels_when_pointer_leaves_while_pressed(self) -> None:
        fired = []
        control = self.root.add(ArrowBoxControl("arr", Rect(20, 20, 40, 30), 0, on_activate=lambda: fired.append(True), repeat_interval_seconds=0.05))

        self.app.process_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"pos": (30, 30), "button": 1}))
        self.assertEqual(len(fired), 1)
        self.assertIn(control._timer_id, self.app.timers._timers)

        self.app.process_event(
            pygame.event.Event(
                pygame.MOUSEMOTION,
                {"pos": (200, 120), "rel": (5, 0), "buttons": (1, 0, 0)},
            )
        )
        self.assertNotIn(control._timer_id, self.app.timers._timers)

        self.app.update(0.2)
        self.assertEqual(len(fired), 1)

    def test_hover_resets_when_reenabled_after_pointer_moves_away_while_disabled(self) -> None:
        control = self.root.add(ArrowBoxControl("arr", Rect(20, 20, 40, 30), 0, on_activate=lambda: None, repeat_interval_seconds=0.05))

        self.app.process_event(pygame.event.Event(pygame.MOUSEMOTION, {"pos": (30, 30), "rel": (0, 0), "buttons": (0, 0, 0)}))
        self.assertTrue(control._hovered)

        control.enabled = False
        self.app.process_event(pygame.event.Event(pygame.MOUSEMOTION, {"pos": (200, 120), "rel": (0, 0), "buttons": (0, 0, 0)}))
        control.enabled = True

        self.assertFalse(control._hovered)
        self.assertFalse(control._pressed)

    def test_disabled_visual_includes_arrow_glyph(self) -> None:
        rect = Rect(0, 0, 40, 30)
        factory = self.app.theme.graphics_factory
        arrow_visuals = factory.draw_arrow_visuals(rect, 0)
        frame_visuals = factory.build_frame_visuals(rect)

        # Regression guard: disabled arrow visuals must not be frame-only.
        arrow_disabled = pygame.image.tobytes(arrow_visuals.disabled, "RGBA")
        frame_disabled = pygame.image.tobytes(frame_visuals.disabled, "RGBA")
        self.assertNotEqual(arrow_disabled, frame_disabled)


if __name__ == "__main__":
    unittest.main()
