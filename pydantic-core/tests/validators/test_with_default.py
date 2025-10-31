import os
import platform
import sys
import weakref
from collections import deque
from dataclasses import dataclass
from typing import Any, Callable, Union, cast

import pytest
from pydantic_core import (
    ArgsKwargs,
    PydanticUndefined,
    PydanticUseDefault,
    SchemaError,
    SchemaValidator,
    Some,
    ValidationError,
    core_schema,
)
from pydantic_core._pydantic_core import SchemaSerializer

from ..conftest import PyAndJson, assert_gc


def test_typed_dict_default():
    v = SchemaValidator(
        core_schema.typed_dict_schema(
            fields={
                'x': core_schema.typed_dict_field(schema=core_schema.str_schema()),
                'y': core_schema.typed_dict_field(
                    schema=core_schema.with_default_schema(schema=core_schema.str_schema(), default='[default]')
                ),
            }
        )
    )
    assert v.validate_python({'x': 'x', 'y': 'y'}) == {'x': 'x', 'y': 'y'}
    assert v.validate_python({'x': 'x'}) == {'x': 'x', 'y': '[default]'}


def test_typed_dict_omit():
    v = SchemaValidator(
        core_schema.typed_dict_schema(
            fields={
                'x': core_schema.typed_dict_field(schema=core_schema.str_schema()),
                'y': core_schema.typed_dict_field(
                    schema=core_schema.with_default_schema(schema=core_schema.str_schema(), on_error='omit'),
                    required=False,
                ),
            }
        )
    )
    assert v.validate_python({'x': 'x', 'y': 'y'}) == {'x': 'x', 'y': 'y'}
    assert v.validate_python({'x': 'x'}) == {'x': 'x'}
    assert v.validate_python({'x': 'x', 'y': 42}) == {'x': 'x'}


def test_arguments():
    v = SchemaValidator(
        core_schema.arguments_schema(
            arguments=[
                {
                    'name': 'a',
                    'mode': 'positional_or_keyword',
                    'schema': core_schema.with_default_schema(
                        schema=core_schema.int_schema(), default_factory=lambda: 1
                    ),
                }
            ]
        )
    )
    assert v.validate_python({'a': 2}) == ((), {'a': 2})
    assert v.validate_python(ArgsKwargs((2,))) == ((2,), {})
    assert v.validate_python(ArgsKwargs((2,), {})) == ((2,), {})
    assert v.validate_python(()) == ((), {'a': 1})


def test_arguments_omit():
    with pytest.raises(SchemaError, match="Parameter 'a': omit_on_error cannot be used with arguments"):
        SchemaValidator(
            schema=core_schema.arguments_schema(
                arguments=[
                    {
                        'name': 'a',
                        'mode': 'positional_or_keyword',
                        'schema': core_schema.with_default_schema(
                            schema=core_schema.int_schema(), default=1, on_error='omit'
                        ),
                    }
                ]
            )
        )


@pytest.mark.parametrize(
    'input_value,expected', [([1, 2, 3], [1, 2, 3]), ([1, '2', 3], [1, 2, 3]), ([1, 'wrong', 3], [1, 3])]
)
def test_list_json(py_and_json: PyAndJson, input_value, expected):
    v = py_and_json(
        {'type': 'list', 'items_schema': {'type': 'default', 'schema': {'type': 'int'}, 'on_error': 'omit'}}
    )
    assert v.validate_test(input_value) == expected


@pytest.mark.parametrize(
    'input_value,expected',
    [
        ([1, '2', 3], [1, 2, 3]),
        ([1, 'wrong', 3], [1, 3]),
        ((1, '2', 3), [1, 2, 3]),
        ((1, 'wrong', 3), [1, 3]),
        (deque([1, '2', 3]), [1, 2, 3]),
        (deque([1, 'wrong', 3]), [1, 3]),
    ],
)
def test_list(input_value, expected):
    v = SchemaValidator(
        core_schema.list_schema(
            items_schema=core_schema.with_default_schema(schema=core_schema.int_schema(), on_error='omit')
        )
    )
    assert v.validate_python(input_value) == expected


@pytest.mark.parametrize(
    'input_value,expected',
    [
        ({1, '2', 3}, {1, 2, 3}),
        ([1, '2', 3], {1, 2, 3}),
        ([1, 'wrong', 3], {1, 3}),
        (deque([1, '2', 3]), {1, 2, 3}),
        (deque([1, 'wrong', 3]), {1, 3}),
    ],
)
def test_set(input_value, expected):
    v = SchemaValidator(
        core_schema.set_schema(
            items_schema=core_schema.with_default_schema(schema=core_schema.int_schema(), on_error='omit')
        )
    )
    assert v.validate_python(input_value) == expected


