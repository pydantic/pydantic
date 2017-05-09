import json
from collections import OrderedDict, namedtuple


def type_display(type_: type):
    if type_:
        try:
            return type_.__name__
        except AttributeError:
            # happens with unions
            return str(type_)


Error = namedtuple('Error', ['exc', 'track', 'index'])


def jsonify_errors(e):
    if not e:
        return e
    elif isinstance(e, Error):
        d = {
            'error_type': e.exc.__class__.__name__,
            'track': type_display(e.track),
            'index': e.index,
        }
        if isinstance(e.exc, ValidationError):
            d.update(
                error_msg=e.exc.message,
                error_details=e.exc.errors_jsonable,
            )
        else:
            d['error_msg'] = str(e.exc)
        return d
    elif isinstance(e, OrderedDict):
        return OrderedDict([(k, jsonify_errors(v)) for k, v in e.items()])
    else:
        return [jsonify_errors(e_) for e_ in e]


class ValidationError(ValueError):
    def __init__(self, errors):
        self.errors = errors
        e_count = len(self.errors)
        s = '' if e_count == 1 else 's'
        self.message = f'{e_count} error{s} validating input'
        self.errors_jsonable = jsonify_errors(errors)
        super().__init__(f'{self.message}: {self.json()}')

    def json(self, indent=None):
        return json.dumps(self.errors_jsonable, indent=indent, sort_keys=True)


class ConfigError(RuntimeError):
    pass


class Missing(ValueError):
    pass


class Extra(ValueError):
    pass
