"""Convert python types to pydantic-core schema."""

from __future__ import annotations as _annotations

import dataclasses
import sys
import typing
import warnings
from collections.abc import Callable, Generator, Iterable, Iterator, Mapping
from contextlib import contextmanager
from copy import copy
from functools import partial
from inspect import Parameter, _ParameterKind
from types import FunctionType, GenericAlias, LambdaType, MethodType, NoneType
from typing import (
    TYPE_CHECKING,
    Any,
    ForwardRef,
    Literal,
    TypeAlias,
    TypeVar,
    overload,
)

import typing_extensions
from pydantic_core import (
    MISSING,
    CoreSchema,
    PydanticUndefined,
    core_schema,
    to_jsonable_python,
)
from typing_extensions import (  # noqa: UP035 (for `get_args` and `get_origin`)
    get_args,
    get_origin,
    is_typeddict,
)
from typing_inspection import typing_objects
from typing_inspection.introspection import AnnotationSource, is_union_origin

from ..aliases import AliasChoices, AliasPath
from ..annotated_handlers import GetCoreSchemaHandler
from ..config import JsonDict, JsonEncoder, JsonSchemaExtraCallable
from ..errors import (
    PydanticForbiddenQualifier,
    PydanticInvalidForJsonSchema,
    PydanticSchemaGenerationError,
    PydanticUndefinedAnnotation,
    PydanticUserError,
)
from ..functional_validators import AfterValidator, BeforeValidator, FieldValidatorModes, PlainValidator, WrapValidator
from ..version import version_short
from ..warnings import (
    ArbitraryTypeWarning,
    PydanticDeprecatedSince20,
    UnsupportedFieldAttributeWarning,
)
from . import _decorators, _discriminated_union, _known_annotated_metadata, _type_refs, _typing_extra
from ._config import ConfigWrapper, ConfigWrapperStack
from ._core_metadata import update_core_metadata
from ._core_utils import get_ref
from ._decorators import (
    Decorator,
    DecoratorInfos,
    FieldSerializerDecoratorInfo,
    FieldValidatorDecoratorInfo,
    ModelSerializerDecoratorInfo,
    ModelValidatorDecoratorInfo,
    inspect_field_serializer,
    inspect_model_serializer,
    inspect_validator,
    mro,
)
from ._fields import (
    takes_validated_data_argument,
    update_field_from_config,
)
from ._forward_ref import PydanticRecursiveRef
from ._generics import replace_types
from ._import_utils import import_cached_base_model, import_cached_field_info
from ._namespace_utils import NamespacesTuple, NsResolver
from ._schema_gather import MissingDefinitionError, gather_schemas_for_cleaning
from ._schema_gen._annotations_handler import EMPTY_ANNOTATIONS_HANDLER, AnnotationsHandler
from ._schema_gen._type_handlers import BaseTypeHandler
from ._schema_gen._type_registry import TypeRegistry
from ._schema_generation_shared import CallbackGetCoreSchemaHandler

if TYPE_CHECKING:
    from ..fields import ComputedFieldInfo, FieldInfo
    from ..types import Discriminator
    from ._schema_generation_shared import GetJsonSchemaFunction

if sys.version_info >= (3, 15):
    pass

_SUPPORTS_TYPEDDICT = sys.version_info >= (3, 12)

FieldDecoratorInfo: TypeAlias = FieldValidatorDecoratorInfo | FieldSerializerDecoratorInfo
FieldDecoratorInfoType = TypeVar('FieldDecoratorInfoType', bound=FieldDecoratorInfo)
AnyFieldDecorator = Decorator[FieldValidatorDecoratorInfo] | Decorator[FieldSerializerDecoratorInfo]

ModifyCoreSchemaWrapHandler: TypeAlias = GetCoreSchemaHandler
GetCoreSchemaFunction: TypeAlias = Callable[[Any, ModifyCoreSchemaWrapHandler], core_schema.CoreSchema]
ParametersCallback: TypeAlias = Callable[[int, str, Any], Literal['skip'] | None]

TUPLE_TYPES: list[type] = [typing.Tuple, tuple]  # noqa: UP006

# Note: This does not play very well with type checkers. For example,
# `a: LambdaType = lambda x: x` will raise a type error by Pyright.
ValidateCallSupportedTypes: TypeAlias = LambdaType | FunctionType | MethodType | partial


VALIDATE_CALL_SUPPORTED_TYPES = get_args(ValidateCallSupportedTypes)
UNSUPPORTED_STANDALONE_FIELDINFO_ATTRIBUTES: list[tuple[str, Any]] = [
    ('alias', None),
    ('validation_alias', None),
    ('serialization_alias', None),
    # will be set if any alias is set, so disable it to avoid double warnings:
    # 'alias_priority',
    ('default', PydanticUndefined),
    ('default_factory', None),
    ('exclude', None),
    ('deprecated', None),
    ('repr', True),
    ('validate_default', None),
    ('frozen', None),
    ('init', None),
    ('init_var', None),
    ('kw_only', None),
]
"""`FieldInfo` attributes (and their default value) that can't be used outside of a model (e.g. in a type adapter or a PEP 695 type alias)."""

_mode_to_validator: dict[
    FieldValidatorModes, type[BeforeValidator | AfterValidator | PlainValidator | WrapValidator]
] = {'before': BeforeValidator, 'after': AfterValidator, 'plain': PlainValidator, 'wrap': WrapValidator}


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
    fields = info.fields
    return '*' in fields or field in fields


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
        if '*' in dec.info.fields:
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


def _extract_json_schema_info_from_field_info(
    info: FieldInfo | ComputedFieldInfo,
) -> tuple[JsonDict | None, JsonDict | JsonSchemaExtraCallable | None]:
    json_schema_updates = {
        'title': info.title,
        'description': info.description,
        'deprecated': bool(info.deprecated) or info.deprecated == '' or None,
        'examples': to_jsonable_python(info.examples),
    }
    json_schema_updates = {k: v for k, v in json_schema_updates.items() if v is not None}
    return (json_schema_updates or None, info.json_schema_extra)


JsonEncoders = dict[type[Any], JsonEncoder]


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
            f'`json_encoders` is deprecated. See https://pydantic.dev/docs/validation/{version_short()}/concepts/serialization/#custom-serializers for alternatives',
            PydanticDeprecatedSince20,
        )

        # TODO: in theory we should check that the schema accepts a serialization key
        schema['serialization'] = core_schema.plain_serializer_function_ser_schema(encoder, when_used='json')
        return schema

    return schema


GENERATE_SCHEMA_ERRORS = (
    PydanticForbiddenQualifier,
    PydanticInvalidForJsonSchema,
    PydanticSchemaGenerationError,
    PydanticUndefinedAnnotation,
)
"""Errors raised during core schema generation. This does *not* include `InvalidSchemaError`, which is raised during schema cleaning."""


def _get_typed_dict_extra_items(typed_dict_cls: type[Any]) -> tuple[bool, Any, bool]:
    """Return whether the TypedDict class is closed, the type of its extra items and whether
    they are read-only (as per PEP 728).

    The `__closed__` and `__extra_items__` attributes only reflect the arguments passed to the class itself,
    so the first class in the (virtual) MRO explicitly specifying one of them is used.
    `extra_items=Never` is normalized to `closed=True`, and the `ReadOnly` qualifier is stripped.
    """
    for base in mro(typed_dict_cls):
        # `__closed__` is `None` when not specified:
        closed = base.__dict__.get('__closed__')
        extra_items = base.__dict__.get('__extra_items__', typing_extensions.NoExtraItems)
        if closed is not None or not typing_objects.is_noextraitems(extra_items):
            break
    else:
        return False, typing_extensions.NoExtraItems, False

    if closed is not None:
        # `closed` and `extra_items` can't be used together:
        return closed, typing_extensions.NoExtraItems, False

    readonly = typing_objects.is_readonly(get_origin(extra_items))
    if readonly:
        extra_items = get_args(extra_items)[0]
    # TODO: `Never` wrapped in a type alias (e.g. `type NoExtras = Never`) or in `Annotated` isn't detected here,
    # and fails during schema generation. Unwrapping should only apply to this check (to preserve alias handling).
    if typing_objects.is_never(extra_items):
        return True, typing_extensions.NoExtraItems, False
    return False, extra_items, readonly


