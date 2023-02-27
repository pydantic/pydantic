def __getattr__(name: str) -> None:
    from .import_helper import getattr

    return getattr(__name__, name)
