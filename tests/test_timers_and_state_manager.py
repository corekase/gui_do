import unittest
from concurrent.futures import Future
from threading import Event

from gui_manager_test_factory import build_state_manager_stub
from gui.utility.scheduler import Scheduler, Task, Timers
from gui.utility.statemanager import StateManager


class SchedulerStub:
    def __init__(self, fail: bool = False) -> None:
        self.fail = fail
        self.shutdown_calls = 0

    def shutdown(self) -> None:
        self.shutdown_calls += 1
        if self.fail:
            raise RuntimeError("shutdown failed")


class GuiStubFactory:
    @staticmethod
    def build(mouse_pos=(0, 0), fail_shutdown: bool = False):
        gui = build_state_manager_stub()
        gui._scheduler = SchedulerStub(fail=fail_shutdown)
        gui._mouse_pos = mouse_pos
        gui.set_calls = []

        def set_mouse_pos(pos, update_physical_coords=True):
            gui._mouse_pos = pos
            gui.set_calls.append((pos, update_physical_coords))
        gui.set_mouse_pos = set_mouse_pos
        return gui

    @staticmethod
    def build_with_real_scheduler(mouse_pos=(0, 0)):
        gui = build_state_manager_stub()
        gui._scheduler = Scheduler(gui)
        gui._mouse_pos = mouse_pos
        gui.set_calls = []

        def set_mouse_pos(pos, update_physical_coords=True):
            gui._mouse_pos = pos
            gui.set_calls.append((pos, update_physical_coords))
        gui.set_mouse_pos = set_mouse_pos
        return gui


class TimersTests(unittest.TestCase):
    def test_timer_accumulates_elapsed_before_firing(self) -> None:
        timers = Timers()
        fired = []

        timers.add_timer("tick", 10, lambda: fired.append(True))
        timers.timer_updates(100)
        timers.timer_updates(105)
        timers.timer_updates(116)

        self.assertEqual(len(fired), 1)

    def test_timer_can_fire_multiple_times_in_one_update(self) -> None:
        timers = Timers()
        fired = []

        timers.add_timer("tick", 10, lambda: fired.append(True))
        timers.timer_updates(0)
        timers.timer_updates(35)

        self.assertEqual(len(fired), 3)

    def test_timer_callback_can_remove_own_timer(self) -> None:
        timers = Timers()
        fired = []

        def callback() -> None:
            fired.append(True)
            timers.remove_timer("self")

        timers.add_timer("self", 10, callback)
        timers.timer_updates(0)
        timers.timer_updates(25)

        self.assertEqual(len(fired), 1)
        self.assertNotIn("self", timers.timers)


