import re
from collections import deque
from typing import Any

import pytest

from pydantic_core import SchemaValidator, ValidationError
from pydantic_core import core_schema as cs

from ..conftest import Err, PyAndJson, infinite_generator


@pytest.mark.parametrize(
    'input_value,expected',
    [
        ([], set()),
        ([1, 2, 3], {1, 2, 3}),
        ([1, 2, '3'], {1, 2, 3}),
        ([1, 2, 3, 2, 3], {1, 2, 3}),
        (5, Err('[type=set_type, input_value=5, input_type=int]')),
    ],
)
def test_set_ints_both(py_and_json: PyAndJson, input_value, expected):
    v = py_and_json({'type': 'set', 'items_schema': {'type': 'int'}})
    if isinstance(expected, Err):
        with pytest.raises(ValidationError, match=re.escape(expected.message)):
            v.validate_test(input_value)
    else:
        assert v.validate_test(input_value) == expected


@pytest.mark.parametrize('input_value,expected', [([1, 2.5, '3'], {1, 2.5, '3'})])
def test_set_no_validators_both(py_and_json: PyAndJson, input_value, expected):
    v = py_and_json({'type': 'set'})
    assert v.validate_test(input_value) == expected


@pytest.mark.parametrize(
    'input_value,expected',
    [
        ([1, 2.5, '3'], {1, 2.5, '3'}),
        ('foo', Err('[type=set_type, input_value=foo, input_type=str]')),
        (1, Err('[type=set_type, input_value=1.0, input_type=float]')),
        (1.0, Err('[type=set_type, input_value=1.0, input_type=float]')),
        (False, Err('[type=set_type, input_value=False, input_type=bool]')),
    ],
)
def test_frozenset_no_validators_both(py_and_json: PyAndJson, input_value, expected):
    v = py_and_json({'type': 'set'})
    if isinstance(expected, Err):
        with pytest.raises(ValidationError, match=expected.message):
            v.validate_test(input_value)
    else:
        assert v.validate_test(input_value) == expected


@pytest.mark.parametrize(
    'input_value,expected',
    [
        ({1, 2, 3}, {1, 2, 3}),
        (set(), set()),
        ([1, 2, 3, 2, 3], {1, 2, 3}),
        ([], set()),
        ((1, 2, 3, 2, 3), {1, 2, 3}),
        ((), set()),
        (frozenset([1, 2, 3, 2, 3]), {1, 2, 3}),
        (deque((1, 2, '3')), {1, 2, 3}),
        ({1: 10, 2: 20, '3': '30'}.keys(), {1, 2, 3}),
        ({1: 10, 2: 20, '3': '30'}.values(), {10, 20, 30}),
        ({1: 10, 2: 20, '3': '30'}, Err('Input should be a valid set [type=set_type,')),
        ((x for x in [1, 2, '3']), {1, 2, 3}),
        ({'abc'}, Err('0\n  Input should be a valid integer')),
        ({1: 2}, Err('1 validation error for set[int]\n  Input should be a valid set')),
        ('abc', Err('Input should be a valid set')),
    ],
)
@pytest.mark.thread_unsafe  # generators in parameters not compatible with pytest-run-parallel, https://github.com/Quansight-Labs/pytest-run-parallel/issues/14
def test_set_ints_python(input_value, expected):
    v = SchemaValidator(cs.set_schema(items_schema=cs.int_schema()))
    if isinstance(expected, Err):
        with pytest.raises(ValidationError, match=re.escape(expected.message)):
            v.validate_python(input_value)
    else:
        assert v.validate_python(input_value) == expected


@pytest.mark.parametrize('input_value,expected', [([1, 2.5, '3'], {1, 2.5, '3'}), ([(1, 2), (3, 4)], {(1, 2), (3, 4)})])
def test_set_no_validators_python(input_value, expected):
    v = SchemaValidator(cs.set_schema())
    assert v.validate_python(input_value) == expected


def test_set_multiple_errors():
    v = SchemaValidator(cs.set_schema(items_schema=cs.int_schema()))
    with pytest.raises(ValidationError) as exc_info:
        v.validate_python(['a', (1, 2), []])
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'int_parsing',
            'loc': (0,),
            'msg': 'Input should be a valid integer, unable to parse string as an integer',
            'input': 'a',
        },
        {'type': 'int_type', 'loc': (1,), 'msg': 'Input should be a valid integer', 'input': (1, 2)},
        {'type': 'int_type', 'loc': (2,), 'msg': 'Input should be a valid integer', 'input': []},
    ]


