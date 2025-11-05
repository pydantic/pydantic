from __future__ import annotations

import re

import pytest

from pydantic_core import ArgsKwargs, SchemaValidator, ValidationError
from pydantic_core import core_schema as cs

from ...conftest import Err, PyAndJson


@pytest.mark.parametrize(
    ['input_value', 'expected'],
    (
        [ArgsKwargs((1,)), ((1,), {})],
        [ArgsKwargs((), {'Foo': 1}), ((), {'a': 1})],
        [ArgsKwargs((), {'a': 1}), Err('Foo\n  Missing required argument [type=missing_argument,')],
        [{'Foo': 1}, ((1,), {})],
        [{'a': 1}, Err('Foo\n  Missing required argument [type=missing_argument,')],
    ),
    ids=repr,
)
def test_alias(py_and_json: PyAndJson, input_value, expected) -> None:
    v = py_and_json(
        cs.arguments_v3_schema(
            [
                cs.arguments_v3_parameter(name='a', schema=cs.int_schema(), alias='Foo', mode='positional_or_keyword'),
            ]
        )
    )
    if isinstance(expected, Err):
        with pytest.raises(ValidationError, match=re.escape(expected.message)):
            v.validate_test(input_value)
    else:
        assert v.validate_test(input_value) == expected


@pytest.mark.parametrize(
    ['input_value', 'expected'],
    (
        [ArgsKwargs((1,)), ((1,), {})],
        [ArgsKwargs((), {'Foo': 1}), ((), {'a': 1})],
        [ArgsKwargs((), {'a': 1}), ((), {'a': 1})],
        [ArgsKwargs((), {'a': 1, 'b': 2}), Err('b\n  Unexpected keyword argument [type=unexpected_keyword_argument,')],
        [
            ArgsKwargs((), {'a': 1, 'Foo': 2}),
            Err('a\n  Unexpected keyword argument [type=unexpected_keyword_argument,'),
        ],
        [{'Foo': 1}, ((1,), {})],
        [{'a': 1}, ((1,), {})],
    ),
    ids=repr,
)
def test_alias_validate_by_name(py_and_json: PyAndJson, input_value, expected):
    v = py_and_json(
        cs.arguments_v3_schema(
            [
                cs.arguments_v3_parameter(name='a', schema=cs.int_schema(), alias='Foo', mode='positional_or_keyword'),
            ],
            validate_by_name=True,
        )
    )
    if isinstance(expected, Err):
        with pytest.raises(ValidationError, match=re.escape(expected.message)):
            v.validate_test(input_value)
    else:
        assert v.validate_test(input_value) == expected


def test_only_validate_by_name(py_and_json) -> None:
    v = py_and_json(
        cs.arguments_v3_schema(
            [
                cs.arguments_v3_parameter(
                    name='a', schema=cs.str_schema(), alias='FieldA', mode='positional_or_keyword'
                ),
            ],
            validate_by_name=True,
            validate_by_alias=False,
        )
    )

    assert v.validate_test(ArgsKwargs((), {'a': 'hello'})) == ((), {'a': 'hello'})
    assert v.validate_test({'a': 'hello'}) == (('hello',), {})

    with pytest.raises(ValidationError, match=r'a\n +Missing required argument \[type=missing_argument,'):
        assert v.validate_test(ArgsKwargs((), {'FieldA': 'hello'}))
    with pytest.raises(ValidationError, match=r'a\n +Missing required argument \[type=missing_argument,'):
        assert v.validate_test({'FieldA': 'hello'})


def test_only_allow_alias(py_and_json) -> None:
    v = py_and_json(
        cs.arguments_v3_schema(
            [
                cs.arguments_v3_parameter(
                    name='a', schema=cs.str_schema(), alias='FieldA', mode='positional_or_keyword'
                ),
            ],
            validate_by_name=False,
            validate_by_alias=True,
        )
    )
    assert v.validate_test(ArgsKwargs((), {'FieldA': 'hello'})) == ((), {'a': 'hello'})
    assert v.validate_test({'FieldA': 'hello'}) == (('hello',), {})

    with pytest.raises(ValidationError, match=r'FieldA\n +Missing required argument \[type=missing_argument,'):
        assert v.validate_test(ArgsKwargs((), {'a': 'hello'}))
    with pytest.raises(ValidationError, match=r'FieldA\n +Missing required argument \[type=missing_argument,'):
        assert v.validate_test({'a': 'hello'})


@pytest.mark.parametrize('config_by_alias', [None, True, False])
@pytest.mark.parametrize('config_by_name', [None, True, False])
@pytest.mark.parametrize('runtime_by_alias', [None, True, False])
@pytest.mark.parametrize('runtime_by_name', [None, True, False])
def test_by_alias_and_name_config_interaction(
    config_by_alias: bool | None,
    config_by_name: bool | None,
    runtime_by_alias: bool | None,
    runtime_by_name: bool | None,
) -> None:
    """This test reflects the priority that applies for config vs runtime validation alias configuration.

    Runtime values take precedence over config values, when set.
    By default, by_alias is True and by_name is False.
    """

    if config_by_alias is False and config_by_name is False and runtime_by_alias is False and runtime_by_name is False:
        pytest.skip("Can't have both by_alias and by_name as effectively False")

    schema = cs.arguments_v3_schema(
        arguments=[
            cs.arguments_v3_parameter(name='my_field', schema=cs.int_schema(), alias='my_alias'),
        ],
        **({'validate_by_alias': config_by_alias} if config_by_alias is not None else {}),
        **({'validate_by_name': config_by_name} if config_by_name is not None else {}),
    )
    s = SchemaValidator(schema)

    alias_allowed = next(x for x in (runtime_by_alias, config_by_alias, True) if x is not None)
    name_allowed = next(x for x in (runtime_by_name, config_by_name, False) if x is not None)

    if alias_allowed:
        assert s.validate_python(
            ArgsKwargs((), {'my_alias': 1}), by_alias=runtime_by_alias, by_name=runtime_by_name
        ) == (
            (),
            {'my_field': 1},
        )
    if name_allowed:
        assert s.validate_python(
            ArgsKwargs((), {'my_field': 1}), by_alias=runtime_by_alias, by_name=runtime_by_name
        ) == (
            (),
            {'my_field': 1},
        )
