import json
from functools import lru_cache
from typing import Iterable, Type

from .errors import PydanticErrorMixin
from .utils import to_snake_case

__all__ = (
    'ErrorWrapper',
    'ValidationError',
)


class ErrorWrapper:
    __slots__ = 'exc', 'loc', 'msg_template'

    def __init__(self, exc, *, loc, config=None):
        self.exc = exc
        self.loc = loc if isinstance(loc, tuple) else (loc,)
        self.msg_template = config.error_msg_templates.get(self.type_) if config else None

    @property
    def ctx(self):
        return getattr(self.exc, 'ctx', None)

    @property
    def msg(self):
        default_msg_template = getattr(self.exc, 'msg_template', None)
        msg_template = self.msg_template or default_msg_template
        if msg_template:
            return msg_template.format(**self.ctx or {})

        return str(self.exc)

    @property
    def type_(self):
        return get_exc_type(self.exc)

    def dict(self, *, loc_prefix=None):
        loc = self.loc if loc_prefix is None else loc_prefix + self.loc

        d = {
            'loc': loc,
            'msg': self.msg,
            'type': self.type_,
        }

        if self.ctx is not None:
            d['ctx'] = self.ctx

        return d


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
        f'{_display_error_loc(e)}\n  {e["msg"]} ({_display_error_type_and_ctx(e)})'
        for e in errors
    )


def _display_error_loc(error):
    return ' -> '.join(str(l) for l in error['loc'])


def _display_error_type_and_ctx(error):
    display = f'type={error["type"]}'

    ctx = error.get('ctx')
    if ctx:
        ctx = '; '.join(f'{k}={v}' for k, v in ctx.items())
        display = f'{display}; {ctx}'

    return display


def flatten_errors(errors, *, loc=None):
    for error in errors:
        if isinstance(error, ErrorWrapper):
            if isinstance(error.exc, ValidationError):
                yield from flatten_errors(error.exc.errors, loc=error.loc)
            else:
                yield error.dict(loc_prefix=loc)
        elif isinstance(error, list):
            yield from flatten_errors(error)
        else:
            raise RuntimeError(f'Unknown error object: {error}')


@lru_cache()
def get_exc_type(exc: Exception) -> str:
    cls = type(exc)

    if issubclass(cls, PydanticErrorMixin):
        return _get_pydantic_exc_type(cls)

    bases = tuple(_get_exc_bases(cls))
    bases = bases[::-1]

    return to_snake_case('.'.join(bases))


def _get_pydantic_exc_type(exc: Type[PydanticErrorMixin]) -> str:
    if issubclass(exc, TypeError):
        type_ = 'type_error'
    else:
        type_ = 'value_error'

    return f'{type_}.{exc.code}'


def _get_exc_bases(exc: Type[Exception]) -> Iterable[str]:
    for b in exc.__mro__:  # pragma: no branch
        if b in (TypeError, ValueError):
            yield b.__name__
            break

        yield b.__name__.replace('Error', '')
