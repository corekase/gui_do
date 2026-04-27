import os
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame
from pygame import Rect

from gui_do import TabControl, TabItem, PanelControl, GuiApplication, LabelControl


class TabControlRuntimeTests(unittest.TestCase):

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

    def test_empty_tabs_selected_key_none(self) -> None:
        ctrl = TabControl("tc", Rect(10, 10, 400, 300))
        self.assertIsNone(ctrl.selected_key)

    def test_first_tab_selected_by_default(self) -> None:
        ctrl = TabControl("tc", Rect(10, 10, 400, 300), items=[
            TabItem("a", "Alpha"),
            TabItem("b", "Beta"),
        ])
        self.assertEqual(ctrl.selected_key, "a")

    def test_initial_selected_key_respected(self) -> None:
        ctrl = TabControl("tc", Rect(10, 10, 400, 300), items=[
            TabItem("a", "Alpha"),
            TabItem("b", "Beta"),
        ], selected_key="b")
        self.assertEqual(ctrl.selected_key, "b")

    def test_invalid_selected_key_falls_back_to_first(self) -> None:
        ctrl = TabControl("tc", Rect(10, 10, 400, 300), items=[
            TabItem("a", "Alpha"),
        ], selected_key="nonexistent")
        self.assertEqual(ctrl.selected_key, "a")

    # ------------------------------------------------------------------
    # select
    # ------------------------------------------------------------------

    def test_select_changes_key(self) -> None:
        ctrl = TabControl("tc", Rect(10, 10, 400, 300), items=[
            TabItem("a", "Alpha"),
            TabItem("b", "Beta"),
        ])
        result = ctrl.select("b")
        self.assertTrue(result)
        self.assertEqual(ctrl.selected_key, "b")

    def test_select_returns_false_for_unknown_key(self) -> None:
        ctrl = TabControl("tc", Rect(10, 10, 400, 300), items=[
            TabItem("a", "Alpha"),
        ])
        result = ctrl.select("zzz")
        self.assertFalse(result)

    def test_select_returns_false_for_disabled_tab(self) -> None:
        ctrl = TabControl("tc", Rect(10, 10, 400, 300), items=[
            TabItem("a", "Alpha"),
            TabItem("b", "Beta", enabled=False),
        ])
        result = ctrl.select("b")
        self.assertFalse(result)
        self.assertEqual(ctrl.selected_key, "a")

    def test_select_fires_on_change(self) -> None:
        changes = []
        ctrl = TabControl("tc", Rect(10, 10, 400, 300), items=[
            TabItem("a", "Alpha"),
            TabItem("b", "Beta"),
        ], on_change=lambda k: changes.append(k))
        ctrl.select("b")
        self.assertIn("b", changes)

    def test_select_same_key_no_callback(self) -> None:
        changes = []
        ctrl = TabControl("tc", Rect(10, 10, 400, 300), items=[
            TabItem("a", "Alpha"),
        ], on_change=lambda k: changes.append(k))
        ctrl.select("a")  # already selected
        self.assertEqual(changes, [])

    # ------------------------------------------------------------------
    # add_item
    # ------------------------------------------------------------------

    def test_add_item_appends(self) -> None:
        ctrl = TabControl("tc", Rect(10, 10, 400, 300))
        ctrl.add_item(TabItem("a", "Alpha"))
        self.assertEqual(ctrl.selected_key, "a")

    def test_add_item_does_not_change_selection_if_already_set(self) -> None:
        ctrl = TabControl("tc", Rect(10, 10, 400, 300), items=[TabItem("a", "Alpha")])
        ctrl.add_item(TabItem("b", "Beta"))
        self.assertEqual(ctrl.selected_key, "a")

    # ------------------------------------------------------------------
    # remove_item
    # ------------------------------------------------------------------

    def test_remove_item_returns_true(self) -> None:
        ctrl = TabControl("tc", Rect(10, 10, 400, 300), items=[
            TabItem("a", "Alpha"),
            TabItem("b", "Beta"),
        ])
        result = ctrl.remove_item("a")
        self.assertTrue(result)

    def test_remove_item_returns_false_for_unknown(self) -> None:
        ctrl = TabControl("tc", Rect(10, 10, 400, 300))
        result = ctrl.remove_item("zzz")
        self.assertFalse(result)

    def test_remove_selected_advances_selection(self) -> None:
        ctrl = TabControl("tc", Rect(10, 10, 400, 300), items=[
            TabItem("a", "Alpha"),
            TabItem("b", "Beta"),
        ])
        ctrl.remove_item("a")
        self.assertEqual(ctrl.selected_key, "b")

    def test_remove_only_item_clears_selection(self) -> None:
        ctrl = TabControl("tc", Rect(10, 10, 400, 300), items=[TabItem("a", "Alpha")])
        ctrl.remove_item("a")
        self.assertIsNone(ctrl.selected_key)

    # ------------------------------------------------------------------
    # items()
    # ------------------------------------------------------------------

    def test_items_returns_copy(self) -> None:
        ctrl = TabControl("tc", Rect(10, 10, 400, 300), items=[TabItem("a", "Alpha")])
        items = ctrl.items()
        items.clear()
        self.assertEqual(len(ctrl.items()), 1)

    # ------------------------------------------------------------------
    # Mouse click selection
    # ------------------------------------------------------------------

    def test_mouse_click_on_tab_selects(self) -> None:
        changes = []
        content_a = PanelControl("content_a", Rect(0, 0, 400, 268))
        content_b = PanelControl("content_b", Rect(0, 0, 400, 268))
        ctrl = self.root.add(TabControl("tc", Rect(10, 10, 400, 300), items=[
            TabItem("a", "Alpha", content_a),
            TabItem("b", "Beta", content_b),
        ], on_change=lambda k: changes.append(k)))
        # Build tab rects so click can be hit-tested
        self.app.draw()
        if ctrl._tab_rects and len(ctrl._tab_rects) > 1:
            second_tab = ctrl._tab_rects[1]
            cx = second_tab.centerx
            cy = second_tab.centery
            self.app.process_event(
                pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"button": 1, "pos": (cx, cy)})
            )
            self.assertEqual(ctrl.selected_key, "b")

    # ------------------------------------------------------------------
    # Keyboard navigation
    # ------------------------------------------------------------------

    def test_left_right_arrow_key_navigation(self) -> None:
        ctrl = self.root.add(TabControl("tc", Rect(10, 10, 400, 300), items=[
            TabItem("a", "Alpha"),
            TabItem("b", "Beta"),
            TabItem("c", "Gamma"),
        ]))
        self.app.focus.set_focus(ctrl)
        self.assertEqual(ctrl.selected_key, "a")
        self.app.process_event(
            pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_RIGHT, "mod": 0, "unicode": ""})
        )
        self.assertEqual(ctrl.selected_key, "b")
        self.app.process_event(
            pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_LEFT, "mod": 0, "unicode": ""})
        )
        self.assertEqual(ctrl.selected_key, "a")

    def test_left_arrow_at_first_tab_stays(self) -> None:
        ctrl = self.root.add(TabControl("tc", Rect(10, 10, 400, 300), items=[
            TabItem("a", "Alpha"),
            TabItem("b", "Beta"),
        ]))
        self.app.focus.set_focus(ctrl)
        self.app.process_event(
            pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_LEFT, "mod": 0, "unicode": ""})
        )
        self.assertEqual(ctrl.selected_key, "a")

    def test_right_arrow_at_last_tab_stays(self) -> None:
        ctrl = self.root.add(TabControl("tc", Rect(10, 10, 400, 300), items=[
            TabItem("a", "Alpha"),
            TabItem("b", "Beta"),
        ]))
        ctrl.select("b")
        self.app.focus.set_focus(ctrl)
        self.app.process_event(
            pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_RIGHT, "mod": 0, "unicode": ""})
        )
        self.assertEqual(ctrl.selected_key, "b")

    # ------------------------------------------------------------------
    # Focus / TabItem
    # ------------------------------------------------------------------

    def test_accepts_focus(self) -> None:
        ctrl = TabControl("tc", Rect(10, 10, 400, 300))
        self.assertTrue(ctrl.accepts_focus())

    def test_accepts_mouse_focus(self) -> None:
        ctrl = TabControl("tc", Rect(10, 10, 400, 300))
        self.assertTrue(ctrl.accepts_mouse_focus())

    def test_tab_item_defaults(self) -> None:
        item = TabItem("k", "Label")
        self.assertEqual(item.key, "k")
        self.assertEqual(item.label, "Label")
        self.assertIsNone(item.content)
        self.assertTrue(item.enabled)

    # ------------------------------------------------------------------
    # Drawing
    # ------------------------------------------------------------------

    def test_draw_does_not_raise(self) -> None:
        ctrl = self.root.add(TabControl("tc", Rect(10, 10, 400, 300), items=[
            TabItem("a", "Alpha"),
            TabItem("b", "Beta"),
        ]))
        self.app.draw()

    def test_draw_with_content_nodes(self) -> None:
        label = LabelControl("lbl", Rect(0, 0, 400, 268), "Tab A content")
        ctrl = self.root.add(TabControl("tc", Rect(10, 10, 400, 300), items=[
            TabItem("a", "Alpha", label),
        ]))
        self.app.draw()

    def test_draw_empty_tabs_does_not_raise(self) -> None:
        ctrl = self.root.add(TabControl("tc", Rect(10, 10, 400, 300)))
        self.app.draw()

    def test_update_forwarded_to_active_content(self) -> None:
        update_calls = []

        class UpdatablePanel(PanelControl):
            def update(self, dt: float) -> None:
                update_calls.append(dt)

        content = UpdatablePanel("up", Rect(0, 0, 400, 268))
        ctrl = self.root.add(TabControl("tc", Rect(10, 10, 400, 300), items=[
            TabItem("a", "Alpha", content),
        ]))
        ctrl.update(0.016)
        self.assertEqual(len(update_calls), 1)


if __name__ == "__main__":
    unittest.main()
