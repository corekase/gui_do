"""Tests for DocumentModel and SceneSpatialIndex."""
import tempfile
import unittest
from pathlib import Path

from pygame import Rect

from gui_do.forms.document_model import DocumentModel
from gui_do.introspection.spatial_index import SceneSpatialIndex


# ===========================================================================
# DocumentModel
# ===========================================================================


class TestDocumentModelInitialState(unittest.TestCase):
    def setUp(self):
        self.doc = DocumentModel(document_id="doc1")

    def test_document_id(self):
        self.assertEqual("doc1", self.doc.document_id)

    def test_content_initially_none(self):
        self.assertIsNone(self.doc.content)

    def test_path_initially_none(self):
        self.assertIsNone(self.doc.path)

    def test_revision_initially_zero(self):
        self.assertEqual(0, self.doc.revision)

    def test_saved_revision_initially_zero(self):
        self.assertEqual(0, self.doc.saved_revision)

    def test_initially_not_dirty(self):
        self.assertFalse(self.doc.is_dirty)

    def test_metadata_initially_empty(self):
        self.assertEqual({}, self.doc.metadata)


class TestDocumentModelSetContent(unittest.TestCase):
    def setUp(self):
        self.doc = DocumentModel(document_id="doc1")

    def test_set_content_updates_content(self):
        self.doc.set_content("hello")
        self.assertEqual("hello", self.doc.content)

    def test_set_content_increments_revision(self):
        self.doc.set_content("hello")
        self.assertEqual(1, self.doc.revision)

    def test_set_content_marks_dirty(self):
        self.doc.set_content("hello")
        self.assertTrue(self.doc.is_dirty)

    def test_set_content_multiple_times_increments(self):
        self.doc.set_content("a")
        self.doc.set_content("b")
        self.assertEqual(2, self.doc.revision)


class TestDocumentModelMarkSaved(unittest.TestCase):
    def setUp(self):
        self.doc = DocumentModel(document_id="doc1")
        self.doc.set_content("v1")

    def test_mark_saved_clears_dirty(self):
        self.doc.mark_saved()
        self.assertFalse(self.doc.is_dirty)

    def test_mark_saved_with_path_sets_path(self):
        self.doc.mark_saved(path="/tmp/doc.txt")
        self.assertEqual(Path("/tmp/doc.txt"), self.doc.path)

    def test_mark_saved_without_path_preserves_path(self):
        self.doc.path = Path("/existing/path.txt")
        self.doc.mark_saved()
        self.assertEqual(Path("/existing/path.txt"), self.doc.path)

    def test_mark_saved_syncs_saved_revision(self):
        self.doc.set_content("v2")
        self.doc.mark_saved()
        self.assertEqual(self.doc.revision, self.doc.saved_revision)


class TestDocumentModelUpdateMetadata(unittest.TestCase):
    def test_update_metadata_adds_keys(self):
        doc = DocumentModel(document_id="x")
        doc.update_metadata(author="Alice", version="1.0")
        self.assertEqual("Alice", doc.metadata["author"])
        self.assertEqual("1.0", doc.metadata["version"])

    def test_update_metadata_overwrites(self):
        doc = DocumentModel(document_id="x")
        doc.update_metadata(author="Alice")
        doc.update_metadata(author="Bob")
        self.assertEqual("Bob", doc.metadata["author"])


class TestDocumentModelSaveLoad(unittest.TestCase):
    def test_save_writes_file_and_marks_clean(self):
        doc = DocumentModel(document_id="x")
        doc.set_content("test content")
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "out.txt"
            doc.save(p)
            self.assertEqual("test content", p.read_text(encoding="utf-8"))
        self.assertFalse(doc.is_dirty)

    def test_save_no_path_raises(self):
        doc = DocumentModel(document_id="x")
        with self.assertRaises(ValueError):
            doc.save()

    def test_save_custom_saver(self):
        saved = {}
        def saver(path, content):
            saved["path"] = path
            saved["content"] = content

        doc = DocumentModel(document_id="x")
        doc.set_content({"key": "val"})
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "out.json"
            doc.save(p, saver=saver)
        self.assertEqual({"key": "val"}, saved["content"])

    def test_load_reads_file(self):
        doc = DocumentModel(document_id="x")
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "in.txt"
            p.write_text("loaded content", encoding="utf-8")
            result = doc.load(p)
        self.assertEqual("loaded content", result)
        self.assertEqual("loaded content", doc.content)
        self.assertFalse(doc.is_dirty)

    def test_load_custom_loader(self):
        doc = DocumentModel(document_id="x")
        loader = lambda path: {"loaded": True}
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "f.bin"
            p.touch()
            result = doc.load(p, loader=loader)
        self.assertEqual({"loaded": True}, result)


