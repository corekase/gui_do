from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter
from typing import Callable, Dict, Optional


@dataclass
class FirstFrameSample:
    category: str
    key: str
    elapsed_ms: float
    detail: str


class FirstFrameProfiler:
    """Collect one-time first-open hotspot timings with lightweight logging."""

    def __init__(
        self,
        *,
        enabled: bool = False,
        min_ms: float = 0.25,
        logger: Optional[Callable[[str], None]] = None,
    ) -> None:
        self.enabled = bool(enabled)
        self.min_ms = max(0.0, float(min_ms))
        self._logger = logger
        self._scene_frame_counts: Dict[str, int] = {}
        self._once_seen: set[tuple[str, str]] = set()

    def configure(
        self,
        *,
        enabled: Optional[bool] = None,
        min_ms: Optional[float] = None,
        logger: Optional[Callable[[str], None]] = None,
    ) -> None:
        if enabled is not None:
            self.enabled = bool(enabled)
        if min_ms is not None:
            self.min_ms = max(0.0, float(min_ms))
        if logger is not None:
            self._logger = logger

    def begin_frame(self, scene_name: str) -> int:
        scene_key = str(scene_name)
        next_frame = int(self._scene_frame_counts.get(scene_key, 0)) + 1
        self._scene_frame_counts[scene_key] = next_frame
        return next_frame

    def scene_frame_count(self, scene_name: str) -> int:
        return int(self._scene_frame_counts.get(str(scene_name), 0))

    def profile_first_frame(self, scene_name: str) -> bool:
        return self.scene_frame_count(scene_name) <= 1

    def record_once(self, category: str, key: str, elapsed_ms: float, detail: str = "") -> None:
        if not self.enabled:
            return
        elapsed = float(elapsed_ms)
        if elapsed < self.min_ms:
            return
        identity = (str(category), str(key))
        if identity in self._once_seen:
            return
        self._once_seen.add(identity)
        self._emit(FirstFrameSample(category=str(category), key=str(key), elapsed_ms=elapsed, detail=str(detail)))

    def time_once(self, category: str, key: str, detail: str = ""):
        start = perf_counter()

        def _finish() -> float:
            elapsed_ms = (perf_counter() - start) * 1000.0
            self.record_once(category, key, elapsed_ms, detail)
            return elapsed_ms

        return _finish

    def _emit(self, sample: FirstFrameSample) -> None:
        message = (
            f"[gui_do][first-open] {sample.category}:{sample.key} "
            f"{sample.elapsed_ms:.3f} ms"
        )
        if sample.detail:
            message += f" | {sample.detail}"
        if self._logger is not None:
            self._logger(message)
            return
        print(message)


_GLOBAL_PROFILER = FirstFrameProfiler(enabled=False)


def first_frame_profiler() -> FirstFrameProfiler:
    return _GLOBAL_PROFILER
