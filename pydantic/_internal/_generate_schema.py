"""Convert python types to pydantic-core schema."""
from __future__ import annotations as _annotations

import collections.abc
import dataclasses
import inspect
import re
import sys
import typing
import warnings
from contextlib import contextmanager, nullcontext
from copy import copy
from enum import Enum
from functools import partial
from inspect import Parameter, _ParameterKind, signature
from itertools import chain
from operator import attrgetter
from types import FunctionType, LambdaType, MethodType
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    ContextManager,
    Dict,
    ForwardRef,
    Iterable,
    Iterator,
    Mapping,
    Type,
    TypeVar,
    Union,
    cast,
    overload,
)
from warnings import warn

from pydantic_core import CoreSchema, PydanticUndefined, core_schema
from typing_extensions import Annotated, Final, Literal, TypeAliasType, TypedDict, get_args, get_origin, is_typeddict

from ..config import ConfigDict, JsonEncoder
from ..errors import PydanticSchemaGenerationError, PydanticUndefinedAnnotation, PydanticUserError
from ..fields import AliasChoices, AliasPath, FieldInfo
from ..json_schema import JsonSchemaValue
from ..version import version_short
from ..warnings import PydanticDeprecatedSince20
from . import _decorators, _discriminated_union, _known_annotated_metadata, _typing_extra
from ._annotated_handlers import GetCoreSchemaHandler, GetJsonSchemaHandler
from ._config import ConfigWrapper
from ._core_metadata import (
    CoreMetadataHandler,
    build_metadata_dict,
)
from ._core_utils import (
    CoreSchemaOrField,
    define_expected_missing_refs,
    flatten_schema_defs,
    get_type_ref,
    is_list_like_schema_with_items_schema,
)
from ._decorators import (
    ComputedFieldInfo,
    Decorator,
    DecoratorInfos,
    FieldSerializerDecoratorInfo,
    FieldValidatorDecoratorInfo,
    ModelSerializerDecoratorInfo,
    ModelValidatorDecoratorInfo,
    RootValidatorDecoratorInfo,
    ValidatorDecoratorInfo,
    inspect_field_serializer,
    inspect_model_serializer,
    inspect_validator,
)
from ._fields import collect_dataclass_fields, get_type_hints_infer_globalns
from ._forward_ref import PydanticRecursiveRef
from ._generics import get_standard_typevars_map, has_instance_in_type, recursively_defined_type_refs, replace_types
from ._schema_generation_shared import (
    CallbackGetCoreSchemaHandler,
)
from ._typing_extra import is_finalvar
from ._utils import lenient_issubclass

if TYPE_CHECKING:
    from ..main import BaseModel
    from ..validators import FieldValidatorModes
    from ._dataclasses import StandardDataclass
    from ._schema_generation_shared import GetJsonSchemaFunction

_SUPPORTS_TYPEDDICT = sys.version_info >= (3, 12)
_AnnotatedType = type(Annotated[int, 123])

FieldDecoratorInfo = Union[ValidatorDecoratorInfo, FieldValidatorDecoratorInfo, FieldSerializerDecoratorInfo]
FieldDecoratorInfoType = TypeVar('FieldDecoratorInfoType', bound=FieldDecoratorInfo)
AnyFieldDecorator = Union[
    Decorator[ValidatorDecoratorInfo],
    Decorator[FieldValidatorDecoratorInfo],
    Decorator[FieldSerializerDecoratorInfo],
]

ModifyCoreSchemaWrapHandler = GetCoreSchemaHandler
GetCoreSchemaFunction = Callable[[Any, ModifyCoreSchemaWrapHandler], core_schema.CoreSchema]


TUPLE_TYPES: list[type] = [tuple, typing.Tuple]
LIST_TYPES: list[type] = [list, typing.List, collections.abc.MutableSequence]
SET_TYPES: list[type] = [set, typing.Set, collections.abc.MutableSet]
FROZEN_SET_TYPES: list[type] = [frozenset, typing.FrozenSet, collections.abc.Set]
DICT_TYPES: list[type] = [dict, typing.Dict, collections.abc.MutableMapping, collections.abc.Mapping]


def check_validator_fields_against_field_name(
    info: FieldDecoratorInfo,
    field: str,
) -> bool:
    """Check if field name is in validator fields.

    Args:
        info: The field info.
        field: The field name to check.

    Returns:
        `True` if field name is in validator fields, `False` otherwise.
    """
    if isinstance(info, (ValidatorDecoratorInfo, FieldValidatorDecoratorInfo)):
        if '*' in info.fields:
            return True
    for v_field_name in info.fields:
        if v_field_name == field:
            return True
    return False


def check_decorator_fields_exist(decorators: Iterable[AnyFieldDecorator], fields: Iterable[str]) -> None:
    """Check if the defined fields in decorators exist in `fields` param.

    It ignores the check for a decorator if the decorator has `*` as field or `check_fields=False`.

    Args:
        decorators: An iterable of decorators.
        fields: An iterable of fields name.

    Raises:
        PydanticUserError: If one of the field names does not exist in `fields` param.
    """
    fields = set(fields)
    for dec in decorators:
        if isinstance(dec.info, (ValidatorDecoratorInfo, FieldValidatorDecoratorInfo)) and '*' in dec.info.fields:
            continue
        if dec.info.check_fields is False:
            continue
        for field in dec.info.fields:
            if field not in fields:
                raise PydanticUserError(
                    f'Decorators defined with incorrect fields: {dec.cls_ref}.{dec.cls_var_name}'
                    " (use check_fields=False if you're inheriting from the model and intended this)",
                    code='decorator-missing-field',
                )


def filter_field_decorator_info_by_field(
    validator_functions: Iterable[Decorator[FieldDecoratorInfoType]], field: str
) -> list[Decorator[FieldDecoratorInfoType]]:
    return [dec for dec in validator_functions if check_validator_fields_against_field_name(dec.info, field)]


def apply_each_item_validators(
    schema: core_schema.CoreSchema,
    each_item_validators: list[Decorator[ValidatorDecoratorInfo]],
    field_name: str | None,
) -> core_schema.CoreSchema:
    # This V1 compatibility shim should eventually be removed

    # push down any `each_item=True` validators
    # note that this won't work for any Annotated types that get wrapped by a function validator
    # but that's okay because that didn't exist in V1
    if schema['type'] == 'nullable':
        schema['schema'] = apply_each_item_validators(schema['schema'], each_item_validators, field_name)
        return schema
    elif is_list_like_schema_with_items_schema(schema):
        inner_schema = schema.get('items_schema', None)
        if inner_schema is None:
            inner_schema = core_schema.any_schema()
        schema['items_schema'] = apply_validators(inner_schema, each_item_validators, field_name)
    elif schema['type'] == 'dict':
        # push down any `each_item=True` validators onto dict _values_
        # this is super arbitrary but it's the V1 behavior
        inner_schema = schema.get('values_schema', None)
        if inner_schema is None:
            inner_schema = core_schema.any_schema()
        schema['values_schema'] = apply_validators(inner_schema, each_item_validators, field_name)
    elif each_item_validators:
        raise TypeError(
            f"`@validator(..., each_item=True)` cannot be applied to fields with a schema of {schema['type']}"
        )
    return schema


def modify_model_json_schema(
    schema_or_field: CoreSchemaOrField, handler: GetJsonSchemaHandler, *, cls: Any
) -> JsonSchemaValue:
    """Add title and description for model-like classes' JSON schema.

    Args:
        schema_or_field: The schema data to generate a JSON schema from.
        handler: The `GetCoreSchemaHandler` instance.
        cls: The model-like class.

    Returns:
        JsonSchemaValue: The updated JSON schema.
    """
    json_schema = handler(schema_or_field)
    original_schema = handler.resolve_ref_schema(json_schema)
    # Preserve the fact that definitions schemas should never have sibling keys:
    if '$ref' in original_schema:
        ref = original_schema['$ref']
        original_schema.clear()
        original_schema['allOf'] = [{'$ref': ref}]
    if 'title' not in original_schema:
        original_schema['title'] = cls.__name__
    docstring = cls.__doc__
    if docstring and 'description' not in original_schema:
        original_schema['description'] = inspect.cleandoc(docstring)
    return json_schema


JsonEncoders = Dict[Type[Any], JsonEncoder]


def _add_custom_serialization_from_json_encoders(
    json_encoders: JsonEncoders | None, tp: Any, schema: CoreSchema
) -> CoreSchema:
    """Iterate over the json_encoders and add the first matching encoder to the schema.

    Args:
        json_encoders: A dictionary of types and their encoder functions.
        tp: The type to check for a matching encoder.
        schema: The schema to add the encoder to.
    """
    if not json_encoders:
        return schema
    if 'serialization' in schema:
        return schema
    # Check the class type and its superclasses for a matching encoder
    # Decimal.__class__.__mro__ (and probably other cases) doesn't include Decimal itself
    # if the type is a GenericAlias (e.g. from list[int]) we need to use __class__ instead of .__mro__
    for base in (tp, *getattr(tp, '__mro__', tp.__class__.__mro__)[:-1]):
        encoder = json_encoders.get(base)
        if encoder is None:
            continue

        warnings.warn(
            f'`json_encoders` is deprecated. See https://docs.pydantic.dev/{version_short()}/usage/serialization/#custom-serializers for alternatives',
            PydanticDeprecatedSince20,
        )

        # TODO: in theory we should check that the schema accepts a serialization key
        schema['serialization'] = core_schema.plain_serializer_function_ser_schema(encoder, when_used='json')
        return schema

    return schema


