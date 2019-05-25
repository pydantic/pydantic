from copy import deepcopy
from enum import Enum
from typing import TYPE_CHECKING, Any, Dict, Optional, Set, Tuple, Type, Union

from .error_wrappers import ErrorWrapper, ValidationError
from .errors import ConfigError, ExtraError, MissingError
from .utils import ForwardRef

if TYPE_CHECKING:  # pragma: no cover
    from .types import ModelOrDc
    from .main import BaseModel  # noqa: F401

    DictStrAny = Dict[str, Any]
    SetStr = Set[str]


__all__ = ['Extra', 'compiled', 'parse_model']


try:
    import cython  # type: ignore
except ImportError:
    compiled: bool = False
else:
    compiled = cython.compiled


class Extra(str, Enum):
    allow = 'allow'
    ignore = 'ignore'
    forbid = 'forbid'


_missing = object()


def parse_model(  # noqa: C901 (ignore complexity)
    model: Union['BaseModel', Type['BaseModel']],
    input_data: 'DictStrAny',
    raise_exc: bool = True,
    cls: 'ModelOrDc' = None,
) -> Tuple['DictStrAny', 'SetStr', Optional[ValidationError]]:
    """
    validate data against a model.
    """
    values = {}
    errors = []
    # input_data names, possibly alias
    names_used = set()
    # field names, never aliases
    fields_set = set()
    config = model.__config__
    check_extra = config.extra is not Extra.ignore

    for name, field in model.__fields__.items():
        if type(field.type_) == ForwardRef:
            raise ConfigError(
                f'field "{field.name}" not yet prepared so type is still a ForwardRef, '
                f'you might need to call {model.__class__.__name__}.update_forward_refs().'
            )

        value = input_data.get(field.alias, _missing)
        using_name = False
        if value is _missing and config.allow_population_by_alias and field.alt_alias:
            value = input_data.get(field.name, _missing)
            using_name = True

        if value is _missing:
            if field.required:
                errors.append(ErrorWrapper(MissingError(), loc=field.alias, config=model.__config__))
                continue
            value = deepcopy(field.default)
            if not model.__config__.validate_all and not field.validate_always:
                values[name] = value
                continue
        else:
            fields_set.add(name)
            if check_extra:
                names_used.add(field.name if using_name else field.alias)

        v_, errors_ = field.validate(value, values, loc=field.alias, cls=cls or model.__class__)  # type: ignore
        if isinstance(errors_, ErrorWrapper):
            errors.append(errors_)
        elif isinstance(errors_, list):
            errors.extend(errors_)
        else:
            values[name] = v_

    if check_extra:
        extra = input_data.keys() - names_used
        if extra:
            fields_set |= extra
            if config.extra is Extra.allow:
                for f in extra:
                    values[f] = input_data[f]
            else:
                for f in sorted(extra):
                    errors.append(ErrorWrapper(ExtraError(), loc=f, config=config))

    if not raise_exc:
        return values, fields_set, ValidationError(errors) if errors else None

    if errors:
        raise ValidationError(errors)
    return values, fields_set, None
