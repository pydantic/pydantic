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
from typing import Any, Callable, Final, Literal, ParamSpec, TypeVar

from pydantic_core import ValidationError

from .plugin import Plugin

P = ParamSpec('P')
R = TypeVar('R')


GROUP: Final[str] = 'pydantic'


def load_plugins() -> list[Plugin]:
    """Load plugins for pydantic.

    Inspired by:
    - https://github.com/pytest-dev/pytest/blob/5c0e5aa39916e6a49962e662002c23f578e897c9/src/pluggy/_manager.py#L352-L377
    """
    plugins: list[Plugin] = []
    for dist in importlib.metadata.distributions():
        for entry_point in dist.entry_points:
            if entry_point.group == GROUP:
                plugins.append(entry_point.load())
    return plugins

plugins = load_plugins()


def plug(func: Callable[P, R]) -> Callable[P, R]:
    """Call plugins for pydantic."""

    def call_step(step: Literal['enter', 'on_success', 'on_error']):
        def call(*args: Any, **kwargs: Any) -> None:
            for plugin in plugins:
                if plugin.on_validate_python and getattr(plugin.on_validate_python, step):
                    getattr(plugin.on_validate_python, step)(*args, **kwargs)
        return call

    call_enter = call_step('enter')
    call_on_success = call_step('on_success')
    call_on_error = call_step('on_success')

    @functools.wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        call_enter(*args, **kwargs)
        try:
            result = func(*args, **kwargs)
        except ValidationError as error:
            call_on_error(error)
            raise error
        else:
            call_on_success(result)
            return result

    return wrapper
