from __future__ import annotations as _annotations

from typing import Any

from pydantic_core import PydanticValueError

__all__ = ('import_string',)


def import_string(value: Any, **kwargs) -> Any:
    if isinstance(value, str):
        try:
            return _import_string_logic(value)
        except ImportError as e:
            raise PydanticValueError('import_error', 'Invalid python path: {error}', {'error': str(e)})
    else:
        # otherwise we just return the value and let the next validator do the test of the work
        return value


def _import_string_logic(dotted_path: str) -> Any:
    """
    Stolen approximately from django. Import a dotted module path and return the attribute/class designated by the
    last name in the path. Raise ImportError if the import fails.
    """
    from importlib import import_module

    try:
        module_path, class_name = dotted_path.strip(' ').rsplit('.', 1)
    except ValueError as e:
        raise ImportError(f'"{dotted_path}" doesn\'t look like a module path') from e

    module = import_module(module_path)
    try:
        return getattr(module, class_name)
    except AttributeError as e:
        raise ImportError(f'Module "{module_path}" does not define a "{class_name}" attribute') from e
