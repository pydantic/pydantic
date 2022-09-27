from __future__ import annotations as _annotations

from typing import Any


class PydanticMetadata:
    """
    Base class for annotation markers like `Strict`.
    """

    __slots__ = ()


class CustomMetadata(PydanticMetadata):
    def __init__(self, **metadata: Any):
        self.__dict__ = metadata
