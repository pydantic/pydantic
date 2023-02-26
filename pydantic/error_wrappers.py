from .import_helper import getattr


def __getattr__(name: str) -> None:
    return getattr(__name__, name)
