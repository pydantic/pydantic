"""Type handlers for model-like types (Pydantic models, dataclasses, typed dictionaries, named tuples), enums and functions."""

from __future__ import annotations

import dataclasses
import inspect
import warnings
from copy import copy
from enum import Enum
from inspect import Parameter
from itertools import chain
from operator import attrgetter
from typing import TYPE_CHECKING, Any, Literal, get_origin

from pydantic_core import CoreSchema, core_schema
from typing_extensions import is_typeddict
from typing_inspection import typing_objects
from typing_inspection.introspection import AnnotationSource

from ....errors import PydanticSchemaGenerationError, PydanticUndefinedAnnotation, PydanticUserError
from ....warnings import TypedDictExtraConfigWarning
from ... import _type_refs, _typing_extra
from ..._config import ConfigWrapper
from ..._core_metadata import update_core_metadata
from ..._core_utils import get_ref
from ..._decorators import DecoratorInfos, get_attribute_from_bases
from ..._docs_extraction import extract_docstrings_from_cls
from ..._fields import (
    collect_dataclass_fields,
    rebuild_dataclass_fields,
    rebuild_model_fields,
    update_field_from_config,
)
from ..._generics import get_model_typevars_map, get_standard_typevars_map, replace_types
from ..._import_utils import import_cached_base_model, import_cached_field_info
from ..._mock_val_ser import MockCoreSchema
from ..._model_construction import ModelMetaclass
from .._annotations_handler import AnnotationsHandler
from .._conditions import Predicate
from .._type_handlers import TypeHandler
from .._type_registry import default_registry

# Note: this module is imported lazily by `_generate_schema` (see `_get_default_registry()`), so there's no import cycle:
from ..._generate_schema import (  # isort: skip
    _SUPPORTS_TYPEDDICT,
    VALIDATE_CALL_SUPPORTED_TYPES,
    _convert_to_aliases,
    _get_typed_dict_extra_items,
    apply_model_validators,
    check_decorator_fields_exist,
    wrap_default,
)

if TYPE_CHECKING:
    from ....annotated_handlers import GetJsonSchemaHandler
    from ....config import ConfigDict
    from ....json_schema import JsonSchemaValue
    from ....main import BaseModel
    from ..._dataclasses import StandardDataclass
    from ..._generate_schema import GenerateSchema


def _is_model_class(obj: Any) -> bool:
    # Equivalent to (and faster than) an `issubclass()` check against `BaseModel`:
    return isinstance(obj, ModelMetaclass)


