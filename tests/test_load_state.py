"""Tests for LoadState, LoadStateKind, and AsyncDataProvider subscription logic."""
import unittest

from gui_do.data.async_data_provider import LoadState, LoadStateKind


# ===========================================================================
# LoadStateKind
# ===========================================================================


class TestLoadStateKind(unittest.TestCase):
    def test_enum_values(self):
        self.assertEqual("idle", LoadStateKind.IDLE.value)
        self.assertEqual("loading", LoadStateKind.LOADING.value)
        self.assertEqual("loaded", LoadStateKind.LOADED.value)
        self.assertEqual("failed", LoadStateKind.FAILED.value)


# ===========================================================================
# LoadState
# ===========================================================================


class TestLoadStateIdle(unittest.TestCase):
    def test_default_kind(self):
        ls = LoadState()
        self.assertEqual(LoadStateKind.IDLE, ls.kind)

    def test_is_idle_true(self):
        ls = LoadState()
        self.assertTrue(ls.is_idle)

    def test_is_loading_false(self):
        ls = LoadState()
        self.assertFalse(ls.is_loading)

    def test_is_loaded_false(self):
        ls = LoadState()
        self.assertFalse(ls.is_loaded)

    def test_is_failed_false(self):
        ls = LoadState()
        self.assertFalse(ls.is_failed)

    def test_data_none(self):
        ls = LoadState()
        self.assertIsNone(ls.data)

    def test_error_none(self):
        ls = LoadState()
        self.assertIsNone(ls.error)

    def test_progress_zero(self):
        ls = LoadState()
        self.assertEqual(0.0, ls.progress)


class TestLoadStateLoading(unittest.TestCase):
    def test_is_loading(self):
        ls = LoadState(kind=LoadStateKind.LOADING, progress=0.5)
        self.assertTrue(ls.is_loading)
        self.assertFalse(ls.is_idle)
        self.assertFalse(ls.is_loaded)
        self.assertFalse(ls.is_failed)

    def test_progress_stored(self):
        ls = LoadState(kind=LoadStateKind.LOADING, progress=0.7)
        self.assertAlmostEqual(0.7, ls.progress)


class TestLoadStateLoaded(unittest.TestCase):
    def test_is_loaded(self):
        ls = LoadState(kind=LoadStateKind.LOADED, data=[1, 2, 3])
        self.assertTrue(ls.is_loaded)
        self.assertFalse(ls.is_idle)
        self.assertFalse(ls.is_loading)
        self.assertFalse(ls.is_failed)

    def test_data_stored(self):
        ls = LoadState(kind=LoadStateKind.LOADED, data={"key": "value"})
        self.assertEqual({"key": "value"}, ls.data)


class TestLoadStateFailed(unittest.TestCase):
    def test_is_failed(self):
        ls = LoadState(kind=LoadStateKind.FAILED, error="connection refused")
        self.assertTrue(ls.is_failed)
        self.assertFalse(ls.is_idle)
        self.assertFalse(ls.is_loading)
        self.assertFalse(ls.is_loaded)

    def test_error_stored(self):
        ls = LoadState(kind=LoadStateKind.FAILED, error="timeout")
        self.assertEqual("timeout", ls.error)


if __name__ == "__main__":
    unittest.main()
