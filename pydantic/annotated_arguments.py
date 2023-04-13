from __future__ import annotations

from pydantic_core import core_schema as _core_schema
from typing_extensions import Literal

from ._internal._internal_dataclass import slots_dataclass


@slots_dataclass
class AfterValidator:
    func: _core_schema.NoInfoValidatorFunction | _core_schema.GeneralValidatorFunction


@slots_dataclass
class BeforeValidator:
    func: _core_schema.NoInfoValidatorFunction | _core_schema.GeneralValidatorFunction


@slots_dataclass
class PlainValidator:
    func: _core_schema.NoInfoValidatorFunction | _core_schema.GeneralValidatorFunction


@slots_dataclass
class WrapValidator:
    func: _core_schema.GeneralWrapValidatorFunction | _core_schema.FieldWrapValidatorFunction


@slots_dataclass
class PlainSerializer:
    func: _core_schema.SerializerFunction
    json_return_type: _core_schema.JsonReturnTypes | None = None
    when_used: Literal['always', 'unless-none', 'json', 'json-unless-none'] = 'always'


@slots_dataclass
class WrapSerializer:
    func: _core_schema.WrapSerializerFunction
    json_return_type: _core_schema.JsonReturnTypes | None = None
    when_used: Literal['always', 'unless-none', 'json', 'json-unless-none'] = 'always'
