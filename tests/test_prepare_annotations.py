from dataclasses import dataclass
from typing import Any, Iterable, List, Tuple

import dirty_equals as de
import pytest
from annotated_types import Gt, Lt
from pydantic_core import CoreSchema, core_schema
from typing_extensions import Annotated

from pydantic import (
    AllowInfNan,
    BaseModel,
    ConfigDict,
    GetCoreSchemaHandler,
    GetJsonSchemaHandler,
    TypeAdapter,
    ValidationError,
)
from pydantic.functional_validators import AfterValidator
from pydantic.json_schema import JsonSchemaValue


def test_prepare_annotations_without_get_core_schema() -> None:
    class Foo:
        @classmethod
        def __prepare_pydantic_annotations__(
            cls, src_type: Any, annotations: List[Any], _config_dict: ConfigDict
        ) -> Tuple[Any, List[Any]]:
            return int, annotations

    ta = TypeAdapter(Foo)
    assert ta.validate_json('1') == 1


@dataclass
class MetadataApplier:
    inner_core_schema: CoreSchema
    outer_core_schema: CoreSchema

    def __get_pydantic_core_schema__(self, _source_type: Any, _handler: GetCoreSchemaHandler) -> CoreSchema:
        return self.outer_core_schema

    def __get_pydantic_json_schema__(self, _schema: CoreSchema, handler: GetJsonSchemaHandler) -> JsonSchemaValue:
        return handler(self.inner_core_schema)


class MyDecimal(float):
    """
    An example of what a user would need to do if they wanted to implement something that
    behaves like Decimal (aside from the fact that we special case Decimal).
    """

    @classmethod
    def __prepare_pydantic_annotations__(
        cls, source_type: Any, annotations: Tuple[Any, ...], _config_dict: ConfigDict
    ) -> Tuple[Any, Iterable[Any]]:
        assert source_type is MyDecimal
        metadata: dict[str, Any] = {}
        remaining_annotations: list[Any] = []
        for annotation in annotations:
            if isinstance(annotation, Gt):
                metadata['gt'] = annotation.gt
            else:
                remaining_annotations.append(annotation)
        inner_schema = core_schema.float_schema(**metadata)
        outer_schema = core_schema.no_info_after_validator_function(MyDecimal, inner_schema)
        new_annotations = (
            MetadataApplier(inner_core_schema=inner_schema, outer_core_schema=outer_schema),
            *remaining_annotations,
        )
        return source_type, new_annotations


def test_decimal_like_in_annotated() -> None:
    def no_op_val(x: Any) -> Any:
        return x

    a = TypeAdapter(List[Annotated[MyDecimal, Gt(10), AfterValidator(no_op_val)]])

    expected = de.IsPartialDict(
        core_schema.list_schema(
            de.IsPartialDict(
                core_schema.no_info_after_validator_function(
                    no_op_val,
                    de.IsPartialDict(
                        core_schema.no_info_after_validator_function(
                            MyDecimal, de.IsPartialDict(core_schema.float_schema(gt=10))
                        )
                    ),
                )
            )
        )
    )

    assert a.core_schema == expected


def test_decimal_like_outside_of_annotated() -> None:
    a = TypeAdapter(List[MyDecimal])

    expected = de.IsPartialDict(
        core_schema.list_schema(
            de.IsPartialDict(
                core_schema.no_info_after_validator_function(MyDecimal, de.IsPartialDict(core_schema.float_schema()))
            )
        )
    )

    assert a.core_schema == expected


def test_generator_custom_type() -> None:
    class MyType(int):
        @classmethod
        def __prepare_pydantic_annotations__(
            cls, _source_type: Any, annotations: Tuple[Any, ...], _config: ConfigDict
        ) -> Tuple[Any, Iterable[Any]]:
            return int, (Gt(123), *annotations)

    a = TypeAdapter(MyType)
    assert a.core_schema == de.IsPartialDict(core_schema.int_schema(gt=123))

    a = TypeAdapter(Annotated[MyType, Lt(420)])
    assert a.core_schema == de.IsPartialDict(core_schema.int_schema(gt=123, lt=420))


