import json
from functools import lru_cache
from typing import TYPE_CHECKING, Any, Dict, Generator, List, Optional, Sequence, Tuple, Type, Union

if TYPE_CHECKING:  # pragma: no cover
    from pydantic import BaseConfig  # noqa: F401

__all__ = ('ErrorWrapper', 'ValidationError')


class ErrorWrapper:
    __slots__ = 'exc', 'type_', 'loc', 'msg_template'

    def __init__(
        self, exc: Exception, *, loc: Union[Tuple[str, ...], str], config: Optional[Type['BaseConfig']] = None
    ) -> None:
        self.exc = exc
        self.type_ = get_exc_type(type(exc))
        self.loc: Tuple[str, ...] = loc if isinstance(loc, tuple) else (loc,)  # type: ignore
        self.msg_template = config.error_msg_templates.get(self.type_) if config else None

    @property
    def ctx(self) -> Dict[str, Any]:
        return getattr(self.exc, 'ctx', None)

    @property
    def msg(self) -> str:
        default_msg_template = getattr(self.exc, 'msg_template', None)
        msg_template = self.msg_template or default_msg_template
        if msg_template:
            return msg_template.format(**self.ctx or {})

        return str(self.exc)

    def dict(self, *, loc_prefix: Optional[Tuple[str, ...]] = None) -> Dict[str, Any]:
        loc = self.loc if loc_prefix is None else loc_prefix + self.loc

        d: Dict[str, Any] = {'loc': loc, 'msg': self.msg, 'type': self.type_}

        if self.ctx is not None:
            d['ctx'] = self.ctx

        return d


# ErrorList is something like Union[List[Union[List[ErrorWrapper], ErrorWrapper]], ErrorWrapper]
# but recursive, therefore just use:
ErrorList = Union[Sequence[Any], ErrorWrapper]


class ValidationError(ValueError):
    __slots__ = ('raw_errors',)

    def __init__(self, errors: Sequence[ErrorList]) -> None:
        self.raw_errors = errors

    @lru_cache()
    def errors(self) -> List[Dict[str, Any]]:
        return list(flatten_errors(self.raw_errors))

    def json(self, *, indent: Union[None, int, str] = 2) -> str:
        return json.dumps(self.errors(), indent=indent)

    def __str__(self) -> str:
        errors = self.errors()
        no_errors = len(errors)
        return f'{no_errors} validation error{"" if no_errors == 1 else "s"}\n{display_errors(errors)}'


def display_errors(errors: List[Dict[str, Any]]) -> str:
    return '\n'.join(f'{_display_error_loc(e)}\n  {e["msg"]} ({_display_error_type_and_ctx(e)})' for e in errors)


def _display_error_loc(error: Dict[str, Any]) -> str:
    return ' -> '.join(str(l) for l in error['loc'])


def _display_error_type_and_ctx(error: Dict[str, Any]) -> str:
    t = 'type=' + error['type']
    ctx = error.get('ctx')
    if ctx:
        return t + ''.join(f'; {k}={v}' for k, v in ctx.items())
    else:
        return t


def flatten_errors(
    errors: Sequence[Any], *, loc: Optional[Tuple[str, ...]] = None
) -> Generator[Dict[str, Any], None, None]:
    for error in errors:
        if isinstance(error, ErrorWrapper):
            if isinstance(error.exc, ValidationError):
                if loc is not None:
                    error_loc = loc + error.loc
                else:
                    error_loc = error.loc
                yield from flatten_errors(error.exc.raw_errors, loc=error_loc)
            else:
                yield error.dict(loc_prefix=loc)
        elif isinstance(error, list):
            yield from flatten_errors(error)
        else:
            raise RuntimeError(f'Unknown error object: {error}')


@lru_cache()
def get_exc_type(cls: Type[Exception]) -> str:

    base_name = 'type_error' if issubclass(cls, TypeError) else 'value_error'
    if cls in (TypeError, ValueError):
        # just TypeError or ValueError, no extra code
        return base_name

    # if it's not a TypeError or ValueError, we just take the lowercase of the exception name
    # no chaining or snake case logic, use "code" for more complex error types.
    code = getattr(cls, 'code', None) or cls.__name__.replace('Error', '').lower()
    return base_name + '.' + code
