import pytest

from pydantic_core import ArgsKwargs, ValidationError
from pydantic_core import core_schema as cs

from ...conftest import PyAndJson


@pytest.mark.parametrize(
    ['input_value', 'err_type'],
    (
        [ArgsKwargs((), {'a': 1, 'b': 2, 'c': 3}), 'unexpected_keyword_argument'],
        [ArgsKwargs((), {'a': 1, 'c': 3, 'extra': 'value'}), 'unexpected_keyword_argument'],
        [{'a': 1, 'b': 2, 'c': 3}, 'extra_forbidden'],
        [{'a': 1, 'c': 3, 'extra': 'value'}, 'extra_forbidden'],
    ),
)
def test_extra_forbid(py_and_json: PyAndJson, input_value, err_type) -> None:
    v = py_and_json(
        cs.arguments_v3_schema(
            [
                cs.arguments_v3_parameter(name='a', schema=cs.int_schema()),
                cs.arguments_v3_parameter(name='b', schema=cs.int_schema(), alias='c'),
            ],
            extra_behavior='forbid',
        ),
    )

    with pytest.raises(ValidationError) as exc_info:
        v.validate_test(input_value)

    error = exc_info.value.errors()[0]

    assert error['type'] == err_type


@pytest.mark.parametrize(
    'input_value',
    [
        ArgsKwargs((), {'a': 1, 'b': 2, 'c': 3}),
        ArgsKwargs((), {'a': 1, 'c': 3, 'extra': 'value'}),
        {'a': 1, 'b': 2, 'c': 3},
        {'a': 1, 'c': 3, 'extra': 'value'},
    ],
)
def test_extra_ignore(py_and_json: PyAndJson, input_value) -> None:
    v = py_and_json(
        cs.arguments_v3_schema(
            [
                cs.arguments_v3_parameter(name='a', schema=cs.int_schema(), mode='keyword_only'),
                cs.arguments_v3_parameter(name='b', schema=cs.int_schema(), alias='c', mode='keyword_only'),
            ],
            extra_behavior='ignore',
        ),
    )

    assert v.validate_test(input_value) == ((), {'a': 1, 'b': 3})
