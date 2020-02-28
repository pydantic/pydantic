from functools import wraps
from inspect import Parameter, signature
from itertools import groupby
from operator import itemgetter
from typing import Any, Callable, Dict, Tuple, TypeVar

from .main import BaseConfig, Extra, create_model
from .utils import to_camel

__all__ = ('validate_arguments',)

T = TypeVar('T')


class Config(BaseConfig):
    extra = Extra.forbid


def coalesce(param: Parameter, default: Any) -> Any:
    return param if param != Parameter.empty else default


def make_field(arg: Parameter) -> Dict[str, Any]:
    return {'name': arg.name, 'kind': arg.kind, 'field': (coalesce(arg.annotation, Any), coalesce(arg.default, ...))}


def validate_arguments(func: Callable[..., T]) -> Callable[..., T]:
    """
    Decorator to validate the arguments passed to a function.
    """
    sig = signature(func)
    fields = [make_field(p) for p in sig.parameters.values()]

    # Python syntax should already enforce fields to be ordered by kind
    grouped = groupby(fields, key=itemgetter('kind'))
    params = {kind: {field['name']: field['field'] for field in val} for kind, val in grouped}

    # Arguments descriptions by kind
    positional_only = params.get(Parameter.POSITIONAL_ONLY, {})
    positional_or_keyword = params.get(Parameter.POSITIONAL_OR_KEYWORD, {})
    var_positional = params.get(Parameter.VAR_POSITIONAL, {})
    keyword_only = params.get(Parameter.KEYWORD_ONLY, {})
    var_keyword = params.get(Parameter.VAR_KEYWORD, {})

    var_positional = {name: (Tuple[annotation, ...], ...) for name, (annotation, _) in var_positional.items()}
    var_keyword = {
        name: (Dict[str, annotation], ...)  # type: ignore
        for name, (annotation, _) in var_keyword.items()
    }

    assert len(var_positional) <= 1
    assert len(var_keyword) <= 1

    model = create_model(
        to_camel(func.__name__),
        __config__=Config,
        **positional_only,
        **positional_or_keyword,
        **var_positional,
        **keyword_only,
        **var_keyword,
    )

    @wraps(func)
    def apply(*args: Any, **kwargs: Any) -> T:

        # NOTE: this throws TypeError if does not match signature
        given_pos = sig.bind_partial(*args).arguments
        given_kw = sig.bind_partial(**kwargs).arguments

        # use dict(model) instead of model.dict() so values stay cast as intended
        instance = dict(model(**given_pos, **given_kw))

        upd_arg = {k: instance.get(k, v) for k, v in given_pos.items()}
        upd_kw = {k: instance.get(k, v) for k, v in given_kw.items()}

        return func(*upd_arg.values(), **upd_kw)

    return apply
