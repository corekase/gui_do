import unittest
from types import SimpleNamespace

from shared.part_lifecycle import Part, PartManager


class _PrewarmPart(Part):
    HOST_REQUIREMENTS = {
        "prewarm": ("app",),
    }

    def __init__(self, name: str, *, scene_name: str | None = None) -> None:
        super().__init__(name, scene_name=scene_name)
        self.prewarm_calls = 0

    def prewarm(self, host, surface, theme) -> None:
        del host, surface, theme
        self.prewarm_calls += 1


class PartManagerPrewarmRuntimeTests(unittest.TestCase):

    def setUp(self) -> None:
        self.app = SimpleNamespace(active_scene_name="main")
        self.manager = PartManager(self.app)
        self.host = SimpleNamespace(app=SimpleNamespace())

    def test_prewarm_parts_only_runs_active_scene_parts(self) -> None:
        main_part = _PrewarmPart("main_part", scene_name="main")
        showcase_part = _PrewarmPart("showcase_part", scene_name="control_showcase")
        shared_part = _PrewarmPart("shared_part", scene_name=None)
        self.manager.register(main_part, host=self.host)
        self.manager.register(showcase_part, host=self.host)
        self.manager.register(shared_part, host=self.host)

        warmed = self.manager.prewarm_parts(self.host, object(), object(), scene_name="control_showcase")

        self.assertEqual(2, warmed)
        self.assertEqual(0, main_part.prewarm_calls)
        self.assertEqual(1, showcase_part.prewarm_calls)
        self.assertEqual(1, shared_part.prewarm_calls)

    def test_prewarm_parts_is_idempotent_per_scene(self) -> None:
        part = _PrewarmPart("showcase_part", scene_name="control_showcase")
        self.manager.register(part, host=self.host)

        warmed_first = self.manager.prewarm_parts(self.host, object(), object(), scene_name="control_showcase")
        warmed_second = self.manager.prewarm_parts(self.host, object(), object(), scene_name="control_showcase")

        self.assertEqual(1, warmed_first)
        self.assertEqual(0, warmed_second)
        self.assertEqual(1, part.prewarm_calls)

    def test_prewarm_parts_force_replays_prewarm(self) -> None:
        part = _PrewarmPart("showcase_part", scene_name="control_showcase")
        self.manager.register(part, host=self.host)

        self.manager.prewarm_parts(self.host, object(), object(), scene_name="control_showcase")
        warmed = self.manager.prewarm_parts(self.host, object(), object(), scene_name="control_showcase", force=True)

        self.assertEqual(1, warmed)
        self.assertEqual(2, part.prewarm_calls)


if __name__ == "__main__":
    unittest.main()
