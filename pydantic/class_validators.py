from __future__ import annotations as _annotations

import warnings
from collections import ChainMap
from types import FunctionType
from typing import TYPE_CHECKING, Callable, Dict, Optional, Set, Union, overload

from typing_extensions import Literal

from ._internal.valdation_functions import FIELD_VALIDATOR_TAG, ROOT_VALIDATOR_TAG, Validator
from .errors import ConfigError
from .utils import in_ipython

if TYPE_CHECKING:
    from ._internal.typing_extra import AnyCallable, AnyClassMethod
    from .types import ModelOrDc


_FUNCS: Set[str] = set()


def validator(
    *fields: str,
    mode: Literal['before', 'after', 'wrap', 'plain'] = 'after',
    check_fields: bool | None = None,
    sub_path: tuple[str | int, ...] | None = None,
    allow_reuse: bool = False,
) -> Callable[[AnyCallable], AnyClassMethod]:
    """
    Decorate methods on the class indicating that they should be used to validate fields
    :param fields: which field(s) the method should be called on
    :param mode: TODO
    :param sub_path: TODO
    :param check_fields: whether to check that the fields actually exist on the model
    :param allow_reuse: whether to track and raise an error if another validator refers to the decorated function
    """
    if not fields:
        raise ConfigError('validator with no fields specified')
    elif isinstance(fields[0], FunctionType):
        raise ConfigError(
            "validators should be used with fields and keyword arguments, not bare. "  # noqa: Q000
            "E.g. usage should be `@validator('<field_name>', ...)`"
        )
    elif not all(isinstance(field, str) for field in fields):
        raise ConfigError(
            "validator fields should be passed as separate string args. "  # noqa: Q000
            "E.g. usage should be `@validator('<field_name_1>', '<field_name_2>', ...)`"
        )

    def dec(f: AnyCallable) -> AnyClassMethod:
        f_cls = _prepare_validator(f, allow_reuse)
        setattr(
            f_cls,
            FIELD_VALIDATOR_TAG,
            (
                fields,
                Validator(mode=mode, sub_path=sub_path, check_fields=check_fields),
            ),
        )
        return f_cls

    return dec


@overload
def root_validator(__func: AnyCallable) -> AnyClassMethod:
    ...


@overload
def root_validator(
    *,
    mode: Literal['before', 'after', 'wrap', 'plain'] = 'after',
    allow_reuse: bool = False,
) -> Callable[[AnyCallable], AnyClassMethod]:
    ...


def root_validator(
    __func: Optional[AnyCallable] = None,
    *,
    mode: Literal['before', 'after', 'wrap', 'plain'] = 'after',
    allow_reuse: bool = False,
) -> Union[AnyClassMethod, Callable[[AnyCallable], AnyClassMethod]]:
    """
    Decorate methods on a model indicating that they should be used to validate (and perhaps modify) data either
    before or after standard model parsing/validation is performed.
    """
    if __func:
        f_cls = _prepare_validator(__func, allow_reuse)
        setattr(f_cls, ROOT_VALIDATOR_TAG, Validator(mode=mode))
        return f_cls

    def dec(f: AnyCallable) -> AnyClassMethod:
        f_cls = _prepare_validator(f, allow_reuse)
        setattr(f_cls, ROOT_VALIDATOR_TAG, Validator(mode=mode))
        return f_cls

    return dec


def _prepare_validator(function: AnyCallable, allow_reuse: bool) -> AnyClassMethod:
    """
    Warn about validators with duplicated names since without this, validators can be overwritten silently
    which generally isn't the intended behaviour, don't run in ipython (see #312) or if `allow_reuse` is True.
    """
    f_cls = function if isinstance(function, classmethod) else classmethod(function)
    if not allow_reuse and not in_ipython():
        ref = f'{f_cls.__func__.__module__}::{f_cls.__func__.__qualname__}'
        if ref in _FUNCS:
            warnings.warn(f'duplicate validator function "{ref}"; if this is intended, set `allow_reuse=True`')
        _FUNCS.add(ref)
    return f_cls


def gather_all_validators(type_: 'ModelOrDc') -> Dict[str, AnyClassMethod]:
    all_attributes = ChainMap(*[cls.__dict__ for cls in type_.__mro__])  # type: ignore[arg-type,var-annotated]
    return {
        k: v for k, v in all_attributes.items() if hasattr(v, FIELD_VALIDATOR_TAG) or hasattr(v, ROOT_VALIDATOR_TAG)
    }
