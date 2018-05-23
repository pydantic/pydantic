import inspect
import json

from .utils import to_snake_case

__all__ = (
    'Error',
    'ValidationError',
    'ConfigError',
    'Missing',
    'Extra',
)


class Error:
    __slots__ = 'exc_info', 'loc'

    def __init__(self, exc, *, loc):
        self.exc_info = exc
        self.loc = loc if isinstance(loc, tuple) else (loc,)

    @property
    def msg(self):
        return str(self.exc_info)

    @property
    def type_(self):
        bases = []
        for b in inspect.getmro(type(self.exc_info)):
            bases.append(b.__name__)
            if b in (ValueError, TypeError):
                break

        return to_snake_case('.'.join(bases[::-1]))


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


class Missing(ValueError):
    pass


class Extra(ValueError):
    pass


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
            if isinstance(error.exc_info, ValidationError):
                yield from flatten_errors(error.exc_info.errors, loc=error.loc)
            else:
                yield {
                    'loc': error.loc if loc is None else loc + error.loc,
                    'msg': error.msg,
                    'type': error.type_,
                }
        elif isinstance(error, list):
            yield from flatten_errors(error)
        else:
            raise RuntimeError(f'Unknown error object: {error}')
