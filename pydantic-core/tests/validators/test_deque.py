import re
from collections import deque
from typing import Any

import pytest

from pydantic_core import SchemaValidator, ValidationError
from pydantic_core import core_schema as cs

from ..conftest import Err, PyAndJson, infinite_generator, plain_repr


@pytest.mark.parametrize(
    ['input_value', 'expected'],
    [
        ([], deque()),
        ([1, 2, 3], deque([1, 2, 3])),
        ([1, 2, '3'], deque([1, 2, 3])),
        ([1, 2, 3, 2, 3], deque([1, 2, 3, 2, 3])),
    ],
)
def test_deque_ints_both(py_and_json: PyAndJson, input_value, expected) -> None:
    v = py_and_json({'type': 'deque', 'items_schema': {'type': 'int'}})
    output = v.validate_test(input_value)

    assert output == expected
    assert isinstance(output, deque)


@pytest.mark.parametrize(
    ['input_value', 'expected'],
    [([], deque()), ([1, '2', b'3'], deque([1, '2', b'3'])), (deque([1, '2', b'3']), deque([1, '2', b'3']))],
)
def test_deque_any(input_value, expected) -> None:
    v = SchemaValidator(cs.deque_schema())
    output = v.validate_python(input_value)

    assert output == expected
    assert isinstance(output, deque)


def test_no_copy() -> None:
    v = SchemaValidator(cs.deque_schema())
    input_value = deque([1, 2, 3])
    output = v.validate_python(input_value)

    assert output == input_value
    assert output is not input_value


@pytest.mark.parametrize(
    ['input_value', 'expected'],
    [
        ([1, 2.5, '3'], deque([1, 2.5, '3'])),
        ('foo', Err("[type=deque_type, input_value='foo', input_type=str]")),
        (1, Err('[type=deque_type, input_value=1, input_type=int]')),
        (1.0, Err('[type=deque_type, input_value=1.0, input_type=float]')),
        (False, Err('[type=deque_type, input_value=False, input_type=bool]')),
    ],
)
def test_deque_no_validators_both(py_and_json: PyAndJson, input_value, expected) -> None:
    v = py_and_json({'type': 'deque'})

    if isinstance(expected, Err):
        with pytest.raises(ValidationError, match=re.escape(expected.message)):
            v.validate_test(input_value)
    else:
        output = v.validate_test(input_value)
        assert output == expected
        assert isinstance(output, deque)


def test_deque_json_error_message() -> None:
    v = SchemaValidator(cs.deque_schema(cs.int_schema()))
    with pytest.raises(ValidationError) as exc_info:
        v.validate_json('"abc"')

    assert exc_info.value.errors(include_url=False) == [
        {'type': 'deque_type', 'loc': (), 'msg': 'Input should be a valid array', 'input': 'abc'}
    ]


@pytest.mark.parametrize(
    ['input_value', 'expected'],
    [
        (deque([1, 2, '3']), deque([1, 2, 3])),
        (deque(), deque()),
        ([1, 2, '3'], deque([1, 2, 3])),
        ([], deque()),
        ((1, 2, '3'), deque([1, 2, 3])),
        ((), deque()),
        ({1, 2, 3}, deque([1, 2, 3])),
        (frozenset([1, 2, 3]), deque([1, 2, 3])),
        ({1: 10, 2: 20, '3': '30'}.keys(), deque([1, 2, 3])),
        ({1: 10, 2: 20, '3': '30'}.values(), deque([10, 20, 30])),
        ({1: 10, 2: 20, '3': '30'}, Err('Input should be a valid deque [type=deque_type,')),
        ((x for x in [1, 2, '3']), deque([1, 2, 3])),
        (['abc'], Err('0\n  Input should be a valid integer')),
        ([1, 2, 'wrong'], Err('Input should be a valid integer')),
        ({1: 2}, Err('1 validation error for deque[int]\n  Input should be a valid deque')),
        ('abc', Err('Input should be a valid deque')),
        (b'abc', Err('Input should be a valid deque')),
    ],
)
@pytest.mark.thread_unsafe(
    reason='generators in parameters not compatible with pytest-run-parallel, https://github.com/Quansight-Labs/pytest-run-parallel/issues/14'
)
def test_deque_ints_python(input_value, expected) -> None:
    v = SchemaValidator(cs.deque_schema(items_schema=cs.int_schema()))

    if isinstance(expected, Err):
        with pytest.raises(ValidationError, match=re.escape(expected.message)):
            v.validate_python(input_value)
    else:
        output = v.validate_python(input_value)
        assert output == expected
        assert isinstance(output, deque)


