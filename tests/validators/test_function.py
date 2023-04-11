import platform
import re
from copy import deepcopy
from typing import Any, Dict, Type, Union

import pytest

from pydantic_core import SchemaError, SchemaValidator, ValidationError, core_schema

from ..conftest import plain_repr


def deepcopy_info(info: Union[core_schema.ValidationInfo, core_schema.FieldValidationInfo]) -> Dict[str, Any]:
    return {
        'context': deepcopy(info.context),
        'data': deepcopy(getattr(info, 'data', None)),
        'field_name': deepcopy(getattr(info, 'field_name', None)),
        'config': deepcopy(info.config),
    }


def test_function_before():
    def f(input_value, _info):
        return input_value + ' Changed'

    v = SchemaValidator(
        {'type': 'function-before', 'function': {'type': 'general', 'function': f}, 'schema': {'type': 'str'}}
    )

    assert v.validate_python('input value') == 'input value Changed'


def test_function_before_no_info():
    def f(input_value):
        return input_value + ' Changed'

    v = SchemaValidator(
        {'type': 'function-before', 'function': {'type': 'no-info', 'function': f}, 'schema': {'type': 'str'}}
    )

    assert v.validate_python('input value') == 'input value Changed'


def test_function_before_raise():
    def f(input_value, info):
        raise ValueError('foobar')

    v = SchemaValidator(
        {'type': 'function-before', 'function': {'type': 'general', 'function': f}, 'schema': {'type': 'str'}}
    )

    with pytest.raises(ValidationError) as exc_info:
        assert v.validate_python('input value') == 'input value Changed'
    # debug(str(exc_info.value))
    assert exc_info.value.errors() == [
        {
            'type': 'value_error',
            'loc': (),
            'msg': 'Value error, foobar',
            'input': 'input value',
            'ctx': {'error': 'foobar'},
        }
    ]


def test_function_before_error():
    def my_function(input_value, info):
        return input_value + 'x'

    v = SchemaValidator(
        {
            'type': 'function-before',
            'function': {'type': 'general', 'function': my_function},
            'schema': {'type': 'str', 'max_length': 5},
        }
    )

    assert v.validate_python('1234') == '1234x'
    with pytest.raises(ValidationError) as exc_info:
        v.validate_python('12345')
    assert exc_info.value.errors() == [
        {
            'type': 'string_too_long',
            'loc': (),
            'msg': 'String should have at most 5 characters',
            'input': '12345x',
            'ctx': {'max_length': 5},
        }
    ]
    assert repr(exc_info.value).startswith('1 validation error for function-before[my_function(), constrained-str]\n')


def test_function_before_error_model():
    def f(input_value, info):
        if 'my_field' in input_value:
            input_value['my_field'] += 'x'
        return input_value

    v = SchemaValidator(
        {
            'type': 'function-before',
            'function': {'type': 'general', 'function': f},
            'schema': {
                'type': 'typed-dict',
                'fields': {'my_field': {'type': 'typed-dict-field', 'schema': {'type': 'str', 'max_length': 5}}},
            },
        }
    )

    assert v.validate_python({'my_field': '1234'}) == {'my_field': '1234x'}
    with pytest.raises(ValidationError) as exc_info:
        v.validate_python({'my_field': '12345'})
    assert exc_info.value.errors() == [
        {
            'type': 'string_too_long',
            'loc': ('my_field',),
            'msg': 'String should have at most 5 characters',
            'input': '12345x',
            'ctx': {'max_length': 5},
        }
    ]


@pytest.mark.parametrize(
    'config,kwargs,expected_repr',
    [
        (None, {}, 'ValidationInfo(config=None, context=None)'),
        (None, {'context': {1: 2}}, 'ValidationInfo(config=None, context={1: 2})'),
        (None, {'context': None}, 'ValidationInfo(config=None, context=None)'),
        ({'title': 'hello'}, {}, "ValidationInfo(config={'title': 'hello'}, context=None)"),
    ],
)
def test_val_info_repr(config, kwargs, expected_repr):
    def f(input_value, info: core_schema.ValidationInfo):
        assert repr(info) == expected_repr
        assert str(info) == expected_repr
        return input_value

    v = SchemaValidator(
        {'type': 'function-before', 'function': {'type': 'general', 'function': f}, 'schema': {'type': 'str'}}, config
    )

    assert v.validate_python('input value', **kwargs) == 'input value'