def test_dict_values(py_and_json: PyAndJson):
    v = py_and_json(
        {
            'type': 'dict',
            'keys_schema': {'type': 'str'},
            'values_schema': {'type': 'default', 'schema': {'type': 'int'}, 'on_error': 'omit'},
        }
    )
    assert v.validate_test({'a': 1, 'b': '2'}) == {'a': 1, 'b': 2}
    assert v.validate_test({'a': 1, 'b': 'wrong'}) == {'a': 1}
    assert v.validate_test({'a': 1, 'b': 'wrong', 'c': '3'}) == {'a': 1, 'c': 3}


def test_dict_keys():
    v = SchemaValidator(
        core_schema.dict_schema(
            keys_schema=core_schema.with_default_schema(schema=core_schema.int_schema(), on_error='omit'),
            values_schema=core_schema.str_schema(),
        )
    )
    assert v.validate_python({1: 'a', '2': 'b'}) == {1: 'a', 2: 'b'}
    assert v.validate_python({1: 'a', 'wrong': 'b'}) == {1: 'a'}
    assert v.validate_python({1: 'a', 'wrong': 'b', 3: 'c'}) == {1: 'a', 3: 'c'}


def test_tuple_variable(py_and_json: PyAndJson):
    v = py_and_json(
        {
            'type': 'tuple',
            'items_schema': [{'type': 'default', 'schema': {'type': 'int'}, 'on_error': 'omit'}],
            'variadic_item_index': 0,
        }
    )
    assert v.validate_python((1, 2, 3)) == (1, 2, 3)
    assert v.validate_python([1, '2', 3]) == (1, 2, 3)
    assert v.validate_python([1, 'wrong', 3]) == (1, 3)


def test_tuple_positional():
    v = SchemaValidator(
        core_schema.tuple_schema(
            items_schema=[
                core_schema.int_schema(),
                core_schema.with_default_schema(schema=core_schema.int_schema(), default=42),
            ]
        )
    )
    assert v.validate_python((1, '2')) == (1, 2)
    assert v.validate_python([1, '2']) == (1, 2)
    assert v.validate_json('[1, "2"]') == (1, 2)
    assert v.validate_python((1,)) == (1, 42)


def test_tuple_positional_omit():
    v = SchemaValidator(
        core_schema.tuple_schema(
            items_schema=[
                core_schema.int_schema(),
                core_schema.int_schema(),
                core_schema.with_default_schema(schema=core_schema.int_schema(), on_error='omit'),
            ],
            variadic_item_index=2,
        )
    )
    assert v.validate_python((1, '2')) == (1, 2)
    assert v.validate_python((1, '2', 3, '4')) == (1, 2, 3, 4)
    assert v.validate_python((1, '2', 'wrong', '4')) == (1, 2, 4)
    assert v.validate_python((1, '2', 3, 'x4')) == (1, 2, 3)
    assert v.validate_json('[1, "2", 3, "x4"]') == (1, 2, 3)


def test_on_error_default():
    v = SchemaValidator(core_schema.with_default_schema(schema=core_schema.int_schema(), default=2, on_error='default'))
    assert v.validate_python(42) == 42
    assert v.validate_python('42') == 42
    assert v.validate_python('wrong') == 2


def test_factory_runtime_error():
    def broken():
        raise RuntimeError('this is broken')

    v = SchemaValidator(
        core_schema.with_default_schema(schema=core_schema.int_schema(), on_error='default', default_factory=broken)
    )
    assert v.validate_python(42) == 42
    assert v.validate_python('42') == 42
    with pytest.raises(RuntimeError, match='this is broken'):
        v.validate_python('wrong')


def test_factory_missing_arg():
    def broken(x):
        return 7

    v = SchemaValidator(
        core_schema.with_default_schema(
            schema=core_schema.int_schema(),
            on_error='default',
            default_factory=broken,
            default_factory_takes_data=False,
        )
    )
    assert v.validate_python(42) == 42
    assert v.validate_python('42') == 42
    with pytest.raises(TypeError, match=r"broken\(\) missing 1 required positional argument: 'x'"):
        v.validate_python('wrong')


