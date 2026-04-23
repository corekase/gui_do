import os
import unittest
from types import SimpleNamespace

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame

from demo_parts.life_demo_part import LifeSimulationFeature
from demo_parts.mandelbrot_demo_part import MANDEL_KIND_STATUS
from demo_parts.mandelbrot_demo_part import MandelbrotRenderFeature


class _Packet:
    def __init__(self, *, local_pos=None, pos=None, button=1) -> None:
        self.local_pos = local_pos
        self.pos = pos
        self.button = button

    def is_mouse_down(self, button=None) -> bool:
        return button is None or button == self.button


class _CanvasStub:
    def __init__(self, events) -> None:
        self.rect = pygame.Rect(20, 30, 100, 100)
        self.canvas = pygame.Surface((100, 100), pygame.SRCALPHA)
        self._events = list(events)

    def read_event(self):
        if not self._events:
            return None
        return self._events.pop(0)


class _A11yControl:
    def __init__(self) -> None:
        self.tab_index = None
        self.role = None
        self.label = None

    def set_tab_index(self, value):
        self.tab_index = value

    def set_accessibility(self, *, role, label):
        self.role = role
        self.label = label


class _RootStub:
    def add(self, node):
        return node


class _LayoutStub:
    def __init__(self) -> None:
        self._linear_index = 0
        self._anchor = (0, 0)
        self._item_width = 100
        self._item_height = 30
        self._spacing = 8

    def anchored(self, size, anchor="top_right", margin=(0, 0), use_rect=True):
        del anchor, margin, use_rect
        return pygame.Rect(0, 0, int(size[0]), int(size[1]))

    def set_linear_properties(self, *, anchor, item_width, item_height, spacing, horizontal=True):
        del horizontal
        self._anchor = (int(anchor[0]), int(anchor[1]))
        self._item_width = int(item_width)
        self._item_height = int(item_height)
        self._spacing = int(spacing)
        self._linear_index = 0

    def next_linear(self):
        x = self._anchor[0] + self._linear_index * (self._item_width + self._spacing)
        y = self._anchor[1]
        self._linear_index += 1
        return pygame.Rect(x, y, self._item_width, self._item_height)


class _WindowStub:
    def __init__(self, _control_id, rect, _title, **_kwargs) -> None:
        self.rect = pygame.Rect(rect)
        self.children = []
        self.visible = True

    def content_rect(self):
        return pygame.Rect(self.rect.left, self.rect.top + 24, self.rect.width, self.rect.height - 24)

    def add(self, child):
        self.children.append(child)
        return child


class _WidgetStub:
    def __init__(self, *_args, **kwargs) -> None:
        self.rect = None
        for arg in _args:
            if isinstance(arg, pygame.Rect):
                self.rect = pygame.Rect(arg)
                break
        if self.rect is None:
            self.rect = pygame.Rect(0, 0, 10, 10)
        self.pushed = bool(kwargs.get("pushed", False))
        self.value = float(kwargs.get("value", kwargs.get("initial", 0.0)))
        self.text = str(_args[2]) if len(_args) > 2 and isinstance(_args[2], str) else ""
        self.enabled = True
        self.visible = True
        width = max(1, int(self.rect.width))
        height = max(1, int(self.rect.height))
        self.canvas = pygame.Surface((width, height), pygame.SRCALPHA)

    def accepts_focus(self) -> bool:
        return True


class _SliderStub(_WidgetStub):
    def __init__(self, *_args, **_kwargs) -> None:
        super().__init__(*_args, **_kwargs)
        if len(_args) >= 6:
            self.value = float(_args[5])


class _LabelStub(_WidgetStub):
    pass