def test_function_wrap():
    def f(input_value, validator, info):
        return validator(input_value=input_value) + ' Changed'

    v = SchemaValidator(
        {'type': 'function-wrap', 'function': {'type': 'general', 'function': f}, 'schema': {'type': 'str'}}
    )

    assert v.validate_python('input value') == 'input value Changed'


def test_function_wrap_no_info():
    def f(input_value, validator):
        return validator(input_value=input_value) + ' Changed'

    v = SchemaValidator(
        {'type': 'function-wrap', 'function': {'type': 'no-info', 'function': f}, 'schema': {'type': 'str'}}
    )

    assert v.validate_python('input value') == 'input value Changed'


def test_function_wrap_repr():
    def f(input_value, validator, info):
        assert repr(validator) == str(validator)
        return plain_repr(validator)

    v = SchemaValidator(
        {'type': 'function-wrap', 'function': {'type': 'general', 'function': f}, 'schema': {'type': 'str'}}
    )

    assert v.validate_python('input value') == 'ValidatorCallable(Str(StrValidator{strict:false}))'


def test_function_wrap_str():
    def f(input_value, validator, info):
        return plain_repr(validator)

    v = SchemaValidator(
        {'type': 'function-wrap', 'function': {'type': 'general', 'function': f}, 'schema': {'type': 'str'}}
    )

    assert v.validate_python('input value') == 'ValidatorCallable(Str(StrValidator{strict:false}))'


def test_function_wrap_not_callable():
    with pytest.raises(SchemaError, match='function-wrap.function.typed-dict.function\n  Input should be callable'):
        SchemaValidator(
            {'type': 'function-wrap', 'function': {'type': 'general', 'function': []}, 'schema': {'type': 'str'}}
        )

    with pytest.raises(SchemaError, match='function-wrap.function\n  Field required'):
        SchemaValidator({'type': 'function-wrap', 'schema': {'type': 'str'}})


def test_wrap_error():
    def f(input_value, validator, info):
        try:
            return validator(input_value) * 2
        except ValidationError as e:
            assert e.title == 'ValidatorCallable'
            assert str(e).startswith('1 validation error for ValidatorCallable\n')
            raise e

    v = SchemaValidator(
        {'type': 'function-wrap', 'function': {'type': 'general', 'function': f}, 'schema': {'type': 'int'}}
    )

    assert v.validate_python('42') == 84
    with pytest.raises(ValidationError) as exc_info:
        v.validate_python('wrong')
    assert exc_info.value.errors() == [
        {
            'type': 'int_parsing',
            'loc': (),
            'msg': 'Input should be a valid integer, unable to parse string as an integer',
            'input': 'wrong',
        }
    ]


def test_function_wrap_location():
    def f(input_value, validator, info):
        return validator(input_value, outer_location='foo') + 2

    v = SchemaValidator(
        {'type': 'function-wrap', 'function': {'type': 'general', 'function': f}, 'schema': {'type': 'int'}}
    )

    assert v.validate_python(4) == 6
    with pytest.raises(ValidationError) as exc_info:
        v.validate_python('wrong')
    # insert_assert(exc_info.value.errors())
    assert exc_info.value.errors() == [
        {
            'type': 'int_parsing',
            'loc': ('foo',),
            'msg': 'Input should be a valid integer, unable to parse string as an integer',
            'input': 'wrong',
        }
    ]


def test_function_wrap_invalid_location():
    def f(input_value, validator, info):
        return validator(input_value, ('4',)) + 2

    v = SchemaValidator(
        {'type': 'function-wrap', 'function': {'type': 'general', 'function': f}, 'schema': {'type': 'int'}}
    )

    with pytest.raises(TypeError, match='^outer_location must be a str or int$'):
        v.validate_python(4)


def test_function_after():
    def f(input_value, _info):
        return input_value + ' Changed'

    v = SchemaValidator(
        {'type': 'function-after', 'function': {'type': 'general', 'function': f}, 'schema': {'type': 'str'}}
    )

    assert v.validate_python('input value') == 'input value Changed'


