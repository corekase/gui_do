"""Tests for FileDialogOptions and FileDialogHandle pure-logic."""
import unittest

from gui_do.overlays.file_dialog_manager import FileDialogOptions, FileDialogHandle


# ===========================================================================
# FileDialogOptions
# ===========================================================================


class TestFileDialogOptions(unittest.TestCase):
    def test_defaults(self):
        opts = FileDialogOptions()
        self.assertEqual("Open File", opts.title)
        self.assertIsNone(opts.start_dir)
        self.assertEqual([], opts.filters)
        self.assertFalse(opts.allow_new_file)
        self.assertFalse(opts.multi_select)

    def test_custom_title(self):
        opts = FileDialogOptions(title="Save As...")
        self.assertEqual("Save As...", opts.title)

    def test_filters_stored(self):
        filters = [("Images", [".png", ".jpg"]), ("All", ["*"])]
        opts = FileDialogOptions(filters=filters)
        self.assertEqual(filters, opts.filters)

    def test_allow_new_file(self):
        opts = FileDialogOptions(allow_new_file=True)
        self.assertTrue(opts.allow_new_file)

    def test_multi_select(self):
        opts = FileDialogOptions(multi_select=True)
        self.assertTrue(opts.multi_select)

    def test_start_dir(self):
        opts = FileDialogOptions(start_dir="/home/user")
        self.assertEqual("/home/user", opts.start_dir)


# ===========================================================================
# FileDialogHandle
# ===========================================================================


class TestFileDialogHandleInitial(unittest.TestCase):
    def test_is_open_true(self):
        handle = FileDialogHandle()
        self.assertTrue(handle.is_open)

    def test_result_none(self):
        handle = FileDialogHandle()
        self.assertIsNone(handle.result)


class TestFileDialogHandleResolve(unittest.TestCase):
    def test_resolve_closes_dialog(self):
        handle = FileDialogHandle()
        handle._resolve(["/path/to/file.txt"])
        self.assertFalse(handle.is_open)

    def test_resolve_stores_paths(self):
        handle = FileDialogHandle()
        paths = ["/a.png", "/b.png"]
        handle._resolve(paths)
        self.assertEqual(paths, handle.result)

    def test_resolve_calls_on_close(self):
        handle = FileDialogHandle()
        received = []
        handle._on_close = lambda paths: received.extend(paths)
        handle._resolve(["/file.txt"])
        self.assertEqual(["/file.txt"], received)

    def test_cancel_resolves_empty(self):
        handle = FileDialogHandle()
        handle._cancel()
        self.assertEqual([], handle.result)
        self.assertFalse(handle.is_open)

    def test_on_close_exception_is_swallowed(self):
        handle = FileDialogHandle()
        handle._on_close = lambda _: (_ for _ in ()).throw(RuntimeError("boom"))
        # Should not raise
        handle._resolve([])

    def test_is_open_false_after_cancel(self):
        handle = FileDialogHandle()
        handle._cancel()
        self.assertFalse(handle.is_open)


if __name__ == "__main__":
    unittest.main()