class StateManagerLifecycleTests(unittest.TestCase):
    def test_switch_context_carries_mouse_from_previous_context(self) -> None:
        manager = StateManager(mouse_pos_provider=lambda: (99, 88))
        old_gui = GuiStubFactory.build(mouse_pos=(12, 34))
        new_gui = GuiStubFactory.build(mouse_pos=(0, 0))

        manager.register_context("old", old_gui)
        manager.register_context("new", new_gui)

        manager.switch_context("old")
        old_gui._mouse_pos = (12, 34)
        manager.switch_context("new")

        self.assertEqual(new_gui._mouse_pos, (12, 34))
        self.assertEqual(new_gui.set_calls[-1], ((12, 34), True))

    def test_exit_shuts_down_all_contexts_even_if_one_fails(self) -> None:
        manager = StateManager(mouse_pos_provider=lambda: (0, 0))
        gui_ok = GuiStubFactory.build(fail_shutdown=False)
        gui_fail = GuiStubFactory.build(fail_shutdown=True)

        manager.register_context("ok", gui_ok)
        manager.register_context("fail", gui_fail)

        with self.assertLogs("gui.utility.statemanager", level="WARNING") as captured:
            manager.__exit__(None, None, None)

        self.assertEqual(gui_ok._scheduler.shutdown_calls, 1)
        self.assertEqual(gui_fail._scheduler.shutdown_calls, 1)
        self.assertEqual(manager.is_running, False)
        self.assertTrue(any('context "fail"' in message for message in captured.output))
        self.assertTrue(any('shutdown failed' in message for message in captured.output))

    def test_repeated_enter_exit_cycles_keep_shutdown_stable(self) -> None:
        manager = StateManager(mouse_pos_provider=lambda: (0, 0))
        gui_ok = GuiStubFactory.build(fail_shutdown=False)
        gui_fail = GuiStubFactory.build(fail_shutdown=True)

        manager.register_context("ok", gui_ok)
        manager.register_context("fail", gui_fail)

        for _ in range(3):
            manager.__enter__()
            self.assertTrue(manager.is_running)
            with self.assertLogs("gui.utility.statemanager", level="WARNING") as captured:
                manager.__exit__(None, None, None)
            self.assertFalse(manager.is_running)
            self.assertTrue(any('context "fail"' in message for message in captured.output))
            self.assertTrue(any('shutdown failed' in message for message in captured.output))

        self.assertEqual(gui_ok._scheduler.shutdown_calls, 3)
        self.assertEqual(gui_fail._scheduler.shutdown_calls, 3)

    def test_enter_restores_running_state_after_exit(self) -> None:
        manager = StateManager(mouse_pos_provider=lambda: (0, 0))
        gui_ok = GuiStubFactory.build(fail_shutdown=False)

        manager.register_context("ok", gui_ok)
        manager.__exit__(None, None, None)
        self.assertFalse(manager.is_running)

        manager.__enter__()

        self.assertTrue(manager.is_running)

    def test_rapid_multi_context_switch_carries_previous_mouse_each_hop(self) -> None:
        manager = StateManager(mouse_pos_provider=lambda: (111, 222))
        gui_a = GuiStubFactory.build(mouse_pos=(1, 1))
        gui_b = GuiStubFactory.build(mouse_pos=(2, 2))
        gui_c = GuiStubFactory.build(mouse_pos=(3, 3))

        manager.register_context("a", gui_a)
        manager.register_context("b", gui_b)
        manager.register_context("c", gui_c)

        manager.switch_context("a")
        gui_a._mouse_pos = (10, 10)

        manager.switch_context("b")
        self.assertEqual(gui_b._mouse_pos, (10, 10))
        self.assertEqual(gui_b.set_calls[-1], ((10, 10), True))
        gui_b._mouse_pos = (20, 20)

        manager.switch_context("c")
        self.assertEqual(gui_c._mouse_pos, (20, 20))
        self.assertEqual(gui_c.set_calls[-1], ((20, 20), True))
        gui_c._mouse_pos = (30, 30)

        manager.switch_context("a")
        self.assertEqual(gui_a._mouse_pos, (30, 30))
        self.assertEqual(gui_a.set_calls[-1], ((30, 30), True))

    def test_mouse_provider_used_only_for_first_activation_in_switch_chain(self) -> None:
        provider_calls = []

        def provider():
            provider_calls.append(True)
            return (77, 66)

        manager = StateManager(mouse_pos_provider=provider)
        gui_a = GuiStubFactory.build(mouse_pos=(0, 0))
        gui_b = GuiStubFactory.build(mouse_pos=(0, 0))
        gui_c = GuiStubFactory.build(mouse_pos=(0, 0))

        manager.register_context("a", gui_a)
        manager.register_context("b", gui_b)
        manager.register_context("c", gui_c)

        manager.switch_context("a")
        gui_a._mouse_pos = (5, 6)
        manager.switch_context("b")
        gui_b._mouse_pos = (7, 8)
        manager.switch_context("c")

        self.assertEqual(len(provider_calls), 1)
        self.assertEqual(gui_a.set_calls[-1], ((77, 66), True))
        self.assertEqual(gui_b.set_calls[-1], ((5, 6), True))
        self.assertEqual(gui_c.set_calls[-1], ((7, 8), True))

    def test_switch_to_same_context_is_noop_for_mouse_transfer(self) -> None:
        manager = StateManager(mouse_pos_provider=lambda: (44, 55))
        gui = GuiStubFactory.build(mouse_pos=(0, 0))
        manager.register_context("ctx", gui)

        manager.switch_context("ctx")
        set_call_count = len(gui.set_calls)
        gui._mouse_pos = (9, 9)

        manager.switch_context("ctx")

        self.assertEqual(len(gui.set_calls), set_call_count)
        self.assertEqual(gui._mouse_pos, (9, 9))

    def test_exit_cleans_real_scheduler_backlog_for_all_contexts(self) -> None:
        manager = StateManager(mouse_pos_provider=lambda: (0, 0))
        gui_a = GuiStubFactory.build_with_real_scheduler(mouse_pos=(1, 1))
        gui_b = GuiStubFactory.build_with_real_scheduler(mouse_pos=(2, 2))

        manager.register_context("a", gui_a)
        manager.register_context("b", gui_b)

        for scheduler in (gui_a._scheduler, gui_b._scheduler):
            scheduler.tasks["task"] = Task(
                id="task",
                run_callable=lambda: None,
                message_method=lambda _payload: None,
                generation=1,
            )
            scheduler._task_generation["task"] = 1
            scheduler._pending.append("task")
            scheduler._pending_set.add("task")
            scheduler.send_message("task", "m1")
            scheduler.send_message("task", "m2")
            scheduler._drain_incoming_task_messages()
            self.assertTrue(scheduler.tasks_busy())

        manager.__exit__(None, None, None)

        self.assertFalse(manager.is_running)
        for scheduler in (gui_a._scheduler, gui_b._scheduler):
            self.assertFalse(scheduler.tasks_active())
            self.assertFalse(scheduler.tasks_busy())
            self.assertEqual(scheduler.tasks, {})
            self.assertEqual(len(scheduler._task_messages), 0)
            self.assertEqual(scheduler._task_message_counts, {})

    def test_rapid_switch_then_exit_handles_mixed_context_cleanup(self) -> None:
        manager = StateManager(mouse_pos_provider=lambda: (13, 17))
        gui_real = GuiStubFactory.build_with_real_scheduler(mouse_pos=(1, 1))
        gui_regular = GuiStubFactory.build(mouse_pos=(2, 2), fail_shutdown=False)
        gui_fail = GuiStubFactory.build(mouse_pos=(3, 3), fail_shutdown=True)

        manager.register_context("real", gui_real)
        manager.register_context("regular", gui_regular)
        manager.register_context("fail", gui_fail)

        manager.switch_context("real")
        gui_real._mouse_pos = (20, 21)
        manager.switch_context("regular")
        gui_regular._mouse_pos = (22, 23)
        manager.switch_context("fail")

        scheduler = gui_real._scheduler
        scheduler.tasks["task"] = Task(
            id="task",
            run_callable=lambda: None,
            message_method=lambda _payload: None,
            generation=1,
        )
        scheduler._task_generation["task"] = 1
        scheduler._pending.append("task")
        scheduler._pending_set.add("task")
        scheduler.send_message("task", "m1")
        scheduler._drain_incoming_task_messages()
        self.assertTrue(scheduler.tasks_busy())

        with self.assertLogs("gui.utility.statemanager", level="WARNING") as captured:
            manager.__exit__(None, None, None)

        self.assertFalse(manager.is_running)
        self.assertEqual(gui_regular._scheduler.shutdown_calls, 1)
        self.assertEqual(gui_fail._scheduler.shutdown_calls, 1)
        self.assertTrue(any('context "fail"' in message for message in captured.output))
        self.assertTrue(any('shutdown failed' in message for message in captured.output))
        self.assertFalse(scheduler.tasks_active())
        self.assertFalse(scheduler.tasks_busy())

    def test_exit_clears_throttled_scheduler_queued_counts(self) -> None:
        manager = StateManager(mouse_pos_provider=lambda: (0, 0))
        gui = GuiStubFactory.build_with_real_scheduler(mouse_pos=(1, 1))
        manager.register_context("throttled", gui)

        scheduler = gui._scheduler
        scheduler.tasks["task"] = Task(
            id="task",
            run_callable=lambda: None,
            message_method=lambda _payload: None,
            generation=1,
        )
        scheduler._task_generation["task"] = 1
        scheduler.set_message_ingest_limit(1)
        scheduler.set_message_dispatch_limit(1)
        scheduler.set_max_queued_messages_per_task(32)

        for index in range(8):
            scheduler.send_message("task", index)

        scheduler._drain_incoming_task_messages()
        scheduler._dispatch_task_messages()

        self.assertGreater(scheduler._task_message_counts.get("task", 0), 0)

        manager.__exit__(None, None, None)

        self.assertFalse(scheduler.tasks_busy())
        self.assertEqual(scheduler._task_message_counts, {})
        self.assertEqual(len(scheduler._task_messages), 0)

    def test_exit_clears_throttled_pending_and_queued_across_contexts(self) -> None:
        manager = StateManager(mouse_pos_provider=lambda: (0, 0))
        gui_a = GuiStubFactory.build_with_real_scheduler(mouse_pos=(1, 1))
        gui_b = GuiStubFactory.build_with_real_scheduler(mouse_pos=(2, 2))
        manager.register_context("a", gui_a)
        manager.register_context("b", gui_b)

        for scheduler in (gui_a._scheduler, gui_b._scheduler):
            scheduler.tasks["task"] = Task(
                id="task",
                run_callable=lambda: None,
                message_method=lambda _payload: None,
                generation=1,
            )
            scheduler._task_generation["task"] = 1
            scheduler._pending.append("task")
            scheduler._pending_set.add("task")
            scheduler.set_message_ingest_limit(1)
            scheduler.set_message_dispatch_limit(1)

            scheduler.send_message("task", "m1")
            scheduler.send_message("task", "m2")
            scheduler._drain_incoming_task_messages()

            self.assertTrue(scheduler.tasks_busy())
            self.assertTrue(scheduler.tasks_active())

        manager.__exit__(None, None, None)

        for scheduler in (gui_a._scheduler, gui_b._scheduler):
            self.assertFalse(scheduler.tasks_active())
            self.assertFalse(scheduler.tasks_busy())
            self.assertEqual(scheduler._task_message_counts, {})
            self.assertEqual(len(scheduler._task_messages), 0)

    def test_exit_cleans_scheduler_state_with_inflight_running_task(self) -> None:
        manager = StateManager(mouse_pos_provider=lambda: (0, 0))
        gui = GuiStubFactory.build_with_real_scheduler(mouse_pos=(1, 1))
        manager.register_context("inflight", gui)

        scheduler = gui._scheduler
        started = Event()
        release = Event()

        def blocking_logic(_task_id):
            started.set()
            release.wait(timeout=2.0)
            return "done"

        scheduler.add_task("run", blocking_logic)
        scheduler.update()
        self.assertTrue(started.wait(timeout=1.0))
        self.assertTrue(scheduler.tasks_active_match_any("run"))

        try:
            manager.__exit__(None, None, None)

            self.assertFalse(manager.is_running)
            self.assertFalse(scheduler.tasks_active())
            self.assertFalse(scheduler.tasks_busy())
            self.assertEqual(scheduler.tasks, {})
            self.assertEqual(scheduler._running, set())
        finally:
            release.set()

    def test_stale_completion_queued_around_exit_is_ignored(self) -> None:
        manager = StateManager(mouse_pos_provider=lambda: (0, 0))
        gui = GuiStubFactory.build_with_real_scheduler(mouse_pos=(1, 1))
        manager.register_context("ctx", gui)

        scheduler = gui._scheduler
        future: Future[object] = Future()
        future.set_result("done")

        scheduler.tasks["task"] = Task(
            id="task",
            run_callable=lambda: None,
            message_method=None,
            future=future,
            generation=1,
        )
        scheduler._task_generation["task"] = 1
        scheduler._running.add("task")
        scheduler._enqueue_task_completion("task", 1, future)

        manager.__exit__(None, None, None)

        scheduler._collect_finished_tasks()

        self.assertEqual(scheduler.get_finished_tasks(), [])
        self.assertIsNone(scheduler.pop_result("task", default=None))
        self.assertEqual(scheduler.tasks, {})
        self.assertFalse(scheduler.tasks_busy())

    def test_stale_failure_queued_around_exit_is_ignored(self) -> None:
        manager = StateManager(mouse_pos_provider=lambda: (0, 0))
        gui = GuiStubFactory.build_with_real_scheduler(mouse_pos=(1, 1))
        manager.register_context("ctx", gui)

        scheduler = gui._scheduler
        scheduler.tasks["task"] = Task(
            id="task",
            run_callable=lambda: None,
            message_method=None,
            generation=1,
        )
        scheduler._task_generation["task"] = 1
        scheduler._enqueue_task_failure("task", 1, "late failure")

        manager.__exit__(None, None, None)

        scheduler._drain_incoming_task_failures()

        self.assertEqual(scheduler.get_failed_tasks(), [])
        self.assertEqual(scheduler.tasks, {})
        self.assertFalse(scheduler.tasks_busy())

    def test_exit_clears_suspended_task_bookkeeping(self) -> None:
        manager = StateManager(mouse_pos_provider=lambda: (0, 0))
        gui = GuiStubFactory.build_with_real_scheduler(mouse_pos=(1, 1))
        manager.register_context("ctx", gui)

        scheduler = gui._scheduler
        scheduler.add_task("a", lambda task_id: task_id)
        scheduler.add_task("b", lambda task_id: task_id)
        scheduler.add_task("c", lambda task_id: task_id)
        scheduler.suspend_tasks("b", "c")

        self.assertEqual(scheduler.read_suspended(), ["b", "c"])
        self.assertTrue(scheduler.tasks_active())

        manager.__exit__(None, None, None)

        self.assertFalse(manager.is_running)
        self.assertEqual(scheduler.read_suspended(), [])
        self.assertEqual(scheduler.read_suspended_len(), 0)
        self.assertEqual(scheduler._suspended_set, set())
        self.assertEqual(list(scheduler._pending), [])
        self.assertEqual(scheduler._pending_set, set())
        self.assertFalse(scheduler.tasks_active())
        self.assertFalse(scheduler.tasks_busy())

    def test_exit_clears_mixed_pending_suspended_and_queued_states(self) -> None:
        manager = StateManager(mouse_pos_provider=lambda: (0, 0))
        gui_a = GuiStubFactory.build_with_real_scheduler(mouse_pos=(1, 1))
        gui_b = GuiStubFactory.build_with_real_scheduler(mouse_pos=(2, 2))
        manager.register_context("a", gui_a)
        manager.register_context("b", gui_b)

        scheduler_a = gui_a._scheduler
        scheduler_b = gui_b._scheduler

        scheduler_a.add_task("a1", lambda task_id: task_id)
        scheduler_a.add_task("a2", lambda task_id: task_id)
        scheduler_a.suspend_tasks("a2")

        scheduler_b.tasks["b1"] = Task(
            id="b1",
            run_callable=lambda: None,
            message_method=lambda _payload: None,
            generation=1,
        )
        scheduler_b._task_generation["b1"] = 1
        scheduler_b._pending.append("b1")
        scheduler_b._pending_set.add("b1")
        scheduler_b.send_message("b1", "msg")
        scheduler_b._drain_incoming_task_messages()

        self.assertTrue(scheduler_a.read_suspended_len() > 0)
        self.assertTrue(scheduler_a.tasks_active())
        self.assertTrue(scheduler_b.tasks_busy())

        manager.__exit__(None, None, None)

        for scheduler in (scheduler_a, scheduler_b):
            self.assertEqual(scheduler.read_suspended(), [])
            self.assertEqual(scheduler.read_suspended_len(), 0)
            self.assertEqual(scheduler._suspended_set, set())
            self.assertEqual(list(scheduler._pending), [])
            self.assertEqual(scheduler._pending_set, set())
            self.assertEqual(scheduler._task_message_counts, {})
            self.assertEqual(len(scheduler._task_messages), 0)
            self.assertFalse(scheduler.tasks_active())
            self.assertFalse(scheduler.tasks_busy())

    def test_bounded_multi_cycle_rapid_switch_and_exit_leaves_no_state_leak(self) -> None:
        for cycle in range(6):
            manager = StateManager(mouse_pos_provider=lambda: (10 + cycle, 20 + cycle))
            gui_a = GuiStubFactory.build_with_real_scheduler(mouse_pos=(1, 1))
            gui_b = GuiStubFactory.build_with_real_scheduler(mouse_pos=(2, 2))
            gui_c = GuiStubFactory.build_with_real_scheduler(mouse_pos=(3, 3))
            manager.register_context("a", gui_a)
            manager.register_context("b", gui_b)
            manager.register_context("c", gui_c)

            manager.switch_context("a")
            gui_a._mouse_pos = (100 + cycle, 200 + cycle)
            manager.switch_context("b")
            gui_b._mouse_pos = (110 + cycle, 210 + cycle)
            manager.switch_context("c")

            scheduler_a = gui_a._scheduler
            scheduler_a.add_task("sa1", lambda task_id: task_id)
            scheduler_a.add_task("sa2", lambda task_id: task_id)
            scheduler_a.suspend_tasks("sa2")

            scheduler_b = gui_b._scheduler
            scheduler_b.tasks["sb1"] = Task(
                id="sb1",
                run_callable=lambda: None,
                message_method=lambda _payload: None,
                generation=1,
            )
            scheduler_b._task_generation["sb1"] = 1
            scheduler_b._pending.append("sb1")
            scheduler_b._pending_set.add("sb1")
            scheduler_b.set_message_ingest_limit(1)
            scheduler_b.set_message_dispatch_limit(1)
            scheduler_b.send_message("sb1", "m1")
            scheduler_b.send_message("sb1", "m2")
            scheduler_b._drain_incoming_task_messages()

            scheduler_c = gui_c._scheduler
            scheduler_c.tasks["sc1"] = Task(
                id="sc1",
                run_callable=lambda: None,
                message_method=lambda _payload: None,
                generation=1,
            )
            scheduler_c._task_generation["sc1"] = 1
            scheduler_c.send_message("sc1", "msg")

            self.assertTrue(scheduler_a.read_suspended_len() > 0)
            self.assertTrue(scheduler_b.tasks_busy())
            self.assertTrue(scheduler_c.tasks_busy())

            manager.__exit__(None, None, None)

            for scheduler in (scheduler_a, scheduler_b, scheduler_c):
                self.assertEqual(scheduler.read_suspended(), [])
                self.assertEqual(scheduler.read_suspended_len(), 0)
                self.assertEqual(scheduler._suspended_set, set())
                self.assertEqual(list(scheduler._pending), [])
                self.assertEqual(scheduler._pending_set, set())
                self.assertEqual(scheduler._task_message_counts, {})
                self.assertEqual(len(scheduler._task_messages), 0)
                self.assertFalse(scheduler.tasks_active())
                self.assertFalse(scheduler.tasks_busy())


if __name__ == "__main__":
    unittest.main()