class TestDocumentModelSnapshotRestore(unittest.TestCase):
    def setUp(self):
        self.doc = DocumentModel(document_id="orig")
        self.doc.set_content("snapshot_content")
        self.doc.update_metadata(key="val")

    def test_snapshot_contains_expected_keys(self):
        snap = self.doc.snapshot()
        self.assertIn("document_id", snap)
        self.assertIn("content", snap)
        self.assertIn("revision", snap)
        self.assertIn("saved_revision", snap)
        self.assertIn("metadata", snap)

    def test_snapshot_content_matches(self):
        snap = self.doc.snapshot()
        self.assertEqual("snapshot_content", snap["content"])

    def test_snapshot_metadata_is_copy(self):
        snap = self.doc.snapshot()
        snap["metadata"]["extra"] = "x"
        self.assertNotIn("extra", self.doc.metadata)

    def test_restore_updates_content(self):
        snap = self.doc.snapshot()
        doc2 = DocumentModel(document_id="doc2")
        doc2.restore(snap)
        self.assertEqual("snapshot_content", doc2.content)

    def test_restore_updates_revision(self):
        snap = self.doc.snapshot()
        doc2 = DocumentModel(document_id="doc2")
        doc2.restore(snap)
        self.assertEqual(snap["revision"], doc2.revision)

    def test_restore_updates_metadata(self):
        snap = self.doc.snapshot()
        doc2 = DocumentModel(document_id="doc2")
        doc2.restore(snap)
        self.assertEqual("val", doc2.metadata["key"])

    def test_restore_path_none_stays_none(self):
        snap = self.doc.snapshot()
        doc2 = DocumentModel(document_id="doc2")
        doc2.restore(snap)
        self.assertIsNone(doc2.path)

    def test_restore_path_string_becomes_path(self):
        self.doc.mark_saved(path="/tmp/file.txt")
        snap = self.doc.snapshot()
        doc2 = DocumentModel(document_id="doc2")
        doc2.restore(snap)
        self.assertEqual(Path("/tmp/file.txt"), doc2.path)


# ===========================================================================
# SceneSpatialIndex
# ===========================================================================


class _FakeNode:
    """Minimal node that SceneSpatialIndex can operate on."""

    def __init__(self, control_id: str, rect: Rect, *, visible: bool = True, enabled: bool = True):
        self.control_id = control_id
        self.rect = rect
        self.visible = visible
        self.enabled = enabled


class _FakeScene:
    """Minimal scene that exposes _walk_nodes()."""

    def __init__(self, nodes):
        self._nodes_list = list(nodes)

    def _walk_nodes(self):
        yield from self._nodes_list


class TestSceneSpatialIndexInitialState(unittest.TestCase):
    def test_node_count_initially_zero(self):
        idx = SceneSpatialIndex()
        self.assertEqual(0, idx.node_count)

    def test_cell_size_default(self):
        idx = SceneSpatialIndex()
        self.assertEqual(64, idx.cell_size)

    def test_cell_size_custom(self):
        idx = SceneSpatialIndex(cell_size=32)
        self.assertEqual(32, idx.cell_size)

    def test_cell_size_minimum_one(self):
        idx = SceneSpatialIndex(cell_size=0)
        self.assertEqual(1, idx.cell_size)


class TestSceneSpatialIndexBuild(unittest.TestCase):
    def test_build_from_scene(self):
        nodes = [
            _FakeNode("a", Rect(0, 0, 50, 50)),
            _FakeNode("b", Rect(100, 100, 50, 50)),
        ]
        idx = SceneSpatialIndex()
        idx.build(_FakeScene(nodes))
        self.assertEqual(2, idx.node_count)

    def test_build_empty_scene(self):
        idx = SceneSpatialIndex()
        idx.build(_FakeScene([]))
        self.assertEqual(0, idx.node_count)

    def test_build_none_scene_does_not_raise(self):
        idx = SceneSpatialIndex()
        idx.build(None)
        self.assertEqual(0, idx.node_count)

    def test_rebuild_replaces_previous(self):
        n1 = _FakeNode("a", Rect(0, 0, 50, 50))
        idx = SceneSpatialIndex()
        idx.build(_FakeScene([n1]))
        n2 = _FakeNode("b", Rect(0, 0, 50, 50))
        idx.build(_FakeScene([n2]))
        self.assertEqual(1, idx.node_count)