roman_numbers = {
    'I': 1,
    'II': 2,
    'III': 3,
    'IV': 4,
    'V': 5,
    'VI': 6,
    'VII': 7,
    'VIII': 8,
    'IX': 9,
    'X': 10,
}
roman_numbers_lookup = {v: k for k, v in roman_numbers.items()}


class Roman:
    def __init__(self, value: int, *, allow_nan: bool = False) -> None:
        try:
            self.numeral = roman_numbers_lookup[value]
        except KeyError:
            if allow_nan:
                self.numeral = 'NAN'
            else:
                raise ValueError('not a roman numeral')

    @classmethod
    def from_str(cls, value: str, *, allow_nan: bool = False) -> 'Roman':
        if value == 'NAN':
            return cls(0, allow_nan=allow_nan)

        try:
            value = roman_numbers[value]
        except KeyError:
            raise ValueError('invalid input')
        else:
            return cls(value)

    @property
    def int(self) -> int:
        try:
            return roman_numbers[self.numeral]
        except KeyError:
            raise ValueError('not a numeral')

    def __add__(self, other):
        return Roman(self.int + other.int)

    def __sub__(self, other):
        return Roman(self.int - other.int)

    def __eq__(self, other):
        if isinstance(other, Roman):
            return self.numeral == other.numeral
        else:
            return False

    def __str__(self):
        return self.numeral

    def __repr__(self):
        return f'Roman({self.numeral})'

    @classmethod
    def __prepare_pydantic_annotations__(
        cls, source_type: Any, annotations: Tuple[Any, ...], config: ConfigDict
    ) -> Tuple[Any, Iterable[Any]]:
        allow_inf_nan = config.get('allow_inf_nan', False)
        for an in annotations:
            if isinstance(an, AllowInfNan):
                allow_inf_nan = an.allow_inf_nan
                break

        return source_type, [RomanValidator(allow_inf_nan)]


@dataclass
class RomanValidator:
    allow_inf_nan: bool

    def __get_pydantic_core_schema__(self, _source_type: Any, _handler: GetCoreSchemaHandler) -> CoreSchema:
        return core_schema.no_info_wrap_validator_function(
            self.validate,
            core_schema.int_schema(),
        )

    def validate(self, input_value: Any, handler: core_schema.ValidatorFunctionWrapHandler) -> Roman:
        if isinstance(input_value, str):
            return Roman.from_str(input_value, allow_nan=self.allow_inf_nan)

        int_value = handler(input_value)
        return Roman(int_value, allow_nan=self.allow_inf_nan)


def test_roman():
    assert Roman.from_str('III') + Roman.from_str('II') == Roman.from_str('V')

    ta = TypeAdapter(Roman)

    assert ta.validate_python(1) == Roman(1)
    assert ta.validate_python('I') == Roman(1)
    assert ta.validate_python('V') == Roman(5)

    with pytest.raises(ValidationError, match='Value error, invalid input'):
        ta.validate_python('wrong')

    with pytest.raises(ValidationError, match='Value error, not a roman numeral'):
        ta.validate_python('NAN')


def test_roman_allow_nan():
    ta = TypeAdapter(Roman, config=ConfigDict(allow_inf_nan=True))

    assert ta.validate_python('I') == Roman(1)
    assert ta.validate_python('V') == Roman(5)
    assert ta.validate_python('NAN') == Roman(0, allow_nan=True)


def test_roman_allow_nannotation():
    class OnConfig(BaseModel, allow_inf_nan=True):
        value: Roman

    assert OnConfig(value='I').value == Roman(1)
    assert OnConfig(value='NAN').value == Roman(0, allow_nan=True)

    class OnAnnotation(BaseModel):
        value: Annotated[Roman, AllowInfNan()]

    assert OnAnnotation(value='I').value == Roman(1)
    assert OnAnnotation(value='NAN').value == Roman(0, allow_nan=True)

    class OverrideOnAnnotation(BaseModel, allow_inf_nan=True):
        value: Annotated[Roman, AllowInfNan(False)]

    assert OverrideOnAnnotation(value='I').value == Roman(1)
    with pytest.raises(ValidationError, match='Value error, not a roman numeral'):
        OverrideOnAnnotation(value='NAN')
