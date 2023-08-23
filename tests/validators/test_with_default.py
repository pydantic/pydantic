import gc
import platform
import sys
import weakref
from collections import deque
from typing import Any, Callable, Dict, List, Union, cast

import pytest

from pydantic_core import (
    ArgsKwargs,
    PydanticUseDefault,
    SchemaError,
    SchemaValidator,
    Some,
    ValidationError,
    core_schema,
)

from ..conftest import PyAndJson


def test_typed_dict_default():
    v = SchemaValidator(
        {
            'type': 'typed-dict',
            'fields': {
                'x': {'type': 'typed-dict-field', 'schema': {'type': 'str'}},
                'y': {
                    'type': 'typed-dict-field',
                    'schema': {'type': 'default', 'schema': {'type': 'str'}, 'default': '[default]'},
                },
            },
        }
    )
    assert v.validate_python({'x': 'x', 'y': 'y'}) == {'x': 'x', 'y': 'y'}
    assert v.validate_python({'x': 'x'}) == {'x': 'x', 'y': '[default]'}


def test_typed_dict_omit():
    v = SchemaValidator(
        {
            'type': 'typed-dict',
            'fields': {
                'x': {'type': 'typed-dict-field', 'schema': {'type': 'str'}},
                'y': {
                    'type': 'typed-dict-field',
                    'schema': {'type': 'default', 'schema': {'type': 'str'}, 'on_error': 'omit'},
                    'required': False,
                },
            },
        }
    )
    assert v.validate_python({'x': 'x', 'y': 'y'}) == {'x': 'x', 'y': 'y'}
    assert v.validate_python({'x': 'x'}) == {'x': 'x'}
    assert v.validate_python({'x': 'x', 'y': 42}) == {'x': 'x'}


def test_arguments():
    v = SchemaValidator(
        {
            'type': 'arguments',
            'arguments_schema': [
                {
                    'name': 'a',
                    'mode': 'positional_or_keyword',
                    'schema': {'type': 'default', 'schema': {'type': 'int'}, 'default_factory': lambda: 1},
                }
            ],
        }
    )
    assert v.validate_python({'a': 2}) == ((), {'a': 2})
    assert v.validate_python(ArgsKwargs((2,))) == ((2,), {})
    assert v.validate_python(ArgsKwargs((2,), {})) == ((2,), {})
    assert v.validate_python(()) == ((), {'a': 1})


def test_arguments_omit():
    with pytest.raises(SchemaError, match="Parameter 'a': omit_on_error cannot be used with arguments"):
        SchemaValidator(
            {
                'type': 'arguments',
                'arguments_schema': [
                    {
                        'name': 'a',
                        'mode': 'positional_or_keyword',
                        'schema': {'type': 'default', 'schema': {'type': 'int'}, 'default': 1, 'on_error': 'omit'},
                    }
                ],
            }
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
        {'type': 'list', 'items_schema': {'type': 'default', 'schema': {'type': 'int'}, 'on_error': 'omit'}}
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
        {'type': 'set', 'items_schema': {'type': 'default', 'schema': {'type': 'int'}, 'on_error': 'omit'}}
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
        {
            'type': 'dict',
            'keys_schema': {'type': 'default', 'schema': {'type': 'int'}, 'on_error': 'omit'},
            'values_schema': {'type': 'str'},
        }
    )
    assert v.validate_python({1: 'a', '2': 'b'}) == {1: 'a', 2: 'b'}
    assert v.validate_python({1: 'a', 'wrong': 'b'}) == {1: 'a'}
    assert v.validate_python({1: 'a', 'wrong': 'b', 3: 'c'}) == {1: 'a', 3: 'c'}


def test_tuple_variable(py_and_json: PyAndJson):
    v = py_and_json(
        {'type': 'tuple-variable', 'items_schema': {'type': 'default', 'schema': {'type': 'int'}, 'on_error': 'omit'}}
    )
    assert v.validate_python((1, 2, 3)) == (1, 2, 3)
    assert v.validate_python([1, '2', 3]) == (1, 2, 3)
    assert v.validate_python([1, 'wrong', 3]) == (1, 3)


