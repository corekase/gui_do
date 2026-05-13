"""LayoutRegistry — extensible registry for layout handlers."""
from typing import Dict, Type

class LayoutRegistry:
    """Registry for named layout handler classes."""
    _registry: Dict[str, Type] = {}

    @classmethod
    def register(cls, name: str, handler: Type) -> None:
        cls._registry[name] = handler

    @classmethod
    def get(cls, name: str) -> Type:
        return cls._registry[name]

    @classmethod
    def all(cls) -> Dict[str, Type]:
        return dict(cls._registry)

# Example usage:
# LayoutRegistry.register('flex', FlexLayout)
# LayoutRegistry.get('flex')
