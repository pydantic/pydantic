import inspect
import json
from typing import Union

from .utils import to_snake_case

__all__ = (
    'Error',
    'ValidationError',
    'ConfigError',
    'Missing',
    'Extra',
)


class Error:
    def __init__(self, exc: Exception, *, loc: Union[str, int] = None) -> None:
        self.exc_info = exc
        self.exc_type = type(exc)
        self.loc = loc

    @property
    def msg(self) -> str:
        return str(self.exc_info)

    @property
    def type_(self) -> str:
        bases = []
        for b in inspect.getmro(self.exc_type):
            bases.append(b.__name__)
            if b in (ValueError, TypeError):
                break

        return to_snake_case('.'.join(bases[::-1]))


class ValidationError(ValueError):
    def __init__(self, errors):
        self.errors = errors
        self.message = 'validation errors'

        super().__init__(self.message)

    @property
    def display_errors(self):
        return display_errors(self.flatten_errors)

    @property
    def flatten_errors(self):
        return flatten_errors(self.errors)

    def __str__(self):
        return f'{self.message}\n{self.display_errors}'

    def json(self, *, indent=2):
        return json.dumps(self.flatten_errors, indent=indent, sort_keys=True)


class ConfigError(RuntimeError):
    pass


class Missing(ValueError):
    pass


class Extra(ValueError):
    pass


def display_errors(errors):
    display = []

    for error in errors:
        display.extend([
            error['loc'],
            f'  {error["msg"]} (type={error["type"]})',
        ])

    return '\n'.join(display)


def flatten_errors(errors, *, loc=None):
    flatten = []

    for error in errors:
        if isinstance(error, Error):
            if isinstance(error.exc_info, ValidationError):
                flatten.extend(flatten_errors(error.exc_info.errors, loc=error.loc))
            else:
                flatten.append({
                    'loc': error.loc if loc is None else f'{loc}.{error.loc}',
                    'msg': error.msg,
                    'type': error.type_,
                })
        elif isinstance(error, list):
            flatten.extend(flatten_errors(error))
        else:
            raise TypeError(f'Unknown error object: {error}')

    return flatten
