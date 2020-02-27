from functools import wraps
from inspect import Parameter, signature
from itertools import filterfalse, groupby, tee
from operator import itemgetter
from typing import Any, Callable, Container, Dict, Iterable, Protocol, Tuple, TypeVar

from .main import create_model
from .utils import to_camel

__all__ = ('validate_arguments',)

T = TypeVar('T')

# based on itertools recipe `partition` from https://docs.python.org/3.8/library/itertools.html
def partition_dict(pred: Callable[..., bool], iterable: Dict[str, T]) -> Tuple[Dict[str, T], Dict[str, T]]:
    t1, t2 = tee(iterable.items())
    return dict(filterfalse(pred, t1)), dict(filter(pred, t2))


def coalesce(param: Parameter, default: Any) -> Any:
    return param if param != Parameter.empty else default


def make_field(arg: Parameter) -> Dict[str, Any]:
    return {'name': arg.name, 'kind': arg.kind, 'field': (coalesce(arg.annotation, Any), coalesce(arg.default, ...))}


def contained(mapping: Container[T]) -> Callable[[Tuple[str, T]], bool]:
    def inner(entry: Tuple[str, T]) -> bool:
        return entry[0] in mapping

    return inner


def validate_arguments(func: Callable[..., T]) -> Callable[..., T]:
    """
    Decorator to validate the arguments passed to a function.
    """
    sig = signature(func).parameters
    fields = [make_field(p) for p in sig.values()]

    # Python syntax should already enforce fields to be ordered by kind
    grouped = groupby(fields, key=itemgetter('kind'))
    params = {kind: {field['name']: field['field'] for field in val} for kind, val in grouped}

    # Arguments descriptions by kind
    # note that VAR_POSITIONAL and VAR_KEYWORD are ignored here
    # otherwise, the model will expect them on function call.
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

    vp_name = next(iter(var_positional.keys()), None)
    vk_name = next(iter(var_keyword.keys()), None)

    model = create_model(
        to_camel(func.__name__),
        **positional_only,
        **positional_or_keyword,
        **var_positional,
        **keyword_only,
        **var_keyword,
    )
    sig_pos = tuple(positional_only) + tuple(positional_or_keyword)
    sig_kw = set(positional_or_keyword) | set(keyword_only)

    @wraps(func)
    def apply(*args: Any, **kwargs: Any) -> T:

        # Consume used positional arguments
        iargs = iter(args)
        given_pos = dict(zip(sig_pos, iargs))
        rest_pos = {vp_name: tuple(iargs)} if vp_name else {}

        ikwargs, given_kw = partition_dict(contained(sig_kw), kwargs)
        rest_kw = {vk_name: ikwargs} if vk_name else {}

        # use dict(model) instead of model.dict() so values stay cast as intended
        instance = dict(model(**given_pos, **rest_pos, **given_kw, **rest_kw))

        as_kw, as_pos = partition_dict(contained(given_pos), instance)

        as_rest_pos = tuple(as_kw[vp_name]) if vp_name else tuple(iargs)
        as_rest_kw = as_kw[vk_name] if vk_name else ikwargs

        as_kw = {k: v for k, v in as_kw.items() if k not in {vp_name, vk_name}}

        # Preserve original keyword ordering - not sure if this is necessary
        kw_order = {k: idx for idx, (k, v) in enumerate(kwargs.items())}
        sorted_all_kw = dict(
            sorted({**as_kw, **as_rest_kw}.items(), key=lambda val: kw_order.get(val[0], len(given_kw)))
        )

        return func(*as_pos.values(), *as_rest_pos, **sorted_all_kw)

        # # Without preserving original keyword ordering
        # return func(*as_pos.values(), *as_rest_pos, **as_kw, **as_rest_kw)

    return apply
