"""
Private logic for creating models.
"""
from __future__ import annotations as _annotations

import typing
from functools import partial
from types import FunctionType
from typing import Any, Callable

from pydantic_core import SchemaSerializer, SchemaValidator

from ..errors import PydanticErrorCodes, PydanticUndefinedAnnotation, PydanticUserError
from ..fields import FieldInfo, ModelPrivateAttr, PrivateAttr
from ._config import ConfigWrapper
from ._core_utils import flatten_schema_defs, inline_schema_defs
from ._decorators import ComputedFieldInfo, PydanticDescriptorProxy
from ._fields import Undefined, collect_model_fields
from ._generate_schema import GenerateSchema
from ._generics import get_model_typevars_map
from ._typing_extra import is_classvar
from ._utils import ClassAttribute, is_valid_identifier

if typing.TYPE_CHECKING:
    from inspect import Signature

    from ..config import ConfigDict
    from ..main import BaseModel


IGNORED_TYPES: tuple[Any, ...] = (
    FunctionType,
    property,
    type,
    classmethod,
    staticmethod,
    PydanticDescriptorProxy,
    ComputedFieldInfo,
)
object_setattr = object.__setattr__


def init_private_attributes(self: BaseModel, __context: Any) -> None:
    """
    This function is meant to behave like a BaseModel method to initialise private attributes.

    It takes context as an argument since that's what pydantic-core passes when calling it.
    """
    for name, private_attr in self.__private_attributes__.items():
        default = private_attr.get_default()
        if default is not Undefined:
            object_setattr(self, name, default)


def inspect_namespace(  # noqa C901
    namespace: dict[str, Any],
    ignored_types: tuple[type[Any], ...],
    base_class_vars: set[str],
    base_class_fields: set[str],
) -> dict[str, ModelPrivateAttr]:
    """
    iterate over the namespace and:
    * gather private attributes
    * check for items which look like fields but are not (e.g. have no annotation) and warn
    """
    all_ignored_types = ignored_types + IGNORED_TYPES

    private_attributes: dict[str, ModelPrivateAttr] = {}
    raw_annotations = namespace.get('__annotations__', {})

    if '__root__' in raw_annotations or '__root__' in namespace:
        # TODO: Update error message with migration description and/or link to documentation
        #   Needs to mention:
        #   * Use root_validator to wrap input data in a dict
        #   * Use model_serializer to extract wrapped data during dumping
        #   * Use model_modify_json_schema (or whatever it becomes) to unwrap the JSON schema
        raise TypeError(
            '__root__ models are no longer supported in v2; a migration guide will be added in the near future'
        )

    ignored_names: set[str] = set()
    for var_name, value in list(namespace.items()):
        if var_name == 'model_config':
            continue
        elif isinstance(value, all_ignored_types) or value.__class__.__module__ == 'functools':
            ignored_names.add(var_name)
            continue
        elif isinstance(value, ModelPrivateAttr):
            if var_name.startswith('__'):
                raise NameError(
                    f'Private attributes "{var_name}" must not have dunder names; '
                    'use a single underscore prefix instead.'
                )
            elif not single_underscore(var_name):
                raise NameError(
                    f'Private attributes "{var_name}" must not be a valid field name; '
                    f'use sunder names, e.g. "_{var_name}"'
                )
            private_attributes[var_name] = value
            del namespace[var_name]
        elif var_name.startswith('__'):
            continue
        elif var_name.startswith('_'):
            if var_name in raw_annotations and not is_classvar(raw_annotations[var_name]):
                private_attributes[var_name] = PrivateAttr(default=value)
                del namespace[var_name]
        elif var_name in base_class_vars:
            continue
        elif var_name not in raw_annotations:
            if var_name in base_class_fields:
                raise PydanticUserError(
                    f'Field {var_name!r} defined on a base class was overridden by a non-annotated attribute. '
                    f'All field definitions, including overrides, require a type annotation.',
                    code='model-field-overridden',
                )
            elif isinstance(value, FieldInfo):
                raise PydanticUserError(
                    f'Field {var_name!r} requires a type annotation', code='model-field-missing-annotation'
                )
            else:
                raise PydanticUserError(
                    f"A non-annotated attribute was detected: `{var_name} = {value!r}`. All model fields require a "
                    f"type annotation; if `{var_name}` is not meant to be a field, you may be able to resolve this "
                    f"error by annotating it as a `ClassVar` or updating `model_config['ignored_types']`.",
                    code='model-field-missing-annotation',
                )

    for ann_name, ann_type in raw_annotations.items():
        if (
            single_underscore(ann_name)
            and ann_name not in private_attributes
            and ann_name not in ignored_names
            and not is_classvar(ann_type)
            and ann_type not in all_ignored_types
            and ann_type.__module__ != 'functools'
        ):
            private_attributes[ann_name] = PrivateAttr()

    return private_attributes