class ConfigWrapperStack:
    """A stack of `ConfigWrapper` instances."""

    def __init__(self, config_wrapper: ConfigWrapper):
        self._config_wrapper_stack: list[ConfigWrapper] = [config_wrapper]

    @property
    def tail(self) -> ConfigWrapper:
        return self._config_wrapper_stack[-1]

    def push(self, config_wrapper: ConfigWrapper | ConfigDict | None) -> ContextManager[None]:
        if config_wrapper is None:
            return nullcontext()

        if not isinstance(config_wrapper, ConfigWrapper):
            config_wrapper = ConfigWrapper(config_wrapper, check=False)

        @contextmanager
        def _context_manager() -> Iterator[None]:
            self._config_wrapper_stack.append(config_wrapper)
            try:
                yield
            finally:
                self._config_wrapper_stack.pop()

        return _context_manager()


class GenerateSchema:
    """Generate core schema for a Pydantic model, dataclass and types like `str`, `datetime`, ... ."""

    def __init__(
        self,
        config_wrapper: ConfigWrapper,
        types_namespace: dict[str, Any] | None,
        typevars_map: dict[Any, Any] | None = None,
    ):
        # we need a stack for recursing into child models
        self._config_wrapper_stack = ConfigWrapperStack(config_wrapper)
        self._types_namespace = types_namespace
        self._typevars_map = typevars_map
        self.defs = _Definitions()

    @classmethod
    def __from_parent(
        cls,
        config_wrapper_stack: ConfigWrapperStack,
        types_namespace: dict[str, Any] | None,
        typevars_map: dict[Any, Any] | None,
        defs: _Definitions,
    ) -> GenerateSchema:
        obj = cls.__new__(cls)
        obj._config_wrapper_stack = config_wrapper_stack
        obj._types_namespace = types_namespace
        obj._typevars_map = typevars_map
        obj.defs = defs
        return obj

    @property
    def _config_wrapper(self) -> ConfigWrapper:
        return self._config_wrapper_stack.tail

    @property
    def _current_generate_schema(self) -> GenerateSchema:
        cls = self._config_wrapper.schema_generator or GenerateSchema
        return cls.__from_parent(
            self._config_wrapper_stack,
            self._types_namespace,
            self._typevars_map,
            self.defs,
        )

    @property
    def _arbitrary_types(self) -> bool:
        return self._config_wrapper.arbitrary_types_allowed

    def str_schema(self) -> CoreSchema:
        """Generate a CoreSchema for `str`"""
        return core_schema.str_schema()

    # the following methods can be overridden but should be considered
    # unstable / private APIs
    def _list_schema(self, tp: Any, items_type: Any) -> CoreSchema:
        return core_schema.list_schema(self.generate_schema(items_type))

    def _dict_schema(self, tp: Any, keys_type: Any, values_type: Any) -> CoreSchema:
        return core_schema.dict_schema(self.generate_schema(keys_type), self.generate_schema(values_type))

    def _set_schema(self, tp: Any, items_type: Any) -> CoreSchema:
        return core_schema.set_schema(self.generate_schema(items_type))

    def _frozenset_schema(self, tp: Any, items_type: Any) -> CoreSchema:
        return core_schema.frozenset_schema(self.generate_schema(items_type))

    def _tuple_variable_schema(self, tp: Any, items_type: Any) -> CoreSchema:
        return core_schema.tuple_variable_schema(self.generate_schema(items_type))

    def _tuple_positional_schema(self, tp: Any, items_types: list[Any]) -> CoreSchema:
        items_schemas = [self.generate_schema(items_type) for items_type in items_types]
        return core_schema.tuple_positional_schema(items_schemas)

    def _arbitrary_type_schema(self, tp: Any) -> CoreSchema:
        if not isinstance(tp, type):
            warn(
                f'{tp!r} is not a Python type (it may be an instance of an object),'
                ' Pydantic will allow any object with no validation since we cannot even'
                ' enforce that the input is an instance of the given type.'
                ' To get rid of this error wrap the type with `pydantic.SkipValidation`.',
                UserWarning,
            )
            return core_schema.any_schema()
        return core_schema.is_instance_schema(tp)

    def _unknown_type_schema(self, obj: Any) -> CoreSchema:
        raise PydanticSchemaGenerationError(
            f'Unable to generate pydantic-core schema for {obj!r}. '
            'Set `arbitrary_types_allowed=True` in the model_config to ignore this error'
            ' or implement `__get_pydantic_core_schema__` on your type to fully support it.'
            '\n\nIf you got this error by calling handler(<some type>) within'
            ' `__get_pydantic_core_schema__` then you likely need to call'
            ' `handler.generate_schema(<some type>)` since we do not call'
            ' `__get_pydantic_core_schema__` on `<some type>` otherwise to avoid infinite recursion.'
        )

    def collect_definitions(self, schema: CoreSchema) -> CoreSchema:
        ref = cast('str | None', schema.get('ref', None))
        if ref:
            self.defs.definitions[ref] = schema
        return core_schema.definitions_schema(
            schema,
            list(self.defs.definitions.values()),
        )

    def _add_js_function(self, metadata_schema: CoreSchema, js_function: Callable[..., Any]) -> None:
        metadata = CoreMetadataHandler(metadata_schema).metadata
        pydantic_js_functions = metadata.setdefault('pydantic_js_functions', [])
        # because of how we generate core schemas for nested generic models
        # we can end up adding `BaseModel.__get_pydantic_json_schema__` multiple times
        # this check may fail to catch duplicates if the function is a `functools.partial`
        # or something like that
        # but if it does it'll fail by inserting the duplicate
        if js_function not in pydantic_js_functions:
            pydantic_js_functions.append(js_function)

    def generate_schema(
        self,
        obj: Any,
        from_dunder_get_core_schema: bool = True,
        from_prepare_args: bool = True,
    ) -> core_schema.CoreSchema:
        """Generate core schema.

        Args:
            obj: The object to generate core schema for.
            from_dunder_get_core_schema: Whether to generate schema from either the
                `__get_pydantic_core_schema__` function or `__pydantic_core_schema__` property.
            from_prepare_args: Whether to generate schema from either the
                `__prepare_pydantic_annotations__` function or `__prepare_pydantic_annotations__` property.

        Returns:
            The generated core schema.

        Raises:
            PydanticUndefinedAnnotation:
                If it is not possible to evaluate forward reference.
            PydanticSchemaGenerationError:
                If it is not possible to generate pydantic-core schema.
            TypeError:
                - If `alias_generator` returns a non-string value.
                - If V1 style validator with `each_item=True` applied on a wrong field.
            PydanticUserError:
                - If `typing.TypedDict` is used instead of `typing_extensions.TypedDict` on Python < 3.12.
                - If `__modify_schema__` method is used instead of `__get_pydantic_json_schema__`.
        """
        schema: CoreSchema | None = None

        if from_prepare_args:
            schema = self._generate_schema_from_prepare_annotations(obj)

        if from_dunder_get_core_schema:
            from_property = self._generate_schema_from_property(obj, obj)
            if from_property is not None:
                schema = from_property

        if schema is None:
            schema = self._generate_schema(obj)

        metadata_js_function = _extract_get_pydantic_json_schema(obj, schema)
        if metadata_js_function is not None:
            metadata_schema = resolve_original_schema(schema, self.defs.definitions)
            if metadata_schema:
                self._add_js_function(metadata_schema, metadata_js_function)

        schema = _add_custom_serialization_from_json_encoders(self._config_wrapper.json_encoders, obj, schema)

        return schema

    def _model_schema(self, cls: type[BaseModel]) -> core_schema.CoreSchema:
        """Generate schema for a Pydantic model."""
        with self.defs.get_schema_or_ref(cls) as (model_ref, maybe_schema):
            if maybe_schema is not None:
                return maybe_schema

            fields = cls.model_fields
            decorators = cls.__pydantic_decorators__
            computed_fields = decorators.computed_fields
            check_decorator_fields_exist(
                chain(
                    decorators.field_validators.values(),
                    decorators.field_serializers.values(),
                    decorators.validators.values(),
                ),
                {*fields.keys(), *computed_fields.keys()},
            )
            config_wrapper = ConfigWrapper(cls.model_config, check=False)
            core_config = config_wrapper.core_config(cls)
            metadata = build_metadata_dict(js_functions=[partial(modify_model_json_schema, cls=cls)])

            model_validators = decorators.model_validators.values()

            extra_validator = None
            if core_config.get('extra_fields_behavior') == 'allow':
                for tp in (cls, *cls.__mro__):
                    extras_annotation = cls.__annotations__.get('__pydantic_extra__', None)
                    if extras_annotation is not None:
                        tp = get_origin(extras_annotation)
                        if tp not in (Dict, dict):
                            raise PydanticSchemaGenerationError(
                                'The type annotation for `__pydantic_extra__` must be `Dict[str, ...]`'
                            )
                        extra_items_type = self._get_args_resolving_forward_refs(
                            cls.__annotations__['__pydantic_extra__'],
                            required=True,
                        )[1]
                        if extra_items_type is not Any:
                            extra_validator = self.generate_schema(extra_items_type)
                            break

            with self._config_wrapper_stack.push(config_wrapper):
                self = self._current_generate_schema
                if cls.__pydantic_root_model__:
                    root_field = self._common_field_schema('root', fields['root'], decorators)
                    inner_schema = root_field['schema']
                    inner_schema = apply_model_validators(inner_schema, model_validators, 'inner')
                    model_schema = core_schema.model_schema(
                        cls,
                        inner_schema,
                        custom_init=getattr(cls, '__pydantic_custom_init__', None),
                        root_model=True,
                        post_init=getattr(cls, '__pydantic_post_init__', None),
                        config=core_config,
                        ref=model_ref,
                        metadata=metadata,
                    )
                else:
                    fields_schema: core_schema.CoreSchema = core_schema.model_fields_schema(
                        {k: self._generate_md_field_schema(k, v, decorators) for k, v in fields.items()},
                        computed_fields=[
                            self._computed_field_schema(d, decorators.field_serializers)
                            for d in computed_fields.values()
                        ],
                        extra_validator=extra_validator,
                        model_name=cls.__name__,
                    )
                    inner_schema = apply_validators(fields_schema, decorators.root_validators.values(), None)
                    inner_schema = define_expected_missing_refs(inner_schema, recursively_defined_type_refs())
                    inner_schema = apply_model_validators(inner_schema, model_validators, 'inner')

                    model_schema = core_schema.model_schema(
                        cls,
                        inner_schema,
                        custom_init=getattr(cls, '__pydantic_custom_init__', None),
                        root_model=False,
                        post_init=getattr(cls, '__pydantic_post_init__', None),
                        config=core_config,
                        ref=model_ref,
                        metadata=metadata,
                    )

                schema = self._apply_model_serializers(model_schema, decorators.model_serializers.values())
                schema = apply_model_validators(schema, model_validators, 'outer')
                self.defs.definitions[model_ref] = schema
                return core_schema.definition_reference_schema(model_ref)

    def _generate_schema_from_prepare_annotations(self, obj: Any) -> core_schema.CoreSchema | None:
        """Try to generate schema from either the `__prepare_pydantic_annotations__` function or
        `__prepare_pydantic_annotations__` property.
        """
        new_obj, new_annotations = self._prepare_annotations(obj, [])
        if new_obj is not obj or new_annotations:
            return self._apply_annotations(
                new_obj,
                new_annotations,
            )
        return None

    def _unpack_refs_defs(self, schema: CoreSchema) -> CoreSchema:
        """Unpack all 'definitions' schemas into `GenerateSchema.defs.definitions`
        and return the inner schema.
        """

        def get_ref(s: CoreSchema) -> str:
            return s['ref']  # type: ignore

        schema = flatten_schema_defs(schema)

        if schema['type'] == 'definitions':
            self.defs.definitions.update({get_ref(s): s for s in schema['definitions']})
            schema = schema['schema']
        return schema

    def _generate_schema_from_property(self, obj: Any, source: Any) -> core_schema.CoreSchema | None:
        """Try to generate schema from either the `__get_pydantic_core_schema__` function or
        `__pydantic_core_schema__` property.

        Note: `__get_pydantic_core_schema__` takes priority so it can
        decide whether to use a `__pydantic_core_schema__` attribute, or generate a fresh schema.
        """
        # avoid calling `__get_pydantic_core_schema__` if we've already visited this object
        with self.defs.get_schema_or_ref(obj) as (_, maybe_schema):
            if maybe_schema is not None:
                return maybe_schema
        if obj is source:
            ref_mode = 'unpack'
        else:
            ref_mode = 'to-def'

        schema: CoreSchema
        get_schema = getattr(obj, '__get_pydantic_core_schema__', None)
        if get_schema is None:
            validators = getattr(obj, '__get_validators__', None)
            if validators is None:
                return None
            warn(
                '`__get_validators__` is deprecated and will be removed, use `__get_pydantic_core_schema__` instead.',
                PydanticDeprecatedSince20,
            )
            schema = core_schema.chain_schema([core_schema.general_plain_validator_function(v) for v in validators()])
        else:
            if len(inspect.signature(get_schema).parameters) == 1:
                # (source) -> CoreSchema
                schema = get_schema(source)
            else:
                schema = get_schema(
                    source, CallbackGetCoreSchemaHandler(self._generate_schema, self, ref_mode=ref_mode)
                )

        schema = self._unpack_refs_defs(schema)

        ref: str | None = schema.get('ref', None)
        if ref:
            self.defs.definitions[ref] = schema
            return core_schema.definition_reference_schema(ref)
        return schema

    def _resolve_forward_ref(self, obj: Any) -> Any:
        # we assume that types_namespace has the target of forward references in its scope,
        # but this could fail, for example, if calling Validator on an imported type which contains
        # forward references to other types only defined in the module from which it was imported
        # `Validator(SomeImportedTypeAliasWithAForwardReference)`
        # or the equivalent for BaseModel
        # class Model(BaseModel):
        #   x: SomeImportedTypeAliasWithAForwardReference
        try:
            obj = _typing_extra.evaluate_fwd_ref(obj, globalns=self._types_namespace)
        except NameError as e:
            raise PydanticUndefinedAnnotation.from_name_error(e) from e

        # if obj is still a ForwardRef, it means we can't evaluate it, raise PydanticUndefinedAnnotation
        if isinstance(obj, ForwardRef):
            raise PydanticUndefinedAnnotation(obj.__forward_arg__, f'Unable to evaluate forward reference {obj}')

        if self._typevars_map:
            obj = replace_types(obj, self._typevars_map)

        return obj

    @overload
    def _get_args_resolving_forward_refs(self, obj: Any, required: Literal[True]) -> tuple[Any, ...]:
        ...

    @overload
    def _get_args_resolving_forward_refs(self, obj: Any) -> tuple[Any, ...] | None:
        ...

    def _get_args_resolving_forward_refs(self, obj: Any, required: bool = False) -> tuple[Any, ...] | None:
        args = get_args(obj)
        if args:
            args = tuple([self._resolve_forward_ref(a) if isinstance(a, ForwardRef) else a for a in args])
        elif required:  # pragma: no cover
            raise TypeError(f'Expected {obj} to have generic parameters but it had none')
        return args

    def _get_first_arg_or_any(self, obj: Any) -> Any:
        args = self._get_args_resolving_forward_refs(obj)
        if not args:
            return Any
        return args[0]

    def _get_first_two_args_or_any(self, obj: Any) -> tuple[Any, Any]:
        args = self._get_args_resolving_forward_refs(obj)
        if not args:
            return (Any, Any)
        if len(args) < 2:
            origin = get_origin(obj)
            raise TypeError(f'Expected two type arguments for {origin}, got 1')
        return args[0], args[1]

    def _generate_schema(self, obj: Any) -> core_schema.CoreSchema:
        """Recursively generate a pydantic-core schema for any supported python type."""
        if isinstance(obj, _AnnotatedType):
            return self._annotated_schema(obj)

        if isinstance(obj, dict):
            # we assume this is already a valid schema
            return obj  # type: ignore[return-value]

        if isinstance(obj, str):
            obj = ForwardRef(obj)

        if isinstance(obj, ForwardRef):
            return self.generate_schema(self._resolve_forward_ref(obj))

        from ..main import BaseModel

        if lenient_issubclass(obj, BaseModel):
            return self._model_schema(obj)

        if isinstance(obj, PydanticRecursiveRef):
            return core_schema.definition_reference_schema(schema_ref=obj.type_ref)

        return self.match_type(obj)

    def match_type(self, obj: Any) -> core_schema.CoreSchema:  # noqa: C901
        """Main mapping of types to schemas.

        The general structure is a series of if statements starting with the simple cases
        (non-generic primitive types) and then handling generics and other more complex cases.

        Each case either generates a schema directly, calls into a public user-overridable method
        (like `GenerateSchema.tuple_variable_schema`) or calls into a private method that handles some
        boilerplate before calling into the user-facing method (e.g. `GenerateSchema._tuple_schema`).

        The idea is that we'll evolve this into adding more and more user facing methods over time
        as they get requested and we figure out what the right API for them is.
        """
        if obj is str:
            return self.str_schema()
        elif obj is bytes:
            return core_schema.bytes_schema()
        elif obj is int:
            return core_schema.int_schema()
        elif obj is float:
            return core_schema.float_schema()
        elif obj is bool:
            return core_schema.bool_schema()
        elif obj is Any or obj is object:
            return core_schema.any_schema()
        elif obj is None or obj is _typing_extra.NoneType:
            return core_schema.none_schema()
        elif obj in TUPLE_TYPES:
            return self._tuple_schema(obj)
        elif obj in LIST_TYPES:
            return self._list_schema(obj, self._get_first_arg_or_any(obj))
        elif obj in SET_TYPES:
            return self._set_schema(obj, self._get_first_arg_or_any(obj))
        elif obj in FROZEN_SET_TYPES:
            return self._frozenset_schema(obj, self._get_first_arg_or_any(obj))
        elif obj in DICT_TYPES:
            return self._dict_schema(obj, *self._get_first_two_args_or_any(obj))
        elif isinstance(obj, TypeAliasType):
            return self._type_alias_type_schema(obj)
        elif obj == type:
            return self._type_schema()
        elif _typing_extra.is_callable_type(obj):
            return core_schema.callable_schema()
        elif _typing_extra.is_literal_type(obj):
            return self._literal_schema(obj)
        elif is_typeddict(obj):
            return self._typed_dict_schema(obj, None)
        elif _typing_extra.is_namedtuple(obj):
            return self._namedtuple_schema(obj, None)
        elif _typing_extra.is_new_type(obj):
            # NewType, can't use isinstance because it fails <3.7
            return self.generate_schema(obj.__supertype__)
        elif obj == re.Pattern:
            return self._pattern_schema(obj)
        elif obj is collections.abc.Hashable or obj is typing.Hashable:
            return self._hashable_schema()
        elif isinstance(obj, typing.TypeVar):
            return self._unsubstituted_typevar_schema(obj)
        elif is_finalvar(obj):
            if obj is Final:
                return core_schema.any_schema()
            return self.generate_schema(
                self._get_first_arg_or_any(obj),
            )
        elif isinstance(obj, (FunctionType, LambdaType, MethodType, partial)):
            return self._callable_schema(obj)
        elif inspect.isclass(obj) and issubclass(obj, Enum):
            from ._std_types_schema import get_enum_core_schema

            return get_enum_core_schema(obj, self._config_wrapper.config_dict)

        if _typing_extra.is_dataclass(obj):
            return self._dataclass_schema(obj, None)

        res = self._get_prepare_pydantic_annotations_for_known_type(obj, ())
        if res is not None:
            source_type, annotations = res
            return self._apply_annotations(source_type, annotations)

        origin = get_origin(obj)
        if origin is not None:
            return self._match_generic_type(obj, origin)

        if self._arbitrary_types:
            return self._arbitrary_type_schema(obj)
        return self._unknown_type_schema(obj)

    def _match_generic_type(self, obj: Any, origin: Any) -> CoreSchema:  # noqa: C901
        if isinstance(origin, TypeAliasType):
            return self._type_alias_type_schema(obj)

        # Need to handle generic dataclasses before looking for the schema properties because attribute accesses
        # on _GenericAlias delegate to the origin type, so lose the information about the concrete parametrization
        # As a result, currently, there is no way to cache the schema for generic dataclasses. This may be possible
        # to resolve by modifying the value returned by `Generic.__class_getitem__`, but that is a dangerous game.
        if _typing_extra.is_dataclass(origin):
            return self._dataclass_schema(obj, origin)
        if _typing_extra.is_namedtuple(origin):
            return self._namedtuple_schema(obj, origin)

        from_property = self._generate_schema_from_property(origin, obj)
        if from_property is not None:
            return from_property

        if _typing_extra.origin_is_union(origin):
            return self._union_schema(obj)
        elif origin in TUPLE_TYPES:
            return self._tuple_schema(obj)
        elif origin in LIST_TYPES:
            return self._list_schema(obj, self._get_first_arg_or_any(obj))
        elif origin in SET_TYPES:
            return self._set_schema(obj, self._get_first_arg_or_any(obj))
        elif origin in FROZEN_SET_TYPES:
            return self._frozenset_schema(obj, self._get_first_arg_or_any(obj))
        elif origin in DICT_TYPES:
            return self._dict_schema(obj, *self._get_first_two_args_or_any(obj))
        elif is_typeddict(origin):
            return self._typed_dict_schema(obj, origin)
        elif origin in (typing.Type, type):
            return self._subclass_schema(obj)
        elif origin in {typing.Sequence, collections.abc.Sequence}:
            return self._sequence_schema(obj)
        elif origin in {typing.Iterable, collections.abc.Iterable, typing.Generator, collections.abc.Generator}:
            return self._iterable_schema(obj)
        elif origin in (re.Pattern, typing.Pattern):
            return self._pattern_schema(obj)

        if self._arbitrary_types:
            return self._arbitrary_type_schema(origin)
        return self._unknown_type_schema(obj)

    def _generate_td_field_schema(
        self,
        name: str,
        field_info: FieldInfo,
        decorators: DecoratorInfos,
        *,
        required: bool = True,
    ) -> core_schema.TypedDictField:
        """Prepare a TypedDictField to represent a model or typeddict field."""
        common_field = self._common_field_schema(name, field_info, decorators)
        return core_schema.typed_dict_field(
            common_field['schema'],
            required=False if not field_info.is_required() else required,
            serialization_exclude=common_field['serialization_exclude'],
            validation_alias=common_field['validation_alias'],
            serialization_alias=common_field['serialization_alias'],
            metadata=common_field['metadata'],
        )

    def _generate_md_field_schema(
        self,
        name: str,
        field_info: FieldInfo,
        decorators: DecoratorInfos,
    ) -> core_schema.ModelField:
        """Prepare a ModelField to represent a model field."""
        common_field = self._common_field_schema(name, field_info, decorators)
        return core_schema.model_field(
            common_field['schema'],
            serialization_exclude=common_field['serialization_exclude'],
            validation_alias=common_field['validation_alias'],
            serialization_alias=common_field['serialization_alias'],
            frozen=common_field['frozen'],
            metadata=common_field['metadata'],
        )

    def _generate_dc_field_schema(
        self,
        name: str,
        field_info: FieldInfo,
        decorators: DecoratorInfos,
    ) -> core_schema.DataclassField:
        """Prepare a DataclassField to represent the parameter/field, of a dataclass."""
        common_field = self._common_field_schema(name, field_info, decorators)
        return core_schema.dataclass_field(
            name,
            common_field['schema'],
            init_only=field_info.init_var or None,
            kw_only=None if field_info.kw_only else False,
            serialization_exclude=common_field['serialization_exclude'],
            validation_alias=common_field['validation_alias'],
            serialization_alias=common_field['serialization_alias'],
            frozen=common_field['frozen'],
            metadata=common_field['metadata'],
        )

    def _common_field_schema(self, name: str, field_info: FieldInfo, decorators: DecoratorInfos) -> _CommonField:
        # Update FieldInfo annotation if appropriate:
        if has_instance_in_type(field_info.annotation, (ForwardRef, str)):
            types_namespace = self._types_namespace
            if self._typevars_map:
                types_namespace = (types_namespace or {}).copy()
                # Ensure that typevars get mapped to their concrete types:
                types_namespace.update({k.__name__: v for k, v in self._typevars_map.items()})

            evaluated = _typing_extra.eval_type_lenient(field_info.annotation, types_namespace, None)
            if evaluated is not field_info.annotation and not has_instance_in_type(evaluated, PydanticRecursiveRef):
                field_info.annotation = evaluated

        source_type, annotations = field_info.annotation, field_info.metadata

        def set_discriminator(schema: CoreSchema) -> CoreSchema:
            _discriminated_union.set_discriminator(schema, field_info.discriminator)
            return schema

        if field_info.discriminator is not None:
            schema = self._apply_annotations(source_type, annotations, transform_inner_schema=set_discriminator)
        else:
            schema = self._apply_annotations(
                source_type,
                annotations,
            )

        # This V1 compatibility shim should eventually be removed
        # push down any `each_item=True` validators
        # note that this won't work for any Annotated types that get wrapped by a function validator
        # but that's okay because that didn't exist in V1
        this_field_validators = filter_field_decorator_info_by_field(decorators.validators.values(), name)
        if _validators_require_validate_default(this_field_validators):
            field_info.validate_default = True
        each_item_validators = [v for v in this_field_validators if v.info.each_item is True]
        this_field_validators = [v for v in this_field_validators if v not in each_item_validators]
        schema = apply_each_item_validators(schema, each_item_validators, name)

        schema = apply_validators(schema, filter_field_decorator_info_by_field(this_field_validators, name), name)
        schema = apply_validators(
            schema, filter_field_decorator_info_by_field(decorators.field_validators.values(), name), name
        )

        # the default validator needs to go outside of any other validators
        # so that it is the topmost validator for the field validator
        # which uses it to check if the field has a default value or not
        if not field_info.is_required():
            schema = wrap_default(field_info, schema)

        schema = self._apply_field_serializers(
            schema, filter_field_decorator_info_by_field(decorators.field_serializers.values(), name)
        )
        json_schema_updates = {
            'title': field_info.title,
            'description': field_info.description,
            'examples': field_info.examples,
        }
        json_schema_updates = {k: v for k, v in json_schema_updates.items() if v is not None}

        json_schema_extra = field_info.json_schema_extra

        def json_schema_update_func(schema: CoreSchemaOrField, handler: GetJsonSchemaHandler) -> JsonSchemaValue:
            json_schema = {**handler(schema), **json_schema_updates}
            if isinstance(json_schema_extra, dict):
                json_schema.update(json_schema_extra)
            elif callable(json_schema_extra):
                json_schema_extra(json_schema)
            return json_schema

        metadata = build_metadata_dict(js_annotation_functions=[json_schema_update_func])

        # apply alias generator
        alias_generator = self._config_wrapper.alias_generator
        if alias_generator and (field_info.alias_priority is None or field_info.alias_priority <= 1):
            alias = alias_generator(name)
            if not isinstance(alias, str):
                raise TypeError(f'alias_generator {alias_generator} must return str, not {alias.__class__}')
            field_info.alias = alias
            field_info.validation_alias = alias
            field_info.serialization_alias = alias
            field_info.alias_priority = 1

        if isinstance(field_info.validation_alias, (AliasChoices, AliasPath)):
            validation_alias = field_info.validation_alias.convert_to_aliases()
        else:
            validation_alias = field_info.validation_alias

        return _common_field(
            schema,
            serialization_exclude=True if field_info.exclude else None,
            validation_alias=validation_alias,
            serialization_alias=field_info.serialization_alias,
            frozen=field_info.frozen,
            metadata=metadata,
        )

    def _union_schema(self, union_type: Any) -> core_schema.CoreSchema:
        """Generate schema for a Union."""
        args = self._get_args_resolving_forward_refs(union_type, required=True)
        choices: list[CoreSchema | tuple[CoreSchema, str]] = []
        nullable = False
        for arg in args:
            if arg is None or arg is _typing_extra.NoneType:
                nullable = True
            else:
                choices.append(self.generate_schema(arg))

        if len(choices) == 1:
            first_choice = choices[0]
            s = first_choice[0] if isinstance(first_choice, tuple) else first_choice
        else:
            s = core_schema.union_schema(choices)

        if nullable:
            s = core_schema.nullable_schema(s)
        return s

    def _type_alias_type_schema(
        self,
        obj: Any,  # TypeAliasType
    ) -> CoreSchema:
        origin = get_origin(obj)
        origin = origin or obj
        with self.defs.get_schema_or_ref(origin) as (ref, maybe_schema):
            if maybe_schema is not None:
                return maybe_schema

            namespace = (self._types_namespace or {}).copy()
            new_namespace = {**_typing_extra.get_cls_types_namespace(origin), **namespace}
            annotation = origin.__value__

            self._types_namespace = new_namespace
            typevars_map = get_standard_typevars_map(obj)
            annotation = replace_types(annotation, typevars_map)
            schema = self.generate_schema(annotation)
            assert schema['type'] != 'definitions'
            schema['ref'] = ref  # type: ignore
            self._types_namespace = namespace or None
            self.defs.definitions[ref] = schema
            return core_schema.definition_reference_schema(ref)

    def _literal_schema(self, literal_type: Any) -> CoreSchema:
        """Generate schema for a Literal."""
        expected = _typing_extra.all_literal_values(literal_type)
        assert expected, f'literal "expected" cannot be empty, obj={literal_type}'
        return core_schema.literal_schema(expected)

    def _typed_dict_schema(self, typed_dict_cls: Any, origin: Any) -> core_schema.CoreSchema:
        """Generate schema for a TypedDict.

        It is not possible to track required/optional keys in TypedDict without __required_keys__
        since TypedDict.__new__ erases the base classes (it replaces them with just `dict`)
        and thus we can track usage of total=True/False
        __required_keys__ was added in Python 3.9
        (https://github.com/miss-islington/cpython/blob/1e9939657dd1f8eb9f596f77c1084d2d351172fc/Doc/library/typing.rst?plain=1#L1546-L1548)
        however it is buggy
        (https://github.com/python/typing_extensions/blob/ac52ac5f2cb0e00e7988bae1e2a1b8257ac88d6d/src/typing_extensions.py#L657-L666).

        On 3.11 but < 3.12 TypedDict does not preserve inheritance information.

        Hence to avoid creating validators that do not do what users expect we only
        support typing.TypedDict on Python >= 3.12 or typing_extension.TypedDict on all versions
        """
        with self.defs.get_schema_or_ref(typed_dict_cls) as (typed_dict_ref, maybe_schema):
            if maybe_schema is not None:
                return maybe_schema

            typevars_map = get_standard_typevars_map(typed_dict_cls)
            if origin is not None:
                typed_dict_cls = origin

            if not _SUPPORTS_TYPEDDICT and type(typed_dict_cls).__module__ == 'typing':
                raise PydanticUserError(
                    'Please use `typing_extensions.TypedDict` instead of `typing.TypedDict` on Python < 3.12.',
                    code='typed-dict-version',
                )

            config: ConfigDict | None = None
            for base in (typed_dict_cls, *typed_dict_cls.__orig_bases__):
                config = getattr(base, '__pydantic_config__', None)
                if config is not None:
                    break

            with self._config_wrapper_stack.push(config):
                core_config = self._config_wrapper.core_config(typed_dict_cls)

                self = self._current_generate_schema

                required_keys: frozenset[str] = typed_dict_cls.__required_keys__

                fields: dict[str, core_schema.TypedDictField] = {}

                decorators = DecoratorInfos.build(typed_dict_cls)

                for field_name, annotation in get_type_hints_infer_globalns(
                    typed_dict_cls, localns=self._types_namespace, include_extras=True
                ).items():
                    annotation = replace_types(annotation, typevars_map)
                    required = field_name in required_keys

                    if get_origin(annotation) == _typing_extra.Required:
                        required = True
                        annotation = self._get_args_resolving_forward_refs(
                            annotation,
                            required=True,
                        )[0]
                    elif get_origin(annotation) == _typing_extra.NotRequired:
                        required = False
                        annotation = self._get_args_resolving_forward_refs(
                            annotation,
                            required=True,
                        )[0]

                    field_info = FieldInfo.from_annotation(annotation)
                    fields[field_name] = self._generate_td_field_schema(
                        field_name, field_info, decorators, required=required
                    )

                metadata = build_metadata_dict(js_functions=[partial(modify_model_json_schema, cls=typed_dict_cls)])

                td_schema = core_schema.typed_dict_schema(
                    fields,
                    computed_fields=[
                        self._computed_field_schema(d, decorators.field_serializers)
                        for d in decorators.computed_fields.values()
                    ],
                    ref=typed_dict_ref,
                    metadata=metadata,
                    config=core_config,
                )

                schema = self._apply_model_serializers(td_schema, decorators.model_serializers.values())
                schema = apply_model_validators(schema, decorators.model_validators.values(), 'all')
                self.defs.definitions[typed_dict_ref] = schema
                return core_schema.definition_reference_schema(typed_dict_ref)

    def _namedtuple_schema(self, namedtuple_cls: Any, origin: Any) -> core_schema.CoreSchema:
        """Generate schema for a NamedTuple."""
        with self.defs.get_schema_or_ref(namedtuple_cls) as (namedtuple_ref, maybe_schema):
            if maybe_schema is not None:
                return maybe_schema
            typevars_map = get_standard_typevars_map(namedtuple_cls)
            if origin is not None:
                namedtuple_cls = origin

            annotations: dict[str, Any] = get_type_hints_infer_globalns(
                namedtuple_cls, include_extras=True, localns=self._types_namespace
            )
            if not annotations:
                # annotations is empty, happens if namedtuple_cls defined via collections.namedtuple(...)
                annotations = {k: Any for k in namedtuple_cls._fields}

            if typevars_map:
                annotations = {
                    field_name: replace_types(annotation, typevars_map)
                    for field_name, annotation in annotations.items()
                }

            arguments_schema = core_schema.arguments_schema(
                [
                    self._generate_parameter_schema(
                        field_name, annotation, default=namedtuple_cls._field_defaults.get(field_name, Parameter.empty)
                    )
                    for field_name, annotation in annotations.items()
                ],
                metadata=build_metadata_dict(js_prefer_positional_arguments=True),
            )
            return core_schema.call_schema(arguments_schema, namedtuple_cls, ref=namedtuple_ref)

    def _generate_parameter_schema(
        self,
        name: str,
        annotation: type[Any],
        default: Any = Parameter.empty,
        mode: Literal['positional_only', 'positional_or_keyword', 'keyword_only'] | None = None,
    ) -> core_schema.ArgumentsParameter:
        """Prepare a ArgumentsParameter to represent a field in a namedtuple or function signature."""
        if default is Parameter.empty:
            field = FieldInfo.from_annotation(annotation)
        else:
            field = FieldInfo.from_annotated_attribute(annotation, default)
        assert field.annotation is not None, 'field.annotation should not be None when generating a schema'
        source_type, annotations = field.annotation, field.metadata
        schema = self._apply_annotations(source_type, annotations)

        if not field.is_required():
            schema = wrap_default(field, schema)

        parameter_schema = core_schema.arguments_parameter(name, schema)
        if mode is not None:
            parameter_schema['mode'] = mode
        if field.alias is not None:
            parameter_schema['alias'] = field.alias
        else:
            alias_generator = self._config_wrapper.alias_generator
            if alias_generator:
                parameter_schema['alias'] = alias_generator(name)
        return parameter_schema

    def _tuple_schema(self, tuple_type: Any) -> core_schema.CoreSchema:
        """Generate schema for a Tuple, e.g. `tuple[int, str]` or `tuple[int, ...]`."""
        # TODO: do we really need to resolve type vars here?
        typevars_map = get_standard_typevars_map(tuple_type)
        params = self._get_args_resolving_forward_refs(tuple_type)

        if typevars_map and params:
            params = tuple(replace_types(param, typevars_map) for param in params)

        # NOTE: subtle difference: `tuple[()]` gives `params=()`, whereas `typing.Tuple[()]` gives `params=((),)`
        # This is only true for <3.11, on Python 3.11+ `typing.Tuple[()]` gives `params=()`
        if not params:
            if tuple_type in TUPLE_TYPES:
                return core_schema.tuple_variable_schema()
            else:
                # special case for `tuple[()]` which means `tuple[]` - an empty tuple
                return core_schema.tuple_positional_schema([])
        elif params[-1] is Ellipsis:
            if len(params) == 2:
                return self._tuple_variable_schema(tuple_type, params[0])
            else:
                # TODO: something like https://github.com/pydantic/pydantic/issues/5952
                raise ValueError('Variable tuples can only have one type')
        elif len(params) == 1 and params[0] == ():
            # special case for `Tuple[()]` which means `Tuple[]` - an empty tuple
            # NOTE: This conditional can be removed when we drop support for Python 3.10.
            return self._tuple_positional_schema(tuple_type, [])
        else:
            return self._tuple_positional_schema(tuple_type, list(params))

    def _type_schema(self) -> core_schema.CoreSchema:
        return core_schema.custom_error_schema(
            core_schema.is_instance_schema(type),
            custom_error_type='is_type',
            custom_error_message='Input should be a type',
        )

    def _subclass_schema(self, type_: Any) -> core_schema.CoreSchema:
        """Generate schema for a Type, e.g. `Type[int]`."""
        type_param = self._get_first_arg_or_any(type_)
        if type_param == Any:
            return self._type_schema()
        elif isinstance(type_param, typing.TypeVar):
            if type_param.__bound__:
                return core_schema.is_subclass_schema(type_param.__bound__)
            elif type_param.__constraints__:
                return core_schema.union_schema(
                    [self.generate_schema(typing.Type[c]) for c in type_param.__constraints__]
                )
            else:
                return self._type_schema()
        elif _typing_extra.origin_is_union(get_origin(type_param)):
            args = self._get_args_resolving_forward_refs(type_param, required=True)
            return core_schema.union_schema([self.generate_schema(typing.Type[args]) for args in args])
        else:
            return core_schema.is_subclass_schema(type_param)

    def _sequence_schema(self, sequence_type: Any) -> core_schema.CoreSchema:
        """Generate schema for a Sequence, e.g. `Sequence[int]`."""
        item_type = self._get_first_arg_or_any(sequence_type)

        def json_schema_func(_schema: CoreSchemaOrField, handler: GetJsonSchemaHandler) -> JsonSchemaValue:
            items_schema = self._generate_schema(item_type)
            return handler(core_schema.list_schema(items_schema))

        metadata = build_metadata_dict(js_functions=[json_schema_func])

        list_schema = core_schema.list_schema(self.generate_schema(item_type))
        python_schema = core_schema.is_instance_schema(typing.Sequence, cls_repr='Sequence')
        if item_type != Any:
            from ._validators import sequence_validator

            python_schema = core_schema.chain_schema(
                [python_schema, core_schema.no_info_wrap_validator_function(sequence_validator, list_schema)],
            )
        return core_schema.json_or_python_schema(
            json_schema=list_schema, python_schema=python_schema, metadata=metadata
        )

    def _iterable_schema(self, type_: Any) -> core_schema.GeneratorSchema:
        """Generate a schema for an `Iterable`."""
        item_type = self._get_first_arg_or_any(type_)

        return core_schema.generator_schema(self.generate_schema(item_type))

    def _pattern_schema(self, pattern_type: Any) -> core_schema.CoreSchema:
        from . import _validators

        metadata = build_metadata_dict(js_functions=[lambda _1, _2: {'type': 'string', 'format': 'regex'}])
        ser = core_schema.plain_serializer_function_ser_schema(
            attrgetter('pattern'), when_used='json', return_schema=core_schema.str_schema()
        )
        if pattern_type == typing.Pattern or pattern_type == re.Pattern:
            # bare type
            return core_schema.no_info_plain_validator_function(
                _validators.pattern_either_validator, serialization=ser, metadata=metadata
            )

        param = self._get_args_resolving_forward_refs(
            pattern_type,
            required=True,
        )[0]
        if param == str:
            return core_schema.no_info_plain_validator_function(
                _validators.pattern_str_validator, serialization=ser, metadata=metadata
            )
        elif param == bytes:
            return core_schema.no_info_plain_validator_function(
                _validators.pattern_bytes_validator, serialization=ser, metadata=metadata
            )
        else:
            raise PydanticSchemaGenerationError(f'Unable to generate pydantic-core schema for {pattern_type!r}.')

    def _hashable_schema(self) -> core_schema.CoreSchema:
        return core_schema.custom_error_schema(
            core_schema.is_instance_schema(collections.abc.Hashable),
            custom_error_type='is_hashable',
            custom_error_message='Input should be hashable',
        )

    def _dataclass_schema(
        self, dataclass: type[StandardDataclass], origin: type[StandardDataclass] | None
    ) -> core_schema.CoreSchema:
        """Generate schema for a dataclass."""
        with self.defs.get_schema_or_ref(dataclass) as (dataclass_ref, maybe_schema):
            if maybe_schema is not None:
                return maybe_schema

            typevars_map = get_standard_typevars_map(dataclass)
            if origin is not None:
                dataclass = origin

            config = getattr(dataclass, '__pydantic_config__', None)
            with self._config_wrapper_stack.push(config):
                core_config = self._config_wrapper.core_config(dataclass)

                self = self._current_generate_schema

                from ._dataclasses import is_pydantic_dataclass

                if is_pydantic_dataclass(dataclass):
                    fields = dataclass.__pydantic_fields__
                    if typevars_map:
                        for field in fields.values():
                            field.apply_typevars_map(typevars_map, self._types_namespace)
                else:
                    fields = collect_dataclass_fields(
                        dataclass,
                        self._types_namespace,
                        typevars_map=typevars_map,
                    )
                decorators = dataclass.__dict__.get('__pydantic_decorators__') or DecoratorInfos.build(dataclass)
                # Move kw_only=False args to the start of the list, as this is how vanilla dataclasses work.
                # Note that when kw_only is missing or None, it is treated as equivalent to kw_only=True
                args = sorted(
                    (self._generate_dc_field_schema(k, v, decorators) for k, v in fields.items()),
                    key=lambda a: a.get('kw_only') is not False,
                )
                has_post_init = hasattr(dataclass, '__post_init__')
                has_slots = hasattr(dataclass, '__slots__')

                args_schema = core_schema.dataclass_args_schema(
                    dataclass.__name__,
                    args,
                    computed_fields=[
                        self._computed_field_schema(d, decorators.field_serializers)
                        for d in decorators.computed_fields.values()
                    ],
                    collect_init_only=has_post_init,
                )

                inner_schema = apply_validators(args_schema, decorators.root_validators.values(), None)

                model_validators = decorators.model_validators.values()
                inner_schema = apply_model_validators(inner_schema, model_validators, 'inner')

                dc_schema = core_schema.dataclass_schema(
                    dataclass,
                    inner_schema,
                    post_init=has_post_init,
                    ref=dataclass_ref,
                    fields=[field.name for field in dataclasses.fields(dataclass)],
                    slots=has_slots,
                    config=core_config,
                )
                schema = self._apply_model_serializers(dc_schema, decorators.model_serializers.values())
                schema = apply_model_validators(schema, model_validators, 'outer')
                self.defs.definitions[dataclass_ref] = schema
                return core_schema.definition_reference_schema(dataclass_ref)

    def _callable_schema(self, function: Callable[..., Any]) -> core_schema.CallSchema:
        """Generate schema for a Callable.

        TODO support functional validators once we support them in Config
        """
        sig = signature(function)

        type_hints = _typing_extra.get_function_type_hints(function)

        mode_lookup: dict[_ParameterKind, Literal['positional_only', 'positional_or_keyword', 'keyword_only']] = {
            Parameter.POSITIONAL_ONLY: 'positional_only',
            Parameter.POSITIONAL_OR_KEYWORD: 'positional_or_keyword',
            Parameter.KEYWORD_ONLY: 'keyword_only',
        }

        arguments_list: list[core_schema.ArgumentsParameter] = []
        var_args_schema: core_schema.CoreSchema | None = None
        var_kwargs_schema: core_schema.CoreSchema | None = None

        for name, p in sig.parameters.items():
            if p.annotation is sig.empty:
                annotation = Any
            else:
                annotation = type_hints[name]

            parameter_mode = mode_lookup.get(p.kind)
            if parameter_mode is not None:
                arg_schema = self._generate_parameter_schema(name, annotation, p.default, parameter_mode)
                arguments_list.append(arg_schema)
            elif p.kind == Parameter.VAR_POSITIONAL:
                var_args_schema = self.generate_schema(annotation)
            else:
                assert p.kind == Parameter.VAR_KEYWORD, p.kind
                var_kwargs_schema = self.generate_schema(annotation)

        return_schema: core_schema.CoreSchema | None = None
        config_wrapper = self._config_wrapper
        if config_wrapper.validate_return:
            return_hint = type_hints.get('return')
            if return_hint is not None:
                return_schema = self.generate_schema(return_hint)

        return core_schema.call_schema(
            core_schema.arguments_schema(
                arguments_list,
                var_args_schema=var_args_schema,
                var_kwargs_schema=var_kwargs_schema,
                populate_by_name=config_wrapper.populate_by_name,
            ),
            function,
            return_schema=return_schema,
        )

    def _unsubstituted_typevar_schema(self, typevar: typing.TypeVar) -> core_schema.CoreSchema:
        assert isinstance(typevar, typing.TypeVar)

        if typevar.__bound__:
            return self.generate_schema(typevar.__bound__)
        elif typevar.__constraints__:
            return self._union_schema(typing.Union[typevar.__constraints__])  # type: ignore
        else:
            return core_schema.any_schema()

    def _computed_field_schema(
        self,
        d: Decorator[ComputedFieldInfo],
        field_serializers: dict[str, Decorator[FieldSerializerDecoratorInfo]],
    ) -> core_schema.ComputedField:
        try:
            return_type = _decorators.get_function_return_type(d.func, d.info.return_type, self._types_namespace)
        except NameError as e:
            raise PydanticUndefinedAnnotation.from_name_error(e) from e
        if return_type is PydanticUndefined:
            raise PydanticUserError(
                'Computed field is missing return type annotation or specifying `return_type`'
                ' to the `@computed_field` decorator (e.g. `@computed_field(return_type=int|str)`)',
                code='model-field-missing-annotation',
            )

        return_type = replace_types(return_type, self._typevars_map)
        return_type_schema = self.generate_schema(return_type)
        # Apply serializers to computed field if there exist
        return_type_schema = self._apply_field_serializers(
            return_type_schema,
            filter_field_decorator_info_by_field(field_serializers.values(), d.cls_var_name),
            computed_field=True,
        )
        # Handle alias_generator using similar logic to that from
        # pydantic._internal._generate_schema.GenerateSchema._common_field_schema,
        # with field_info -> d.info and name -> d.cls_var_name
        alias_generator = self._config_wrapper.alias_generator
        if alias_generator and (d.info.alias_priority is None or d.info.alias_priority <= 1):
            alias = alias_generator(d.cls_var_name)
            if not isinstance(alias, str):
                raise TypeError(f'alias_generator {alias_generator} must return str, not {alias.__class__}')
            d.info.alias = alias
            d.info.alias_priority = 1

        def set_computed_field_metadata(schema: CoreSchemaOrField, handler: GetJsonSchemaHandler) -> JsonSchemaValue:
            json_schema = handler(schema)

            json_schema['readOnly'] = True

            title = d.info.title
            if title is not None:
                json_schema['title'] = title

            description = d.info.description
            if description is not None:
                json_schema['description'] = description

            return json_schema

        metadata = build_metadata_dict(js_annotation_functions=[set_computed_field_metadata])
        return core_schema.computed_field(
            d.cls_var_name, return_schema=return_type_schema, alias=d.info.alias, metadata=metadata
        )

    def _annotated_schema(self, annotated_type: Any) -> core_schema.CoreSchema:
        """Generate schema for an Annotated type, e.g. `Annotated[int, Field(...)]` or `Annotated[int, Gt(0)]`."""
        source_type, *annotations = self._get_args_resolving_forward_refs(
            annotated_type,
            required=True,
        )
        schema = self._apply_annotations(source_type, annotations)
        # put the default validator last so that TypeAdapter.get_default_value() works
        # even if there are function validators involved
        for annotation in annotations:
            if isinstance(annotation, FieldInfo):
                schema = wrap_default(annotation, schema)
        return schema

    def _get_prepare_pydantic_annotations_for_known_type(
        self, obj: Any, annotations: tuple[Any, ...]
    ) -> tuple[Any, list[Any]] | None:
        from ._std_types_schema import PREPARE_METHODS

        # This check for hashability is only necessary for python 3.7
        try:
            hash(obj)
        except TypeError:
            # obj is definitely not a known type if this fails
            return None

        for gen in PREPARE_METHODS:
            res = gen(obj, annotations, self._config_wrapper.config_dict)
            if res is not None:
                return res

        return None

    def _prepare_annotations(self, source_type: Any, annotations: Iterable[Any]) -> tuple[Any, list[Any]]:
        """Call `__prepare_pydantic_annotations__` if it exists and return a tuple of
            (new_source_type, new_annotations).

        This should be treated conceptually similar to the transformation
        `Annotated[source_type, *annotations]` -> `Annotated[new_source_type, *new_annotations]`
        """
        prepare = getattr(source_type, '__prepare_pydantic_annotations__', None)

        annotations = tuple(annotations)  # make them immutable to avoid confusion over mutating them

        if prepare is not None:
            source_type, annotations = prepare(source_type, tuple(annotations), self._config_wrapper.config_dict)
            annotations = list(annotations)
        else:
            res = self._get_prepare_pydantic_annotations_for_known_type(source_type, annotations)
            if res is not None:
                source_type, annotations = res

        return source_type, list(annotations)

    def _apply_annotations(
        self,
        source_type: Any,
        annotations: list[Any],
        transform_inner_schema: Callable[[CoreSchema], CoreSchema] = lambda x: x,
    ) -> CoreSchema:
        """Apply arguments from `Annotated` or from `FieldInfo` to a schema.

        This gets called by `GenerateSchema._annotated_schema` but differs from it in that it does
        not expect `source_type` to be an `Annotated` object, it expects it to be  the first argument of that
        (in other words, `GenerateSchema._annotated_schema` just unpacks `Annotated`, this process it).
        """
        # expand annotations before we start processing them so that `__prepare_pydantic_annotations` can consume
        # individual items from GroupedMetadata
        annotations = list(_known_annotated_metadata.expand_grouped_metadata(annotations))
        idx = -1
        prepare = getattr(source_type, '__prepare_pydantic_annotations__', None)
        if prepare:
            source_type, annotations = prepare(source_type, tuple(annotations), self._config_wrapper.config_dict)
            annotations = list(annotations)
        else:
            res = self._get_prepare_pydantic_annotations_for_known_type(source_type, tuple(annotations))
            if res is not None:
                source_type, annotations = res

        pydantic_js_annotation_functions: list[GetJsonSchemaFunction] = []

        def inner_handler(obj: Any) -> CoreSchema:
            from_property = self._generate_schema_from_property(obj, obj)
            if from_property is None:
                schema = self._generate_schema(obj)
            else:
                schema = from_property
            metadata_js_function = _extract_get_pydantic_json_schema(obj, schema)
            if metadata_js_function is not None:
                metadata_schema = resolve_original_schema(schema, self.defs.definitions)
                if metadata_schema is not None:
                    self._add_js_function(metadata_schema, metadata_js_function)
            return transform_inner_schema(schema)

        get_inner_schema = CallbackGetCoreSchemaHandler(inner_handler, self)

        while True:
            idx += 1
            if idx == len(annotations):
                break
            annotation = annotations[idx]
            if annotation is None:
                continue
            prepare = getattr(annotation, '__prepare_pydantic_annotations__', None)
            if prepare is not None:
                previous = annotations[:idx]
                remaining = annotations[idx + 1 :]
                new_source_type, remaining = prepare(source_type, tuple(remaining), self._config_wrapper.config_dict)
                annotations = previous + list(remaining)
                if new_source_type is not source_type:
                    return self._apply_annotations(
                        new_source_type,
                        annotations,
                        transform_inner_schema=transform_inner_schema,
                    )
            annotation = annotations[idx]
            get_inner_schema = self._get_wrapped_inner_schema(
                get_inner_schema, annotation, pydantic_js_annotation_functions
            )

        schema = get_inner_schema(source_type)
        if pydantic_js_annotation_functions:
            metadata = CoreMetadataHandler(schema).metadata
            metadata.setdefault('pydantic_js_annotation_functions', []).extend(pydantic_js_annotation_functions)
        return _add_custom_serialization_from_json_encoders(self._config_wrapper.json_encoders, source_type, schema)

    def _apply_single_annotation(self, schema: core_schema.CoreSchema, metadata: Any) -> core_schema.CoreSchema:
        if isinstance(metadata, FieldInfo):
            for field_metadata in metadata.metadata:
                schema = self._apply_single_annotation(schema, field_metadata)

            if metadata.discriminator is not None:
                _discriminated_union.set_discriminator(
                    schema,
                    metadata.discriminator,
                )
            return schema

        if schema['type'] == 'nullable':
            # for nullable schemas, metadata is automatically applied to the inner schema
            inner = schema.get('schema', core_schema.any_schema())
            inner = self._apply_single_annotation(inner, metadata)
            if inner:
                schema['schema'] = inner
            return schema

        original_schema = schema
        ref = schema.get('ref', None)
        if ref is not None:
            schema = schema.copy()
            new_ref = ref + f'_{repr(metadata)}'
            if new_ref in self.defs.definitions:
                return self.defs.definitions[new_ref]
            schema['ref'] = new_ref  # type: ignore
        elif schema['type'] == 'definition-ref':
            ref = schema['schema_ref']
            if ref in self.defs.definitions:
                schema = self.defs.definitions[ref].copy()
                new_ref = ref + f'_{repr(metadata)}'
                if new_ref in self.defs.definitions:
                    return self.defs.definitions[new_ref]
                schema['ref'] = new_ref  # type: ignore

        maybe_updated_schema = _known_annotated_metadata.apply_known_metadata(metadata, schema.copy())

        if maybe_updated_schema is not None:
            return maybe_updated_schema
        return original_schema

    def _apply_single_annotation_json_schema(
        self, schema: core_schema.CoreSchema, metadata: Any
    ) -> core_schema.CoreSchema:
        if isinstance(metadata, FieldInfo):
            for field_metadata in metadata.metadata:
                schema = self._apply_single_annotation_json_schema(schema, field_metadata)
            json_schema_update: JsonSchemaValue = {}
            if metadata.title:
                json_schema_update['title'] = metadata.title
            if metadata.description:
                json_schema_update['description'] = metadata.description
            if metadata.examples:
                json_schema_update['examples'] = metadata.examples

            json_schema_extra = metadata.json_schema_extra
            if json_schema_update or json_schema_extra:

                def json_schema_update_func(
                    core_schema: CoreSchemaOrField, handler: GetJsonSchemaHandler
                ) -> JsonSchemaValue:
                    json_schema = handler(core_schema)
                    json_schema.update(json_schema_update)
                    if isinstance(json_schema_extra, dict):
                        json_schema.update(json_schema_extra)
                    elif callable(json_schema_extra):
                        json_schema_extra(json_schema)
                    return json_schema

                CoreMetadataHandler(schema).metadata.setdefault('pydantic_js_annotation_functions', []).append(
                    json_schema_update_func
                )
        return schema

    def _get_wrapped_inner_schema(
        self,
        get_inner_schema: GetCoreSchemaHandler,
        annotation: Any,
        pydantic_js_annotation_functions: list[GetJsonSchemaFunction],
    ) -> CallbackGetCoreSchemaHandler:
        metadata_get_schema: GetCoreSchemaFunction = getattr(annotation, '__get_pydantic_core_schema__', None) or (
            lambda source, handler: handler(source)
        )

        def new_handler(source: Any) -> core_schema.CoreSchema:
            schema = metadata_get_schema(source, get_inner_schema)
            schema = self._apply_single_annotation(schema, annotation)
            schema = self._apply_single_annotation_json_schema(schema, annotation)

            metadata_js_function = _extract_get_pydantic_json_schema(annotation, schema)
            if metadata_js_function is not None:
                pydantic_js_annotation_functions.append(metadata_js_function)
            return schema

        return CallbackGetCoreSchemaHandler(new_handler, self)

    def _apply_field_serializers(
        self,
        schema: core_schema.CoreSchema,
        serializers: list[Decorator[FieldSerializerDecoratorInfo]],
        computed_field: bool = False,
    ) -> core_schema.CoreSchema:
        """Apply field serializers to a schema."""
        if serializers:
            schema = copy(schema)
            if schema['type'] == 'definitions':
                inner_schema = schema['schema']
                schema['schema'] = self._apply_field_serializers(inner_schema, serializers)
                return schema
            else:
                ref = typing.cast('str|None', schema.get('ref', None))
                if ref is not None:
                    schema = core_schema.definition_reference_schema(ref)

            # use the last serializer to make it easy to override a serializer set on a parent model
            serializer = serializers[-1]
            is_field_serializer, info_arg = inspect_field_serializer(
                serializer.func, serializer.info.mode, computed_field=computed_field
            )

            try:
                return_type = _decorators.get_function_return_type(
                    serializer.func, serializer.info.return_type, self._types_namespace
                )
            except NameError as e:
                raise PydanticUndefinedAnnotation.from_name_error(e) from e

            if return_type is PydanticUndefined:
                return_schema = None
            else:
                return_schema = self.generate_schema(return_type)

            if serializer.info.mode == 'wrap':
                schema['serialization'] = core_schema.wrap_serializer_function_ser_schema(
                    serializer.func,
                    is_field_serializer=is_field_serializer,
                    info_arg=info_arg,
                    return_schema=return_schema,
                    when_used=serializer.info.when_used,
                )
            else:
                assert serializer.info.mode == 'plain'
                schema['serialization'] = core_schema.plain_serializer_function_ser_schema(
                    serializer.func,
                    is_field_serializer=is_field_serializer,
                    info_arg=info_arg,
                    return_schema=return_schema,
                    when_used=serializer.info.when_used,
                )
        return schema

    def _apply_model_serializers(
        self, schema: core_schema.CoreSchema, serializers: Iterable[Decorator[ModelSerializerDecoratorInfo]]
    ) -> core_schema.CoreSchema:
        """Apply model serializers to a schema."""
        ref: str | None = schema.pop('ref', None)  # type: ignore
        if serializers:
            serializer = list(serializers)[-1]
            info_arg = inspect_model_serializer(serializer.func, serializer.info.mode)

            try:
                return_type = _decorators.get_function_return_type(
                    serializer.func, serializer.info.return_type, self._types_namespace
                )
            except NameError as e:
                raise PydanticUndefinedAnnotation.from_name_error(e) from e
            if return_type is PydanticUndefined:
                return_schema = None
            else:
                return_schema = self.generate_schema(return_type)

            if serializer.info.mode == 'wrap':
                ser_schema: core_schema.SerSchema = core_schema.wrap_serializer_function_ser_schema(
                    serializer.func,
                    info_arg=info_arg,
                    return_schema=return_schema,
                    when_used=serializer.info.when_used,
                )
            else:
                # plain
                ser_schema = core_schema.plain_serializer_function_ser_schema(
                    serializer.func,
                    info_arg=info_arg,
                    return_schema=return_schema,
                    when_used=serializer.info.when_used,
                )
            schema['serialization'] = ser_schema
        if ref:
            schema['ref'] = ref  # type: ignore
        return schema