def test_list_with_unhashable_items():
    v = SchemaValidator(cs.set_schema())

    class Unhashable:
        __hash__ = None

    unhashable = Unhashable()

    with pytest.raises(ValidationError) as exc_info:
        v.validate_python([{'a': 'b'}, unhashable])
    assert exc_info.value.errors(include_url=False) == [
        {'type': 'set_item_not_hashable', 'loc': (0,), 'msg': 'Set items should be hashable', 'input': {'a': 'b'}},
        {'type': 'set_item_not_hashable', 'loc': (1,), 'msg': 'Set items should be hashable', 'input': unhashable},
    ]


def generate_repeats():
    for i in 1, 2, 3:
        yield i
        yield i


@pytest.mark.parametrize(
    'kwargs,input_value,expected',
    [
        ({'strict': True}, {1, 2, 3}, {1, 2, 3}),
        ({'strict': True}, set(), set()),
        ({'strict': True}, [1, 2, 3, 2, 3], Err('Input should be a valid set [type=set_type,')),
        ({'strict': True}, [], Err('Input should be a valid set [type=set_type,')),
        ({'strict': True}, (), Err('Input should be a valid set [type=set_type,')),
        ({'strict': True}, (1, 2, 3), Err('Input should be a valid set [type=set_type,')),
        ({'strict': True}, frozenset([1, 2, 3]), Err('Input should be a valid set [type=set_type,')),
        ({'strict': True}, 'abc', Err('Input should be a valid set [type=set_type,')),
        ({'min_length': 3}, {1, 2, 3}, {1, 2, 3}),
        ({'min_length': 3}, {1, 2}, Err('Set should have at least 3 items after validation, not 2 [type=too_short,')),
        (
            {'max_length': 3},
            {1, 2, 3, 4},
            Err('Set should have at most 3 items after validation, not more [type=too_long,'),
        ),
        (
            {'max_length': 3},
            [1, 2, 3, 4],
            Err('Set should have at most 3 items after validation, not more [type=too_long,'),
        ),
        ({'max_length': 3, 'items_schema': {'type': 'int'}}, {1, 2, 3, 4}, Err('type=too_long,')),
        ({'max_length': 3, 'items_schema': {'type': 'int'}}, [1, 2, 3, 4], Err('type=too_long,')),
        # length check after set creation
        ({'max_length': 3}, [1, 1, 2, 2, 3, 3], {1, 2, 3}),
        ({'max_length': 3}, generate_repeats(), {1, 2, 3}),
        (
            {'max_length': 3},
            infinite_generator(),
            Err('Set should have at most 3 items after validation, not more [type=too_long,'),
        ),
    ],
    ids=repr,
)
@pytest.mark.thread_unsafe  # generators in parameters not compatible with pytest-run-parallel, https://github.com/Quansight-Labs/pytest-run-parallel/issues/14
def test_set_kwargs(kwargs: dict[str, Any], input_value, expected):
    v = SchemaValidator(cs.set_schema(**kwargs))
    if isinstance(expected, Err):
        with pytest.raises(ValidationError, match=re.escape(expected.message)):
            r = v.validate_python(input_value)
            print(f'unexpected result: {r!r}')
    else:
        assert v.validate_python(input_value) == expected


@pytest.mark.parametrize('input_value,expected', [({1, 2, 3}, {1, 2, 3}), ([1, 2, 3], [1, 2, 3])])
def test_union_set_list(input_value, expected):
    v = SchemaValidator(cs.union_schema(choices=[cs.set_schema(), cs.list_schema()]))
    if isinstance(expected, Err):
        with pytest.raises(ValidationError, match=re.escape(expected.message)):
            v.validate_python(input_value)
    else:
        assert v.validate_python(input_value) == expected


