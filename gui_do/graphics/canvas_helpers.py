"""
Generalized canvas and color table helpers for graphics features.
User code should only specify color table intent; caching and mapping is automatic.
"""
from typing import Dict, Tuple

class CanvasColorTableCache:
    def __init__(self):
        self._cache: Dict[int, Tuple[int, ...]] = {}
    def get(self, key: int, generator) -> Tuple[int, ...]:
        if key not in self._cache:
            self._cache[key] = generator()
        return self._cache[key]

class CanvasPixelMapper:
    @staticmethod
    def map_pixels(canvas, color_table: Tuple[int, ...]):
        # Example: apply color table to canvas pixels
        # User code only provides color table, not mapping logic
        for y in range(canvas.height):
            for x in range(canvas.width):
                idx = canvas.get_pixel_index(x, y)
                canvas.set_pixel_color(x, y, color_table[idx % len(color_table)])
