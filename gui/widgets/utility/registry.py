from typing import Callable, Any, Dict

_Registry: Dict[str, Callable[..., Any]] = {}

def register_widget(name: str) -> Callable:
    def decorator(cls: type) -> type:
        _Registry[name] = cls
        return cls
    return decorator

def create_widget(name: str, *args: Any, **kwargs: Any) -> Any:
    return _Registry[name](*args, **kwargs)