def test_typed_dict_error():
    v = SchemaValidator(
        core_schema.typed_dict_schema(
            fields={
                'x': core_schema.typed_dict_field(schema=core_schema.str_schema()),
                'y': core_schema.typed_dict_field(
                    schema=core_schema.with_default_schema(
                        schema=core_schema.str_schema(), default_factory=lambda y: y * 2
                    )
                ),
            }
        )
    )
    assert v.validate_python({'x': 'x', 'y': 'y'}) == {'x': 'x', 'y': 'y'}
    with pytest.raises(TypeError, match=r"<lambda>\(\) missing 1 required positional argument: 'y'"):
        v.validate_python({'x': 'x'})


def test_on_error_default_not_int():
    v = SchemaValidator(
        core_schema.with_default_schema(schema=core_schema.int_schema(), default=[1, 2, 3], on_error='default')
    )
    assert v.validate_python(42) == 42
    assert v.validate_python('42') == 42
    assert v.validate_python('wrong') == [1, 2, 3]


def test_on_error_default_factory():
    v = SchemaValidator(
        core_schema.with_default_schema(schema=core_schema.int_schema(), default_factory=lambda: 17, on_error='default')
    )
    assert v.validate_python(42) == 42
    assert v.validate_python('42') == 42
    assert v.validate_python('wrong') == 17


def test_on_error_omit():
    v = SchemaValidator(core_schema.with_default_schema(schema=core_schema.int_schema(), on_error='omit'))
    assert v.validate_python(42) == 42
    with pytest.raises(SchemaError, match='Uncaught Omit error, please check your usage of `default` validators.'):
        v.validate_python('wrong')


def test_on_error_wrong():
    with pytest.raises(SchemaError, match="'on_error = default' requires a `default` or `default_factory`"):
        SchemaValidator(core_schema.with_default_schema(schema=core_schema.int_schema(), on_error='default'))


def test_build_default_and_default_factory():
    with pytest.raises(SchemaError, match="'default' and 'default_factory' cannot be used together"):
        SchemaValidator(
            schema=core_schema.with_default_schema(
                schema=core_schema.int_schema(), default_factory=lambda: 1, default=2
            )
        )


def test_model_class():
    class MyModel:
        __slots__ = '__dict__', '__pydantic_fields_set__', '__pydantic_extra__', '__pydantic_private__'
        field_a: str
        field_b: int

    v = SchemaValidator(
        core_schema.model_schema(
            cls=MyModel,
            schema=core_schema.with_default_schema(
                schema=core_schema.model_fields_schema(
                    fields={
                        'field_a': core_schema.model_field(schema=core_schema.str_schema()),
                        'field_b': core_schema.model_field(schema=core_schema.int_schema()),
                    }
                ),
                default=({'field_a': '[default-a]', 'field_b': '[default-b]'}, None, set()),
                on_error='default',
            ),
        )
    )
    m = v.validate_python({'field_a': 'test', 'field_b': 12})
    assert isinstance(m, MyModel)
    assert m.field_a == 'test'
    assert m.field_b == 12
    assert m.__pydantic_fields_set__ == {'field_a', 'field_b'}
    m = v.validate_python({'field_a': 'test', 'field_b': 'wrong'})
    assert isinstance(m, MyModel)
    assert m.field_a == '[default-a]'
    assert m.field_b == '[default-b]'
    assert m.__pydantic_fields_set__ == set()


@pytest.mark.parametrize('config_validate_default', [True, False, None])
@pytest.mark.parametrize('schema_validate_default', [True, False, None])
@pytest.mark.parametrize(
    'inner_schema',
    [
        core_schema.no_info_after_validator_function(lambda x: x * 2, core_schema.int_schema()),
        core_schema.no_info_before_validator_function(lambda x: str(int(x) * 2), core_schema.int_schema()),
        core_schema.no_info_wrap_validator_function(lambda x, h: h(str(int(x) * 2)), core_schema.int_schema()),
        core_schema.no_info_wrap_validator_function(lambda x, h: h(x) * 2, core_schema.int_schema()),
    ],
    ids=['after', 'before', 'wrap-before', 'wrap-after'],
)
def test_validate_default(
    config_validate_default: Union[bool, None],
    schema_validate_default: Union[bool, None],
    inner_schema: core_schema.CoreSchema,
):
    if config_validate_default is not None:
        config = core_schema.CoreConfig(validate_default=config_validate_default)
    else:
        config = None
    v = SchemaValidator(
        core_schema.typed_dict_schema(
            {
                'x': core_schema.typed_dict_field(
                    core_schema.with_default_schema(
                        inner_schema, default='42', validate_default=schema_validate_default
                    )
                )
            },
            config=config,
        )
    )
    assert v.validate_python({'x': '2'}) == {'x': 4}
    expected = (
        84
        if (config_validate_default is True and schema_validate_default is not False or schema_validate_default is True)
        else '42'
    )
    assert v.validate_python({}) == {'x': expected}


