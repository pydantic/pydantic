import dataclasses
import re
from datetime import date, datetime

import pytest

from pydantic_core import SchemaValidator, ValidationError, core_schema

from .conftest import Err


def test_bool():
    v = SchemaValidator(core_schema.bool_schema())

    assert v.validate_strings('true') is True
    assert v.validate_strings('true', strict=True) is True
    assert v.validate_strings('false') is False


@pytest.mark.parametrize(
    'schema,input_value,expected,strict',
    [
        (core_schema.int_schema(), '1', 1, False),
        (core_schema.int_schema(), '1', 1, True),
        (core_schema.int_schema(), 'xxx', Err('type=int_parsing'), True),
        (core_schema.float_schema(), '1.1', 1.1, False),
        (core_schema.float_schema(), '1.10', 1.1, False),
        (core_schema.float_schema(), '1.1', 1.1, True),
        (core_schema.float_schema(), '1.10', 1.1, True),
        (core_schema.date_schema(), '2017-01-01', date(2017, 1, 1), False),
        (core_schema.date_schema(), '2017-01-01', date(2017, 1, 1), True),
        (core_schema.datetime_schema(), '2017-01-01T12:13:14.567', datetime(2017, 1, 1, 12, 13, 14, 567_000), False),
        (core_schema.datetime_schema(), '2017-01-01T12:13:14.567', datetime(2017, 1, 1, 12, 13, 14, 567_000), True),
        (core_schema.date_schema(), '2017-01-01T12:13:14.567', Err('type=date_from_datetime_inexact'), False),
        (core_schema.date_schema(), '2017-01-01T12:13:14.567', Err('type=date_parsing'), True),
        (core_schema.date_schema(), '2017-01-01T00:00:00', date(2017, 1, 1), False),
        (core_schema.date_schema(), '2017-01-01T00:00:00', Err('type=date_parsing'), True),
    ],
    ids=repr,
)
def test_validate_strings(schema, input_value, expected, strict):
    v = SchemaValidator(schema)
    if isinstance(expected, Err):
        with pytest.raises(ValidationError, match=re.escape(expected.message)):
            v.validate_strings(input_value, strict=strict)
    else:
        assert v.validate_strings(input_value, strict=strict) == expected


def test_dict():
    v = SchemaValidator(core_schema.dict_schema(core_schema.int_schema(), core_schema.date_schema()))

    assert v.validate_strings({'1': '2017-01-01', '2': '2017-01-02'}) == {1: date(2017, 1, 1), 2: date(2017, 1, 2)}
    assert v.validate_strings({'1': '2017-01-01', '2': '2017-01-02'}, strict=True) == {
        1: date(2017, 1, 1),
        2: date(2017, 1, 2),
    }


def test_model():
    class MyModel:
        # this is not required, but it avoids `__pydantic_fields_set__` being included in `__dict__`
        __slots__ = '__dict__', '__pydantic_fields_set__', '__pydantic_extra__', '__pydantic_private__'
        field_a: int
        field_b: date

    v = SchemaValidator(
        core_schema.model_schema(
            MyModel,
            core_schema.model_fields_schema(
                {
                    'field_a': core_schema.model_field(core_schema.int_schema()),
                    'field_b': core_schema.model_field(core_schema.date_schema()),
                }
            ),
        )
    )
    m2 = v.validate_strings({'field_a': '1', 'field_b': '2017-01-01'})
    assert m2.__dict__ == {'field_a': 1, 'field_b': date(2017, 1, 1)}
    m2 = v.validate_strings({'field_a': '1', 'field_b': '2017-01-01'}, strict=True)
    assert m2.__dict__ == {'field_a': 1, 'field_b': date(2017, 1, 1)}


def test_dataclass():
    @dataclasses.dataclass
    class MyDataClass:
        field_a: int
        field_b: date

    v = SchemaValidator(
        core_schema.dataclass_schema(
            MyDataClass,
            core_schema.dataclass_args_schema(
                'MyDataClass',
                [
                    core_schema.dataclass_field('field_a', core_schema.int_schema()),
                    core_schema.dataclass_field('field_b', core_schema.date_schema()),
                ],
            ),
            ['field_a', 'field_b'],
        )
    )
    m2 = v.validate_strings({'field_a': '1', 'field_b': '2017-01-01'})
    assert m2.__dict__ == {'field_a': 1, 'field_b': date(2017, 1, 1)}
    m2 = v.validate_strings({'field_a': '1', 'field_b': '2017-01-01'}, strict=True)
    assert m2.__dict__ == {'field_a': 1, 'field_b': date(2017, 1, 1)}


def test_typed_dict():
    v = SchemaValidator(
        core_schema.typed_dict_schema(
            {
                'field_a': core_schema.typed_dict_field(core_schema.int_schema()),
                'field_b': core_schema.typed_dict_field(core_schema.date_schema()),
            }
        )
    )
    m2 = v.validate_strings({'field_a': '1', 'field_b': '2017-01-01'})
    assert m2 == {'field_a': 1, 'field_b': date(2017, 1, 1)}
    m2 = v.validate_strings({'field_a': '1', 'field_b': '2017-01-01'}, strict=True)
    assert m2 == {'field_a': 1, 'field_b': date(2017, 1, 1)}
