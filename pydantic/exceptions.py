import inspect
import json
from itertools import chain
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
    __slots__ = (
        'exc_info',
        'exc_type',
        'loc',
    )

    def __init__(self, exc: Exception, *, loc: Union[str, int] = None) -> None:
        self.exc_info = exc
        self.exc_type = type(exc)
        self.loc = loc

    @property
    def type_(self) -> str:
        bases = []
        for b in inspect.getmro(self.exc_type):
            bases.append(b.__name__)
            if b in (ValueError, TypeError):
                break

        return to_snake_case('.'.join(bases[::-1]))


class ErrorDict(dict):
    pass


def pretty_errors(e):
    if isinstance(e, Error):
        d = ErrorDict(type=e.type_)
        if e.loc is not None:
            d['loc'] = e.loc
        if isinstance(e.exc_info, ValidationError):
            d.update(
                error_msg=e.exc_info.message,
                error_details=e.exc_info.errors_dict,
            )
        else:
            d['error_msg'] = str(e.exc_info)
        return d
    elif isinstance(e, dict):
        return {k: pretty_errors(v) for k, v in e.items()}
    elif isinstance(e, (list, tuple)):
        return [pretty_errors(e_) for e_ in e]
    else:
        raise TypeError(f'Unknown error object: {e}')


E_KEYS = 'type', 'loc'


def _render_errors(e, indent=0):
    if isinstance(e, list):
        return list(chain(*(_render_errors(error, indent) for error in e)))
    elif isinstance(e, ErrorDict):
        v = ' '.join(f'{k}={e.get(k)}' for k in E_KEYS if e.get(k))
        r = [(indent, f'{e["error_msg"]} ({v})')]
        error_details = e.get('error_details')
        if error_details:
            r.extend(_render_errors(error_details, indent=indent + 1))
        return r
    else:
        # assumes e is a dict
        r = []
        for key, error in e.items():
            r.append((indent, key + ':'))
            r.extend(_render_errors(error, indent=indent + 1))
        return r


class ValidationError(ValueError):
    def __init__(self, errors):
        self.errors_raw = errors
        e_count = len(errors)
        self.message = 'error validating input' if e_count == 1 else f'{e_count} errors validating input'
        super().__init__(self.message)

    def json(self, indent=2):
        return json.dumps(self.errors_dict, indent=indent, sort_keys=True)

    @property
    def errors_dict(self):
        return pretty_errors(self.errors_raw)

    @property
    def display_errors(self):
        return '\n'.join('  ' * i + msg for i, msg in _render_errors(self.errors_dict))

    def __str__(self):
        return f'{self.message}\n{self.display_errors}'


class ConfigError(RuntimeError):
    pass


class Missing(ValueError):
    pass


class Extra(ValueError):
    pass
