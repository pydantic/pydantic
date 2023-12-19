from __future__ import annotations

from inspect import Parameter, Signature, signature
from typing import TYPE_CHECKING, Any, Callable

from ._config import ConfigWrapper
from ._utils import is_valid_identifier

if TYPE_CHECKING:
    from ..fields import FieldInfo


def _field_name_or_alias(field_name: str, field_info: FieldInfo) -> str:
    """Extract the correct name to use for the field when generating a signature.
    If it has a valid alias then returns its alais, else returns its name
    Args:
        field_name: The name of the field
        field_info: The field

    Returns:
        The correct name to use when generating a signature.
    """
    return (
        field_info.alias if isinstance(field_info.alias, str) and is_valid_identifier(field_info.alias) else field_name
    )


def generate_pydantic_signature(
    init: Callable[..., None],
    fields: dict[str, FieldInfo],
    config_wrapper: ConfigWrapper,
    parameter_post_processor: Callable[[Parameter], Parameter] = lambda x: x,
) -> Signature:
    """Generate signature for a pydantic BaseModel or dataclass.

    Args:
        init: The class init.
        fields: The model fields.
        config_wrapper: The config wrapper instance.
        parameter_post_processor: Optional additional processing for parameter

    Returns:
        The dataclass/BaseModel subclass signature.
    """
    from itertools import islice

    present_params = signature(init).parameters.values()
    merged_params: dict[str, Parameter] = {}
    var_kw = None
    use_var_kw = False

    for param in islice(present_params, 1, None):  # skip self arg
        # inspect does "clever" things to show annotations as strings because we have
        # `from __future__ import annotations` in main, we don't want that
        if fields.get(param.name) and isinstance(fields[param.name].alias, str):
            param_name = _field_name_or_alias(param.name, fields[param.name])
            param = param.replace(name=param_name)
        if param.annotation == 'Any':
            param = param.replace(annotation=Any)
        if param.kind is param.VAR_KEYWORD:
            var_kw = param
            continue
        merged_params[param.name] = parameter_post_processor(param)

    if var_kw:  # if custom init has no var_kw, fields which are not declared in it cannot be passed through
        allow_names = config_wrapper.populate_by_name
        for field_name, field in fields.items():
            # when alias is a str it should be used for signature generation
            param_name = _field_name_or_alias(field_name, field)

            if field_name in merged_params or param_name in merged_params:
                continue

            if not is_valid_identifier(param_name):
                if allow_names:
                    param_name = field_name
                else:
                    use_var_kw = True
                    continue

            kwargs = {} if field.is_required() else {'default': field.get_default(call_default_factory=False)}
            merged_params[param_name] = parameter_post_processor(
                Parameter(param_name, Parameter.KEYWORD_ONLY, annotation=field.rebuild_annotation(), **kwargs)
            )

    if config_wrapper.extra == 'allow':
        use_var_kw = True

    if var_kw and use_var_kw:
        # Make sure the parameter for extra kwargs
        # does not have the same name as a field
        default_model_signature = [
            ('self', Parameter.POSITIONAL_ONLY),
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
        merged_params[var_kw_name] = parameter_post_processor(var_kw.replace(name=var_kw_name))

    return Signature(parameters=list(merged_params.values()), return_annotation=None)