def test_validate_default_factory():
    v = SchemaValidator(
        core_schema.tuple_positional_schema(
            [core_schema.with_default_schema(core_schema.int_schema(), default_factory=lambda: '42')]
        ),
        config=dict(validate_default=True),
    )
    assert v.validate_python(('2',)) == (2,)
    assert v.validate_python(()) == (42,)


def test_validate_default_error_tuple():
    v = SchemaValidator(
        core_schema.tuple_positional_schema(
            [core_schema.with_default_schema(core_schema.int_schema(), default='wrong', validate_default=True)]
        )
    )
    assert v.validate_python(('2',)) == (2,)
    with pytest.raises(ValidationError, match='Input should be a valid integer,') as exc_info:
        v.validate_python(())

    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'int_parsing',
            'loc': (0,),
            'msg': 'Input should be a valid integer, unable to parse string as an integer',
            'input': 'wrong',
        }
    ]


def test_validate_default_error_typed_dict():
    v = SchemaValidator(
        core_schema.typed_dict_schema(
            {
                'x': core_schema.typed_dict_field(
                    core_schema.with_default_schema(core_schema.int_schema(), default='xx', validate_default=True)
                )
            }
        )
    )
    assert v.validate_python({'x': '2'}) == {'x': 2}
    with pytest.raises(ValidationError, match='Input should be a valid integer,') as exc_info:
        v.validate_python({})

    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'int_parsing',
            'loc': ('x',),
            'msg': 'Input should be a valid integer, unable to parse string as an integer',
            'input': 'xx',
        }
    ]


def test_deepcopy_mutable_defaults():
    stored_empty_list = []
    stored_empty_dict = {}

    class Model:
        int_list_with_default: list[int] = stored_empty_list
        str_dict_with_default: dict[str, str] = stored_empty_dict

    v = SchemaValidator(
        core_schema.model_schema(
            cls=Model,
            schema=core_schema.model_fields_schema(
                fields={
                    'int_list_with_default': core_schema.model_field(
                        schema=core_schema.with_default_schema(
                            schema=core_schema.list_schema(items_schema=core_schema.int_schema()),
                            default=stored_empty_list,
                        )
                    ),
                    'str_dict_with_default': core_schema.model_field(
                        schema=core_schema.with_default_schema(
                            schema=core_schema.dict_schema(
                                keys_schema=core_schema.str_schema(), values_schema=core_schema.str_schema()
                            ),
                            default=stored_empty_dict,
                        )
                    ),
                }
            ),
        )
    )

    m1 = v.validate_python({})

    assert m1.int_list_with_default == []
    assert m1.str_dict_with_default == {}

    assert m1.int_list_with_default is not stored_empty_list
    assert m1.str_dict_with_default is not stored_empty_dict

    m1.int_list_with_default.append(1)
    m1.str_dict_with_default['a'] = 'abc'

    m2 = v.validate_python({})

    assert m2.int_list_with_default == []
    assert m2.str_dict_with_default == {}

    assert m2.int_list_with_default is not m1.int_list_with_default
    assert m2.str_dict_with_default is not m1.str_dict_with_default


def test_default_value() -> None:
    s = core_schema.with_default_schema(core_schema.list_schema(core_schema.int_schema()), default=[1, 2, 3])

    v = SchemaValidator(s)

    r = v.get_default_value()
    assert r is not None
    assert r.value == [1, 2, 3]


def test_default_value_validate_default() -> None:
    s = core_schema.with_default_schema(core_schema.list_schema(core_schema.int_schema()), default=['1', '2', '3'])

    v = SchemaValidator(s, config=core_schema.CoreConfig(validate_default=True))

    r = v.get_default_value()
    assert r is not None
    assert r.value == [1, 2, 3]


