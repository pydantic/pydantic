"""
Logic related to validators applied to models etc. via the `@validator` and `@root_validator` decorators.
"""
from __future__ import annotations as _annotations

import warnings
from typing import TYPE_CHECKING, Any, Callable

from ..errors import PydanticUserError

if TYPE_CHECKING:
    from typing_extensions import Literal

    from ..main import BaseModel

__all__ = 'FIELD_VALIDATOR_TAG', 'ROOT_VALIDATOR_TAG', 'Validator', 'ValidationFunctions', 'prepare_validator'
FIELD_VALIDATOR_TAG = '_field_validator'
ROOT_VALIDATOR_TAG = '_root_validator'


class Validator:
    """
    Store information about field and root validators.
    """

    __slots__ = 'function', 'mode', 'sub_path', 'check_fields'

    def __init__(
        self,
        *,
        mode: Literal['before', 'after', 'wrap', 'plain'],
        sub_path: tuple[str | int, ...] | None = None,
        check_fields: bool | None = None,
    ):
        # function is set later after the class is created and functions are bound
        self.function: Callable[..., Any] | None = None
        self.mode = mode
        self.sub_path = sub_path
        self.check_fields = check_fields


class ValidationFunctions:
    __slots__ = (
        '_validators',
        '_field_validators',
        '_direct_field_validators',
        '_all_fields_validators',
        '_root_validators',
        '_used_validators',
    )

    def __init__(self, bases: tuple[type[Any], ...]) -> None:
        self._validators: dict[str, Validator] = {}
        self._field_validators: dict[str, list[str]] = {}
        self._direct_field_validators: set[str] = set()
        self._all_fields_validators: list[str] = []
        self._root_validators: list[str] = []
        self._used_validators: set[str] = set()
        self._inherit(bases)

    def extract_validator(self, name: str, value: Any) -> None:
        """
        If the value is a field or root validator, add it to the appropriate group of validators.

        Note at this point the function is not bound to the class,
        we have to set functions later in `set_bound_functions`.
        """
        f_validator: tuple[tuple[str, ...], Validator] | None = getattr(value, FIELD_VALIDATOR_TAG, None)
        if f_validator:
            fields, validator = f_validator
            self._validators[name] = validator
            for field_name in fields:
                this_field_validators = self._field_validators.get(field_name)
                if this_field_validators:
                    this_field_validators.append(name)
                else:
                    self._field_validators[field_name] = [name]
        else:
            r_validator: Validator | None = getattr(value, ROOT_VALIDATOR_TAG, None)
            if r_validator:
                self._validators[name] = r_validator
                self._root_validators.append(name)

    def set_bound_functions(self, cls: type[BaseModel]) -> None:
        """
        Set functions in self._validators, now that the class is created and functions are bound.
        """
        for name, validator in self._validators.items():
            validator.function = getattr(cls, name)

    def get_root_validators(self) -> list[Validator]:
        return [self._validators[name] for name in self._root_validators]

    def get_field_validators(self, name: str) -> list[Validator]:
        """
        Get all validators for a given field name.
        """
        self._used_validators.add(name)
        validators_names = self._field_validators.get(name, [])
        validators_names += self._all_fields_validators
        return [self._validators[name] for name in validators_names]

    def check_for_unused(self) -> None:
        unused_validator_keys = self._validators.keys() - self._used_validators - set(self._root_validators)
        unused_validators = [name for name in unused_validator_keys if self._validators[name].check_fields]
        if unused_validators:
            fn = ', '.join(unused_validators)
            raise PydanticUserError(
                f"Validators defined with incorrect fields: {fn} "  # noqa: Q000
                f"(use check_fields=False if you're inheriting from the model and intended this)"
            )

    def _inherit(self, bases: tuple[type[Any], ...]) -> None:
        """
        Inherit validators from `ValidationFunctions` instances on base classes.

        Validators from the closest base should be called last, and the greatest-(grand)parent first - to roughly
        match their definition order in code.
        """
        for base in reversed(bases):
            parent_vf: ValidationFunctions | None = getattr(base, '__pydantic_validator_functions__', None)
            if parent_vf:
                self._validators.update(parent_vf._validators)
                for k, v in parent_vf._field_validators.items():
                    existing = self._field_validators.get(k)
                    if existing:
                        existing.extend(v)
                    self._field_validators[k] = v[:]
                self._all_fields_validators.extend(parent_vf._all_fields_validators)
                self._root_validators.extend(parent_vf._root_validators)


_FUNCS: set[str] = set()


def prepare_validator(function: Callable[..., Any], allow_reuse: bool) -> classmethod[Any]:
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


def in_ipython() -> bool:
    """
    Check whether we're in an ipython environment, including jupyter notebooks.
    """
    try:
        eval('__IPYTHON__')
    except NameError:
        return False
    else:  # pragma: no cover
        return True