def test_function_no_info():
    def f(input_value):
        return input_value + ' Changed'

    v = SchemaValidator(
        {'type': 'function-after', 'function': {'type': 'no-info', 'function': f}, 'schema': {'type': 'str'}}
    )

    assert v.validate_python('input value') == 'input value Changed'


def test_function_after_raise():
    def f(input_value, info):
        raise ValueError('foobar')

    v = SchemaValidator(
        {'type': 'function-after', 'function': {'type': 'general', 'function': f}, 'schema': {'type': 'str'}}
    )

    with pytest.raises(ValidationError) as exc_info:
        assert v.validate_python('input value') == 'input value Changed'
    # debug(str(exc_info.value))
    assert exc_info.value.errors() == [
        {
            'type': 'value_error',
            'loc': (),
            'msg': 'Value error, foobar',
            'input': 'input value',
            'ctx': {'error': 'foobar'},
        }
    ]


def test_function_after_config():
    f_kwargs = None

    def f(input_value, info):
        nonlocal f_kwargs
        f_kwargs = deepcopy_info(info)
        return input_value + ' Changed'

    v = SchemaValidator(
        {
            'type': 'typed-dict',
            'fields': {
                'test_field': {
                    'type': 'typed-dict-field',
                    'schema': {
                        'type': 'function-after',
                        'function': {'type': 'field', 'function': f},
                        'schema': {'type': 'str'},
                    },
                }
            },
        },
        {'config_choose_priority': 2},
    )

    assert v.validate_python({'test_field': b'321'}) == {'test_field': '321 Changed'}
    assert f_kwargs == {
        'data': {},
        'config': {'config_choose_priority': 2},
        'context': None,
        'field_name': 'test_field',
    }


def test_config_no_model():
    f_kwargs = None

    def f(input_value, info: core_schema.ValidationInfo):
        nonlocal f_kwargs
        f_kwargs = deepcopy_info(info)
        return input_value + ' Changed'

    v = SchemaValidator(
        {'type': 'function-after', 'function': {'type': 'general', 'function': f}, 'schema': {'type': 'str'}}
    )

    assert v.validate_python(b'abc') == 'abc Changed'
    assert f_kwargs == {'data': None, 'config': None, 'context': None, 'field_name': None}


def test_function_plain():
    def f(input_value, _info):
        return input_value * 2

    v = SchemaValidator({'type': 'function-plain', 'function': {'type': 'general', 'function': f}})

    assert v.validate_python(1) == 2
    assert v.validate_python('x') == 'xx'


def test_function_plain_no_info():
    def f(input_value):
        return input_value * 2

    v = SchemaValidator({'type': 'function-plain', 'function': {'type': 'no-info', 'function': f}})

    assert v.validate_python(1) == 2
    assert v.validate_python('x') == 'xx'


def test_plain_with_schema():
    with pytest.raises(SchemaError, match='function-plain.schema\n  Extra inputs are not permitted'):
        SchemaValidator(
            {
                'type': 'function-plain',
                'function': {'type': 'general', 'function': lambda x: x},
                'schema': {'type': 'str'},
            }
        )


def test_validate_assignment():
    def f(input_value, info):
        input_value['more'] = 'foobar'
        return input_value

    v = SchemaValidator(
        {
            'type': 'function-after',
            'function': {'type': 'general', 'function': f},
            'schema': {
                'type': 'typed-dict',
                'fields': {'field_a': {'type': 'typed-dict-field', 'schema': {'type': 'str'}}},
            },
        }
    )

    m = {'field_a': 'test', 'more': 'foobar'}
    assert v.validate_python({'field_a': 'test'}) == m
    assert v.validate_assignment(m, 'field_a', b'abc') == {'field_a': 'abc', 'more': 'foobar'}


def test_function_wrong_sig():
    def f(input_value):
        return input_value + ' Changed'

    v = SchemaValidator(
        {'type': 'function-before', 'function': {'type': 'general', 'function': f}, 'schema': {'type': 'str'}}
    )

    # exception messages differ between python and pypy
    if platform.python_implementation() == 'PyPy':
        error_message = 'f() takes 1 positional argument but 2 were given'
    else:
        error_message = 'f() takes 1 positional argument but 2 were given'

    with pytest.raises(TypeError, match=re.escape(error_message)):
        v.validate_python('input value')


