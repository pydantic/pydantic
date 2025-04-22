from __future__ import annotations


from typing import TYPE_CHECKING, Any, cast

from typing_extensions import get_origin

from typing_inspection import typing_objects
from typing_inspection.introspection import is_union_origin, get_literal_values

from .._core_metadata import CoreMetadata
from .._generate_schema import _Definitions, _FieldNameStack, _ModelTypeStack
from .._config import ConfigWrapper, ConfigWrapperStack
from .._namespace_utils import NsResolver
from ._annotations_handler import AnnotationsHandler
from ...errors import PydanticUserError

from pydantic_core import PydanticUndefined, CoreSchema, core_schema

if TYPE_CHECKING:
    from ._type_registry import TypeRegistry


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
        get_schema = getattr(obj, '__get_pydantic_core_schema__', None)
        if get_schema is not None:
            from pydantic import BaseModel

            is_base_model_get_schema = (
                getattr(get_schema, '__func__', None) is BaseModel.__get_pydantic_core_schema__.__func__  # pyright: ignore[reportFunctionMemberAccess]
            )
            if get_schema is not None and not is_base_model_get_schema:
                ...

        if typing_objects.is_self(obj):
            ...

        origin = get_origin(obj)

        if typing_objects.is_annotated(origin):
            return self._generate_schema_inner(
                obj=obj.__origin__,  # <typ> in Annotated[<typ>, 'meta']
                metadata=obj.__metadata__,  # ('meta',) in Annotated[<typ>, 'meta']
            )

        schema = self._generate_schema_inner(
            obj,
            _origin=origin,
        )

        metadata_js_function = _extract_get_pydantic_json_schema(obj, origin)
        if metadata_js_function is not None:
            ...

        return schema

    def _generate_schema_inner(
        self,
        obj: Any,
        metadata: list[Any] | None = None,
        _origin: Any = PydanticUndefined,
    ) -> CoreSchema:
        origin = _origin if _origin is not PydanticUndefined else get_origin(obj)

        if is_union_origin(origin):
            return self._union_schema(obj)

        if typing_objects.is_literal(origin):
            return self._literal_schema(obj)

        metadata = metadata if metadata is not None else []

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

                annotations_handler = AnnotationsHandler(metadata, type_handler_class.known_metadata)
                core_schema = type_handler._generate_schema(origin, obj, annotations_handler)
                return core_schema
        else:
            annotations_handler = AnnotationsHandler(metadata, type_handler_class.known_metadata)
            core_schema = type_handler._generate_schema(origin, obj, annotations_handler)

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

    class CollectedInvalid(Exception):
        pass

    def clean_schema(self, schema: CoreSchema) -> CoreSchema:
        schema = self.defs.finalize_schema(schema)
        return schema


# Improved version of the existing one, can be backported:
def _extract_get_pydantic_json_schema(tp: Any, origin: Any | None):
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

    if origin is not None:
        return _extract_get_pydantic_json_schema(origin, None)

    return js_modify_function
