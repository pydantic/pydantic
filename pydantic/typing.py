# flake8: noqa
from typing import Any

from ._internal import typing_extra


def __getattr__(name: str) -> Any:
    return getattr(typing_extra, name)
