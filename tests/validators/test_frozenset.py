import platform
import re
from collections import deque
from typing import Any, Dict

import pytest

from pydantic_core import SchemaValidator, ValidationError

from ..conftest import Err, PyAndJson, infinite_generator, plain_repr


@pytest.mark.parametrize(
    'input_value,expected',
    [([], frozenset()), ([1, 2, 3], {1, 2, 3}), ([1, 2, '3'], {1, 2, 3}), ([1, 2, 3, 2, 3], {1, 2, 3})],
)
def test_frozenset_ints_both(py_and_json: PyAndJson, input_value, expected):
    v = py_and_json({'type': 'frozenset', 'items_schema': {'type': 'int'}})
    output = v.validate_test(input_value)
    assert output == expected
    assert isinstance(output, frozenset)


@pytest.mark.parametrize(
    'input_value,expected',
    [([], frozenset()), ([1, '2', b'3'], {1, '2', b'3'}), (frozenset([1, '2', b'3']), {1, '2', b'3'})],
)
def test_frozenset_any(input_value, expected):
    v = SchemaValidator({'type': 'frozenset'})
    output = v.validate_python(input_value)
    assert output == expected
    assert isinstance(output, frozenset)


def test_no_copy():
    v = SchemaValidator({'type': 'frozenset'})
    input_value = frozenset([1, 2, 3])
    output = v.validate_python(input_value)
    assert output == input_value
    assert output is input_value
    assert id(output) == id(input_value)


@pytest.mark.parametrize(
    'input_value,expected',
    [
        ([1, 2.5, '3'], {1, 2.5, '3'}),
        ('foo', Err('Input should be a valid frozenset')),
        (1, Err('Input should be a valid frozenset')),
        (1.0, Err('Input should be a valid frozenset')),
        (False, Err('Input should be a valid frozenset')),
    ],
)
def test_frozenset_no_validators_both(py_and_json: PyAndJson, input_value, expected):
    v = py_and_json({'type': 'frozenset'})
    if isinstance(expected, Err):
        with pytest.raises(ValidationError, match=re.escape(expected.message)):
            v.validate_test(input_value)
    else:
        output = v.validate_test(input_value)
        assert output == expected
        assert isinstance(output, frozenset)


@pytest.mark.parametrize(
    'input_value,expected',
    [
        ({1, 2, 3}, frozenset({1, 2, 3})),
        (frozenset(), frozenset()),
        ([1, 2, 3, 2, 3], frozenset({1, 2, 3})),
        ([], frozenset()),
        ((1, 2, 3, 2, 3), frozenset({1, 2, 3})),
        (deque((1, 2, '3')), frozenset({1, 2, 3})),
        ((), frozenset()),
        (frozenset([1, 2, 3, 2, 3]), frozenset({1, 2, 3})),
        pytest.param(
            {1: 10, 2: 20, '3': '30'}.keys(),
            frozenset({1, 2, 3}),
            marks=pytest.mark.skipif(
                platform.python_implementation() == 'PyPy', reason='dict views not implemented in pyo3 for pypy'
            ),
        ),
        pytest.param(
            {1: 10, 2: 20, '3': '30'}.values(),
            frozenset({10, 20, 30}),
            marks=pytest.mark.skipif(
                platform.python_implementation() == 'PyPy', reason='dict views not implemented in pyo3 for pypy'
            ),
        ),
        ({1: 10, 2: 20, '3': '30'}, Err('Input should be a valid frozenset [type=frozen_set_type,')),
        ((x for x in [1, 2, '3']), frozenset({1, 2, 3})),
        ({'abc'}, Err('0\n  Input should be a valid integer')),
        ({1, 2, 'wrong'}, Err('Input should be a valid integer')),
        ({1: 2}, Err('1 validation error for frozenset[int]\n  Input should be a valid frozenset')),
        ('abc', Err('Input should be a valid frozenset')),
    ],
)
def test_frozenset_ints_python(input_value, expected):
    v = SchemaValidator({'type': 'frozenset', 'items_schema': {'type': 'int'}})
    if isinstance(expected, Err):
        with pytest.raises(ValidationError, match=re.escape(expected.message)):
            v.validate_python(input_value)
    else:
        output = v.validate_python(input_value)
        assert output == expected
        assert isinstance(output, frozenset)