class DemoPartsGuiPortabilityTests(unittest.TestCase):
    def setUp(self) -> None:
        pygame.init()
        pygame.display.set_mode((16, 16))

    def tearDown(self) -> None:
        pygame.quit()

    def test_life_update_life_works_without_demo_part_wrappers(self) -> None:
        part = LifeSimulationFeature()
        host = SimpleNamespace(app=SimpleNamespace(theme=SimpleNamespace(medium=(0, 0, 0))))
        part.demo = host
        part.canvas = _CanvasStub([_Packet(local_pos=(10, 10), button=1)])
        part.toggle = SimpleNamespace(pushed=False)
        part.zoom_slider = SimpleNamespace(value=5.0)
        part.zoom_label = SimpleNamespace(text="")
        part.life_origin = [0.0, 0.0]
        part.life_cell_size = 10

        part.update_life()

        self.assertIn((1, 1), part.life_cells)

    def test_life_part_messages_are_consumed_in_on_update(self) -> None:
        part = LifeSimulationFeature()
        host = SimpleNamespace(app=SimpleNamespace(theme=SimpleNamespace(medium=(0, 0, 0))))
        part.demo = host
        part.canvas = _CanvasStub([])
        part.toggle = SimpleNamespace(pushed=False)
        part.zoom_slider = SimpleNamespace(value=5.0)
        part.zoom_label = SimpleNamespace(text="")

        part.enqueue_message({"topic": "life_logic", "event": "state", "life_cells": {(4, 5)}})

        part.update_life()
        self.assertEqual(part.life_cells, set())

        part.on_update(host)
        self.assertEqual(part.life_cells, {(4, 5)})

    def test_life_part_ignores_unregistered_message_topics(self) -> None:
        part = LifeSimulationFeature()
        host = SimpleNamespace(app=SimpleNamespace(theme=SimpleNamespace(medium=(0, 0, 0))))
        part.demo = host
        part.canvas = _CanvasStub([])
        part.toggle = SimpleNamespace(pushed=False)
        part.zoom_slider = SimpleNamespace(value=5.0)
        part.zoom_label = SimpleNamespace(text="")
        part.life_cells = {(9, 9)}

        part.enqueue_message({"topic": "demo.mandel.status", "kind": "status", "detail": "ignored"})

        part.on_update(host)

        self.assertEqual(part.life_cells, {(9, 9)})

    def test_life_accessibility_uses_part_owned_controls(self) -> None:
        part = LifeSimulationFeature()
        part.reset_button = _A11yControl()
        part.toggle = _A11yControl()
        part.zoom_slider = _A11yControl()

        next_index = part.configure_accessibility(SimpleNamespace(), 3)

        self.assertEqual(next_index, 6)
        self.assertEqual(part.reset_button.tab_index, 3)
        self.assertEqual(part.toggle.tab_index, 4)
        self.assertEqual(part.zoom_slider.tab_index, 5)

    def test_mandel_publish_event_updates_internal_status_without_model(self) -> None:
        part = MandelbrotRenderFeature()
        host = SimpleNamespace(app=SimpleNamespace())
        part.demo = host
        part.status_label = SimpleNamespace(text="")

        part.publish_event(MANDEL_KIND_STATUS, "portable status")

        self.assertEqual(part.status_text, "portable status")
        self.assertEqual(part.status_label.text, "portable status")

    def test_mandel_status_event_from_bus_updates_internal_status_without_model(self) -> None:
        part = MandelbrotRenderFeature()
        host = SimpleNamespace(app=SimpleNamespace())
        part.demo = host
        part.status_label = SimpleNamespace(text="")

        part.on_status_event(host, {"kind": MANDEL_KIND_STATUS, "detail": "bus status"})

        self.assertEqual(part.status_text, "bus status")
        self.assertEqual(part.status_label.text, "bus status")

    def test_life_build_window_requests_frame_backdrop_mode(self) -> None:
        captured = {}

        class _CaptureLifeWindow(_WindowStub):
            def __init__(self, control_id, rect, title, **kwargs) -> None:
                captured.update(kwargs)
                super().__init__(control_id, rect, title, **kwargs)

        demo = SimpleNamespace(
            root=_RootStub(),
            app=SimpleNamespace(layout=_LayoutStub(), style_label=lambda label, **_kwargs: label),
        )
        part = LifeSimulationFeature()
        part.demo = demo
        part.register_font_roles = lambda *_args, **_kwargs: None
        part.font_role = lambda _name: "body"

        part.build_window(
            demo,
            window_control_cls=_CaptureLifeWindow,
            canvas_control_cls=_WidgetStub,
            button_control_cls=_WidgetStub,
            toggle_control_cls=_WidgetStub,
            slider_control_cls=_SliderStub,
            label_control_cls=_LabelStub,
            layout_axis_cls=SimpleNamespace(HORIZONTAL="h"),
        )

        self.assertTrue(captured.get("use_frame_backdrop"))

    def test_mandel_build_window_requests_frame_backdrop_mode(self) -> None:
        captured = {}

        class _CaptureMandelWindow(_WindowStub):
            def __init__(self, control_id, rect, title, **kwargs) -> None:
                captured.update(kwargs)
                super().__init__(control_id, rect, title, **kwargs)

        scheduler_stub = SimpleNamespace(remove_tasks=lambda *_args: None)
        focus_stub = SimpleNamespace(focused_node=None, set_focus=lambda *_args, **_kwargs: None, revalidate_focus=lambda *_args, **_kwargs: None)
        demo = SimpleNamespace(
            root=_RootStub(),
            app=SimpleNamespace(
                layout=_LayoutStub(),
                style_label=lambda label, **_kwargs: label,
                theme=SimpleNamespace(medium=(0, 0, 0)),
                focus=focus_stub,
                scene=SimpleNamespace(),
                get_scene_scheduler=lambda _name: scheduler_stub,
            ),
        )
        part = MandelbrotRenderFeature()
        part.demo = demo
        part.font_role = lambda _name: "body"

        part.build_window(
            demo,
            window_control_cls=_CaptureMandelWindow,
            label_control_cls=_LabelStub,
            canvas_control_cls=_WidgetStub,
            button_control_cls=_WidgetStub,
        )

        self.assertTrue(captured.get("use_frame_backdrop"))


if __name__ == "__main__":
    unittest.main()