_VALIDATOR_F_MATCH: Mapping[
    tuple[FieldValidatorModes, Literal['no-info', 'general', 'field']],
    Callable[[Callable[..., Any], None, core_schema.CoreSchema], core_schema.CoreSchema],
] = {
    ('before', 'no-info'): lambda f, _, schema: core_schema.no_info_before_validator_function(f, schema),
    ('after', 'no-info'): lambda f, _, schema: core_schema.no_info_after_validator_function(f, schema),
    ('plain', 'no-info'): lambda f, _1, _2: core_schema.no_info_plain_validator_function(f),
    ('wrap', 'no-info'): lambda f, _, schema: core_schema.no_info_wrap_validator_function(f, schema),
    ('before', 'general'): lambda f, _, schema: core_schema.general_before_validator_function(f, schema),
    ('after', 'general'): lambda f, _, schema: core_schema.general_after_validator_function(f, schema),
    ('plain', 'general'): lambda f, _1, _2: core_schema.general_plain_validator_function(f),
    ('wrap', 'general'): lambda f, _, schema: core_schema.general_wrap_validator_function(f, schema),
}


_FIELD_VALIDATOR_F_MATCH: Mapping[
    tuple[FieldValidatorModes, Literal['no-info', 'general', 'field']],
    Callable[[Callable[..., Any], str, core_schema.CoreSchema], core_schema.CoreSchema],
] = {
    ('before', 'field'): core_schema.field_before_validator_function,
    ('after', 'field'): core_schema.field_after_validator_function,
    ('plain', 'field'): lambda f, field_name, _: core_schema.field_plain_validator_function(f, field_name),
    ('wrap', 'field'): core_schema.field_wrap_validator_function,
}


