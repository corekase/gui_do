from typing import TYPE_CHECKING, Optional, Tuple, Any, Callable, Union
from pygame import Rect

if TYPE_CHECKING:
    from ..widgets.window import Window
    from ..widgets.button import Button
    from ..widgets.label import Label
    from ..widgets.canvas import Canvas
    from ..widgets.image import Image
    from ..widgets.scrollbar import Scrollbar
    from ..widgets.toggle import Toggle
    from ..widgets.arrowbox import ArrowBox
    from ..widgets.buttongroup import ButtonGroup
    from ..widgets.frame import Frame

# having just the widget constructors in a class is for IDE intellisense.  only what is here will be in autocomplete.
class Widget_Collection:
    def __init__(self, gui):
        self._gui = gui

    def window(self, title: str, pos: Tuple[int, int], size: Tuple[int, int], backdrop: Optional[str] = None) -> "Window":
        from ..widgets.window import Window
        return self._gui.add(Window(self._gui, title, pos, size, backdrop))

    def button(self, id: Any, rect: Any, style: Any, text: Optional[str], button_callback: Optional[Callable] = None, skip_factory: bool = False) -> "Button":
        from ..widgets.button import Button
        return self._gui.add(Button(self._gui, id, rect, style, text, button_callback, skip_factory))

    def label(self, position: Union[Tuple[int, int], Tuple[int, int, int, int]], text: str, shadow: bool = False) -> "Label":
        from ..widgets.label import Label
        return self._gui.add(Label(self._gui, position, text, shadow))

    def canvas(self, id: Any, rect: Rect, backdrop: Optional[str] = None, canvas_callback: Optional[Any] = None, automatic_pristine: bool = False) -> "Canvas":
        from ..widgets.canvas import Canvas
        return self._gui.add(Canvas(self._gui, id, rect, backdrop, canvas_callback, automatic_pristine))

    def image(self, id: Any, rect: Any, image: str, automatic_pristine: bool = False, scale: bool = True) -> "Image":
        from ..widgets.image import Image
        return self._gui.add(Image(self._gui, id, rect, image, automatic_pristine, scale))

    def scrollbar(self, id: Any, overall_rect: Rect, horizontal: Any, style: Any, params: Tuple[int, int, int, int]) -> "Scrollbar":
        from ..widgets.scrollbar import Scrollbar
        return self._gui.add(Scrollbar(self._gui, id, overall_rect, horizontal, style, params))

    def toggle(self, id: Any, rect: Any, style: Any, pushed: bool, pressed_text: str, raised_text: Optional[str] = None) -> "Toggle":
        from ..widgets.toggle import Toggle
        return self._gui.add(Toggle(self._gui, id, rect, style, pushed, pressed_text, raised_text))

    def arrowbox(self, id: Any, rect: Any, direction: float, callback: Optional[Callable] = None) -> "ArrowBox":
        from ..widgets.arrowbox import ArrowBox
        return self._gui.add(ArrowBox(self._gui, id, rect, direction, callback))

    def buttongroup(self, group: str, id: Any, rect: Any, style: Any, text: str) -> "ButtonGroup":
        from ..widgets.buttongroup import ButtonGroup
        return self._gui.add(ButtonGroup(self._gui, group, id, rect, style, text))

    def frame(self, id: Any, rect: Any) -> "Frame":
        from ..widgets.frame import Frame
        return self._gui.add(Frame(self._gui, id, rect))
