import collections.abc
import re
from collections import deque
from dataclasses import dataclass
from typing import Any, Dict, Iterator, List, Union

import pytest
from dirty_equals import Contains, HasRepr, IsInstance, IsList, IsStr

from pydantic_core import SchemaValidator, ValidationError, core_schema

from ..conftest import Err, PyAndJson, infinite_generator


@pytest.mark.parametrize(
    'input_value,expected',
    [
        ([1, 2, 3], [1, 2, 3]),
        ([1, 2, '3'], [1, 2, 3]),
        (5, Err(r'Input should be a valid (list|array) \[type=list_type, input_value=5, input_type=int\]')),
        ('5', Err(r"Input should be a valid (list|array) \[type=list_type, input_value='5', input_type=str\]")),
    ],
    ids=repr,
)
def test_list_py_or_json(py_and_json: PyAndJson, input_value, expected):
    v = py_and_json({'type': 'list', 'items_schema': {'type': 'int'}})
    if isinstance(expected, Err):
        with pytest.raises(ValidationError, match=expected.message):
            v.validate_test(input_value)
    else:
        assert v.validate_test(input_value) == expected


def test_list_strict():
    v = SchemaValidator({'type': 'list', 'items_schema': {'type': 'int'}, 'strict': True})
    assert v.validate_python([1, 2, '33']) == [1, 2, 33]
    with pytest.raises(ValidationError) as exc_info:
        v.validate_python((1, 2, '33'))
    assert exc_info.value.errors(include_url=False) == [
        {'type': 'list_type', 'loc': (), 'msg': 'Input should be a valid list', 'input': (1, 2, '33')}
    ]


def test_list_no_copy():
    v = SchemaValidator({'type': 'list'})
    assert v.validate_python([1, 2, 3]) is not [1, 2, 3]


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
        ({1, 2, '3'}, IsList(1, 2, 3, check_order=False)),
        (gen_ints(), [1, 2, 3]),
        (frozenset({1, 2, '3'}), IsList(1, 2, 3, check_order=False)),
        ({1: 10, 2: 20, '3': '30'}.keys(), [1, 2, 3]),
        ({1: 10, 2: 20, '3': '30'}.values(), [10, 20, 30]),
        ({1: 10, 2: 20, '3': '30'}, Err('Input should be a valid list [type=list_type,')),
        ((x for x in [1, 2, '3']), [1, 2, 3]),
        ('456', Err("Input should be a valid list [type=list_type, input_value='456', input_type=str]")),
        (b'789', Err("Input should be a valid list [type=list_type, input_value=b'789', input_type=bytes]")),
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


def test_list_json():
    v = SchemaValidator({'type': 'list', 'items_schema': {'type': 'int'}})
    assert v.validate_json('[1, "2", 3]') == [1, 2, 3]

    with pytest.raises(ValidationError) as exc_info:
        v.validate_json('1')

    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {'type': 'list_type', 'loc': (), 'msg': 'Input should be a valid array', 'input': 1}
    ]


@pytest.mark.parametrize(
    'input_value,expected',
    [
        ([], []),
        ([1, '2', b'3'], [1, '2', b'3']),
        (frozenset([1, '2', b'3']), IsList(1, '2', b'3', check_order=False)),
        ((), []),
        ((1, '2', b'3'), [1, '2', b'3']),
        (deque([1, '2', b'3']), [1, '2', b'3']),
        ({1, '2', b'3'}, IsList(1, '2', b'3', check_order=False)),
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
    assert exc_info.value.errors(include_url=False) == [
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
        (
            {'max_length': 3},
            [1, 2, 3, 4, 5, 6, 7],
            Err('List should have at most 3 items after validation, not 7 [type=too_long,'),
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
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
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

    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'too_long',
            'loc': (),
            'msg': 'List should have at most 3 items after validation, not 4',
            'input': [1, 2, 3, 4],
            'ctx': {'field_type': 'List', 'max_length': 3, 'actual_length': 4},
        }
    ]


def test_list_function():
    def f(input_value, info):
        return input_value * 2

    v = SchemaValidator(
        {'type': 'list', 'items_schema': {'type': 'function-plain', 'function': {'type': 'general', 'function': f}}}
    )

    assert v.validate_python([1, 2, 3]) == [2, 4, 6]


def test_list_function_val_error():
    def f(input_value, info):
        raise ValueError(f'error {input_value}')

    v = SchemaValidator(
        {'type': 'list', 'items_schema': {'type': 'function-plain', 'function': {'type': 'general', 'function': f}}}
    )

    with pytest.raises(ValidationError) as exc_info:
        v.validate_python([1, 2])
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'value_error',
            'loc': (0,),
            'msg': 'Value error, error 1',
            'input': 1,
            'ctx': {'error': HasRepr(repr(ValueError('error 1')))},
        },
        {
            'type': 'value_error',
            'loc': (1,),
            'msg': 'Value error, error 2',
            'input': 2,
            'ctx': {'error': HasRepr(repr(ValueError('error 2')))},
        },
    ]


def test_list_function_internal_error():
    def f(input_value, info):
        raise RuntimeError(f'error {input_value}')

    v = SchemaValidator(
        {'type': 'list', 'items_schema': {'type': 'function-plain', 'function': {'type': 'general', 'function': f}}}
    )

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
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'iteration_error',
            'loc': (2,),
            'msg': 'Error iterating over object, error: RuntimeError: error',
            'input': HasRepr(IsStr(regex='<generator object test_generator_error.<locals>.gen at 0x[0-9a-fA-F]+>')),
            'ctx': {'error': 'RuntimeError: error'},
        }
    ]


