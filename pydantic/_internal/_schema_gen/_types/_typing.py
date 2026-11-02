"""Type handlers for typing special forms and constructs, such as unions, `Literal`, type aliases, etc."""

from __future__ import annotations

import types
import typing
from enum import Enum
from typing import Any, cast, get_origin

from pydantic_core import MISSING, CoreSchema, core_schema
from typing_extensions import TypeAliasType
from typing_inspection import typing_objects
from typing_inspection.introspection import get_literal_values

from ....errors import PydanticUndefinedAnnotation
from ... import _constraints as c
from ... import _type_refs, _typing_extra
from ..._core_metadata import CoreMetadata
from ..._generics import get_standard_typevars_map, replace_types
from .._annotations_handler import AnnotationsHandler
from .._conditions import Predicate, TypeIs, TypeIsTypingMember
from .._type_handlers import GenericTypeHandler, TypeHandler
from .._type_registry import default_registry


@default_registry.register
class UnionTypeHandler(GenericTypeHandler):
    """Type handler for unions (`typing.Union` and `types.UnionType`)."""

    match_condition = TypeIsTypingMember('Union') | TypeIs(types.UnionType)
    known_metadata = frozenset({c.UnionMode})

    def handle_type(self, type: Any, args: tuple[Any, ...], annotations_handler: AnnotationsHandler) -> CoreSchema:
        choices: list[CoreSchema] = []
        nullable = False
        allow_missing = False
        for arg in args:
            if arg is None or arg is types.NoneType:
                nullable = True
            elif arg is MISSING:
                allow_missing = True
            else:
                choices.append(self.generate_schema(arg))

        if not choices:
            # Only `None` and `MISSING` were present in the union (e.g. `None | MISSING`):
            s: CoreSchema = core_schema.none_schema()
            nullable = False
        elif len(choices) == 1:
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
            for annotation in annotations_handler.iter_annotations():
                s['mode'] = annotation.union_mode

        if nullable:
            s = core_schema.nullable_schema(s)
        if allow_missing:
            s = core_schema.missing_sentinel_schema(s)
        return s


@default_registry.register
class LiteralTypeHandler(TypeHandler):
    """Type handler for `typing.Literal`."""

    match_condition = TypeIsTypingMember('Literal')

    def handle_type(self, type: Any, annotations_handler: AnnotationsHandler) -> CoreSchema:
        expected = list(get_literal_values(type, type_check=False, unpack_type_aliases='eager'))
        assert expected, f'literal "expected" cannot be empty, obj={type}'
        schema = core_schema.literal_schema(expected)

        if self.schema_generator._config_wrapper.use_enum_values and any(isinstance(v, Enum) for v in expected):
            schema = core_schema.no_info_after_validator_function(
                lambda v: v.value if isinstance(v, Enum) else v, schema
            )

        return schema


@default_registry.register
class FinalTypeHandler(GenericTypeHandler):
    """Type handler for `typing.Final`."""

    # TODO: I'm not sure `Final` can be encountered here, we call `typing_inspection.introspection.inspect_annotation()`
    # early for model-like fields, which handles it already.
    match_condition = TypeIsTypingMember('Final')
    default_args = (Any,)

    def handle_type(self, type: Any, args: tuple[Any, ...], annotations_handler: AnnotationsHandler) -> CoreSchema:
        return self.generate_schema(args[0])


@default_registry.register
class TypeAliasTypeHandler(TypeHandler):
    """Type handler for type aliases created using the `type` statement (or `typing(_extensions).TypeAliasType`)."""

    match_condition = Predicate(typing_objects.is_typealiastype)

    def get_reference(self, obj: Any, origin: Any | None) -> str:
        return _type_refs.type_alias_type_ref(obj)

    def handle_type(self, type: Any, annotations_handler: AnnotationsHandler) -> CoreSchema:
        gen = self.schema_generator
        origin: TypeAliasType = get_origin(type) or type
        typevars_map = get_standard_typevars_map(type)

        with gen._ns_resolver.push(origin):
            try:
                annotation = _typing_extra.eval_type(origin.__value__, *gen._types_namespace)
            except NameError as e:
                raise PydanticUndefinedAnnotation.from_name_error(e) from e
            annotation = replace_types(annotation, typevars_map)
            schema = self.generate_schema(annotation)
            assert schema['type'] != 'definitions'
        return schema


@default_registry.register
class NewTypeTypeHandler(TypeHandler):
    """Type handler for `typing.NewType`."""

    match_condition = Predicate(typing_objects.is_newtype)

    def handle_type(self, type: Any, annotations_handler: AnnotationsHandler) -> CoreSchema:
        return self.generate_schema(type.__supertype__)


@default_registry.register
class TypeVarTypeHandler(TypeHandler):
    """Type handler for unsubstituted type variables."""

    match_condition = Predicate(lambda obj: isinstance(obj, typing.TypeVar))

    def handle_type(self, type: Any, annotations_handler: AnnotationsHandler) -> CoreSchema:
        typevar: typing.TypeVar = type
        try:
            has_default = typevar.has_default()  # pyright: ignore[reportAttributeAccessIssue]
        except AttributeError:
            # Happens if using `typing.TypeVar` (and not `typing_extensions`) on Python < 3.13
            pass
        else:
            if has_default:
                return self.generate_schema(typevar.__default__)  # pyright: ignore[reportAttributeAccessIssue]

        if constraints := typevar.__constraints__:
            return self.generate_schema(typing.Union[constraints])  # noqa: UP007

        if bound := typevar.__bound__:
            schema = self.generate_schema(bound)
            schema['serialization'] = core_schema.simple_ser_schema('any')
            return schema

        return core_schema.any_schema()
