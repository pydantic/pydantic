"""
Logic for V1 validators, e.g. `@validator` and `@root_validator`.
"""
from __future__ import annotations as _annotations

from inspect import Parameter, signature
from typing import Any, Dict, Set, Tuple, Union, cast

from pydantic_core import core_schema
from typing_extensions import Protocol

from ..errors import PydanticUserError
from ._decorators import can_be_positional


class V1OnlyValueValidator(Protocol):
    """
    A simple validator, supported for V1 validators and V2 validators
    """

    def __call__(self, __value: Any) -> Any:
        ...


class V1ValidatorWithValues(Protocol):
    def __call__(self, __value: Any, values: dict[str, Any]) -> Any:
        ...


class V1ValidatorWithValuesKwOnly(Protocol):
    def __call__(self, __value: Any, *, values: dict[str, Any]) -> Any:
        ...


class V1ValidatorWithKwargs(Protocol):
    def __call__(self, __value: Any, **kwargs: Any) -> Any:
        ...


class V1ValidatorWithValuesAndKwargs(Protocol):
    def __call__(self, __value: Any, values: dict[str, Any], **kwargs: Any) -> Any:
        ...


V1Validator = Union[
    V1ValidatorWithValues, V1ValidatorWithValuesKwOnly, V1ValidatorWithKwargs, V1ValidatorWithValuesAndKwargs
]


def can_be_keyword(param: Parameter) -> bool:
    return param.kind in (Parameter.POSITIONAL_OR_KEYWORD, Parameter.KEYWORD_ONLY)


def make_generic_v1_field_validator(validator: V1Validator) -> core_schema.FieldValidatorFunction:
    sig = signature(validator)

    needs_values_kw = False

    for param_num, (param_name, parameter) in enumerate(sig.parameters.items()):
        if can_be_keyword(parameter) and param_name in ('field', 'config'):
            raise PydanticUserError(
                'The `field` and `config` parameters are not available in Pydantic V2, '
                'please use the `info` parameter instead.',
                code='validator-field-config-info',
            )
        if parameter.kind is Parameter.VAR_KEYWORD:
            needs_values_kw = True
        elif can_be_keyword(parameter) and param_name == 'values':
            needs_values_kw = True
        elif can_be_positional(parameter) and param_num == 0:
            # value
            continue
        elif parameter.default is Parameter.empty:  # ignore params with defaults e.g. bound by functools.partial
            raise PydanticUserError(
                f'Unsupported signature for V1 style validator {validator}: {sig} is not supported.',
                code='validator-v1-signature',
            )

    if needs_values_kw:
        # (v, **kwargs), (v, values, **kwargs), (v, *, values, **kwargs) or (v, *, values)
        val1 = cast(V1ValidatorWithValues, validator)

        def wrapper1(value: Any, info: core_schema.FieldValidationInfo) -> Any:
            return val1(value, values=info.data)

        return wrapper1
    else:
        val2 = cast(V1OnlyValueValidator, validator)

        def wrapper2(value: Any, _: core_schema.FieldValidationInfo) -> Any:
            return val2(value)

        return wrapper2


RootValidatorValues = Dict[str, Any]
RootValidatorFieldsSet = Set[str]
RootValidatorValuesAndFieldsSet = Tuple[RootValidatorValues, RootValidatorFieldsSet]


class V1RootValidatorFunction(Protocol):
    def __call__(self, __values: RootValidatorValues) -> RootValidatorValues:
        ...


class V2CoreBeforeRootValidator(Protocol):
    def __call__(self, __values: RootValidatorValues, __info: core_schema.ValidationInfo) -> RootValidatorValues:
        ...


class V2CoreAfterRootValidator(Protocol):
    def __call__(
        self, __values_and_fields_set: RootValidatorValuesAndFieldsSet, __info: core_schema.ValidationInfo
    ) -> RootValidatorValuesAndFieldsSet:
        ...


def make_v1_generic_root_validator(
    validator: V1RootValidatorFunction, pre: bool
) -> V2CoreBeforeRootValidator | V2CoreAfterRootValidator:
    """
    Wrap a V1 style root validator for V2 compatibility
    """
    if pre is True:
        # mode='before' for pydantic-core
        def _wrapper1(values: RootValidatorValues, _: core_schema.ValidationInfo) -> RootValidatorValues:
            return validator(values)

        return _wrapper1

    # mode='after' for pydantic-core
    def _wrapper2(
        values_and_fields_set: tuple[RootValidatorValues, RootValidatorFieldsSet], _: core_schema.ValidationInfo
    ) -> tuple[RootValidatorValues, RootValidatorFieldsSet]:
        values, fields_set = values_and_fields_set
        values = validator(values)
        return values, fields_set

    return _wrapper2
