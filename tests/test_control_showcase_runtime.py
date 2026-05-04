import unittest

from demo_features.controls.controls_showcase_feature import (
    control_has_open_popup,
    promote_open_popup_controls,
)


class _StubControl:
    def __init__(self, name: str):
        self.name = name
        self.visible = True
        self.enabled = True


class _StubRoot:
    def __init__(self, children):
        self.children = list(children)
        self.invalidated = False

    def invalidate(self):
        self.invalidated = True


class TestControlShowcaseRuntime(unittest.TestCase):
    def test_control_has_open_popup_detects_all_supported_flags(self):
        c1 = _StubControl("c1")
        c1._open = True
        self.assertTrue(control_has_open_popup(c1))

        c2 = _StubControl("c2")
        c2._dropdown_open = True
        self.assertTrue(control_has_open_popup(c2))

        c3 = _StubControl("c3")
        c3._is_open = True
        self.assertTrue(control_has_open_popup(c3))

        c4 = _StubControl("c4")
        c4._open_index = 0
        self.assertTrue(control_has_open_popup(c4))

        c5 = _StubControl("c5")
        self.assertFalse(control_has_open_popup(c5))

    def test_promote_open_popup_controls_moves_open_control_to_end(self):
        a = _StubControl("a")
        b = _StubControl("b")
        c = _StubControl("c")
        b._open = True

        root = _StubRoot([a, b, c])
        changed = promote_open_popup_controls(root, [a, b, c])

        self.assertTrue(changed)
        self.assertEqual([a, c, b], root.children)
        self.assertTrue(root.invalidated)

    def test_promote_open_popup_controls_noop_when_no_open_control(self):
        a = _StubControl("a")
        b = _StubControl("b")
        root = _StubRoot([a, b])

        changed = promote_open_popup_controls(root, [a, b])

        self.assertFalse(changed)
        self.assertEqual([a, b], root.children)
        self.assertFalse(root.invalidated)


if __name__ == "__main__":
    unittest.main()