def apply_validators(
    schema: core_schema.CoreSchema,
    validators: Iterable[Decorator[RootValidatorDecoratorInfo]]
    | Iterable[Decorator[ValidatorDecoratorInfo]]
    | Iterable[Decorator[FieldValidatorDecoratorInfo]],
    field_name: str | None,
) -> core_schema.CoreSchema:
    """Apply validators to a schema.

    Args:
        schema: The schema to apply validators on.
        validators: An iterable of validators.
        field_name: The name of the field if validators are being applied to a model field.

    Returns:
        The updated schema.
    """
    for validator in validators:
        info_arg = inspect_validator(validator.func, validator.info.mode)
        if not info_arg:
            val_type: Literal['no-info', 'general', 'field'] = 'no-info'
        elif isinstance(validator.info, (FieldValidatorDecoratorInfo, ValidatorDecoratorInfo)):
            assert field_name is not None, 'field validators must be used within a model field'
            val_type = 'field'
        else:
            val_type = 'general'

        if field_name is None or val_type != 'field':
            schema = _VALIDATOR_F_MATCH[(validator.info.mode, val_type)](validator.func, None, schema)
        else:
            schema = _FIELD_VALIDATOR_F_MATCH[(validator.info.mode, val_type)](validator.func, field_name, schema)
    return schema


