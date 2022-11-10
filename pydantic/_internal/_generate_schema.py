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
from typing_extensions import Annotated, Literal, get_args, get_origin, is_typeddict

from ..errors import PydanticSchemaGenerationError
from ..fields import FieldInfo
from . import _fields, _typing_extra
from ._validation_functions import ValidationFunctions, Validator

if TYPE_CHECKING:
    from ..main import BaseModel

__all__ = 'model_fields_schema', 'GenerateSchema', 'generate_config'


def model_fields_schema(
    ref: str,
    fields: dict[str, FieldInfo],
    validator_functions: ValidationFunctions,
    arbitrary_types: bool,
    types_namespace: dict[str, Any] | None,
) -> core_schema.CoreSchema:
    """
    Generate schema for the fields of a pydantic model, this is slightly different to the schema for the model itself,
    since this is typed_dict schema which is used to create the model.
    """
    schema_generator = GenerateSchema(arbitrary_types, types_namespace)
    schema: core_schema.CoreSchema = core_schema.typed_dict_schema(
        {k: schema_generator.generate_field_schema(k, v, validator_functions) for k, v in fields.items()},
        ref=ref,
        return_fields_set=True,
    )
    schema = apply_validators(schema, validator_functions.get_root_validators())
    return schema


def generate_config(cls: type[BaseModel]) -> core_schema.CoreConfig:
    """
    Create a pydantic-core config from a pydantic config.
    """
    config = cls.__config__
    return core_schema.CoreConfig(
        title=config.title or cls.__name__,
        typed_dict_extra_behavior=config.extra.value,
        allow_inf_nan=config.allow_inf_nan,
        populate_by_name=config.allow_population_by_field_name,
        str_strip_whitespace=config.anystr_strip_whitespace,
        str_to_lower=config.anystr_lower,
        str_to_upper=config.anystr_upper,
        strict=config.strict,
    )


