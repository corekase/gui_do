"""Mandelbrot feature part extracted from the gui_do demo entrypoint."""

from __future__ import annotations

import pygame
from typing import Optional, Tuple

from pygame import Rect

from .mandel_events import (
    MANDEL_KIND_CLEARED,
    MANDEL_KIND_COMPLETE,
    MANDEL_KIND_FAILED,
    MANDEL_KIND_RUNNING_FOUR_SPLIT,
    MANDEL_KIND_RUNNING_ITERATIVE,
    MANDEL_KIND_RUNNING_ONE_SPLIT,
    MANDEL_KIND_RUNNING_RECURSIVE,
    MANDEL_KIND_STATUS,
    MandelStatusEvent,
)


class MandelbrotRenderFeature:
    """Build and run the Mandelbrot demo windows, tasks, and status plumbing."""

    name = "mandelbrot"

    def build(self, demo) -> None:
        self.build_window(
            demo,
            window_control_cls=demo._window_control_cls,
            label_control_cls=demo._label_control_cls,
            canvas_control_cls=demo._canvas_control_cls,
            button_control_cls=demo._button_control_cls,
        )

    def bind_runtime(self, demo) -> None:
        demo.mandel_scheduler.set_message_dispatch_limit(256)
        demo.app.actions.register_action("mandel_failure_preview_decrease", lambda _event: demo._adjust_mandel_failure_preview_limit(-1))
        demo.app.actions.register_action("mandel_failure_preview_increase", lambda _event: demo._adjust_mandel_failure_preview_limit(1))
        demo.app.actions.bind_key(pygame.K_LEFTBRACKET, "mandel_failure_preview_decrease", scene="main")
        demo.app.actions.bind_key(pygame.K_RIGHTBRACKET, "mandel_failure_preview_increase", scene="main")
        demo.mandel_model.bind(demo.mandel_model.status_text, demo._on_mandel_status_changed)
        demo._mandel_status_subscription = demo.app.events.subscribe(
            demo._mandel_status_topic,
            demo._on_mandel_status_event,
            scope=demo._mandel_status_scope,
        )
        demo._mandel_status_bus_ready = True

    def configure_accessibility(self, demo, tab_index_start: int) -> int:
        controls = [
            demo.mandel_reset_button,
            demo.mandel_iter_button,
            demo.mandel_recur_button,
            demo.mandel_one_split_button,
            demo.mandel_four_split_button,
        ]
        labels = [
            "Clear Mandelbrot surfaces",
            "Run Mandelbrot iterative",
            "Run Mandelbrot recursive",
            "Run Mandelbrot one canvas split",
            "Run Mandelbrot four canvases split",
        ]
        next_index = int(tab_index_start)
        for control, label in zip(controls, labels):
            control.set_tab_index(next_index)
            control.set_accessibility(role="button", label=label)
            next_index += 1
        return next_index

    def on_post_frame(self, demo) -> None:
        self.update_events(demo)

    @staticmethod
    def format_help_text(demo) -> str:
        limit = int(getattr(demo, "_mandel_failure_preview_limit", 3))
        return f"Modes: Iterative, Recursive, 1M 4Tasks, 4M 4Tasks | Failure preview [ ]: {limit}"

    @staticmethod
    def set_help_label(demo) -> None:
        if hasattr(demo, "mandel_help") and demo.mandel_help is not None:
            demo.mandel_help.text = MandelbrotDemoPart.format_help_text(demo)

    @staticmethod
    def set_failure_preview_limit(demo, limit: int) -> int:
        clamped = max(demo._MANDEL_FAILURE_PREVIEW_MIN, min(demo._MANDEL_FAILURE_PREVIEW_MAX, int(limit)))
        demo._mandel_failure_preview_limit = clamped
        MandelbrotDemoPart.set_help_label(demo)
        return clamped

    @staticmethod
    def adjust_failure_preview_limit(demo, delta: int) -> bool:
        previous = demo._mandel_failure_preview_limit
        effective = MandelbrotDemoPart.set_failure_preview_limit(demo, previous + int(delta))
        detail = f"Mandelbrot failure preview limit: {effective}"
        if effective == previous:
            detail = f"{detail} (at bound)"
        demo._publish_mandel_event(MANDEL_KIND_STATUS, detail)
        return True

    @staticmethod
    def build_window(
        demo,
        *,
        window_control_cls,
        label_control_cls,
        canvas_control_cls,
        button_control_cls,
    ) -> None:
        mandel_rect = demo.app.layout.anchored((640, 724), anchor="top_right", margin=(28, 92), use_rect=True)
        demo.mandel_window = demo.root.add(
            window_control_cls(
                "mandel_window",
                mandel_rect,
                "Mandelbrot",
                event_handler=demo._mandel_window_event_handler,
            )
        )
        left = mandel_rect.left
        top = mandel_rect.top
        canvas_size = 580
        canvas_x = left + 20
        canvas_y = top + 54
        split_gap = 6
        split_size = (canvas_size - split_gap) // 2
        controls_y = canvas_y + canvas_size + 12
        status_y = controls_y + 38

        demo.mandel_help = demo._set_text(
            demo.mandel_window.add(
                label_control_cls(
                    "mandel_help",
                    Rect(left + 20, top + 30, 590, 20),
                    MandelbrotDemoPart.format_help_text(demo),
                )
            )
        )
        demo.mandel_canvas = demo.mandel_window.add(canvas_control_cls("mandel_canvas", Rect(canvas_x, canvas_y, canvas_size, canvas_size), max_events=128))
        demo.mandel_canvas_rect = Rect(canvas_x, canvas_y, canvas_size, canvas_size)
        demo.canvas1 = demo.mandel_window.add(canvas_control_cls("can1", Rect(canvas_x, canvas_y, split_size, split_size), max_events=32))
        demo.canvas2 = demo.mandel_window.add(canvas_control_cls("can2", Rect(canvas_x + split_size + split_gap, canvas_y, split_size, split_size), max_events=32))
        demo.canvas3 = demo.mandel_window.add(canvas_control_cls("can3", Rect(canvas_x, canvas_y + split_size + split_gap, split_size, split_size), max_events=32))
        demo.canvas4 = demo.mandel_window.add(
            canvas_control_cls("can4", Rect(canvas_x + split_size + split_gap, canvas_y + split_size + split_gap, split_size, split_size), max_events=32)
        )

        demo.app.layout.set_linear_properties(
            anchor=(left + 20, controls_y),
            item_width=112,
            item_height=30,
            spacing=8,
            horizontal=True,
        )
        mandel_reset_rect = demo.app.layout.next_linear()
        mandel_iter_rect = demo.app.layout.next_linear()
        mandel_recur_rect = demo.app.layout.next_linear()
        mandel_one_split_rect = demo.app.layout.next_linear()
        mandel_four_split_rect = demo.app.layout.next_linear()

        demo.mandel_reset_button = demo.mandel_window.add(
            button_control_cls("mandel_reset", mandel_reset_rect, "Reset", demo._clear_mandel, style="angle")
        )
        demo.mandel_iter_button = demo.mandel_window.add(
            button_control_cls("mandel_iter", mandel_iter_rect, "Iterative", demo._launch_mandel_iterative, style="round")
        )
        demo.mandel_recur_button = demo.mandel_window.add(
            button_control_cls("mandel_recur", mandel_recur_rect, "Recursive", demo._launch_mandel_recursive, style="round")
        )
        demo.mandel_one_split_button = demo.mandel_window.add(
            button_control_cls("mandel_one_split", mandel_one_split_rect, "1M 4Tasks", demo._launch_mandel_one_split, style="round")
        )
        demo.mandel_four_split_button = demo.mandel_window.add(
            button_control_cls("mandel_four_split", mandel_four_split_rect, "4M 4Tasks", demo._launch_mandel_four_split, style="round")
        )
        demo.mandel_task_buttons = (
            demo.mandel_iter_button,
            demo.mandel_recur_button,
            demo.mandel_one_split_button,
            demo.mandel_four_split_button,
        )

        demo.mandel_status = demo._set_text(
            demo.mandel_window.add(
                label_control_cls("mandel_status", Rect(left + 20, status_y, 590, 20), demo.mandel_model.status_text.value)
            )
        )

        demo.canvas1.visible = False
        demo.canvas2.visible = False
        demo.canvas3.visible = False
        demo.canvas4.visible = False
        MandelbrotDemoPart.set_task_buttons_disabled(demo, False)
        MandelbrotDemoPart.clear(demo)
        demo.mandel_window.visible = False

    @staticmethod
    def on_status_changed(demo, text: str) -> None:
        demo.mandel_status.text = text

    @staticmethod
    def on_status_event(demo, payload) -> None:
        demo.mandel_model.set_status(MandelbrotDemoPart.format_status(demo, MandelStatusEvent.from_payload(payload)))

    @staticmethod
    def format_status(_demo, payload) -> str:
        event = MandelStatusEvent.from_payload(payload)
        details = "" if event.detail is None else str(event.detail)
        mapping = {
            "idle": "Mandelbrot: idle",
            MANDEL_KIND_CLEARED: "Mandelbrot: cleared",
            MANDEL_KIND_RUNNING_ITERATIVE: "Mandelbrot: running iterative",
            MANDEL_KIND_RUNNING_RECURSIVE: "Mandelbrot: running recursive",
            MANDEL_KIND_RUNNING_ONE_SPLIT: "Mandelbrot: running 1M 4Tasks",
            MANDEL_KIND_RUNNING_FOUR_SPLIT: "Mandelbrot: running 4M 4Tasks",
            MANDEL_KIND_COMPLETE: "Mandelbrot: complete",
        }
        if event.kind in mapping:
            return mapping[event.kind]
        if event.kind == MANDEL_KIND_FAILED:
            return f"Mandelbrot failed: {details}" if details else "Mandelbrot failed"
        if event.kind == MANDEL_KIND_STATUS:
            return details if details else "Mandelbrot: idle"
        return details if details else f"Mandelbrot: {event.kind}"

    @staticmethod
    def publish_event(demo, kind: str, detail: Optional[str] = None) -> None:
        if kind in (MANDEL_KIND_CLEARED, MANDEL_KIND_COMPLETE, MANDEL_KIND_FAILED):
            demo._mandel_running_mode = None
        event = MandelStatusEvent(kind=str(kind), detail=None if detail is None else str(detail))
        payload = event.to_payload()
        if getattr(demo, "_mandel_status_bus_ready", False):
            demo.app.events.publish(demo._mandel_status_topic, payload, scope=demo._mandel_status_scope)
            return
        demo.mandel_model.set_status(MandelbrotDemoPart.format_status(demo, event))

    @staticmethod
    def publish_running_status(demo) -> None:
        if not demo.mandel_task_ids:
            return
        mode = demo._mandel_running_mode if demo._mandel_running_mode is not None else "running"
        task_count = len(demo.mandel_task_ids)
        task_word = "task" if task_count == 1 else "tasks"
        detail = f"Mandelbrot: {mode} ({task_count} {task_word})"
        if demo.mandel_model.status_text.value == detail:
            return
        demo._publish_mandel_event(MANDEL_KIND_STATUS, detail)

    @staticmethod
    def format_failure_summary(demo, failed_details) -> str:
        if not failed_details:
            return ""
        if len(failed_details) == 1:
            task_id, error = failed_details[0]
            return f"{task_id}: {error}"

        configured = int(getattr(demo, "_mandel_failure_preview_limit", 3))
        limit = max(demo._MANDEL_FAILURE_PREVIEW_MIN, min(demo._MANDEL_FAILURE_PREVIEW_MAX, configured))
        preview = failed_details[:limit]
        summary = "; ".join(f"{task_id}: {error}" for task_id, error in preview)
        remaining = len(failed_details) - len(preview)
        if remaining > 0:
            summary = f"{summary}; +{remaining} more"
        return f"{len(failed_details)} tasks failed - {summary}"

    @staticmethod
    def window_event_handler(_demo, event) -> bool:
        return False

    @staticmethod
    def mandel_col(demo, k: int) -> Tuple[int, int, int]:
        if k >= demo.max_iter - 1:
            return (0, 0, 0)
        return demo.mandel_cols[k % len(demo.mandel_cols)]

    @staticmethod
    def mandel_viewport(_demo, width: int, height: int) -> Tuple[complex, float]:
        center = -0.7 + 0.0j
        extent = 2.5 + 2.5j
        scale = max((extent / width).real, (extent / height).imag)
        return center, scale

    @staticmethod
    def mandel_pixel(demo, px: int, py: int, width: int, height: int, center: complex, scale: float) -> int:
        c = center + (px - width // 2 + (py - height // 2) * 1j) * scale
        z = 0j
        for k in range(demo.max_iter):
            z = z * z + c
            if (z * z.conjugate()).real > 4.0:
                return k
        return demo.max_iter - 1

    @staticmethod
    def clear_surfaces(demo) -> None:
        demo.mandel_canvas.canvas.fill(demo.app.theme.medium)
        demo.canvas1.canvas.fill(demo.app.theme.medium)
        demo.canvas2.canvas.fill(demo.app.theme.medium)
        demo.canvas3.canvas.fill(demo.app.theme.medium)
        demo.canvas4.canvas.fill(demo.app.theme.medium)

    @staticmethod
    def set_task_buttons_disabled(demo, disabled: bool) -> None:
        buttons = getattr(demo, "mandel_task_buttons", ())
        for button in buttons:
            button.enabled = not disabled
        if not disabled:
            return
        if not buttons:
            return
        focused = demo.app.focus.focused_node
        if focused not in buttons:
            return
        if demo.mandel_reset_button.visible and demo.mandel_reset_button.enabled and demo.mandel_reset_button.accepts_focus():
            demo.app.focus.set_focus(demo.mandel_reset_button, show_hint=False)
            return
        demo.app.focus.revalidate_focus(demo.app.scene)

    @staticmethod
    def show_single_canvas(demo) -> None:
        demo.mandel_canvas.visible = True
        demo.canvas1.visible = False
        demo.canvas2.visible = False
        demo.canvas3.visible = False
        demo.canvas4.visible = False
        MandelbrotDemoPart.clear_surfaces(demo)

    @staticmethod
    def prepare_single_canvas_run(demo) -> None:
        MandelbrotDemoPart.set_task_buttons_disabled(demo, True)
        MandelbrotDemoPart.show_single_canvas(demo)

    @staticmethod
    def prepare_split_canvas_run(demo) -> None:
        MandelbrotDemoPart.set_task_buttons_disabled(demo, True)
        demo.mandel_canvas.visible = False
        demo.canvas1.visible = True
        demo.canvas2.visible = True
        demo.canvas3.visible = True
        demo.canvas4.visible = True
        MandelbrotDemoPart.clear_surfaces(demo)

    @staticmethod
    def canvas_for_task(demo, task_id: str):
        canvas_by_task = {
            "iter": demo.mandel_canvas.canvas,
            "recu": demo.mandel_canvas.canvas,
            "1": demo.mandel_canvas.canvas,
            "2": demo.mandel_canvas.canvas,
            "3": demo.mandel_canvas.canvas,
            "4": demo.mandel_canvas.canvas,
            "can1": demo.canvas1.canvas,
            "can2": demo.canvas2.canvas,
            "can3": demo.canvas3.canvas,
            "can4": demo.canvas4.canvas,
        }
        return canvas_by_task.get(task_id)

    @staticmethod
    def make_progress_handler(demo, task_id: str):
        def handler(payload):
            MandelbrotDemoPart.apply_result(demo, task_id, payload)

        return handler

    @staticmethod
    def apply_result(demo, task_id: str, payload) -> None:
        canvas = MandelbrotDemoPart.canvas_for_task(demo, task_id)
        if canvas is None:
            return

        if task_id == "iter":
            y_pos, row = payload
            if y_pos < 0 or y_pos >= canvas.get_height():
                return
            for x_pos, value in enumerate(row):
                if 0 <= x_pos < canvas.get_width():
                    canvas.set_at((x_pos, y_pos), MandelbrotDemoPart.mandel_col(demo, value))
            return

        x_pos, y_pos, width, height, values = payload
        x0 = max(0, x_pos)
        y0 = max(0, y_pos)
        x1 = min(canvas.get_width(), x_pos + width)
        y1 = min(canvas.get_height(), y_pos + height)
        if x1 <= x0 or y1 <= y0:
            return

        if isinstance(values, int):
            canvas.fill(MandelbrotDemoPart.mandel_col(demo, values), Rect(x0, y0, x1 - x0, y1 - y0))
            return

        src_w = max(1, width)
        if (x0, y0, x1, y1) != (x_pos, y_pos, x_pos + width, y_pos + height):
            clipped_values = []
            for row_index in range(y0 - y_pos, y1 - y_pos):
                start = row_index * src_w + (x0 - x_pos)
                end = start + (x1 - x0)
                clipped_values.extend(values[start:end])
            values = clipped_values
            x_pos, y_pos, width, height = x0, y0, x1 - x0, y1 - y0

        idx = 0
        for yy in range(y_pos, y_pos + height):
            for xx in range(x_pos, x_pos + width):
                canvas.set_at((xx, yy), MandelbrotDemoPart.mandel_col(demo, values[idx]))
                idx += 1

    @staticmethod
    def clear(demo) -> None:
        demo.mandel_scheduler.remove_tasks(*demo.mandel_task_id_pool)
        demo.mandel_task_ids.clear()
        demo._mandel_running_mode = None
        MandelbrotDemoPart.show_single_canvas(demo)
        MandelbrotDemoPart.set_task_buttons_disabled(demo, False)
        MandelbrotDemoPart.publish_event(demo, MANDEL_KIND_CLEARED)

    @staticmethod
    def iterative_task(demo, task_id, params):
        width, height = params["size"]
        center = params["center"]
        scale = params["scale"]
        for y in range(height):
            row = [MandelbrotDemoPart.mandel_pixel(demo, x, y, width, height, center, scale) for x in range(width)]
            demo.mandel_scheduler.send_message(task_id, (y, row))
        return None

    @staticmethod
    def recursive_fill(demo, task_id: str, x: int, y: int, w: int, h: int, width: int, height: int, center: complex, scale: float) -> None:
        if w <= 0 or h <= 0:
            return
        tl = MandelbrotDemoPart.mandel_pixel(demo, x, y, width, height, center, scale)
        tr = MandelbrotDemoPart.mandel_pixel(demo, x + w - 1, y, width, height, center, scale)
        bl = MandelbrotDemoPart.mandel_pixel(demo, x, y + h - 1, width, height, center, scale)
        br = MandelbrotDemoPart.mandel_pixel(demo, x + w - 1, y + h - 1, width, height, center, scale)
        if w <= 4 or h <= 4:
            values = []
            for yy in range(y, y + h):
                for xx in range(x, x + w):
                    values.append(MandelbrotDemoPart.mandel_pixel(demo, xx, yy, width, height, center, scale))
            demo.mandel_scheduler.send_message(task_id, (x, y, w, h, values))
            return
        if tl == tr == bl == br:
            demo.mandel_scheduler.send_message(task_id, (x, y, w, h, tl))
            return
        hw = w // 2
        hh = h // 2
        MandelbrotDemoPart.recursive_fill(demo, task_id, x, y, hw, hh, width, height, center, scale)
        MandelbrotDemoPart.recursive_fill(demo, task_id, x + hw, y, w - hw, hh, width, height, center, scale)
        MandelbrotDemoPart.recursive_fill(demo, task_id, x, y + hh, hw, h - hh, width, height, center, scale)
        MandelbrotDemoPart.recursive_fill(demo, task_id, x + hw, y + hh, w - hw, h - hh, width, height, center, scale)

    @staticmethod
    def recursive_task(demo, task_id, params):
        width, height = params["size"]
        center = params["center"]
        scale = params["scale"]
        rect = Rect(params.get("rect", Rect(0, 0, width, height)))
        MandelbrotDemoPart.recursive_fill(demo, task_id, rect.x, rect.y, rect.width, rect.height, width, height, center, scale)
        return None

    @staticmethod
    def queue_recursive_task(demo, task_id: str, rect: Rect, size: Tuple[int, int], center: complex, scale: float) -> None:
        demo.mandel_scheduler.add_task(
            task_id,
            demo._mandel_recursive_task,
            parameters={"size": size, "center": center, "scale": scale, "rect": Rect(rect)},
            message_method=demo._make_mandel_progress_handler(task_id),
        )
        demo.mandel_task_ids.add(task_id)

    @staticmethod
    def launch_iterative(demo) -> None:
        if demo.mandel_scheduler.tasks_busy_match_any(*demo.mandel_task_id_pool):
            return
        MandelbrotDemoPart.prepare_single_canvas_run(demo)
        width, height = demo.mandel_canvas.canvas.get_size()
        center, scale = MandelbrotDemoPart.mandel_viewport(demo, width, height)
        demo.mandel_scheduler.add_task(
            "iter",
            demo._mandel_iterative_task,
            parameters={"size": (width, height), "center": center, "scale": scale},
            message_method=demo._make_mandel_progress_handler("iter"),
        )
        demo.mandel_task_ids.add("iter")
        demo._mandel_running_mode = "running iterative"
        MandelbrotDemoPart.publish_event(demo, MANDEL_KIND_RUNNING_ITERATIVE)
        MandelbrotDemoPart.publish_running_status(demo)

    @staticmethod
    def launch_recursive(demo) -> None:
        if demo.mandel_scheduler.tasks_busy_match_any(*demo.mandel_task_id_pool):
            return
        MandelbrotDemoPart.prepare_single_canvas_run(demo)
        width, height = demo.mandel_canvas.canvas.get_size()
        center, scale = MandelbrotDemoPart.mandel_viewport(demo, width, height)
        MandelbrotDemoPart.queue_recursive_task(demo, "recu", Rect(0, 0, width, height), (width, height), center, scale)
        demo._mandel_running_mode = "running recursive"
        MandelbrotDemoPart.publish_event(demo, MANDEL_KIND_RUNNING_RECURSIVE)
        MandelbrotDemoPart.publish_running_status(demo)

    @staticmethod
    def launch_one_split(demo) -> None:
        if demo.mandel_scheduler.tasks_busy_match_any(*demo.mandel_task_id_pool):
            return
        MandelbrotDemoPart.prepare_single_canvas_run(demo)
        width, height = demo.mandel_canvas.canvas.get_size()
        center, scale = MandelbrotDemoPart.mandel_viewport(demo, width, height)
        left_w, top_h = width // 2, height // 2
        right_w, bottom_h = width - left_w, height - top_h
        MandelbrotDemoPart.queue_recursive_task(demo, "1", Rect(0, 0, left_w, top_h), (width, height), center, scale)
        MandelbrotDemoPart.queue_recursive_task(demo, "2", Rect(left_w, 0, right_w, top_h), (width, height), center, scale)
        MandelbrotDemoPart.queue_recursive_task(demo, "3", Rect(0, top_h, left_w, bottom_h), (width, height), center, scale)
        MandelbrotDemoPart.queue_recursive_task(demo, "4", Rect(left_w, top_h, right_w, bottom_h), (width, height), center, scale)
        demo._mandel_running_mode = "running 1M 4Tasks"
        MandelbrotDemoPart.publish_event(demo, MANDEL_KIND_RUNNING_ONE_SPLIT)
        MandelbrotDemoPart.publish_running_status(demo)

    @staticmethod
    def launch_four_split(demo) -> None:
        if demo.mandel_scheduler.tasks_busy_match_any(*demo.mandel_task_id_pool):
            return
        MandelbrotDemoPart.prepare_split_canvas_run(demo)
        width, height = demo.canvas1.canvas.get_size()
        center, scale = MandelbrotDemoPart.mandel_viewport(demo, width, height)
        for task_id in ("can1", "can2", "can3", "can4"):
            MandelbrotDemoPart.queue_recursive_task(demo, task_id, Rect(0, 0, width, height), (width, height), center, scale)
        demo._mandel_running_mode = "running 4M 4Tasks"
        MandelbrotDemoPart.publish_event(demo, MANDEL_KIND_RUNNING_FOUR_SPLIT)
        MandelbrotDemoPart.publish_running_status(demo)

    @staticmethod
    def update_events(demo) -> None:
        finished = demo.mandel_scheduler.get_finished_events()
        failed = demo.mandel_scheduler.get_failed_events()
        failed_details = []

        for event in finished:
            if event.task_id in demo.mandel_task_ids:
                demo.mandel_task_ids.remove(event.task_id)
                demo.mandel_scheduler.pop_result(event.task_id, None)
        for event in failed:
            if event.task_id in demo.mandel_task_ids:
                demo.mandel_task_ids.remove(event.task_id)
                failed_details.append((str(event.task_id), str(event.error)))

        if failed_details:
            failed_details.sort(key=lambda item: (item[0], item[1]))
            demo._publish_mandel_event(MANDEL_KIND_FAILED, MandelbrotDemoPart.format_failure_summary(demo, failed_details))

        busy = demo.mandel_scheduler.tasks_busy_match_any(*demo.mandel_task_id_pool)
        demo._set_mandel_task_buttons_disabled(busy)
        if busy:
            demo._publish_mandel_running_status()
        demo.mandel_scheduler.clear_events()
        if not busy and demo.mandel_model.status_text.value.startswith("Mandelbrot: running"):
            demo._mandel_running_mode = None
            demo._publish_mandel_event(MANDEL_KIND_COMPLETE)


# Backward-compatible alias retained for in-flight refs/tests during migration.
MandelbrotDemoPart = MandelbrotRenderFeature