@pytest.mark.parametrize(
    'input_value',
    [
        deque([1, 2, 3], maxlen=5),
        deque([1, 2, 3]),
        deque([], maxlen=0),
    ],
)
@pytest.mark.parametrize('items_schema', [None, cs.int_schema()])
def test_deque_maxlen_preserved(items_schema, input_value) -> None:
    """`maxlen` is preserved when the input is a deque instance."""
    v = SchemaValidator(cs.deque_schema(items_schema))
    output = v.validate_python(input_value)

    assert output == input_value
    assert output.maxlen == input_value.maxlen


def test_deque_maxlen_not_set_for_other_inputs() -> None:
    v = SchemaValidator(cs.deque_schema(cs.int_schema()))

    assert v.validate_python([1, 2, 3]).maxlen is None
    assert v.validate_json('[1, 2, 3]').maxlen is None


def test_deque_multiple_errors() -> None:
    v = SchemaValidator(cs.deque_schema(items_schema=cs.int_schema()))

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


@pytest.mark.parametrize(
    ['kwargs', 'input_value', 'expected'],
    [
        ({'strict': True}, deque(), deque()),
        ({'strict': True}, deque([1, 2, 3]), deque([1, 2, 3])),
        ({'strict': True}, [1, 2, 3], Err('Input should be a valid deque [type=deque_type,')),
        ({'strict': True}, [], Err('Input should be a valid deque [type=deque_type,')),
        ({'strict': True}, (), Err('Input should be a valid deque [type=deque_type,')),
        ({'strict': True}, (1, 2, 3), Err('Input should be a valid deque [type=deque_type,')),
        ({'strict': True}, {1, 2, 3}, Err('Input should be a valid deque [type=deque_type,')),
        ({'strict': True}, 'abc', Err('Input should be a valid deque [type=deque_type,')),
        ({'min_length': 3}, [1, 2, 3], deque([1, 2, 3])),
        ({'min_length': 3}, [1, 2], Err('Deque should have at least 3 items after validation, not 2 [type=too_short,')),
        (
            {'min_length': 3},
            deque([1, 2]),
            Err('Deque should have at least 3 items after validation, not 2 [type=too_short,'),
        ),
        ({'max_length': 3}, [1, 2, 3], deque([1, 2, 3])),
        (
            {'max_length': 3},
            [1, 2, 3, 4],
            Err('Deque should have at most 3 items after validation, not 4 [type=too_long,'),
        ),
        (
            {'max_length': 3},
            deque([1, 2, 3, 4]),
            Err('Deque should have at most 3 items after validation, not 4 [type=too_long,'),
        ),
        (
            {'items_schema': {'type': 'int'}, 'max_length': 3},
            [1, 2, 3, 4],
            Err('Deque should have at most 3 items after validation, not 4 [type=too_long,'),
        ),
        (
            {'max_length': 3},
            infinite_generator(),
            Err('Deque should have at most 3 items after validation, not more [type=too_long,'),
        ),
    ],
)
@pytest.mark.thread_unsafe(
    reason='generators in parameters not compatible with pytest-run-parallel, https://github.com/Quansight-Labs/pytest-run-parallel/issues/14'
)
def test_deque_kwargs_python(kwargs: dict[str, Any], input_value, expected) -> None:
    v = SchemaValidator(cs.deque_schema(**kwargs))

    if isinstance(expected, Err):
        with pytest.raises(ValidationError, match=re.escape(expected.message)):
            v.validate_python(input_value)
    else:
        output = v.validate_python(input_value)
        assert output == expected
        assert isinstance(output, deque)


