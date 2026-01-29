"""Type handler for Pydantic models."""

from __future__ import annotations

import typing
from typing import TYPE_CHECKING, Any, TypedDict
from itertools import chain


from pydantic import Strict, PydanticUndefinedAnnotation
from .._type_handlers import TypeHandler

from ... import _repr
from ..._import_utils import import_cached_base_model
from ..._core_utils import get_ref
from ..._mock_val_ser import MockCoreSchema
from ..._fields import rebuild_model_fields
from .._type_registry import pydantic_registry
from .._conditions import Predicate
from pydantic_core import CoreSchema
import pydantic_core.core_schema as cs

from typing_extensions import TypeIs, get_origin

if TYPE_CHECKING:
    from pydantic import BaseModel
    from pydantic.fields import FieldInfo
    from ..._decorators import DecoratorInfos


def is_pydantic_model(tp) -> TypeIs[type[BaseModel]]:
    from pydantic import BaseModel

    return isinstance(tp, type) and issubclass(tp, BaseModel)


class _CommonField(TypedDict):
    schema: CoreSchema
    validation_alias: str | list[str | int] | list[list[str | int]] | None
    serialization_alias: str | None
    serialization_exclude: bool | None
    frozen: bool | None
    metadata: dict[str, Any]


def _common_field(
    schema: CoreSchema,
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


@pydantic_registry.register(condition=Predicate(is_pydantic_model))
class PydanticModelTypeHandler(TypeHandler):
    """Type handler for Pydantic models."""

    known_metadata = {Strict}
    produces_reference = True

    def handle_type(self, type: type[BaseModel]) -> CoreSchema:
        from ..._generate_schema import check_decorator_fields_exist, apply_model_validators, apply_validators
        from ..._config import ConfigWrapper
        from pydantic.errors import PydanticSchemaGenerationError

        BaseModel_ = import_cached_base_model()

        cls = type

        schema = cls.__dict__.get('__pydantic_core_schema__')
        if schema is not None and not isinstance(schema, MockCoreSchema):
            if schema['type'] == 'definitions':
                schema = self.generate_schema.defs.unpack_definitions(schema)
            ref = get_ref(schema)
            if ref:
                return self.generate_schema.defs.create_definition_reference_schema(schema)
            else:
                return schema

        ref = self.get_reference(None, cls)

        config_wrapper = ConfigWrapper(cls.model_config, check=False)

        with (
            self.generate_schema._config_wrapper_stack.push(config_wrapper),
            self.generate_schema._ns_resolver.push(cls),
        ):
            core_config = config_wrapper.core_config(title=cls.__name__)

            if cls.__pydantic_fields_complete__ or cls is BaseModel_:
                fields = getattr(cls, '__pydantic_fields__', {})
                extra_info = getattr(cls, '__pydantic_extra_info__', None)
            else:
                try:
                    fields, extra_info = rebuild_model_fields(
                        cls,
                        config_wrapper=self.generate_schema._config_wrapper_stack.tail,
                        ns_resolver=self.generate_schema._ns_resolver,
                        typevars_map=self.generate_schema._typevars_map or {},
                    )
                except NameError as e:
                    raise PydanticUndefinedAnnotation.from_name_error(e) from e

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

            model_validators = decorators.model_validators.values()

            extras_schema = None
            extras_keys_schema = None
            if core_config.get('extra_fields_behavior') == 'allow' and extra_info is not None:
                tp = get_origin(extra_info.annotation)
                if tp not in (dict, typing.Dict):
                    raise PydanticSchemaGenerationError(
                        'The type annotation for `__pydantic_extra__` must be `dict[str, ...]`',
                    )

            generic_origin: type[BaseModel] | None = getattr(cls, '__pydantic_generic_metadata__', {}).get('origin')

            if cls.__pydantic_root_model__:
                inner_schema, _ = self.generate_schema._common_field_schema('root', fields['root'], decorators)
                inner_schema = apply_model_validators(inner_schema, model_validators, 'inner')
                model_schema = cs.model_schema(
                    cls,
                    inner_schema,
                    generic_origin=generic_origin,
                    custom_init=getattr(cls, '__pydantic_custom_init__', None),
                    root_model=True,
                    post_init=getattr(cls, '__pydantic_post_init__', None),
                    config=core_config,
                    ref=ref,
                )
            else:
                fields_schema: CoreSchema = cs.model_fields_schema(
                    {k: self._generate_md_field_schema(k, v, decorators) for k, v in fields.items()},
                    computed_fields=[],
                    extras_schema=extras_schema,
                    model_name=cls.__name__,
                )
                inner_schema = apply_validators(fields_schema, decorators.root_validators.values())
                inner_schema = apply_model_validators(inner_schema, model_validators, 'inner')

                model_schema = cs.model_schema(
                    cls,
                    inner_schema,
                    generic_origin=generic_origin,
                    custom_init=getattr(cls, '__pydantic_custom_init__', None),
                    root_model=False,
                    post_init=getattr(cls, '__pydantic_post_init__', None),
                    config=core_config,
                    ref=ref,
                )

            # schema = self._apply_model_serializers(model_schema, decorators.model_serializers.values())
            schema = apply_model_validators(model_schema, model_validators, 'outer')
            return self.generate_schema.defs.create_definition_reference_schema(schema)

    def get_reference(self, origin: None, obj: type[BaseModel]) -> str:
        # TODO: AttributeError for bare `BaseModel`:
        generic_metadata = obj.__pydantic_generic_metadata__
        pydantic_origin = generic_metadata['origin'] or obj
        args = generic_metadata['args']
        module_name = getattr(pydantic_origin, '__module__', '<No __module__>')
        qualname = getattr(pydantic_origin, '__qualname__', '<No __qualname__>')
        type_ref = f'{module_name}.{qualname}:{id(pydantic_origin)}'

        arg_refs: list[str] = []
        for arg in args:
            if isinstance(arg, str):
                # Handle string literals as a special case; we may be able to remove this special handling if we
                # wrap them in a ForwardRef at some point.
                arg_ref = f'{arg}:str-{id(arg)}'
            else:
                arg_ref = f'{_repr.display_as_type(arg)}:{id(arg)}'
            arg_refs.append(arg_ref)

        if arg_refs:
            type_ref = f'{type_ref}[{",".join(arg_refs)}]'
        return type_ref

    def _common_field_schema(  # C901
        self, name: str, field_info: FieldInfo, decorators: DecoratorInfos
    ) -> _CommonField:
        from pydantic import AliasChoices, AliasPath
        from ..._generate_schema import (
            filter_field_decorator_info_by_field,
            _mode_to_validator,
            _validators_require_validate_default,
            apply_each_item_validators,
            apply_validators,
            wrap_default,
            _extract_json_schema_info_from_field_info,
            update_core_metadata,
        )

        source_type, annotations = field_info.annotation, field_info.metadata

        # Convert `@field_validator` decorators to `Before/After/Plain/WrapValidator` instances:
        validators_from_decorators = []
        for decorator in filter_field_decorator_info_by_field(decorators.field_validators.values(), name):
            validators_from_decorators.append(_mode_to_validator[decorator.info.mode]._from_decorator(decorator))

        with self.generate_schema.field_name_stack.push(name):
            if field_info.discriminator is not None:
                schema = self.generate_schema._generate_schema_inner(
                    source_type, annotations + validators_from_decorators
                )
            else:
                schema = self.generate_schema._generate_schema_inner(
                    source_type, annotations + validators_from_decorators
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

        schema = apply_validators(schema, this_field_validators)

        # the default validator needs to go outside of any other validators
        # so that it is the topmost validator for the field validator
        # which uses it to check if the field has a default value or not
        if not field_info.is_required():
            schema = wrap_default(field_info, schema)

        filter_field_decorator_info_by_field(decorators.field_serializers.values(), name)
        # schema = self._apply_field_serializers(
        #     schema, filter_field_decorator_info_by_field(decorators.field_serializers.values(), name)
        # )

        pydantic_js_updates, pydantic_js_extra = _extract_json_schema_info_from_field_info(field_info)
        core_metadata: dict[str, Any] = {}
        update_core_metadata(
            core_metadata, pydantic_js_updates=pydantic_js_updates, pydantic_js_extra=pydantic_js_extra
        )

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
            metadata=core_metadata,
        )

    def _generate_md_field_schema(
        self,
        name: str,
        field_info: FieldInfo,
        decorators: DecoratorInfos,
    ):
        """Prepare a ModelField to represent a model field."""

        from ..._generate_schema import _convert_to_aliases

        schema, metadata = self.generate_schema._common_field_schema(name, field_info, decorators)
        return cs.model_field(
            schema,
            serialization_exclude=field_info.exclude,
            validation_alias=_convert_to_aliases(field_info.validation_alias),
            serialization_alias=field_info.serialization_alias,
            frozen=field_info.frozen,
            metadata=metadata,
        )