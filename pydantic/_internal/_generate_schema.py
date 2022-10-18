"""
Convert python types to pydantic-core schema.
"""
from __future__ import annotations as _annotations

import collections.abc
import dataclasses
import re
import typing
from typing import TYPE_CHECKING, Any

from annotated_types import BaseMetadata, GroupedMetadata
from pydantic_core import core_schema
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

__all__ = 'model_fields_schema', 'GenerateSchema', 'generate_config'


def model_fields_schema(
    ref: str, fields: dict[str, FieldInfo], validator_functions: ValidationFunctions, arbitrary_types: bool
) -> core_schema.CoreSchema:
    schema_generator = GenerateSchema(arbitrary_types)
    schema: core_schema.CoreSchema = core_schema.typed_dict_schema(
        {k: generate_field_schema(k, v, validator_functions, schema_generator) for k, v in fields.items()},
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


class GenerateSchema:
    __slots__ = ('arbitrary_types',)

    def __init__(self, arbitrary_types: bool):
        self.arbitrary_types = arbitrary_types

    def generate_schema(self, obj: type[Any] | str | dict[str, Any]) -> core_schema.CoreSchema:  # noqa: C901
        """
        Recursively generate a pydantic-core schema for any supported python type.
        """
        if isinstance(obj, str):
            return {'type': obj}  # type: ignore[return-value,misc]
        elif isinstance(obj, dict):
            # we assume this is already a valid schema
            return obj  # type: ignore[return-value]
        elif obj in {bool, int, float, str, bytes, list, set, frozenset, tuple, dict}:
            return {'type': obj.__name__}  # type: ignore[return-value,misc]
        elif obj is Any or obj is object:
            return core_schema.AnySchema(type='any')
        elif obj is None or obj is NoneType:
            return core_schema.NoneSchema(type='none')
        elif obj == type:
            return self._type_schema()
        elif is_callable_type(obj):
            return core_schema.CallableSchema(type='callable')
        elif is_literal_type(obj):
            return self._literal_schema(obj)
        elif is_typeddict(obj):
            return self._type_dict_schema(obj)
        elif isinstance(obj, typing.NewType):
            return self.generate_schema(obj.__supertype__)
        elif obj == re.Pattern:
            return self._pattern_schema(obj)
        elif isinstance(obj, type):
            if issubclass(obj, dict):
                return self._dict_subclass_schema(obj)
            # probably need to take care of other subclasses here

        std_schema = self._std_types_schema(obj)
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
            if self.arbitrary_types:
                return core_schema.is_instance_schema(obj)
            else:
                raise PydanticSchemaGenerationError(f'Unable to generate pydantic-core schema for {obj!r}.')

        if origin_is_union(origin):
            return self._union_schema(obj)
        elif issubclass(origin, typing.Annotated):  # type: ignore[arg-type]
            return self._annotated_schema(obj)
        elif issubclass(origin, (typing.List, typing.Set, typing.FrozenSet)):
            return self._generic_collection_schema(obj)
        elif issubclass(origin, typing.Tuple):  # type: ignore[arg-type]
            return self._tuple_schema(obj)
        elif issubclass(origin, typing.Counter):
            return self._counter_schema(obj)
        elif origin == typing.Dict:
            return self._dict_schema(obj)
        elif issubclass(origin, typing.Dict):
            return self._dict_subclass_schema(obj)
        elif issubclass(origin, typing.Mapping):
            return self._mapping_schema(obj)
        elif issubclass(origin, typing.Type):  # type: ignore[arg-type]
            return self._subclass_schema(obj)
        elif issubclass(origin, typing.Deque):
            from ._std_types_schema import deque_schema

            return deque_schema(self, obj)
        elif issubclass(origin, typing.OrderedDict):
            from ._std_types_schema import ordered_dict_schema

            return ordered_dict_schema(self, obj)
        elif issubclass(origin, typing.Sequence):
            return self._sequence_schema(obj)
        elif issubclass(origin, typing.MutableSet):
            raise PydanticSchemaGenerationError('Unable to generate pydantic-core schema MutableSet TODO.')
        elif issubclass(origin, (typing.Iterable, collections.abc.Iterable)):
            return self._iterable_schema(obj)
        elif issubclass(origin, (re.Pattern, typing.Pattern)):
            return self._pattern_schema(obj)
        else:
            # debug(obj)
            raise PydanticSchemaGenerationError(
                f'Unable to generate pydantic-core schema for {obj!r} (origin={origin!r}).'
            )

    def _union_schema(self, union_type: Any) -> core_schema.CoreSchema:
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
                choices.append(self.generate_schema(arg))

        if len(choices) == 1:
            s = choices[0]
        else:
            s = core_schema.union_schema(*choices)

        if nullable:
            s = core_schema.nullable_schema(s)
        return s

    def _annotated_schema(self, annotated_type: Any) -> core_schema.CoreSchema:
        """
        Generate schema for an Annotated type, e.g. `Annotated[int, Field(...)]` or `Annotated[int, Gt(0)]`.
        """
        args = get_args(annotated_type)
        schema = self.generate_schema(args[0])
        return apply_annotations(schema, args[1:])

    def _literal_schema(self, literal_type: Any) -> core_schema.LiteralSchema:
        """
        Generate schema for a Literal.
        """
        expected = all_literal_values(literal_type)
        assert expected, f'literal "expected" cannot be empty, obj={literal_type}'
        return core_schema.literal_schema(*expected)

    def _type_dict_schema(self, typed_dict: Any) -> core_schema.TypedDictSchema:
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

                schema = self.generate_schema(field_type)

            fields[field_name] = {'schema': schema, 'required': required}

        return core_schema.typed_dict_schema(fields, extra_behavior='forbid')

    def _generic_collection_schema(self, type_: Any) -> core_schema.CoreSchema:
        """
        Generate schema for List, Set etc. - where the schema includes `items_schema`

        e.g. `list[int]`.
        """
        try:
            name = type_.__name__
        except AttributeError:
            name = get_origin(type_).__name__  # type: ignore[union-attr]

        return {  # type: ignore[misc,return-value]
            'type': name.lower(),
            'items_schema': self.generate_schema(get_first_arg(type_)),
        }

    def _tuple_schema(self, tuple_type: Any) -> core_schema.CoreSchema:
        """
        Generate schema for a Tuple, e.g. `tuple[int, str]` or `tuple[int, ...]`.
        """
        params = get_args(tuple_type)
        if not params:
            return core_schema.tuple_variable_schema()

        if params[-1] is Ellipsis:
            if len(params) == 2:
                sv = core_schema.tuple_variable_schema(self.generate_schema(params[0]))
                return sv

            # not sure this case is valid in python, but may as well support it here since pydantic-core does
            *items_schema, extra_schema = params
            return core_schema.tuple_positional_schema(
                *[self.generate_schema(p) for p in items_schema], extra_schema=self.generate_schema(extra_schema)
            )
        else:
            return core_schema.tuple_positional_schema(*[self.generate_schema(p) for p in params])

    def _dict_schema(self, dict_type: Any) -> core_schema.DictSchema:
        """
        Generate schema for a Dict, e.g. `dict[str, int]`.
        """
        try:
            arg0, arg1 = get_args(dict_type)
        except ValueError:
            return core_schema.dict_schema()
        else:
            return core_schema.dict_schema(
                keys_schema=self.generate_schema(arg0),
                values_schema=self.generate_schema(arg1),
            )

    def _dict_subclass_schema(self, dict_subclass: Any) -> core_schema.CoreSchema:
        """
        Generate schema for a subclass of dict or Dict
        """
        try:
            arg0, arg1 = get_args(dict_subclass)
        except ValueError:
            arg0, arg1 = Any, Any

        from ._validators import mapping_validator

        # TODO could do `core_schema.chain_schema(core_schema.is_instance_schema(dict_subclass), ...` in strict mode
        return core_schema.function_wrap_schema(
            mapping_validator,
            core_schema.dict_schema(
                keys_schema=self.generate_schema(arg0),
                values_schema=self.generate_schema(arg1),
            ),
        )

    def _counter_schema(self, counter_type: Any) -> core_schema.CoreSchema:
        """
        Generate schema for `typing.Counter`
        """
        arg = get_first_arg(counter_type)

        from ._validators import construct_counter

        # TODO could do `core_schema.chain_schema(core_schema.is_instance_schema(Counter), ...` in strict mode
        return core_schema.function_after_schema(
            core_schema.dict_schema(
                keys_schema=self.generate_schema(arg),
                values_schema=core_schema.int_schema(),
            ),
            construct_counter,
        )

    def _mapping_schema(self, mapping_type: Any) -> core_schema.CoreSchema:
        """
        Generate schema for a Dict, e.g. `dict[str, int]`.
        """
        try:
            arg0, arg1 = get_args(mapping_type)
        except ValueError:
            return core_schema.is_instance_schema(typing.Mapping, cls_repr='Mapping')
        else:
            from ._validators import mapping_validator

            return core_schema.function_wrap_schema(
                mapping_validator,
                core_schema.dict_schema(
                    keys_schema=self.generate_schema(arg0),
                    values_schema=self.generate_schema(arg1),
                ),
            )

    def _type_schema(self) -> core_schema.CoreSchema:
        return core_schema.custom_error_schema(
            core_schema.is_instance_schema(type),
            custom_error_kind='is_type',
            custom_error_message='Input should be a type',
        )

    def _subclass_schema(self, type_: Any) -> core_schema.CoreSchema:
        """
        Generate schema for a Type, e.g. `Type[int]`.
        """
        type_param = get_first_arg(type_)
        if type_param == Any:
            return self._type_schema()
        else:
            return core_schema.is_subclass_schema(type_param)

    def _sequence_schema(self, sequence_type: Any) -> core_schema.CoreSchema:
        """
        Generate schema for a Sequence, e.g. `Sequence[int]`.
        """
        item_type = get_first_arg(sequence_type)

        if item_type == Any:
            return core_schema.is_instance_schema(typing.Sequence, cls_repr='Sequence')
        else:
            from ._validators import sequence_validator

            return core_schema.chain_schema(
                core_schema.is_instance_schema(typing.Sequence, cls_repr='Sequence'),
                core_schema.function_wrap_schema(
                    sequence_validator,
                    core_schema.list_schema(self.generate_schema(item_type), allow_any_iter=True),
                ),
            )

    def _iterable_schema(self, type_: Any) -> core_schema.GeneratorSchema:
        """
        Generate a schema for an `Iterable`.

        TODO replace with pydantic-core's generator validator.
        """
        item_type = get_first_arg(type_)

        return core_schema.generator_schema(self.generate_schema(item_type))

    def _pattern_schema(self, pattern_type: Any) -> core_schema.CoreSchema:
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

    def _std_types_schema(self, obj: Any) -> core_schema.CoreSchema | None:
        """
        Generate schema for types in the standard library.
        """
        if not isinstance(obj, type):
            return None

        # Import here to avoid the extra import time earlier since _std_validators imports lots of things globally
        from ._std_types_schema import SCHEMA_LOOKUP

        # instead of iterating over a list and calling is_instance, this should be somewhat faster,
        # especially as it should catch most types on the first iteration
        # (same as we do/used to do in json encoding)
        for base in obj.__mro__[:-1]:
            try:
                encoder = SCHEMA_LOOKUP[base]
            except KeyError:
                continue
            return encoder(self, obj)
        return None


def generate_field_schema(
    name: str, field: FieldInfo, validator_functions: ValidationFunctions, schema_generator: GenerateSchema
) -> core_schema.TypedDictField:
    """
    Prepare a TypedDictField to represent a model or typeddict field.
    """
    assert field.annotation is not None, 'field.annotation should not be None when generating a schema'
    schema = schema_generator.generate_schema(field.annotation)
    schema = apply_annotations(schema, field.constraints)

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
        elif validator.mode == 'wrap':
            schema = core_schema.function_wrap_schema(function, schema)
        else:
            schema = core_schema.FunctionSchema(
                type='function',
                mode=validator.mode,
                function=function,
                schema=schema,
            )
    return schema


def apply_annotations(schema: core_schema.CoreSchema, annotations: typing.Iterable[Any]) -> core_schema.CoreSchema:
    """
    Apply arguments to `Annotated` to a schema.
    """
    for c in annotations:
        if c is None:
            continue

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
            schema = apply_annotations(schema, c)
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
            extra: CustomValidator | dict[str, Any] | None = schema.get('extra')  # type: ignore[assignment]
            if extra is None:
                schema.update(constraints_dict)  # type: ignore[typeddict-item]
            else:
                if isinstance(extra, dict):
                    update_schema_function = extra['__pydantic_update_schema__']
                else:
                    update_schema_function = extra.__pydantic_update_schema__

                new_schema = update_schema_function(schema, **constraints_dict)
                if new_schema is not None:
                    schema = new_schema
    return schema


class PydanticSchemaGenerationError(TypeError):
    pass


def get_first_arg(type_: Any) -> Any:
    """
    Get the first argument from a typing object, e.g. `List[int]` -> `int`, or `Any` if no argument.
    """
    try:
        return get_args(type_)[0]
    except IndexError:
        return Any