def test_deque_strict_json() -> None:
    """A JSON array is always accepted, even in strict mode."""
    v = SchemaValidator(cs.deque_schema(cs.int_schema(), strict=True))

    assert v.validate_json('[1, 2]') == deque([1, 2])


@pytest.mark.parametrize(['input_value', 'expected'], [(deque([1, 2, 3]), deque([1, 2, 3])), ([1, 2, 3], [1, 2, 3])])
def test_union_deque_list(input_value, expected) -> None:
    v = SchemaValidator(cs.union_schema(choices=[cs.deque_schema(), cs.list_schema()]))
    output = v.validate_python(input_value)

    assert output == expected
    assert type(output) is type(expected)


def test_deque_as_dict_keys(py_and_json: PyAndJson) -> None:
    v = py_and_json({'type': 'dict', 'keys_schema': {'type': 'deque'}, 'values_schema': {'type': 'int'}})

    with pytest.raises(ValidationError, match=re.escape("[type=int_parsing, input_value='bar', input_type=str]")):
        v.validate_test({'foo': 'bar'})


def test_repr() -> None:
    v = SchemaValidator(cs.deque_schema(strict=True, min_length=42))
    assert plain_repr(v) == (
        'SchemaValidator('
        'title="deque[any]",'
        'validator=Deque(DequeValidator{'
        'strict:true,item_validator:None,min_length:Some(42),max_length:None,'
        'name:OnceLock("deque[any]"),'
        'fail_fast:false'
        '}),'
        'definitions=[],'
        'cache_strings=True)'
    )


def test_generator_error() -> None:
    def gen(error: bool):
        yield 1
        yield 2
        if error:
            raise RuntimeError('my error')
        yield 3

    v = SchemaValidator(cs.deque_schema(items_schema=cs.int_schema()))
    r = v.validate_python(gen(False))
    assert r == deque([1, 2, 3])
    assert isinstance(r, deque)

    msg = r'Error iterating over object, error: RuntimeError: my error \[type=iteration_error,'
    with pytest.raises(ValidationError, match=msg):
        v.validate_python(gen(True))


@pytest.mark.parametrize(
    ['input_value', 'items_schema', 'expected'],
    [
        pytest.param(
            {1: 10, 2: 20, '3': '30'}.items(),
            {'type': 'tuple', 'items_schema': [{'type': 'any'}], 'variadic_item_index': 0},
            deque([(1, 10), (2, 20), ('3', '30')]),
            id='Tuple[Any, Any]',
        ),
        pytest.param(
            {1: 10, 2: 20, '3': '30'}.items(),
            {'type': 'tuple', 'items_schema': [{'type': 'int'}], 'variadic_item_index': 0},
            deque([(1, 10), (2, 20), (3, 30)]),
            id='Tuple[int, int]',
        ),
        pytest.param(
            {1: 10, 2: 20, '3': '30'}.items(), {'type': 'any'}, deque([(1, 10), (2, 20), ('3', '30')]), id='Any'
        ),
    ],
)
def test_deque_from_dict_items(input_value, items_schema, expected) -> None:
    v = SchemaValidator(cs.deque_schema(items_schema=items_schema))
    output = v.validate_python(input_value)

    assert isinstance(output, deque)
    assert output == expected


@pytest.mark.parametrize(
    ['fail_fast', 'expected'],
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
def test_deque_fail_fast(fail_fast, expected) -> None:
    v = SchemaValidator(cs.deque_schema(items_schema=cs.int_schema(), fail_fast=fail_fast))

    with pytest.raises(ValidationError) as exc_info:
        v.validate_python([1, 'not-num', 'again'])

    assert exc_info.value.errors(include_url=False) == expected


def test_deque_subclass() -> None:
    class MyDeque(deque):
        pass

    v = SchemaValidator(cs.deque_schema(cs.int_schema(), strict=True))
    output = v.validate_python(MyDeque([1, '2']))

    assert output == deque([1, 2])
    assert type(output) is deque