@pytest.mark.parametrize(
    'input_value,items_schema,expected',
    [
        pytest.param(
            {1: 10, 2: 20, '3': '30'}.items(),
            {'type': 'tuple-variable', 'items_schema': {'type': 'any'}},
            [(1, 10), (2, 20), ('3', '30')],
            id='Tuple[Any, Any]',
        ),
        pytest.param(
            {1: 10, 2: 20, '3': '30'}.items(),
            {'type': 'tuple-variable', 'items_schema': {'type': 'int'}},
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

    v = SchemaValidator({'type': 'list', 'items_schema': {'type': items_schema}})
    assert v.validate_python(BadIter(True)) == [1]
    with pytest.raises(ValidationError) as exc_info:
        v.validate_python(BadIter(False))
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'iteration_error',
            'loc': (1,),
            'msg': 'Error iterating over object, error: RuntimeError: broken',
            'input': IsInstance(BadIter),
            'ctx': {'error': 'RuntimeError: broken'},
        }
    ]


@pytest.mark.parametrize('error_in_func', [True, False])
def test_max_length_fail_fast(error_in_func: bool) -> None:
    calls: list[int] = []

    def f(v: int) -> int:
        calls.append(v)
        if error_in_func:
            assert v < 10
        return v

    s = core_schema.list_schema(
        core_schema.no_info_after_validator_function(f, core_schema.int_schema()), max_length=10
    )

    v = SchemaValidator(s)

    data = list(range(15))

    with pytest.raises(ValidationError) as exc_info:
        v.validate_python(data)

    assert len(calls) <= 11, len(calls)  # we still run validation on the "extra" item

    assert exc_info.value.errors(include_url=False) == Contains(
        {
            'type': 'too_long',
            'loc': (),
            'msg': 'List should have at most 10 items after validation, not 11',
            'input': data,
            'ctx': {'field_type': 'List', 'max_length': 10, 'actual_length': 11},
        }
    )


class MySequence(collections.abc.Sequence):
    def __init__(self, data: List[Any]):
        self._data = data

    def __getitem__(self, index: int) -> Any:
        return self._data[index]

    def __len__(self):
        return len(self._data)

    def __repr__(self) -> str:
        return f'MySequence({repr(self._data)})'


class MyMapping(collections.abc.Mapping):
    def __init__(self, data: Dict[Any, Any]) -> None:
        self._data = data

    def __getitem__(self, key: Any) -> Any:
        return self._data[key]

    def __iter__(self) -> Iterator[Any]:
        return iter(self._data)

    def __len__(self) -> int:
        return len(self._data)

    def __repr__(self) -> str:
        return f'MyMapping({repr(self._data)})'


@dataclass
class ListInputTestCase:
    input: Any
    output: Union[Any, Err]
    strict: Union[bool, None] = None


LAX_MODE_INPUTS: List[Any] = [
    (1, 2, 3),
    frozenset((1, 2, 3)),
    set((1, 2, 3)),
    deque([1, 2, 3]),
    {1: 'a', 2: 'b', 3: 'c'}.keys(),
    {'a': 1, 'b': 2, 'c': 3}.values(),
    MySequence([1, 2, 3]),
    MyMapping({1: 'a', 2: 'b', 3: 'c'}).keys(),
    MyMapping({'a': 1, 'b': 2, 'c': 3}).values(),
    (x for x in [1, 2, 3]),
]


@pytest.mark.parametrize(
    'testcase',
    [
        *[ListInputTestCase([1, 2, 3], [1, 2, 3], strict) for strict in (True, False, None)],
        *[
            ListInputTestCase(inp, Err('Input should be a valid list [type=list_type,'), True)
            for inp in [*LAX_MODE_INPUTS, '123', b'123']
        ],
        *[ListInputTestCase(inp, [1, 2, 3], False) for inp in LAX_MODE_INPUTS],
        *[
            ListInputTestCase(inp, Err('Input should be a valid list [type=list_type,'), False)
            for inp in ['123', b'123', MyMapping({1: 'a', 2: 'b', 3: 'c'}), {1: 'a', 2: 'b', 3: 'c'}]
        ],
    ],
    ids=repr,
)
def test_list_allowed_inputs_python(testcase: ListInputTestCase):
    v = SchemaValidator(core_schema.list_schema(core_schema.int_schema(), strict=testcase.strict))
    if isinstance(testcase.output, Err):
        with pytest.raises(ValidationError, match=re.escape(testcase.output.message)):
            v.validate_python(testcase.input)
    else:
        output = v.validate_python(testcase.input)
        assert output == testcase.output
        assert output is not testcase.input


@pytest.mark.parametrize(
    'testcase',
    [
        ListInputTestCase({1: 1, 2: 2, 3: 3}.items(), Err('Input should be a valid list [type=list_type,'), True),
        ListInputTestCase(
            MyMapping({1: 1, 2: 2, 3: 3}).items(), Err('Input should be a valid list [type=list_type,'), True
        ),
        ListInputTestCase({1: 1, 2: 2, 3: 3}.items(), [(1, 1), (2, 2), (3, 3)], False),
        ListInputTestCase(MyMapping({1: 1, 2: 2, 3: 3}).items(), [(1, 1), (2, 2), (3, 3)], False),
    ],
    ids=repr,
)
def test_list_dict_items_input(testcase: ListInputTestCase) -> None:
    v = SchemaValidator(
        core_schema.list_schema(
            core_schema.tuple_positional_schema([core_schema.int_schema(), core_schema.int_schema()]),
            strict=testcase.strict,
        )
    )
    if isinstance(testcase.output, Err):
        with pytest.raises(ValidationError, match=re.escape(testcase.output.message)):
            v.validate_python(testcase.input)
    else:
        output = v.validate_python(testcase.input)
        assert output == testcase.output
        assert output is not testcase.input
