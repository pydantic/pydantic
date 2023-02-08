import platform
import re
from collections import deque
from collections.abc import Sequence
from typing import Any, Dict

import pytest
from dirty_equals import HasRepr, IsInstance, IsStr

from pydantic_core import SchemaValidator, ValidationError

from ..conftest import Err, PyAndJson, infinite_generator


@pytest.mark.parametrize(
    'input_value,expected',
    [
        ([1, 2, 3], [1, 2, 3]),
        ([1, 2, '3'], [1, 2, 3]),
        (5, Err('Input should be a valid list/array [type=list_type, input_value=5, input_type=int]')),
        ('5', Err("Input should be a valid list/array [type=list_type, input_value='5', input_type=str]")),
    ],
    ids=repr,
)
def test_list_json(py_and_json: PyAndJson, input_value, expected):
    v = py_and_json({'type': 'list', 'items_schema': {'type': 'int'}})
    if isinstance(expected, Err):
        with pytest.raises(ValidationError, match=re.escape(expected.message)):
            v.validate_test(input_value)
    else:
        assert v.validate_test(input_value) == expected


def test_list_strict():
    v = SchemaValidator({'type': 'list', 'items_schema': {'type': 'int'}, 'strict': True})
    assert v.validate_python([1, 2, '33']) == [1, 2, 33]
    with pytest.raises(ValidationError) as exc_info:
        v.validate_python((1, 2, '33'))
    assert exc_info.value.errors() == [
        {'type': 'list_type', 'loc': (), 'msg': 'Input should be a valid list/array', 'input': (1, 2, '33')}
    ]


def gen_ints():
    yield 1
    yield 2
    yield '3'


@pytest.mark.parametrize(
    'input_value,expected',
    [
        ([1, 2, '3'], [1, 2, 3]),
        ((1, 2, '3'), [1, 2, 3]),
        (deque((1, 2, '3')), [1, 2, 3]),
        ({1, 2, '3'}, Err('Input should be a valid list/array [type=list_type,')),
        (gen_ints(), [1, 2, 3]),
        (frozenset({1, 2, '3'}), Err('Input should be a valid list/array [type=list_type,')),
        pytest.param(
            {1: 10, 2: 20, '3': '30'}.keys(),
            [1, 2, 3],
            marks=pytest.mark.skipif(
                platform.python_implementation() == 'PyPy', reason='dict views not implemented in pyo3 for pypy'
            ),
        ),
        pytest.param(
            {1: 10, 2: 20, '3': '30'}.values(),
            [10, 20, 30],
            marks=pytest.mark.skipif(
                platform.python_implementation() == 'PyPy', reason='dict views not implemented in pyo3 for pypy'
            ),
        ),
        ({1: 10, 2: 20, '3': '30'}, Err('Input should be a valid list/array [type=list_type,')),
        ((x for x in [1, 2, '3']), [1, 2, 3]),
        ('456', Err("Input should be a valid list/array [type=list_type, input_value='456', input_type=str]")),
        (b'789', Err("Input should be a valid list/array [type=list_type, input_value=b'789', input_type=bytes]")),
    ],
    ids=repr,
)
def test_list_int(input_value, expected):
    v = SchemaValidator({'type': 'list', 'items_schema': {'type': 'int'}})
    if isinstance(expected, Err):
        with pytest.raises(ValidationError, match=re.escape(expected.message)):
            v.validate_python(input_value)
    else:
        assert v.validate_python(input_value) == expected


@pytest.mark.parametrize(
    'input_value,expected',
    [
        ([], []),
        ([1, '2', b'3'], [1, '2', b'3']),
        (frozenset([1, '2', b'3']), Err('Input should be a valid list/array [type=list_type,')),
        ((), []),
        ((1, '2', b'3'), [1, '2', b'3']),
        (deque([1, '2', b'3']), [1, '2', b'3']),
        ({1, '2', b'3'}, Err('Input should be a valid list/array [type=list_type,')),
    ],
)
def test_list_any(input_value, expected):
    v = SchemaValidator({'type': 'list'})
    if isinstance(expected, Err):
        with pytest.raises(ValidationError, match=re.escape(expected.message)):
            v.validate_python(input_value)
    else:
        assert v.validate_python(input_value) == expected


@pytest.mark.parametrize(
    'input_value,index',
    [
        (['wrong'], 0),
        (('wrong',), 0),
        (deque(['wrong']), 0),
        ([1, 2, 3, 'wrong'], 3),
        ((1, 2, 3, 'wrong', 4), 3),
        (deque([1, 2, 3, 'wrong']), 3),
    ],
)
def test_list_error(input_value, index):
    v = SchemaValidator({'type': 'list', 'items_schema': {'type': 'int'}})
    with pytest.raises(ValidationError) as exc_info:
        v.validate_python(input_value)
    assert exc_info.value.errors() == [
        {
            'type': 'int_parsing',
            'loc': (index,),
            'msg': 'Input should be a valid integer, unable to parse string as an integer',
            'input': 'wrong',
        }
    ]


