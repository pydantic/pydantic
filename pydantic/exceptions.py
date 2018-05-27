import json
from functools import lru_cache
from typing import Iterable, Type

from .errors import PydanticErrorMixin, PydanticTypeError, PydanticValueError
from .utils import to_snake_case

__all__ = (
    'Error',
    'ValidationError',
)


class Error:
    __slots__ = 'exc', 'loc'

    def __init__(self, exc, *, loc):
        self.exc = exc
        self.loc = loc if isinstance(loc, tuple) else (loc,)

    @property
    def ctx(self):
        return getattr(self.exc, 'ctx', None)

    @property
    def msg(self):
        return str(self.exc)

    @property
    def type_(self):
        return get_exc_type(self.exc)

    def as_dict(self, *, loc_prefix=None):
        loc = self.loc if loc_prefix is None else loc_prefix + self.loc

        return {
            'loc': loc,
            'msg': self.msg,
            'type': self.type_,
            'ctx': self.ctx,
        }


class ValidationError(ValueError):
    __slots__ = 'errors', 'message'

    def __init__(self, errors):
        self.errors = errors
        self.message = 'validation errors'

        super().__init__(self.message)

    @property
    def display_errors(self):
        return display_errors(self.flatten_errors())

    def __str__(self):
        return f'{self.message}\n{self.display_errors}'

    def flatten_errors(self):
        return list(flatten_errors(self.errors))

    def json(self, *, indent=2):
        return json.dumps(self.flatten_errors(), indent=indent, sort_keys=True)


def display_errors(errors):
    return '\n'.join(
        f'{_display_error_loc(e["loc"])}\n  {e["msg"]} (type={e["type"]})'
        for e in errors
    )


def _display_error_loc(loc):
    return ' -> '.join(str(l) for l in loc)


def flatten_errors(errors, *, loc=None):
    for error in errors:
        if isinstance(error, Error):
            if isinstance(error.exc, ValidationError):
                yield from flatten_errors(error.exc.errors, loc=error.loc)
            else:
                yield error.as_dict(loc_prefix=loc)
        elif isinstance(error, list):
            yield from flatten_errors(error)
        else:
            raise RuntimeError(f'Unknown error object: {error}')


@lru_cache()
def get_exc_type(exc: Exception) -> str:
    bases = tuple(_get_exc_bases(type(exc)))
    bases = bases[::-1]

    return to_snake_case('.'.join(bases))


def _get_exc_bases(exc: Type[Exception]) -> Iterable[str]:
    for b in exc.__mro__:  # pragma: no branch
        if b in (PydanticErrorMixin, PydanticTypeError, PydanticValueError):
            continue

        if b in (TypeError, ValueError):
            yield b.__name__
            break

        yield b.__name__.replace('Error', '')