def _validators_require_validate_default(validators: Iterable[Decorator[ValidatorDecoratorInfo]]) -> bool:
    """In v1, if any of the validators for a field had `always=True`, the default value would be validated.

    This serves as an auxiliary function for re-implementing that logic, by looping over a provided
    collection of (v1-style) ValidatorDecoratorInfo's and checking if any of them have `always=True`.

    We should be able to drop this function and the associated logic calling it once we drop support
    for v1-style validator decorators. (Or we can extend it and keep it if we add something equivalent
    to the v1-validator `always` kwarg to `field_validator`.)
    """
    for validator in validators:
        if validator.info.always:
            return True
    return False


def apply_model_validators(
    schema: core_schema.CoreSchema,
    validators: Iterable[Decorator[ModelValidatorDecoratorInfo]],
    mode: Literal['inner', 'outer', 'all'],
) -> core_schema.CoreSchema:
    """Apply model validators to a schema.

    If mode == 'inner', only "before" validators are applied
    If mode == 'outer', validators other than "before" are applied
    If mode == 'all', all validators are applied

    Args:
        schema: The schema to apply validators on.
        validators: An iterable of validators.
        mode: The validator mode.

    Returns:
        The updated schema.
    """
    ref: str | None = schema.pop('ref', None)  # type: ignore
    for validator in validators:
        if mode == 'inner' and validator.info.mode != 'before':
            continue
        if mode == 'outer' and validator.info.mode == 'before':
            continue
        info_arg = inspect_validator(validator.func, validator.info.mode)
        if validator.info.mode == 'wrap':
            if info_arg:
                schema = core_schema.general_wrap_validator_function(function=validator.func, schema=schema)
            else:
                schema = core_schema.no_info_wrap_validator_function(function=validator.func, schema=schema)
        elif validator.info.mode == 'before':
            if info_arg:
                schema = core_schema.general_before_validator_function(function=validator.func, schema=schema)
            else:
                schema = core_schema.no_info_before_validator_function(function=validator.func, schema=schema)
        else:
            assert validator.info.mode == 'after'
            if info_arg:
                schema = core_schema.general_after_validator_function(function=validator.func, schema=schema)
            else:
                schema = core_schema.no_info_after_validator_function(function=validator.func, schema=schema)
    if ref:
        schema['ref'] = ref  # type: ignore
    return schema


