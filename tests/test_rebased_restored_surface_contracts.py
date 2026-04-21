import time
import unittest
from types import SimpleNamespace

from pygame import Rect

from gui import (
    ArrowBoxControl,
    ButtonGroupControl,
    CanvasControl,
    FrameControl,
    LayoutManager,
    TaskPanelControl,
    TaskScheduler,
    TaskEvent,
    Timers,
    ToggleControl,
    WindowControl,
)


class RebasedRestoredSurfaceContractsTests(unittest.TestCase):
    def test_restored_symbols_are_importable(self) -> None:
        self.assertIsNotNone(FrameControl)
        self.assertIsNotNone(ToggleControl)
        self.assertIsNotNone(CanvasControl)
        self.assertIsNotNone(WindowControl)
        self.assertIsNotNone(TaskPanelControl)
        self.assertIsNotNone(ArrowBoxControl)
        self.assertIsNotNone(ButtonGroupControl)
        self.assertIsNotNone(LayoutManager)
        self.assertIsNotNone(Timers)
        self.assertIsNotNone(TaskScheduler)
        self.assertIsNotNone(TaskEvent)

    def test_layout_manager_grid_linear_anchor_and_place(self) -> None:
        manager = LayoutManager()
        manager.set_grid_properties(anchor=(10, 20), width=30, height=40, spacing=5, use_rect=True)
        self.assertEqual(manager.gridded(2, 1), Rect(80, 65, 30, 40))

        manager.set_linear_properties(anchor=(5, 6), item_width=10, item_height=11, spacing=2, horizontal=True, wrap_count=2, use_rect=True)
        self.assertEqual(manager.linear(0), Rect(5, 6, 10, 11))
        self.assertEqual(manager.linear(1), Rect(17, 6, 10, 11))
        self.assertEqual(manager.linear(2), Rect(5, 19, 10, 11))

        manager.set_anchor_bounds(Rect(0, 0, 200, 100))
        self.assertEqual(manager.anchored((20, 10), anchor="top_left", margin=(2, 3), use_rect=True), Rect(2, 3, 20, 10))

        node = SimpleNamespace(rect=Rect(0, 0, 1, 1))
        manager.place_gui_object(node, Rect(7, 8, 9, 10))
        self.assertEqual(node.rect, Rect(7, 8, 9, 10))

    def test_timers_repeat_callbacks(self) -> None:
        timers = Timers()
        fired = []
        timers.add_timer("tick", 0.05, lambda: fired.append(True))
        timers.update(0.02)
        timers.update(0.03)
        timers.update(0.10)
        self.assertEqual(len(fired), 3)

    def test_scheduler_messages_and_completion(self) -> None:
        scheduler = TaskScheduler(max_workers=2)
        messages = []

        def logic(task_id, params):
            total = params["total"]
            for idx in range(1, total + 1):
                scheduler.send_message(task_id, {"idx": idx})
            return {"ok": True, "total": total}

        scheduler.add_task("demo", logic, parameters={"total": 4}, message_method=lambda payload: messages.append(payload["idx"]))

        deadline = time.monotonic() + 1.5
        while time.monotonic() < deadline:
            scheduler.update()
            if scheduler.get_finished_events():
                break
            time.sleep(0.01)

        finished = scheduler.get_finished_events()
        self.assertEqual(len(finished), 1)
        self.assertEqual(finished[0].operation, "finished")
        self.assertEqual(finished[0].task_id, "demo")
        self.assertEqual(messages, [1, 2, 3, 4])
        self.assertEqual(scheduler.pop_result("demo")["total"], 4)
        scheduler.shutdown()

    def test_task_panel_auto_hide_animation(self) -> None:
        panel = TaskPanelControl("panel", Rect(10, 20, 100, 30), auto_hide=True, hidden_peek_pixels=4, animation_step_px=3)
        # Initially not hovered, should move toward hidden y.
        panel.update(0.016)
        self.assertLess(panel.rect.y, 20)

        event = SimpleNamespace(pos=(15, panel.rect.y + 2))
        panel.handle_event(event, None)
        for _ in range(10):
            panel.update(0.016)
        self.assertGreaterEqual(panel.rect.y, panel._hidden_y)


if __name__ == "__main__":
    unittest.main()
