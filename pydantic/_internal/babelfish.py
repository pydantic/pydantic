"""
Convert python types to pydantic-core schema.
"""
from __future__ import annotations as _annotations

import re
import typing
from typing import TYPE_CHECKING, Any

from pydantic_core import schema_types as core_schema
from typing_extensions import get_args, is_typeddict

from pydantic.fields import FieldInfo, Undefined

from .typing_extra import (
    NoneType,
    NotRequired,
    Required,
    all_literal_values,
    evaluate_forwardref,
    get_origin,
    is_callable_type,
    is_literal_type,
    origin_is_union,
)
from .valdation_functions import ValidationFunctions, Validator

if TYPE_CHECKING:
    from ..config import BaseConfig

__all__ = 'generate_config', 'generate_schema', 'model_fields_schema'


def model_fields_schema(
    ref: str, fields: dict[str, FieldInfo], validator_functions: ValidationFunctions
) -> core_schema.Schema:
    schema: core_schema.Schema = core_schema.TypedDictSchema(
        type='typed-dict',
        ref=ref,
        return_fields_set=True,
        fields={k: generate_field_schema(k, v, validator_functions) for k, v in fields.items()},
    )
    schema = apply_validators(schema, validator_functions.get_root_validators())
    return schema


def generate_config(config: type[BaseConfig]) -> core_schema.Config:
    return core_schema.Config(
        typed_dict_extra_behavior=config.extra.value,
        # allow_inf_nan=config.allow_inf_nan,
        populate_by_name=config.allow_population_by_field_name,
    )


def generate_schema(obj: Any) -> core_schema.Schema:  # noqa: C901 (ignore complexity)
    """
    Recursively generate a pydantic-core schema for any supported python type.
    """
    if isinstance(obj, (str, dict)):
        # we assume this is already a valid schema
        return obj  # type: ignore[return-value]
    elif obj in (bool, int, float, str, bytes, list, set, frozenset, tuple, dict):
        return obj.__name__
    elif obj is Any or obj is object:
        return 'any'
    elif obj is None or obj is NoneType:
        return 'none'
    elif obj == type:
        return core_schema.IsInstanceSchema(type='is-instance', class_=type)
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

    schema_property = getattr(obj, '__pydantic_validation_schema__', None)
    if schema_property is not None:
        return schema_property

    get_schema = getattr(obj, '__get_pydantic_validation_schema__', None)
    if get_schema is not None:
        return get_schema()

    origin = get_origin(obj)
    if origin is None:
        raise PydanticSchemaGenerationError(f'Unable to generate pydantic-core schema for {obj!r}.')
    elif origin_is_union(origin):
        return union_schema(obj)
    elif issubclass(origin, (typing.List, typing.Set, typing.FrozenSet)):
        return generic_collection_schema(obj)
    elif issubclass(origin, typing.Tuple):  # type: ignore[arg-type]
        return tuple_schema(obj)
    elif issubclass(origin, typing.Dict):
        return dict_schema(obj)
    elif issubclass(origin, typing.Type):  # type: ignore[arg-type]
        return type_schema(obj)
    else:
        # debug(obj)
        raise PydanticSchemaGenerationError(f'Unable to generate pydantic-core schema for {obj!r} (origin={origin!r}).')


def generate_field_schema(
    name: str, field: FieldInfo, validator_functions: ValidationFunctions
) -> core_schema.TypedDictField:
    """
    Prepare a TypedDictField to represent a model or typeddict field.
    """
    assert field.annotation is not None, 'field.annotation should not be None when generating a schema'
    schema: core_schema.Schema = generate_schema(field.annotation)
    schema = apply_validators(schema, validator_functions.get_field_validators(name))

    required = False
    if field.default_factory:
        schema = core_schema.WithDefaultSchema(type='default', schema=schema, default_factory=field.default_factory)
    elif field.default is Undefined:
        required = True
    else:
        schema = core_schema.WithDefaultSchema(type='default', schema=schema, default=field.default)

    field_schema = core_schema.TypedDictField(schema=schema, required=required)
    if field.alias is not None:
        field_schema['alias'] = field.alias
    return field_schema