class GenerateSchema:
    __slots__ = 'arbitrary_types', 'types_namespace'

    def __init__(self, arbitrary_types: bool, types_namespace: dict[str, Any] | None):
        self.arbitrary_types = arbitrary_types
        self.types_namespace = types_namespace

    def generate_schema(self, obj: Any) -> core_schema.CoreSchema:  # noqa: C901
        """
        Recursively generate a pydantic-core schema for any supported python type.
        """
        if isinstance(obj, str):
            return {'type': obj}  # type: ignore[return-value,misc]
        elif isinstance(obj, dict):
            # we assume this is already a valid schema
            return obj  # type: ignore[return-value]

        schema_property = getattr(obj, '__pydantic_validation_schema__', None)
        if schema_property is not None:
            return schema_property

        get_schema = getattr(obj, '__get_pydantic_validation_schema__', None)
        if get_schema is not None:
            return get_schema(types_namespace=self.types_namespace)

        if obj is _fields.SelfType:
            # returned value doesn't do anything here since SchemaRef should always be used as an annotated argument
            # which replaces the schema returned here, we return `SelfType` to make debugging easier if
            # this schema is not overwritten
            return obj
        elif obj in {bool, int, float, str, bytes, list, set, frozenset, tuple, dict}:
            return {'type': obj.__name__}  # type: ignore[return-value,misc]
        elif obj is Any or obj is object:
            return core_schema.AnySchema(type='any')
        elif obj is None or obj is _typing_extra.NoneType:
            return core_schema.NoneSchema(type='none')
        elif obj == type:
            return self._type_schema()
        elif _typing_extra.is_callable_type(obj):
            return core_schema.CallableSchema(type='callable')
        elif _typing_extra.is_literal_type(obj):
            return self._literal_schema(obj)
        elif is_typeddict(obj):
            return self._type_dict_schema(obj)
        elif _typing_extra.is_namedtuple(obj):
            return self._namedtuple_schema(obj)
        elif _typing_extra.is_new_type(obj):
            # NewType, can't use isinstance because it fails <3.7
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

        origin = get_origin(obj)
        if origin is None:
            if self.arbitrary_types:
                return core_schema.is_instance_schema(obj)
            else:
                raise PydanticSchemaGenerationError(f'Unable to generate pydantic-core schema for {obj!r}.')

        if _typing_extra.origin_is_union(origin):
            return self._union_schema(obj)
        elif issubclass(origin, Annotated):  # type: ignore[arg-type]
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

    def generate_field_schema(
        self, name: str, field: FieldInfo, validator_functions: ValidationFunctions, *, required: bool = True
    ) -> core_schema.TypedDictField:
        """
        Prepare a TypedDictField to represent a model or typeddict field.
        """
        assert field.annotation is not None, 'field.annotation should not be None when generating a schema'
        schema = self.generate_schema(field.annotation)
        schema = apply_metadata(schema, field.metadata)

        if not field.is_required():
            required = False
            schema = wrap_default(field, schema)

        schema = apply_validators(schema, validator_functions.get_field_validators(name))
        field_schema = core_schema.typed_dict_field(schema, required=required)
        if field.alias is not None:
            field_schema['alias'] = field.alias
        return field_schema

    def _union_schema(self, union_type: Any) -> core_schema.CoreSchema:
        """
        Generate schema for a Union.
        """
        args = get_args(union_type)
        choices = []
        nullable = False
        for arg in args:
            if arg is None or arg is _typing_extra.NoneType:
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
        first_arg, *other_args = get_args(annotated_type)
        schema = self.generate_schema(first_arg)
        return apply_metadata(schema, other_args)

    def _literal_schema(self, literal_type: Any) -> core_schema.LiteralSchema:
        """
        Generate schema for a Literal.
        """
        expected = _typing_extra.all_literal_values(literal_type)
        assert expected, f'literal "expected" cannot be empty, obj={literal_type}'
        return core_schema.literal_schema(*expected)

    def _type_dict_schema(self, typed_dict_cls: Any) -> core_schema.TypedDictSchema:
        """
        Generate schema for a TypedDict.
        """
        try:
            required_keys: typing.FrozenSet[str] = typed_dict_cls.__required_keys__
        except AttributeError:
            raise TypeError('Please use `typing_extensions.TypedDict` instead of `typing.TypedDict`.')

        fields: typing.Dict[str, core_schema.TypedDictField] = {}
        validation_functions = ValidationFunctions(())

        for field_name, annotation in _typing_extra.get_type_hints(typed_dict_cls, include_extras=True).items():
            required = field_name in required_keys

            if get_origin(annotation) == _typing_extra.Required:
                required = True
                annotation = get_args(annotation)[0]
            elif get_origin(annotation) == _typing_extra.NotRequired:
                required = False
                annotation = get_args(annotation)[0]

            field_info = FieldInfo.from_annotation(annotation)
            fields[field_name] = self.generate_field_schema(
                field_name, field_info, validation_functions, required=required
            )

        return core_schema.typed_dict_schema(fields, extra_behavior='forbid')

    def _namedtuple_schema(self, namedtuple_cls: Any) -> core_schema.CallSchema:
        """
        Generate schema for a NamedTuple.
        """
        annotations: dict[str, Any] = _typing_extra.get_type_hints(namedtuple_cls, include_extras=True)
        if not annotations:
            # annotations is empty, happens if namedtuple_cls defined via collections.namedtuple(...)
            annotations = {k: Any for k in namedtuple_cls._fields}

        arguments_schema = core_schema.ArgumentsSchema(
            type='arguments',
            arguments_schema=[
                self._generate_parameter_schema(field_name, annotation)
                for field_name, annotation in annotations.items()
            ],
        )
        return core_schema.call_schema(arguments_schema, namedtuple_cls)

    def _generate_parameter_schema(
        self,
        name: str,
        annotation: type[Any],
        mode: Literal['positional_only', 'positional_or_keyword', 'keyword_only'] | None = None,
    ) -> core_schema.ArgumentsParameter:
        """
        Prepare a ArgumentsParameter to represent a field in a namedtuple, dataclass or function signature.
        """
        field = FieldInfo.from_annotation(annotation)
        assert field.annotation is not None, 'field.annotation should not be None when generating a schema'
        schema = self.generate_schema(field.annotation)
        schema = apply_metadata(schema, field.metadata)

        parameter_schema = core_schema.arguments_parameter(name, schema)
        if mode is not None:
            parameter_schema['mode'] = mode
        if field.alias is not None:
            parameter_schema['alias'] = field.alias
        return parameter_schema

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
            custom_error_type='is_type',
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


