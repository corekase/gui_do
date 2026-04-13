_WIDGET_REGISTRY = {}

def register_widget(name):
    def decorator(cls):
        _WIDGET_REGISTRY[name] = cls
        return cls
    return decorator

def create_widget(name, *args, **kwargs):
    return _WIDGET_REGISTRY[name](*args, **kwargs)
