"""
Convert python types to pydantic-core schema.

We probably want to rename this to something more descriptive, but I'll leave it like this
until I'm sure what it does.
"""
from __future__ import annotations as _annotations

import collections.abc
import dataclasses
import re
import typing
from typing import TYPE_CHECKING, Any

from annotated_types import BaseMetadata, GroupedMetadata
from pydantic_core import PydanticCustomError, PydanticKindError, core_schema
from typing_extensions import get_args, is_typeddict

from ..fields import FieldInfo, Undefined
from ._fields import CustomMetadata, CustomValidator, PydanticMetadata
from ._typing_extra import (
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
from ._validation_functions import ValidationFunctions, Validator

if TYPE_CHECKING:
    from ..config import BaseConfig

__all__ = 'generate_config', 'generate_schema', 'model_fields_schema'


def model_fields_schema(
    ref: str, fields: dict[str, FieldInfo], validator_functions: ValidationFunctions
) -> core_schema.CoreSchema:
    schema: core_schema.CoreSchema = core_schema.typed_dict_schema(
        {k: generate_field_schema(k, v, validator_functions) for k, v in fields.items()},
        ref=ref,
        return_fields_set=True,
    )
    schema = apply_validators(schema, validator_functions.get_root_validators())
    return schema


def generate_config(config: type[BaseConfig]) -> core_schema.CoreConfig:
    return core_schema.CoreConfig(
        typed_dict_extra_behavior=config.extra.value,
        allow_inf_nan=config.allow_inf_nan,
        populate_by_name=config.allow_population_by_field_name,
        str_strip_whitespace=config.anystr_strip_whitespace,
        str_to_lower=config.anystr_lower,
        str_to_upper=config.anystr_upper,
    )


def generate_schema(obj: type[Any] | str | dict[str, Any]) -> core_schema.CoreSchema:  # noqa: C901 (ignore complexity)
    """
    Recursively generate a pydantic-core schema for any supported python type.
    """
    if isinstance(obj, str):
        return {'type': str}
    elif isinstance(obj, dict):
        # we assume this is already a valid schema
        return obj  # type: ignore[return-value]
    elif obj in (bool, int, float, str, bytes, list, set, frozenset, tuple, dict):
        return {'type': obj.__name__}
    elif obj is Any or obj is object:
        return {'type': 'any'}
    elif obj is None or obj is NoneType:
        return {'type': 'none'}
    elif obj == type:
        return core_schema.is_instance_schema(type)
    elif is_callable_type(obj):
        return {'type': 'callable'}
    elif is_literal_type(obj):
        return literal_schema(obj)
    elif is_typeddict(obj):
        return type_dict_schema(obj)
    elif isinstance(obj, typing.NewType):
        return generate_schema(obj.__supertype__)
    elif obj == re.Pattern:
        return pattern_schema(obj)

    std_schema = std_types_schema(obj)
    if std_schema is not None:
        return std_schema

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
    elif issubclass(origin, typing.Annotated):
        return annotated_schema(obj)
    elif issubclass(origin, (typing.List, typing.Set, typing.FrozenSet)):
        return generic_collection_schema(obj)
    elif issubclass(origin, typing.Tuple):  # type: ignore[arg-type]
        return tuple_schema(obj)
    elif issubclass(origin, typing.Dict):
        return dict_schema(obj)
    elif issubclass(origin, typing.Type):  # type: ignore[arg-type]
        return type_schema(obj)
    elif issubclass(origin, typing.Deque):
        from ._std_validators import deque_schema

        return deque_schema(obj)
    elif issubclass(origin, typing.OrderedDict):
        from ._std_validators import ordered_dict_schema

        return ordered_dict_schema(obj)
    elif issubclass(origin, typing.Sequence):
        return sequence_schema(obj)
    elif issubclass(origin, typing.MutableSet):
        raise PydanticSchemaGenerationError('Unable to generate pydantic-core schema MutableSet TODO.')
    elif issubclass(origin, (typing.Iterable, collections.abc.Iterable)):
        return iterable_schema(obj)
    elif issubclass(origin, (re.Pattern, typing.Pattern)):
        return pattern_schema(obj)
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
    schema = generate_schema(field.annotation)
    schema = apply_constraints(schema, field.constraints)

    required = False
    if field.default_factory:
        schema = core_schema.with_default_schema(schema, default_factory=field.default_factory)
    elif field.default is Undefined:
        required = True
    else:
        schema = core_schema.with_default_schema(schema, default=field.default)

    schema = apply_validators(schema, validator_functions.get_field_validators(name))
    field_schema = core_schema.typed_dict_field(schema, required=required)
    if field.alias is not None:
        field_schema['alias'] = field.alias
    return field_schema


def apply_validators(schema: core_schema.CoreSchema, validators: list[Validator]) -> core_schema.CoreSchema:
    """
    Apply validators to a schema.
    """
    for validator in validators:
        assert validator.sub_path is None, 'validator.sub_path is not yet supported'
        function = typing.cast(typing.Callable[..., Any], validator.function)
        if validator.mode == 'plain':
            schema = core_schema.function_plain_schema(function)
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


def union_schema(union_type: Any) -> core_schema.CoreSchema:
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
        s = core_schema.union_schema(*choices)

    if nullable:
        s = core_schema.nullable_schema(s)
    return s


def annotated_schema(annotated_type: Any) -> core_schema.CoreSchema:
    """
    Generate schema for an Annotated type, e.g. `Annotated[int, Field(...)]` or `Annotated[int, Gt(0)]`.
    """
    args = get_args(annotated_type)
    schema = generate_schema(args[0])
    return apply_constraints(schema, args[1:])


def apply_constraints(schema: core_schema.CoreSchema, constraints: list[Any]) -> core_schema.CoreSchema:
    for c in constraints:
        c_get_schema = getattr(c, '__get_pydantic_validation_schema__', None)
        if c_get_schema is not None:
            schema = c_get_schema(schema)
            continue
        c_schema = getattr(c, '__pydantic_validation_schema__', None)
        if c_schema is not None:
            schema = c_schema
            continue

        if isinstance(c, GroupedMetadata):
            # GroupedMetadata yields constraints
            schema = apply_constraints(schema, c)
            continue

        if isinstance(c, CustomMetadata):
            constraints_dict = c.__dict__
        elif isinstance(c, (BaseMetadata, PydanticMetadata)):
            constraints_dict = dataclasses.asdict(c)
        elif issubclass(c, PydanticMetadata):
            constraints_dict = {k: v for k, v in vars(c).items() if not k.startswith('_')}
        else:
            raise PydanticSchemaGenerationError(
                'Constraints must be subclasses of annotated_types.BaseMetadata or PydanticMetadata '
                'or a subclass of PydanticMetadata'
            )

        # TODO we need a way to remove constraints which this line currently prevents
        constraints_dict = {k: v for k, v in constraints_dict.items() if v is not None}
        if constraints_dict:
            extra: CustomValidator | dict[str, Any] | None = schema.get('extra')
            if extra is None:
                schema.update(**constraints_dict)
            else:
                if isinstance(extra, dict):
                    update_schema_function = extra['__pydantic_update_schema__']
                else:
                    update_schema_function = extra.__pydantic_update_schema__

                new_schema = update_schema_function(schema, **constraints_dict)
                if new_schema is not None:
                    schema = new_schema
    return schema


def literal_schema(literal_type: Any) -> core_schema.LiteralSchema:
    """
    Generate schema for a Literal.
    """
    expected = all_literal_values(literal_type)
    assert expected, f'literal "expected" cannot be empty, obj={literal_type}'
    return core_schema.literal_schema(*expected)


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

    return core_schema.typed_dict_schema(fields, extra_behavior='forbid')


def generic_collection_schema(obj: Any) -> core_schema.CoreSchema:
    """
    Generate schema for List, Set etc. - where the schema includes `items_schema`

    e.g. `list[int]`.
    """
    try:
        name = obj.__name__
    except AttributeError:
        name = get_origin(obj).__name__  # type: ignore[union-attr]

    schema = {'type': name.lower()}
    try:
        arg = get_args(obj)[0]
    except IndexError:
        pass
    else:
        schema['items_schema'] = generate_schema(arg)
    return schema  # type: ignore[misc,return-value]


def tuple_schema(tuple_type: Any) -> core_schema.CoreSchema:
    """
    Generate schema for a Tuple, e.g. `tuple[int, str]` or `tuple[int, ...]`.
    """
    params = get_args(tuple_type)
    if not params:
        return core_schema.tuple_variable_schema()

    if params[-1] is Ellipsis:
        if len(params) == 2:
            sv = core_schema.tuple_variable_schema(generate_schema(params[0]))
            return sv

        # not sure this case is valid in python, but may as well support it here since pydantic-core does
        *items_schema, extra_schema = params
        return core_schema.tuple_positional_schema(
            *[generate_schema(p) for p in items_schema], extra_schema=generate_schema(extra_schema)
        )
    else:
        return core_schema.tuple_positional_schema(*[generate_schema(p) for p in params])


def dict_schema(dict_type: Any) -> core_schema.DictSchema:
    """
    Generate schema for a Dict, e.g. `dict[str, int]`.
    """
    try:
        arg0, arg1 = get_args(dict_type)
    except ValueError:
        return core_schema.dict_schema()
    else:
        return core_schema.dict_schema(
            keys_schema=generate_schema(arg0),
            values_schema=generate_schema(arg1),
        )


def type_schema(type_: Any) -> core_schema.IsInstanceSchema:
    """
    Generate schema for a Type, e.g. `Type[int]`.
    """
    type_param = get_args(type_)[0]
    if type_param == Any:
        return core_schema.is_instance_schema(type)
    else:
        return core_schema.is_instance_schema(type_param)


def sequence_validator(v: Any, *, validator, **kwargs):
    if not isinstance(v, typing.Sequence):
        raise PydanticKindError('is_instance_of', {'class': 'Sequence'})

    value_type = type(v)
    v_list = validator(v)
    if issubclass(value_type, str):
        try:
            return ''.join(v_list)
        except TypeError:
            # can happen if you pass a string like '123' to `Sequence[int]`
            raise PydanticKindError('str_type')
    elif issubclass(value_type, bytes):
        try:
            return b''.join(v_list)
        except TypeError:
            # can happen if you pass a string like '123' to `Sequence[int]`
            raise PydanticKindError('bytes_type')
    elif issubclass(value_type, range):
        # return the list as we probably can't re-create the range
        return v_list
    else:
        return value_type(v_list)


def sequence_schema(sequence_type: Any) -> core_schema.FunctionWrapSchema:
    """
    Generate schema for a Sequence, e.g. `Sequence[int]`.
    """
    arg0 = get_args(sequence_type)[0]
    return core_schema.function_wrap_schema(
        sequence_validator,
        core_schema.list_schema(generate_schema(arg0), allow_any_iter=True),
    )


def iterable_any_validator(v: Any, **_kwargs: Any) -> typing.Iterable[Any]:
    try:
        return iter(v)
    except TypeError:
        raise PydanticCustomError('iterable_type', 'Input should be a valid iterable')


def validate_yield(
    iterable: typing.Iterable[Any], validator: typing.Callable[[Any], Any]
) -> typing.Generator[Any, None, None]:
    for item in iterable:
        yield validator(item)


def iterable_type_validator(
    v: Any, *, validator: typing.Callable[[Any], Any], **_kwargs: Any
) -> typing.Generator[Any, None, None]:
    try:
        iterable = iter(v)
    except TypeError:
        raise PydanticCustomError('iterable_type', 'Input should be a valid iterable')
    return validate_yield(iterable, validator)


def iterable_schema(type_: Any) -> core_schema.FunctionSchema | core_schema.FunctionPlainSchema:
    """
    Generate a schema for an `Iterable`, not
    """
    param = get_args(type_)[0]
    if param == Any:
        return core_schema.function_plain_schema(iterable_any_validator)
    else:
        schema = generate_schema(param)
        return core_schema.function_wrap_schema(iterable_type_validator, schema)


def pattern_schema(pattern_type: Any) -> core_schema.CoreSchema:
    from . import _validators

    if pattern_type == typing.Pattern or pattern_type == re.Pattern:
        # bare type
        return core_schema.function_plain_schema(_validators.pattern_either_validator)

    param = get_args(pattern_type)[0]
    if param == str:
        return core_schema.function_plain_schema(_validators.pattern_str_validator)
    elif param == bytes:
        return core_schema.function_plain_schema(_validators.pattern_bytes_validator)
    else:
        raise PydanticSchemaGenerationError(f'Unable to generate pydantic-core schema for {pattern_type!r}.')


def std_types_schema(obj: Any) -> core_schema.CoreSchema | None:
    """
    Generate schema for types in the standard library.
    """
    if not isinstance(obj, type):
        return None

    # Import here to avoid the extra import time earlier since _std_validators imports lots of things globally
    from ._std_validators import SCHEMA_LOOKUP

    # instead of iterating over a list and calling is_instance, this should be somewhat faster,
    # especially as it should catch most types on the first iteration
    # (same as we do/used to do in json encoding)
    for base in obj.__mro__[:-1]:
        try:
            encoder = SCHEMA_LOOKUP[base]
        except KeyError:
            continue
        return encoder(obj)