@pytest.mark.parametrize(
    'input_value,expected',
    [
        ({1, 2, 3}, {1, 2, 3}),
        ({'a', 'b', 'c'}, {'a', 'b', 'c'}),
        (
            [1, 'a'],
            Err(
                '2 validation errors for union',
                errors=[
                    {
                        'type': 'int_type',
                        'loc': ('set[int]', 1),
                        'msg': 'Input should be a valid integer',
                        'input': 'a',
                    },
                    # second because validation on the string choice comes second
                    {
                        'type': 'string_type',
                        'loc': ('set[str]', 0),
                        'msg': 'Input should be a valid string',
                        'input': 1,
                    },
                ],
            ),
        ),
    ],
)
def test_union_set_int_set_str(input_value, expected):
    v = SchemaValidator(
        cs.union_schema(
            choices=[
                cs.set_schema(items_schema=cs.int_schema(strict=True)),
                cs.set_schema(items_schema=cs.str_schema(strict=True)),
            ]
        )
    )
    if isinstance(expected, Err):
        with pytest.raises(ValidationError, match=re.escape(expected.message)) as exc_info:
            v.validate_python(input_value)
        if expected.errors is not None:
            assert exc_info.value.errors(include_url=False) == expected.errors
    else:
        assert v.validate_python(input_value) == expected


def test_set_as_dict_keys(py_and_json: PyAndJson):
    v = py_and_json({'type': 'dict', 'keys_schema': {'type': 'set'}, 'values_schema': {'type': 'int'}})
    with pytest.raises(ValidationError, match=re.escape("[type=set_type, input_value='foo', input_type=str]")):
        v.validate_test({'foo': 'bar'})


def test_generator_error():
    def gen(error: bool):
        yield 1
        yield 2
        if error:
            raise RuntimeError('my error')
        yield 3

    v = SchemaValidator(cs.set_schema(items_schema=cs.int_schema()))
    r = v.validate_python(gen(False))
    assert r == {1, 2, 3}
    assert isinstance(r, set)

    msg = r'Error iterating over object, error: RuntimeError: my error \[type=iteration_error,'
    with pytest.raises(ValidationError, match=msg):
        v.validate_python(gen(True))


@pytest.mark.parametrize(
    'input_value,items_schema,expected',
    [
        pytest.param(
            {1: 10, 2: 20, '3': '30'}.items(),
            {'type': 'tuple', 'items_schema': [{'type': 'any'}], 'variadic_item_index': 0},
            {(1, 10), (2, 20), ('3', '30')},
            id='Tuple[Any, Any]',
        ),
        pytest.param(
            {1: 10, 2: 20, '3': '30'}.items(),
            {'type': 'tuple', 'items_schema': [{'type': 'int'}], 'variadic_item_index': 0},
            {(1, 10), (2, 20), (3, 30)},
            id='Tuple[int, int]',
        ),
        pytest.param({1: 10, 2: 20, '3': '30'}.items(), {'type': 'any'}, {(1, 10), (2, 20), ('3', '30')}, id='Any'),
    ],
)
def test_set_from_dict_items(input_value, items_schema, expected):
    v = SchemaValidator(cs.set_schema(items_schema=items_schema))
    output = v.validate_python(input_value)
    assert isinstance(output, set)
    assert output == expected


@pytest.mark.parametrize(
    'input_value,expected',
    [
        ([], set()),
        ([1, '2', b'3'], {1, '2', b'3'}),
        ({1, '2', b'3'}, {1, '2', b'3'}),
        (frozenset([1, '2', b'3']), {1, '2', b'3'}),
        (deque([1, '2', b'3']), {1, '2', b'3'}),
    ],
)
def test_set_any(input_value, expected):
    v = SchemaValidator(cs.set_schema())
    output = v.validate_python(input_value)
    assert output == expected
    assert isinstance(output, set)


@pytest.mark.parametrize(
    'fail_fast,expected',
    [
        pytest.param(
            True,
            [
                {
                    'type': 'int_parsing',
                    'loc': (1,),
                    'msg': 'Input should be a valid integer, unable to parse string as an integer',
                    'input': 'not-num',
                },
            ],
            id='fail_fast',
        ),
        pytest.param(
            False,
            [
                {
                    'type': 'int_parsing',
                    'loc': (1,),
                    'msg': 'Input should be a valid integer, unable to parse string as an integer',
                    'input': 'not-num',
                },
                {
                    'type': 'int_parsing',
                    'loc': (2,),
                    'msg': 'Input should be a valid integer, unable to parse string as an integer',
                    'input': 'again',
                },
            ],
            id='not_fail_fast',
        ),
    ],
)
def test_set_fail_fast(fail_fast, expected):
    v = SchemaValidator(cs.set_schema(items_schema=cs.int_schema(), fail_fast=fail_fast))

    with pytest.raises(ValidationError) as exc_info:
        v.validate_python([1, 'not-num', 'again'])

    assert exc_info.value.errors(include_url=False) == expected