def test_default_value_validate_default_fail() -> None:
    s = core_schema.with_default_schema(core_schema.list_schema(core_schema.int_schema()), default=['a'])

    v = SchemaValidator(s, config=core_schema.CoreConfig(validate_default=True))

    with pytest.raises(ValidationError) as exc_info:
        v.get_default_value()
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'int_parsing',
            'loc': (0,),
            'msg': 'Input should be a valid integer, unable to parse string as an integer',
            'input': 'a',
        }
    ]


def test_default_value_validate_default_strict_pass() -> None:
    s = core_schema.with_default_schema(core_schema.list_schema(core_schema.int_schema()), default=[1, 2, 3])

    v = SchemaValidator(s, config=core_schema.CoreConfig(validate_default=True))

    r = v.get_default_value(strict=True)
    assert r is not None
    assert r.value == [1, 2, 3]


def test_default_value_validate_default_strict_fail() -> None:
    s = core_schema.with_default_schema(core_schema.list_schema(core_schema.int_schema()), default=['1'])

    v = SchemaValidator(s, config=core_schema.CoreConfig(validate_default=True))

    with pytest.raises(ValidationError) as exc_info:
        v.get_default_value(strict=True)
    assert exc_info.value.errors(include_url=False) == [
        {'type': 'int_type', 'loc': (0,), 'msg': 'Input should be a valid integer', 'input': '1'}
    ]


@pytest.mark.parametrize('validate_default', [True, False])
def test_no_default_value(validate_default: bool) -> None:
    s = core_schema.list_schema(core_schema.int_schema())
    v = SchemaValidator(s, config=core_schema.CoreConfig(validate_default=validate_default))

    assert v.get_default_value() is None


@pytest.mark.parametrize('validate_default', [True, False])
def test_some(validate_default: bool) -> None:
    def get_default() -> Union[Some[int], None]:
        s = core_schema.with_default_schema(core_schema.int_schema(), default=42)
        return SchemaValidator(s).get_default_value()

    res = get_default()
    assert res is not None
    assert res.value == 42
    assert repr(res) == 'Some(42)'


@pytest.mark.skipif(sys.version_info < (3, 10), reason='pattern matching was added in 3.10')
def test_some_pattern_match() -> None:
    code = """\
def f(v: Union[Some[Any], None]) -> str:
    match v:
        case Some(1):
            return 'case1'
        case Some(value=2):
            return 'case2'
        case Some(int(value)):
            return f'case3: {value}'
        case Some(value):
            return f'case4: {type(value).__name__}({value})'
        case None:
            return 'case5'
"""

    local_vars = {}
    exec(code, globals(), local_vars)
    f = cast(Callable[[Union[Some[Any], None]], str], local_vars['f'])

    res = f(SchemaValidator(core_schema.with_default_schema(core_schema.int_schema(), default=1)).get_default_value())
    assert res == 'case1'

    res = f(SchemaValidator(core_schema.with_default_schema(core_schema.int_schema(), default=2)).get_default_value())
    assert res == 'case2'

    res = f(SchemaValidator(core_schema.with_default_schema(core_schema.int_schema(), default=3)).get_default_value())
    assert res == 'case3: 3'

    res = f(
        SchemaValidator(
            schema=core_schema.with_default_schema(core_schema.int_schema(), default='4')
        ).get_default_value()
    )
    assert res == 'case4: str(4)'

    res = f(SchemaValidator(core_schema.int_schema()).get_default_value())
    assert res == 'case5'


def test_use_default_error() -> None:
    def val_func(v: Any, handler: core_schema.ValidatorFunctionWrapHandler) -> Any:
        if isinstance(v, str) and v == '':
            raise PydanticUseDefault
        return handler(v)

    validator = SchemaValidator(
        core_schema.with_default_schema(
            core_schema.no_info_wrap_validator_function(val_func, core_schema.int_schema()), default=10
        )
    )

    assert validator.validate_python('1') == 1
    assert validator.validate_python('') == 10

    # without a default value the error bubbles up
    # the error message is the same as the error message produced by PydanticOmit
    validator = SchemaValidator(
        core_schema.with_default_schema(core_schema.no_info_wrap_validator_function(val_func, core_schema.int_schema()))
    )
    with pytest.raises(
        SchemaError,
        match='Uncaught `PydanticUseDefault` exception: the error was raised in a field validator and no default value is available for that field.',
    ):
        validator.validate_python('')

    # same if there is no WithDefault validator
    validator = SchemaValidator(core_schema.no_info_wrap_validator_function(val_func, core_schema.int_schema()))
    with pytest.raises(
        SchemaError,
        match='Uncaught `PydanticUseDefault` exception: the error was raised in a field validator and no default value is available for that field.',
    ):
        validator.validate_python('')


