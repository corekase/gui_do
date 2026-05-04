"""Tests for gui_do.layout.adaptive_constraint_layout."""
from __future__ import annotations

import unittest

from pygame import Rect

from gui_do.layout.adaptive_constraint_layout import (
    AdaptivePolicy,
    ConstraintAttr,
    ConstraintLayoutEngine,
    ConstraintSet,
    LayoutConstraint,
    resolve_adaptive_policy,
)


class TestLayoutConstraint(unittest.TestCase):
    def _container(self) -> Rect:
        return Rect(0, 0, 800, 600)

    def test_pixel_value(self):
        c = LayoutConstraint("w", ConstraintAttr.LEFT, 50)
        self.assertEqual(c.resolve(self._container()), 50)

    def test_fraction_width(self):
        c = LayoutConstraint("w", ConstraintAttr.LEFT, 0.5, is_fraction=True)
        self.assertAlmostEqual(c.resolve(self._container()), 400.0)

    def test_fraction_height(self):
        c = LayoutConstraint("w", ConstraintAttr.TOP, 0.25, is_fraction=True)
        self.assertAlmostEqual(c.resolve(self._container()), 150.0)

    def test_default_priority(self):
        c = LayoutConstraint("w", ConstraintAttr.WIDTH, 100)
        self.assertEqual(c.priority, 1000)


class TestConstraintSet(unittest.TestCase):
    def test_add_and_count(self):
        cs = ConstraintSet()
        cs.add(LayoutConstraint("w", ConstraintAttr.LEFT, 0))
        cs.add(LayoutConstraint("w", ConstraintAttr.TOP, 0))
        self.assertEqual(len(cs), 2)

    def test_conflict_same_priority_raises(self):
        cs = ConstraintSet()
        cs.add(LayoutConstraint("w", ConstraintAttr.LEFT, 0, priority=500))
        with self.assertRaises(ValueError):
            cs.add(LayoutConstraint("w", ConstraintAttr.LEFT, 10, priority=500))

    def test_higher_priority_replaces(self):
        cs = ConstraintSet()
        cs.add(LayoutConstraint("w", ConstraintAttr.LEFT, 0, priority=100))
        cs.add(LayoutConstraint("w", ConstraintAttr.LEFT, 50, priority=200))
        constraint = cs.for_target("w")[0]
        self.assertEqual(constraint.value, 50)

    def test_lower_priority_ignored(self):
        cs = ConstraintSet()
        cs.add(LayoutConstraint("w", ConstraintAttr.LEFT, 50, priority=200))
        cs.add(LayoutConstraint("w", ConstraintAttr.LEFT, 0, priority=100))
        constraint = cs.for_target("w")[0]
        self.assertEqual(constraint.value, 50)

    def test_remove(self):
        cs = ConstraintSet()
        cs.add(LayoutConstraint("w", ConstraintAttr.LEFT, 0))
        cs.remove("w", ConstraintAttr.LEFT)
        self.assertEqual(len(cs), 0)

    def test_for_target_filters(self):
        cs = ConstraintSet()
        cs.add(LayoutConstraint("a", ConstraintAttr.LEFT, 0))
        cs.add(LayoutConstraint("b", ConstraintAttr.LEFT, 0))
        self.assertEqual(len(cs.for_target("a")), 1)
        self.assertEqual(len(cs.for_target("b")), 1)

    def test_all_constraints_returns_copy(self):
        cs = ConstraintSet()
        all_c = cs.all_constraints
        all_c.append(LayoutConstraint("x", ConstraintAttr.WIDTH, 0))
        self.assertEqual(len(cs), 0)


