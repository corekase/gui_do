"""Tests for FirstFrameProfiler and FirstFrameSample."""
import unittest

from gui_do.app.first_frame_profiler import FirstFrameProfiler, FirstFrameSample


# ===========================================================================
# FirstFrameSample
# ===========================================================================


class TestFirstFrameSample(unittest.TestCase):
    def test_fields_stored(self):
        s = FirstFrameSample(category="render", key="ui", elapsed_ms=1.5, detail="info")
        self.assertEqual("render", s.category)
        self.assertEqual("ui", s.key)
        self.assertEqual(1.5, s.elapsed_ms)
        self.assertEqual("info", s.detail)


# ===========================================================================
# FirstFrameProfiler — initial state
# ===========================================================================


class TestFirstFrameProfilerInitial(unittest.TestCase):
    def test_disabled_by_default(self):
        p = FirstFrameProfiler()
        self.assertFalse(p.enabled)

    def test_min_ms_default(self):
        p = FirstFrameProfiler()
        self.assertEqual(0.25, p.min_ms)

    def test_scene_frame_count_zero_for_unknown(self):
        p = FirstFrameProfiler()
        self.assertEqual(0, p.scene_frame_count("unknown_scene"))

    def test_profile_first_frame_true_before_begin(self):
        p = FirstFrameProfiler()
        self.assertTrue(p.profile_first_frame("scene1"))


# ===========================================================================
# FirstFrameProfiler.configure
# ===========================================================================


class TestFirstFrameProfilerConfigure(unittest.TestCase):
    def test_configure_enable(self):
        p = FirstFrameProfiler()
        p.configure(enabled=True)
        self.assertTrue(p.enabled)

    def test_configure_min_ms(self):
        p = FirstFrameProfiler()
        p.configure(min_ms=1.0)
        self.assertEqual(1.0, p.min_ms)

    def test_configure_logger(self):
        p = FirstFrameProfiler()
        logger = lambda s: None
        p.configure(logger=logger)
        self.assertIs(logger, p._logger)


# ===========================================================================
# FirstFrameProfiler.begin_frame / scene_frame_count
# ===========================================================================


class TestFirstFrameProfilerBeginFrame(unittest.TestCase):
    def test_begin_frame_increments(self):
        p = FirstFrameProfiler()
        p.begin_frame("scene1")
        self.assertEqual(1, p.scene_frame_count("scene1"))

    def test_begin_frame_second_call(self):
        p = FirstFrameProfiler()
        p.begin_frame("scene1")
        p.begin_frame("scene1")
        self.assertEqual(2, p.scene_frame_count("scene1"))

    def test_begin_frame_different_scenes_independent(self):
        p = FirstFrameProfiler()
        p.begin_frame("a")
        p.begin_frame("b")
        p.begin_frame("b")
        self.assertEqual(1, p.scene_frame_count("a"))
        self.assertEqual(2, p.scene_frame_count("b"))

    def test_profile_first_frame_true_on_frame_one(self):
        p = FirstFrameProfiler()
        p.begin_frame("s")
        self.assertTrue(p.profile_first_frame("s"))

    def test_profile_first_frame_false_on_frame_two(self):
        p = FirstFrameProfiler()
        p.begin_frame("s")
        p.begin_frame("s")
        self.assertFalse(p.profile_first_frame("s"))


# ===========================================================================
# FirstFrameProfiler.record_once
# ===========================================================================


class TestFirstFrameProfilerRecordOnce(unittest.TestCase):
    def test_disabled_records_nothing(self):
        emitted = []
        p = FirstFrameProfiler(enabled=False, logger=lambda s: emitted.append(s))
        p.record_once("cat", "key", 100.0)
        self.assertEqual([], emitted)

    def test_enabled_records_above_min_ms(self):
        samples = []
        p = FirstFrameProfiler(enabled=True, min_ms=0.0, logger=lambda s: samples.append(s))
        p.record_once("render", "ui", 5.0, "detail")
        self.assertEqual(1, len(samples))

    def test_records_only_once_per_key(self):
        samples = []
        p = FirstFrameProfiler(enabled=True, min_ms=0.0, logger=lambda s: samples.append(s))
        p.record_once("render", "ui", 5.0)
        p.record_once("render", "ui", 5.0)
        self.assertEqual(1, len(samples))

    def test_below_min_ms_not_recorded(self):
        samples = []
        p = FirstFrameProfiler(enabled=True, min_ms=10.0, logger=lambda s: samples.append(s))
        p.record_once("cat", "key", 1.0)
        self.assertEqual([], samples)

    def test_different_keys_both_recorded(self):
        samples = []
        p = FirstFrameProfiler(enabled=True, min_ms=0.0, logger=lambda s: samples.append(s))
        p.record_once("cat", "key1", 5.0)
        p.record_once("cat", "key2", 5.0)
        self.assertEqual(2, len(samples))


if __name__ == "__main__":
    unittest.main()
