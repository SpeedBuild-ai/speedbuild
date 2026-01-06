import os

def get_activated_venv():
    """Returns the path of the currently activated virtual environment, or None if none is activated."""
    return os.environ.get("VIRTUAL_ENV")