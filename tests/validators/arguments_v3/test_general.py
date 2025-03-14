import pytest

from pydantic_core import ArgsKwargs, SchemaValidator, ValidationError
from pydantic_core import core_schema as cs

from ...conftest import Err, PyAndJson, plain_repr


@pytest.mark.parametrize(
    ['input_value', 'expected'],
    (
        [ArgsKwargs(()), ((), {})],
        [{}, ((), {})],
        [ArgsKwargs((1,)), Err('', [{'type': 'unexpected_positional_argument'}])],
        [ArgsKwargs((), {'a': 1}), Err('', [{'type': 'unexpected_keyword_argument'}])],
    ),
)
def test_no_args(py_and_json: PyAndJson, input_value, expected) -> None:
    v = py_and_json(cs.arguments_v3_schema([]))

    if isinstance(expected, Err):
        with pytest.raises(ValidationError) as exc_info:
            v.validate_test(input_value)

        error = exc_info.value.errors()[0]

        assert error['type'] == expected.errors[0]['type']
    else:
        assert v.validate_test(input_value) == expected


@pytest.mark.parametrize(
    ['input_value', 'expected'],
    [
        [ArgsKwargs((1, 2)), ((1, 2), {})],
        [ArgsKwargs((1,)), ((1,), {'b': 42})],
        [ArgsKwargs((1,), {'b': 3}), ((1,), {'b': 3})],
        [ArgsKwargs((), {'a': 1}), ((), {'a': 1, 'b': 42})],
        [{'a': 1, 'b': 2}, ((1, 2), {})],
        [{'a': 1}, ((1, 42), {})],
    ],
    ids=repr,
)
def test_default_factory(py_and_json: PyAndJson, input_value, expected) -> None:
    v = py_and_json(
        cs.arguments_v3_schema(
            [
                cs.arguments_v3_parameter(name='a', schema=cs.int_schema(), mode='positional_or_keyword'),
                cs.arguments_v3_parameter(
                    name='b',
                    schema=cs.with_default_schema(schema=cs.int_schema(), default_factory=lambda: 42),
                    mode='positional_or_keyword',
                ),
            ]
        )
    )

    assert v.validate_test(input_value) == expected


def double_or_bust(input_value):
    if input_value == 1:
        raise RuntimeError('bust')
    return input_value * 2


def test_internal_error(py_and_json: PyAndJson) -> None:
    v = py_and_json(
        cs.arguments_v3_schema(
            [
                cs.arguments_v3_parameter(name='a', schema=cs.int_schema(), mode='positional_only'),
                cs.arguments_v3_parameter(
                    name='b', schema=cs.no_info_plain_validator_function(double_or_bust), mode='positional_only'
                ),
            ]
        )
    )

    assert v.validate_test(ArgsKwargs((1, 2))) == ((1, 4), {})
    with pytest.raises(RuntimeError, match='bust'):
        v.validate_test(ArgsKwargs((1, 1)))


def test_repr() -> None:
    v = SchemaValidator(
        cs.arguments_v3_schema(
            [
                cs.arguments_v3_parameter(name='a', schema=cs.int_schema(), mode='positional_or_keyword'),
                cs.arguments_v3_parameter(
                    name='b',
                    schema=cs.with_default_schema(schema=cs.int_schema(), default_factory=lambda: 42),
                    mode='keyword_only',
                ),
            ]
        )
    )
    assert 'positional_params_count:1,' in plain_repr(v)


@pytest.mark.parametrize(
    ['input_value', 'expected'],
    (
        [ArgsKwargs((1, 't', 2, 3, 4), {'c': True, 'other': 1}), ((1, 't', 2, 3, 4), {'c': True, 'other': 1})],
        [
            {'aa': 1, 'b': 't', 'args': [2, 3, 4], 'c': True, 'kwargs': {'other': 1}},
            ((1, 't', 2, 3, 4), {'c': True, 'other': 1}),
        ],
    ),
)
def test_full(py_and_json: PyAndJson, input_value, expected) -> None:
    """Test inputs against all parameter types:

    ```python
    def func(a: Annotated[int, Field(alias='aa')], /, b: str, *args: int, c: bool, **kwargs: int):
        ...
    ```
    """

    v = py_and_json(
        cs.arguments_v3_schema(
            [
                cs.arguments_v3_parameter(name='a', schema=cs.int_schema(), alias='aa', mode='positional_only'),
                cs.arguments_v3_parameter(name='b', schema=cs.str_schema(), mode='positional_or_keyword'),
                cs.arguments_v3_parameter(name='args', schema=cs.int_schema(), mode='var_args'),
                cs.arguments_v3_parameter(name='c', schema=cs.bool_schema(), mode='keyword_only'),
                cs.arguments_v3_parameter(name='kwargs', schema=cs.int_schema(), mode='var_kwargs_uniform'),
            ]
        )
    )

    assert v.validate_test(input_value) == expected
