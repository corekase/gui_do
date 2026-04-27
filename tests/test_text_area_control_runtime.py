import os
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame
from pygame import Rect

from gui_do import TextAreaControl, GuiApplication, PanelControl


class TextAreaControlRuntimeTests(unittest.TestCase):

    def setUp(self) -> None:
        pygame.init()
        self.surface = pygame.display.set_mode((640, 480))
        self.app = GuiApplication(self.surface)
        self.root = self.app.add(PanelControl("root", Rect(0, 0, 640, 480)))

    def tearDown(self) -> None:
        pygame.quit()

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------

    def test_default_value_empty(self) -> None:
        ctrl = TextAreaControl("ta", Rect(10, 10, 300, 200))
        self.assertEqual(ctrl.value, "")

    def test_initial_value_set(self) -> None:
        ctrl = TextAreaControl("ta", Rect(10, 10, 300, 200), value="hello")
        self.assertEqual(ctrl.value, "hello")

    def test_cursor_at_end_on_init(self) -> None:
        ctrl = TextAreaControl("ta", Rect(10, 10, 300, 200), value="hello")
        self.assertEqual(ctrl.cursor_pos, 5)

    def test_no_selection_on_init(self) -> None:
        ctrl = TextAreaControl("ta", Rect(10, 10, 300, 200))
        lo, hi = ctrl.selection_range
        self.assertEqual(lo, hi)

    # ------------------------------------------------------------------
    # set_value
    # ------------------------------------------------------------------

    def test_set_value_updates(self) -> None:
        ctrl = TextAreaControl("ta", Rect(10, 10, 300, 200))
        ctrl.set_value("new text")
        self.assertEqual(ctrl.value, "new text")

    def test_set_value_resets_cursor(self) -> None:
        ctrl = TextAreaControl("ta", Rect(10, 10, 300, 200), value="abc")
        ctrl.set_value("xy")
        self.assertEqual(ctrl.cursor_pos, 2)

    def test_max_length_respected(self) -> None:
        ctrl = TextAreaControl("ta", Rect(10, 10, 300, 200), max_length=5)
        ctrl.set_value("123456789")
        self.assertEqual(ctrl.value, "12345")

    # ------------------------------------------------------------------
    # select_all
    # ------------------------------------------------------------------

    def test_select_all(self) -> None:
        ctrl = TextAreaControl("ta", Rect(10, 10, 300, 200), value="hello")
        ctrl.select_all()
        lo, hi = ctrl.selection_range
        self.assertEqual(lo, 0)
        self.assertEqual(hi, 5)

    # ------------------------------------------------------------------
    # read_only
    # ------------------------------------------------------------------

    def test_read_only_property(self) -> None:
        ctrl = TextAreaControl("ta", Rect(10, 10, 300, 200), read_only=True)
        self.assertTrue(ctrl.read_only)

    def test_read_only_setter(self) -> None:
        ctrl = TextAreaControl("ta", Rect(10, 10, 300, 200))
        ctrl.read_only = True
        self.assertTrue(ctrl.read_only)

    def test_read_only_blocks_text_input(self) -> None:
        ctrl = self.root.add(TextAreaControl("ta", Rect(10, 10, 300, 200), read_only=True))
        self.app.focus.set_focus(ctrl)
        self.app.process_event(
            pygame.event.Event(pygame.TEXTINPUT, {"text": "hello"})
        )
        self.assertEqual(ctrl.value, "")

    # ------------------------------------------------------------------
    # Keyboard input
    # ------------------------------------------------------------------

    def test_text_input_inserts_text(self) -> None:
        ctrl = self.root.add(TextAreaControl("ta", Rect(10, 10, 300, 200)))
        self.app.focus.set_focus(ctrl)
        self.app.process_event(
            pygame.event.Event(pygame.TEXTINPUT, {"text": "hello"})
        )
        self.assertEqual(ctrl.value, "hello")

    def test_enter_inserts_newline(self) -> None:
        ctrl = self.root.add(TextAreaControl("ta", Rect(10, 10, 300, 200), value="a"))
        ctrl._cursor_pos = 1
        self.app.focus.set_focus(ctrl)
        self.app.process_event(
            pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_RETURN, "mod": 0, "unicode": ""})
        )
        self.assertIn("\n", ctrl.value)

    def test_backspace_removes_character(self) -> None:
        ctrl = self.root.add(TextAreaControl("ta", Rect(10, 10, 300, 200), value="abc"))
        self.app.focus.set_focus(ctrl)
        self.app.process_event(
            pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_BACKSPACE, "mod": 0, "unicode": ""})
        )
        self.assertEqual(ctrl.value, "ab")

    def test_delete_removes_forward(self) -> None:
        ctrl = self.root.add(TextAreaControl("ta", Rect(10, 10, 300, 200), value="abc"))
        ctrl._cursor_pos = 0
        self.app.focus.set_focus(ctrl)
        self.app.process_event(
            pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_DELETE, "mod": 0, "unicode": ""})
        )
        self.assertEqual(ctrl.value, "bc")

    # ------------------------------------------------------------------
    # Clipboard
    # ------------------------------------------------------------------

    def test_ctrl_a_selects_all(self) -> None:
        ctrl = self.root.add(TextAreaControl("ta", Rect(10, 10, 300, 200), value="hello"))
        self.app.focus.set_focus(ctrl)
        self.app.process_event(
            pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_a, "mod": pygame.KMOD_CTRL, "unicode": ""})
        )
        lo, hi = ctrl.selection_range
        self.assertEqual(lo, 0)
        self.assertEqual(hi, 5)

    # ------------------------------------------------------------------
    # on_change callback
    # ------------------------------------------------------------------

    def test_on_change_fires_on_input(self) -> None:
        changes = []
        ctrl = self.root.add(
            TextAreaControl("ta", Rect(10, 10, 300, 200), on_change=lambda v: changes.append(v))
        )
        self.app.focus.set_focus(ctrl)
        self.app.process_event(
            pygame.event.Event(pygame.TEXTINPUT, {"text": "x"})
        )
        self.assertTrue(len(changes) > 0)
        self.assertEqual(changes[-1], "x")

    # ------------------------------------------------------------------
    # focus
    # ------------------------------------------------------------------

    def test_accepts_focus(self) -> None:
        ctrl = TextAreaControl("ta", Rect(10, 10, 300, 200))
        self.assertTrue(ctrl.accepts_focus())

    def test_accepts_mouse_focus(self) -> None:
        ctrl = TextAreaControl("ta", Rect(10, 10, 300, 200))
        self.assertTrue(ctrl.accepts_mouse_focus())

    # ------------------------------------------------------------------
    # Drawing (smoke test)
    # ------------------------------------------------------------------

    def test_draw_does_not_raise(self) -> None:
        ctrl = self.root.add(TextAreaControl("ta", Rect(10, 10, 300, 200), value="line one\nline two"))
        self.app.draw()


if __name__ == "__main__":
    unittest.main()
