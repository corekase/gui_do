# all the widgets are imported so that their decorators are initialized
def _init_decorations() -> None:
    from ..widgets.window import Window
    from ..widgets.button import Button
    from ..widgets.arrowbox import ArrowBox
    from ..widgets.buttongroup import ButtonGroup
    from ..widgets.canvas import Canvas
    from ..widgets.frame import Frame
    from ..widgets.image import Image
    from ..widgets.label import Label
    from ..widgets.scrollbar import Scrollbar
    from ..widgets.toggle import Toggle
