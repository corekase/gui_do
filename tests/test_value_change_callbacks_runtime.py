import os
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame
from pygame import Rect

from gui_do import GuiApplication, LayoutAxis, PanelControl, ScrollbarControl, SliderControl, ValueChangeReason


class ValueChangeCallbacksRuntimeTests(unittest.TestCase):
    def setUp(self) -> None:
        pygame.init()
        self.surface = pygame.display.set_mode((300, 200))
        self.app = GuiApplication(self.surface)
        self.root = self.app.add(PanelControl("root", Rect(0, 0, 300, 200)))

    def tearDown(self) -> None:
        pygame.quit()

    def test_slider_keyboard_triggers_on_change_only_when_value_changes(self) -> None:
        changed = []
        slider = self.root.add(
            SliderControl(
                "s",
                Rect(20, 20, 180, 24),
                LayoutAxis.HORIZONTAL,
                0.0,
                100.0,
                0.0,
                on_change=lambda value, _reason: changed.append(value),
            )
        )
        slider.set_tab_index(0)
        self.app.focus.set_focus(slider)

        consumed_home = self.app.process_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_HOME}))
        consumed_right = self.app.process_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_RIGHT}))

        self.assertFalse(consumed_home)
        self.assertTrue(consumed_right)
        self.assertEqual(changed, [5.0])

    def test_slider_end_triggers_on_change_once_until_value_changes_again(self) -> None:
        changed = []
        slider = self.root.add(
            SliderControl(
                "s",
                Rect(20, 20, 180, 24),
                LayoutAxis.HORIZONTAL,
                0.0,
                100.0,
                50.0,
                on_change=lambda value, _reason: changed.append(value),
            )
        )
        slider.set_tab_index(0)
        self.app.focus.set_focus(slider)

        consumed_end = self.app.process_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_END}))
        consumed_end_again = self.app.process_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_END}))

        self.assertTrue(consumed_end)
        self.assertFalse(consumed_end_again)
        self.assertEqual(changed, [100.0])

    def test_scrollbar_keyboard_triggers_on_change_only_when_offset_changes(self) -> None:
        changed = []
        bar = self.root.add(
            ScrollbarControl(
                "sb",
                Rect(20, 60, 180, 24),
                LayoutAxis.HORIZONTAL,
                content_size=1000,
                viewport_size=200,
                offset=0,
                step=10,
                on_change=lambda value, _reason: changed.append(value),
            )
        )
        bar.set_tab_index(0)
        self.app.focus.set_focus(bar)

        consumed_home = self.app.process_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_HOME}))
        consumed_right = self.app.process_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_RIGHT}))

        self.assertFalse(consumed_home)
        self.assertTrue(consumed_right)
        self.assertEqual(changed, [10])

    def test_scrollbar_page_down_triggers_on_change_once_at_lower_bound(self) -> None:
        changed = []
        bar = self.root.add(
            ScrollbarControl(
                "sb",
                Rect(20, 60, 180, 24),
                LayoutAxis.HORIZONTAL,
                content_size=1000,
                viewport_size=200,
                offset=0,
                step=10,
                on_change=lambda value, _reason: changed.append(value),
            )
        )
        bar.set_tab_index(0)
        self.app.focus.set_focus(bar)

        consumed_page_down = self.app.process_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_PAGEDOWN}))
        consumed_home = self.app.process_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_HOME}))
        consumed_home_again = self.app.process_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_HOME}))

        self.assertTrue(consumed_page_down)
        self.assertTrue(consumed_home)
        self.assertFalse(consumed_home_again)
        self.assertEqual(changed, [180, 0])

    def test_slider_programmatic_set_and_adjust_emit_callbacks_only_on_change(self) -> None:
        changed = []
        slider = self.root.add(
            SliderControl(
                "s",
                Rect(20, 20, 180, 24),
                LayoutAxis.HORIZONTAL,
                0.0,
                100.0,
                50.0,
                on_change=lambda value, _reason: changed.append(value),
            )
        )

        changed_set = slider.set_value(75.0)
        unchanged_set = slider.set_value(75.0)
        changed_adjust = slider.adjust_value(100.0)
        unchanged_adjust = slider.adjust_value(0.0)

        self.assertTrue(changed_set)
        self.assertFalse(unchanged_set)
        self.assertTrue(changed_adjust)
        self.assertFalse(unchanged_adjust)
        self.assertEqual(slider.value, 100.0)
        self.assertEqual(changed, [75.0, 100.0])

    def test_scrollbar_programmatic_set_and_adjust_emit_callbacks_only_on_change(self) -> None:
        changed = []
        bar = self.root.add(
            ScrollbarControl(
                "sb",
                Rect(20, 60, 180, 24),
                LayoutAxis.HORIZONTAL,
                content_size=1000,
                viewport_size=200,
                offset=100,
                step=10,
                on_change=lambda value, _reason: changed.append(value),
            )
        )

        changed_set = bar.set_offset(250)
        unchanged_set = bar.set_offset(250)
        changed_adjust = bar.adjust_offset(1000)
        unchanged_adjust = bar.adjust_offset(0)

        self.assertTrue(changed_set)
        self.assertFalse(unchanged_set)
        self.assertTrue(changed_adjust)
        self.assertFalse(unchanged_adjust)
        self.assertEqual(bar.offset, 800)
        self.assertEqual(changed, [250, 800])

    def test_slider_on_change_receives_reason_metadata_when_callback_accepts_it(self) -> None:
        changed = []
        slider = self.root.add(
            SliderControl(
                "s",
                Rect(20, 20, 180, 24),
                LayoutAxis.HORIZONTAL,
                0.0,
                100.0,
                50.0,
                on_change=lambda value, reason: changed.append((value, reason)),
            )
        )
        slider.set_tab_index(0)
        self.app.focus.set_focus(slider)

        self.app.process_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_RIGHT}))
        slider.adjust_value(5.0)

        self.assertEqual(changed, [(55.0, ValueChangeReason.KEYBOARD), (60.0, ValueChangeReason.PROGRAMMATIC)])

    def test_scrollbar_on_change_receives_reason_metadata_when_callback_accepts_it(self) -> None:
        changed = []
        bar = self.root.add(
            ScrollbarControl(
                "sb",
                Rect(20, 60, 180, 24),
                LayoutAxis.HORIZONTAL,
                content_size=1000,
                viewport_size=200,
                offset=100,
                step=10,
                on_change=lambda value, reason: changed.append((value, reason)),
            )
        )
        bar.set_tab_index(0)
        self.app.focus.set_focus(bar)

        self.app.process_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_RIGHT}))
        bar.adjust_offset(10)

        self.assertEqual(changed, [(110, ValueChangeReason.KEYBOARD), (120, ValueChangeReason.PROGRAMMATIC)])

    def test_set_on_change_callback_updates_callback(self) -> None:
        slider = self.root.add(SliderControl("s", Rect(20, 20, 180, 24), LayoutAxis.HORIZONTAL, 0.0, 100.0, 50.0))
        bar = self.root.add(
            ScrollbarControl("sb", Rect(20, 60, 180, 24), LayoutAxis.HORIZONTAL, content_size=1000, viewport_size=200, offset=100, step=10)
        )

        slider_callback = slider.set_on_change_callback(lambda value, reason: None)
        bar_callback = bar.set_on_change_callback(lambda value, reason: None)

        self.assertIsNotNone(slider_callback)
        self.assertIsNotNone(bar_callback)


if __name__ == "__main__":
    unittest.main()
