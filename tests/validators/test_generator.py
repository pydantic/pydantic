import re

import pytest
from dirty_equals import HasRepr, IsStr

from pydantic_core import SchemaValidator, ValidationError

from ..conftest import Err, PyAndJson


@pytest.mark.parametrize(
    'input_value,expected',
    [
        ([1, 2, 3], [1, 2, 3]),
        ([1, 2, '3'], [1, 2, 3]),
        ({1: 2, 3: 4}, [1, 3]),
        ('123', [1, 2, 3]),
        (5, Err('Input should be iterable [type=iterable_type, input_value=5, input_type=int]')),
        (
            [1, 'wrong'],
            Err(
                'Input should be a valid integer, unable to parse string as an integer '
                "[type=int_parsing, input_value='wrong', input_type=str]"
            ),
        ),
    ],
    ids=repr,
)
def test_generator_json_int(py_and_json: PyAndJson, input_value, expected):
    v = py_and_json({'type': 'generator', 'items_schema': {'type': 'int'}})
    if isinstance(expected, Err):
        with pytest.raises(ValidationError, match=re.escape(expected.message)):
            list(v.validate_test(input_value))

    else:
        assert list(v.validate_test(input_value)) == expected


@pytest.mark.parametrize(
    'input_value,expected',
    [
        ([1, 2, 3], [1, 2, 3]),
        ([1, 2, '3'], [1, 2, '3']),
        ({'1': 2, '3': 4}, ['1', '3']),
        ('123', ['1', '2', '3']),
        (5, Err('Input should be iterable [type=iterable_type, input_value=5, input_type=int]')),
        ([1, 'wrong'], [1, 'wrong']),
    ],
    ids=repr,
)
def test_generator_json_any(py_and_json: PyAndJson, input_value, expected):
    v = py_and_json({'type': 'generator'})
    if isinstance(expected, Err):
        with pytest.raises(ValidationError, match=re.escape(expected.message)):
            list(v.validate_test(input_value))

    else:
        assert list(v.validate_test(input_value)) == expected


def test_error_index(py_and_json: PyAndJson):
    v = py_and_json({'type': 'generator', 'items_schema': {'type': 'int'}})
    gen = v.validate_test(['wrong'])
    assert gen.index == 0
    with pytest.raises(ValidationError) as exc_info:
        next(gen)
    assert gen.index == 1
    # insert_assert(exc_info.value.errors())
    assert exc_info.value.title == 'ValidatorIterator'
    assert str(exc_info.value).startswith('1 validation error for ValidatorIterator\n')
    assert exc_info.value.errors() == [
        {
            'type': 'int_parsing',
            'loc': (0,),
            'msg': 'Input should be a valid integer, unable to parse string as an integer',
            'input': 'wrong',
        }
    ]
    gen = v.validate_test([1, 2, 3, 'wrong', 4])
    assert gen.index == 0
    assert next(gen) == 1
    assert gen.index == 1
    assert next(gen) == 2
    assert gen.index == 2
    assert next(gen) == 3
    assert gen.index == 3
    with pytest.raises(ValidationError) as exc_info:
        next(gen)
    assert gen.index == 4
    assert exc_info.value.errors() == [
        {
            'type': 'int_parsing',
            'loc': (3,),
            'msg': 'Input should be a valid integer, unable to parse string as an integer',
            'input': 'wrong',
        }
    ]
    assert next(gen) == 4
    assert gen.index == 5


def test_too_long(py_and_json: PyAndJson):
    v = py_and_json({'type': 'generator', 'items_schema': {'type': 'int'}, 'max_length': 2})
    assert list(v.validate_test([1])) == [1]
    assert list(v.validate_test([1, 2])) == [1, 2]
    with pytest.raises(ValidationError) as exc_info:
        list(v.validate_test([1, 2, 3]))
    # insert_assert(exc_info.value.errors())
    assert exc_info.value.errors() == [
        {
            'type': 'too_long',
            'loc': (),
            'msg': 'Generator should have at most 2 items after validation, not 3',
            'input': [1, 2, 3],
            'ctx': {'field_type': 'Generator', 'max_length': 2, 'actual_length': 3},
        }
    ]


def test_too_short(py_and_json: PyAndJson):
    v = py_and_json({'type': 'generator', 'items_schema': {'type': 'int'}, 'min_length': 2})
    assert list(v.validate_test([1, 2, 3])) == [1, 2, 3]
    assert list(v.validate_test([1, 2])) == [1, 2]
    with pytest.raises(ValidationError) as exc_info:
        list(v.validate_test([1]))
    # insert_assert(exc_info.value.errors())
    assert exc_info.value.errors() == [
        {
            'type': 'too_short',
            'loc': (),
            'msg': 'Generator should have at least 2 items after validation, not 1',
            'input': [1],
            'ctx': {'field_type': 'Generator', 'min_length': 2, 'actual_length': 1},
        }
    ]


def gen():
    yield 1
    yield 2
    yield 3


def test_generator_too_long():
    v = SchemaValidator({'type': 'generator', 'items_schema': {'type': 'int'}, 'max_length': 2})

    validating_iterator = v.validate_python(gen())

    # Ensure the error happens at exactly the right step:
    assert next(validating_iterator) == 1
    assert next(validating_iterator) == 2
    with pytest.raises(ValidationError) as exc_info:
        next(validating_iterator)

    errors = exc_info.value.errors()
    # insert_assert(errors)
    assert errors == [
        {
            'type': 'too_long',
            'loc': (),
            'input': HasRepr(IsStr(regex='<generator object gen at .+>')),
            'msg': 'Generator should have at most 2 items after validation, not 3',
            'ctx': {'field_type': 'Generator', 'max_length': 2, 'actual_length': 3},
        }
    ]


def test_generator_too_short():
    v = SchemaValidator({'type': 'generator', 'items_schema': {'type': 'int'}, 'min_length': 4})

    validating_iterator = v.validate_python(gen())

    # Ensure the error happens at exactly the right step:
    assert next(validating_iterator) == 1
    assert next(validating_iterator) == 2
    assert next(validating_iterator) == 3
    with pytest.raises(ValidationError) as exc_info:
        next(validating_iterator)

    errors = exc_info.value.errors()
    # insert_assert(errors)
    assert errors == [
        {
            'type': 'too_short',
            'input': HasRepr(IsStr(regex='<generator object gen at .+>')),
            'loc': (),
            'msg': 'Generator should have at least 4 items after validation, not 3',
            'ctx': {'field_type': 'Generator', 'min_length': 4, 'actual_length': 3},
        }
    ]