class TestConstraintLayoutEngine(unittest.TestCase):
    def _container(self) -> Rect:
        return Rect(0, 0, 800, 600)

    def test_left_constraint(self):
        engine = ConstraintLayoutEngine()
        engine.set_initial_rect("btn", Rect(0, 0, 100, 30))
        cs = ConstraintSet()
        cs.add(LayoutConstraint("btn", ConstraintAttr.LEFT, 10))
        result = engine.solve(cs, self._container())
        self.assertEqual(result["btn"].left, 10)

    def test_top_constraint(self):
        engine = ConstraintLayoutEngine()
        engine.set_initial_rect("btn", Rect(0, 0, 100, 30))
        cs = ConstraintSet()
        cs.add(LayoutConstraint("btn", ConstraintAttr.TOP, 20))
        result = engine.solve(cs, self._container())
        self.assertEqual(result["btn"].top, 20)

    def test_right_constraint(self):
        engine = ConstraintLayoutEngine()
        engine.set_initial_rect("btn", Rect(0, 0, 100, 30))
        cs = ConstraintSet()
        cs.add(LayoutConstraint("btn", ConstraintAttr.RIGHT, 10))
        result = engine.solve(cs, self._container())
        self.assertEqual(result["btn"].right, self._container().right - 10)

    def test_width_constraint(self):
        engine = ConstraintLayoutEngine()
        engine.set_initial_rect("btn", Rect(0, 0, 50, 30))
        cs = ConstraintSet()
        cs.add(LayoutConstraint("btn", ConstraintAttr.WIDTH, 200))
        result = engine.solve(cs, self._container())
        self.assertEqual(result["btn"].width, 200)

    def test_height_constraint(self):
        engine = ConstraintLayoutEngine()
        engine.set_initial_rect("btn", Rect(0, 0, 50, 30))
        cs = ConstraintSet()
        cs.add(LayoutConstraint("btn", ConstraintAttr.HEIGHT, 60))
        result = engine.solve(cs, self._container())
        self.assertEqual(result["btn"].height, 60)

    def test_center_x_constraint(self):
        engine = ConstraintLayoutEngine()
        engine.set_initial_rect("btn", Rect(0, 0, 100, 30))
        cs = ConstraintSet()
        cs.add(LayoutConstraint("btn", ConstraintAttr.CENTER_X, 400))
        result = engine.solve(cs, self._container())
        self.assertEqual(result["btn"].centerx, 400)

    def test_center_y_constraint(self):
        engine = ConstraintLayoutEngine()
        engine.set_initial_rect("btn", Rect(0, 0, 100, 30))
        cs = ConstraintSet()
        cs.add(LayoutConstraint("btn", ConstraintAttr.CENTER_Y, 300))
        result = engine.solve(cs, self._container())
        self.assertEqual(result["btn"].centery, 300)

    def test_fraction_left(self):
        engine = ConstraintLayoutEngine()
        engine.set_initial_rect("x", Rect(0, 0, 0, 0))
        cs = ConstraintSet()
        cs.add(LayoutConstraint("x", ConstraintAttr.LEFT, 0.5, is_fraction=True))
        result = engine.solve(cs, self._container())
        self.assertEqual(result["x"].left, 400)

    def test_fallback_initial_rect_used(self):
        engine = ConstraintLayoutEngine()
        engine.set_initial_rect("w", Rect(5, 10, 200, 50))
        cs = ConstraintSet()  # no constraints for "w"
        result = engine.solve(cs, self._container())
        self.assertEqual(result["w"], Rect(5, 10, 200, 50))

    def test_multiple_widgets(self):
        engine = ConstraintLayoutEngine()
        engine.set_initial_rect("a", Rect(0, 0, 50, 20))
        engine.set_initial_rect("b", Rect(0, 0, 80, 30))
        cs = ConstraintSet()
        cs.add(LayoutConstraint("a", ConstraintAttr.LEFT, 10))
        cs.add(LayoutConstraint("b", ConstraintAttr.LEFT, 100))
        result = engine.solve(cs, self._container())
        self.assertEqual(result["a"].left, 10)
        self.assertEqual(result["b"].left, 100)

    def test_bottom_constraint(self):
        engine = ConstraintLayoutEngine()
        engine.set_initial_rect("btn", Rect(0, 0, 100, 30))
        cs = ConstraintSet()
        cs.add(LayoutConstraint("btn", ConstraintAttr.BOTTOM, 10))
        result = engine.solve(cs, self._container())
        self.assertEqual(result["btn"].bottom, self._container().bottom - 10)


class TestAdaptivePolicy(unittest.TestCase):
    def _make_policy(self, name: str, min_w: int) -> AdaptivePolicy:
        return AdaptivePolicy(
            name=name,
            min_width=min_w,
            constraints=[LayoutConstraint("w", ConstraintAttr.WIDTH, float(min_w))],
        )

    def test_resolve_returns_most_specific(self):
        desktop = self._make_policy("desktop", 1024)
        tablet = self._make_policy("tablet", 600)
        mobile = self._make_policy("mobile", 0)
        container = Rect(0, 0, 1200, 800)
        selected = resolve_adaptive_policy([mobile, tablet, desktop], container)
        self.assertEqual(selected.name, "desktop")

    def test_resolve_fallback(self):
        desktop = self._make_policy("desktop", 1024)
        mobile = self._make_policy("mobile", 0)
        container = Rect(0, 0, 400, 600)
        selected = resolve_adaptive_policy([desktop, mobile], container)
        self.assertEqual(selected.name, "mobile")

    def test_resolve_no_match_returns_none(self):
        policies = [self._make_policy("big", 2000)]
        container = Rect(0, 0, 800, 600)
        self.assertIsNone(resolve_adaptive_policy(policies, container))

    def test_build_constraint_set(self):
        policy = self._make_policy("desktop", 1024)
        cs = policy.build_constraint_set()
        self.assertEqual(len(cs), 1)


if __name__ == "__main__":
    unittest.main()
