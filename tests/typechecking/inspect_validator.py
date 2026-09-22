"""Typing coverage for `inspect_validator` as a strict type guard."""

from pydantic_core.core_schema import (
    NoInfoValidatorFunction,
    NoInfoWrapValidatorFunction,
    WithInfoValidatorFunction,
    WithInfoWrapValidatorFunction,
)
from typing_extensions import assert_type

from pydantic._internal._decorators import inspect_validator


def check_plain(func: NoInfoValidatorFunction | WithInfoValidatorFunction) -> None:
    if inspect_validator(func, mode='plain', type='field'):
        assert_type(func, WithInfoValidatorFunction)


def check_wrap(func: NoInfoWrapValidatorFunction | WithInfoWrapValidatorFunction) -> None:
    if inspect_validator(func, mode='wrap', type='model'):
        assert_type(func, WithInfoWrapValidatorFunction)