@default_registry.register
class ModelTypeHandler(TypeHandler):
    """Type handler for Pydantic models."""

    match_condition = Predicate(_is_model_class)

    def handle_type(self, type: type[BaseModel], annotations_handler: AnnotationsHandler) -> CoreSchema:
        gen = self.schema_generator
        # Fast path for models whose schema was already built (avoids the context managers overhead):
        existing_schema = type.__dict__.get('__pydantic_core_schema__')
        if existing_schema is not None and not isinstance(existing_schema, MockCoreSchema):
            model_ref = _type_refs.model_type_ref(type)
            if model_ref in gen.defs._recursively_seen or model_ref in gen.defs._definitions:
                return core_schema.definition_reference_schema(model_ref)
            return gen._reuse_model_schema(existing_schema)

        with gen.model_type_stack.push(type):
            return self._model_schema(gen, type)

    def _model_schema(self, gen: GenerateSchema, cls: type[BaseModel]) -> CoreSchema:
        """Generate schema for a Pydantic model."""
        BaseModel_ = import_cached_base_model()

        model_ref = _type_refs.model_type_ref(cls)
        with gen.defs.get_definition_ref_schema(ref=model_ref) as maybe_schema:
            if maybe_schema is not None:
                return maybe_schema

            config_wrapper = ConfigWrapper(cls.model_config, check=False)

            with gen._config_wrapper_stack.push(config_wrapper), gen._ns_resolver.push(cls):
                core_config = gen._config_wrapper.core_config(title=cls.__name__)

                if cls.__pydantic_fields_complete__ or cls is BaseModel_:
                    fields = getattr(cls, '__pydantic_fields__', {})
                    extra_info = getattr(cls, '__pydantic_extra_info__', None)
                else:
                    if '__pydantic_fields__' not in cls.__dict__:
                        # This happens when we have a loop in the schema generation:
                        # class Base[T](BaseModel):
                        #     t: T
                        #
                        # class Other(BaseModel):
                        #     b: 'Base[Other]'
                        # When we build fields for `Other`, we evaluate the forward annotation.
                        # At this point, `Other` doesn't have the model fields set. We create
                        # `Base[Other]`; model fields are successfully built, and we try to generate
                        # a schema for `t: Other`. As `Other.__pydantic_fields__` aren't set, we abort.
                        raise PydanticUndefinedAnnotation(
                            name=cls.__name__,
                            message=f'Class {cls.__name__!r} is not defined',
                        )
                    try:
                        fields, extra_info = rebuild_model_fields(
                            cls,
                            config_wrapper=gen._config_wrapper,
                            ns_resolver=gen._ns_resolver,
                            typevars_map=get_model_typevars_map(cls),
                        )
                    except NameError as e:
                        raise PydanticUndefinedAnnotation.from_name_error(e) from e

                decorators = cls.__pydantic_decorators__
                computed_fields = decorators.computed_fields
                if decorators.field_validators or decorators.field_serializers:
                    check_decorator_fields_exist(
                        chain(
                            decorators.field_validators.values(),
                            decorators.field_serializers.values(),
                        ),
                        {*fields.keys(), *computed_fields.keys()},
                    )

                model_validators = decorators.model_validators.values()

                extras_schema = None
                extras_keys_schema = None
                if core_config.get('extra_fields_behavior') == 'allow' and extra_info is not None:
                    tp = get_origin(extra_info.annotation)
                    if tp is not dict:
                        raise PydanticSchemaGenerationError(
                            'The type annotation for `__pydantic_extra__` must be `dict[str, ...]`'
                        )
                    # See the comments in `_get_args_resolving_forward_refs()` for why we need
                    # to re-evaluate the annotation:
                    extra_keys_type, extra_items_type = gen._get_args_resolving_forward_refs(
                        extra_info.annotation,
                        required=True,
                    )
                    if extra_keys_type is not str:
                        extras_keys_schema = gen.generate_schema(extra_keys_type)
                    if not typing_objects.is_any(extra_items_type):
                        extras_schema = gen.generate_schema(extra_items_type)

                generic_origin: type[BaseModel] | None = getattr(cls, '__pydantic_generic_metadata__', {}).get('origin')

                if cls.__pydantic_root_model__:
                    inner_schema, metadata = gen._common_field_schema('root', fields['root'], decorators)
                    if cls.__doc__ and metadata.get('pydantic_js_updates', {}).get('description'):
                        # This is a bit of a leaky abstraction, but as the model docstring takes priority
                        # over the root field's description, we need to override it here. This can't be done
                        # in the JSON Schema generation logic because the metadata's `pydantic_js_updates` are
                        # applied last, and overrides any value previously set (so the description set from the
                        # docstring in `GenerateJsonSchema._update_class_schema()` is overridden):
                        update_core_metadata(
                            metadata, pydantic_js_updates={'description': inspect.cleandoc(cls.__doc__)}
                        )

                    inner_schema = apply_model_validators(inner_schema, model_validators, 'inner')
                    model_schema = core_schema.model_schema(
                        cls,
                        inner_schema,
                        generic_origin=generic_origin,
                        custom_init=getattr(cls, '__pydantic_custom_init__', None),
                        root_model=True,
                        post_init=getattr(cls, '__pydantic_post_init__', None),
                        config=core_config,
                        ref=model_ref,
                        metadata=metadata,
                    )
                else:
                    fields_schema: core_schema.CoreSchema = core_schema.model_fields_schema(
                        {k: gen._generate_md_field_schema(k, v, decorators) for k, v in fields.items()},
                        computed_fields=[
                            gen._computed_field_schema(d, decorators.field_serializers)
                            for d in computed_fields.values()
                        ],
                        extras_schema=extras_schema,
                        extras_keys_schema=extras_keys_schema,
                        model_name=cls.__name__,
                    )
                    inner_schema = apply_model_validators(fields_schema, model_validators, 'inner')

                    model_schema = core_schema.model_schema(
                        cls,
                        inner_schema,
                        generic_origin=generic_origin,
                        custom_init=getattr(cls, '__pydantic_custom_init__', None),
                        root_model=False,
                        post_init=getattr(cls, '__pydantic_post_init__', None),
                        config=core_config,
                        ref=model_ref,
                    )

                schema = gen._apply_model_serializers(model_schema, decorators.model_serializers.values())
                schema = apply_model_validators(schema, model_validators, 'outer')
                return gen.defs.create_definition_reference_schema(schema)


