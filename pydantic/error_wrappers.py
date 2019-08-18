import json
from functools import lru_cache
from typing import TYPE_CHECKING, Any, Dict, Generator, List, Optional, Sequence, Tuple, Type, Union

if TYPE_CHECKING:  # pragma: no cover
    from pydantic import BaseConfig  # noqa: F401
    from .types import ModelOrDc  # noqa: F401

__all__ = ('ErrorWrapper', 'ValidationError')


class ErrorWrapper:
    __slots__ = 'exc', 'loc'

    def __init__(self, exc: Exception, *, loc: Union[Tuple[str, ...], str]) -> None:
        self.exc = exc
        self.loc: Tuple[str, ...] = loc if isinstance(loc, tuple) else (loc,)  # type: ignore

    def dict(
        self, *, config: Optional[Type['BaseConfig']] = None, loc_prefix: Optional[Tuple[str, ...]] = None
    ) -> Dict[str, Any]:
        loc = self.loc if loc_prefix is None else loc_prefix + self.loc

        type_ = get_exc_type(type(self.exc))
        msg_template: Optional[str] = config and config.error_msg_templates.get(type_)  # type: ignore
        msg_template = msg_template or getattr(self.exc, 'msg_template', None)
        ctx = getattr(self.exc, 'ctx', None)
        if msg_template:
            if ctx:
                msg: str = msg_template.format(**ctx)
            else:
                msg = msg_template
        else:
            msg = str(self.exc)

        d: Dict[str, Any] = {'loc': loc, 'msg': msg, 'type': type_}

        if ctx is not None:
            d['ctx'] = ctx

        return d

    def __repr__(self) -> str:
        return f'<ErrorWrapper {self.dict()}>'


# ErrorList is something like Union[List[Union[List[ErrorWrapper], ErrorWrapper]], ErrorWrapper]
# but recursive, therefore just use:
ErrorList = Union[Sequence[Any], ErrorWrapper]


class ValidationError(ValueError):
    __slots__ = 'raw_errors', 'model'

    def __init__(self, errors: Sequence[ErrorList], model: 'ModelOrDc') -> None:
        self.raw_errors = errors
        self.model = model

    @lru_cache()
    def errors(self) -> List[Dict[str, Any]]:
        try:
            config = self.model.__config__  # type: ignore
        except AttributeError:
            config = self.model.__pydantic_model__.__config__  # type: ignore
        return list(flatten_errors(self.raw_errors, config))

    def json(self, *, indent: Union[None, int, str] = 2) -> str:
        return json.dumps(self.errors(), indent=indent)

    def __str__(self) -> str:
        errors = self.errors()
        no_errors = len(errors)
        return (
            f'{no_errors} validation error{"" if no_errors == 1 else "s"} for {self.model.__name__}\n'
            f'{display_errors(errors)}'
        )


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
    errors: Sequence[Any], config: Type['BaseConfig'], *, loc: Optional[Tuple[str, ...]] = None
) -> Generator[Dict[str, Any], None, None]:
    for error in errors:
        if isinstance(error, ErrorWrapper):
            if isinstance(error.exc, ValidationError):
                if loc is not None:
                    error_loc = loc + error.loc
                else:
                    error_loc = error.loc
                yield from flatten_errors(error.exc.raw_errors, config, loc=error_loc)
            else:
                yield error.dict(config=config, loc_prefix=loc)
        elif isinstance(error, list):
            yield from flatten_errors(error, config)
        else:
            raise RuntimeError(f'Unknown error object: {error}')


@lru_cache()
def get_exc_type(cls: Type[Exception]) -> str:
    if issubclass(cls, AssertionError):
        return 'assertion_error'

    base_name = 'type_error' if issubclass(cls, TypeError) else 'value_error'
    if cls in (TypeError, ValueError):
        # just TypeError or ValueError, no extra code
        return base_name

    # if it's not a TypeError or ValueError, we just take the lowercase of the exception name
    # no chaining or snake case logic, use "code" for more complex error types.
    code = getattr(cls, 'code', None) or cls.__name__.replace('Error', '').lower()
    return base_name + '.' + code
