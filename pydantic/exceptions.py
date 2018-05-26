import json
from typing import Iterable, Type

from .utils import to_snake_case

__all__ = (
    'Error',
    'ValidationError',
    'ConfigError',

    'ValueError_',
    'TypeError_',

    'MissingError',
    'ExtraError',

    'DecimalError',
    'DecimalIsNotFiniteError',
    'DecimalMaxDigitsError',
    'DecimalMaxPlacesError',
    'DecimalWholeDigitsError',

    'UUIDError',
    'UUIDVersionError',
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


class ConfigError(RuntimeError):
    pass


class ValueError_(ValueError):
    def __init__(self, msg_tmpl, **ctx):
        self.ctx = ctx or None
        self.msg_tmpl = msg_tmpl

        super().__init__()

    def __str__(self) -> str:
        return self.msg_tmpl.format(**self.ctx or {})


class TypeError_(TypeError):
    def __init__(self, msg_tmpl, **ctx):
        self.ctx = ctx or None
        self.msg_tmpl = msg_tmpl

        super().__init__()

    def __str__(self) -> str:
        return self.msg_tmpl.format(**self.ctx or {})


class MissingError(ValueError_):
    def __init__(self) -> None:
        super().__init__('field required')


class ExtraError(ValueError_):
    def __init__(self) -> None:
        super().__init__('extra fields not permitted')


class DecimalError(TypeError_):
    def __init__(self) -> None:
        super().__init__('value is not a valid decimal')


class DecimalIsNotFiniteError(ValueError_):
    def __init__(self) -> None:
        super().__init__('value is not a valid decimal')


class DecimalMaxDigitsError(ValueError_):
    def __init__(self, *, max_digits: int) -> None:
        super().__init__(
            'ensure that there are no more than {max_digits} digits in total',
            max_digits=max_digits
        )


class DecimalMaxPlacesError(ValueError_):
    def __init__(self, *, decimal_places: int) -> None:
        super().__init__(
            'ensure that there are no more than {decimal_places} decimal places',
            decimal_places=decimal_places
        )


class DecimalWholeDigitsError(ValueError_):
    def __init__(self, *, whole_digits: int) -> None:
        super().__init__(
            'ensure that there are no more than {whole_digits} digits before the decimal point',
            whole_digits=whole_digits
        )


class UUIDError(TypeError_):
    def __init__(self):
        super().__init__('value is not a valid uuid')


class UUIDVersionError(ValueError_):
    def __init__(self, *, required_version: int) -> None:
        super().__init__(
            'uuid version {required_version} expected',
            required_version=required_version
        )


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


_EXC_TYPES = {}


def get_exc_type(exc: Exception) -> str:
    exc = type(exc)
    if exc in _EXC_TYPES:
        return _EXC_TYPES[exc]

    bases = tuple(_get_exc_bases(exc))
    bases = bases[::-1]

    type_ = to_snake_case('.'.join(bases))
    _EXC_TYPES[exc] = type_
    return type_


def _get_exc_bases(exc: Type[Exception]) -> Iterable[str]:
    for b in exc.__mro__:
        if b in (ValueError_, TypeError_,):
            continue

        if b in (ValueError, TypeError):
            yield b.__name__
            break

        yield b.__name__.replace('Error', '')