@default_registry.register
class TypedDictTypeHandler(TypeHandler):
    """Type handler for typed dictionaries."""

    match_condition = Predicate(is_typeddict)

    def _generate_schema(self, obj: Any, origin: Any | None, annotations_handler: AnnotationsHandler) -> CoreSchema:
        return self._typed_dict_schema(self.schema_generator, obj, origin)

    def handle_type(self, type: Any, annotations_handler: AnnotationsHandler) -> CoreSchema:
        return self._typed_dict_schema(self.schema_generator, type, None)

    def _typed_dict_schema(self, gen: GenerateSchema, typed_dict_cls: Any, origin: Any) -> CoreSchema:
        """Generate a core schema for a `TypedDict` class.

        To be able to build a `DecoratorInfos` instance for the `TypedDict` class (which will include
        validators, serializers, etc.), we need to have access to the original bases of the class
        (see https://docs.python.org/3/library/types.html#types.get_original_bases).
        However, the `__orig_bases__` attribute was only added in 3.12 (https://github.com/python/cpython/pull/103698).

        For this reason, we require Python 3.12 (or using the `typing_extensions` backport).
        """
        FieldInfo = import_cached_field_info()

        typed_dict_ref = _type_refs.class_type_ref(typed_dict_cls, origin)
        with (
            gen.model_type_stack.push(typed_dict_cls),
            gen.defs.get_definition_ref_schema(ref=typed_dict_ref) as maybe_schema,
        ):
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

            try:
                # if a typed dictionary class doesn't have config, we use the parent's config, hence a default of `None`
                # see https://github.com/pydantic/pydantic/issues/10917
                config: ConfigDict | None = get_attribute_from_bases(typed_dict_cls, '__pydantic_config__')
            except AttributeError:
                config = None

            with gen._config_wrapper_stack.push(config):
                core_config = gen._config_wrapper.core_config(title=typed_dict_cls.__name__)

                required_keys: frozenset[str] = typed_dict_cls.__required_keys__

                fields: dict[str, core_schema.TypedDictField] = {}

                decorators = DecoratorInfos.build(typed_dict_cls, replace_wrapped_methods=False)
                decorators.update_from_config(gen._config_wrapper)

                if gen._config_wrapper.use_attribute_docstrings:
                    field_docstrings = extract_docstrings_from_cls(typed_dict_cls, use_inspect=True)
                else:
                    field_docstrings = None

                try:
                    annotations = _typing_extra.get_cls_type_hints(typed_dict_cls, ns_resolver=gen._ns_resolver)
                except NameError as e:
                    raise PydanticUndefinedAnnotation.from_name_error(e) from e

                readonly_fields: list[str] = []

                for field_name, annotation in annotations.items():
                    field_info = FieldInfo.from_annotation(annotation, _source=AnnotationSource.TYPED_DICT)
                    field_info.annotation = replace_types(field_info.annotation, typevars_map)

                    required = (
                        field_name in required_keys or 'required' in field_info._qualifiers
                    ) and 'not_required' not in field_info._qualifiers
                    if 'read_only' in field_info._qualifiers:
                        readonly_fields.append(field_name)

                    if (
                        field_docstrings is not None
                        and field_info.description is None
                        and field_name in field_docstrings
                    ):
                        field_info.description = field_docstrings[field_name]
                    update_field_from_config(gen._config_wrapper, field_name, field_info)

                    fields[field_name] = gen._generate_td_field_schema(
                        field_name, field_info, decorators, required=required
                    )

                if readonly_fields:
                    fields_repr = ', '.join(repr(f) for f in readonly_fields)
                    plural = len(readonly_fields) >= 2
                    warnings.warn(
                        f'Item{"s" if plural else ""} {fields_repr} on TypedDict class {typed_dict_cls.__name__!r} '
                        f'{"are" if plural else "is"} using the `ReadOnly` qualifier. Pydantic will not protect items '
                        'from any mutation on dictionary instances.',
                        UserWarning,
                    )

                extra_behavior: core_schema.ExtraBehavior = 'ignore'
                extras_schema: CoreSchema | None = None  # For 'allow', equivalent to `Any` - no validation performed.

                is_closed, extra_items, extra_items_readonly = _get_typed_dict_extra_items(typed_dict_cls)
                if is_closed:
                    extra_behavior = 'forbid'
                    extras_schema = None
                elif not typing_objects.is_noextraitems(extra_items):
                    extra_behavior = 'allow'
                    extras_schema = gen.generate_schema(replace_types(extra_items, typevars_map))

                if extra_items_readonly:
                    warnings.warn(
                        f'Extra items on TypedDict class {typed_dict_cls.__name__!r} are using the `ReadOnly` qualifier. '
                        'Pydantic will not protect items from any mutation on dictionary instances.',
                        UserWarning,
                    )

                if (config_extra := gen._config_wrapper.extra) in ('allow', 'forbid'):
                    if is_closed and config_extra == 'allow':
                        warnings.warn(
                            f"TypedDict class {typed_dict_cls.__qualname__!r} is closed, but 'extra' configuration "
                            "is set to `'allow'`. The 'extra' configuration value will be ignored.",
                            category=TypedDictExtraConfigWarning,
                        )
                    elif not typing_objects.is_noextraitems(extra_items) and config_extra == 'forbid':
                        warnings.warn(
                            f"TypedDict class {typed_dict_cls.__qualname__!r} allows extra items, but 'extra' configuration "
                            "is set to `'forbid'`. The 'extra' configuration value will be ignored.",
                            category=TypedDictExtraConfigWarning,
                        )
                    else:
                        extra_behavior = config_extra

                td_schema = core_schema.typed_dict_schema(
                    fields,
                    cls=typed_dict_cls,
                    computed_fields=[
                        gen._computed_field_schema(d, decorators.field_serializers)
                        for d in decorators.computed_fields.values()
                    ],
                    extra_behavior=extra_behavior,
                    extras_schema=extras_schema,
                    ref=typed_dict_ref,
                    config=core_config,
                )

                schema = gen._apply_model_serializers(td_schema, decorators.model_serializers.values())
                schema = apply_model_validators(schema, decorators.model_validators.values(), 'all')
                return gen.defs.create_definition_reference_schema(schema)


