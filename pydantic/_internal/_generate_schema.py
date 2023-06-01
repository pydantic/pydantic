"""
Convert python types to pydantic-core schema.
"""
from __future__ import annotations as _annotations

import collections.abc
import dataclasses
import inspect
import re
import sys
import typing
import warnings
from functools import partial
from inspect import Parameter, _ParameterKind, signature
from itertools import chain
from operator import attrgetter
from types import FunctionType, LambdaType, MethodType
from typing import TYPE_CHECKING, Any, Callable, ForwardRef, Iterable, Mapping, TypeVar, Union, cast

from pydantic_core import CoreSchema, core_schema
from typing_extensions import Annotated, Final, Literal, TypeAliasType, TypedDict, get_args, get_origin, is_typeddict

from ..config import ConfigDict
from ..errors import PydanticSchemaGenerationError, PydanticUndefinedAnnotation, PydanticUserError
from ..fields import AliasChoices, AliasPath, FieldInfo
from ..json_schema import JsonSchemaValue
from . import _discriminated_union, _known_annotated_metadata, _typing_extra
from ._annotated_handlers import GetCoreSchemaHandler, GetJsonSchemaHandler
from ._config import ConfigWrapper
from ._core_metadata import (
    CoreMetadataHandler,
    build_metadata_dict,
)
from ._core_utils import (
    CoreSchemaOrField,
    consolidate_refs,
    define_expected_missing_refs,
    get_type_ref,
    is_list_like_schema_with_items_schema,
    remove_unnecessary_invalid_definitions,
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
from ._fields import (
    Undefined,
    collect_dataclass_fields,
    get_type_hints_infer_globalns,
)
from ._forward_ref import PydanticForwardRef, PydanticRecursiveRef
from ._generics import get_standard_typevars_map, recursively_defined_type_refs, replace_types
from ._schema_generation_shared import (
    CallbackGetCoreSchemaHandler,
    UnpackedRefJsonSchemaHandler,
    wrap_json_schema_fn_for_model_or_custom_type_with_ref_unpacking,
)
from ._typing_extra import is_finalvar
from ._utils import lenient_issubclass

if TYPE_CHECKING:
    from ..main import BaseModel
    from ..validators import FieldValidatorModes
    from ._dataclasses import StandardDataclass
    from ._schema_generation_shared import GetJsonSchemaFunction

_SUPPORTS_TYPEDDICT = sys.version_info >= (3, 12)

FieldDecoratorInfo = Union[ValidatorDecoratorInfo, FieldValidatorDecoratorInfo, FieldSerializerDecoratorInfo]
FieldDecoratorInfoType = TypeVar('FieldDecoratorInfoType', bound=FieldDecoratorInfo)
AnyFieldDecorator = Union[
    Decorator[ValidatorDecoratorInfo],
    Decorator[FieldValidatorDecoratorInfo],
    Decorator[FieldSerializerDecoratorInfo],
]

ModifyCoreSchemaWrapHandler = GetCoreSchemaHandler
GetCoreSchemaFunction = Callable[[Any, ModifyCoreSchemaWrapHandler], core_schema.CoreSchema]


def check_validator_fields_against_field_name(
    info: FieldDecoratorInfo,
    field: str,
) -> bool:
    if isinstance(info, (ValidatorDecoratorInfo, FieldValidatorDecoratorInfo)):
        if '*' in info.fields:
            return True
    for v_field_name in info.fields:
        if v_field_name == field:
            return True
    return False


def check_decorator_fields_exist(decorators: Iterable[AnyFieldDecorator], fields: Iterable[str]) -> None:
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
    schema: core_schema.CoreSchema, each_item_validators: list[Decorator[ValidatorDecoratorInfo]]
) -> core_schema.CoreSchema:
    # This V1 compatibility shim should eventually be removed

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


def modify_model_json_schema(
    schema_or_field: CoreSchemaOrField, handler: GetJsonSchemaHandler, *, cls: Any
) -> JsonSchemaValue:
    """Add title and description for model-like classes' JSON schema"""
    wrapped_handler = UnpackedRefJsonSchemaHandler(handler)

    json_schema = handler(schema_or_field)
    original_schema = wrapped_handler.resolve_ref_schema(json_schema)
    if 'title' not in original_schema:
        original_schema['title'] = cls.__name__
    docstring = cls.__doc__
    if docstring and 'description' not in original_schema:
        original_schema['description'] = docstring
    return json_schema


