import re

import pytest
from dirty_equals import IsNonNegative, IsTuple

from pydantic_core import SchemaError, SchemaValidator, ValidationError

from ..conftest import Err


@pytest.mark.parametrize(
    'tuple_variant,items,input_value,expected',
    [
        ('tuple-var-len', {'type': 'int'}, [1, 2, 3], (1, 2, 3)),
        (
            'tuple-var-len',
            {'type': 'int'},
            1,
            Err('Value must be a valid tuple [kind=tuple_type, input_value=1, input_type=int]'),
        ),
        ('tuple-fix-len', [{'type': 'int'}, {'type': 'int'}, {'type': 'int'}], [1, 2, '3'], (1, 2, 3)),
        (
            'tuple-fix-len',
            [{'type': 'int'}, {'type': 'int'}, {'type': 'int'}],
            5,
            Err('Value must be a valid tuple [kind=tuple_type, input_value=5, input_type=int]'),
        ),
    ],
)
def test_tuple_json(py_or_json, tuple_variant, items, input_value, expected):
    v = py_or_json({'type': tuple_variant, 'items': items})
    if isinstance(expected, Err):
        with pytest.raises(ValidationError, match=re.escape(expected.message)):
            v.validate_test(input_value)
    else:
        assert v.validate_test(input_value) == expected


@pytest.mark.parametrize(
    'tuple_variant,items,input,expected',
    [
        ('tuple-var-len', {'type': 'int'}, (1, 2, '33'), (1, 2, 33)),
        ('tuple-var-len', {'type': 'str'}, (1, 2, '33'), ('1', '2', '33')),
        ('tuple-fix-len', [{'type': 'int'}, {'type': 'str'}, {'type': 'float'}], (1, 2, 33), (1, '2', 33.0)),
    ],
)
def test_tuple_strict_passes_with_tuple(tuple_variant, items, input, expected):
    v = SchemaValidator({'type': tuple_variant, 'items': items, 'strict': True})
    assert v.validate_python(input) == expected


@pytest.mark.parametrize(
    'tuple_variant,items',
    [('tuple-var-len', {'type': 'int'}), ('tuple-fix-len', [{'type': 'int'}, {'type': 'int'}, {'type': 'int'}])],
)
@pytest.mark.parametrize('wrong_coll_type', [list, set, frozenset])
def test_tuple_strict_fails_without_tuple(wrong_coll_type, tuple_variant, items):
    v = SchemaValidator({'type': tuple_variant, 'items': items, 'strict': True})
    with pytest.raises(ValidationError) as exc_info:
        v.validate_python(wrong_coll_type([1, 2, '33']))
    assert exc_info.value.errors() == [
        {
            'kind': 'tuple_type',
            'loc': [],
            'message': 'Value must be a valid tuple',
            'input_value': wrong_coll_type([1, 2, '33']),
        }
    ]


@pytest.mark.parametrize(
    'kwargs,input_value,expected',
    [
        ({}, (1, 2, 3, 4), (1, 2, 3, 4)),
        ({'min_items': 3}, (1, 2, 3, 4), (1, 2, 3, 4)),
        ({'min_items': 3}, (1, 2), Err('Tuple must have at least 3 items [kind=too_short')),
        ({'max_items': 4}, (1, 2, 3, 4), (1, 2, 3, 4)),
        ({'max_items': 3}, (1, 2, 3, 4), Err('Tuple must have at most 3 items [kind=too_long')),
    ],
)
def test_tuple_var_len_kwargs(kwargs, input_value, expected):
    v = SchemaValidator({'type': 'tuple-var-len', **kwargs})
    if isinstance(expected, Err):
        with pytest.raises(ValidationError, match=re.escape(expected.message)):
            v.validate_python(input_value)
    else:
        assert v.validate_python(input_value) == expected