@default_registry.register
class EnumTypeHandler(TypeHandler):
    """Type handler for enums."""

    # NOTE: this must be registered before the named tuple type handler, as enums values can be named tuples:
    match_condition = Predicate(lambda obj: inspect.isclass(obj) and issubclass(obj, Enum))

    def handle_type(self, type: type[Enum], annotations_handler: AnnotationsHandler) -> CoreSchema:
        gen = self.schema_generator
        enum_type = type
        cases: list[Any] = list(enum_type.__members__.values())

        enum_ref = _type_refs.enum_type_ref(enum_type)
        description = None if not enum_type.__doc__ else inspect.cleandoc(enum_type.__doc__)
        if (
            description == 'An enumeration.'
        ):  # This is the default value provided by enum.EnumMeta.__new__; don't use it
            description = None
        js_updates = {'title': enum_type.__name__, 'description': description}
        js_updates = {k: v for k, v in js_updates.items() if v is not None}

        sub_type: Literal['str', 'int', 'float'] | None = None
        if issubclass(enum_type, int):
            sub_type = 'int'
            value_ser_type: core_schema.SerSchema = core_schema.simple_ser_schema('int')
        elif issubclass(enum_type, str):
            # this handles `StrEnum` (3.11 only), and also `Foobar(str, Enum)`
            sub_type = 'str'
            value_ser_type = core_schema.simple_ser_schema('str')
        elif issubclass(enum_type, float):
            sub_type = 'float'
            value_ser_type = core_schema.simple_ser_schema('float')
        else:
            # TODO this is an ugly hack, how do we trigger an Any schema for serialization?
            value_ser_type = core_schema.plain_serializer_function_ser_schema(lambda x: x)

        if cases:

            def get_json_schema(schema: CoreSchema, handler: GetJsonSchemaHandler) -> JsonSchemaValue:
                json_schema = handler(schema)
                original_schema = handler.resolve_ref_schema(json_schema)
                original_schema.update(js_updates)
                return json_schema

            enum_schema = core_schema.enum_schema(
                enum_type,
                cases,
                sub_type=sub_type,
                ref=enum_ref,
                metadata={'pydantic_js_functions': [get_json_schema]},
            )

            if gen._config_wrapper.use_enum_values:
                enum_schema = core_schema.no_info_after_validator_function(
                    attrgetter('value'), enum_schema, serialization=value_ser_type
                )

            return enum_schema

        else:

            def get_json_schema_no_cases(_, handler: GetJsonSchemaHandler) -> JsonSchemaValue:
                json_schema = handler(core_schema.enum_schema(enum_type, cases, sub_type=sub_type, ref=enum_ref))
                original_schema = handler.resolve_ref_schema(json_schema)
                original_schema.update(js_updates)
                return json_schema

            # Use an isinstance check for enums with no cases.
            # The most important use case for this is creating TypeVar bounds for generics that should
            # be restricted to enums. This is more consistent than it might seem at first, since you can only
            # subclass enum.Enum (or subclasses of enum.Enum) if all parent classes have no cases.
            # We use the get_json_schema function when an Enum subclass has been declared with no cases
            # so that we can still generate a valid json schema.
            return core_schema.is_instance_schema(
                enum_type,
                metadata={'pydantic_js_functions': [get_json_schema_no_cases]},
            )


