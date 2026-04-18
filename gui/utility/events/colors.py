from types import MappingProxyType

colours = MappingProxyType({
    'full': (255, 255, 255),
    'light': (0, 200, 200),
    'medium': (0, 150, 150),
    'dark': (0, 100, 100),
    'none': (0, 0, 0),
    'text': (255, 255, 255),
    'highlight': (238, 230, 0),
    'background': (0, 60, 60),
})