@pytest.mark.parametrize(
    'tuple_variant,items',
    [('tuple-var-len', {'type': 'int'}), ('tuple-fix-len', [{'type': 'int'}, {'type': 'int'}, {'type': 'int'}])],
)
@pytest.mark.parametrize(
    'input_value,expected',
    [
        ((1, 2, '3'), (1, 2, 3)),
        ({1, 2, '3'}, IsTuple(1, 2, 3, check_order=False)),
        (frozenset([1, 2, '3']), IsTuple(1, 2, 3, check_order=False)),
    ],
)
def test_tuple_validate(input_value, expected, tuple_variant, items):
    v = SchemaValidator({'type': tuple_variant, 'items': items})
    assert v.validate_python(input_value) == expected


@pytest.mark.parametrize(
    'input_value,index',
    [
        (['wrong'], 0),
        (('wrong',), 0),
        ({'wrong'}, 0),
        ((1, 2, 3, 'wrong'), 3),
        ((1, 2, 3, 'wrong', 4), 3),
        ((1, 2, 'wrong'), IsNonNegative()),
    ],
)
def test_tuple_var_len_errors(input_value, index):
    v = SchemaValidator({'type': 'tuple-var-len', 'items': {'type': 'int'}})
    with pytest.raises(ValidationError) as exc_info:
        assert v.validate_python(input_value)
    assert exc_info.value.errors() == [
        {
            'kind': 'int_parsing',
            'loc': [index],
            'message': 'Value must be a valid integer, unable to parse string as an integer',
            'input_value': 'wrong',
        }
    ]


@pytest.mark.parametrize(
    'input_value,items,index',
    [
        (['wrong'], [{'type': 'int'}], 0),
        (('wrong',), [{'type': 'int'}], 0),
        ({'wrong'}, [{'type': 'int'}], 0),
        ((1, 2, 3, 'wrong'), [{'type': 'int'}, {'type': 'int'}, {'type': 'int'}, {'type': 'int'}], 3),
        (
            (1, 2, 3, 'wrong', 4),
            [{'type': 'int'}, {'type': 'int'}, {'type': 'int'}, {'type': 'int'}, {'type': 'int'}],
            3,
        ),
        ((1, 2, 'wrong'), [{'type': 'int'}, {'type': 'int'}, {'type': 'int'}], IsNonNegative()),
    ],
)
def test_tuple_fix_len_errors(input_value, items, index):
    v = SchemaValidator({'type': 'tuple-fix-len', 'items': items})
    with pytest.raises(ValidationError) as exc_info:
        assert v.validate_python(input_value)
    assert exc_info.value.errors() == [
        {
            'kind': 'int_parsing',
            'loc': [index],
            'message': 'Value must be a valid integer, unable to parse string as an integer',
            'input_value': 'wrong',
        }
    ]


@pytest.mark.parametrize(
    'items,input_value,expected',
    [
        ([{'type': 'int'}], [1, 2, 3], Err('Tuple must have exactly 1 item')),
        ([{'type': 'int'}, {'type': 'int'}], [1], Err('Tuple must have exactly 2 items')),
    ],
    ids=['input too long', 'input too short'],
)
def test_tuple_fix_len_input_and_schemas_len_mismatch(items, input_value, expected):
    v = SchemaValidator({'type': 'tuple-fix-len', 'items': items})
    with pytest.raises(ValidationError, match=re.escape(expected.message)):
        v.validate_python(input_value)


@pytest.mark.parametrize('items,expected', [([], Err('Missing schemas for tuple elements'))])
def test_tuple_fix_len_schema_error(items, expected):
    with pytest.raises(SchemaError, match=expected.message):
        SchemaValidator({'type': 'tuple-fix-len', 'items': items})


@pytest.mark.parametrize('input_value,expected', [((1, 2, 3), (1, 2, 3)), ([1, 2, 3], [1, 2, 3])])
def test_union_tuple_list(input_value, expected):
    v = SchemaValidator({'type': 'union', 'choices': [{'type': 'tuple-var-len'}, {'type': 'list'}]})
    assert v.validate_python(input_value) == expected


