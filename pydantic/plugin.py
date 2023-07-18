"""This module is used to load plugins for pydantic.

Plugins are installed via Python entry points, for example in `pyproject.toml`:

    [tool.poetry.plugins."pydantic"]
    observer = "pydantic_sdk:main"

The entry point group is `pydantic` and the name of the entry point is the name of the plugin.

On Pydantic, plugins are loaded by calling `load_plugins()`. Plugins are loaded in the order
they are found, and the order they are found is not guaranteed.

Consider that you have a plugin called `observer`, then you can use it like this:

    from pydantic import BaseModel

    class Foo(BaseModel, observer='all'):
        ...

On each validation call, a callable registered for the event `all` will be called with the
instance of `Foo`, the event name, and the validation result.
"""
from __future__ import annotations

import functools
import importlib.metadata
from contextlib import AbstractContextManager, ExitStack
from typing import Any, Callable, Final, ParamSpec, TypeVar

from typing_extensions import Self

P = ParamSpec('P')
R = TypeVar('R')


class PluginManager:
    """Plugin manager for pydantic."""

    GROUP: Final[str] = 'pydantic'

    _instance: Self | None = None
    plugins: list[Callable[..., AbstractContextManager[Any]]] = []

    def __new__(cls, *args: Any, **kwargs: Any):  # noqa: D102
        if cls._instance is None:
            cls._instance = object.__new__(cls, *args, **kwargs)
        return cls._instance

    def load_plugins(self) -> None:
        """Load plugins for pydantic.

        Inspired by:
        - https://github.com/pytest-dev/pytest/blob/5c0e5aa39916e6a49962e662002c23f578e897c9/src/pluggy/_manager.py#L352-L377
        """
        for dist in importlib.metadata.distributions():
            for entry_point in dist.entry_points:
                if entry_point.group == self.GROUP:
                    self.plugins.append(entry_point.load())


def call_plugins(func: Callable[P, R]) -> Callable[P, R]:
    """Call plugins for pydantic."""

    @functools.wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        with ExitStack() as stack:
            for plugin in PluginManager().plugins:
                stack.enter_context(plugin(*args, **kwargs))
            try:
                return func(*args, **kwargs)
            except Exception as e:
                exc = e
                raise exc
        raise exc  # type: ignore

    return wrapper
