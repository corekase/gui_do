import unittest

import pygame
from pygame import Rect

from gui_do.controls.chrome.window_control import WindowControl
from gui_do.controls.chrome.task_panel_control import TaskPanelControl
from gui_do.controls.composite.panel_control import PanelControl
from gui_do.controls.input.image_button_control import ImageButtonControl
from gui_do.events.gui_event import EventType, GuiEvent
from gui_do.events.pointer_capture import PointerCapture

pygame.init()


class _StubFactory:
    @staticmethod
    def build_disabled_bitmap(bitmap: pygame.Surface) -> pygame.Surface:
        out = bitmap.copy()
        out.fill((160, 160, 160, 255), special_flags=pygame.BLEND_RGBA_MULT)
        return out

    @staticmethod
    def build_hidden_bitmap(size) -> pygame.Surface:
        return pygame.Surface(size, pygame.SRCALPHA)

    @staticmethod
    def resolve_visual_state(visuals, *, visible: bool, enabled: bool, armed: bool, hovered: bool):
        if not visible:
            return visuals.hidden
        if not enabled:
            return visuals.disabled_armed if armed else visuals.disabled
        if armed:
            return visuals.armed
        if hovered:
            return visuals.hover
        return visuals.idle


class _StubTheme:
    def __init__(self):
        self.graphics_factory = _StubFactory()


class _StubFocus:
    focused_node = None

    @staticmethod
    def clear_focus() -> None:
        return None


class _StubApp:
    def __init__(self):
        self.surface = pygame.Surface((800, 600))
        self.pointer_capture = PointerCapture()
        self.focus = _StubFocus()
        self.logical_pointer_pos = (0, 0)

    @staticmethod
    def chain_screen_fallthrough(event_handler, *, scene_name=None):
        return lambda: True


class TestImageButtonControl(unittest.TestCase):
    def _make_control(self, on_click=None) -> ImageButtonControl:
        idle = pygame.Surface((12, 12), pygame.SRCALPHA)
        idle.fill((10, 20, 30, 255))
        hover = pygame.Surface((12, 12), pygame.SRCALPHA)
        hover.fill((40, 50, 60, 255))
        armed = pygame.Surface((12, 12), pygame.SRCALPHA)
        armed.fill((70, 80, 90, 255))
        return ImageButtonControl("img_btn", Rect(10, 10, 12, 12), idle, hover, armed, on_click=on_click)

    def test_click_invokes_callback_on_release_inside(self):
        calls = []
        control = self._make_control(on_click=lambda: calls.append("clicked"))
        app = _StubApp()

        down = GuiEvent(kind=EventType.MOUSE_BUTTON_DOWN, type=0, pos=(12, 12), button=1)
        up = GuiEvent(kind=EventType.MOUSE_BUTTON_UP, type=0, pos=(12, 12), button=1)

        self.assertTrue(control.handle_event(down, app))
        self.assertTrue(control.handle_event(up, app))
        self.assertEqual(["clicked"], calls)

    def test_release_outside_does_not_invoke_callback(self):
        calls = []
        control = self._make_control(on_click=lambda: calls.append("clicked"))
        app = _StubApp()

        down = GuiEvent(kind=EventType.MOUSE_BUTTON_DOWN, type=0, pos=(12, 12), button=1)
        move = GuiEvent(kind=EventType.MOUSE_MOTION, type=0, pos=(30, 30), rel=(18, 18), raw_rel=(18, 18))
        up = GuiEvent(kind=EventType.MOUSE_BUTTON_UP, type=0, pos=(30, 30), button=1)

        self.assertTrue(control.handle_event(down, app))
        self.assertFalse(control.handle_event(move, app))
        self.assertTrue(control.handle_event(up, app))
        self.assertEqual([], calls)

    def test_draw_uses_disabled_bitmap_when_control_disabled(self):
        control = self._make_control()
        control.enabled = False
        theme = _StubTheme()
        canvas = pygame.Surface((40, 40), pygame.SRCALPHA)

        control.draw(canvas, theme)

        rendered = canvas.get_at((10, 10))
        self.assertLess(rendered.r, 10)
        self.assertLess(rendered.g, 20)
        self.assertLess(rendered.b, 30)