def single_underscore(name: str) -> bool:
    return name.startswith('_') and not name.startswith('__')


def set_model_fields(cls: type[BaseModel], bases: tuple[type[Any], ...], types_namespace: dict[str, Any]) -> None:
    """
    Collect and set `cls.model_fields` and `cls.__class_vars__`.
    """
    typevars_map = get_model_typevars_map(cls)
    fields, class_vars = collect_model_fields(cls, bases, types_namespace, typevars_map=typevars_map)

    apply_alias_generator(cls.model_config, fields)
    cls.model_fields = fields
    cls.__class_vars__.update(class_vars)


def complete_model_class(
    cls: type[BaseModel],
    cls_name: str,
    config_wrapper: ConfigWrapper,
    *,
    raise_errors: bool = True,
    types_namespace: dict[str, Any] | None,
) -> bool:
    """
    Finish building a model class.

    Returns `True` if the model is successfully completed, else `False`.

    This logic must be called after class has been created since validation functions must be bound
    and `get_type_hints` requires a class object.
    """
    typevars_map = get_model_typevars_map(cls)
    gen_schema = GenerateSchema(
        config_wrapper,
        types_namespace,
        typevars_map,
    )
    try:
        schema = cls.__get_pydantic_core_schema__(
            cls, partial(gen_schema.generate_schema, from_dunder_get_core_schema=False)
        )
    except PydanticUndefinedAnnotation as e:
        if raise_errors:
            raise
        if config_wrapper.undefined_types_warning:
            config_warning_string = (
                f'`{cls_name}` has an undefined annotation: `{e.name}`. '
                f'It may be possible to resolve this by setting '
                f'undefined_types_warning=False in the config for `{cls_name}`.'
            )
            # FIXME UserWarning should not be raised here, but rather warned!
            raise UserWarning(config_warning_string)
        usage_warning_string = (
            f'`{cls_name}` is not fully defined; you should define `{e.name}`, then call `{cls_name}.model_rebuild()` '
            f'before the first `{cls_name}` instance is created.'
        )
        cls.__pydantic_validator__ = MockValidator(  # type: ignore[assignment]
            usage_warning_string, code='model-not-fully-defined'
        )
        return False

    core_config = config_wrapper.core_config(cls)

    # debug(schema)
    cls.__pydantic_core_schema__ = schema

    schema = flatten_schema_defs(schema)
    simplified_core_schema = inline_schema_defs(schema)
    cls.__pydantic_validator__ = SchemaValidator(simplified_core_schema, core_config)
    cls.__pydantic_serializer__ = SchemaSerializer(simplified_core_schema, core_config)
    cls.__pydantic_model_complete__ = True

    # set __signature__ attr only for model class, but not for its instances
    cls.__signature__ = ClassAttribute(
        '__signature__', generate_model_signature(cls.__init__, cls.model_fields, config_wrapper)
    )
    return True