class GenerateSchema:
    __slots__ = '_config_wrapper_stack', 'types_namespace', 'typevars_map', 'recursion_cache', 'definitions'

    def __init__(
        self,
        config_wrapper: ConfigWrapper,
        types_namespace: dict[str, Any] | None,
        typevars_map: dict[Any, Any] | None = None,
    ):
        # we need a stack for recursing into child models
        self._config_wrapper_stack: list[ConfigWrapper] = [config_wrapper]
        self.types_namespace = types_namespace
        self.typevars_map = typevars_map

        self.recursion_cache: dict[str, core_schema.DefinitionReferenceSchema] = {}
        self.definitions: dict[str, core_schema.CoreSchema] = {}

    @property
    def config_wrapper(self) -> ConfigWrapper:
        return self._config_wrapper_stack[-1]

    @property
    def arbitrary_types(self) -> bool:
        return self.config_wrapper.arbitrary_types_allowed

    def generate_schema(
        self,
        obj: Any,
        from_dunder_get_core_schema: bool = True,
        from_prepare_args: bool = True,
    ) -> core_schema.CoreSchema:
        if isinstance(obj, type(Annotated[int, 123])):
            return self._annotated_schema(obj)
        return self._generate_schema_for_type(
            obj, from_dunder_get_core_schema=from_dunder_get_core_schema, from_prepare_args=from_prepare_args
        )

    def _generate_schema_for_type(
        self,
        obj: Any,
        from_dunder_get_core_schema: bool = True,
        from_prepare_args: bool = True,
    ) -> CoreSchema:
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
            metadata = CoreMetadataHandler(schema).metadata
            metadata.setdefault('pydantic_js_functions', []).append(metadata_js_function)

        schema = remove_unnecessary_invalid_definitions(schema)

        ref = schema.get('ref', None)
        if ref:
            # definitions and definition-ref schemas don't have 'ref', causing the type error ignored on the next line
            self.definitions[ref] = schema

        return schema

    def model_schema(self, cls: type[BaseModel]) -> core_schema.CoreSchema:
        """
        Generate schema for a pydantic model.

        Since models generate schemas for themselves this method is public and can be called
        from within BaseModel's metaclass.
        """
        model_ref, schema = self._get_or_cache_recursive_ref(cls)
        if schema is not None:
            return schema

        fields = cls.model_fields
        decorators = cls.__pydantic_decorators__
        check_decorator_fields_exist(
            chain(
                decorators.field_validators.values(),
                decorators.field_serializers.values(),
                decorators.validators.values(),
            ),
            fields.keys(),
        )
        config_wrapper = ConfigWrapper(cls.model_config, check=False)
        core_config = config_wrapper.core_config(cls)
        metadata = build_metadata_dict(js_functions=[partial(modify_model_json_schema, cls=cls)])

        model_validators = decorators.model_validators.values()

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
                metadata={**metadata, **root_field['metadata']},
            )
        else:
            self._config_wrapper_stack.append(config_wrapper)
            try:
                fields_schema: core_schema.CoreSchema = core_schema.model_fields_schema(
                    {k: self._generate_md_field_schema(k, v, decorators) for k, v in fields.items()},
                    computed_fields=[self._computed_field_schema(d) for d in decorators.computed_fields.values()],
                )
            finally:
                self._config_wrapper_stack.pop()

            inner_schema = apply_validators(fields_schema, decorators.root_validators.values())
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

        model_schema = consolidate_refs(model_schema)
        schema = self._apply_model_serializers(model_schema, decorators.model_serializers.values())
        return apply_model_validators(schema, model_validators, 'outer')

    def _generate_schema_from_prepare_annotations(self, obj: Any) -> core_schema.CoreSchema | None:
        """
        Try to generate schema from either the `__get_pydantic_core_schema__` function or
        `__pydantic_core_schema__` property.

        Note: `__get_pydantic_core_schema__` takes priority so it can
        decide whether to use a `__pydantic_core_schema__` attribute, or generate a fresh schema.
        """
        new_obj, new_annotations = self._prepare_annotations(obj, [])
        if new_obj is not obj or new_annotations:
            return self._apply_annotations(
                lambda x: x,
                new_obj,
                new_annotations,
            )
        return None

    def _generate_schema_from_property(self, obj: Any, source: Any) -> core_schema.CoreSchema | None:
        """
        Try to generate schema from either the `__get_pydantic_core_schema__` function or
        `__pydantic_core_schema__` property.

        Note: `__get_pydantic_core_schema__` takes priority so it can
        decide whether to use a `__pydantic_core_schema__` attribute, or generate a fresh schema.
        """
        get_schema = getattr(obj, '__get_pydantic_core_schema__', None)
        if get_schema is None:
            return None

        if len(inspect.signature(get_schema).parameters) == 1:
            # (source) -> CoreSchema
            return get_schema(source)

        return get_schema(source, CallbackGetCoreSchemaHandler(self._generate_schema, self.generate_schema))

    def _generate_schema(self, obj: Any) -> core_schema.CoreSchema:  # noqa: C901
        """
        Recursively generate a pydantic-core schema for any supported python type.
        """
        if isinstance(obj, dict):
            # we assume this is already a valid schema
            return obj  # type: ignore[return-value]

        if isinstance(obj, str):
            obj = ForwardRef(obj)

        if isinstance(obj, ForwardRef):
            # we assume that types_namespace has the target of forward references in its scope,
            # but this could fail, for example, if calling Validator on an imported type which contains
            # forward references to other types only defined in the module from which it was imported
            # `Validator(SomeImportedTypeAliasWithAForwardReference)`
            # or the equivalent for BaseModel
            # class Model(BaseModel):
            #   x: SomeImportedTypeAliasWithAForwardReference
            try:
                obj = _typing_extra.evaluate_fwd_ref(obj, globalns=self.types_namespace)
            except NameError as e:
                raise PydanticUndefinedAnnotation.from_name_error(e) from e

            # if obj is still a ForwardRef, it means we can't evaluate it, raise PydanticUndefinedAnnotation
            if isinstance(obj, ForwardRef):
                raise PydanticUndefinedAnnotation(obj.__forward_arg__, f'Unable to evaluate forward reference {obj}')

            if self.typevars_map:
                obj = replace_types(obj, self.typevars_map)

            return self.generate_schema(obj)

        from ..main import BaseModel

        if lenient_issubclass(obj, BaseModel):
            return self.model_schema(obj)

        if isinstance(obj, PydanticRecursiveRef):
            return core_schema.definition_reference_schema(schema_ref=obj.type_ref)

        if isinstance(obj, PydanticForwardRef):
            if not obj.deferred_actions:
                return obj.schema
            resolved_model = obj.resolve_model()
            if isinstance(resolved_model, PydanticForwardRef):
                # If you still have a PydanticForwardRef after resolving, it should be deeply nested enough that it will
                # eventually be substituted out. So it is safe to return an invalid schema here.
                # TODO: Replace this with a (new) CoreSchema that, if present at any level, makes validation fail
                #   Issue: https://github.com/pydantic/pydantic-core/issues/619
                return core_schema.none_schema(
                    metadata={'invalid': True, 'pydantic_debug_self_schema': resolved_model.schema}
                )
            else:
                model_ref = get_type_ref(resolved_model)
                return core_schema.definition_reference_schema(model_ref)

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
            return self._typed_dict_schema(obj, None)
        elif _typing_extra.is_namedtuple(obj):
            return self._namedtuple_schema(obj)
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
                return core_schema.AnySchema(type='any')
            return self.generate_schema(get_args(obj)[0])
        elif isinstance(obj, (FunctionType, LambdaType, MethodType, partial)):
            return self._callable_schema(obj)

        if _typing_extra.is_dataclass(obj):
            return self._dataclass_schema(obj, None)

        origin = get_origin(obj)

        if isinstance(obj, TypeAliasType) or isinstance(origin, TypeAliasType):
            return self._type_alias_type_schema(obj)

        if origin is None:
            return self._arbitrary_type_schema(obj, obj)

        # Need to handle generic dataclasses before looking for the schema properties because attribute accesses
        # on _GenericAlias delegate to the origin type, so lose the information about the concrete parametrization
        # As a result, currently, there is no way to cache the schema for generic dataclasses. This may be possible
        # to resolve by modifying the value returned by `Generic.__class_getitem__`, but that is a dangerous game.
        if _typing_extra.is_dataclass(origin):
            return self._dataclass_schema(obj, origin)

        from_property = self._generate_schema_from_property(origin, obj)
        if from_property is not None:
            return from_property

        if _typing_extra.origin_is_union(origin):
            return self._union_schema(obj)
        elif issubclass(origin, typing.Tuple):  # type: ignore[arg-type]
            return self._tuple_schema(obj)
        elif is_typeddict(origin):
            return self._typed_dict_schema(obj, origin)
        elif issubclass(origin, typing.Type):  # type: ignore[arg-type]
            return self._subclass_schema(obj)
        elif issubclass(origin, typing.Sequence):
            if origin in {typing.Sequence, collections.abc.Sequence}:
                return self._sequence_schema(obj)
            else:
                return self._arbitrary_type_schema(obj, origin)
        elif issubclass(origin, (typing.Iterable, collections.abc.Iterable)):
            # Because typing.Iterable does not have a specified `__init__` signature, we don't validate into subclasses
            if origin in {typing.Iterable, collections.abc.Iterable, typing.Generator, collections.abc.Generator}:
                return self._iterable_schema(obj)
            else:
                return self._arbitrary_type_schema(obj, origin)
        elif issubclass(origin, (re.Pattern, typing.Pattern)):
            return self._pattern_schema(obj)
        else:
            return self._arbitrary_type_schema(obj, origin)

    def _arbitrary_type_schema(self, obj: Any, type_: Any) -> CoreSchema:
        if self.arbitrary_types and isinstance(type_, type):
            return core_schema.is_instance_schema(type_)
        else:
            raise PydanticSchemaGenerationError(
                f'Unable to generate pydantic-core schema for {obj!r}. '
                'Set `arbitrary_types_allowed=True` in the model_config to ignore this error'
                ' or implement `__get_pydantic_core_schema__` on your type to fully support it.'
                '\n\nIf you got this error by calling handler(<some type>) within'
                ' `__get_pydantic_core_schema__` then you likely need to call'
                ' `handler.generate_schema(<some type>)` since we do not call'
                ' `__get_pydantic_core_schema__` on `<some type>` otherwise to avoid infinite recursion.'
            )

    def _generate_td_field_schema(
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
        *,
        required: bool = True,
    ) -> core_schema.ModelField:
        """
        Prepare a ModelField to represent a model field.
        """
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
        """
        Prepare a DataclassField to represent the parameter/field, of a dataclass
        """
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
        assert field_info.annotation is not None, 'field_info.annotation should not be None when generating a schema'

        def apply_discriminator(schema: CoreSchema) -> CoreSchema:
            if field_info.discriminator is not None:
                schema = _discriminated_union.apply_discriminator(schema, field_info.discriminator, self.definitions)
            return schema

        source_type, annotations = field_info.annotation, field_info.metadata
        schema = self._apply_annotations(
            apply_discriminator,
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
        schema = apply_each_item_validators(schema, each_item_validators)

        schema = apply_validators(schema, filter_field_decorator_info_by_field(this_field_validators, name))
        schema = apply_validators(
            schema, filter_field_decorator_info_by_field(decorators.field_validators.values(), name)
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
        json_schema_updates.update(field_info.json_schema_extra or {})

        def json_schema_update_func(schema: CoreSchemaOrField, handler: GetJsonSchemaHandler) -> JsonSchemaValue:
            return {**handler(schema), **json_schema_updates}

        metadata = build_metadata_dict(js_functions=[json_schema_update_func])

        # apply alias generator
        alias_generator = self.config_wrapper.alias_generator
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
            frozen=field_info.frozen or field_info.final,
            metadata=metadata,
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
            s = core_schema.union_schema(choices)

        if nullable:
            s = core_schema.nullable_schema(s)
        return s

    def _type_alias_type_schema(
        self,
        obj: Any,  # TypeAliasType
    ) -> CoreSchema:
        origin = get_origin(obj)
        if origin is not None and _typing_extra.origin_is_type_alias_type(origin):  # type: ignore
            origin = cast(Any, origin)
            ref, schema = self._get_or_cache_recursive_ref(origin)
            if schema is not None:
                return schema
            namespace = (self.types_namespace or {}).copy()
            new_namespace = {**_typing_extra.get_cls_types_namespace(origin), **namespace}
            annotation = origin.__value__
        else:
            ref, schema = self._get_or_cache_recursive_ref(obj)
            if schema is not None:
                return schema
            namespace = (self.types_namespace or {}).copy()
            new_namespace = {**_typing_extra.get_cls_types_namespace(obj), **namespace}
            annotation = obj.__value__
        self.types_namespace = new_namespace
        typevars_map = get_standard_typevars_map(obj)
        annotation = replace_types(annotation, typevars_map)
        schema = self.generate_schema(annotation)
        assert schema['type'] != 'definitions'
        schema['ref'] = ref  # type: ignore
        self.types_namespace = namespace or None
        self.recursion_cache[obj] = schema  # type: ignore
        self.definitions[ref] = schema
        return schema

    def _literal_schema(self, literal_type: Any) -> core_schema.LiteralSchema:
        """
        Generate schema for a Literal.
        """
        expected = _typing_extra.all_literal_values(literal_type)
        assert expected, f'literal "expected" cannot be empty, obj={literal_type}'
        return core_schema.literal_schema(expected)

    def _typed_dict_schema(self, typed_dict_cls: Any, origin: Any) -> core_schema.CoreSchema:
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
        typed_dict_ref, schema = self._get_or_cache_recursive_ref(typed_dict_cls)
        if schema is not None:
            return schema

        typevars_map = get_standard_typevars_map(typed_dict_cls)
        if origin is not None:
            typed_dict_cls = origin

        if not _SUPPORTS_TYPEDDICT and type(typed_dict_cls).__module__ == 'typing':
            raise PydanticUserError(
                'Please use `typing_extensions.TypedDict` instead of `typing.TypedDict` on Python < 3.12.',
                code='typed-dict-version',
            )

        config: ConfigDict | None = getattr(typed_dict_cls, '__pydantic_config__', None)
        config_wrapper = ConfigWrapper(config)
        core_config = config_wrapper.core_config(None)

        required_keys: frozenset[str] = typed_dict_cls.__required_keys__

        fields: dict[str, core_schema.TypedDictField] = {}

        decorators = DecoratorInfos.build(typed_dict_cls)

        for field_name, annotation in get_type_hints_infer_globalns(
            typed_dict_cls, localns=self.types_namespace, include_extras=True
        ).items():
            annotation = replace_types(annotation, typevars_map)
            required = field_name in required_keys

            if get_origin(annotation) == _typing_extra.Required:
                required = True
                annotation = get_args(annotation)[0]
            elif get_origin(annotation) == _typing_extra.NotRequired:
                required = False
                annotation = get_args(annotation)[0]

            field_info = FieldInfo.from_annotation(annotation)
            fields[field_name] = self._generate_td_field_schema(field_name, field_info, decorators, required=required)

        metadata = build_metadata_dict(js_functions=[partial(modify_model_json_schema, cls=typed_dict_cls)])

        td_schema = core_schema.typed_dict_schema(
            fields,
            extra_behavior='forbid',
            ref=typed_dict_ref,
            metadata=metadata,
            config=core_config,
        )

        schema = self._apply_model_serializers(td_schema, decorators.model_serializers.values())
        return apply_model_validators(schema, decorators.model_validators.values(), 'all')

    def _namedtuple_schema(self, namedtuple_cls: Any) -> core_schema.CallSchema:
        """
        Generate schema for a NamedTuple.
        """
        annotations: dict[str, Any] = get_type_hints_infer_globalns(
            namedtuple_cls, include_extras=True, localns=self.types_namespace
        )
        if not annotations:
            # annotations is empty, happens if namedtuple_cls defined via collections.namedtuple(...)
            annotations = {k: Any for k in namedtuple_cls._fields}

        arguments_schema = core_schema.ArgumentsSchema(
            type='arguments',
            arguments_schema=[
                self._generate_parameter_schema(field_name, annotation)
                for field_name, annotation in annotations.items()
            ],
            metadata=build_metadata_dict(js_prefer_positional_arguments=True),
        )
        return core_schema.call_schema(arguments_schema, namedtuple_cls)

    def _generate_parameter_schema(
        self,
        name: str,
        annotation: type[Any],
        default: Any = Parameter.empty,
        mode: Literal['positional_only', 'positional_or_keyword', 'keyword_only'] | None = None,
    ) -> core_schema.ArgumentsParameter:
        """
        Prepare a ArgumentsParameter to represent a field in a namedtuple or function signature.
        """
        if default is Parameter.empty:
            field = FieldInfo.from_annotation(annotation)
        else:
            field = FieldInfo.from_annotated_attribute(annotation, default)
        assert field.annotation is not None, 'field.annotation should not be None when generating a schema'
        source_type, annotations = field.annotation, field.metadata
        schema = self._apply_annotations(lambda x: x, source_type, annotations)

        if not field.is_required():
            schema = wrap_default(field, schema)

        parameter_schema = core_schema.arguments_parameter(name, schema)
        if mode is not None:
            parameter_schema['mode'] = mode
        if field.alias is not None:
            parameter_schema['alias'] = field.alias
        else:
            alias_generator = self.config_wrapper.alias_generator
            if alias_generator:
                parameter_schema['alias'] = alias_generator(name)
        return parameter_schema

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
                return core_schema.tuple_positional_schema([])
        elif params[-1] is Ellipsis:
            if len(params) == 2:
                sv = core_schema.tuple_variable_schema(self.generate_schema(params[0]))
                return sv

            # not sure this case is valid in python, but may as well support it here since pydantic-core does
            *items_schema, extra_schema = params
            return core_schema.tuple_positional_schema(
                [self.generate_schema(p) for p in items_schema], extra_schema=self.generate_schema(extra_schema)
            )
        elif len(params) == 1 and params[0] == ():
            # special case for `Tuple[()]` which means `Tuple[]` - an empty tuple
            return core_schema.tuple_positional_schema([])
        else:
            return core_schema.tuple_positional_schema([self.generate_schema(p) for p in params])

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
                    [self.generate_schema(typing.Type[c]) for c in type_param.__constraints__]
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
        """
        Generate a schema for an `Iterable`.
        """
        item_type = get_first_arg(type_)

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

        param = get_args(pattern_type)[0]
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
        """
        Generate schema for a dataclass.
        """
        dataclass_ref, schema = self._get_or_cache_recursive_ref(dataclass)
        if schema is not None:
            return schema

        typevars_map = get_standard_typevars_map(dataclass)
        if origin is not None:
            dataclass = origin

        from ._dataclasses import is_pydantic_dataclass

        if is_pydantic_dataclass(dataclass):
            fields = dataclass.__pydantic_fields__
            if typevars_map:
                for field in fields.values():
                    field.apply_typevars_map(typevars_map, self.types_namespace)
        else:
            fields = collect_dataclass_fields(
                dataclass,
                self.types_namespace,
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

        config = getattr(dataclass, '__pydantic_config__', None)
        if config is not None:
            config_wrapper = ConfigWrapper(config, check=False)
            self._config_wrapper_stack.append(config_wrapper)
            core_config = config_wrapper.core_config(dataclass)
        else:
            core_config = None

        try:
            args_schema = core_schema.dataclass_args_schema(
                dataclass.__name__,
                args,
                computed_fields=[self._computed_field_schema(d) for d in decorators.computed_fields.values()],
                collect_init_only=has_post_init,
            )
        finally:
            if config is not None:
                self._config_wrapper_stack.pop()

        inner_schema = apply_validators(args_schema, decorators.root_validators.values())

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
        return apply_model_validators(schema, model_validators, 'outer')

    def _callable_schema(self, function: Callable[..., Any]) -> core_schema.CallSchema:
        """
        Generate schema for a Callable.

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
        config_wrapper = self.config_wrapper
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
            return core_schema.AnySchema(type='any')

    def _get_or_cache_recursive_ref(self, cls: type[Any]) -> tuple[str, core_schema.DefinitionReferenceSchema | None]:
        obj_ref = get_type_ref(cls)
        if obj_ref in self.recursion_cache:
            return obj_ref, self.recursion_cache[obj_ref]
        else:
            self.recursion_cache[obj_ref] = core_schema.definition_reference_schema(obj_ref)
            return obj_ref, None

    def _computed_field_schema(self, d: Decorator[ComputedFieldInfo]) -> core_schema.ComputedField:
        return_type_schema = self.generate_schema(d.info.return_type)

        # Handle alias_generator using similar logic to that from
        # pydantic._internal._generate_schema.GenerateSchema._common_field_schema,
        # with field_info -> d.info and name -> d.cls_var_name
        alias_generator = self.config_wrapper.alias_generator
        if alias_generator and (d.info.alias_priority is None or d.info.alias_priority <= 1):
            alias = alias_generator(d.cls_var_name)
            if not isinstance(alias, str):
                raise TypeError(f'alias_generator {alias_generator} must return str, not {alias.__class__}')
            d.info.alias = alias
            d.info.alias_priority = 1

        return core_schema.computed_field(d.cls_var_name, return_schema=return_type_schema, alias=d.info.alias)

    def _annotated_schema(self, annotated_type: Any) -> core_schema.CoreSchema:
        """
        Generate schema for an Annotated type, e.g. `Annotated[int, Field(...)]` or `Annotated[int, Gt(0)]`.
        """
        source_type, *annotations = get_args(annotated_type)
        schema = self._apply_annotations(lambda x: x, source_type, annotations)
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

        for gen in PREPARE_METHODS:
            res = gen(obj, annotations, self.config_wrapper.config_dict)
            if res is not None:
                return res

        return None

    def _prepare_annotations(self, source_type: Any, annotations: Iterable[Any]) -> tuple[Any, list[Any]]:
        """
        Call `__prepare_pydantic_annotations__` if it exists and return a tuple of (new_source_type, new_annotations).

        This should be treated conceptually similar to the transformation
        `Annotated[source_type, *annotations]` -> `Annotated[new_source_type, *new_annotations]`
        """

        prepare = getattr(source_type, '__prepare_pydantic_annotations__', None)

        annotations = tuple(annotations)  # make them immutable to avoid confusion over mutating them

        if prepare is not None:
            source_type, annotations = prepare(source_type, tuple(annotations), self.config_wrapper.config_dict)
            annotations = list(annotations)
        else:
            res = self._get_prepare_pydantic_annotations_for_known_type(source_type, annotations)
            if res is not None:
                source_type, annotations = res

        return source_type, list(annotations)

    def _apply_annotations(
        self,
        transform_inner_schema: Callable[[CoreSchema], CoreSchema],
        source_type: Any,
        annotations: list[Any],
    ) -> CoreSchema:
        """
        Apply arguments from `Annotated` or from `FieldInfo` to a schema.

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
            source_type, annotations = prepare(source_type, tuple(annotations), self.config_wrapper.config_dict)
            annotations = list(annotations)
        else:
            res = self._get_prepare_pydantic_annotations_for_known_type(source_type, tuple(annotations))
            if res is not None:
                source_type, annotations = res

        pydantic_js_functions: list[GetJsonSchemaFunction] = []

        def inner_handler(obj: Any) -> CoreSchema:
            if isinstance(obj, type(Annotated[int, 123])):
                schema = transform_inner_schema(self._annotated_schema(obj))
            else:
                from_property = self._generate_schema_from_property(obj, obj)
                if from_property is None:
                    schema = self._generate_schema(obj)
                else:
                    schema = from_property
                metadata_js_function = _extract_get_pydantic_json_schema(obj, schema)
                if metadata_js_function is not None:
                    pydantic_js_functions.append(metadata_js_function)
            return transform_inner_schema(schema)

        get_inner_schema = CallbackGetCoreSchemaHandler(inner_handler, self.generate_schema)

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
                new_source_type, remaining = prepare(source_type, tuple(remaining), self.config_wrapper.config_dict)
                annotations = previous + list(remaining)
                if new_source_type is not source_type:
                    return self._apply_annotations(
                        transform_inner_schema,
                        new_source_type,
                        annotations,
                    )
            annotation = annotations[idx]
            get_inner_schema = self._get_wrapped_inner_schema(
                get_inner_schema, annotation, self.definitions, pydantic_js_functions
            )

        schema = get_inner_schema(source_type)
        metadata = CoreMetadataHandler(schema).metadata
        metadata.setdefault('pydantic_js_functions', []).extend(pydantic_js_functions)
        return schema

    def _get_wrapped_inner_schema(
        self,
        get_inner_schema: GetCoreSchemaHandler,
        annotation: Any,
        definitions: dict[str, core_schema.CoreSchema],
        pydantic_js_functions: list[GetJsonSchemaFunction],
    ) -> CallbackGetCoreSchemaHandler:
        metadata_get_schema: GetCoreSchemaFunction = getattr(annotation, '__get_pydantic_core_schema__', None) or (
            lambda source, handler: handler(source)
        )

        def new_handler(source: Any) -> core_schema.CoreSchema:
            schema = metadata_get_schema(source, get_inner_schema)
            schema = apply_single_annotation(schema, annotation, definitions)

            metadata_js_function = _extract_get_pydantic_json_schema(annotation, schema)
            if metadata_js_function is not None:
                pydantic_js_functions.append(metadata_js_function)
            return schema

        return CallbackGetCoreSchemaHandler(new_handler, self.generate_schema)

    def _apply_field_serializers(
        self, schema: core_schema.CoreSchema, serializers: list[Decorator[FieldSerializerDecoratorInfo]]
    ) -> core_schema.CoreSchema:
        """
        Apply field serializers to a schema.
        """
        if serializers:
            # use the last serializer to make it easy to override a serializer set on a parent model
            serializer = serializers[-1]
            is_field_serializer, info_arg = inspect_field_serializer(serializer.func, serializer.info.mode)

            if serializer.info.return_type is None:
                return_schema = None
            else:
                return_schema = self.generate_schema(serializer.info.return_type)

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
        """
        Apply model serializers to a schema.
        """
        ref: str | None = schema.pop('ref', None)  # type: ignore
        if serializers:
            serializer = list(serializers)[-1]
            info_arg = inspect_model_serializer(serializer.func, serializer.info.mode)

            if serializer.info.return_type is None:
                return_schema = None
            else:
                return_schema = self.generate_schema(serializer.info.return_type)

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
    Callable[[Callable[..., Any], core_schema.CoreSchema], core_schema.CoreSchema],
] = {
    ('before', 'no-info'): core_schema.no_info_before_validator_function,
    ('after', 'no-info'): core_schema.no_info_after_validator_function,
    ('plain', 'no-info'): lambda f, _: core_schema.no_info_plain_validator_function(f),
    ('wrap', 'no-info'): core_schema.no_info_wrap_validator_function,
    ('before', 'general'): core_schema.general_before_validator_function,
    ('after', 'general'): core_schema.general_after_validator_function,
    ('plain', 'general'): lambda f, _: core_schema.general_plain_validator_function(f),
    ('wrap', 'general'): core_schema.general_wrap_validator_function,
    ('before', 'field'): core_schema.field_before_validator_function,
    ('after', 'field'): core_schema.field_after_validator_function,
    ('plain', 'field'): lambda f, _: core_schema.field_plain_validator_function(f),
    ('wrap', 'field'): core_schema.field_wrap_validator_function,
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
        info_arg = inspect_validator(validator.func, validator.info.mode)
        if not info_arg:
            val_type: Literal['no-info', 'general', 'field'] = 'no-info'
        elif isinstance(validator.info, (FieldValidatorDecoratorInfo, ValidatorDecoratorInfo)):
            val_type = 'field'
        else:
            val_type = 'general'
        schema = _VALIDATOR_F_MATCH[(validator.info.mode, val_type)](validator.func, schema)
    return schema


def _validators_require_validate_default(validators: Iterable[Decorator[ValidatorDecoratorInfo]]) -> bool:
    """
    In v1, if any of the validators for a field had `always=True`, the default value would be validated.

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
    """
    Apply model validators to a schema.

    If mode == 'inner', only "before" validators are applied
    If mode == 'outer', validators other than "before" are applied
    If mode == 'all', all validators are applied
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


def apply_single_annotation(
    schema: core_schema.CoreSchema, metadata: Any, definitions: dict[str, core_schema.CoreSchema]
) -> core_schema.CoreSchema:
    if isinstance(metadata, FieldInfo):
        for field_metadata in metadata.metadata:
            schema = apply_single_annotation(schema, field_metadata, definitions)
        if metadata.discriminator is not None:
            schema = _discriminated_union.apply_discriminator(schema, metadata.discriminator, definitions)
        return schema

    if schema['type'] == 'nullable':
        # for nullable schemas, metadata is automatically applied to the inner schema
        inner = schema.get('schema', core_schema.any_schema())
        inner = apply_single_annotation(inner, metadata, definitions)
        if inner:
            schema['schema'] = inner
        return schema

    return _known_annotated_metadata.apply_known_metadata(metadata, schema.copy())


def wrap_default(field_info: FieldInfo, schema: core_schema.CoreSchema) -> core_schema.CoreSchema:
    if field_info.default_factory:
        return core_schema.with_default_schema(
            schema, default_factory=field_info.default_factory, validate_default=field_info.validate_default
        )
    elif field_info.default is not Undefined:
        return core_schema.with_default_schema(
            schema, default=field_info.default, validate_default=field_info.validate_default
        )
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


def _extract_get_pydantic_json_schema(tp: Any, schema: CoreSchema) -> GetJsonSchemaFunction | None:
    """Extract `__get_pydantic_json_schema__` from a type, handling the deprecated `__modify_schema__`"""
    js_modify_function = getattr(tp, '__get_pydantic_json_schema__', None)

    if js_modify_function is None and hasattr(tp, '__modify_schema__'):
        warnings.warn(
            'The __modify_schema__ method is deprecated, use __get_pydantic_json_schema__ instead',
            DeprecationWarning,
        )
        return lambda c, h: tp.__modify_schema__(h(c))

    # handle GenericAlias' but ignore Annotated which "lies" about it's origin (in this case it would be `int`)
    if hasattr(tp, '__origin__') and not isinstance(tp, type(Annotated[int, 'placeholder'])):
        return _extract_get_pydantic_json_schema(tp.__origin__, schema)

    if js_modify_function is None:
        return None

    # wrap the schema so that we unpack ref schemas and always call metadata_js_function with the full schema
    if schema['type'] != 'definition-ref':
        # we would fail to unpack recursive ref schemas!
        js_modify_function = wrap_json_schema_fn_for_model_or_custom_type_with_ref_unpacking(js_modify_function)
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