class TestWindowLowerControlUsesImageButtonBehavior(unittest.TestCase):
    def test_lower_control_lowers_window_on_release(self):
        panel = PanelControl("panel", Rect(0, 0, 800, 600))
        window_a = WindowControl("wa", Rect(40, 40, 220, 140), "A")
        window_b = WindowControl("wb", Rect(70, 70, 220, 140), "B")
        panel.add(window_a)
        panel.add(window_b)
        app = _StubApp()

        lower_rect = window_b.lower_control_rect()
        click_pos = lower_rect.center
        down = GuiEvent(kind=EventType.MOUSE_BUTTON_DOWN, type=0, pos=click_pos, button=1)
        up = GuiEvent(kind=EventType.MOUSE_BUTTON_UP, type=0, pos=click_pos, button=1)

        self.assertTrue(panel.on_event_capture(down, app))
        # Lowering now follows button behavior, so order should not change until release.
        self.assertIs(panel.children[-1], window_b)

        self.assertTrue(panel.on_event_capture(up, app))
        self.assertIs(panel.children[0], window_b)
        self.assertIs(panel.children[-1], window_a)

    def test_task_panel_occludes_underlying_window_lower_control_hover(self):
        panel = PanelControl("panel", Rect(0, 0, 800, 600))
        window = WindowControl("w", Rect(560, 540, 220, 140), "W")
        task_panel = TaskPanelControl(
            "task",
            Rect(0, 520, 800, 80),
            auto_hide=True,
            hidden_peek_pixels=6,
            animation_step_px=200,
            dock_bottom=True,
        )
        panel.add(window)
        panel.add(task_panel)
        app = _StubApp()

        # Raise the autohide panel to ensure it overlays the window title area.
        task_panel.set_focus_mode(True)
        task_panel.update(0.0)

        lower_rect = window.lower_control_rect()
        hover_pos = lower_rect.center
        self.assertTrue(task_panel.rect.collidepoint(hover_pos))

        move = GuiEvent(
            kind=EventType.MOUSE_MOTION,
            type=0,
            pos=hover_pos,
            rel=(0, 0),
            raw_rel=(0, 0),
        )

        consumed = panel.on_event_capture(move, app)
        self.assertTrue(consumed)
        self.assertFalse(window._lower_control_button.hovered)

    def test_task_panel_occludes_underlying_window_titlebar_drag_start(self):
        panel = PanelControl("panel", Rect(0, 0, 800, 600))
        window = WindowControl("w", Rect(560, 540, 220, 140), "W")
        task_panel = TaskPanelControl(
            "task",
            Rect(0, 520, 800, 80),
            auto_hide=True,
            hidden_peek_pixels=6,
            animation_step_px=200,
            dock_bottom=True,
        )
        panel.add(window)
        panel.add(task_panel)
        app = _StubApp()

        task_panel.set_focus_mode(True)
        task_panel.update(0.0)

        title_pos = window.title_bar_rect().center
        self.assertTrue(task_panel.rect.collidepoint(title_pos))

        down = GuiEvent(kind=EventType.MOUSE_BUTTON_DOWN, type=0, pos=title_pos, button=1)
        consumed = panel.on_event_capture(down, app)

        self.assertTrue(consumed)
        self.assertIsNone(panel._drag_window)
        self.assertFalse(app.pointer_capture.is_active)

    def test_task_panel_occludes_underlying_window_lower_control_hover_in_target_phase(self):
        panel = PanelControl("panel", Rect(0, 0, 800, 600))
        window = WindowControl("w", Rect(560, 540, 220, 140), "W")
        task_panel = TaskPanelControl(
            "task",
            Rect(0, 520, 800, 80),
            auto_hide=True,
            hidden_peek_pixels=6,
            animation_step_px=200,
            dock_bottom=True,
        )
        panel.add(window)
        panel.add(task_panel)
        app = _StubApp()

        task_panel.set_focus_mode(True)
        task_panel.update(0.0)

        hover_pos = window.lower_control_rect().center
        self.assertTrue(task_panel.rect.collidepoint(hover_pos))

        move = GuiEvent(
            kind=EventType.MOUSE_MOTION,
            type=0,
            pos=hover_pos,
            rel=(0, 0),
            raw_rel=(0, 0),
        )

        consumed = panel.handle_event(move, app)
        self.assertTrue(consumed)
        self.assertFalse(window._lower_control_button.hovered)

    def test_stale_lower_control_hover_cleared_when_panel_raises_over_stationary_pointer(self):
        panel = PanelControl("panel", Rect(0, 0, 800, 600))
        window = WindowControl("w", Rect(560, 540, 220, 140), "W")
        task_panel = TaskPanelControl(
            "task",
            Rect(0, 520, 800, 80),
            auto_hide=True,
            hidden_peek_pixels=6,
            animation_step_px=200,
            dock_bottom=True,
        )
        panel.add(window)
        panel.add(task_panel)
        app = _StubApp()

        hover_pos = window.lower_control_rect().center
        window._lower_control_button.hovered = True

        task_panel.set_focus_mode(True)
        task_panel.update(0.0)
        self.assertTrue(task_panel.rect.collidepoint(hover_pos))
        app.logical_pointer_pos = hover_pos

        self.assertTrue(panel._clear_occluded_window_hovers_for_pointer(app.logical_pointer_pos))
        self.assertFalse(window._lower_control_button.hovered)

    def test_lowered_autohide_task_panel_does_not_consume_pointer_outside_current_rect(self):
        panel = PanelControl("panel", Rect(0, 0, 800, 600))
        window = WindowControl("w", Rect(560, 500, 220, 140), "W")
        task_panel = TaskPanelControl(
            "task",
            Rect(0, 520, 800, 80),
            auto_hide=True,
            hidden_peek_pixels=6,
            animation_step_px=8,
            dock_bottom=True,
        )
        panel.add(window)
        panel.add(task_panel)
        app = _StubApp()

        task_panel.set_focus_mode(False)
        task_panel.update(0.0)

        # Point in the would-be raised area but above the current lowered rect.
        travel_band_point = (window.lower_control_rect().centerx, int(task_panel._shown_y + 4))
        parent_rect = Rect(panel.rect)
        self.assertTrue(parent_rect.collidepoint(travel_band_point))
        self.assertFalse(task_panel.rect.collidepoint(travel_band_point))

        move = GuiEvent(
            kind=EventType.MOUSE_MOTION,
            type=0,
            pos=travel_band_point,
            rel=(0, 0),
            raw_rel=(0, 0),
        )

        consumed = panel.on_event_capture(move, app)
        self.assertTrue(consumed)
        self.assertFalse(move.default_prevented)
        self.assertFalse(move.propagation_stopped)