@pytest.mark.parametrize(
    'input_value,expected',
    [(frozenset([1, 2.5, '3']), {1, 2.5, '3'}), ([1, 2.5, '3'], {1, 2.5, '3'}), ([(1, 2), (3, 4)], {(1, 2), (3, 4)})],
)
def test_frozenset_no_validators_python(input_value, expected):
    v = SchemaValidator({'type': 'frozenset'})
    output = v.validate_python(input_value)
    assert output == expected
    assert isinstance(output, frozenset)


def test_frozenset_multiple_errors():
    v = SchemaValidator({'type': 'frozenset', 'items_schema': {'type': 'int'}})
    with pytest.raises(ValidationError) as exc_info:
        v.validate_python(['a', (1, 2), []])
    assert exc_info.value.errors() == [
        {
            'type': 'int_parsing',
            'loc': (0,),
            'msg': 'Input should be a valid integer, unable to parse string as an integer',
            'input': 'a',
        },
        {'type': 'int_type', 'loc': (1,), 'msg': 'Input should be a valid integer', 'input': (1, 2)},
        {'type': 'int_type', 'loc': (2,), 'msg': 'Input should be a valid integer', 'input': []},
    ]


def generate_repeats():
    for i in 1, 2, 3:
        yield i
        yield i


@pytest.mark.parametrize(
    'kwargs,input_value,expected',
    [
        ({'strict': True}, frozenset(), frozenset()),
        ({'strict': True}, frozenset([1, 2, 3]), {1, 2, 3}),
        ({'strict': True}, {1, 2, 3}, Err('Input should be a valid frozenset')),
        ({'strict': True}, [1, 2, 3, 2, 3], Err('Input should be a valid frozenset [type=frozen_set_type,')),
        ({'strict': True}, [], Err('Input should be a valid frozenset [type=frozen_set_type,')),
        ({'strict': True}, (), Err('Input should be a valid frozenset [type=frozen_set_type,')),
        ({'strict': True}, (1, 2, 3), Err('Input should be a valid frozenset [type=frozen_set_type,')),
        ({'strict': True}, {1, 2, 3}, Err('Input should be a valid frozenset [type=frozen_set_type,')),
        ({'strict': True}, 'abc', Err('Input should be a valid frozenset [type=frozen_set_type,')),
        ({'min_length': 3}, {1, 2, 3}, {1, 2, 3}),
        (
            {'min_length': 3},
            {1, 2},
            Err('Frozenset should have at least 3 items after validation, not 2 [type=too_short,'),
        ),
        ({'max_length': 3}, {1, 2, 3}, {1, 2, 3}),
        (
            {'max_length': 3},
            {1, 2, 3, 4},
            Err('Frozenset should have at most 3 items after validation, not 4 [type=too_long,'),
        ),
        # length check after set creation
        ({'max_length': 3}, [1, 1, 2, 2, 3, 3], {1, 2, 3}),
        ({'max_length': 3}, generate_repeats(), {1, 2, 3}),
        # because of default max_length * 10
        (
            {'max_length': 3},
            infinite_generator(),
            Err('Frozenset should have at most 30 items after validation, not 31 [type=too_long,'),
        ),
        (
            {'max_length': 3, 'generator_max_length': 3},
            infinite_generator(),
            Err('Frozenset should have at most 3 items after validation, not 4 [type=too_long,'),
        ),
    ],
)
def test_frozenset_kwargs_python(kwargs: Dict[str, Any], input_value, expected):
    v = SchemaValidator({'type': 'frozenset', **kwargs})
    if isinstance(expected, Err):
        with pytest.raises(ValidationError, match=re.escape(expected.message)):
            v.validate_python(input_value)
    else:
        output = v.validate_python(input_value)
        assert output == expected
        assert isinstance(output, frozenset)