@pytest.mark.xfail(
    condition=platform.python_implementation() == 'PyPy', reason='https://foss.heptapod.net/pypy/pypy/-/issues/3899'
)
@pytest.mark.skipif(platform.python_implementation() == 'GraalVM', reason='Cannot reliably trigger GC on GraalPy')
def test_leak_with_default():
    def fn():
        class Defaulted(int):
            @classmethod
            def _validator(cls, v, info):
                return Defaulted(v)

        schema = core_schema.with_info_plain_validator_function(Defaulted._validator)
        schema = core_schema.with_default_schema(schema, default=Defaulted(0))

        # If any of the Rust validators don't implement traversal properly,
        # there will be an undetectable cycle created by this assignment
        # which will keep Defaulted alive
        Defaulted.__pydantic_validator__ = SchemaValidator(schema)

        return Defaulted

    klass = fn()
    ref = weakref.ref(klass)
    assert ref() is not None

    del klass
    assert_gc(lambda: ref() is None)


validate_default_raises_examples = [
    (
        {},
        [
            {'type': 'assertion_error', 'loc': ('x',), 'msg': 'Assertion failed, ', 'input': None},
            {'type': 'assertion_error', 'loc': ('y',), 'msg': 'Assertion failed, ', 'input': None},
            {'type': 'missing', 'loc': ('z',), 'msg': 'Field required', 'input': {}},
        ],
    ),
    (
        {'z': 'some str'},
        [
            {'type': 'assertion_error', 'loc': ('x',), 'msg': 'Assertion failed, ', 'input': None},
            {'type': 'assertion_error', 'loc': ('y',), 'msg': 'Assertion failed, ', 'input': None},
        ],
    ),
    (
        {'x': None},
        [
            {'type': 'assertion_error', 'loc': ('x',), 'msg': 'Assertion failed, ', 'input': None},
            {'type': 'assertion_error', 'loc': ('y',), 'msg': 'Assertion failed, ', 'input': None},
            {'type': 'missing', 'loc': ('z',), 'msg': 'Field required', 'input': {'x': None}},
        ],
    ),
    (
        {'x': None, 'z': 'some str'},
        [
            {'type': 'assertion_error', 'loc': ('x',), 'msg': 'Assertion failed, ', 'input': None},
            {'type': 'assertion_error', 'loc': ('y',), 'msg': 'Assertion failed, ', 'input': None},
        ],
    ),
    (
        {'y': None},
        [
            {'type': 'assertion_error', 'loc': ('x',), 'msg': 'Assertion failed, ', 'input': None},
            {'type': 'assertion_error', 'loc': ('y',), 'msg': 'Assertion failed, ', 'input': None},
            {'type': 'missing', 'loc': ('z',), 'msg': 'Field required', 'input': {'y': None}},
        ],
    ),
    (
        {'y': None, 'z': 'some str'},
        [
            {'type': 'assertion_error', 'loc': ('x',), 'msg': 'Assertion failed, ', 'input': None},
            {'type': 'assertion_error', 'loc': ('y',), 'msg': 'Assertion failed, ', 'input': None},
        ],
    ),
    (
        {'x': None, 'y': None},
        [
            {'type': 'assertion_error', 'loc': ('x',), 'msg': 'Assertion failed, ', 'input': None},
            {'type': 'assertion_error', 'loc': ('y',), 'msg': 'Assertion failed, ', 'input': None},
            {'type': 'missing', 'loc': ('z',), 'msg': 'Field required', 'input': {'x': None, 'y': None}},
        ],
    ),
    (
        {'x': None, 'y': None, 'z': 'some str'},
        [
            {'type': 'assertion_error', 'loc': ('x',), 'msg': 'Assertion failed, ', 'input': None},
            {'type': 'assertion_error', 'loc': ('y',), 'msg': 'Assertion failed, ', 'input': None},
        ],
    ),
    (
        {'x': 1, 'y': None, 'z': 'some str'},
        [
            {'type': 'assertion_error', 'loc': ('x',), 'msg': 'Assertion failed, ', 'input': 1},
            {'type': 'assertion_error', 'loc': ('y',), 'msg': 'Assertion failed, ', 'input': None},
        ],
    ),
    (
        {'x': None, 'y': 1, 'z': 'some str'},
        [
            {'type': 'assertion_error', 'loc': ('x',), 'msg': 'Assertion failed, ', 'input': None},
            {'type': 'assertion_error', 'loc': ('y',), 'msg': 'Assertion failed, ', 'input': 1},
        ],
    ),
    (
        {'x': 1, 'y': 1, 'z': 'some str'},
        [
            {'type': 'assertion_error', 'loc': ('x',), 'msg': 'Assertion failed, ', 'input': 1},
            {'type': 'assertion_error', 'loc': ('y',), 'msg': 'Assertion failed, ', 'input': 1},
        ],
    ),
]


