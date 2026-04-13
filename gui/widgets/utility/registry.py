_Registry = {}

def register_widget(name):
    def decorator(cls):
        _Registry[name] = cls
        return cls
    return decorator

def create_widget(name, *args, **kwargs):
    return _Registry[name](*args, **kwargs)
