"""Tests for TransferData, TransferManager (overlays), and FormSchema (forms)."""
import unittest

from gui_do.overlays.transfer_data import TransferData, TransferManager
from gui_do.forms.form_schema import FormSchema, SchemaField


# ===========================================================================
# TransferData
# ===========================================================================


class TestTransferDataInitial(unittest.TestCase):
    def test_empty_formats(self):
        td = TransferData()
        self.assertEqual([], td.format_names())

    def test_preferred_format_default(self):
        td = TransferData()
        self.assertEqual("text/plain", td.preferred_format)

    def test_has_format_false_initially(self):
        td = TransferData()
        self.assertFalse(td.has_format("text/plain"))


class TestTransferDataSetGet(unittest.TestCase):
    def test_set_then_get(self):
        td = TransferData()
        td.set("text/plain", "hello")
        self.assertEqual("hello", td.get("text/plain"))

    def test_has_format_after_set(self):
        td = TransferData()
        td.set("image/png", b"\x89PNG")
        self.assertTrue(td.has_format("image/png"))

    def test_get_missing_returns_default(self):
        td = TransferData()
        self.assertIsNone(td.get("text/html"))

    def test_get_missing_custom_default(self):
        td = TransferData()
        self.assertEqual("fallback", td.get("text/html", "fallback"))

    def test_format_names_sorted(self):
        td = TransferData()
        td.set("z", 1)
        td.set("a", 2)
        self.assertEqual(["a", "z"], td.format_names())


# ===========================================================================
# TransferManager
# ===========================================================================


class TestTransferManagerClipboard(unittest.TestCase):
    def test_initial_clipboard_none(self):
        mgr = TransferManager()
        self.assertIsNone(mgr.get_clipboard())

    def test_set_clipboard(self):
        mgr = TransferManager()
        td = TransferData()
        td.set("text/plain", "hi")
        mgr.set_clipboard(td)
        self.assertIs(td, mgr.get_clipboard())

    def test_clear_clipboard(self):
        mgr = TransferManager()
        mgr.set_clipboard(TransferData())
        mgr.clear_clipboard()
        self.assertIsNone(mgr.get_clipboard())


class TestTransferManagerDrag(unittest.TestCase):
    def test_initial_drag_none(self):
        mgr = TransferManager()
        self.assertIsNone(mgr.current_drag())

    def test_begin_drag(self):
        mgr = TransferManager()
        td = TransferData()
        mgr.begin_drag(td)
        self.assertIs(td, mgr.current_drag())

    def test_end_drag_returns_data(self):
        mgr = TransferManager()
        td = TransferData()
        mgr.begin_drag(td)
        result = mgr.end_drag()
        self.assertIs(td, result)
        self.assertIsNone(mgr.current_drag())

    def test_copy_drag_to_clipboard(self):
        mgr = TransferManager()
        td = TransferData()
        mgr.begin_drag(td)
        success = mgr.copy_drag_to_clipboard()
        self.assertTrue(success)
        self.assertIs(td, mgr.get_clipboard())

    def test_copy_drag_no_drag_returns_false(self):
        mgr = TransferManager()
        self.assertFalse(mgr.copy_drag_to_clipboard())


# ===========================================================================
# SchemaField
# ===========================================================================


class TestSchemaField(unittest.TestCase):
    def test_fields_stored(self):
        sf = SchemaField(name="email", default="", label="Email", required=True)
        self.assertEqual("email", sf.name)
        self.assertEqual("", sf.default)
        self.assertEqual("Email", sf.label)
        self.assertTrue(sf.required)

    def test_defaults(self):
        sf = SchemaField(name="x", default=0)
        self.assertEqual("", sf.label)
        self.assertFalse(sf.required)
        self.assertEqual(0, len(sf.validators))


# ===========================================================================
# FormSchema
# ===========================================================================


class TestFormSchema(unittest.TestCase):
    def test_fields_property(self):
        schema = FormSchema([SchemaField("name", ""), SchemaField("age", 0)])
        self.assertEqual(2, len(schema.fields))

    def test_duplicate_names_raises(self):
        with self.assertRaises(ValueError):
            FormSchema([SchemaField("name", ""), SchemaField("name", "")])

    def test_build_form_creates_fields(self):
        schema = FormSchema([SchemaField("email", ""), SchemaField("volume", 1.0)])
        form = schema.build_form()
        self.assertIn("email", form.fields)
        self.assertIn("volume", form.fields)

    def test_defaults(self):
        schema = FormSchema([SchemaField("x", 10), SchemaField("y", 20)])
        self.assertEqual({"x": 10, "y": 20}, schema.defaults())

    def test_build_form_preserves_required(self):
        schema = FormSchema([SchemaField("name", "", required=True)])
        form = schema.build_form()
        field = form.field("name")
        # Required field should report invalid when empty string
        self.assertFalse(field.validate())

    def test_validate_values_no_errors(self):
        schema = FormSchema([SchemaField("name", "", required=True)])
        errors = schema.validate_values({"name": "Alice"})
        self.assertEqual([], errors)

    def test_validate_values_required_empty(self):
        schema = FormSchema([SchemaField("name", "", required=True)])
        errors = schema.validate_values({"name": ""})
        self.assertGreater(len(errors), 0)

    def test_extract_from(self):
        schema = FormSchema([SchemaField("x", 10), SchemaField("y", 20)])
        form = schema.build_form()
        form.field("x").value.value = 99
        extracted = schema.extract_from(form)
        self.assertEqual(99, extracted["x"])
        self.assertEqual(20, extracted["y"])


if __name__ == "__main__":
    unittest.main()
