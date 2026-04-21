import time
import unittest
from types import SimpleNamespace
from unittest.mock import patch

import pygame
from pygame import Rect, Surface

from gui import (
    ArrowBoxControl,
    ButtonControl,
    ButtonGroupControl,
    CanvasControl,
    FrameControl,
    GuiApplication,
    LayoutManager,
    PanelControl,
    TaskPanelControl,
    TaskScheduler,
    TaskEvent,
    Timers,
    ToggleControl,
    WindowControl,
    WindowTilingManager,
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
        self.assertIsNotNone(WindowTilingManager)
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
        self.assertEqual(manager.anchored((20, 10), anchor="top_center", margin=(0, 4), use_rect=True), Rect(90, 4, 20, 10))
        self.assertEqual(manager.linear(2), Rect(5, 19, 10, 11))
        self.assertEqual(manager.next_linear(), Rect(5, 6, 10, 11))

        node = SimpleNamespace(rect=Rect(0, 0, 1, 1))
        manager.place_gui_object(node, Rect(7, 8, 9, 10))
        self.assertEqual(node.rect, Rect(7, 8, 9, 10))

    def test_window_tiling_api_tiles_non_overlapping_windows(self) -> None:
        pygame.init()
        try:
            app = GuiApplication(Surface((900, 700)))
            root = app.add(PanelControl("root", Rect(0, 0, 900, 700)))
            w1 = root.add(WindowControl("w1", Rect(20, 20, 260, 200), "W1"))
            w2 = root.add(WindowControl("w2", Rect(40, 40, 260, 200), "W2"))
            w3 = root.add(WindowControl("w3", Rect(60, 60, 260, 200), "W3"))

            app.set_window_tiling_enabled(True, relayout=False)
            app.configure_window_tiling(gap=12, padding=12, avoid_task_panel=False, center_on_failure=True, relayout=False)
            app.tile_windows()

            settings = app.read_window_tiling_settings()
            self.assertTrue(settings["enabled"])
            self.assertEqual(settings["gap"], 12)

            self.assertFalse(w1.rect.colliderect(w2.rect))
            self.assertFalse(w1.rect.colliderect(w3.rect))
            self.assertFalse(w2.rect.colliderect(w3.rect))
        finally:
            pygame.quit()

    def test_scene_window_tilers_are_independent(self) -> None:
        pygame.init()
        try:
            app = GuiApplication(Surface((900, 700)))
            app.create_scene("life")
            app.create_scene("mandel")

            app.switch_scene("life")
            life_tiler = app.window_tiling
            app.set_window_tiling_enabled(True, relayout=False)
            app.configure_window_tiling(gap=11, padding=22, avoid_task_panel=False, center_on_failure=False, relayout=False)

            app.switch_scene("mandel")
            mandel_tiler = app.window_tiling
            self.assertIsNot(life_tiler, mandel_tiler)

            settings = app.read_window_tiling_settings()
            self.assertFalse(settings["enabled"])
            self.assertEqual(settings["gap"], 16)
            self.assertEqual(settings["padding"], 16)
            self.assertTrue(settings["avoid_task_panel"])
            self.assertTrue(settings["center_on_failure"])

            app.set_window_tiling_enabled(True, relayout=False)
            app.configure_window_tiling(gap=7, padding=9, avoid_task_panel=True, center_on_failure=True, relayout=False)

            app.switch_scene("life")
            settings = app.read_window_tiling_settings()
            self.assertTrue(settings["enabled"])
            self.assertEqual(settings["gap"], 11)
            self.assertEqual(settings["padding"], 22)
            self.assertFalse(settings["avoid_task_panel"])
            self.assertFalse(settings["center_on_failure"])

            app.switch_scene("mandel")
            settings = app.read_window_tiling_settings()
            self.assertTrue(settings["enabled"])
            self.assertEqual(settings["gap"], 7)
            self.assertEqual(settings["padding"], 9)
            self.assertTrue(settings["avoid_task_panel"])
            self.assertTrue(settings["center_on_failure"])
        finally:
            pygame.quit()

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

    def test_scheduler_duplicate_task_id_replaces_pending_task(self) -> None:
        scheduler = TaskScheduler(max_workers=1)

        def old_logic(_task_id):
            return "old"

        def new_logic(_task_id):
            return "new"

        scheduler.add_task("dup", old_logic)
        scheduler.add_task("dup", new_logic)

        deadline = time.monotonic() + 1.5
        while time.monotonic() < deadline:
            scheduler.update()
            if scheduler.get_finished_events():
                break
            time.sleep(0.01)

        self.assertEqual(scheduler.pop_result("dup"), "new")
        scheduler.shutdown()

    def test_scheduler_suspend_resume_controls_execution(self) -> None:
        scheduler = TaskScheduler(max_workers=1)
        ran = []

        def logic(_task_id):
            ran.append(True)
            return "ok"

        scheduler.add_task("s", logic)
        scheduler.suspend_tasks("s")
        scheduler.update()
        self.assertEqual(ran, [])
        self.assertEqual(scheduler.read_suspended(), ["s"])

        scheduler.resume_tasks("s")
        deadline = time.monotonic() + 1.5
        while time.monotonic() < deadline:
            scheduler.update()
            if scheduler.get_finished_events():
                break
            time.sleep(0.01)

        self.assertEqual(ran, [True])
        self.assertEqual(scheduler.pop_result("s"), "ok")
        scheduler.shutdown()

    def test_scheduler_message_dispatch_and_ingest_limits(self) -> None:
        scheduler = TaskScheduler(max_workers=1)
        messages = []

        def logic(_task_id):
            time.sleep(0.2)
            return "done"

        scheduler.add_task("slow", logic, message_method=lambda payload: messages.append(payload))
        scheduler.set_message_ingest_limit(1)
        scheduler.set_message_dispatch_limit(1)

        scheduler.send_message("slow", 1)
        scheduler.send_message("slow", 2)
        scheduler.send_message("slow", 3)

        scheduler.update()
        self.assertEqual(messages, [1])
        scheduler.update()
        self.assertEqual(messages, [1, 2])
        scheduler.update()
        self.assertEqual(messages, [1, 2, 3])
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

    def test_button_arms_on_mouse_down_and_clicks_on_mouse_up(self) -> None:
        fired = []
        control = ButtonControl("b", Rect(10, 10, 80, 30), "B", on_click=lambda: fired.append(True))

        down = SimpleNamespace(type=pygame.MOUSEBUTTONDOWN, pos=(20, 20), button=1)
        up = SimpleNamespace(type=pygame.MOUSEBUTTONUP, pos=(20, 20), button=1)

        self.assertTrue(control.handle_event(down, None))
        self.assertTrue(control.pressed)
        self.assertEqual(fired, [])

        self.assertTrue(control.handle_event(up, None))
        self.assertFalse(control.pressed)
        self.assertEqual(fired, [True])

    def test_lock_point_dispatches_logical_pos_and_preserves_raw_pos(self) -> None:
        pygame.init()
        try:
            app = GuiApplication(Surface((300, 200)))

            class Probe:
                def __init__(self):
                    self.visible = True
                    self.enabled = True
                    self.captured = None

                def handle_event(self, event, _app):
                    if getattr(event, "type", None) == pygame.MOUSEMOTION:
                        self.captured = {
                            "pos": getattr(event, "pos", None),
                            "raw_pos": getattr(event, "raw_pos", None),
                            "rel": getattr(event, "rel", None),
                            "raw_rel": getattr(event, "raw_rel", None),
                        }
                    return False

                def update(self, _dt):
                    return None

                def draw(self, _surface, _theme):
                    return None

            probe = app.add(Probe())
            lock_point = (120, 90)
            app.set_lock_point(probe, lock_point)

            app.process_event(pygame.event.Event(pygame.MOUSEMOTION, {"pos": (240, 160), "rel": (7, -3)}))

            self.assertIsNotNone(probe.captured)
            self.assertEqual(probe.captured["pos"], lock_point)
            self.assertEqual(probe.captured["raw_pos"], (240, 160))
            self.assertEqual(probe.captured["raw_rel"], (7, -3))
            self.assertEqual(app.input_state.pointer_pos, lock_point)
        finally:
            pygame.quit()

    def test_mouse_wheel_updates_logical_pointer_without_motion_event(self) -> None:
        pygame.init()
        try:
            app = GuiApplication(Surface((300, 200)))
            app._logical_pointer_pos = (0, 0)
            app.input_state.pointer_pos = (0, 0)

            with patch("pygame.mouse.get_pos", return_value=(123, 77)):
                app.process_event(pygame.event.Event(pygame.MOUSEWHEEL, {"x": 0, "y": 1}))

            self.assertEqual(app.logical_pointer_pos, (123, 77))
            self.assertEqual(app.input_state.pointer_pos, (123, 77))
        finally:
            pygame.quit()

    def test_scene_switch_routes_event_update_and_draw_to_active_scene_only(self) -> None:
        pygame.init()
        try:
            app = GuiApplication(Surface((320, 180)))
            app.create_scene("life")
            app.create_scene("mandel")

            class Probe:
                def __init__(self):
                    self.visible = True
                    self.enabled = True
                    self.event_count = 0
                    self.update_count = 0
                    self.draw_count = 0

                def handle_event(self, _event, _app):
                    self.event_count += 1
                    return False

                def update(self, _dt):
                    self.update_count += 1

                def draw(self, _surface, _theme):
                    self.draw_count += 1

            life_probe = app.add(Probe(), scene_name="life")
            mandel_probe = app.add(Probe(), scene_name="mandel")

            motion = pygame.event.Event(pygame.MOUSEMOTION, {"pos": (40, 30), "rel": (2, 1)})

            app.switch_scene("life")
            app.process_event(motion)
            app.update(0.016)
            app.draw()

            self.assertEqual(life_probe.event_count, 1)
            self.assertEqual(life_probe.update_count, 1)
            self.assertEqual(life_probe.draw_count, 1)
            self.assertEqual(mandel_probe.event_count, 0)
            self.assertEqual(mandel_probe.update_count, 0)
            self.assertEqual(mandel_probe.draw_count, 0)

            app.switch_scene("mandel")
            app.process_event(motion)
            app.update(0.016)
            app.draw()

            self.assertEqual(life_probe.event_count, 1)
            self.assertEqual(life_probe.update_count, 1)
            self.assertEqual(life_probe.draw_count, 1)
            self.assertEqual(mandel_probe.event_count, 1)
            self.assertEqual(mandel_probe.update_count, 1)
            self.assertEqual(mandel_probe.draw_count, 1)
        finally:
            pygame.quit()

    def test_keyboard_routes_to_active_window_before_screen_handler(self) -> None:
        pygame.init()
        try:
            app = GuiApplication(Surface((320, 180)))
            root = app.add(PanelControl("root", Rect(0, 0, 320, 180)))

            seen = {"window": 0, "screen": 0}

            def window_handler(event) -> bool:
                if getattr(event, "type", None) == pygame.KEYDOWN and getattr(event, "key", None) == pygame.K_a:
                    seen["window"] += 1
                    return True
                return False

            win = root.add(WindowControl("win", Rect(20, 20, 180, 120), "A", event_handler=window_handler))
            win.active = True

            def screen_handler(_event) -> bool:
                seen["screen"] += 1
                return True

            app.set_screen_lifecycle(event_handler=screen_handler)
            app.process_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_a}))

            self.assertEqual(seen["window"], 1)
            self.assertEqual(seen["screen"], 0)
        finally:
            pygame.quit()

    def test_keyboard_routes_to_screen_handler_when_no_active_window(self) -> None:
        pygame.init()
        try:
            app = GuiApplication(Surface((320, 180)))
            root = app.add(PanelControl("root", Rect(0, 0, 320, 180)))

            seen = {"window": 0, "screen": 0}

            def window_handler(event) -> bool:
                if getattr(event, "type", None) == pygame.KEYDOWN:
                    seen["window"] += 1
                    return True
                return False

            root.add(WindowControl("win", Rect(20, 20, 180, 120), "A", event_handler=window_handler))

            def screen_handler(event) -> bool:
                if getattr(event, "type", None) == pygame.KEYDOWN and getattr(event, "key", None) == pygame.K_ESCAPE:
                    seen["screen"] += 1
                    return True
                return False

            app.set_screen_lifecycle(event_handler=screen_handler)
            app.process_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_ESCAPE}))

            self.assertEqual(seen["window"], 0)
            self.assertEqual(seen["screen"], 1)
        finally:
            pygame.quit()

    def test_scene_schedulers_are_independent_and_inactive_scene_tasks_do_not_advance(self) -> None:
        pygame.init()
        try:
            app = GuiApplication(Surface((320, 180)))
            app.create_scene("life")
            app.create_scene("mandel")

            life_scheduler = app.get_scene_scheduler("life")
            mandel_scheduler = app.get_scene_scheduler("mandel")
            self.assertIsNot(life_scheduler, mandel_scheduler)

            app.switch_scene("life")
            finished = {"life": False, "mandel": False}

            life_scheduler.add_task("life_task", lambda _task_id: "life-done")
            mandel_scheduler.add_task("mandel_task", lambda _task_id: "mandel-done")

            deadline = time.monotonic() + 1.0
            while time.monotonic() < deadline and not life_scheduler.get_finished_events():
                app.update(0.016)
                time.sleep(0.005)

            finished["life"] = bool(life_scheduler.get_finished_events())
            finished["mandel"] = bool(mandel_scheduler.get_finished_events())
            self.assertTrue(finished["life"])
            self.assertFalse(finished["mandel"])

            app.switch_scene("mandel")
            deadline = time.monotonic() + 1.0
            while time.monotonic() < deadline and not mandel_scheduler.get_finished_events():
                app.update(0.016)
                time.sleep(0.005)
            finished["mandel"] = bool(mandel_scheduler.get_finished_events())
            self.assertTrue(finished["mandel"])
        finally:
            pygame.quit()

    def test_scene_switch_suspends_inactive_scheduler_tasks_and_resumes_on_reactivation(self) -> None:
        pygame.init()
        try:
            app = GuiApplication(Surface((320, 180)))
            app.create_scene("life")
            app.create_scene("mandel")

            life_scheduler = app.get_scene_scheduler("life")
            mandel_scheduler = app.get_scene_scheduler("mandel")

            life_scheduler.add_task("life_task", lambda _task_id: "life")
            mandel_scheduler.add_task("mandel_task", lambda _task_id: "mandel")

            app.switch_scene("life")
            self.assertEqual(life_scheduler.read_suspended(), [])
            self.assertIn("mandel_task", mandel_scheduler.read_suspended())

            app.switch_scene("mandel")
            self.assertIn("life_task", life_scheduler.read_suspended())
            self.assertNotIn("mandel_task", mandel_scheduler.read_suspended())

            app.switch_scene("life")
            self.assertNotIn("life_task", life_scheduler.read_suspended())
            self.assertIn("mandel_task", mandel_scheduler.read_suspended())
        finally:
            pygame.quit()

    def test_running_inactive_scene_task_pauses_until_scene_is_active_again(self) -> None:
        pygame.init()
        try:
            app = GuiApplication(Surface((320, 180)))
            app.create_scene("life")
            app.create_scene("mandel")

            mandel_scheduler = app.get_scene_scheduler("mandel")

            def progress_task(task_id, params):
                for step in range(params["steps"]):
                    time.sleep(params["sleep"])
                    mandel_scheduler.send_message(task_id, step)
                return "done"

            consumed = []
            mandel_scheduler.add_task(
                "mandel_progress",
                progress_task,
                parameters={"steps": 200, "sleep": 0.002},
                message_method=lambda payload: consumed.append(payload),
            )

            app.switch_scene("mandel")
            app.update(0.016)

            app.switch_scene("life")
            paused_count = len(consumed)
            time.sleep(0.06)

            self.assertEqual(mandel_scheduler.get_finished_events(), [])
            self.assertEqual(len(consumed), paused_count)

            app.switch_scene("mandel")
            deadline = time.monotonic() + 2.5
            while time.monotonic() < deadline:
                app.update(0.016)
                if mandel_scheduler.get_finished_events():
                    break
                time.sleep(0.01)

            self.assertTrue(bool(mandel_scheduler.get_finished_events()))
        finally:
            pygame.quit()


if __name__ == "__main__":
    unittest.main()