@pytest.mark.parametrize(
    'input_value,expected',
    [
        ((1, 2, 3), (1, 2, 3)),
        (('a', 'b', 'c'), ('a', 'b', 'c')),
        (('a', 1, 'c'), ('a', '1', 'c')),
        (
            [5],
            Err(
                '2 validation errors for union',
                errors=[
                    {
                        # first of all, not a tuple of ints ..
                        'kind': 'tuple_type',
                        'loc': ['tuple-var-len-int'],
                        'message': 'Value must be a valid tuple',
                        'input_value': [5],
                    },
                    # .. and not a tuple of strings, either
                    {
                        'kind': 'tuple_type',
                        'loc': ['tuple-var-len-str'],
                        'message': 'Value must be a valid tuple',
                        'input_value': [5],
                    },
                ],
            ),
        ),
    ],
)
def test_union_tuple_var_len(input_value, expected):
    v = SchemaValidator(
        {
            'type': 'union',
            'choices': [
                {'type': 'tuple-var-len', 'items': {'type': 'int'}, 'strict': True},
                {'type': 'tuple-var-len', 'items': {'type': 'str'}, 'strict': True},
            ],
        }
    )
    if isinstance(expected, Err):
        with pytest.raises(ValidationError, match=re.escape(expected.message)) as exc_info:
            v.validate_python(input_value)
        if expected.errors is not None:
            assert exc_info.value.errors() == expected.errors
    else:
        assert v.validate_python(input_value) == expected


@pytest.mark.parametrize(
    'input_value,expected',
    [
        ((1, 2, 3), (1, 2, 3)),
        (('a', 'b', 'c'), ('a', 'b', 'c')),
        (('a', 1, 'c'), ('a', '1', 'c')),
        (
            [5, '1', 1],
            Err(
                '2 validation errors for union',
                errors=[
                    {
                        'kind': 'tuple_type',
                        'loc': ['tuple-fix-len-3-items'],
                        'message': 'Value must be a valid tuple',
                        'input_value': [5, '1', 1],
                    },
                    {
                        'kind': 'tuple_type',
                        'loc': ['tuple-fix-len-3-items'],
                        'message': 'Value must be a valid tuple',
                        'input_value': [5, '1', 1],
                    },
                ],
            ),
        ),
    ],
)
def test_union_tuple_fix_len(input_value, expected):
    v = SchemaValidator(
        {
            'type': 'union',
            'choices': [
                {'type': 'tuple-fix-len', 'items': [{'type': 'int'}, {'type': 'int'}, {'type': 'int'}], 'strict': True},
                {'type': 'tuple-fix-len', 'items': [{'type': 'str'}, {'type': 'str'}, {'type': 'str'}], 'strict': True},
            ],
        }
    )
    if isinstance(expected, Err):
        with pytest.raises(ValidationError, match=re.escape(expected.message)) as exc_info:
            v.validate_python(input_value)
        if expected.errors is not None:
            assert exc_info.value.errors() == expected.errors
    else:
        assert v.validate_python(input_value) == expected


@pytest.mark.parametrize(
    'tuple_variant,items,expected',
    [
        ('tuple-var-len', {'type': 'mint'}, Err('Error building "tuple-var-len" validator')),
        ('tuple-fix-len', [{'type': 'mint'}], Err('Error building "tuple-fix-len" validator')),
    ],
)
def test_error_building_tuple_with_wrong_items(tuple_variant, items, expected):

    with pytest.raises(SchemaError, match=re.escape(expected.message)):
        SchemaValidator({'type': tuple_variant, 'items': items})


def test_tuple_fix_error():
    v = SchemaValidator({'type': 'tuple-fix-len', 'items': ['int', 'str']})
    with pytest.raises(ValidationError) as exc_info:
        v.validate_python([1])

    assert exc_info.value.errors() == [
        {
            'kind': 'tuple_length_mismatch',
            'loc': [],
            'message': 'Tuple must have exactly 2 items',
            'input_value': [1],
            'context': {'expected_length': 2, 'plural': 's'},
        }
    ]