def wrap_default(field_info: FieldInfo, schema: core_schema.CoreSchema) -> core_schema.CoreSchema:
    """Wrap schema with default schema if default value or `default_factory` are available.

    Args:
        field_info: The field info object.
        schema: The schema to apply default on.

    Returns:
        Updated schema by default value or `default_factory`.
    """
    if field_info.default_factory:
        return core_schema.with_default_schema(
            schema, default_factory=field_info.default_factory, validate_default=field_info.validate_default
        )
    elif field_info.default is not PydanticUndefined:
        return core_schema.with_default_schema(
            schema, default=field_info.default, validate_default=field_info.validate_default
        )
    else:
        return schema


def _extract_get_pydantic_json_schema(tp: Any, schema: CoreSchema) -> GetJsonSchemaFunction | None:
    """Extract `__get_pydantic_json_schema__` from a type, handling the deprecated `__modify_schema__`."""
    js_modify_function = getattr(tp, '__get_pydantic_json_schema__', None)

    if hasattr(tp, '__modify_schema__'):
        from pydantic import BaseModel  # circular reference

        has_custom_v2_modify_js_func = (
            js_modify_function is not None
            and BaseModel.__get_pydantic_json_schema__.__func__
            not in (js_modify_function, getattr(js_modify_function, '__func__', None))
        )

        if not has_custom_v2_modify_js_func:
            raise PydanticUserError(
                'The `__modify_schema__` method is not supported in Pydantic v2. '
                'Use `__get_pydantic_json_schema__` instead.',
                code='custom-json-schema',
            )

    # handle GenericAlias' but ignore Annotated which "lies" about its origin (in this case it would be `int`)
    if hasattr(tp, '__origin__') and not isinstance(tp, type(Annotated[int, 'placeholder'])):
        return _extract_get_pydantic_json_schema(tp.__origin__, schema)

    if js_modify_function is None:
        return None

    return js_modify_function


