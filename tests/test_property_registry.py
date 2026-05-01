"""Tests for PropertyRegistry, ui_property decorator, and PropertyDescriptor."""
import unittest

from gui_do.introspection.property_registry import (
    PropertyDescriptor,
    PropertyRegistry,
    ui_property,
)


# ===========================================================================
# PropertyDescriptor dataclass
# ===========================================================================


class TestPropertyDescriptor(unittest.TestCase):
    def test_required_fields(self):
        d = PropertyDescriptor(name="alpha", label="Opacity")
        self.assertEqual("alpha", d.name)
        self.assertEqual("Opacity", d.label)

    def test_defaults(self):
        d = PropertyDescriptor(name="x", label="X")
        self.assertEqual("str", d.type)
        self.assertIsNone(d.min)
        self.assertIsNone(d.max)
        self.assertEqual("General", d.group)
        self.assertFalse(d.read_only)
        self.assertIsNone(d.owner_class)

    def test_custom_fields(self):
        d = PropertyDescriptor(
            name="width", label="Width", type="float",
            min=0.0, max=1000.0, group="Layout", read_only=True
        )
        self.assertEqual("float", d.type)
        self.assertEqual(0.0, d.min)
        self.assertEqual(1000.0, d.max)
        self.assertEqual("Layout", d.group)
        self.assertTrue(d.read_only)


# ===========================================================================
# ui_property decorator
# ===========================================================================


class TestUiPropertyDecorator(unittest.TestCase):
    def test_attaches_metadata_to_function(self):
        def my_getter(self):
            return 0

        decorated = ui_property(label="My Prop", type="int")(my_getter)
        meta = getattr(decorated, "_ui_property_meta", None)
        self.assertIsNotNone(meta)
        self.assertEqual("My Prop", meta["label"])
        self.assertEqual("int", meta["type"])

    def test_defaults_in_metadata(self):
        def getter(self):
            return 0

        decorated = ui_property(label="Test")(getter)
        meta = decorated._ui_property_meta
        self.assertIsNone(meta["min"])
        self.assertIsNone(meta["max"])
        self.assertEqual("General", meta["group"])
        self.assertFalse(meta["read_only"])


# ===========================================================================
# PropertyRegistry
# ===========================================================================


class _SampleBase:
    @property
    @ui_property(label="Base Prop", type="str", group="Base")
    def base_attr(self):
        return "base"


class _SampleChild(_SampleBase):
    @property
    @ui_property(label="Child Prop", type="int", min=0, max=100, group="Child")
    def child_attr(self):
        return 0


class TestPropertyRegistry(unittest.TestCase):
    def setUp(self):
        self.reg = PropertyRegistry()

    def test_descriptors_for_empty_class(self):
        class Plain:
            pass
        result = self.reg.descriptors_for(Plain)
        self.assertEqual([], result)

    def test_descriptors_for_single_property(self):
        descs = self.reg.descriptors_for(_SampleBase)
        names = [d.name for d in descs]
        self.assertIn("base_attr", names)

    def test_descriptor_metadata_correct(self):
        descs = self.reg.descriptors_for(_SampleBase)
        d = next(x for x in descs if x.name == "base_attr")
        self.assertEqual("Base Prop", d.label)
        self.assertEqual("str", d.type)
        self.assertEqual("Base", d.group)

    def test_inherits_parent_descriptors(self):
        descs = self.reg.descriptors_for(_SampleChild)
        names = [d.name for d in descs]
        self.assertIn("child_attr", names)
        self.assertIn("base_attr", names)

    def test_descriptors_for_instance(self):
        obj = _SampleBase()
        descs = self.reg.descriptors_for(obj)
        names = [d.name for d in descs]
        self.assertIn("base_attr", names)

    def test_manual_register(self):
        class Manually:
            pass

        d = PropertyDescriptor(name="foo", label="Foo", owner_class=Manually)
        self.reg.register(Manually, d)
        descs = self.reg.descriptors_for(Manually)
        self.assertTrue(any(x.name == "foo" for x in descs))

    def test_all_classes_returns_registered(self):
        self.reg.descriptors_for(_SampleBase)
        classes = self.reg.all_classes()
        self.assertIn(_SampleBase, classes)

    def test_clear_resets_registry(self):
        self.reg.descriptors_for(_SampleBase)
        self.reg.clear()
        # After clear, all_classes should be empty
        self.assertEqual([], self.reg.all_classes())


if __name__ == "__main__":
    unittest.main()
