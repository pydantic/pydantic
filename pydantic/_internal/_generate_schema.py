"""
Convert python types to pydantic-core schema.
"""
from __future__ import annotations as _annotations

import collections.abc
import dataclasses
import re
import sys
import typing
import warnings
from typing import TYPE_CHECKING, Any, Callable, ForwardRef, Iterable, Mapping, TypeVar, Union

from annotated_types import BaseMetadata, GroupedMetadata
from pydantic_core import SchemaError, SchemaValidator, core_schema
from typing_extensions import Annotated, Literal, get_args, get_origin, is_typeddict

from ..errors import PydanticSchemaGenerationError, PydanticUserError
from ..fields import FieldInfo
from ..json_schema import JsonSchemaMetadata, JsonSchemaValue
from . import _discriminated_union, _typing_extra
from ._core_metadata import CoreMetadataHandler, build_metadata_dict
from ._core_utils import get_type_ref, is_list_like_schema_with_items_schema
from ._decorators import (
    Decorator,
    DecoratorInfos,
    FieldValidatorDecoratorInfo,
    RootValidatorDecoratorInfo,
    SerializerDecoratorInfo,
    ValidatorDecoratorInfo,
)
from ._fields import PydanticGeneralMetadata, PydanticMetadata, Undefined, collect_fields
from ._forward_ref import PydanticForwardRef
from ._generics import replace_types

if TYPE_CHECKING:
    from ..config import ConfigDict
    from ..main import BaseModel
    from ._dataclasses import StandardDataclass

__all__ = 'model_fields_schema', 'dataclass_schema', 'GenerateSchema', 'generate_config', 'get_model_self_schema'


_SUPPORTS_TYPEDDICT = sys.version_info >= (3, 11)


FieldDecoratorInfo = Union[ValidatorDecoratorInfo, FieldValidatorDecoratorInfo, SerializerDecoratorInfo]
FieldDecoratorInfoType = TypeVar('FieldDecoratorInfoType', bound=FieldDecoratorInfo)
AnyFieldDecorator = Union[
    Decorator[ValidatorDecoratorInfo],
    Decorator[FieldValidatorDecoratorInfo],
    Decorator[SerializerDecoratorInfo],
]


def check_validator_fields_against_field_name(
    info: FieldDecoratorInfo,
    field: str,
) -> bool:
    if isinstance(info, ValidatorDecoratorInfo):
        # V1 compat: accept `'*'` as a wildcard that matches all fields
        if info.fields == ('*',):
            return True
    for v_field_name in info.fields:
        if v_field_name == field:
            return True
    return False


def check_validator_fields_exist(decorators: Iterable[AnyFieldDecorator], fields: Iterable[str]) -> None:
    fields = set(fields)
    for dec in decorators:
        if isinstance(dec.info, ValidatorDecoratorInfo) and dec.info.fields == ('*',):
            # V1 compat: accept `'*'` as a wildcard that matches all fields
            continue
        if dec.info.check_fields is False:
            continue
        for field in dec.info.fields:
            if field not in fields:
                raise PydanticUserError(
                    f'Validators defined with incorrect fields: {dec.unwrapped_func.__name__}'
                    " (use check_fields=False if you're inheriting from the model and intended this)"
                )


def filter_field_decorator_info_by_field(
    validator_functions: Iterable[Decorator[FieldDecoratorInfoType]], field: str
) -> list[Decorator[FieldDecoratorInfoType]]:
    return [dec for dec in validator_functions if check_validator_fields_against_field_name(dec.info, field)]


def apply_each_item_validators(
    schema: core_schema.CoreSchema, each_item_validators: list[Decorator[ValidatorDecoratorInfo]]
) -> core_schema.CoreSchema:
    # TODO: remove this V1 compatibility shim once it's deprecated
    # push down any `each_item=True` validators
    # note that this won't work for any Annotated types that get wrapped by a function validator
    # but that's okay because that didn't exist in V1
    if schema['type'] == 'nullable':
        schema['schema'] = apply_each_item_validators(schema['schema'], each_item_validators)
        return schema
    elif is_list_like_schema_with_items_schema(schema):
        inner_schema = schema.get('items_schema', None)
        if inner_schema is None:
            inner_schema = core_schema.any_schema()
        schema['items_schema'] = apply_validators(inner_schema, each_item_validators)
    elif schema['type'] == 'dict':
        # push down any `each_item=True` validators onto dict _values_
        # this is super arbitrary but it's the V1 behavior
        inner_schema = schema.get('values_schema', None)
        if inner_schema is None:
            inner_schema = core_schema.any_schema()
        schema['values_schema'] = apply_validators(inner_schema, each_item_validators)
    elif each_item_validators:
        raise TypeError(
            f"`@validator(..., each_item=True)` cannot be applied to fields with a schema of {schema['type']}"
        )
    return schema