class TestSceneSpatialIndexQueryPoint(unittest.TestCase):
    def setUp(self):
        self.idx = SceneSpatialIndex(cell_size=64)
        self.n = _FakeNode("box", Rect(10, 10, 80, 80))
        self.idx.build(_FakeScene([self.n]))

    def test_point_inside_returns_node(self):
        result = self.idx.query_point(50, 50)
        self.assertIn(self.n, result)

    def test_point_outside_returns_empty(self):
        result = self.idx.query_point(200, 200)
        self.assertEqual([], result)

    def test_point_on_boundary_top_left(self):
        result = self.idx.query_point(10, 10)
        self.assertIn(self.n, result)

    def test_invisible_node_excluded(self):
        n = _FakeNode("hidden", Rect(0, 0, 100, 100), visible=False)
        idx = SceneSpatialIndex(cell_size=64)
        idx.build(_FakeScene([n]))
        self.assertEqual([], idx.query_point(50, 50))

    def test_disabled_node_excluded(self):
        n = _FakeNode("disabled", Rect(0, 0, 100, 100), enabled=False)
        idx = SceneSpatialIndex(cell_size=64)
        idx.build(_FakeScene([n]))
        self.assertEqual([], idx.query_point(50, 50))

    def test_multiple_overlapping_nodes_all_returned(self):
        na = _FakeNode("a", Rect(0, 0, 100, 100))
        nb = _FakeNode("b", Rect(0, 0, 100, 100))
        idx = SceneSpatialIndex(cell_size=64)
        idx.build(_FakeScene([na, nb]))
        result = idx.query_point(50, 50)
        self.assertIn(na, result)
        self.assertIn(nb, result)

    def test_result_sorted_by_insertion_order(self):
        na = _FakeNode("a", Rect(0, 0, 100, 100))
        nb = _FakeNode("b", Rect(0, 0, 100, 100))
        nc = _FakeNode("c", Rect(0, 0, 100, 100))
        idx = SceneSpatialIndex(cell_size=64)
        idx.build(_FakeScene([na, nb, nc]))
        result = idx.query_point(50, 50)
        ids = [n.control_id for n in result]
        self.assertEqual(["a", "b", "c"], ids)


class TestSceneSpatialIndexQueryRect(unittest.TestCase):
    def test_overlapping_rect_returns_node(self):
        n = _FakeNode("box", Rect(50, 50, 50, 50))
        idx = SceneSpatialIndex(cell_size=64)
        idx.build(_FakeScene([n]))
        result = idx.query_rect(Rect(60, 60, 20, 20))
        self.assertIn(n, result)

    def test_non_overlapping_rect_returns_empty(self):
        n = _FakeNode("box", Rect(50, 50, 50, 50))
        idx = SceneSpatialIndex(cell_size=64)
        idx.build(_FakeScene([n]))
        self.assertEqual([], idx.query_rect(Rect(200, 200, 20, 20)))

    def test_query_rect_invisible_excluded(self):
        n = _FakeNode("box", Rect(0, 0, 100, 100), visible=False)
        idx = SceneSpatialIndex(cell_size=64)
        idx.build(_FakeScene([n]))
        self.assertEqual([], idx.query_rect(Rect(0, 0, 100, 100)))


class TestSceneSpatialIndexMutation(unittest.TestCase):
    def test_update_node_after_move(self):
        n = _FakeNode("box", Rect(0, 0, 50, 50))
        idx = SceneSpatialIndex(cell_size=64)
        idx.build(_FakeScene([n]))
        # Move node far away
        n.rect = Rect(300, 300, 50, 50)
        idx.update_node(n)
        # Old location should not find it
        self.assertEqual([], idx.query_point(25, 25))
        # New location should
        self.assertIn(n, idx.query_point(325, 325))

    def test_remove_node(self):
        n = _FakeNode("box", Rect(0, 0, 100, 100))
        idx = SceneSpatialIndex(cell_size=64)
        idx.build(_FakeScene([n]))
        idx.remove_node(n)
        self.assertEqual(0, idx.node_count)
        self.assertEqual([], idx.query_point(50, 50))

    def test_remove_missing_node_no_error(self):
        idx = SceneSpatialIndex()
        idx.remove_node(_FakeNode("ghost", Rect(0, 0, 10, 10)))  # should not raise

    def test_clear_empties_index(self):
        nodes = [_FakeNode("a", Rect(0, 0, 50, 50)), _FakeNode("b", Rect(100, 100, 50, 50))]
        idx = SceneSpatialIndex(cell_size=64)
        idx.build(_FakeScene(nodes))
        idx.clear()
        self.assertEqual(0, idx.node_count)

    def test_node_without_control_id_ignored(self):
        class _NoId:
            rect = Rect(0, 0, 100, 100)
            visible = True
            enabled = True

        idx = SceneSpatialIndex()
        idx.build(_FakeScene([_NoId()]))
        self.assertEqual(0, idx.node_count)

    def test_update_node_adds_if_new(self):
        n = _FakeNode("fresh", Rect(10, 10, 40, 40))
        idx = SceneSpatialIndex(cell_size=64)
        idx.update_node(n)
        self.assertEqual(1, idx.node_count)


if __name__ == "__main__":
    unittest.main()