def test_class_with_validator():
    class Foobar:
        a: int

        def __init__(self, a):
            self.a = a

        @classmethod
        def __validate__(cls, input_value, info):
            return Foobar(input_value * 2)

    v = SchemaValidator(
        {
            'type': 'function-after',
            'function': {'type': 'general', 'function': Foobar.__validate__},
            'schema': {'type': 'str'},
        }
    )

    f = v.validate_python('foo')
    assert isinstance(f, Foobar)
    assert f.a == 'foofoo'

    f = v.validate_python(b'a')
    assert isinstance(f, Foobar)
    assert f.a == 'aa'

    with pytest.raises(ValidationError) as exc_info:
        v.validate_python(True)

    assert exc_info.value.errors() == [
        {'type': 'string_type', 'loc': (), 'msg': 'Input should be a valid string', 'input': True}
    ]


def test_raise_assertion_error():
    def f(input_value, info):
        raise AssertionError('foobar')

    v = SchemaValidator(
        {'type': 'function-before', 'function': {'type': 'general', 'function': f}, 'schema': {'type': 'str'}}
    )

    with pytest.raises(ValidationError) as exc_info:
        v.validate_python('input value')

    assert exc_info.value.errors() == [
        {
            'type': 'assertion_error',
            'loc': (),
            'msg': 'Assertion failed, foobar',
            'input': 'input value',
            'ctx': {'error': 'foobar'},
        }
    ]


def test_raise_assertion_error_plain():
    def f(input_value, info):
        raise AssertionError

    v = SchemaValidator(
        {'type': 'function-before', 'function': {'type': 'general', 'function': f}, 'schema': {'type': 'str'}}
    )

    with pytest.raises(ValidationError) as exc_info:
        v.validate_python('input value')

    assert exc_info.value.errors() == [
        {
            'type': 'assertion_error',
            'loc': (),
            'msg': 'Assertion failed, Unknown error',
            'input': 'input value',
            'ctx': {'error': 'Unknown error'},
        }
    ]


@pytest.mark.parametrize('base_error', [ValueError, AssertionError])
def test_error_with_error(base_error: Type[Exception]):
    class MyError(base_error):
        def __str__(self):
            raise RuntimeError('internal error')

    def f(input_value, info):
        raise MyError()

    v = SchemaValidator(
        {'type': 'function-before', 'function': {'type': 'general', 'function': f}, 'schema': {'type': 'str'}}
    )

    with pytest.raises(RuntimeError, match='internal error'):
        v.validate_python('input value')


def test_raise_type_error():
    def f(input_value, info):
        raise TypeError('foobar')

    v = SchemaValidator(
        {'type': 'function-before', 'function': {'type': 'general', 'function': f}, 'schema': {'type': 'str'}}
    )

    with pytest.raises(TypeError, match='^foobar$'):
        v.validate_python('input value')


def test_model_field_before_validator() -> None:
    class Model:
        x: str

        def __init__(self, **kwargs: Any) -> None:
            self.__dict__.update(kwargs)

    def f(input_value: Any, info: core_schema.FieldValidationInfo) -> Any:
        assert info.field_name == 'x'
        assert info.data == {}
        assert repr(info) == "ValidationInfo(config=None, context=None, data={}, field_name='x')"
        assert str(info) == "ValidationInfo(config=None, context=None, data={}, field_name='x')"
        assert isinstance(input_value, bytes)
        return f'input: {input_value.decode()}'

    v = SchemaValidator(
        core_schema.model_schema(
            Model,
            core_schema.typed_dict_schema(
                {
                    'x': core_schema.typed_dict_field(
                        core_schema.field_before_validator_function(f, core_schema.str_schema())
                    )
                }
            ),
        )
    )

    assert v.validate_python({'x': b'foo'}).x == 'input: foo'


def test_model_field_after_validator() -> None:
    class Model:
        x: str

        def __init__(self, **kwargs: Any) -> None:
            self.__dict__.update(kwargs)

    def f(input_value: str, info: core_schema.FieldValidationInfo) -> Any:
        assert info.field_name == 'x'
        assert info.data == {}
        assert isinstance(input_value, str)
        return f'input: {input_value}'

    v = SchemaValidator(
        core_schema.model_schema(
            Model,
            core_schema.typed_dict_schema(
                {
                    'x': core_schema.typed_dict_field(
                        core_schema.field_after_validator_function(f, core_schema.str_schema())
                    )
                }
            ),
        )
    )

    assert v.validate_python({'x': b'foo'}).x == 'input: foo'


