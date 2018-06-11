import json
from functools import lru_cache

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
    __slots__ = 'raw_errors',

    def __init__(self, errors):
        self.raw_errors = errors

    @lru_cache()
    def errors(self):
        return list(flatten_errors(self.raw_errors))

    def json(self, *, indent=2):
        return json.dumps(self.errors(), indent=indent)

    def __str__(self):
        errors = self.errors()
        no_errors = len(errors)
        return f'{no_errors} validation error{"" if no_errors == 1 else "s"}\n{display_errors(errors)}'


def display_errors(errors):
    return '\n'.join(
        f'{_display_error_loc(e)}\n  {e["msg"]} ({_display_error_type_and_ctx(e)})'
        for e in errors
    )


def _display_error_loc(error):
    return ' -> '.join(str(l) for l in error['loc'])


def _display_error_type_and_ctx(error):
    t = 'type=' + error['type']
    ctx = error.get('ctx')
    if ctx:
        return t + ''.join(f'; {k}={v}' for k, v in ctx.items())
    else:
        return t


def flatten_errors(errors, *, loc=None):
    for error in errors:
        if isinstance(error, ErrorWrapper):
            if isinstance(error.exc, ValidationError):
                yield from flatten_errors(error.exc.raw_errors, loc=error.loc)
            else:
                yield error.dict(loc_prefix=loc)
        elif isinstance(error, list):
            yield from flatten_errors(error)
        else:
            raise RuntimeError(f'Unknown error object: {error}')


@lru_cache()
def get_exc_type(exc: Exception) -> str:
    cls = type(exc)

    base_name = 'type_error' if issubclass(cls, TypeError) else 'value_error'
    if cls in (TypeError, ValueError):
        # just TypeError or ValueError, no extra code
        return base_name

    # if it's not a TypeError or ValueError, we just take the lowercase of the exception name
    # no chaining or snake case logic, use "code" for more complex error types.
    code = getattr(cls, 'code', None) or cls.__name__.replace('Error', '').lower()
    return base_name + '.' + code