def apply_metadata(  # noqa: C901
    schema: core_schema.CoreSchema, annotations: typing.Iterable[Any]
) -> core_schema.CoreSchema:
    """
    Apply arguments from `Annotated` or from `FieldInfo` to a schema.
    """
    for metadata in annotations:
        if metadata is None:
            continue

        metadata_schema = getattr(metadata, '__pydantic_validation_schema__', None)
        if metadata_schema is not None:
            schema = metadata_schema
            continue
        metadata_get_schema = getattr(metadata, '__get_pydantic_validation_schema__', None)
        if metadata_get_schema is not None:
            schema = metadata_get_schema(schema)
            continue

        if isinstance(metadata, GroupedMetadata):
            # GroupedMetadata yields `BaseMetadata`s
            schema = apply_metadata(schema, metadata)
            continue
        elif isinstance(metadata, FieldInfo):
            schema = apply_metadata(schema, metadata.metadata)
            # TODO setting a default here needs to be tested
            schema = wrap_default(metadata, schema)
            continue

        if isinstance(metadata, _fields.PydanticGeneralMetadata):
            metadata_dict = metadata.__dict__
        elif isinstance(metadata, (BaseMetadata, _fields.PydanticMetadata)):
            metadata_dict = dataclasses.asdict(metadata)
        elif isinstance(metadata, type) and issubclass(metadata, _fields.PydanticMetadata):
            # also support PydanticMetadata classes being used without initialisation,
            # e.g. `Annotated[int, Strict]` as well as `Annotated[int, Strict()]`
            metadata_dict = {k: v for k, v in vars(metadata).items() if not k.startswith('_')}
        else:
            raise PydanticSchemaGenerationError(
                'Metadata must be instances of annotated_types.BaseMetadata or PydanticMetadata '
                'or a subclass of PydanticMetadata'
            )

        # TODO we need a way to remove metadata which this line currently prevents
        metadata_dict = {k: v for k, v in metadata_dict.items() if v is not None}
        if not metadata_dict:
            continue

        extra: _fields.CustomValidator | dict[str, Any] | None = schema.get('extra')  # type: ignore[assignment]
        if extra is None:
            if schema['type'] == 'nullable':
                # for nullable schemas, metadata is automatically applied to the inner schema
                # TODO need to do the same for lists, tuples and more
                schema['schema'].update(metadata_dict)
            else:
                schema.update(metadata_dict)  # type: ignore[typeddict-item]
        else:
            if isinstance(extra, dict):
                update_schema_function = extra['__pydantic_update_schema__']
            else:
                update_schema_function = extra.__pydantic_update_schema__

            new_schema = update_schema_function(schema, **metadata_dict)
            if new_schema is not None:
                schema = new_schema
    return schema


def wrap_default(field_info: FieldInfo, schema: core_schema.CoreSchema) -> core_schema.CoreSchema:
    if field_info.default_factory:
        return core_schema.with_default_schema(schema, default_factory=field_info.default_factory)
    elif field_info.default is not _fields.Undefined:
        return core_schema.with_default_schema(schema, default=field_info.default)
    else:
        return schema


def get_first_arg(type_: Any) -> Any:
    """
    Get the first argument from a typing object, e.g. `List[int]` -> `int`, or `Any` if no argument.
    """
    try:
        return get_args(type_)[0]
    except IndexError:
        return Any