def test_tuple_positional():
    v = SchemaValidator(
        {
            'type': 'tuple-positional',
            'items_schema': [{'type': 'int'}, {'type': 'default', 'schema': {'type': 'int'}, 'default': 42}],
        }
    )
    assert v.validate_python((1, '2')) == (1, 2)
    assert v.validate_python([1, '2']) == (1, 2)
    assert v.validate_json('[1, "2"]') == (1, 2)
    assert v.validate_python((1,)) == (1, 42)


def test_tuple_positional_omit():
    v = SchemaValidator(
        {
            'type': 'tuple-positional',
            'items_schema': [{'type': 'int'}, {'type': 'int'}],
            'extras_schema': {'type': 'default', 'schema': {'type': 'int'}, 'on_error': 'omit'},
        }
    )
    assert v.validate_python((1, '2')) == (1, 2)
    assert v.validate_python((1, '2', 3, '4')) == (1, 2, 3, 4)
    assert v.validate_python((1, '2', 'wrong', '4')) == (1, 2, 4)
    assert v.validate_python((1, '2', 3, 'x4')) == (1, 2, 3)
    assert v.validate_json('[1, "2", 3, "x4"]') == (1, 2, 3)


def test_on_error_default():
    v = SchemaValidator({'type': 'default', 'schema': {'type': 'int'}, 'default': 2, 'on_error': 'default'})
    assert v.validate_python(42) == 42
    assert v.validate_python('42') == 42
    assert v.validate_python('wrong') == 2


def test_factory_runtime_error():
    def broken():
        raise RuntimeError('this is broken')

    v = SchemaValidator(
        {'type': 'default', 'schema': {'type': 'int'}, 'on_error': 'default', 'default_factory': broken}
    )
    assert v.validate_python(42) == 42
    assert v.validate_python('42') == 42
    with pytest.raises(RuntimeError, match='this is broken'):
        v.validate_python('wrong')


def test_factory_type_error():
    def broken(x):
        return 7

    v = SchemaValidator(
        {'type': 'default', 'schema': {'type': 'int'}, 'on_error': 'default', 'default_factory': broken}
    )
    assert v.validate_python(42) == 42
    assert v.validate_python('42') == 42
    with pytest.raises(TypeError, match=r"broken\(\) missing 1 required positional argument: 'x'"):
        v.validate_python('wrong')


def test_typed_dict_error():
    v = SchemaValidator(
        {
            'type': 'typed-dict',
            'fields': {
                'x': {'type': 'typed-dict-field', 'schema': {'type': 'str'}},
                'y': {
                    'type': 'typed-dict-field',
                    'schema': {'type': 'default', 'schema': {'type': 'str'}, 'default_factory': lambda y: y * 2},
                },
            },
        }
    )
    assert v.validate_python({'x': 'x', 'y': 'y'}) == {'x': 'x', 'y': 'y'}
    with pytest.raises(TypeError, match=r"<lambda>\(\) missing 1 required positional argument: 'y'"):
        v.validate_python({'x': 'x'})


def test_on_error_default_not_int():
    v = SchemaValidator({'type': 'default', 'schema': {'type': 'int'}, 'default': [1, 2, 3], 'on_error': 'default'})
    assert v.validate_python(42) == 42
    assert v.validate_python('42') == 42
    assert v.validate_python('wrong') == [1, 2, 3]


def test_on_error_default_factory():
    v = SchemaValidator(
        {'type': 'default', 'schema': {'type': 'int'}, 'default_factory': lambda: 17, 'on_error': 'default'}
    )
    assert v.validate_python(42) == 42
    assert v.validate_python('42') == 42
    assert v.validate_python('wrong') == 17


def test_on_error_omit():
    v = SchemaValidator({'type': 'default', 'schema': {'type': 'int'}, 'on_error': 'omit'})
    assert v.validate_python(42) == 42
    with pytest.raises(SchemaError, match='Uncaught Omit error, please check your usage of `default` validators.'):
        v.validate_python('wrong')


def test_on_error_wrong():
    with pytest.raises(SchemaError, match="'on_error = default' requires a `default` or `default_factory`"):
        SchemaValidator({'type': 'default', 'schema': {'type': 'int'}, 'on_error': 'default'})