def model_fields_schema(
    model_ref: str,
    fields: dict[str, FieldInfo],
    decorators: DecoratorInfos,
    arbitrary_types: bool,
    types_namespace: dict[str, Any] | None,
    typevars_map: dict[Any, Any] | None,
) -> core_schema.CoreSchema:
    """
    Generate schema for the fields of a pydantic model, this is slightly different to the schema for the model itself.

    This is typed_dict schema which is used to create the model.
    """
    schema_generator = GenerateSchema(arbitrary_types, types_namespace, typevars_map)
    check_validator_fields_exist(
        [*decorators.field_validator.values(), *decorators.serializer.values(), *decorators.validator.values()],
        fields.keys(),
    )
    fields_schema: core_schema.CoreSchema = core_schema.typed_dict_schema(
        {k: schema_generator.generate_td_field_schema(k, v, decorators) for k, v in fields.items()},
        ref=model_ref,
        return_fields_set=True,
    )
    fields_schema = apply_validators(fields_schema, decorators.root_validator.values())
    return fields_schema


def dataclass_schema(
    cls: type[Any],
    ref: str,
    fields: dict[str, FieldInfo],
    decorators: DecoratorInfos,
    arbitrary_types: bool,
    types_namespace: dict[str, Any] | None,
) -> core_schema.CoreSchema:
    """
    Generate schema for a dataclass.
    """
    # TODO add typevars_map argument when we support generic dataclasses
    schema_generator = GenerateSchema(arbitrary_types, types_namespace, None)
    args = [schema_generator.generate_dc_field_schema(k, v, decorators) for k, v in fields.items()]
    has_post_init = hasattr(cls, '__post_init__')
    args_schema = core_schema.dataclass_args_schema(cls.__name__, args, collect_init_only=has_post_init)
    inner_schema = apply_validators(args_schema, decorators.root_validator.values())
    return core_schema.dataclass_schema(cls, inner_schema, post_init=has_post_init, ref=ref)


def generate_config(config: ConfigDict, cls: type[Any]) -> core_schema.CoreConfig:
    """
    Create a pydantic-core config from a pydantic config.
    """
    core_config = core_schema.CoreConfig(
        title=config['title'] or cls.__name__,
        typed_dict_extra_behavior=config['extra'].value,
        allow_inf_nan=config['allow_inf_nan'],
        populate_by_name=config['populate_by_name'],
        str_strip_whitespace=config['str_strip_whitespace'],
        str_to_lower=config['str_to_lower'],
        str_to_upper=config['str_to_upper'],
        strict=config['strict'],
        ser_json_timedelta=config['ser_json_timedelta'],
        ser_json_bytes=config['ser_json_bytes'],
    )
    str_max_length = config.get('str_max_length')
    if str_max_length is not None:
        core_config['str_max_length'] = str_max_length
    str_min_length = config.get('str_min_length')
    if str_min_length is not None:
        core_config['str_min_length'] = str_min_length

    return core_config