def apply_validators(schema: core_schema.Schema, validators: list[Validator]) -> core_schema.Schema:
    """
    Apply validators to a schema.
    """
    for validator in validators:
        assert validator.sub_path is None, 'validator.sub_path is not yet supported'
        function = typing.cast(typing.Callable[..., Any], validator.function)
        if validator.mode == 'plain':
            schema = core_schema.FunctionPlainSchema(
                type='function',
                mode='plain',
                function=function,
            )
        else:
            schema = core_schema.FunctionSchema(
                type='function',
                mode=validator.mode,
                function=function,
                schema=schema,
            )
    return schema


class PydanticSchemaGenerationError(TypeError):
    pass


def union_schema(union_type: Any) -> core_schema.Schema:
    """
    Generate schema for a Union.
    """
    args = get_args(union_type)
    choices = []
    nullable = False
    for arg in args:
        if arg is None or arg is NoneType:
            nullable = True
        else:
            choices.append(generate_schema(arg))

    if len(choices) == 1:
        s = choices[0]
    else:
        s = core_schema.UnionSchema(type='union', choices=choices)

    if nullable:
        s = core_schema.NullableSchema(type='nullable', schema=s)
    return s


def literal_schema(literal_type: Any) -> core_schema.Schema:
    """
    Generate schema for a Literal.
    """
    expected = all_literal_values(literal_type)
    assert expected, f'literal "expected" cannot be empty, obj={literal_type}'
    return {'type': 'literal', 'expected': list(expected)}


def type_dict_schema(typed_dict: Any) -> core_schema.TypedDictSchema:
    """
    Generate schema for a TypedDict.
    """
    required_keys: typing.Set[str] = getattr(typed_dict, '__required_keys__', set())
    fields: typing.Dict[str, core_schema.TypedDictField] = {}

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

            field_type = evaluate_forwardref(field_type)  # type: ignore

        if schema is None:
            if get_origin(field_type) == Required:
                required = True
                field_type = field_type.__args__[0]
            if get_origin(field_type) == NotRequired:
                required = False
                field_type = field_type.__args__[0]

            schema = generate_schema(field_type)

        fields[field_name] = {'schema': schema, 'required': required}

    return core_schema.TypedDictSchema(type='typed-dict', fields=fields, extra_behavior='forbid')


def generic_collection_schema(obj: Any) -> core_schema.Schema:
    """
    Generate schema for List, Set etc. - where the schema includes `items_schema`

    e.g. `list[int]`.
    """
    return {
        'type': obj.__name__.lower(),
        'items_schema': generate_schema(get_args(obj)[0]),
    }  # type: ignore[misc,return-value]


def tuple_schema(tuple_type: Any) -> core_schema.Schema:
    """
    Generate schema for a Tuple, e.g. `tuple[int, str]` or `tuple[int, ...]`.
    """
    params = get_args(tuple_type)
    if params[-1] is Ellipsis:
        if len(params) == 2:
            sv = core_schema.TupleVariableSchema(type='tuple', mode='variable', items_schema=generate_schema(params[0]))
            return sv

        # not sure this case is valid in python, but may as well support it here since pydantic-core does
        *items_schema, extra_schema = params
        return {
            'type': 'tuple',
            'mode': 'positional',
            'items_schema': [generate_schema(p) for p in items_schema],
            'extra_schema': generate_schema(extra_schema),
        }
    else:
        sp = core_schema.TuplePositionalSchema(
            type='tuple',
            mode='positional',
            items_schema=[generate_schema(p) for p in params],
        )
        return sp


def dict_schema(dict_type: Any) -> core_schema.DictSchema:
    """
    Generate schema for a Dict, e.g. `dict[str, int]`.
    """
    arg0, arg1 = get_args(dict_type)
    return core_schema.DictSchema(
        type='dict',
        keys_schema=generate_schema(arg0),
        values_schema=generate_schema(arg1),
    )


def type_schema(type_: Any) -> core_schema.IsInstanceSchema:
    """
    Generate schema for a Type, e.g. `Type[int]`.
    """
    type_param = get_args(type_)[0]
    if type_param == Any:
        return core_schema.IsInstanceSchema(type='is-instance', class_=type)
    else:
        return core_schema.IsInstanceSchema(type='is-instance', class_=type_param)