def generate_model_signature(
    init: Callable[..., None], fields: dict[str, FieldInfo], config_wrapper: ConfigWrapper
) -> Signature:
    """
    Generate signature for model based on its fields
    """
    from inspect import Parameter, Signature, signature
    from itertools import islice

    present_params = signature(init).parameters.values()
    merged_params: dict[str, Parameter] = {}
    var_kw = None
    use_var_kw = False

    for param in islice(present_params, 1, None):  # skip self arg
        # inspect does "clever" things to show annotations as strings because we have
        # `from __future__ import annotations` in main, we don't want that
        if param.annotation == 'Any':
            param = param.replace(annotation=Any)
        if param.kind is param.VAR_KEYWORD:
            var_kw = param
            continue
        merged_params[param.name] = param

    if var_kw:  # if custom init has no var_kw, fields which are not declared in it cannot be passed through
        allow_names = config_wrapper.populate_by_name
        for field_name, field in fields.items():
            # when alias is a str it should be used for signature generation
            if isinstance(field.alias, str):
                param_name = field.alias
            else:
                param_name = field_name
            if field_name in merged_params or param_name in merged_params:
                continue
            elif not is_valid_identifier(param_name):
                if allow_names and is_valid_identifier(field_name):
                    param_name = field_name
                else:
                    use_var_kw = True
                    continue

            # TODO: replace annotation with actual expected types once #1055 solved
            kwargs = {} if field.is_required() else {'default': field.get_default(call_default_factory=False)}
            merged_params[param_name] = Parameter(
                param_name, Parameter.KEYWORD_ONLY, annotation=field.rebuild_annotation(), **kwargs
            )

    if config_wrapper.extra == 'allow':
        use_var_kw = True

    if var_kw and use_var_kw:
        # Make sure the parameter for extra kwargs
        # does not have the same name as a field
        default_model_signature = [
            ('__pydantic_self__', Parameter.POSITIONAL_OR_KEYWORD),
            ('data', Parameter.VAR_KEYWORD),
        ]
        if [(p.name, p.kind) for p in present_params] == default_model_signature:
            # if this is the standard model signature, use extra_data as the extra args name
            var_kw_name = 'extra_data'
        else:
            # else start from var_kw
            var_kw_name = var_kw.name

        # generate a name that's definitely unique
        while var_kw_name in fields:
            var_kw_name += '_'
        merged_params[var_kw_name] = var_kw.replace(name=var_kw_name)

    return Signature(parameters=list(merged_params.values()), return_annotation=None)


class MockValidator:
    """
    Mocker for `pydantic_core.SchemaValidator` which just raises an error when one of its methods is accessed.
    """

    __slots__ = '_error_message', '_code'

    def __init__(self, error_message: str, *, code: PydanticErrorCodes) -> None:
        self._error_message = error_message
        self._code: PydanticErrorCodes = code

    def __getattr__(self, item: str) -> None:
        __tracebackhide__ = True
        # raise an AttributeError if `item` doesn't exist
        getattr(SchemaValidator, item)
        raise PydanticUserError(self._error_message, code=self._code)


def apply_alias_generator(config: ConfigDict, fields: dict[str, FieldInfo]) -> None:
    alias_generator = config.get('alias_generator')
    if alias_generator is None:
        return

    for name, field_info in fields.items():
        if field_info.alias_priority is None or field_info.alias_priority <= 1:
            alias = alias_generator(name)
            if not isinstance(alias, str):
                raise TypeError(f'alias_generator {alias_generator} must return str, not {alias.__class__}')
            field_info.alias = alias
            field_info.validation_alias = alias
            field_info.serialization_alias = alias
            field_info.alias_priority = 1


def model_extra_getattr(self: BaseModel, item: str) -> Any:
    """
    This function is used to retrieve unrecognized attribute values from BaseModel subclasses which
    allow (and store) extra
    """
    if self.__pydantic_extra__ is not None:
        try:
            return self.__pydantic_extra__[item]
        except KeyError as exc:
            raise AttributeError(f'{type(self).__name__!r} object has no attribute {item!r}') from exc
    else:
        raise AttributeError(f'{type(self).__name__!r} object has no attribute {item!r}')
