from __future__ import annotations as _annotations

import sys
import warnings
from types import FunctionType
from typing import TYPE_CHECKING, Any, Callable, Type, get_type_hints

from pydantic_core import Schema as PydanticCoreSchema, SchemaValidator

from ..fields import FieldInfo, ModelPrivateAttr, PrivateAttr
from ..utils import ClassAttribute, is_valid_identifier
from .babelfish import generate_config, model_fields_schema
from .typing_extra import is_classvar
from .valdation_functions import ValidationFunctions

if TYPE_CHECKING:
    from inspect import Signature

    from ..config import BaseConfig
    from ..main import BaseModel

__all__ = 'inspect_namespace', 'complete_model_class'


IGNORED_TYPES: tuple[Any, ...] = (FunctionType, property, type, classmethod, staticmethod)
DUNDER_ATTRIBUTES = {
    '__annotations__',
    '__classcell__',
    '__doc__',
    '__module__',
    '__orig_bases__',
    '__orig_class__',
    '__qualname__',
    '__slots__',
    '__config__',
}
# attribute names to ignore off the bat, mostly to save time
IGNORED_ATTRIBUTES = DUNDER_ATTRIBUTES | {'Config'}


def inspect_namespace(namespace) -> None:
    """
    iterate over the namespace and:
    * gather private attributes
    * check for items which look like fields but are not (e.g. have no annotation) and warn
    """
    private_attributes: dict[str, ModelPrivateAttr] = {}
    raw_annotations = namespace.get('__annotations__', {})
    for var_name, value in namespace.items():
        if isinstance(value, ModelPrivateAttr):
            if not var_name.startswith('_') or var_name in DUNDER_ATTRIBUTES:
                raise NameError(
                    f'Private attributes "{var_name}" must not be a valid field name; '
                    f'Use sunder or dunder names, e. g. "_{var_name}" or "__{var_name}__"'
                )
            private_attributes[var_name] = value
        elif var_name in IGNORED_ATTRIBUTES:
            continue
        elif var_name.startswith('_'):
            private_attributes[var_name] = PrivateAttr(default=value)
        elif var_name not in raw_annotations and not isinstance(value, IGNORED_TYPES):
            warnings.warn(
                f'All fields must include a type annotation; '
                f'{var_name!r} looks like a field but has no type annotation.',
                DeprecationWarning,
            )

    namespace['__private_attributes__'] = private_attributes
    if private_attributes:
        for k in private_attributes:
            del namespace[k]
        slots: set[str] = set(namespace.get('__slots__', ()))
        namespace['__slots__'] = slots | private_attributes.keys()


class SelfType:
    """
    This is used to identify a reference to the current model class, e.g. in recursive classes
    """

    pass


def complete_model_class(
    cls: Type[BaseModel], name: str, validator_functions: ValidationFunctions, bases: tuple[type[Any], ...]
):
    """
    Collect bound validator functions, build the model validation schema and set the model signature.

    This logic must be called after class has been created since validation functions must be bound
    and `get_type_hints` requires a class object.
    """
    validator_functions.set_bound_functions(cls)

    module_name = getattr(cls, '__module__')
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
    for ann_name, ann_type in get_type_hints(cls, base_globals, {name: SelfType}).items():
        # TODO NotField
        if ann_name.startswith('_') or is_classvar(ann_type):
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

    core_config = generate_config(cls.__config__)
    inner_schema = model_fields_schema(fields, validator_functions)
    validator_functions.check_for_unused()

    cls.__fields__ = fields
    cls.__pydantic_validator__ = SchemaValidator(inner_schema, core_config)
    cls.__pydantic_validation_schema__: PydanticCoreSchema = {
        'type': 'new-class',
        'class_type': cls,
        'schema': inner_schema,
        'config': core_config,
    }

    # set __signature__ attr only for model class, but not for its instances
    cls.__signature__ = ClassAttribute('__signature__', generate_model_signature(cls.__init__, fields, cls.__config__))


def generate_model_signature(
    init: Callable[..., None], fields: dict[str, FieldInfo], config: Type[BaseConfig]
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
