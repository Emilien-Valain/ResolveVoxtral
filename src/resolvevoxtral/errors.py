"""Exception hierarchy shared across the app.

Every module below the GUI layer raises one of these with a plain-language
``user_message`` already attached, so ``gui.py``/``app.py`` never need to
interpret a raw exception to decide what to show the user.
"""


class ResolveVoxtralError(Exception):
    def __init__(self, user_message, *, cause=None):
        super().__init__(user_message)
        self.user_message = user_message
        self.cause = cause


class ConfigError(ResolveVoxtralError):
    pass


class ResolveEnvironmentError(ResolveVoxtralError):
    pass


class RenderError(ResolveVoxtralError):
    pass


class TranscriptionError(ResolveVoxtralError):
    pass
