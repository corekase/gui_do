import unittest
from types import SimpleNamespace

from demo_parts.bouncing_shapes_demo_part import BouncingShapesBackdropFeature
from demo_parts.life_demo_part import LifeSimulationFeature
from demo_parts.mandelbrot_demo_part import MandelbrotRenderFeature
from shared.part_lifecycle import PartManager


class DemoPartsHostContractTests(unittest.TestCase):
    def test_life_build_requires_app_and_root(self) -> None:
        part = LifeSimulationFeature()
        manager = PartManager(SimpleNamespace())
        manager.register(part)

        with self.assertRaisesRegex(AttributeError, "LifeSimulationFeature.build requires host fields: root"):
            manager.build_parts(SimpleNamespace(app=SimpleNamespace()))

    def test_life_bind_runtime_requires_app(self) -> None:
        part = LifeSimulationFeature()
        manager = PartManager(SimpleNamespace())
        manager.register(part)

        with self.assertRaisesRegex(AttributeError, "LifeSimulationFeature.bind_runtime requires host fields: app"):
            manager.bind_runtime(SimpleNamespace())

    def test_mandel_build_requires_app_and_root(self) -> None:
        part = MandelbrotRenderFeature()
        manager = PartManager(SimpleNamespace())
        manager.register(part)

        with self.assertRaisesRegex(AttributeError, "MandelbrotRenderFeature.build requires host fields: root"):
            manager.build_parts(SimpleNamespace(app=SimpleNamespace()))

    def test_mandel_bind_runtime_requires_app(self) -> None:
        part = MandelbrotRenderFeature()
        manager = PartManager(SimpleNamespace())
        manager.register(part)

        with self.assertRaisesRegex(AttributeError, "MandelbrotRenderFeature.bind_runtime requires host fields: app"):
            manager.bind_runtime(SimpleNamespace())

    def test_bouncing_bind_runtime_requires_screen_rect(self) -> None:
        part = BouncingShapesBackdropFeature()
        manager = PartManager(SimpleNamespace())
        manager.register(part)

        with self.assertRaisesRegex(AttributeError, "BouncingShapesBackdropFeature.bind_runtime requires host fields: screen_rect"):
            manager.bind_runtime(SimpleNamespace(app=SimpleNamespace()))


if __name__ == "__main__":
    unittest.main()
