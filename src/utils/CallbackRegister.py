class CallbackRegistry:
    """Registry for managing GUI event callbacks in a decoupled way."""

    def __init__(self):
        self.callbacks = {}

    def register(self, event_name: str, callback):
        """Register a callback for a specific event."""
        self.callbacks[event_name] = callback

    def trigger(self, event_name, *args, **kwargs):
        """Trigger a callback for a specific event."""
        if event_name in self.callbacks:
            self.callbacks[event_name](*args, **kwargs)
        else:
            print(f"Колбэк для события '{event_name}' не зарегистрирован")