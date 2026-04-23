import unittest
from types import SimpleNamespace

from demo_parts.bouncing_shapes_demo_part import BouncingShapesBackdropFeature
from demo_parts.life_demo_part import LifeSimulationFeature
from demo_parts.life_demo_part import LifeSimulationLogicPart
from demo_parts.mandelbrot_demo_part import MandelbrotRenderFeature
from demo_parts.mandelbrot_demo_part import MandelbrotLogicPart
from demo_parts.styles_demo_part import StylesShowcaseFeature
from shared.part_lifecycle import Part, PartManager


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

    def test_styles_build_requires_control_showcase_root(self) -> None:
        part = StylesShowcaseFeature()
        manager = PartManager(SimpleNamespace())
        manager.register(part)

        with self.assertRaisesRegex(AttributeError, "StylesShowcaseFeature.build requires host fields: control_showcase_root"):
            manager.build_parts(SimpleNamespace(app=SimpleNamespace()))

    def test_demo_parts_inherit_host_parameter_contract_from_lifecycle(self) -> None:
        manager = PartManager(SimpleNamespace())
        parts = (
            BouncingShapesBackdropFeature(),
            StylesShowcaseFeature(),
            LifeSimulationFeature(),
            LifeSimulationLogicPart(),
            MandelbrotRenderFeature(),
            MandelbrotLogicPart(),
        )

        for part in parts:
            manager.register(part)

    def test_register_rejects_parts_with_non_host_lifecycle_parameter_names(self) -> None:
        class _BadHostNamePart(Part):
            def __init__(self) -> None:
                super().__init__("bad_host_name")

            def bind_runtime(self, demo) -> None:
                del demo

        manager = PartManager(SimpleNamespace())

        with self.assertRaisesRegex(
            ValueError,
            "_BadHostNamePart.bind_runtime first positional parameter must be 'host' or '_host'",
        ):
            manager.register(_BadHostNamePart())


if __name__ == "__main__":
    unittest.main()