class _CommonField(TypedDict):
    schema: core_schema.CoreSchema
    validation_alias: str | list[str | int] | list[list[str | int]] | None
    serialization_alias: str | None
    serialization_exclude: bool | None
    frozen: bool | None
    metadata: dict[str, Any]


def _common_field(
    schema: core_schema.CoreSchema,
    *,
    validation_alias: str | list[str | int] | list[list[str | int]] | None = None,
    serialization_alias: str | None = None,
    serialization_exclude: bool | None = None,
    frozen: bool | None = None,
    metadata: Any = None,
) -> _CommonField:
    return {
        'schema': schema,
        'validation_alias': validation_alias,
        'serialization_alias': serialization_alias,
        'serialization_exclude': serialization_exclude,
        'frozen': frozen,
        'metadata': metadata,
    }


class _Definitions:
    """Keeps track of references and definitions."""

    def __init__(self) -> None:
        self.seen: set[str] = set()
        self.definitions: dict[str, core_schema.CoreSchema] = {}

    @contextmanager
    def get_schema_or_ref(self, tp: Any) -> Iterator[tuple[str, None] | tuple[str, CoreSchema]]:
        """Get a definition for `tp` if one exists.

        If a definition exists, a tuple of `(ref_string, CoreSchema)` is returned.
        If no definition exists yet, a tuple of `(ref_string, None)` is returned.

        Note that the returned `CoreSchema` will always be a `DefinitionReferenceSchema`,
        not the actual definition itself.

        This should be called for any type that can be identified by reference.
        This includes any recursive types.

        At present the following types can be named/recursive:

        - BaseModel
        - Dataclasses
        - TypedDict
        - TypeAliasType
        """
        ref = get_type_ref(tp)
        # return the reference if we're either (1) in a cycle or (2) it was already defined
        if ref in self.seen or ref in self.definitions:
            yield (ref, core_schema.definition_reference_schema(ref))
        else:
            self.seen.add(ref)
            try:
                yield (ref, None)
            finally:
                self.seen.discard(ref)


def resolve_original_schema(schema: CoreSchema, definitions: dict[str, CoreSchema]) -> CoreSchema | None:
    if schema['type'] == 'definition-ref':
        return definitions.get(schema['schema_ref'], None)
    elif schema['type'] == 'definitions':
        return schema['schema']
    else:
        return schema