@pytest.mark.parametrize(
    'kwargs,input_value,expected',
    [
        ({}, [1, 2, 3, 4], [1, 2, 3, 4]),
        ({'min_length': 3}, [1, 2, 3, 4], [1, 2, 3, 4]),
        ({'min_length': 3}, [1, 2], Err('List should have at least 3 items after validation, not 2 [type=too_short,')),
        ({'min_length': 1}, [], Err('List should have at least 1 item after validation, not 0 [type=too_short,')),
        ({'max_length': 4}, [1, 2, 3, 4], [1, 2, 3, 4]),
        (
            {'max_length': 3},
            [1, 2, 3, 4],
            Err('List should have at most 3 items after validation, not 4 [type=too_long,'),
        ),
        ({'max_length': 1}, [1, 2], Err('List should have at most 1 item after validation, not 2 [type=too_long,')),
        (
            {'max_length': 44},
            infinite_generator(),
            Err('List should have at most 44 items after validation, not 45 [type=too_long,'),
        ),
    ],
)
def test_list_length_constraints(kwargs: Dict[str, Any], input_value, expected):
    v = SchemaValidator({'type': 'list', **kwargs})
    if isinstance(expected, Err):
        with pytest.raises(ValidationError, match=re.escape(expected.message)):
            v.validate_python(input_value)
    else:
        assert v.validate_python(input_value) == expected


@pytest.mark.parametrize(
    'input_value,expected',
    [
        ([1, 2, 3, 4], [1, 2, 3, 4]),
        ([1, 2, 3, 4, 5], Err('List should have at most 4 items after validation, not 5 [type=too_long,')),
        ([1, 2, 3, 'x', 4], [1, 2, 3, 4]),
    ],
)
def test_list_length_constraints_omit(input_value, expected):
    v = SchemaValidator(
        {
            'type': 'list',
            'items_schema': {'type': 'default', 'schema': {'type': 'int'}, 'on_error': 'omit'},
            'max_length': 4,
        }
    )
    if isinstance(expected, Err):
        with pytest.raises(ValidationError, match=re.escape(expected.message)):
            v.validate_python(input_value)
    else:
        assert v.validate_python(input_value) == expected


def test_length_ctx():
    v = SchemaValidator({'type': 'list', 'min_length': 2, 'max_length': 3})
    with pytest.raises(ValidationError) as exc_info:
        v.validate_python([1])
    # insert_assert(exc_info.value.errors())
    assert exc_info.value.errors() == [
        {
            'type': 'too_short',
            'loc': (),
            'msg': 'List should have at least 2 items after validation, not 1',
            'input': [1],
            'ctx': {'field_type': 'List', 'min_length': 2, 'actual_length': 1},
        }
    ]

    with pytest.raises(ValidationError) as exc_info:
        v.validate_python([1, 2, 3, 4])

    # insert_assert(exc_info.value.errors())
    assert exc_info.value.errors() == [
        {
            'type': 'too_long',
            'loc': (),
            'msg': 'List should have at most 3 items after validation, not 4',
            'input': [1, 2, 3, 4],
            'ctx': {'field_type': 'List', 'max_length': 3, 'actual_length': 4},
        }
    ]


def test_list_function():
    def f(input_value, **kwargs):
        return input_value * 2

    v = SchemaValidator({'type': 'list', 'items_schema': {'type': 'function', 'mode': 'plain', 'function': f}})

    assert v.validate_python([1, 2, 3]) == [2, 4, 6]


def test_list_function_val_error():
    def f(input_value, **kwargs):
        raise ValueError(f'error {input_value}')

    v = SchemaValidator({'type': 'list', 'items_schema': {'type': 'function', 'mode': 'plain', 'function': f}})

    with pytest.raises(ValidationError) as exc_info:
        v.validate_python([1, 2])
    assert exc_info.value.errors() == [
        {'type': 'value_error', 'loc': (0,), 'msg': 'Value error, error 1', 'input': 1, 'ctx': {'error': 'error 1'}},
        {'type': 'value_error', 'loc': (1,), 'msg': 'Value error, error 2', 'input': 2, 'ctx': {'error': 'error 2'}},
    ]


def test_list_function_internal_error():
    def f(input_value, **kwargs):
        raise RuntimeError(f'error {input_value}')

    v = SchemaValidator({'type': 'list', 'items_schema': {'type': 'function', 'mode': 'plain', 'function': f}})

    with pytest.raises(RuntimeError, match='^error 1$') as exc_info:
        v.validate_python([1, 2])
    assert exc_info.value.args[0] == 'error 1'