class InvalidSchemaError(Exception):
    """The core schema is invalid."""


class GenerateSchema:
    """Generate core schema for a Pydantic model, dataclass and types like `str`, `datetime`, ... ."""

    __slots__ = (
        '_config_wrapper_stack',
        '_ns_resolver',
        '_typevars_map',
        'field_name_stack',
        'model_type_stack',
        'defs',
        '_registry',
        '_exact_type_handlers',
    )

    def __init__(
        self,
        config_wrapper: ConfigWrapper,
        ns_resolver: NsResolver | None = None,
        typevars_map: Mapping[TypeVar, Any] | None = None,
    ) -> None:
        # we need a stack for recursing into nested models
        self._config_wrapper_stack = ConfigWrapperStack(config_wrapper)
        self._ns_resolver = ns_resolver or NsResolver()
        self._typevars_map = typevars_map
        self.field_name_stack = _FieldNameStack()
        self.model_type_stack = _ModelTypeStack()
        self.defs = _Definitions()
        self._registry = registry = _get_default_registry()
        self._exact_type_handlers = registry._types

    def __init_subclass__(cls) -> None:
        super().__init_subclass__()
        warnings.warn(
            'Subclassing `GenerateSchema` is not supported. The API is highly subject to change in minor versions.',
            UserWarning,
            stacklevel=2,
        )

    @property
    def _config_wrapper(self) -> ConfigWrapper:
        return self._config_wrapper_stack.tail

    @property
    def _types_namespace(self) -> NamespacesTuple:
        return self._ns_resolver.types_namespace

    @property
    def _arbitrary_types(self) -> bool:
        return self._config_wrapper.arbitrary_types_allowed

    def _arbitrary_type_schema(self, tp: Any) -> CoreSchema:
        if not isinstance(tp, type):
            warnings.warn(
                f'{tp!r} is not a Python type (it may be an instance of an object),'
                ' Pydantic will allow any object with no validation since we cannot even'
                ' enforce that the input is an instance of the given type.'
                ' To get rid of this error wrap the type with `pydantic.SkipValidation`.',
                ArbitraryTypeWarning,
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

    def _apply_discriminator_to_union(
        self, schema: CoreSchema, discriminator: str | Discriminator | None
    ) -> CoreSchema:
        if discriminator is None:
            return schema
        try:
            return _discriminated_union.apply_discriminator(
                schema,
                discriminator,
                self.defs._definitions,
            )
        except _discriminated_union.MissingDefinitionForUnionRef:
            # defer until defs are resolved
            _discriminated_union.set_discriminator_in_metadata(
                schema,
                discriminator,
            )
            return schema

    def clean_schema(self, schema: CoreSchema) -> CoreSchema:
        return self.defs.finalize_schema(schema)

    def _add_js_function(self, metadata_schema: CoreSchema, js_function: Callable[..., Any]) -> None:
        metadata = metadata_schema.get('metadata', {})
        pydantic_js_functions = metadata.setdefault('pydantic_js_functions', [])
        # because of how we generate core schemas for nested generic models
        # we can end up adding `BaseModel.__get_pydantic_json_schema__` multiple times
        # this check may fail to catch duplicates if the function is a `functools.partial`
        # or something like that, but if it does it'll fail by inserting the duplicate
        if js_function not in pydantic_js_functions:
            pydantic_js_functions.append(js_function)
        metadata_schema['metadata'] = metadata

    def generate_schema(
        self,
        obj: Any,
    ) -> core_schema.CoreSchema:
        """Generate core schema.

        Args:
            obj: The object to generate core schema for.

        Returns:
            The generated core schema.

        Raises:
            PydanticUndefinedAnnotation:
                If it is not possible to evaluate forward reference.
            PydanticSchemaGenerationError:
                If it is not possible to generate pydantic-core schema.
            TypeError:
                - If `alias_generator` returns a disallowed type (must be str, AliasPath or AliasChoices).
            PydanticUserError:
                - If `typing.TypedDict` is used instead of `typing_extensions.TypedDict` on Python < 3.12.
        """
        origin = get_origin(obj)
        try:
            handler_class = self._exact_type_handlers.get(obj if origin is None else origin)
        except TypeError:
            # Unhashable:
            handler_class = None
        if handler_class is not None:
            # Types matched by exact type (e.g. `int`, `list[int]`) are handled first. They can't have
            # a `__get_pydantic_core_schema__()` or `__get_pydantic_json_schema__()` method:
            schema = handler_class(self)._generate_schema(obj, origin, EMPTY_ANNOTATIONS_HANDLER)
            return _add_custom_serialization_from_json_encoders(self._config_wrapper.json_encoders, obj, schema)

        schema: CoreSchema | None = None
        if origin is None:
            # If the type has an origin, it is guaranteed to *not* be an ordinary class that could have
            # a `__get_pydantic_core_schema__()` method:
            schema = self._generate_schema_from_get_schema_method(obj, obj)

        if schema is None:
            schema = self._generate_schema_inner(obj, origin)

        # `__get_pydantic_json_schema__()` is checked on the origin if it exists:
        metadata_js_function = _extract_get_pydantic_json_schema(origin if origin is not None else obj)
        if metadata_js_function is not None:
            metadata_schema = resolve_original_schema(schema, self.defs)
            if metadata_schema:
                self._add_js_function(metadata_schema, metadata_js_function)

        schema = _add_custom_serialization_from_json_encoders(self._config_wrapper.json_encoders, obj, schema)

        return schema

    def _get_exact_type_handler(self, tp: Any) -> BaseTypeHandler | None:
        """Get the type handler registered for the exact type `tp` (the type itself if unparameterized, or its origin)."""
        try:
            handler_class = self._exact_type_handlers.get(tp)
        except TypeError:
            # `tp` is unhashable:
            return None
        if handler_class is None:
            return None
        return handler_class(self)

    def _get_predicate_type_handler(self, tp: Any) -> BaseTypeHandler | None:
        """Get the type handler whose predicate matches `tp` (the type itself if unparameterized, or its origin)."""
        handler_class = self._registry.get_predicate_handler(tp)
        if handler_class is None:
            return None
        return handler_class(self)

    def _generate_with_type_handler(
        self, handler: BaseTypeHandler, obj: Any, origin: Any, annotations_handler: AnnotationsHandler
    ) -> CoreSchema:
        """Generate the core schema of `obj` using the type handler, taking care of references if supported."""
        if handler.is_referenceable and (ref := handler.get_reference(obj, origin)) is not None:
            with self.defs.get_definition_ref_schema(ref=ref) as maybe_schema:
                if maybe_schema is not None:
                    return maybe_schema
                schema = handler._generate_schema(obj, origin, annotations_handler)
                schema['ref'] = ref  # pyright: ignore[reportGeneralTypeIssues]
                return self.defs.create_definition_reference_schema(schema)
        return handler._generate_schema(obj, origin, annotations_handler)

    def _reuse_model_schema(self, schema: CoreSchema) -> CoreSchema:
        """Reuse the (already built) core schema of a Pydantic model."""
        if schema['type'] == 'definitions':
            schema = self.defs.unpack_definitions(schema)
        if get_ref(schema):
            return self.defs.create_definition_reference_schema(schema)
        return schema

    def _resolve_self_type(self, obj: Any) -> Any:
        obj = self.model_type_stack.get()
        if obj is None:
            raise PydanticUserError('`typing.Self` is invalid in this context', code='invalid-self-type')
        return obj

    def _generate_schema_from_get_schema_method(self, obj: Any, source: Any) -> core_schema.CoreSchema | None:
        BaseModel_ = import_cached_base_model()

        get_schema = getattr(obj, '__get_pydantic_core_schema__', None)

        if (
            get_schema is not None
            # BaseModel.__get_pydantic_core_schema__ is defined for backwards compatibility,
            # to allow existing code to call `super().__get_pydantic_core_schema__` in Pydantic
            # model that overrides `__get_pydantic_core_schema__`. However, it raises a deprecation
            # warning stating that the method will be removed, and during the core schema gen we actually
            # don't call the method:
            and getattr(get_schema, '__func__', None) is not BaseModel_.__get_pydantic_core_schema__.__func__  # pyright: ignore[reportFunctionMemberAccess]
        ):
            # Some referenceable types might have a `__get_pydantic_core_schema__` method
            # defined on it by users (e.g. on a dataclass). This generally doesn't play well
            # as these types are already recognized by the `GenerateSchema` class and isn't ideal
            # as we might end up calling `any_type_ref()` (relatively expensive) on types that are actually
            # not referenceable:
            with self.defs.get_definition_ref_schema(ref=_type_refs.any_type_ref(obj, get_origin(obj))) as maybe_schema:
                if maybe_schema is not None:
                    return maybe_schema

            if obj is source:
                ref_mode = 'unpack'
            else:
                ref_mode = 'to-def'
            schema = get_schema(
                source, CallbackGetCoreSchemaHandler(self._generate_schema_inner, self, ref_mode=ref_mode)
            )
            if schema['type'] == 'definitions':
                schema = self.defs.unpack_definitions(schema)

            ref = get_ref(schema)
            if ref:
                return self.defs.create_definition_reference_schema(schema)

            # Note: if schema is of type `'definition-ref'`, we might want to copy it as a
            # safety measure (because these are inlined in place -- i.e. mutated directly)
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
            obj = _typing_extra.eval_type(obj, *self._types_namespace)
        except NameError as e:
            raise PydanticUndefinedAnnotation.from_name_error(e) from e

        # if obj is still a ForwardRef, it means we can't evaluate it, raise PydanticUndefinedAnnotation
        if isinstance(obj, ForwardRef):
            raise PydanticUndefinedAnnotation(obj.__forward_arg__, f'Unable to evaluate forward reference {obj}')

        if self._typevars_map:
            obj = replace_types(obj, self._typevars_map)

        return obj

    @overload
    def _get_args_resolving_forward_refs(self, obj: Any, required: Literal[True]) -> tuple[Any, ...]: ...

    @overload
    def _get_args_resolving_forward_refs(self, obj: Any) -> tuple[Any, ...] | None: ...

    def _get_args_resolving_forward_refs(self, obj: Any, required: bool = False) -> tuple[Any, ...] | None:
        args = get_args(obj)
        if args:
            if isinstance(obj, GenericAlias):
                # PEP 585 generic aliases don't convert args to ForwardRefs, unlike `typing.List/Dict` etc.
                # This was fixed in https://github.com/python/cpython/pull/30900 (Python 3.11).
                # TODO: this shouldn't be necessary (probably even this `_get_args_resolving_forward_refs()` function)
                # once we drop support for Python 3.10 *or* if we implement our own `typing._eval_type()` implementation.
                args = (ForwardRef(a) if isinstance(a, str) else a for a in args)
            args = tuple(self._resolve_forward_ref(a) if isinstance(a, ForwardRef) else a for a in args)
        elif required:  # pragma: no cover
            raise TypeError(f'Expected {obj} to have generic parameters but it had none')
        return args

    def _generate_schema_inner(self, obj: Any, origin: Any | None = PydanticUndefined) -> core_schema.CoreSchema:
        if typing_objects.is_self(obj):
            obj = self._resolve_self_type(obj)
            # The resolved type can be a parametrized generic (e.g. `GenericDataclass[int]`),
            # so the origin provided by the caller (computed on `Self`) is stale:
            origin = get_origin(obj)

        origin = origin if origin is not PydanticUndefined else get_origin(obj)

        if origin is None:
            if isinstance(obj, dict):
                # we assume this is already a valid schema
                return obj  # type: ignore[return-value]

            if isinstance(obj, str):
                obj = ForwardRef(obj)

            if isinstance(obj, ForwardRef):
                return self.generate_schema(self._resolve_forward_ref(obj))

            if isinstance(obj, PydanticRecursiveRef):
                return core_schema.definition_reference_schema(schema_ref=obj.type_ref)

            handler = self._get_exact_type_handler(obj) or self._get_predicate_type_handler(obj)
        else:
            if typing_objects.is_annotated(origin):
                return self._annotated_schema(obj)

            handler = self._get_exact_type_handler(origin)
            if handler is None:
                # Generic classes not matched by exact type (e.g. a user-defined generic class) can define a
                # `__get_pydantic_core_schema__()` method:
                schema = self._generate_schema_from_get_schema_method(origin, obj)
                if schema is not None:
                    return schema
                handler = self._get_predicate_type_handler(origin)

        if handler is not None:
            return self._generate_with_type_handler(handler, obj, origin, EMPTY_ANNOTATIONS_HANDLER)

        if self._arbitrary_types:
            return self._arbitrary_type_schema(origin if origin is not None else obj)
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
        schema, metadata = self._common_field_schema(name, field_info, decorators)
        return core_schema.typed_dict_field(
            schema,
            required=False if not field_info.is_required() else required,
            serialization_exclude=field_info.exclude,
            validation_alias=_convert_to_aliases(field_info.validation_alias),
            serialization_alias=field_info.serialization_alias,
            serialization_exclude_if=field_info.exclude_if,
            metadata=metadata,
        )

    def _generate_md_field_schema(
        self,
        name: str,
        field_info: FieldInfo,
        decorators: DecoratorInfos,
    ) -> core_schema.ModelField:
        """Prepare a ModelField to represent a model field."""
        schema, metadata = self._common_field_schema(name, field_info, decorators)
        return core_schema.model_field(
            schema,
            serialization_exclude=field_info.exclude,
            validation_alias=_convert_to_aliases(field_info.validation_alias),
            serialization_alias=field_info.serialization_alias,
            serialization_exclude_if=field_info.exclude_if,
            frozen=field_info.frozen,
            metadata=metadata,
        )

    def _generate_dc_field_schema(
        self,
        name: str,
        field_info: FieldInfo,
        decorators: DecoratorInfos,
    ) -> core_schema.DataclassField:
        """Prepare a DataclassField to represent the parameter/field, of a dataclass."""
        schema, metadata = self._common_field_schema(name, field_info, decorators)
        return core_schema.dataclass_field(
            name,
            schema,
            init=field_info.init,
            init_only=field_info.init_var or None,
            kw_only=None if field_info.kw_only else False,
            serialization_exclude=field_info.exclude,
            validation_alias=_convert_to_aliases(field_info.validation_alias),
            serialization_alias=field_info.serialization_alias,
            serialization_exclude_if=field_info.exclude_if,
            frozen=field_info.frozen,
            metadata=metadata,
        )

    def _common_field_schema(  # C901
        self, name: str, field_info: FieldInfo, decorators: DecoratorInfos
    ) -> tuple[CoreSchema, dict[str, Any]]:
        source_type, annotations = field_info.annotation, field_info.metadata

        def set_discriminator(schema: CoreSchema) -> CoreSchema:
            schema = self._apply_discriminator_to_union(schema, field_info.discriminator)
            return schema

        # Convert `@field_validator` decorators to `Before/After/Plain/WrapValidator` instances:
        if decorators.field_validators:
            validators_from_decorators = [
                _mode_to_validator[decorator.info.mode]._from_decorator(decorator)
                for decorator in filter_field_decorator_info_by_field(decorators.field_validators.values(), name)
            ]
        else:
            validators_from_decorators = []

        # Not using `field_name_stack.push()` to avoid the context manager overhead:
        field_name_stack = self.field_name_stack._stack
        field_name_stack.append(name)
        try:
            if field_info.discriminator is not None:
                schema = self._apply_annotations(
                    source_type, annotations + validators_from_decorators, transform_inner_schema=set_discriminator
                )
            else:
                schema = self._apply_annotations(
                    source_type,
                    annotations + validators_from_decorators if validators_from_decorators else annotations,
                )
        finally:
            field_name_stack.pop()

        # the default validator needs to go outside of any other validators
        # so that it is the topmost validator for the field validator
        # which uses it to check if the field has a default value or not
        if not field_info.is_required():
            schema = wrap_default(field_info, schema)

        if decorators.field_serializers:
            schema = self._apply_field_serializers(
                schema, filter_field_decorator_info_by_field(decorators.field_serializers.values(), name)
            )

        pydantic_js_updates, pydantic_js_extra = _extract_json_schema_info_from_field_info(field_info)
        core_metadata: dict[str, Any] = {}
        update_core_metadata(
            core_metadata, pydantic_js_updates=pydantic_js_updates, pydantic_js_extra=pydantic_js_extra
        )

        return schema, core_metadata

    def _generate_parameter_schema(
        self,
        name: str,
        annotation: type[Any],
        source: AnnotationSource,
        default: Any = Parameter.empty,
        mode: Literal['positional_only', 'positional_or_keyword', 'keyword_only'] | None = None,
    ) -> core_schema.ArgumentsParameter:
        """Generate the definition of a parameter in a function signature.

        This definition is meant to be used for the `'arguments'` core schema, which will be replaced
        in V3 by the `'arguments-v3`'.
        """
        FieldInfo = import_cached_field_info()

        if default is Parameter.empty:
            field = FieldInfo.from_annotation(annotation, _source=source)
        else:
            field = FieldInfo.from_annotated_attribute(annotation, default, _source=source)

        assert field.annotation is not None, 'field.annotation should not be None when generating a schema'
        update_field_from_config(self._config_wrapper, name, field)

        with self.field_name_stack.push(name):
            schema = self._apply_annotations(
                field.annotation,
                [field],
                # Because we pass `field` as metadata above (required for attributes relevant for
                # JSON Scheme generation), we need to ignore the potential warnings about `FieldInfo`
                # attributes that will not be used:
                check_unsupported_field_info_attributes=False,
            )

        if not field.is_required():
            schema = wrap_default(field, schema)

        parameter_schema = core_schema.arguments_parameter(
            name,
            schema,
            mode=mode,
            alias=_convert_to_aliases(field.validation_alias),
        )

        return parameter_schema

    def _generate_parameter_v3_schema(
        self,
        name: str,
        annotation: Any,
        source: AnnotationSource,
        mode: Literal[
            'positional_only',
            'positional_or_keyword',
            'keyword_only',
            'var_args',
            'var_kwargs_uniform',
            'var_kwargs_unpacked_typed_dict',
        ],
        default: Any = Parameter.empty,
    ) -> core_schema.ArgumentsV3Parameter:
        """Generate the definition of a parameter in a function signature.

        This definition is meant to be used for the `'arguments-v3'` core schema, which will replace
        the `'arguments`' schema in V3.
        """
        FieldInfo = import_cached_field_info()

        if default is Parameter.empty:
            field = FieldInfo.from_annotation(annotation, _source=source)
        else:
            field = FieldInfo.from_annotated_attribute(annotation, default, _source=source)
        update_field_from_config(self._config_wrapper, name, field)

        with self.field_name_stack.push(name):
            schema = self._apply_annotations(
                field.annotation,
                [field],
                # Because we pass `field` as metadata above (required for attributes relevant for
                # JSON Scheme generation), we need to ignore the potential warnings about `FieldInfo`
                # attributes that will not be used:
                check_unsupported_field_info_attributes=False,
            )

        if not field.is_required():
            schema = wrap_default(field, schema)

        parameter_schema = core_schema.arguments_v3_parameter(
            name=name,
            schema=schema,
            mode=mode,
            alias=_convert_to_aliases(field.validation_alias),
        )

        return parameter_schema

    def _arguments_schema(
        self, function: ValidateCallSupportedTypes, parameters_callback: ParametersCallback | None = None
    ) -> core_schema.ArgumentsSchema:
        """Generate schema for a Signature."""
        mode_lookup: dict[_ParameterKind, Literal['positional_only', 'positional_or_keyword', 'keyword_only']] = {
            Parameter.POSITIONAL_ONLY: 'positional_only',
            Parameter.POSITIONAL_OR_KEYWORD: 'positional_or_keyword',
            Parameter.KEYWORD_ONLY: 'keyword_only',
        }

        sig = _typing_extra.signature_no_eval(function)
        globalns, localns = self._types_namespace
        type_hints = _typing_extra.get_function_type_hints(function, globalns=globalns, localns=localns)

        arguments_list: list[core_schema.ArgumentsParameter] = []
        var_args_schema: core_schema.CoreSchema | None = None
        var_kwargs_schema: core_schema.CoreSchema | None = None
        var_kwargs_mode: core_schema.VarKwargsMode | None = None

        core_config = self._config_wrapper.core_config(title=None)

        for i, (name, p) in enumerate(sig.parameters.items()):
            if p.annotation is sig.empty:
                annotation = typing.cast(Any, Any)
            else:
                annotation = type_hints[name]

            if parameters_callback is not None:
                result = parameters_callback(i, name, annotation)
                if result == 'skip':
                    continue

            parameter_mode = mode_lookup.get(p.kind)
            if parameter_mode is not None:
                arg_schema = self._generate_parameter_schema(
                    name, annotation, AnnotationSource.FUNCTION, p.default, parameter_mode
                )
                arguments_list.append(arg_schema)
            elif p.kind == Parameter.VAR_POSITIONAL:
                var_args_schema = self.generate_schema(annotation)
            else:
                assert p.kind == Parameter.VAR_KEYWORD, p.kind

                unpack_type = _typing_extra.unpack_type(annotation)
                if unpack_type is not None:
                    origin = get_origin(unpack_type) or unpack_type
                    if not is_typeddict(origin):
                        raise PydanticUserError(
                            f'Expected a `TypedDict` class inside `Unpack[...]`, got {unpack_type!r}',
                            code='unpack-typed-dict',
                        )
                    non_pos_only_param_names = {
                        name for name, p in sig.parameters.items() if p.kind != Parameter.POSITIONAL_ONLY
                    }
                    overlapping_params = non_pos_only_param_names.intersection(origin.__annotations__)
                    if overlapping_params:
                        raise PydanticUserError(
                            f'Typed dictionary {origin.__name__!r} overlaps with parameter'
                            f'{"s" if len(overlapping_params) >= 2 else ""} '
                            f'{", ".join(repr(p) for p in sorted(overlapping_params))}',
                            code='overlapping-unpack-typed-dict',
                        )

                    var_kwargs_mode = 'unpacked-typed-dict'
                    var_kwargs_schema = self.generate_schema(unpack_type)
                else:
                    var_kwargs_mode = 'uniform'
                    var_kwargs_schema = self.generate_schema(annotation)

        return core_schema.arguments_schema(
            arguments_list,
            var_args_schema=var_args_schema,
            var_kwargs_mode=var_kwargs_mode,
            var_kwargs_schema=var_kwargs_schema,
            validate_by_name=core_config.get('validate_by_name'),
        )

    def _arguments_v3_schema(
        self, function: ValidateCallSupportedTypes, parameters_callback: ParametersCallback | None = None
    ) -> core_schema.ArgumentsV3Schema:
        mode_lookup: dict[
            _ParameterKind, Literal['positional_only', 'positional_or_keyword', 'var_args', 'keyword_only']
        ] = {
            Parameter.POSITIONAL_ONLY: 'positional_only',
            Parameter.POSITIONAL_OR_KEYWORD: 'positional_or_keyword',
            Parameter.VAR_POSITIONAL: 'var_args',
            Parameter.KEYWORD_ONLY: 'keyword_only',
        }

        sig = _typing_extra.signature_no_eval(function)
        globalns, localns = self._types_namespace
        type_hints = _typing_extra.get_function_type_hints(function, globalns=globalns, localns=localns)

        parameters_list: list[core_schema.ArgumentsV3Parameter] = []
        core_config = self._config_wrapper.core_config(title=None)

        for i, (name, p) in enumerate(sig.parameters.items()):
            if parameters_callback is not None:
                result = parameters_callback(i, name, p.annotation)
                if result == 'skip':
                    continue

            if p.annotation is Parameter.empty:
                annotation = typing.cast(Any, Any)
            else:
                annotation = type_hints[name]

            parameter_mode = mode_lookup.get(p.kind)
            if parameter_mode is None:
                assert p.kind == Parameter.VAR_KEYWORD, p.kind

                unpack_type = _typing_extra.unpack_type(annotation)
                if unpack_type is not None:
                    origin = get_origin(unpack_type) or unpack_type
                    if not is_typeddict(origin):
                        raise PydanticUserError(
                            f'Expected a `TypedDict` class inside `Unpack[...]`, got {unpack_type!r}',
                            code='unpack-typed-dict',
                        )
                    non_pos_only_param_names = {
                        name for name, p in sig.parameters.items() if p.kind != Parameter.POSITIONAL_ONLY
                    }
                    overlapping_params = non_pos_only_param_names.intersection(origin.__annotations__)
                    if overlapping_params:
                        raise PydanticUserError(
                            f'Typed dictionary {origin.__name__!r} overlaps with parameter'
                            f'{"s" if len(overlapping_params) >= 2 else ""} '
                            f'{", ".join(repr(p) for p in sorted(overlapping_params))}',
                            code='overlapping-unpack-typed-dict',
                        )
                    parameter_mode = 'var_kwargs_unpacked_typed_dict'
                    annotation = unpack_type
                else:
                    parameter_mode = 'var_kwargs_uniform'

            parameters_list.append(
                self._generate_parameter_v3_schema(
                    name, annotation, AnnotationSource.FUNCTION, parameter_mode, default=p.default
                )
            )

        return core_schema.arguments_v3_schema(
            parameters_list,
            validate_by_name=core_config.get('validate_by_name'),
        )

    def _computed_field_schema(
        self,
        d: Decorator[ComputedFieldInfo],
        field_serializers: dict[str, Decorator[FieldSerializerDecoratorInfo]],
    ) -> core_schema.ComputedField:
        if d.info.return_type is not PydanticUndefined:
            return_type = d.info.return_type
        else:
            try:
                # Do not pass in globals as the function could be defined in a different module.
                # Instead, let `get_callable_return_type` infer the globals to use, but still pass
                # in locals that may contain a parent/rebuild namespace:
                return_type = _decorators.get_callable_return_type(d.func, localns=self._types_namespace.locals)
            except NameError as e:
                raise PydanticUndefinedAnnotation.from_name_error(e) from e
        if return_type is PydanticUndefined:
            raise PydanticUserError(
                'Computed field is missing return type annotation or specifying `return_type`'
                ' to the `@computed_field` decorator (e.g. `@computed_field(return_type=int | str)`)',
                code='model-field-missing-annotation',
            )

        return_type = replace_types(return_type, self._typevars_map)
        # Create a new ComputedFieldInfo so that different type parametrizations of the same
        # generic model's computed field can have different return types.
        d.info = dataclasses.replace(d.info, return_type=return_type)
        return_type_schema = self.generate_schema(return_type)
        # Apply serializers to computed field if there exist
        return_type_schema = self._apply_field_serializers(
            return_type_schema,
            filter_field_decorator_info_by_field(field_serializers.values(), d.cls_var_name),
        )

        pydantic_js_updates, pydantic_js_extra = _extract_json_schema_info_from_field_info(d.info)
        core_metadata: dict[str, Any] = {}
        update_core_metadata(
            core_metadata,
            pydantic_js_updates={'readOnly': True, **(pydantic_js_updates if pydantic_js_updates else {})},
            pydantic_js_extra=pydantic_js_extra,
        )
        exclude_if = d.info.exclude_if
        # TODO: Should we support exclude_if from annotations?
        return core_schema.computed_field(
            d.cls_var_name,
            return_schema=return_type_schema,
            alias=d.info.alias,
            serialization_exclude_if=exclude_if,
            metadata=core_metadata,
        )

    def _annotated_schema(self, annotated_type: Any) -> core_schema.CoreSchema:
        """Generate schema for an Annotated type, e.g. `Annotated[int, Field(...)]` or `Annotated[int, Gt(0)]`."""
        FieldInfo = import_cached_field_info()
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

    def _apply_annotations(
        self,
        source_type: Any,
        annotations: list[Any],
        transform_inner_schema: Callable[[CoreSchema], CoreSchema] | None = None,
        check_unsupported_field_info_attributes: bool = True,
    ) -> CoreSchema:
        """Apply arguments from `Annotated` or from `FieldInfo` to a schema.

        This gets called by `GenerateSchema._annotated_schema` but differs from it in that it does
        not expect `source_type` to be an `Annotated` object, it expects it to be  the first argument of that
        (in other words, `GenerateSchema._annotated_schema` just unpacks `Annotated`, this process it).

        Annotations are applied in two steps:

        1. The metadata known by the type handler of `source_type` (see `BaseTypeHandler.known_metadata`,
           e.g. `Gt` for `int`, `MaxLen` for `str`) is provided to the type handler through an annotations
           handler, so that it is applied directly to the core schema of the type.
        2. The remaining annotations (e.g. validators, or any annotation with a `__get_pydantic_core_schema__()`
           method) are applied in order, on top of the schema generated during the first step.
        """
        target: _AnnotationsTarget | None = None
        annotations_handler: AnnotationsHandler | None = None
        if annotations:
            annotations, has_known_metadata = _known_annotated_metadata.expand_annotations(annotations)
            if has_known_metadata and (target := self._get_annotations_target(source_type)) is not None:
                annotations_handler = AnnotationsHandler(annotations, target.handler.known_metadata)
                annotations = annotations_handler.remaining_annotations

        def inner_handler(obj: Any) -> CoreSchema:
            if annotations_handler is not None and obj is source_type:
                schema = self._generate_target_schema(target, annotations_handler)  # pyright: ignore[reportArgumentType]
            else:
                origin = get_origin(obj)
                handler = self._get_exact_type_handler(obj if origin is None else origin)
                if handler is not None:
                    # See `generate_schema()`:
                    schema = handler._generate_schema(obj, origin, EMPTY_ANNOTATIONS_HANDLER)
                else:
                    schema = None
                    if origin is None:
                        # If the type has an origin, it is guaranteed to *not* be an ordinary class that could have
                        # a `__get_pydantic_core_schema__()` method:
                        schema = self._generate_schema_from_get_schema_method(obj, source_type)

                    if schema is None:
                        schema = self._generate_schema_inner(obj, origin)

                    # `__get_pydantic_json_schema__()` is checked on the origin if it exists:
                    metadata_js_function = _extract_get_pydantic_json_schema(origin if origin is not None else obj)
                    if metadata_js_function is not None:
                        metadata_schema = resolve_original_schema(schema, self.defs)
                        if metadata_schema is not None:
                            self._add_js_function(metadata_schema, metadata_js_function)

                if annotations_handler is not None:
                    # A `__get_pydantic_core_schema__()` method called the handler with a different type than the
                    # one the known metadata was collected for. Apply it on the generated schema:
                    for annotation in annotations_handler.iter_annotations():
                        schema = self._apply_single_annotation(schema, annotation)

            if transform_inner_schema is not None:
                return transform_inner_schema(schema)
            return schema

        if not annotations:
            schema = inner_handler(source_type)
            return _add_custom_serialization_from_json_encoders(self._config_wrapper.json_encoders, source_type, schema)

        pydantic_js_annotation_functions: list[GetJsonSchemaFunction] = []

        get_inner_schema = CallbackGetCoreSchemaHandler(inner_handler, self)

        for annotation in annotations:
            get_inner_schema = self._get_wrapped_inner_schema(
                get_inner_schema,
                annotation,
                pydantic_js_annotation_functions,
                check_unsupported_field_info_attributes=check_unsupported_field_info_attributes,
            )

        schema = get_inner_schema(source_type)
        if pydantic_js_annotation_functions:
            core_metadata = schema.setdefault('metadata', {})
            update_core_metadata(core_metadata, pydantic_js_annotation_functions=pydantic_js_annotation_functions)
        return _add_custom_serialization_from_json_encoders(self._config_wrapper.json_encoders, source_type, schema)

    def _get_annotations_target(self, source_type: Any) -> _AnnotationsTarget | None:
        """Get the type handler (and related information) that the metadata attached to `source_type` should target.

        Optional types (e.g. `int | None`) are unwrapped, so that the metadata is applied to the non-`None` member.
        `None` is returned if the type handler doesn't know about any metadata, or if the type defines
        a `__get_pydantic_core_schema__()` method.
        """
        obj = source_type
        origin = get_origin(obj)
        nullable = allow_missing = unwrapped = False
        if origin is not None and is_union_origin(origin):
            members: list[Any] = []
            for arg in get_args(obj):
                if arg is None or arg is NoneType:
                    nullable = True
                elif arg is MISSING:
                    allow_missing = True
                else:
                    members.append(arg)
            if len(members) == 1 and not isinstance(members[0], (str, ForwardRef)):
                obj = members[0]
                origin = get_origin(obj)
                unwrapped = True
            else:
                nullable = allow_missing = False

        tp = obj if origin is None else origin
        exact = True
        handler = self._get_exact_type_handler(tp)
        if handler is None:
            if _has_get_pydantic_core_schema(tp):
                return None
            exact = False
            handler = self._get_predicate_type_handler(tp)
        if handler is None or not handler.known_metadata:
            return None
        return _AnnotationsTarget(handler, exact, obj, origin, unwrapped, nullable, allow_missing)

    def _generate_target_schema(
        self, target: _AnnotationsTarget, annotations_handler: AnnotationsHandler
    ) -> CoreSchema:
        obj, origin = target.obj, target.origin
        schema = self._generate_with_type_handler(target.handler, obj, origin, annotations_handler)
        if not target.exact:
            # Mimic what `generate_schema()` does:
            metadata_js_function = _extract_get_pydantic_json_schema(origin if origin is not None else obj)
            if metadata_js_function is not None:
                metadata_schema = resolve_original_schema(schema, self.defs)
                if metadata_schema is not None:
                    self._add_js_function(metadata_schema, metadata_js_function)
        if target.unwrapped:
            schema = _add_custom_serialization_from_json_encoders(self._config_wrapper.json_encoders, obj, schema)
            if target.nullable:
                schema = core_schema.nullable_schema(schema)
            if target.allow_missing:
                schema = core_schema.missing_sentinel_schema(schema)
        return schema

    def _apply_single_annotation(
        self,
        schema: core_schema.CoreSchema,
        metadata: Any,
        check_unsupported_field_info_attributes: bool = True,
    ) -> core_schema.CoreSchema:
        FieldInfo = import_cached_field_info()

        if isinstance(metadata, FieldInfo):
            if (
                check_unsupported_field_info_attributes
                # HACK: we don't want to emit the warning for `FieldInfo` subclasses, because FastAPI does weird manipulations
                # with its subclasses and their annotations:
                and type(metadata) is FieldInfo
            ):
                for attr, value in self._get_unsupported_field_info_attributes(metadata):
                    warnings.warn(
                        f'The {attr!r} attribute with value {value!r} was provided to the `Field()` function, '
                        f'which has no effect in the context it was used. {attr!r} is field-specific metadata, '
                        'and can only be attached to a model field using `Annotated` metadata or by assignment. '
                        'This may have happened because an `Annotated` type alias using the `type` statement was '
                        'used, or if the `Field()` function was attached to a single member of a union type.',
                        category=UnsupportedFieldAttributeWarning,
                    )

                # Inside a model, a standalone `default_factory` is already reported as unsupported above:
                if metadata.default_factory_takes_validated_data and self.model_type_stack.get() is None:
                    warnings.warn(
                        "A 'default_factory' taking validated data as an argument was provided to the `Field()` function, "
                        'but no validated data is available in the context it was used.',
                        category=UnsupportedFieldAttributeWarning,
                    )

            for field_metadata in metadata.metadata:
                schema = self._apply_single_annotation(schema, field_metadata)

            if metadata.discriminator is not None:
                schema = self._apply_discriminator_to_union(schema, metadata.discriminator)
            return schema

        if schema['type'] == 'nullable':
            # for nullable schemas, metadata is automatically applied to the inner schema
            inner = schema.get('schema', core_schema.any_schema())
            inner = self._apply_single_annotation(inner, metadata)
            if inner:
                schema['schema'] = inner
            return schema

        if schema['type'] == 'missing-sentinel' and (inner := schema.get('schema')) is not None:
            # Same behavior as for nullable schemas: metadata is automatically applied to the inner schema
            inner = self._apply_single_annotation(inner, metadata)
            if inner:
                schema['schema'] = inner
            return schema

        original_schema = schema
        ref = schema.get('ref')
        if ref is not None:
            schema = schema.copy()
            new_ref = ref + f'_{repr(metadata)}'
            if (existing := self.defs.get_schema_from_ref(new_ref)) is not None:
                return existing
            schema['ref'] = new_ref  # pyright: ignore[reportGeneralTypeIssues]
        elif schema['type'] == 'definition-ref':
            ref = schema['schema_ref']
            if (referenced_schema := self.defs.get_schema_from_ref(ref)) is not None:
                schema = referenced_schema.copy()
                new_ref = ref + f'_{repr(metadata)}'
                if (existing := self.defs.get_schema_from_ref(new_ref)) is not None:
                    return existing
                schema['ref'] = new_ref  # pyright: ignore[reportGeneralTypeIssues]

        maybe_updated_schema = _known_annotated_metadata.apply_known_metadata(metadata, schema)

        if maybe_updated_schema is not None:
            return maybe_updated_schema
        return original_schema

    def _apply_single_annotation_json_schema(
        self, schema: core_schema.CoreSchema, metadata: Any
    ) -> core_schema.CoreSchema:
        FieldInfo = import_cached_field_info()

        if isinstance(metadata, FieldInfo):
            for field_metadata in metadata.metadata:
                schema = self._apply_single_annotation_json_schema(schema, field_metadata)

            pydantic_js_updates, pydantic_js_extra = _extract_json_schema_info_from_field_info(metadata)
            core_metadata = schema.setdefault('metadata', {})
            update_core_metadata(
                core_metadata, pydantic_js_updates=pydantic_js_updates, pydantic_js_extra=pydantic_js_extra
            )
        return schema

    def _get_unsupported_field_info_attributes(self, field_info: FieldInfo) -> list[tuple[str, Any]]:
        """Get the list of unsupported `FieldInfo` attributes when not directly used in `Annotated` for field annotations."""
        unused_metadata: list[tuple[str, Any]] = []
        for unused_metadata_name, unset_value in UNSUPPORTED_STANDALONE_FIELDINFO_ATTRIBUTES:
            if (
                (unused_metadata_value := getattr(field_info, unused_metadata_name)) is not unset_value
                # `default` and `default_factory` can still be used with a type adapter, so only include them
                # if used with a model-like class:
                and (
                    unused_metadata_name not in ('default', 'default_factory')
                    or self.model_type_stack.get() is not None
                )
                # Setting `alias` will set `validation/serialization_alias` as well, so we want to avoid duplicate warnings:
                and (
                    unused_metadata_name not in ('validation_alias', 'serialization_alias')
                    or 'alias' not in field_info._attributes_set
                )
            ):
                unused_metadata.append((unused_metadata_name, unused_metadata_value))

        return unused_metadata

    def _get_wrapped_inner_schema(
        self,
        get_inner_schema: GetCoreSchemaHandler,
        annotation: Any,
        pydantic_js_annotation_functions: list[GetJsonSchemaFunction],
        check_unsupported_field_info_attributes: bool = False,
    ) -> CallbackGetCoreSchemaHandler:
        annotation_get_schema: GetCoreSchemaFunction | None = getattr(annotation, '__get_pydantic_core_schema__', None)

        def new_handler(source: Any) -> core_schema.CoreSchema:
            if annotation_get_schema is not None:
                schema = annotation_get_schema(source, get_inner_schema)
            else:
                schema = get_inner_schema(source)
                schema = self._apply_single_annotation(
                    schema,
                    annotation,
                    check_unsupported_field_info_attributes=check_unsupported_field_info_attributes,
                )
                schema = self._apply_single_annotation_json_schema(schema, annotation)

            metadata_js_function = _extract_get_pydantic_json_schema(annotation)
            if metadata_js_function is not None:
                pydantic_js_annotation_functions.append(metadata_js_function)
            return schema

        return CallbackGetCoreSchemaHandler(new_handler, self)

    def _apply_field_serializers(
        self,
        schema: core_schema.CoreSchema,
        serializers: list[Decorator[FieldSerializerDecoratorInfo]],
    ) -> core_schema.CoreSchema:
        """Apply field serializers to a schema."""
        if serializers:
            schema = copy(schema)
            if schema['type'] == 'definitions':
                inner_schema = schema['schema']
                schema['schema'] = self._apply_field_serializers(inner_schema, serializers)
                return schema
            elif 'ref' in schema:
                schema = self.defs.create_definition_reference_schema(schema)

            # use the last serializer to make it easy to override a serializer set on a parent model
            serializer = serializers[-1]
            is_field_serializer, info_arg = inspect_field_serializer(serializer.func, serializer.info.mode)

            if serializer.info.return_type is not PydanticUndefined:
                return_type = serializer.info.return_type
            else:
                try:
                    # Do not pass in globals as the function could be defined in a different module.
                    # Instead, let `get_callable_return_type` infer the globals to use, but still pass
                    # in locals that may contain a parent/rebuild namespace:
                    return_type = _decorators.get_callable_return_type(
                        serializer.func, localns=self._types_namespace.locals
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

            if serializer.info.return_type is not PydanticUndefined:
                return_type = serializer.info.return_type
            else:
                try:
                    # Do not pass in globals as the function could be defined in a different module.
                    # Instead, let `get_callable_return_type` infer the globals to use, but still pass
                    # in locals that may contain a parent/rebuild namespace:
                    return_type = _decorators.get_callable_return_type(
                        serializer.func, localns=self._types_namespace.locals
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


def _convert_to_aliases(
    alias: str | AliasChoices | AliasPath | None,
) -> str | list[str | int] | list[list[str | int]] | None:
    if isinstance(alias, (AliasChoices, AliasPath)):
        return alias.convert_to_aliases()
    else:
        return alias


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
        info_arg = inspect_validator(validator.func, mode=validator.info.mode, type='model')
        if validator.info.mode == 'wrap':
            if info_arg:
                schema = core_schema.with_info_wrap_validator_function(function=validator.func, schema=schema)
            else:
                schema = core_schema.no_info_wrap_validator_function(function=validator.func, schema=schema)
        elif validator.info.mode == 'before':
            if info_arg:
                schema = core_schema.with_info_before_validator_function(function=validator.func, schema=schema)
            else:
                schema = core_schema.no_info_before_validator_function(function=validator.func, schema=schema)
        else:
            assert validator.info.mode == 'after'
            if info_arg:
                schema = core_schema.with_info_after_validator_function(function=validator.func, schema=schema)
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
            schema,
            default_factory=field_info.default_factory,
            default_factory_takes_data=takes_validated_data_argument(field_info.default_factory),
            validate_default=field_info.validate_default,
        )
    elif field_info.default is not PydanticUndefined:
        return core_schema.with_default_schema(
            schema, default=field_info.default, validate_default=field_info.validate_default
        )
    else:
        return schema


def _extract_get_pydantic_json_schema(tp: Any) -> GetJsonSchemaFunction | None:
    """Extract `__get_pydantic_json_schema__` from a type."""
    return getattr(tp, '__get_pydantic_json_schema__', None)


def resolve_original_schema(schema: CoreSchema, definitions: _Definitions) -> CoreSchema | None:
    if schema['type'] == 'definition-ref':
        return definitions.get_schema_from_ref(schema['schema_ref'])
    elif schema['type'] == 'definitions':
        return schema['schema']
    else:
        return schema


def _inlining_behavior(
    def_ref: core_schema.DefinitionReferenceSchema,
) -> Literal['inline', 'keep', 'preserve_metadata']:
    """Determine the inlining behavior of the `'definition-ref'` schema.

    - If no `'serialization'` schema and no metadata is attached, the schema can safely be inlined.
    - If it has metadata but only related to the deferred discriminator application, it can be inlined
      provided that such metadata is kept.
    - Otherwise, the schema should not be inlined. Doing so would remove the `'serialization'` schema or metadata.
    """
    if 'serialization' in def_ref:
        return 'keep'
    metadata = def_ref.get('metadata')
    if not metadata:
        return 'inline'
    if len(metadata) == 1 and 'pydantic_internal_union_discriminator' in metadata:
        return 'preserve_metadata'
    return 'keep'


class _Definitions:
    """Keeps track of references and definitions."""

    _recursively_seen: set[str]
    """A set of recursively seen references.

    When a referenceable type is encountered, the `get_schema_or_ref` context manager is
    entered to compute the reference. If the type references itself by some way (e.g. for
    a dataclass a Pydantic model, the class can be referenced as a field annotation),
    entering the context manager again will yield a `'definition-ref'` schema that should
    short-circuit the normal generation process, as the reference was already in this set.
    """

    _definitions: dict[str, core_schema.CoreSchema]
    """A mapping of references to their corresponding schema.

    When a schema for a referenceable type is generated, it is stored in this mapping. If the
    same type is encountered again, the reference is yielded by the `get_schema_or_ref` context
    manager.
    """

    def __init__(self) -> None:
        self._recursively_seen = set()
        self._definitions = {}

    @contextmanager
    def get_definition_ref_schema(self, *, ref: str) -> Generator[core_schema.DefinitionReferenceSchema | None]:
        """Get a `'definition-ref'` schema for `ref`, if the reference was already encountered (or if we are in a cycle).
        Get a definition for `tp` if one exists.

        This should be called for any type that can be identified by reference.
        This includes any recursive types.

        At present the following types can be named/recursive:

        - Pydantic model
        - Pydantic and stdlib dataclasses
        - Typed dictionaries
        - Named tuples
        - `TypeAliasType` instances
        - Enums
        """
        # return the reference if we're either (1) in a cycle or (2) it the reference was already encountered:
        if ref in self._recursively_seen or ref in self._definitions:
            yield core_schema.definition_reference_schema(ref)
        else:
            self._recursively_seen.add(ref)
            try:
                yield None
            finally:
                self._recursively_seen.discard(ref)

    def get_schema_from_ref(self, ref: str) -> CoreSchema | None:
        """Resolve the schema from the given reference."""
        return self._definitions.get(ref)

    def create_definition_reference_schema(self, schema: CoreSchema) -> core_schema.DefinitionReferenceSchema:
        """Store the schema as a definition and return a `'definition-reference'` schema pointing to it.

        The schema must have a reference attached to it.
        """
        ref = schema['ref']  # pyright: ignore
        self._definitions[ref] = schema
        return core_schema.definition_reference_schema(ref)

    def unpack_definitions(self, schema: core_schema.DefinitionsSchema) -> CoreSchema:
        """Store the definitions of the `'definitions'` core schema and return the inner core schema."""
        for def_schema in schema['definitions']:
            self._definitions[def_schema['ref']] = def_schema  # pyright: ignore
        return schema['schema']

    def finalize_schema(self, schema: CoreSchema) -> CoreSchema:
        """Finalize the core schema.

        This traverses the core schema and referenced definitions, replaces `'definition-ref'` schemas
        by the referenced definition if possible, and applies deferred discriminators.
        """
        definitions = self._definitions
        try:
            gather_result = gather_schemas_for_cleaning(
                schema,
                definitions=definitions,
            )
        except MissingDefinitionError as e:
            raise InvalidSchemaError from e

        remaining_defs: dict[str, CoreSchema] = {}

        # References that will be kept as actual definitions (i.e. not inlined). When resolving an
        # "intermediate" `'definition-ref'` schema (see `_resolve_definition()`), we must not follow
        # the reference chain through one of these definitions:
        kept_refs = {
            ref
            for ref, inlinable_def_ref in gather_result['collected_references'].items()
            if inlinable_def_ref is None or _inlining_behavior(inlinable_def_ref) == 'keep'
        }

        # Note: this logic doesn't play well when core schemas with deferred discriminator metadata
        # and references are encountered. See the `test_deferred_discriminated_union_and_references()` test.
        for ref, inlinable_def_ref in gather_result['collected_references'].items():
            if inlinable_def_ref is not None and (inlining_behavior := _inlining_behavior(inlinable_def_ref)) != 'keep':
                if inlining_behavior == 'inline':
                    # `ref` was encountered, and only once:
                    #  - `inlinable_def_ref` is a `'definition-ref'` schema and is guaranteed to be
                    #    the only one. Transform it into the definition it points to.
                    #  - Do not store the definition in the `remaining_defs`.
                    inlinable_def_ref.clear()  # pyright: ignore[reportAttributeAccessIssue]
                    inlinable_def_ref.update(self._resolve_definition(ref, definitions, kept_refs))  # pyright: ignore
                elif inlining_behavior == 'preserve_metadata':
                    # `ref` was encountered, and only once, but contains discriminator metadata.
                    # We will do the same thing as if `inlining_behavior` was `'inline'`, but make
                    # sure to keep the metadata for the deferred discriminator application logic below.
                    meta = inlinable_def_ref.pop('metadata')
                    inlinable_def_ref.clear()  # pyright: ignore[reportAttributeAccessIssue]
                    inlinable_def_ref.update(self._resolve_definition(ref, definitions, kept_refs))  # pyright: ignore
                    inlinable_def_ref['metadata'] = meta
            else:
                # `ref` was encountered, at least two times (or only once, but with metadata or a serialization schema):
                # - Do not inline the `'definition-ref'` schemas (they are not provided in the gather result anyway).
                # - Store the definition in the `remaining_defs`
                remaining_defs[ref] = self._resolve_definition(ref, definitions, kept_refs)

        for cs in gather_result['deferred_discriminator_schemas']:
            discriminator: str | None = cs['metadata'].pop('pydantic_internal_union_discriminator', None)  # pyright: ignore[reportTypedDictNotRequiredAccess]
            if discriminator is None:
                # This can happen in rare scenarios, when a deferred schema is present multiple times in the
                # gather result (e.g. when using the `Sequence` type -- see `test_sequence_discriminated_union()`).
                # In this case, a previous loop iteration applied the discriminator and so we can just skip it here.
                continue
            applied = _discriminated_union.apply_discriminator(cs.copy(), discriminator, remaining_defs)
            # Mutate the schema directly to have the discriminator applied
            cs.clear()  # pyright: ignore[reportAttributeAccessIssue]
            cs.update(applied)  # pyright: ignore

        if remaining_defs:
            schema = core_schema.definitions_schema(schema=schema, definitions=[*remaining_defs.values()])
        return schema

    def _resolve_definition(self, ref: str, definitions: dict[str, CoreSchema], kept_refs: set[str]) -> CoreSchema:
        definition = definitions[ref]
        if definition['type'] != 'definition-ref':
            return definition

        # Some `'definition-ref'` schemas might act as "intermediate" references (e.g. when using
        # a PEP 695 type alias (which is referenceable) that references another PEP 695 type alias):
        visited: set[str] = set()
        while definition['type'] == 'definition-ref' and _inlining_behavior(definition) == 'inline':
            schema_ref = definition['schema_ref']
            if schema_ref in kept_refs and schema_ref != ref:
                # The reference chain leads to a *different* definition that is kept on its own (e.g. a
                # recursive model referenced through a PEP 695 type alias). Resolve to a reference
                # pointing to it instead of following the chain and inlining a copy of that definition,
                # which could otherwise introduce a reference cycle in the resulting schema.
                # Note: when `schema_ref == ref`, the reference points back to itself, which is a genuine
                # circular reference and is reported as an error by the `visited` logic below.
                return {**definition, 'ref': ref}
            if schema_ref in visited:
                raise PydanticUserError(
                    f'{ref} contains a circular reference to itself.', code='circular-reference-schema'
                )
            visited.add(schema_ref)
            definition = definitions[schema_ref]
        return {**definition, 'ref': ref}  # pyright: ignore[reportReturnType]


class _FieldNameStack:
    __slots__ = ('_stack',)

    def __init__(self) -> None:
        self._stack: list[str] = []

    @contextmanager
    def push(self, field_name: str) -> Iterator[None]:
        self._stack.append(field_name)
        try:
            yield
        finally:
            self._stack.pop()

    def get(self) -> str | None:
        if self._stack:
            return self._stack[-1]
        else:
            return None


class _ModelTypeStack:
    __slots__ = ('_stack',)

    def __init__(self) -> None:
        self._stack: list[type] = []

    @contextmanager
    def push(self, type_obj: type) -> Iterator[None]:
        self._stack.append(type_obj)
        try:
            yield
        finally:
            self._stack.pop()

    def get(self) -> type | None:
        if self._stack:
            return self._stack[-1]
        else:
            return None


class _AnnotationsTarget(typing.NamedTuple):
    handler: BaseTypeHandler
    exact: bool
    """Whether the type handler was matched by exact type."""
    obj: Any
    origin: Any
    unwrapped: bool
    """Whether `obj` was unwrapped from an optional type."""
    nullable: bool
    allow_missing: bool


def _has_get_pydantic_core_schema(tp: Any) -> bool:
    BaseModel_ = import_cached_base_model()
    get_schema = getattr(tp, '__get_pydantic_core_schema__', None)
    return (
        get_schema is not None
        and getattr(get_schema, '__func__', None) is not BaseModel_.__get_pydantic_core_schema__.__func__  # pyright: ignore[reportFunctionMemberAccess]
    )


_default_registry: TypeRegistry | None = None


def _get_default_registry() -> TypeRegistry:
    """Get the default type registry, importing the type handlers modules on first use (to avoid import cycles)."""
    global _default_registry
    if _default_registry is None:
        from ._schema_gen import _types  # noqa: F401
        from ._schema_gen._type_registry import default_registry

        _default_registry = default_registry
    return _default_registry
