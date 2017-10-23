import json
from collections import OrderedDict, namedtuple
from itertools import chain

__all__ = (
    'Error',
    'ValidationError',
    'ConfigError',
    'Missing',
    'Extra',
)


def type_display(type_: type):
    try:
        return type_.__name__
    except AttributeError:
        # happens with unions
        return str(type_)


Error = namedtuple('Error', ['exc', 'track', 'index'])


def pretty_errors(e):
    if isinstance(e, Error):
        d = {'error_type': e.exc.__class__.__name__}
        if e.track is not None:
            d['track'] = type_display(e.track)
        if e.index is not None:
            d['index'] = e.index
        if isinstance(e.exc, ValidationError):
            d.update(
                error_msg=e.exc.message,
                error_details=e.exc.errors_dict,
            )
        else:
            d['error_msg'] = str(e.exc)
        return d
    elif isinstance(e, dict):
        return OrderedDict([(k, pretty_errors(v)) for k, v in e.items()])
    elif isinstance(e, (list, tuple)):
        return [pretty_errors(e_) for e_ in e]
    else:
        raise TypeError(f'Unknown error object: {e}')


E_KEYS = 'error_type', 'track', 'index'


def _render_errors(e, indent=0):
    if isinstance(e, list):
        return list(chain(*(_render_errors(error, indent) for error in e)))
    elif isinstance(e, OrderedDict):
        r = []
        for key, error in e.items():
            r.append((indent, key + ':'))
            r.extend(_render_errors(error, indent=indent + 1))
        return r
    else:
        v = ' '.join(f'{k}={e.get(k)}' for k in E_KEYS if e.get(k))
        r = [(indent, f'{e["error_msg"]} ({v})')]
        error_details = e.get('error_details')
        if error_details:
            r.extend(_render_errors(error_details, indent=indent + 1))
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