@default_registry.register
class NamedTupleTypeHandler(TypeHandler):
    """Type handler for named tuples."""

    match_condition = Predicate(_typing_extra.is_namedtuple)

    def _generate_schema(self, obj: Any, origin: Any | None, annotations_handler: AnnotationsHandler) -> CoreSchema:
        return self._namedtuple_schema(self.schema_generator, obj, origin)

    def handle_type(self, type: Any, annotations_handler: AnnotationsHandler) -> CoreSchema:
        return self._namedtuple_schema(self.schema_generator, type, None)

    def _namedtuple_schema(self, gen: GenerateSchema, namedtuple_cls: Any, origin: Any) -> CoreSchema:
        """Generate schema for a NamedTuple."""
        namedtuple_ref = _type_refs.class_type_ref(namedtuple_cls, origin)
        with (
            gen.model_type_stack.push(namedtuple_cls),
            gen.defs.get_definition_ref_schema(ref=namedtuple_ref) as maybe_schema,
        ):
            if maybe_schema is not None:
                return maybe_schema
            typevars_map = get_standard_typevars_map(namedtuple_cls)
            if origin is not None:
                namedtuple_cls = origin

            try:
                annotations = _typing_extra.get_cls_type_hints(namedtuple_cls, ns_resolver=gen._ns_resolver)
            except NameError as e:
                raise PydanticUndefinedAnnotation.from_name_error(e) from e

            # Filter annotations to only include fields that are actually in the NamedTuple
            # (as subclassing an existing NamedTuple is not supported yet - see https://github.com/python/typing/issues/427)
            # and use `Any` if no annotation exist (i.e. when using `collections.namedtuple()`).
            annotations = {field_name: annotations.get(field_name, Any) for field_name in namedtuple_cls._fields}

            if typevars_map:
                annotations = {
                    field_name: replace_types(annotation, typevars_map)
                    for field_name, annotation in annotations.items()
                }

            schema = core_schema.named_tuple_schema(
                namedtuple_cls,
                [
                    self._generate_namedtuple_field_schema(
                        gen,
                        field_name,
                        annotation,
                        default=namedtuple_cls._field_defaults.get(field_name, Parameter.empty),
                    )
                    for field_name, annotation in annotations.items()
                ],
                ref=namedtuple_ref,
            )
            return gen.defs.create_definition_reference_schema(schema)

    def _generate_namedtuple_field_schema(
        self,
        gen: GenerateSchema,
        name: str,
        annotation: Any,
        default: Any = Parameter.empty,
    ) -> core_schema.NamedTupleField:
        """Generate the definition of a field in a named tuple."""
        FieldInfo = import_cached_field_info()

        if default is Parameter.empty:
            field = FieldInfo.from_annotation(annotation, _source=AnnotationSource.NAMED_TUPLE)
        else:
            field = FieldInfo.from_annotated_attribute(annotation, default, _source=AnnotationSource.NAMED_TUPLE)

        assert field.annotation is not None, 'field.annotation should not be None when generating a schema'
        update_field_from_config(gen._config_wrapper, name, field)

        with gen.field_name_stack.push(name):
            schema = gen._apply_annotations(
                field.annotation,
                [field],
                # Because we pass `field` as metadata above (required for attributes relevant for
                # JSON Scheme generation), we need to ignore the potential warnings about `FieldInfo`
                # attributes that will not be used:
                check_unsupported_field_info_attributes=False,
            )

        if not field.is_required():
            schema = wrap_default(field, schema)

        return core_schema.named_tuple_field(
            name,
            schema,
            validation_alias=_convert_to_aliases(field.validation_alias),
        )


