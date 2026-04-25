import os
import unittest
from types import SimpleNamespace

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame

from demo_features.mandelbrot_demo_feature import MandelbrotLogicFeature, MandelbrotRenderFeature
from shared.feature_lifecycle import FeatureManager


class _ActionsStub:
    def register_action(self, _name, _callback):
        return None

    def bind_key(self, _key, _action, scene=None):
        return None


class _EventsStub:
    def subscribe(self, _topic, _handler, scope=None):
        return SimpleNamespace(topic="topic", scope=scope)

    def unsubscribe(self, _subscription):
        return None

    def publish(self, _topic, _payload, scope=None):
        return None


class _SchedulerStub:
    def __init__(self):
        self.messages = []

    def set_message_dispatch_limit(self, _limit):
        return None

    def add_task(self, task_id, worker, parameters=None, message_method=None):
        worker(task_id, parameters or {})
        return None

    def send_message(self, task_id, payload):
        self.messages.append((task_id, payload))

    def remove_tasks(self, *_task_ids):
        return None

    def tasks_busy_match_any(self, *_task_ids):
        return False

    def get_finished_events(self):
        return []

    def get_failed_events(self):
        return []

    def clear_events(self):
        return None

    def pop_result(self, _task_id, _default=None):
        return None


class MandelLogicFeatureRuntimeTests(unittest.TestCase):
    def setUp(self) -> None:
        pygame.init()
        pygame.display.set_mode((16, 16))

    def tearDown(self) -> None:
        pygame.quit()

    def test_logic_part_iterative_runnable_emits_scanlines(self) -> None:
        logic = MandelbrotLogicFeature("mandelbrot_logic_primary")
        manager = FeatureManager(SimpleNamespace(active_scene_name="main"))
        manager.register(logic, host=SimpleNamespace())
        manager.bind_runtime(SimpleNamespace())

        scheduler = _SchedulerStub()
        center, scale = logic.mandel_viewport(4, 3)

        manager.run(
            logic.name,
            "iterative_task",
            scheduler,
            "iter",
            {"size": (4, 3), "center": center, "scale": scale},
        )

        self.assertEqual(len(scheduler.messages), 3)
        for row_idx, (task_id, payload) in enumerate(scheduler.messages):
            self.assertEqual(task_id, "iter")
            self.assertEqual(payload[0], row_idx)
            self.assertEqual(len(payload[1]), 4)

    def test_render_feature_binds_all_mandel_logic_aliases(self) -> None:
        scheduler = _SchedulerStub()
        app = SimpleNamespace(
            active_scene_name="main",
            actions=_ActionsStub(),
            events=_EventsStub(),
            get_scene_scheduler=lambda _scene: scheduler,
        )
        host = SimpleNamespace(app=app)
        manager = FeatureManager(app)

        # Registering MandelbrotRenderFeature auto-registers all 5 logic features
        render = MandelbrotRenderFeature()
        manager.register(render, host=host)

        manager.bind_runtime(host)

        self.assertEqual(render.bound_logic_name(alias=render.LOGIC_ALIAS_PRIMARY), "mandelbrot_logic_primary")
        self.assertEqual(render.bound_logic_name(alias=render.LOGIC_ALIAS_CAN1), "mandelbrot_logic_can1")
        self.assertEqual(render.bound_logic_name(alias=render.LOGIC_ALIAS_CAN2), "mandelbrot_logic_can2")
        self.assertEqual(render.bound_logic_name(alias=render.LOGIC_ALIAS_CAN3), "mandelbrot_logic_can3")
        self.assertEqual(render.bound_logic_name(alias=render.LOGIC_ALIAS_CAN4), "mandelbrot_logic_can4")

    def test_launch_four_split_routes_each_canvas_task_to_its_logic_part(self) -> None:
        scheduler = _SchedulerStub()
        called_logic_parts = []

        app = SimpleNamespace(
            active_scene_name="main",
            actions=_ActionsStub(),
            events=_EventsStub(),
            theme=SimpleNamespace(medium=(0, 0, 0)),
            focus=SimpleNamespace(focused_node=None, set_focus=lambda *_args, **_kwargs: None, revalidate_focus=lambda *_args, **_kwargs: None),
            scene=SimpleNamespace(),
            get_scene_scheduler=lambda _scene: scheduler,
        )
        host = SimpleNamespace(app=app)
        manager = FeatureManager(app)

        # Registering MandelbrotRenderFeature auto-registers all 5 logic features
        render = MandelbrotRenderFeature()
        manager.register(render, host=host)

        app.run_feature_runnable = lambda part_name, runnable_name, sched, task_id, params: (
            called_logic_parts.append(part_name),
            manager.run(part_name, runnable_name, sched, task_id, params),
        )[-1]

        manager.bind_runtime(host)

        render.demo = host
        render.status_label = SimpleNamespace(text="Mandelbrot: idle")
        render.help_label = SimpleNamespace(text="")
        render.primary_canvas = SimpleNamespace(canvas=pygame.Surface((8, 8)), visible=True)
        render.split_canvases = {
            "can1": SimpleNamespace(canvas=pygame.Surface((8, 8)), visible=False),
            "can2": SimpleNamespace(canvas=pygame.Surface((8, 8)), visible=False),
            "can3": SimpleNamespace(canvas=pygame.Surface((8, 8)), visible=False),
            "can4": SimpleNamespace(canvas=pygame.Surface((8, 8)), visible=False),
        }

        render.launch_four_split(host)

        self.assertEqual(
            called_logic_parts,
            [
                "mandelbrot_logic_can1",
                "mandelbrot_logic_can2",
                "mandelbrot_logic_can3",
                "mandelbrot_logic_can4",
            ],
        )


if __name__ == "__main__":
    unittest.main()
