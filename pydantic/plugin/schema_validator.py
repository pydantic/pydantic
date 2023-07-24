"""Pluggable schema validator for pydantic."""
from __future__ import annotations

import contextlib
import functools
from typing import Any, Callable, TypeVar

from pydantic_core import SchemaValidator, ValidationError
from typing_extensions import Literal, ParamSpec

from .loader import plugins

P = ParamSpec('P')
R = TypeVar('R')


def _plug(func: Callable[P, R]) -> Callable[P, R]:
    """Call plugins for pydantic."""
    caller = _StepCaller(func)

    @functools.wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        caller.enter(*args, **kwargs)
        try:
            result = func(*args, **kwargs)
        except ValidationError as error:
            caller.on_error(error)
            raise
        else:
            caller.on_success(result)
            return result

    return wrapper


class _StepCaller:
    """Call a step for plugins."""

    def __init__(self, func: Callable[..., Any]) -> None:
        if func.__name__ == 'validate_json':
            self.event = 'on_validate_json'
        elif func.__name__ == 'validate_python':
            self.event = 'on_validate_python'
        else:
            raise RuntimeError(f'Unknown event for {func.__name__}')

    def enter(self, *args: Any, **kwargs: Any) -> None:
        """Call `enter` step for plugins."""
        self._on_step('enter')(*args, **kwargs)

    def on_success(self, result: Any) -> None:
        """Call `on_success` step for plugins."""
        self._on_step('on_success')(result)

    def on_error(self, error: ValidationError) -> None:
        """Call `on_error` step for plugins."""
        self._on_step('on_error')(error)

    def _on_step(self, step: Literal['enter', 'on_success', 'on_error']):
        """Call a step for plugins."""

        def on_step(*args: Any, **kwargs: Any) -> None:
            for plugin in plugins:
                with contextlib.suppress(AttributeError, TypeError):
                    on_event = getattr(plugin, self.event)
                    step_func = getattr(on_event, step)
                    step_func(*args, **kwargs)

        return on_step


class PluggableSchemaValidator:
    """Pluggable schema validator."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.schema_validator = SchemaValidator(*args, **kwargs)

        self.validate_json = _plug(self.schema_validator.validate_json)
        self.validate_python = _plug(self.schema_validator.validate_python)

    def __getattr__(self, name: str) -> Any:
        return getattr(self.schema_validator, name)