@pytest.mark.parametrize(
    'core_schema_constructor,field_constructor',
    [
        (core_schema.model_fields_schema, core_schema.model_field),
        (core_schema.typed_dict_schema, core_schema.typed_dict_field),
    ],
)
@pytest.mark.parametrize('input_value,expected', validate_default_raises_examples)
def test_validate_default_raises(
    core_schema_constructor: Union[core_schema.ModelFieldsSchema, core_schema.TypedDictSchema],
    field_constructor: Union[core_schema.model_field, core_schema.typed_dict_field],
    input_value: dict,
    expected: Any,
) -> None:
    def _raise(ex: Exception) -> None:
        raise ex()

    inner_schema = core_schema.no_info_after_validator_function(
        lambda x: _raise(AssertionError), core_schema.nullable_schema(core_schema.int_schema())
    )

    v = SchemaValidator(
        core_schema_constructor(
            {
                'x': field_constructor(
                    core_schema.with_default_schema(inner_schema, default=None, validate_default=True)
                ),
                'y': field_constructor(
                    core_schema.with_default_schema(inner_schema, default=None, validate_default=True)
                ),
                'z': field_constructor(core_schema.str_schema()),
            }
        )
    )

    with pytest.raises(ValidationError) as exc_info:
        v.validate_python(input_value)
        assert exc_info.value.errors(include_url=False, include_context=False) == expected


@pytest.mark.parametrize('input_value,expected', validate_default_raises_examples)
def test_validate_default_raises_dataclass(input_value: dict, expected: Any) -> None:
    def _raise(ex: Exception) -> None:
        raise ex()

    inner_schema = core_schema.no_info_after_validator_function(
        lambda x: _raise(AssertionError), core_schema.nullable_schema(core_schema.int_schema())
    )

    x = core_schema.dataclass_field(
        name='x', schema=core_schema.with_default_schema(inner_schema, default=None, validate_default=True)
    )
    y = core_schema.dataclass_field(
        name='y', schema=core_schema.with_default_schema(inner_schema, default=None, validate_default=True)
    )
    z = core_schema.dataclass_field(name='z', schema=core_schema.str_schema())

    v = SchemaValidator(core_schema.dataclass_args_schema('XYZ', [x, y, z]))

    with pytest.raises(ValidationError) as exc_info:
        v.validate_python(input_value)

    assert exc_info.value.errors(include_url=False, include_context=False) == expected


@pytest.fixture(params=['model', 'typed_dict', 'dataclass', 'arguments_v3'])
def container_schema_builder(
    request: pytest.FixtureRequest,
) -> Callable[[dict[str, core_schema.CoreSchema]], core_schema.CoreSchema]:
    if request.param == 'model':
        return lambda fields: core_schema.model_schema(
            cls=type('Test', (), {}),
            schema=core_schema.model_fields_schema(
                fields={k: core_schema.model_field(schema=v) for k, v in fields.items()},
            ),
        )
    elif request.param == 'typed_dict':
        return lambda fields: core_schema.typed_dict_schema(
            fields={k: core_schema.typed_dict_field(schema=v) for k, v in fields.items()}
        )
    elif request.param == 'dataclass':
        return lambda fields: core_schema.dataclass_schema(
            cls=dataclass(type('Test', (), {})),
            schema=core_schema.dataclass_args_schema(
                'Test',
                fields=[core_schema.dataclass_field(name=k, schema=v) for k, v in fields.items()],
            ),
            fields=[k for k in fields.keys()],
        )
    elif request.param == 'arguments_v3':
        # TODO: open an issue for this
        raise pytest.xfail('arguments v3 does not yet support default_factory_takes_data properly')
    else:
        raise ValueError(f'Unknown container type {request.param}')


