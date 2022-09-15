"""
Logic related to validators applied to models etc. via the `@validator` and `@root_validator` decorators.
"""
from __future__ import annotations as _annotations

from itertools import chain
from typing import Any, Callable

from typing_extensions import Literal

from ..errors import ConfigError

__all__ = 'FIELD_VALIDATOR_TAG', 'ROOT_VALIDATOR_TAG', 'Validator', 'ValidationFunctions'
FIELD_VALIDATOR_TAG = '__field_validator__'
ROOT_VALIDATOR_TAG = '__root_validator__'


class Validator:
    __slots__ = 'function', 'mode', 'sub_path', 'check_fields'

    def __init__(
        self,
        function: Callable[..., Any],
        mode: Literal['before', 'after', 'wrap', 'plain'],
        sub_path: tuple[str | int, ...] | None = None,
        check_fields: bool | None = None,
    ):
        self.function = function
        self.mode = mode
        self.sub_path = sub_path
        self.check_fields = check_fields


class ValidationFunctions:
    __slots__ = '_field_validators', '_all_fields_validators', 'root_validators', '_used_validators'

    def __init__(self) -> None:
        self._field_validators: dict[str, list[Validator]] = {}
        self._all_fields_validators: list[Validator] = []
        self.root_validators: list[Validator] = []
        self._used_validators: set[str] = set()

    def inherit(self, parent: ValidationFunctions) -> None:
        """
        Inherit validators from another ValidationFunctions instance in a parent class.

        Parent validators are prepended so that they will be called first.
        """
        for k, v in parent._field_validators.items():
            existing = self._field_validators.get(k)
            if existing:
                self._field_validators[k] = existing + v
            self._field_validators[k] = v[:]
        self._all_fields_validators = parent._all_fields_validators[:] + self._all_fields_validators
        self.root_validators = parent.root_validators[:] + self.root_validators

    def extract_validator(self, value: Any) -> bool:
        f_validator: tuple[tuple[str, ...], Validator] | None = getattr(value, FIELD_VALIDATOR_TAG, None)
        if f_validator:
            fields, validator = f_validator
            for field_name in fields:
                this_field_validators = self._field_validators.get(field_name)
                if this_field_validators:
                    this_field_validators.append(validator)
                else:
                    self._field_validators[field_name] = [validator]
            return True

        r_validator: Validator | None = getattr(value, ROOT_VALIDATOR_TAG, None)
        if f_validator:
            self.root_validators.append(r_validator)
            return True
        else:
            return False

    def get_field_validators(self, name: str) -> list[Validator]:
        """
        Get all validators for a given field name.
        """
        self._used_validators.add(name)
        validators = self._field_validators.get(name, [])
        validators += self._all_fields_validators
        return validators

    def check_for_unused(self) -> None:
        unused_validators = set(
            chain.from_iterable(
                (v.function.__name__ for v in self._field_validators[f] if v.check_fields)
                for f in (self._field_validators.keys() - self._used_validators)
            )
        )
        if unused_validators:
            fn = ', '.join(unused_validators)
            raise ConfigError(
                f"Validators defined with incorrect fields: {fn} "  # noqa: Q000
                f"(use check_fields=False if you're inheriting from the model and intended this)"
            )
