"""Tests for FileDialogManager, FileDialogOptions, and FileDialogHandle."""
import os
import tempfile
import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path
from pygame import Rect

import pygame
pygame.init()
pygame.display.set_mode((1, 1), pygame.NOFRAME)

from gui_do.core.file_dialog_manager import (
    FileDialogManager,
    FileDialogOptions,
    FileDialogHandle,
    _FileDialogPanel,
)


def _make_app() -> MagicMock:
    app = MagicMock()
    app.surface.get_rect.return_value = Rect(0, 0, 800, 600)
    app.surface.get_size.return_value = (800, 600)
    app.overlay = MagicMock()
    return app


class TestFileDialogOptions(unittest.TestCase):

    def test_defaults(self):
        opts = FileDialogOptions()
        self.assertEqual(opts.title, "Open File")
        self.assertIsNone(opts.start_dir)
        self.assertEqual(opts.filters, [])
        self.assertFalse(opts.allow_new_file)
        self.assertFalse(opts.multi_select)

    def test_custom_options(self):
        opts = FileDialogOptions(
            title="Save",
            start_dir="/tmp",
            filters=[("Images", [".png"])],
            allow_new_file=True,
        )
        self.assertEqual(opts.title, "Save")
        self.assertEqual(opts.start_dir, "/tmp")
        self.assertTrue(opts.allow_new_file)


class TestFileDialogHandle(unittest.TestCase):

    def test_initial_state_is_open(self):
        h = FileDialogHandle()
        self.assertTrue(h.is_open)
        self.assertIsNone(h.result)

    def test_resolve_closes_and_sets_result(self):
        h = FileDialogHandle()
        h._resolve(["/path/to/file.txt"])
        self.assertFalse(h.is_open)
        self.assertEqual(h.result, ["/path/to/file.txt"])

    def test_cancel_resolves_empty(self):
        h = FileDialogHandle()
        h._cancel()
        self.assertFalse(h.is_open)
        self.assertEqual(h.result, [])

    def test_on_close_callback_fired(self):
        received = []
        h = FileDialogHandle()
        h._on_close = lambda paths: received.extend(paths)
        h._resolve(["a.txt"])
        self.assertEqual(received, ["a.txt"])

    def test_on_close_callback_fired_on_cancel(self):
        received = []
        h = FileDialogHandle()
        h._on_close = lambda paths: received.extend(paths)
        h._cancel()
        self.assertEqual(received, [])


class TestFileDialogManager(unittest.TestCase):

    def test_show_open_returns_handle(self):
        app = _make_app()
        mgr = FileDialogManager(app)
        handle = mgr.show_open()
        self.assertIsInstance(handle, FileDialogHandle)
        self.assertTrue(handle.is_open)
        app.overlay.show.assert_called_once()

    def test_show_save_returns_handle(self):
        app = _make_app()
        mgr = FileDialogManager(app)
        handle = mgr.show_save()
        self.assertIsInstance(handle, FileDialogHandle)
        app.overlay.show.assert_called_once()

    def test_show_open_forces_allow_new_file_false(self):
        app = _make_app()
        mgr = FileDialogManager(app)
        opts = FileDialogOptions(allow_new_file=True)
        mgr.show_open(opts)
        # Panel created with allow_new_file=False
        panel = app.overlay.show.call_args[0][1]
        self.assertFalse(panel._opts.allow_new_file)

    def test_show_save_forces_allow_new_file_true(self):
        app = _make_app()
        mgr = FileDialogManager(app)
        opts = FileDialogOptions(allow_new_file=False, title="Save")
        mgr.show_save(opts)
        panel = app.overlay.show.call_args[0][1]
        self.assertTrue(panel._opts.allow_new_file)

    def test_on_close_callback_wired_to_handle(self):
        received = []
        app = _make_app()
        mgr = FileDialogManager(app)
        handle = mgr.show_open(on_close=lambda paths: received.extend(paths))
        handle._resolve(["file.txt"])
        self.assertEqual(received, ["file.txt"])

    def test_unique_owner_ids(self):
        app = _make_app()
        mgr = FileDialogManager(app)
        mgr.show_open()
        mgr.show_open()
        calls = app.overlay.show.call_args_list
        id0 = calls[0][0][0]
        id1 = calls[1][0][0]
        self.assertNotEqual(id0, id1)


class TestFileDialogPanelDirectoryListing(unittest.TestCase):

    def test_refresh_directory_lists_entries(self):
        app = _make_app()
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "file1.txt").write_text("a")
            (Path(tmpdir) / "file2.txt").write_text("b")
            opts = FileDialogOptions(start_dir=tmpdir)
            rect = Rect(50, 50, 600, 400)
            handle = FileDialogHandle()
            panel = _FileDialogPanel("p", rect, opts, handle, app)
            labels = [item.label for item in panel._list_view.items]
            # Should have both files (+ optional parent "..")
            names = [l for l in labels if l not in ("..",)]
            self.assertIn("file1.txt", names)
            self.assertIn("file2.txt", names)

    def test_filter_hides_non_matching_extensions(self):
        app = _make_app()
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "image.png").write_text("x")
            (Path(tmpdir) / "doc.txt").write_text("y")
            opts = FileDialogOptions(
                start_dir=tmpdir,
                filters=[("PNG", [".png"])],
            )
            rect = Rect(50, 50, 600, 400)
            handle = FileDialogHandle()
            panel = _FileDialogPanel("p", rect, opts, handle, app)
            labels = [item.label for item in panel._list_view.items]
            self.assertIn("image.png", labels)
            self.assertNotIn("doc.txt", labels)


if __name__ == "__main__":
    unittest.main()
