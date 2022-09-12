"""
Convert python types to pydantic-core schema.
"""
import re
import typing
from typing import TYPE_CHECKING, Any

from typing_extensions import get_args, is_typeddict

from .typing_extra import (
    NotRequired,
    Required,
    all_literal_values,
    evaluate_forwardref,
    get_origin,
    is_callable_type,
    is_literal_type,
    is_union,
)

__all__ = ('generate_core_schema',)

if TYPE_CHECKING:
    from pydantic_core import Schema as PydanticCoreSchema


def generate_core_schema(obj: Any) -> 'PydanticCoreSchema':
    """
    Recursively generate a pydantic-core schema for any supported python type.
    """
    if isinstance(obj, str):
        # we assume this is already a valid schema
        return obj
    elif obj in (bool, int, float, str, bytes, list, set, frozenset, tuple, dict):
        return obj.__name__
    elif obj is Any:
        return 'any'
    elif obj is None:
        return 'none'
    elif obj == type:
        return {'type': 'is-instance', 'class_': type}
    elif is_union(obj):
        return union_schema(obj)
    elif is_callable_type(obj):
        return 'callable'
    elif is_literal_type(obj):
        return literal_schema(obj)
    elif is_typeddict(obj):
        return type_dict_schema(obj)

    # import here to avoid the extra import time earlier
    from datetime import date, datetime, time, timedelta

    if obj in (datetime, timedelta, date, time):
        return obj.__name__

    origin = get_origin(obj)
    if origin is None:
        raise PydanticSchemaGenerationError(f'Unknown type: {obj!r}, origin is None')
    elif issubclass(origin, (typing.List, typing.Set, typing.FrozenSet)):
        return generic_collection_schema(obj)
    elif issubclass(origin, typing.Tuple):
        return tuple_schema(obj)
    elif issubclass(origin, typing.Dict):
        return dict_schema(obj)
    elif issubclass(origin, typing.Type):
        return type_schema(obj)
    else:
        # debug(obj)
        raise PydanticSchemaGenerationError(f'Unknown type: {obj!r}, origin={origin!r}')


class PydanticSchemaGenerationError(TypeError):
    pass


def union_schema(union_type: Any) -> 'PydanticCoreSchema':
    """
    Generate schema for a Union.
    """
    return {'type': 'union', 'choices': [generate_core_schema(arg) for arg in get_args(union_type)]}


def literal_schema(literal_type: Any) -> 'PydanticCoreSchema':
    """
    Generate schema for a Literal.
    """
    expected = all_literal_values(literal_type)
    assert expected, f'literal "expected" cannot be empty, obj={literal_type}'
    return {'type': 'literal', 'expected': expected}


def type_dict_schema(typed_dict: Any) -> 'PydanticCoreSchema':
    """
    Generate schema for a TypedDict.
    """
    required_keys = getattr(typed_dict, '__required_keys__', set())
    fields = {}

    for field_name, field_type in typed_dict.__annotations__.items():
        required = field_name in required_keys
        schema = None
        if type(field_type) == typing.ForwardRef:
            fr_arg = field_type.__forward_arg__
            fr_arg, matched = re.subn(r'NotRequired\[(.+)]', r'\1', fr_arg)
            if matched:
                required = False

            fr_arg, matched = re.subn(r'Required\[(.+)]', r'\1', fr_arg)
            if matched:
                required = True

            field_type = evaluate_forwardref(field_type)

        if schema is None:
            if get_origin(field_type) == Required:
                required = True
                field_type = field_type.__args__[0]
            if get_origin(field_type) == NotRequired:
                required = False
                field_type = field_type.__args__[0]

            schema = generate_core_schema(field_type)

        fields[field_name] = {'schema': schema, 'required': required}

    return {'type': 'typed-dict', 'fields': fields, 'extra_behavior': 'forbid'}


def generic_collection_schema(obj: Any) -> 'PydanticCoreSchema':
    """
    Generate schema for List, Set etc. - where the schema includes `items_schema`

    e.g. `list[int]`.
    """
    return {'type': obj.__name__, 'items_schema': generate_core_schema(get_args(obj)[0])}


def tuple_schema(tuple_type: Any) -> 'PydanticCoreSchema':
    """
    Generate schema for a Tuple, e.g. `tuple[int, str]` or `tuple[int, ...]`.
    """
    params = get_args(tuple_type)
    if params[-1] is Ellipsis:
        if len(params) == 2:
            return {'type': 'tuple', 'mode': 'variable', 'items_schemas': get_args(params[0])}

        # not sure this case is valid in python, but may as well support it here since pydantic-core does
        *items_schema, extra_schema = params
        return {
            'type': 'tuple',
            'mode': 'positional',
            'items_schema': [generate_core_schema(p) for p in items_schema],
            'extra_schema': generate_core_schema(extra_schema),
        }
    else:
        return {
            'type': 'tuple',
            'mode': 'positional',
            'items_schema': [generate_core_schema(p) for p in params],
        }


def dict_schema(dict_type: Any) -> 'PydanticCoreSchema':
    """
    Generate schema for a Dict, e.g. `dict[str, int]`.
    """
    arg0, arg1 = get_args(dict_type)
    return {
        'type': 'dict',
        'keys_schema': generate_core_schema(arg0),
        'values_schema': generate_core_schema(arg1),
    }


def type_schema(type_: Any) -> 'PydanticCoreSchema':
    """
    Generate schema for a Type, e.g. `Type[int]`.
    """
    type_param = get_args(type_)[0]
    if type_param == Any:
        return {'type': 'is-instance', 'class_': type}
    else:
        return {'type': 'is-instance', 'class_': type_param}
