from __future__ import annotations


from typing import TYPE_CHECKING, Any, cast
from collections.abc import Callable

from typing_extensions import TypeAlias, get_origin

from typing_inspection import typing_objects
from typing_inspection.introspection import is_union_origin, get_literal_values

from .. import _known_annotated_metadata
from ...annotated_handlers import GetCoreSchemaHandler
from .._schema_generation_shared import CallbackGetCoreSchemaHandler, GetJsonSchemaFunction
from .._core_metadata import CoreMetadata
from .._generate_schema import _Definitions, _FieldNameStack, _ModelTypeStack
from .._config import ConfigWrapper, ConfigWrapperStack
from .._namespace_utils import NsResolver
from ...errors import PydanticUserError

from pydantic_core import PydanticUndefined, CoreSchema, core_schema

if TYPE_CHECKING:
    from ._type_registry import TypeRegistry


ModifyCoreSchemaWrapHandler: TypeAlias = GetCoreSchemaHandler
GetCoreSchemaFunction: TypeAlias = Callable[[Any, ModifyCoreSchemaWrapHandler], core_schema.CoreSchema]



class GenerateSchema:
    def __init__(
        self,
        type_registry: TypeRegistry,
        config_wrapper: ConfigWrapper,
        ns_resolver: NsResolver | None = None,
        typevars_map: dict[Any, Any] | None = None,
    ) -> None:
        self._type_registry = type_registry
        self._config_wrapper_stack = ConfigWrapperStack(config_wrapper)
        self._ns_resolver = ns_resolver or NsResolver()
        self._typevars_map = typevars_map
        self.field_name_stack = _FieldNameStack()
        self.model_type_stack = _ModelTypeStack()
        self.defs = _Definitions()

    def generate_schema(self, obj: Any) -> CoreSchema:
        # 1. Check GPCS method
        schema = self._generate_schema_from_get_schema_method(obj)

        if schema is None:
            schema = self._generate_schema_inner(obj)


        metadata_js_function = _extract_get_pydantic_json_schema(obj, origin)
        if metadata_js_function is not None:
            ...

        return schema

    def _generate_schema_inner(self, obj: Any) -> CoreSchema:
        if typing_objects.is_self(obj):
            ...

        origin = get_origin(obj)

        if typing_objects.is_annotated(origin):
            return self._generate_schema_with_metadata(
                obj=obj.__origin__,  # <typ> in Annotated[<typ>, 'meta']
                metadata=obj.__metadata__,  # ('meta',) in Annotated[<typ>, 'meta']
            )

        schema = self._match_type(
            obj,
            _origin=origin,
        )

        return schema

    def _match_type(
        self,
        obj: Any,
        _origin: Any = PydanticUndefined,
    ) -> CoreSchema:
        origin = _origin if _origin is not PydanticUndefined else get_origin(obj)

        if is_union_origin(origin):
            return self._union_schema(obj)

        if typing_objects.is_literal(origin):
            return self._literal_schema(obj)

        if origin is not None and (aliased_obj := typing_objects.DEPRECATED_ALIASES.get(obj)):
            obj = aliased_obj
            origin = None

        type_handler_class = self._type_registry.get_type_handler(origin if origin is not None else obj)
        if type_handler_class is None:
            raise Exception(f'No handler for {origin if origin is not None else obj}')

        type_handler = type_handler_class(self)

        ref = type_handler.get_reference(origin, obj)
        if ref is not None:
            with self.defs.get_schema_or_ref(ref) as maybe_schema:
                if maybe_schema is not None:
                    return maybe_schema

                core_schema = type_handler._generate_schema(origin, obj)
                return core_schema
        else:
            core_schema = type_handler._generate_schema(origin, obj)
            return core_schema

    def _literal_schema(self, literal_type: Any) -> CoreSchema:
        expected = list(get_literal_values(literal_type, type_check=False, unpack_type_aliases='eager'))
        schema = core_schema.literal_schema(expected)

        # if self._config_wrapper.use_enum_values and any(isinstance(v, Enum) for v in expected):
        #     schema = core_schema.no_info_after_validator_function(
        #         lambda v: v.value if isinstance(v, Enum) else v, schema
        #     )

        return schema

    def _union_schema(self, union: Any) -> CoreSchema:
        """Generate schema for a Union."""
        # TODO for safety, might be best to use `get_args`, although `union` is guaranteed
        # to be `types.UnionType(...) | typing(_extensions).Union[...]`.
        args = union.__args__
        choices: list[CoreSchema] = []
        nullable = False
        for arg in args:
            if arg is typing_objects.NoneType:  # TODO: can't be `None`?
                nullable = True
            else:
                choices.append(self.generate_schema(arg))

        if len(choices) == 1:
            s = choices[0]
        else:
            choices_with_tags: list[CoreSchema | tuple[CoreSchema, str]] = []
            for choice in choices:
                tag = cast(CoreMetadata, choice.get('metadata', {})).get('pydantic_internal_union_tag_key')
                if tag is not None:
                    choices_with_tags.append((choice, tag))
                else:
                    choices_with_tags.append(choice)
            s = core_schema.union_schema(choices_with_tags)

        if nullable:
            s = core_schema.nullable_schema(s)
        return s

    def _annotated_schema(self, annotated: Any) -> CoreSchema:
        ...

    def _apply_annotations(
        self,
        source_type: Any,
        annotations: list[Any],
        transform_inner_schema: Callable[[CoreSchema], CoreSchema] = lambda x: x,
        check_unsupported_field_info_attributes: bool = True,
    ):
        annotations = list(_known_annotated_metadata.expand_grouped_metadata(annotations))

        pydantic_js_annotation_functions: list[GetJsonSchemaFunction] = []

        def inner_handler(obj: Any) -> CoreSchema:
            schema = self._generate_schema_from_get_schema_method(obj, source_type)

            if schema is None:
                schema = self._generate_schema_inner(obj)

            metadata_js_function = _extract_get_pydantic_json_schema(obj)
            if metadata_js_function is not None:
                metadata_schema = resolve_original_schema(schema, self.defs)
                if metadata_schema is not None:
                    self._add_js_function(metadata_schema, metadata_js_function)
            return transform_inner_schema(schema)

        get_inner_schema = CallbackGetCoreSchemaHandler(inner_handler, self)

        for annotation in annotations:
            if annotation is None:
                continue
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
                for attr, value in (unsupported_attributes := self._get_unsupported_field_info_attributes(metadata)):
                    warnings.warn(
                        f'The {attr!r} attribute with value {value!r} was provided to the `Field()` function, '
                        f'which has no effect in the context it was used. {attr!r} is field-specific metadata, '
                        'and can only be attached to a model field using `Annotated` metadata or by assignment. '
                        'This may have happened because an `Annotated` type alias using the `type` statement was '
                        'used, or if the `Field()` function was attached to a single member of a union type.',
                        category=UnsupportedFieldAttributeWarning,
                    )

                if (
                    metadata.default_factory_takes_validated_data
                    and self.model_type_stack.get() is None
                    and 'defaut_factory' not in unsupported_attributes
                ):
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

    class CollectedInvalid(Exception):
        pass

    def clean_schema(self, schema: CoreSchema) -> CoreSchema:
        schema = self.defs.finalize_schema(schema)
        return schema


    def _generate_schema_from_get_schema_method(self, obj: Any):
        get_schema = getattr(obj, '__get_pydantic_core_schema__', None)
        if get_schema is not None:
            from pydantic import BaseModel

            is_base_model_get_schema = (
                getattr(get_schema, '__func__', None) is BaseModel.__get_pydantic_core_schema__.__func__  # pyright: ignore[reportFunctionMemberAccess]
            )
            if get_schema is not None and not is_base_model_get_schema:
                ...


# Improved version of the existing one, can be backported:
def _extract_get_pydantic_json_schema(tp: Any, _origin: Any | None = None):
    js_modify_function = getattr(tp, '__get_pydantic_json_schema__', None)

    if js_modify_function is not None and hasattr(tp, '__modify_schema__'):
        from pydantic import BaseModel

        is_base_model_get_json_schema = (
            getattr(js_modify_function, '__func__', None) is BaseModel.__get_pydantic_json_schema__.__func__
        )

        if is_base_model_get_json_schema:
            cls_name = getattr(tp, '__name__', None)
            raise PydanticUserError(
                f'The `__modify_schema__` method is not supported in Pydantic v2. '
                f'Use `__get_pydantic_json_schema__` instead{f" in class `{cls_name}`" if cls_name else ""}.',
                code='custom-json-schema',
            )

    origin = _origin if _origin is not None else get_origin(tp)

    if origin is not None:
        return _extract_get_pydantic_json_schema(origin, None)

    return js_modify_function