@default_registry.register
class DataclassTypeHandler(TypeHandler):
    """Type handler for dataclasses (Pydantic or standard library ones)."""

    # `dataclasses.is_dataclass()` coerces dataclass instances to types, but we only handle the case of a dataclass type here:
    match_condition = Predicate(dataclasses.is_dataclass)

    def _generate_schema(self, obj: Any, origin: Any | None, annotations_handler: AnnotationsHandler) -> CoreSchema:
        return self._dataclass_schema(self.schema_generator, obj, origin)

    def handle_type(self, type: Any, annotations_handler: AnnotationsHandler) -> CoreSchema:
        return self._dataclass_schema(self.schema_generator, type, None)

    def _dataclass_schema(
        self, gen: GenerateSchema, dataclass: type[StandardDataclass], origin: type[StandardDataclass] | None
    ) -> CoreSchema:
        """Generate schema for a dataclass."""
        dataclass_ref = _type_refs.class_type_ref(dataclass, origin)
        with (
            gen.model_type_stack.push(dataclass),
            gen.defs.get_definition_ref_schema(ref=dataclass_ref) as maybe_schema,
        ):
            if maybe_schema is not None:
                return maybe_schema

            schema = dataclass.__dict__.get('__pydantic_core_schema__')
            if schema is not None and not isinstance(schema, MockCoreSchema):
                if schema['type'] == 'definitions':
                    schema = gen.defs.unpack_definitions(schema)
                ref = get_ref(schema)
                if ref:
                    return gen.defs.create_definition_reference_schema(schema)
                else:
                    return schema

            typevars_map = get_standard_typevars_map(dataclass)
            if origin is not None:
                dataclass = origin

            # if (plain) dataclass doesn't have config, we use the parent's config, hence a default of `None`
            # (Pydantic dataclasses have an empty dict config by default).
            # see https://github.com/pydantic/pydantic/issues/10917
            config = getattr(dataclass, '__pydantic_config__', None)

            from ....dataclasses import is_pydantic_dataclass

            with gen._ns_resolver.push(dataclass), gen._config_wrapper_stack.push(config):
                if is_pydantic_dataclass(dataclass):
                    if dataclass.__pydantic_fields_complete__():
                        # Copy the field info instances to avoid mutating the `FieldInfo` instances
                        # of the generic dataclass generic origin (e.g. `apply_typevars_map` below).
                        # Note that we don't apply `deepcopy` on `__pydantic_fields__` because we
                        # don't want to copy the `FieldInfo` attributes:
                        fields = {
                            f_name: copy(field_info) for f_name, field_info in dataclass.__pydantic_fields__.items()
                        }
                        if typevars_map:
                            for field in fields.values():
                                field.apply_typevars_map(typevars_map, *gen._types_namespace)
                    else:
                        try:
                            fields = rebuild_dataclass_fields(
                                dataclass,
                                config_wrapper=gen._config_wrapper,
                                ns_resolver=gen._ns_resolver,
                                typevars_map=typevars_map or {},
                            )
                        except NameError as e:
                            raise PydanticUndefinedAnnotation.from_name_error(e) from e
                else:
                    fields = collect_dataclass_fields(
                        dataclass,
                        typevars_map=typevars_map,
                        config_wrapper=gen._config_wrapper,
                    )

                if gen._config_wrapper.extra == 'allow':
                    # disallow combination of init=False on a dataclass field and extra='allow' on a dataclass
                    for field_name, field in fields.items():
                        if field.init is False:
                            raise PydanticUserError(
                                f'Field {field_name} has `init=False` and dataclass has config setting `extra="allow"`. '
                                f'This combination is not allowed.',
                                code='dataclass-init-false-extra-allow',
                            )

                decorators = dataclass.__dict__.get('__pydantic_decorators__')
                if decorators is None:
                    decorators = DecoratorInfos.build(dataclass, replace_wrapped_methods=False)
                    decorators.update_from_config(gen._config_wrapper)
                # Move kw_only=False args to the start of the list, as this is how vanilla dataclasses work.
                # Note that when kw_only is missing or None, it is treated as equivalent to kw_only=True
                args = sorted(
                    (gen._generate_dc_field_schema(k, v, decorators) for k, v in fields.items()),
                    key=lambda a: a.get('kw_only') is not False,
                )
                has_post_init = hasattr(dataclass, '__post_init__')
                has_slots = hasattr(dataclass, '__slots__')

                args_schema = core_schema.dataclass_args_schema(
                    dataclass.__name__,
                    args,
                    computed_fields=[
                        gen._computed_field_schema(d, decorators.field_serializers)
                        for d in decorators.computed_fields.values()
                    ],
                    collect_init_only=has_post_init,
                )

                model_validators = decorators.model_validators.values()
                inner_schema = apply_model_validators(args_schema, model_validators, 'inner')

                core_config = gen._config_wrapper.core_config(title=dataclass.__name__)

                dc_schema = core_schema.dataclass_schema(
                    dataclass,
                    inner_schema,
                    generic_origin=origin,
                    post_init=has_post_init,
                    ref=dataclass_ref,
                    fields=[field.name for field in dataclasses.fields(dataclass)],
                    slots=has_slots,
                    config=core_config,
                    # we don't use a custom __setattr__ for dataclasses, so we must
                    # pass along the frozen config setting to the pydantic-core schema
                    frozen=gen._config_wrapper_stack.tail.frozen,
                )
                schema = gen._apply_model_serializers(dc_schema, decorators.model_serializers.values())
                schema = apply_model_validators(schema, model_validators, 'outer')
                return gen.defs.create_definition_reference_schema(schema)


@default_registry.register
class CallTypeHandler(TypeHandler):
    """Type handler for functions (used by `validate_call()`)."""

    match_condition = Predicate(lambda obj: isinstance(obj, VALIDATE_CALL_SUPPORTED_TYPES))

    def handle_type(self, type: Any, annotations_handler: AnnotationsHandler) -> CoreSchema:
        gen = self.schema_generator
        function = type
        """Generate schema for a Callable.

        TODO support functional validators once we support them in Config
        """
        arguments_schema = gen._arguments_schema(function)

        return_schema: core_schema.CoreSchema | None = None
        config_wrapper = gen._config_wrapper
        if config_wrapper.validate_return:
            sig = _typing_extra.signature_no_eval(function)
            return_hint = sig.return_annotation
            if return_hint is not sig.empty:
                globalns, localns = gen._types_namespace
                type_hints = _typing_extra.get_function_type_hints(
                    function, globalns=globalns, localns=localns, include_keys={'return'}
                )
                return_schema = gen.generate_schema(type_hints['return'])

        return core_schema.call_schema(
            arguments_schema,
            function,
            return_schema=return_schema,
        )