def test_generator_error():
    def gen(error: bool):
        yield 1
        yield 2
        if error:
            raise RuntimeError('error')
        yield 3

    v = SchemaValidator({'type': 'list', 'items_schema': {'type': 'int'}})
    assert v.validate_python(gen(False)) == [1, 2, 3]
    with pytest.raises(ValidationError) as exc_info:
        v.validate_python(gen(True))
    assert exc_info.value.errors() == [
        {
            'type': 'iteration_error',
            'loc': (2,),
            'msg': 'Error iterating over object, error: RuntimeError: error',
            'input': HasRepr(IsStr(regex='<generator object test_generator_error.<locals>.gen at 0x[0-9a-fA-F]+>')),
            'ctx': {'error': 'RuntimeError: error'},
        }
    ]


@pytest.mark.skipif(platform.python_implementation() == 'PyPy', reason='dict views not implemented in pyo3 for pypy')
@pytest.mark.parametrize(
    'input_value,items_schema,expected',
    [
        pytest.param(
            {1: 10, 2: 20, '3': '30'}.items(),
            {'type': 'tuple', 'items_schema': {'type': 'any'}},
            [(1, 10), (2, 20), ('3', '30')],
            id='Tuple[Any, Any]',
        ),
        pytest.param(
            {1: 10, 2: 20, '3': '30'}.items(),
            {'type': 'tuple', 'items_schema': {'type': 'int'}},
            [(1, 10), (2, 20), (3, 30)],
            id='Tuple[int, int]',
        ),
        pytest.param({1: 10, 2: 20, '3': '30'}.items(), {'type': 'any'}, [(1, 10), (2, 20), ('3', '30')], id='Any'),
    ],
)
def test_list_from_dict_items(input_value, items_schema, expected):
    v = SchemaValidator({'type': 'list', 'items_schema': items_schema})
    output = v.validate_python(input_value)
    assert isinstance(output, list)
    assert output == expected


@pytest.fixture(scope='session', name='MySequence')
def my_sequence():
    class MySequence(Sequence):
        def __init__(self):
            self._data = [1, 2, 3]

        def __getitem__(self, index):
            return self._data[index]

        def __len__(self):
            return len(self._data)

        def count(self, value):
            return self._data.count(value)

    assert isinstance(MySequence(), Sequence)
    return MySequence


def test_sequence(MySequence):
    v = SchemaValidator({'type': 'list', 'items_schema': {'type': 'int'}})
    with pytest.raises(ValidationError) as exc_info:
        v.validate_python(MySequence())
    # insert_assert(exc_info.value.errors())
    assert exc_info.value.errors() == [
        {'type': 'list_type', 'loc': (), 'msg': 'Input should be a valid list/array', 'input': IsInstance(MySequence)}
    ]


@pytest.mark.parametrize(
    'input_value,expected',
    [
        ([1, 2, 3], [1, 2, 3]),
        ((1, 2, 3), [1, 2, 3]),
        (range(3), [0, 1, 2]),
        (gen_ints(), [1, 2, 3]),
        ({1: 2, 3: 4}, [1, 3]),
        ('123', [1, 2, 3]),
        (
            123,
            Err(
                '1 validation error for list[int]',
                [{'type': 'list_type', 'loc': (), 'msg': 'Input should be a valid list/array', 'input': 123}],
            ),
        ),
    ],
)
def test_allow_any_iter(input_value, expected):
    v = SchemaValidator({'type': 'list', 'items_schema': {'type': 'int'}, 'allow_any_iter': True})
    if isinstance(expected, Err):
        with pytest.raises(ValidationError, match=re.escape(expected.message)) as exc_info:
            v.validate_python(input_value)
        assert exc_info.value.errors() == expected.errors
    else:
        assert v.validate_python(input_value) == expected


def test_sequence_allow_any_iter(MySequence):
    v = SchemaValidator({'type': 'list', 'items_schema': {'type': 'int'}, 'allow_any_iter': True})
    assert v.validate_python(MySequence()) == [1, 2, 3]


@pytest.mark.parametrize('items_schema', ['int', 'any'])
def test_bad_iter(items_schema):
    class BadIter:
        def __init__(self, success: bool):
            self._success = success
            self._index = 0

        def __iter__(self):
            return self

        def __len__(self):
            return 2

        def __next__(self):
            self._index += 1
            if self._index == 1:
                return 1
            elif self._success:
                raise StopIteration()
            else:
                raise RuntimeError('broken')

    v = SchemaValidator({'type': 'list', 'items_schema': {'type': items_schema}, 'allow_any_iter': True})
    assert v.validate_python(BadIter(True)) == [1]
    with pytest.raises(ValidationError) as exc_info:
        v.validate_python(BadIter(False))
    # insert_assert(exc_info.value.errors())
    assert exc_info.value.errors() == [
        {
            'type': 'iteration_error',
            'loc': (1,),
            'msg': 'Error iterating over object, error: RuntimeError: broken',
            'input': IsInstance(BadIter),
            'ctx': {'error': 'RuntimeError: broken'},
        }
    ]
