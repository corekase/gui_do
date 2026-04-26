import unittest
from types import SimpleNamespace

from demo_features.bouncing_shapes_demo_feature import BouncingShapesBackdropFeature
from demo_features.life_demo_feature import LifeSimulationFeature
from demo_features.mandelbrot_demo_feature import MandelbrotRenderFeature
from demo_features.styles_demo_feature import StylesShowcaseFeature
from gui_do import Feature, FeatureManager


class DemoPartsHostContractTests(unittest.TestCase):

    def test_life_build_requires_app_and_root(self) -> None:
        feature = LifeSimulationFeature()
        manager = FeatureManager(SimpleNamespace())
        manager.register(feature)

        with self.assertRaisesRegex(AttributeError, "LifeSimulationFeature.build requires host fields: root"):
            manager.build_features(SimpleNamespace(app=SimpleNamespace()))

    def test_life_bind_runtime_requires_app(self) -> None:
        feature = LifeSimulationFeature()
        manager = FeatureManager(SimpleNamespace())
        manager.register(feature)

        with self.assertRaisesRegex(AttributeError, "LifeSimulationFeature.bind_runtime requires host fields: app"):
            manager.bind_runtime(SimpleNamespace())

    def test_mandel_build_requires_app_and_root(self) -> None:
        feature = MandelbrotRenderFeature()
        manager = FeatureManager(SimpleNamespace())
        manager.register(feature)

        with self.assertRaisesRegex(AttributeError, "MandelbrotRenderFeature.build requires host fields: root"):
            manager.build_features(SimpleNamespace(app=SimpleNamespace()))

    def test_mandel_bind_runtime_requires_app(self) -> None:
        feature = MandelbrotRenderFeature()
        manager = FeatureManager(SimpleNamespace())
        manager.register(feature)

        with self.assertRaisesRegex(AttributeError, "MandelbrotRenderFeature.bind_runtime requires host fields: app"):
            manager.bind_runtime(SimpleNamespace())

    def test_bouncing_bind_runtime_requires_screen_rect(self) -> None:
        feature = BouncingShapesBackdropFeature()
        manager = FeatureManager(SimpleNamespace())
        manager.register(feature)

        with self.assertRaisesRegex(AttributeError, "BouncingShapesBackdropFeature.bind_runtime requires host fields: screen_rect"):
            manager.bind_runtime(SimpleNamespace(app=SimpleNamespace()))

    def test_styles_build_requires_control_showcase_root(self) -> None:
        feature = StylesShowcaseFeature()
        manager = FeatureManager(SimpleNamespace())
        manager.register(feature)

        with self.assertRaisesRegex(AttributeError, "StylesShowcaseFeature.build requires host fields: control_showcase_root"):
            manager.build_features(SimpleNamespace(app=SimpleNamespace()))

    def test_demo_parts_inherit_host_parameter_contract_from_lifecycle(self) -> None:
        manager = FeatureManager(SimpleNamespace())
        parts = (
            BouncingShapesBackdropFeature(),
            StylesShowcaseFeature(),
            LifeSimulationFeature(),
            MandelbrotRenderFeature(),
        )

        for feature in parts:
            manager.register(feature)

    def test_register_rejects_parts_with_non_host_lifecycle_parameter_names(self) -> None:
        class _BadHostNamePart(Feature):
            def __init__(self) -> None:
                super().__init__("bad_host_name")

            def bind_runtime(self, demo) -> None:
                del demo

        manager = FeatureManager(SimpleNamespace())

        with self.assertRaisesRegex(
            ValueError,
            "_BadHostNamePart.bind_runtime first positional parameter must be 'host' or '_host'",
        ):
            manager.register(_BadHostNamePart())


if __name__ == "__main__":
    unittest.main()