class GenerateSchema:
    __slots__ = 'arbitrary_types', 'types_namespace', 'typevars_map', '_recursion_cache'

    def __init__(
        self, arbitrary_types: bool, types_namespace: dict[str, Any] | None, typevars_map: dict[Any, Any] | None
    ):
        self.arbitrary_types = arbitrary_types
        self.types_namespace = types_namespace
        self.typevars_map = typevars_map
        self._recursion_cache: dict[str, core_schema.DefinitionReferenceSchema] = {}

    def generate_schema(self, obj: Any) -> core_schema.CoreSchema:
        schema = self._generate_schema(obj)
        modify_js_function = _get_pydantic_modify_json_schema(obj)
        if modify_js_function is None:
            # Need to do this to handle custom generics:
            if hasattr(obj, '__origin__'):
                modify_js_function = _get_pydantic_modify_json_schema(obj.__origin__)

        CoreMetadataHandler(schema).combine_modify_js_functions(modify_js_function)

        return schema

    def _generate_schema_from_property(self, obj: Any, source: Any) -> core_schema.CoreSchema | None:
        schema_property = getattr(obj, '__pydantic_core_schema__', None)
        if schema_property is not None:
            return schema_property

        get_schema = getattr(obj, '__get_pydantic_core_schema__', None)
        if get_schema is not None:
            # Can return None to tell pydantic not to override
            return get_schema(types_namespace=self.types_namespace, source=source, generator=self)

        return None

    def _generate_schema(self, obj: Any) -> core_schema.CoreSchema:  # noqa: C901
        """
        Recursively generate a pydantic-core schema for any supported python type.
        """
        if isinstance(obj, str):
            return {'type': obj}  # type: ignore[return-value,misc]
        elif isinstance(obj, dict):
            # we assume this is already a valid schema
            return obj  # type: ignore[return-value]

        if isinstance(obj, ForwardRef):
            # we assume that types_namespace has the target of forward references in its scope,
            # but this could fail, for example, if calling Validator on an imported type which contains
            # forward references to other types only defined in the module from which it was imported
            # `Validator(SomeImportedTypeAliasWithAForwardReference)`
            # or the equivalent for BaseModel
            # class Model(BaseModel):
            #   x: SomeImportedTypeAliasWithAForwardReference
            obj = _typing_extra.evaluate_fwd_ref(obj, globalns=None, localns=self.types_namespace)

        from_property = self._generate_schema_from_property(obj, obj)
        if from_property is not None:
            return from_property

        if isinstance(obj, PydanticForwardRef):
            if not obj.deferred_actions:
                return obj.schema
            resolved_model = obj.resolve_model()
            if isinstance(resolved_model, PydanticForwardRef):
                # If you still have a PydanticForwardRef after resolving, it should be deeply nested enough that it will
                # eventually be substituted out. So it is safe to return an invalid schema here.
                # TODO: Replace this with a (new) CoreSchema that, if present at any level, makes validation fail
                return core_schema.none_schema(
                    metadata={'invalid': True, 'pydantic_debug_self_schema': resolved_model.schema}
                )
            else:
                return get_model_self_schema(resolved_model)[0]

        try:
            if obj in {bool, int, float, str, bytes, list, set, frozenset, dict}:
                # Note: obj may fail to be hashable if it has an unhashable annotation
                return {'type': obj.__name__}
            elif obj is tuple:
                return {'type': 'tuple-variable'}
        except TypeError:  # obj not hashable; can happen due to unhashable annotations
            pass

        if obj is Any or obj is object:
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
            return self._typed_dict_schema(obj)
        elif _typing_extra.is_namedtuple(obj):
            return self._namedtuple_schema(obj)
        elif _typing_extra.is_new_type(obj):
            # NewType, can't use isinstance because it fails <3.7
            return self.generate_schema(obj.__supertype__)
        elif obj == re.Pattern:
            return self._pattern_schema(obj)
        elif isinstance(obj, type):
            if obj is dict:
                return self._dict_schema(obj)
            if issubclass(obj, dict):
                # TODO: We would need to handle generic subclasses of certain typing dict subclasses here
                #   This includes subclasses of typing.Counter, typing.DefaultDict, and typing.OrderedDict
                #   Note also that we may do a better job of handling typing.DefaultDict by inspecting its arguments.
                return self._dict_subclass_schema(obj)
            # probably need to take care of other subclasses here
        elif isinstance(obj, typing.TypeVar):
            return self._unsubstituted_typevar_schema(obj)

        # TODO: _std_types_schema iterates over the __mro__ looking for an expected schema.
        #   This will catch subclasses of typing.Deque, preventing us from properly supporting user-defined
        #   generic subclasses. (In principle this would also catch typing.OrderedDict, but that is currently
        #   already getting caught in the `issubclass(obj, dict):` check above.
        std_schema = self._std_types_schema(obj)
        if std_schema is not None:
            return std_schema

        origin = get_origin(obj)
        if origin is None:
            if self.arbitrary_types:
                return core_schema.is_instance_schema(obj)
            else:
                raise PydanticSchemaGenerationError(
                    f'Unable to generate pydantic-core schema for {obj!r}. '
                    f'Setting `arbitrary_types_allowed=True` in the model_config may prevent this error.'
                )

        from_property = self._generate_schema_from_property(origin, obj)
        if from_property is not None:
            return from_property

        if _typing_extra.origin_is_union(origin):
            return self._union_schema(obj)
        elif issubclass(origin, Annotated):  # type: ignore[arg-type]
            return self._annotated_schema(obj)
        elif issubclass(origin, typing.List):
            return self._generic_collection_schema(list, obj, origin)
        elif issubclass(origin, typing.Set):
            return self._generic_collection_schema(set, obj, origin)
        elif issubclass(origin, typing.FrozenSet):
            return self._generic_collection_schema(frozenset, obj, origin)
        elif issubclass(origin, typing.Tuple):  # type: ignore[arg-type]
            # TODO: To support generic subclasses of typing.Tuple, we need to better-introspect the args to origin
            return self._tuple_schema(obj)
        elif issubclass(origin, typing.Counter):
            # Subclasses of typing.Counter may be handled as subclasses of dict; see note above
            return self._counter_schema(obj)
        elif origin in (typing.Dict, dict):
            return self._dict_schema(obj)
        elif issubclass(origin, typing.Dict):
            # Subclasses of typing.Dict may be handled as subclasses of dict; see note above
            return self._dict_subclass_schema(obj)
        elif issubclass(origin, typing.Mapping):
            # Because typing.Mapping does not have a specified `__init__` signature, we don't validate into subclasses
            return self._mapping_schema(obj)
        elif issubclass(origin, typing.Type):  # type: ignore[arg-type]
            return self._subclass_schema(obj)
        elif issubclass(origin, typing.Deque):
            from ._std_types_schema import deque_schema

            return deque_schema(self, obj)
        elif issubclass(origin, typing.OrderedDict):
            # Subclasses of typing.OrderedDict may be handled as subclasses of dict; see note above
            from ._std_types_schema import ordered_dict_schema

            return ordered_dict_schema(self, obj)
        elif issubclass(origin, typing.Sequence):
            # Because typing.Sequence does not have a specified `__init__` signature, we don't validate into subclasses
            return self._sequence_schema(obj)
        elif issubclass(origin, typing.MutableSet):
            raise PydanticSchemaGenerationError('Unable to generate pydantic-core schema MutableSet TODO.')
        elif issubclass(origin, (typing.Iterable, collections.abc.Iterable)):
            # Because typing.Iterable does not have a specified `__init__` signature, we don't validate into subclasses
            return self._iterable_schema(obj)
        elif issubclass(origin, (re.Pattern, typing.Pattern)):
            return self._pattern_schema(obj)
        else:
            if self.arbitrary_types and isinstance(origin, type):
                return core_schema.is_instance_schema(origin)
            else:
                raise PydanticSchemaGenerationError(
                    f'Unable to generate pydantic-core schema for {obj!r} (origin={origin!r}). '
                    f'Setting `arbitrary_types_allowed=True` in the model_config may prevent this error.'
                )

    def generate_td_field_schema(
        self,
        name: str,
        field_info: FieldInfo,
        decorators: DecoratorInfos,
        *,
        required: bool = True,
    ) -> core_schema.TypedDictField:
        """
        Prepare a TypedDictField to represent a model or typeddict field.
        """
        assert field_info.annotation is not None, 'field_info.annotation should not be None when generating a schema'
        schema = self.generate_schema(field_info.annotation)

        if field_info.discriminator is not None:
            schema = _discriminated_union.apply_discriminator(schema, field_info.discriminator)
        schema = apply_annotations(schema, field_info.metadata)

        # TODO: remove this V1 compatibility shim once it's deprecated
        # push down any `each_item=True` validators
        # note that this won't work for any Annotated types that get wrapped by a function validator
        # but that's okay because that didn't exist in V1
        this_field_validators = filter_field_decorator_info_by_field(decorators.validator.values(), name)
        each_item_validators = [v for v in this_field_validators if v.info.each_item is True]
        this_field_validators = [v for v in this_field_validators if v not in each_item_validators]
        schema = apply_each_item_validators(schema, each_item_validators)

        schema = apply_validators(schema, filter_field_decorator_info_by_field(this_field_validators, name))
        schema = apply_validators(
            schema, filter_field_decorator_info_by_field(decorators.field_validator.values(), name)
        )

        # the default validator needs to go outside of any other validators
        # so that it is the topmost validator for the typed-dict-field validator
        # which uses it to check if the field has a default value or not
        if not field_info.is_required():
            required = False
            schema = wrap_default(field_info, schema)

        schema = apply_serializers(schema, filter_field_decorator_info_by_field(decorators.serializer.values(), name))
        misc = JsonSchemaMetadata(
            title=field_info.title,
            description=field_info.description,
            examples=field_info.examples,
            extra_updates=field_info.json_schema_extra,
        )
        metadata = build_metadata_dict(js_metadata=misc)
        field_schema = core_schema.typed_dict_field(schema, required=required, metadata=metadata)
        if field_info.alias is not None:
            field_schema['validation_alias'] = field_info.alias
            field_schema['serialization_alias'] = field_info.alias
        if field_info.exclude:
            field_schema['serialization_exclude'] = True
        return field_schema

    def generate_dc_field_schema(
        self,
        name: str,
        field_info: FieldInfo,
        decorators: DecoratorInfos,
    ) -> core_schema.DataclassField:
        """
        Prepare a DataclassField to represent the parameter/field, of a dataclass
        """
        assert field_info.annotation is not None, 'field.annotation should not be None when generating a schema'
        schema = self.generate_schema(field_info.annotation)
        schema = apply_annotations(schema, field_info.metadata)

        if not field_info.is_required():
            schema = wrap_default(field_info, schema)

        schema = apply_validators(
            schema, filter_field_decorator_info_by_field(decorators.field_validator.values(), name)
        )
        schema = apply_validators(schema, filter_field_decorator_info_by_field(decorators.validator.values(), name))
        schema = apply_serializers(schema, filter_field_decorator_info_by_field(decorators.serializer.values(), name))
        # use `or None` to so the core schema is minimal
        return core_schema.dataclass_field(
            name,
            schema,
            init_only=field_info.init_var or None,
            kw_only=None if field_info.kw_only else False,
            serialization_exclude=field_info.exclude or None,
            validation_alias=field_info.alias,
            serialization_alias=field_info.alias,
        )

    def _union_schema(self, union_type: Any) -> core_schema.CoreSchema:
        """
        Generate schema for a Union.
        """
        args = get_args(union_type)
        choices: list[core_schema.CoreSchema] = []
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
        return apply_annotations(schema, other_args)

    def _literal_schema(self, literal_type: Any) -> core_schema.LiteralSchema:
        """
        Generate schema for a Literal.
        """
        expected = _typing_extra.all_literal_values(literal_type)
        assert expected, f'literal "expected" cannot be empty, obj={literal_type}'
        return core_schema.literal_schema(*expected)

    def _typed_dict_schema(
        self, typed_dict_cls: Any
    ) -> core_schema.TypedDictSchema | core_schema.DefinitionReferenceSchema:
        """
        Generate schema for a TypedDict.

        It is not possible to track required/optional keys in TypedDict without __required_keys__
        since TypedDict.__new__ erases the base classes (it replaces them with just `dict`)
        and thus we can track usage of total=True/False
        __required_keys__ was added in Python 3.9
        (https://github.com/miss-islington/cpython/blob/1e9939657dd1f8eb9f596f77c1084d2d351172fc/Doc/library/typing.rst?plain=1#L1546-L1548)
        however it is buggy
        (https://github.com/python/typing_extensions/blob/ac52ac5f2cb0e00e7988bae1e2a1b8257ac88d6d/src/typing_extensions.py#L657-L666).
        Hence to avoid creating validators that do not do what users expect we only
        support typing.TypedDict on Python >= 3.11 or typing_extension.TypedDict on all versions
        """
        if not _SUPPORTS_TYPEDDICT and type(typed_dict_cls).__module__ == 'typing':
            raise PydanticUserError(
                'Please use `typing_extensions.TypedDict` instead of `typing.TypedDict` on Python < 3.11.'
            )

        required_keys: frozenset[str] = typed_dict_cls.__required_keys__

        fields: dict[str, core_schema.TypedDictField] = {}

        obj_ref = f'{typed_dict_cls.__module__}.{typed_dict_cls.__qualname__}:{id(typed_dict_cls)}'
        if obj_ref in self._recursion_cache:
            return self._recursion_cache[obj_ref]
        else:
            recursive_schema = core_schema.definition_reference_schema(obj_ref)
            self._recursion_cache[obj_ref] = recursive_schema

        for field_name, annotation in _typing_extra.get_type_hints(typed_dict_cls, include_extras=True).items():
            required = field_name in required_keys

            if get_origin(annotation) == _typing_extra.Required:
                required = True
                annotation = get_args(annotation)[0]
            elif get_origin(annotation) == _typing_extra.NotRequired:
                required = False
                annotation = get_args(annotation)[0]

            if self.typevars_map is not None:
                annotation = replace_types(annotation, self.typevars_map)

            field_info = FieldInfo.from_annotation(annotation)
            fields[field_name] = self.generate_td_field_schema(
                field_name, field_info, DecoratorInfos(), required=required
            )

        typed_dict_ref = get_type_ref(typed_dict_cls)
        return core_schema.typed_dict_schema(
            fields,
            extra_behavior='forbid',
            ref=typed_dict_ref,
            metadata=build_metadata_dict(js_metadata=JsonSchemaMetadata(title=typed_dict_cls.__name__)),
        )

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
            metadata=build_metadata_dict(js_metadata=JsonSchemaMetadata(source_class=namedtuple_cls)),
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
        schema = apply_annotations(schema, field.metadata)

        parameter_schema = core_schema.arguments_parameter(name, schema)
        if mode is not None:
            parameter_schema['mode'] = mode
        if field.alias is not None:
            parameter_schema['alias'] = field.alias
        return parameter_schema

    def _generic_collection_schema(
        self, parent_type: type[Any], type_: type[Any], origin: type[Any]
    ) -> core_schema.CoreSchema:
        """
        Generate schema for List, Set, and FrozenSet, possibly parameterized.

        :param parent_type: Either `list`, `set` or `frozenset` - the builtin type
        :param type_: The type of the collection, e.g. `List[int]` or `List`, or a subclass of one of them
        :param origin: The origin type
        """
        schema: core_schema.CoreSchema = {  # type: ignore[misc,assignment]
            'type': parent_type.__name__.lower(),
            'items_schema': self.generate_schema(get_first_arg(type_)),
        }

        if origin == parent_type:
            return schema
        else:
            # Ensure the validated value is converted back to the specific subclass type
            # NOTE: we might have better performance by using a tuple or list validator for the schema here,
            # but if you care about performance, you can define your own schema.
            # We should optimize for compatibility, not performance in this case
            return core_schema.general_after_validator_function(
                lambda __input_value, __info: type_(__input_value), schema
            )

    def _tuple_schema(self, tuple_type: Any) -> core_schema.CoreSchema:
        """
        Generate schema for a Tuple, e.g. `tuple[int, str]` or `tuple[int, ...]`.
        """
        params = get_args(tuple_type)
        # NOTE: subtle difference: `tuple[()]` gives `params=()`, whereas `typing.Tuple[()]` gives `params=((),)`
        if not params:
            if tuple_type == typing.Tuple:
                return core_schema.tuple_variable_schema()
            else:
                # special case for `tuple[()]` which means `tuple[]` - an empty tuple
                return core_schema.tuple_positional_schema()
        elif params[-1] is Ellipsis:
            if len(params) == 2:
                sv = core_schema.tuple_variable_schema(self.generate_schema(params[0]))
                return sv

            # not sure this case is valid in python, but may as well support it here since pydantic-core does
            *items_schema, extra_schema = params
            return core_schema.tuple_positional_schema(
                *[self.generate_schema(p) for p in items_schema], extra_schema=self.generate_schema(extra_schema)
            )
        elif len(params) == 1 and params[0] == ():
            # special case for `Tuple[()]` which means `Tuple[]` - an empty tuple
            return core_schema.tuple_positional_schema()
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
        return core_schema.general_wrap_validator_function(
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
        return core_schema.general_after_validator_function(
            construct_counter,
            core_schema.dict_schema(
                keys_schema=self.generate_schema(arg),
                values_schema=core_schema.int_schema(),
            ),
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

            return core_schema.general_wrap_validator_function(
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
        elif isinstance(type_param, typing.TypeVar):
            if type_param.__bound__:
                return core_schema.is_subclass_schema(type_param.__bound__)
            elif type_param.__constraints__:
                return core_schema.union_schema(
                    *[self.generate_schema(typing.Type[c]) for c in type_param.__constraints__]
                )
            else:
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
                core_schema.general_wrap_validator_function(
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
        from . import _serializers, _validators

        metadata = build_metadata_dict(js_metadata={'source_class': pattern_type, 'type': 'string', 'format': 'regex'})
        ser = core_schema.general_plain_serializer_function_ser_schema(
            _serializers.pattern_serializer, json_return_type='str'
        )
        if pattern_type == typing.Pattern or pattern_type == re.Pattern:
            # bare type
            return core_schema.general_plain_validator_function(
                _validators.pattern_either_validator, serialization=ser, metadata=metadata
            )

        param = get_args(pattern_type)[0]
        if param == str:
            return core_schema.general_plain_validator_function(
                _validators.pattern_str_validator, serialization=ser, metadata=metadata
            )
        elif param == bytes:
            return core_schema.general_plain_validator_function(
                _validators.pattern_bytes_validator, serialization=ser, metadata=metadata
            )
        else:
            raise PydanticSchemaGenerationError(f'Unable to generate pydantic-core schema for {pattern_type!r}.')

    def _std_types_schema(self, obj: Any) -> core_schema.CoreSchema | None:
        """
        Generate schema for types in the standard library.
        """
        if not isinstance(obj, type):
            return None

        # Import here to avoid the extra import time earlier since _std_validators imports lots of things globally
        import dataclasses

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
        if dataclasses.is_dataclass(obj):
            return self._dataclass_schema(obj)
        return None

    def _dataclass_schema(self, dataclass: type[StandardDataclass]) -> core_schema.CoreSchema:
        """
        Generate schema for a dataclass.
        """
        # FIXME we need a way to make sure kw_only info is propagated through to fields
        fields, _ = collect_fields(
            dataclass, dataclass.__bases__, self.types_namespace, dc_kw_only=True, is_dataclass=True
        )

        return dataclass_schema(
            dataclass,
            get_type_ref(dataclass),
            fields,
            # FIXME we need to get validators and serializers from the dataclasses
            DecoratorInfos(),
            self.arbitrary_types,
            self.types_namespace,
        )

    def _unsubstituted_typevar_schema(self, typevar: typing.TypeVar) -> core_schema.CoreSchema:
        assert isinstance(typevar, typing.TypeVar)
        if typevar.__bound__:
            schema = self.generate_schema(typevar.__bound__)
        elif typevar.__constraints__:
            schema = self._union_schema(typing.Union[typevar.__constraints__])
        else:
            schema = core_schema.AnySchema(type='any')
        return schema


_VALIDATOR_F_MATCH: Mapping[
    tuple[str, bool], Callable[[Callable[..., Any], core_schema.CoreSchema], core_schema.CoreSchema]
] = {
    ('before', True): core_schema.field_before_validator_function,
    ('after', True): core_schema.field_after_validator_function,
    ('plain', True): lambda f, _: core_schema.field_plain_validator_function(f),
    ('wrap', True): core_schema.field_wrap_validator_function,
    ('before', False): core_schema.general_before_validator_function,
    ('after', False): core_schema.general_after_validator_function,
    ('plain', False): lambda f, _: core_schema.general_plain_validator_function(f),
    ('wrap', False): core_schema.general_wrap_validator_function,
}


def apply_validators(
    schema: core_schema.CoreSchema,
    validators: Iterable[Decorator[RootValidatorDecoratorInfo]]
    | Iterable[Decorator[ValidatorDecoratorInfo]]
    | Iterable[Decorator[FieldValidatorDecoratorInfo]],
) -> core_schema.CoreSchema:
    """
    Apply validators to a schema.
    """
    for validator in validators:
        is_field = isinstance(validator.info, (FieldValidatorDecoratorInfo, ValidatorDecoratorInfo))
        schema = _VALIDATOR_F_MATCH[(validator.info.mode, is_field)](validator.func, schema)
    return schema


def apply_serializers(
    schema: core_schema.CoreSchema, serializers: list[Decorator[SerializerDecoratorInfo]]
) -> core_schema.CoreSchema:
    """
    Apply serializers to a schema.
    """
    if serializers:
        # use the last serializer to make it easy to override a serializer set on a parent model
        serializer = serializers[-1]
        function = serializer.func
        if serializer.info.mode == 'wrap':
            sf = (
                core_schema.field_wrap_serializer_function_ser_schema
                if serializer.info.type == 'field'
                else core_schema.general_wrap_serializer_function_ser_schema
            )
            schema['serialization'] = sf(  # type: ignore[operator]
                function,
                schema.copy(),
                json_return_type=serializer.info.json_return_type,
                when_used=serializer.info.when_used,
            )
        else:
            assert serializer.info.mode == 'plain'
            sf = (
                core_schema.field_plain_serializer_function_ser_schema
                if serializer.info.type == 'field'
                else core_schema.general_plain_serializer_function_ser_schema
            )
            schema['serialization'] = sf(  # type: ignore[operator]
                function,
                json_return_type=serializer.info.json_return_type,
                when_used=serializer.info.when_used,
            )
    return schema


def apply_annotations(schema: core_schema.CoreSchema, annotations: typing.Iterable[Any]) -> core_schema.CoreSchema:
    """
    Apply arguments from `Annotated` or from `FieldInfo` to a schema.
    """
    handler = CoreMetadataHandler(schema)
    for metadata in annotations:
        schema = apply_single_annotation(schema, metadata)

        metadata_modify_js_function = _get_pydantic_modify_json_schema(metadata)
        handler.combine_modify_js_functions(metadata_modify_js_function)

    return schema


def apply_single_annotation(schema: core_schema.CoreSchema, metadata: Any) -> core_schema.CoreSchema:  # noqa C901
    if metadata is None:
        return schema

    metadata_schema = getattr(metadata, '__pydantic_core_schema__', None)
    if metadata_schema is not None:
        return metadata_schema

    metadata_get_schema = getattr(metadata, '__get_pydantic_core_schema__', None)
    if metadata_get_schema is not None:
        return metadata_get_schema(schema)

    if isinstance(metadata, GroupedMetadata):
        # GroupedMetadata yields `BaseMetadata`s
        return apply_annotations(schema, metadata)
    elif isinstance(metadata, FieldInfo):
        schema = apply_annotations(schema, metadata.metadata)
        if metadata.discriminator is not None:
            schema = _discriminated_union.apply_discriminator(schema, metadata.discriminator)
        # TODO setting a default here needs to be tested
        return wrap_default(metadata, schema)

    if isinstance(metadata, PydanticGeneralMetadata):
        metadata_dict = metadata.__dict__
    elif isinstance(metadata, (BaseMetadata, PydanticMetadata)):
        metadata_dict = dataclasses.asdict(metadata)  # type: ignore[call-overload]
    elif isinstance(metadata, type) and issubclass(metadata, PydanticMetadata):
        # also support PydanticMetadata classes being used without initialisation,
        # e.g. `Annotated[int, Strict]` as well as `Annotated[int, Strict()]`
        metadata_dict = {k: v for k, v in vars(metadata).items() if not k.startswith('_')}
    else:
        # PEP 593: "If a library (or tool) encounters a typehint Annotated[T, x] and has no
        # special logic for metadata x, it should ignore it and simply treat the type as T."
        # Allow, but ignore, any unknown metadata.
        return schema

    # TODO we need a way to remove metadata which this line currently prevents
    metadata_dict = {k: v for k, v in metadata_dict.items() if v is not None}
    if not metadata_dict:
        return schema

    handler = CoreMetadataHandler(schema)
    update_schema_function = handler.update_cs_function
    if update_schema_function is not None:
        new_schema = update_schema_function(schema, **metadata_dict)
        if new_schema is not None:
            schema = new_schema
    else:
        if schema['type'] == 'nullable':
            # for nullable schemas, metadata is automatically applied to the inner schema
            # TODO need to do the same for lists, tuples and more
            schema['schema'].update(metadata_dict)
        else:
            schema.update(metadata_dict)  # type: ignore[typeddict-item]
        try:
            SchemaValidator(schema)
        except SchemaError as e:
            # TODO: Generate an easier-to-understand ValueError here saying the field constraints are not enforced
            # The relevant test is: `tests.test_schema.test_unenforced_constraints_schema
            raise e
    return schema


def wrap_default(field_info: FieldInfo, schema: core_schema.CoreSchema) -> core_schema.CoreSchema:
    if field_info.default_factory:
        return core_schema.with_default_schema(schema, default_factory=field_info.default_factory)
    elif field_info.default is not Undefined:
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


def _get_pydantic_modify_json_schema(obj: Any) -> typing.Callable[[JsonSchemaValue], None] | None:
    modify_js_function = getattr(obj, '__pydantic_modify_json_schema__', None)

    if modify_js_function is None and hasattr(obj, '__modify_schema__'):
        warnings.warn(
            'The __modify_schema__ method is deprecated, use __pydantic_modify_json_schema__ instead',
            DeprecationWarning,
        )
        return obj.__modify_schema__

    return modify_js_function


def get_model_self_schema(cls: type[BaseModel]) -> tuple[core_schema.ModelSchema, str]:
    model_ref = get_type_ref(cls)
    try:
        model_js_metadata = cls.model_json_schema_metadata()
    except AttributeError:
        model_js_metadata = None
    schema = core_schema.model_schema(
        cls,
        core_schema.definition_reference_schema(model_ref),
        metadata=build_metadata_dict(js_metadata=model_js_metadata),
    )
    return schema, model_ref