def test_default_factory_not_called_if_existing_error(container_schema_builder, pydantic_version) -> None:
    schema = container_schema_builder(
        {
            'a': core_schema.int_schema(),
            'b': core_schema.with_default_schema(
                schema=core_schema.int_schema(), default_factory=lambda data: data['a'], default_factory_takes_data=True
            ),
        }
    )
    v = SchemaValidator(schema)
    with pytest.raises(ValidationError) as e:
        v.validate_python({'a': 'not_an_int'})

    assert e.value.errors(include_url=False) == [
        {
            'type': 'int_parsing',
            'loc': ('a',),
            'msg': 'Input should be a valid integer, unable to parse string as an integer',
            'input': 'not_an_int',
        },
        {
            'input': PydanticUndefined,
            'loc': ('b',),
            'msg': 'The default factory uses validated data, but at least one validation error occurred',
            'type': 'default_factory_not_called',
        },
    ]

    include_urls = os.environ.get('PYDANTIC_ERRORS_INCLUDE_URL', '1') != 'false'

    expected = (
        f"""2 validation errors for {v.title}
a
  Input should be a valid integer, unable to parse string as an integer [type=int_parsing, input_value='not_an_int', input_type=str]"""
        + (
            f"""
    For further information visit https://errors.pydantic.dev/{pydantic_version}/v/int_parsing"""
            if include_urls
            else ''
        )
        + """
b
  The default factory uses validated data, but at least one validation error occurred [type=default_factory_not_called]"""
        + (
            f"""
    For further information visit https://errors.pydantic.dev/{pydantic_version}/v/default_factory_not_called"""
            if include_urls
            else ''
        )
    )

    assert str(e.value) == expected

    # repeat with the first field being a default which validates incorrectly

    schema = container_schema_builder(
        {
            'a': core_schema.with_default_schema(
                schema=core_schema.int_schema(), default='not_an_int', validate_default=True
            ),
            'b': core_schema.with_default_schema(
                schema=core_schema.int_schema(), default_factory=lambda data: data['a'], default_factory_takes_data=True
            ),
        }
    )
    v = SchemaValidator(schema)
    with pytest.raises(ValidationError) as e:
        v.validate_python({})

    assert e.value.errors(include_url=False) == [
        {
            'type': 'int_parsing',
            'loc': ('a',),
            'msg': 'Input should be a valid integer, unable to parse string as an integer',
            'input': 'not_an_int',
        },
        {
            'input': PydanticUndefined,
            'loc': ('b',),
            'msg': 'The default factory uses validated data, but at least one validation error occurred',
            'type': 'default_factory_not_called',
        },
    ]

    assert str(e.value) == expected


def test_default_factory_not_called_union_ok(container_schema_builder) -> None:
    schema_fail = container_schema_builder(
        {
            'a': core_schema.none_schema(),
            'b': core_schema.with_default_schema(
                schema=core_schema.int_schema(),
                default_factory=lambda data: data['a'],
                default_factory_takes_data=True,
            ),
        }
    )

    schema_ok = container_schema_builder(
        {
            'a': core_schema.int_schema(),
            'b': core_schema.with_default_schema(
                schema=core_schema.int_schema(),
                default_factory=lambda data: data['a'] + 1,
                default_factory_takes_data=True,
            ),
            # this is used to show that this union member was selected
            'c': core_schema.with_default_schema(schema=core_schema.int_schema(), default=3),
        }
    )

    schema = core_schema.union_schema([schema_fail, schema_ok])

    v = SchemaValidator(schema)
    s = SchemaSerializer(schema)
    assert s.to_python(v.validate_python({'a': 1}), mode='json') == {'a': 1, 'b': 2, 'c': 3}


def test_default_validate_default_after_validator_field_name() -> None:
    class Model:
        pass

    field_name: str | None = None

    def val_func(value, info: core_schema.ValidationInfo):
        nonlocal field_name
        field_name = info.field_name
        return value

    schema = core_schema.model_schema(
        cls=Model,
        schema=core_schema.model_fields_schema(
            fields={
                'a': core_schema.model_field(
                    schema=core_schema.with_default_schema(
                        schema=core_schema.with_info_after_validator_function(
                            val_func,
                            schema=core_schema.str_schema(),
                        ),
                        default='default',
                    )
                )
            }
        ),
        config={'validate_default': True},
    )

    val = SchemaValidator(schema)
    val.validate_python({})

    assert field_name == 'a'