def test_build_default_and_default_factory():
    with pytest.raises(SchemaError, match="'default' and 'default_factory' cannot be used together"):
        SchemaValidator({'type': 'default', 'schema': {'type': 'int'}, 'default_factory': lambda: 1, 'default': 2})


def test_model_class():
    class MyModel:
        __slots__ = '__dict__', '__pydantic_fields_set__', '__pydantic_extra__', '__pydantic_private__'
        field_a: str
        field_b: int

    v = SchemaValidator(
        {
            'type': 'model',
            'cls': MyModel,
            'schema': {
                'type': 'default',
                'schema': {
                    'type': 'model-fields',
                    'fields': {
                        'field_a': {'type': 'model-field', 'schema': {'type': 'str'}},
                        'field_b': {'type': 'model-field', 'schema': {'type': 'int'}},
                    },
                },
                'default': ({'field_a': '[default-a]', 'field_b': '[default-b]'}, None, set()),
                'on_error': 'default',
            },
        }
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
        int_list_with_default: List[int] = stored_empty_list
        str_dict_with_default: Dict[str, str] = stored_empty_dict

    v = SchemaValidator(
        {
            'type': 'model',
            'cls': Model,
            'schema': {
                'type': 'model-fields',
                'fields': {
                    'int_list_with_default': {
                        'type': 'model-field',
                        'schema': {
                            'type': 'default',
                            'schema': {'type': 'list', 'items_schema': {'type': 'int'}},
                            'default': stored_empty_list,
                        },
                    },
                    'str_dict_with_default': {
                        'type': 'model-field',
                        'schema': {
                            'type': 'default',
                            'schema': {
                                'type': 'dict',
                                'keys_schema': {'type': 'str'},
                                'values_schema': {'type': 'str'},
                            },
                            'default': stored_empty_dict,
                        },
                    },
                },
            },
        }
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

    v = SchemaValidator(s, core_schema.CoreConfig(validate_default=True))

    r = v.get_default_value()
    assert r is not None
    assert r.value == [1, 2, 3]


def test_default_value_validate_default_fail() -> None:
    s = core_schema.with_default_schema(core_schema.list_schema(core_schema.int_schema()), default=['a'])

    v = SchemaValidator(s, core_schema.CoreConfig(validate_default=True))

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

    v = SchemaValidator(s, core_schema.CoreConfig(validate_default=True))

    r = v.get_default_value(strict=True)
    assert r is not None
    assert r.value == [1, 2, 3]


def test_default_value_validate_default_strict_fail() -> None:
    s = core_schema.with_default_schema(core_schema.list_schema(core_schema.int_schema()), default=['1'])

    v = SchemaValidator(s, core_schema.CoreConfig(validate_default=True))

    with pytest.raises(ValidationError) as exc_info:
        v.get_default_value(strict=True)
    assert exc_info.value.errors(include_url=False) == [
        {'type': 'int_type', 'loc': (0,), 'msg': 'Input should be a valid integer', 'input': '1'}
    ]


@pytest.mark.parametrize('validate_default', [True, False])
def test_no_default_value(validate_default: bool) -> None:
    s = core_schema.list_schema(core_schema.int_schema())
    v = SchemaValidator(s, core_schema.CoreConfig(validate_default=validate_default))

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

    res = f(SchemaValidator(core_schema.with_default_schema(core_schema.int_schema(), default='4')).get_default_value())
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
    with pytest.raises(SchemaError, match='Uncaught UseDefault error, please check your usage of `default` validators'):
        validator.validate_python('')

    # same if there is no WithDefault validator
    validator = SchemaValidator(core_schema.no_info_wrap_validator_function(val_func, core_schema.int_schema()))
    with pytest.raises(SchemaError, match='Uncaught UseDefault error, please check your usage of `default` validators'):
        validator.validate_python('')


@pytest.mark.xfail(
    condition=platform.python_implementation() == 'PyPy', reason='https://foss.heptapod.net/pypy/pypy/-/issues/3899'
)
def test_leak_with_default():
    def fn():
        class Defaulted(int):
            @classmethod
            def _validator(cls, v, info):
                return Defaulted(v)

        schema = core_schema.general_plain_validator_function(Defaulted._validator)
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
    gc.collect(0)
    gc.collect(1)
    gc.collect(2)
    gc.collect()

    assert ref() is None
