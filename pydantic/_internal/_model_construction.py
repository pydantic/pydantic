"""
Private logic for creating models.
"""
from __future__ import annotations as _annotations

import sys
import typing
import warnings
from types import FunctionType
from typing import Any, Callable

from pydantic_core import SchemaValidator, core_schema
from typing_extensions import Annotated

from ..fields import FieldInfo, ModelPrivateAttr, PrivateAttr
from . import _typing_extra
from ._fields import SchemaRef, Undefined
from ._generate_schema import generate_config, model_fields_schema
from ._utils import ClassAttribute, is_valid_identifier
from ._validation_functions import ValidationFunctions

if typing.TYPE_CHECKING:
    from inspect import Signature

    from ..config import BaseConfig
    from ..main import BaseModel

__all__ = 'object_setattr', 'init_private_attributes', 'inspect_namespace', 'complete_model_class'


IGNORED_TYPES: tuple[Any, ...] = (FunctionType, property, type, classmethod, staticmethod)
object_setattr = object.__setattr__


def init_private_attributes(self_: Any, **_kwargs: Any) -> None:
    """
    This method is bound to model classes to initialise private attributes.
    """
    for name, private_attr in self_.__private_attributes__.items():
        default = private_attr.get_default()
        if default is not Undefined:
            object_setattr(self_, name, default)


def inspect_namespace(namespace: dict[str, Any]) -> dict[str, ModelPrivateAttr]:
    """
    iterate over the namespace and:
    * gather private attributes
    * check for items which look like fields but are not (e.g. have no annotation) and warn
    """
    private_attributes: dict[str, ModelPrivateAttr] = {}
    raw_annotations = namespace.get('__annotations__', {})
    for var_name, value in list(namespace.items()):
        if isinstance(value, ModelPrivateAttr):
            if var_name.startswith('__'):
                raise NameError(
                    f'Private attributes "{var_name}" must not have dunder names; '
                    'Use a single underscore prefix instead.'
                )
            elif not single_underscore(var_name):
                raise NameError(
                    f'Private attributes "{var_name}" must not be a valid field name; '
                    f'Use sunder or dunder names, e. g. "_{var_name}"'
                )
            private_attributes[var_name] = value
            del namespace[var_name]
        elif not single_underscore(var_name):
            continue
        elif var_name.startswith('_'):
            private_attributes[var_name] = PrivateAttr(default=value)
            del namespace[var_name]
        elif var_name not in raw_annotations and not isinstance(value, IGNORED_TYPES):
            warnings.warn(
                f'All fields must include a type annotation; '
                f'{var_name!r} looks like a field but has no type annotation.',
                DeprecationWarning,
            )

    for ann_name in raw_annotations:
        if single_underscore(ann_name) and ann_name not in private_attributes:
            private_attributes[ann_name] = PrivateAttr()

    return private_attributes


def single_underscore(name: str) -> bool:
    return name.startswith('_') and not name.startswith('__')


def complete_model_class(
    cls: type[BaseModel], name: str, validator_functions: ValidationFunctions, bases: tuple[type[Any], ...]
) -> None:
    """
    Collect bound validator functions, build the model validation schema and set the model signature.

    This logic must be called after class has been created since validation functions must be bound
    and `get_type_hints` requires a class object.
    """
    validator_functions.set_bound_functions(cls)

    module_name = getattr(cls, '__module__', None)
    base_globals: dict[str, Any] | None = None
    if module_name:
        try:
            module = sys.modules[module_name]
        except KeyError:
            # happens occasionally, see https://github.com/pydantic/pydantic/issues/2363
            pass
        else:
            base_globals = module.__dict__

    fields: dict[str, FieldInfo] = {}
    core_config = generate_config(cls.__config__)
    model_ref = f'{module_name}.{name}'
    self_schema = core_schema.new_class_schema(cls, core_schema.recursive_reference_schema(model_ref))
    localns = {name: Annotated[Any, SchemaRef('SelfType', self_schema)]}
    for ann_name, ann_type in _typing_extra.get_type_hints(cls, base_globals, localns, include_extras=True).items():
        if ann_name.startswith('_') or _typing_extra.is_classvar(ann_type):
            continue

        for base in bases:
            if hasattr(base, ann_name):
                raise NameError(
                    f'Field name "{ann_name}" shadows an attribute in parent "{base.__qualname__}"; '
                    f'you might want to use a different field name with "alias=\'{ann_name}\'".'
                )

        try:
            default = getattr(cls, ann_name)
        except AttributeError:
            fields[ann_name] = FieldInfo.from_annotation(ann_type)
        else:
            fields[ann_name] = FieldInfo.from_annotated_attribute(ann_type, default)
            # attributes which are fields are removed from the class namespace:
            # 1. To match the behaviour of annotation-only fields
            # 2. To avoid false positives in the NameError check above
            delattr(cls, ann_name)

    inner_schema = model_fields_schema(model_ref, fields, validator_functions, cls.__config__.arbitrary_types_allowed)
    validator_functions.check_for_unused()

    cls.__fields__ = fields
    cls.__pydantic_validator__ = SchemaValidator(inner_schema, core_config)
    model_post_init = '__pydantic_post_init__' if hasattr(cls, '__pydantic_post_init__') else None
    cls.__pydantic_validation_schema__ = core_schema.new_class_schema(
        cls, inner_schema, config=core_config, call_after_init=model_post_init
    )

    # set __signature__ attr only for model class, but not for its instances
    cls.__signature__ = ClassAttribute('__signature__', generate_model_signature(cls.__init__, fields, cls.__config__))


def generate_model_signature(
    init: Callable[..., None], fields: dict[str, FieldInfo], config: type[BaseConfig]
) -> Signature:
    """
    Generate signature for model based on its fields
    """
    from inspect import Parameter, Signature, signature
    from itertools import islice

    from ..config import Extra

    present_params = signature(init).parameters.values()
    merged_params: dict[str, Parameter] = {}
    var_kw = None
    use_var_kw = False

    for param in islice(present_params, 1, None):  # skip self arg
        if param.kind is param.VAR_KEYWORD:
            var_kw = param
            continue
        merged_params[param.name] = param

    if var_kw:  # if custom init has no var_kw, fields which are not declared in it cannot be passed through
        allow_names = config.allow_population_by_field_name
        for field_name, field in fields.items():
            param_name = field.alias or field_name
            if field_name in merged_params or param_name in merged_params:
                continue
            elif not is_valid_identifier(param_name):
                if allow_names and is_valid_identifier(field_name):
                    param_name = field_name
                else:
                    use_var_kw = True
                    continue

            # TODO: replace annotation with actual expected types once #1055 solved
            kwargs = {} if field.is_required() else {'default': field.get_default()}
            merged_params[param_name] = Parameter(
                param_name, Parameter.KEYWORD_ONLY, annotation=field.annotation, **kwargs
            )

    if config.extra is Extra.allow:
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