def test_model_field_plain_validator() -> None:
    class Model:
        x: str

        def __init__(self, **kwargs: Any) -> None:
            self.__dict__.update(kwargs)

    def f(input_value: Any, info: core_schema.FieldValidationInfo) -> Any:
        assert info.field_name == 'x'
        assert info.data == {}
        assert isinstance(input_value, bytes)
        return f'input: {input_value.decode()}'

    v = SchemaValidator(
        core_schema.model_schema(
            Model,
            core_schema.typed_dict_schema(
                {'x': core_schema.typed_dict_field(core_schema.field_plain_validator_function(f))}
            ),
        )
    )

    assert v.validate_python({'x': b'foo'}).x == 'input: foo'


def test_model_field_wrap_validator() -> None:
    class Model:
        x: str

        def __init__(self, **kwargs: Any) -> None:
            self.__dict__.update(kwargs)

    def f(
        input_value: Any, val: core_schema.ValidatorFunctionWrapHandler, info: core_schema.FieldValidationInfo
    ) -> Any:
        assert info.field_name == 'x'
        assert info.data == {}
        assert isinstance(input_value, bytes)
        return f'input: {val(input_value)}'

    v = SchemaValidator(
        core_schema.model_schema(
            Model,
            core_schema.typed_dict_schema(
                {
                    'x': core_schema.typed_dict_field(
                        core_schema.field_wrap_validator_function(f, core_schema.str_schema())
                    )
                }
            ),
        )
    )

    assert v.validate_python({'x': b'foo'}).x == 'input: foo'


def check_that_info_has_no_model_data(info: core_schema.ValidationInfo) -> None:
    with pytest.raises(AttributeError, match="No attribute named 'field_name'"):
        info.field_name  # type: ignore[attr-defined]
    with pytest.raises(AttributeError, match="No attribute named 'data'"):
        info.data  # type: ignore[attr-defined]
    assert not hasattr(info, 'field_name')
    assert not hasattr(info, 'data')


def test_non_model_field_before_validator_tries_to_access_field_info() -> None:
    class Model:
        x: str

        def __init__(self, **kwargs: Any) -> None:
            self.__dict__.update(kwargs)

    def f(input_value: Any, info: core_schema.ValidationInfo) -> Any:
        check_that_info_has_no_model_data(info)
        assert isinstance(input_value, bytes)
        return f'input: {input_value.decode()}'

    v = SchemaValidator(
        core_schema.model_schema(
            Model,
            core_schema.typed_dict_schema(
                {
                    'x': core_schema.typed_dict_field(
                        core_schema.general_before_validator_function(f, core_schema.str_schema())
                    )
                }
            ),
        )
    )

    assert v.validate_python({'x': b'foo'}).x == 'input: foo'


def test_non_model_field_after_validator_tries_to_access_field_info() -> None:
    class Model:
        x: str

        def __init__(self, **kwargs: Any) -> None:
            self.__dict__.update(kwargs)

    def f(input_value: Any, info: core_schema.ValidationInfo) -> Any:
        check_that_info_has_no_model_data(info)
        return f'input: {input_value}'

    v = SchemaValidator(
        core_schema.model_schema(
            Model,
            core_schema.typed_dict_schema(
                {
                    'x': core_schema.typed_dict_field(
                        core_schema.general_after_validator_function(f, core_schema.str_schema())
                    )
                }
            ),
        )
    )

    assert v.validate_python({'x': b'foo'}).x == 'input: foo'


def test_non_model_field_plain_validator_tries_to_access_field_info() -> None:
    class Model:
        x: str

        def __init__(self, **kwargs: Any) -> None:
            self.__dict__.update(kwargs)

    def f(input_value: Any, info: core_schema.ValidationInfo) -> Any:
        check_that_info_has_no_model_data(info)
        assert isinstance(input_value, bytes)
        return f'input: {input_value.decode()}'

    v = SchemaValidator(
        core_schema.model_schema(
            Model,
            core_schema.typed_dict_schema(
                {'x': core_schema.typed_dict_field(core_schema.general_plain_validator_function(f))}
            ),
        )
    )

    assert v.validate_python({'x': b'foo'}).x == 'input: foo'