@pytest.mark.parametrize('input_value,expected', [({1, 2, 3}, {1, 2, 3}), ([1, 2, 3], [1, 2, 3])])
def test_union_frozenset_list(input_value, expected):
    v = SchemaValidator({'type': 'union', 'choices': [{'type': 'frozenset'}, {'type': 'list'}]})
    if isinstance(expected, Err):
        with pytest.raises(ValidationError, match=re.escape(expected.message)):
            v.validate_python(input_value)
    else:
        v.validate_python(input_value)


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
                        'loc': ('frozenset[int]', 1),
                        'msg': 'Input should be a valid integer',
                        'input': 'a',
                    },
                    # second because validation on the string choice comes second
                    {
                        'type': 'string_type',
                        'loc': ('frozenset[str]', 0),
                        'msg': 'Input should be a valid string',
                        'input': 1,
                    },
                ],
            ),
        ),
    ],
)
def test_union_frozenset_int_frozenset_str(input_value, expected):
    v = SchemaValidator(
        {
            'type': 'union',
            'choices': [
                {'type': 'frozenset', 'items_schema': {'type': 'int', 'strict': True}},
                {'type': 'frozenset', 'items_schema': {'type': 'str', 'strict': True}},
            ],
        }
    )
    if isinstance(expected, Err):
        with pytest.raises(ValidationError, match=re.escape(expected.message)) as exc_info:
            v.validate_python(input_value)
        if expected.errors is not None:
            assert exc_info.value.errors() == expected.errors
    else:
        output = v.validate_python(input_value)
        assert output == expected
        assert isinstance(output, frozenset)


def test_frozenset_as_dict_keys(py_and_json: PyAndJson):
    v = py_and_json({'type': 'dict', 'keys_schema': {'type': 'frozenset'}, 'values_schema': {'type': 'int'}})
    with pytest.raises(ValidationError, match=re.escape('Input should be a valid frozenset')):
        v.validate_test({'foo': 'bar'})


def test_repr():
    v = SchemaValidator({'type': 'frozenset', 'strict': True, 'min_length': 42})
    assert plain_repr(v) == (
        'SchemaValidator('
        'name="frozenset[any]",'
        'validator=FrozenSet(FrozenSetValidator{'
        'strict:true,item_validator:None,min_length:Some(42),max_length:None,generator_max_length:None,'
        'name:"frozenset[any]"'
        '}),slots=[])'
    )


def test_generator_error():
    def gen(error: bool):
        yield 1
        yield 2
        if error:
            raise RuntimeError('my error')
        yield 3

    v = SchemaValidator({'type': 'frozenset', 'items_schema': {'type': 'int'}})
    r = v.validate_python(gen(False))
    assert r == {1, 2, 3}
    assert isinstance(r, frozenset)

    msg = r'Error iterating over object, error: RuntimeError: my error \[type=iteration_error,'
    with pytest.raises(ValidationError, match=msg):
        v.validate_python(gen(True))


@pytest.mark.skipif(platform.python_implementation() == 'PyPy', reason='dict views not implemented in pyo3 for pypy')
@pytest.mark.parametrize(
    'input_value,items_schema,expected',
    [
        pytest.param(
            {1: 10, 2: 20, '3': '30'}.items(),
            {'type': 'tuple', 'items_schema': {'type': 'any'}},
            frozenset(((1, 10), (2, 20), ('3', '30'))),
            id='Tuple[Any, Any]',
        ),
        pytest.param(
            {1: 10, 2: 20, '3': '30'}.items(),
            {'type': 'tuple', 'items_schema': {'type': 'int'}},
            frozenset(((1, 10), (2, 20), (3, 30))),
            id='Tuple[int, int]',
        ),
        pytest.param({1: 10, 2: 20, '3': '30'}.items(), {'type': 'any'}, {(1, 10), (2, 20), ('3', '30')}, id='Any'),
    ],
)
def test_frozenset_from_dict_items(input_value, items_schema, expected):
    v = SchemaValidator({'type': 'frozenset', 'items_schema': items_schema})
    output = v.validate_python(input_value)
    assert isinstance(output, frozenset)
    assert output == expected