def test_non_model_field_wrap_validator_tries_to_access_field_info() -> None:
    class Model:
        x: str

        def __init__(self, **kwargs: Any) -> None:
            self.__dict__.update(kwargs)

    def f(input_value: Any, val: core_schema.ValidatorFunctionWrapHandler, info: core_schema.ValidationInfo) -> Any:
        check_that_info_has_no_model_data(info)
        return f'input: {val(input_value)}'

    v = SchemaValidator(
        core_schema.model_schema(
            Model,
            core_schema.typed_dict_schema(
                {
                    'x': core_schema.typed_dict_field(
                        core_schema.general_wrap_validator_function(f, core_schema.str_schema())
                    )
                }
            ),
        )
    )

    assert v.validate_python({'x': b'foo'}).x == 'input: foo'


def test_method_function_no_model():
    def f(*args: Any, **kwargs: Any) -> Any:  # pragma: no cover
        raise AssertionError('Should not be called')

    v = SchemaValidator({'type': 'function-plain', 'function': {'type': 'field', 'function': f}})

    with pytest.raises(
        RuntimeError,
        match='This validator expected to be run inside the context of a model field but no model field was found',
    ):
        v.validate_python(123)


def test_typed_dict_data() -> None:
    info_stuff = None

    def f(input_value: Any, info: core_schema.FieldValidationInfo) -> Any:
        nonlocal info_stuff
        info_stuff = {'field_name': info.field_name, 'data': info.data.copy()}
        assert isinstance(input_value, str)
        return f'input: {input_value}'

    v = SchemaValidator(
        core_schema.typed_dict_schema(
            {
                'a': core_schema.typed_dict_field(core_schema.int_schema()),
                'b': core_schema.typed_dict_field(core_schema.int_schema()),
                'c': core_schema.typed_dict_field(
                    core_schema.field_after_validator_function(f, core_schema.str_schema())
                ),
            }
        )
    )

    data = v.validate_python({'a': 1, 'b': '2', 'c': b'foo'})
    assert data == {'a': 1, 'b': 2, 'c': 'input: foo'}
    assert info_stuff == {'field_name': 'c', 'data': {'a': 1, 'b': 2}}

    info_stuff = None

    with pytest.raises(ValidationError, match=r'b\s+Input should be a valid integer'):
        v.validate_python({'a': 1, 'b': 'wrong', 'c': b'foo'})

    assert info_stuff == {'field_name': 'c', 'data': {'a': 1}}


@pytest.mark.parametrize(
    'mode,calls1,calls2',
    [
        ('before', {'value': {'x': b'input', 'y': '123'}}, {'value': {'x': 'different', 'y': 123}}),
        ('after', {'value': {'x': 'input', 'y': 123}}, {'value': {'x': 'different', 'y': 123}}),
        ('wrap', {'value': {'x': b'input', 'y': '123'}}, {'value': {'x': 'different', 'y': 123}}),
    ],
)
def test_model_root_function_assignment(mode: str, calls1: Any, calls2: Any):
    calls: list[Any] = []

    class Model:
        x: str
        y: int

        def __init__(self, **kwargs: Any) -> None:
            self.__dict__.update(kwargs)

    def f(input_value: Any, *args: Any) -> Any:
        if mode == 'wrap':
            handler, _ = args
            calls.append({'value': input_value})
            return handler(input_value)
        else:
            calls.append({'value': input_value})
            return input_value

    v = SchemaValidator(
        core_schema.model_schema(
            Model,
            {
                'type': f'function-{mode}',
                'function': {'type': 'general', 'function': f},
                'schema': core_schema.typed_dict_schema(
                    {
                        'x': core_schema.typed_dict_field(core_schema.str_schema()),
                        'y': core_schema.typed_dict_field(core_schema.int_schema()),
                    }
                ),
            },
        )
    )

    m = Model()
    v.validate_python({'x': b'input', 'y': '123'}, self_instance=m)
    assert m.x == 'input'
    assert m.y == 123
    assert calls == [calls1]

    v.validate_assignment(m, 'x', b'different')
    assert calls == [calls1, calls2]
