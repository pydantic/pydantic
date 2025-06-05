import datetime
import platform
import re
from copy import deepcopy
from dataclasses import dataclass
from typing import Any

import pytest
from dirty_equals import HasRepr

from pydantic_core import CoreConfig, SchemaValidator, ValidationError, core_schema
from pydantic_core import core_schema as cs

from ..conftest import plain_repr


def deepcopy_info(info: core_schema.ValidationInfo) -> dict[str, Any]:
    return {
        'context': deepcopy(info.context),
        'data': deepcopy(info.data),
        'field_name': deepcopy(info.field_name),
        'config': deepcopy(info.config),
    }


def test_function_before():
    def f(input_value, _info):
        return input_value + ' Changed'

    v = SchemaValidator(core_schema.with_info_before_validator_function(f, core_schema.str_schema()))

    assert v.validate_python('input value') == 'input value Changed'


def test_function_before_no_info():
    def f(input_value):
        return input_value + ' Changed'

    v = SchemaValidator(core_schema.no_info_before_validator_function(f, core_schema.str_schema()))

    assert v.validate_python('input value') == 'input value Changed'


def test_function_before_raise():
    def f(input_value, info):
        raise ValueError('foobar')

    v = SchemaValidator(core_schema.with_info_before_validator_function(f, core_schema.str_schema()))

    with pytest.raises(ValidationError) as exc_info:
        assert v.validate_python('input value') == 'input value Changed'
    # debug(str(exc_info.value))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'value_error',
            'loc': (),
            'msg': 'Value error, foobar',
            'input': 'input value',
            'ctx': {'error': HasRepr(repr(ValueError('foobar')))},
        }
    ]


def test_function_before_error():
    def my_function(input_value, info):
        return input_value + 'x'

    v = SchemaValidator(
        {
            'type': 'function-before',
            'function': {'type': 'with-info', 'function': my_function},
            'schema': cs.str_schema(max_length=5),
        }
    )

    assert v.validate_python('1234') == '1234x'
    with pytest.raises(ValidationError) as exc_info:
        v.validate_python('12345')
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'string_too_long',
            'loc': (),
            'msg': 'String should have at most 5 characters',
            'input': '12345x',
            'ctx': {'max_length': 5},
        }
    ]
    assert repr(exc_info.value).startswith('1 validation error for function-before[my_function(), constrained-str]\n')


@pytest.mark.parametrize(
    'config,input_str',
    (
        ({}, "type=string_too_long, input_value='12345x', input_type=str"),
        (CoreConfig(hide_input_in_errors=False), "type=string_too_long, input_value='12345x', input_type=str"),
        (CoreConfig(hide_input_in_errors=True), 'type=string_too_long'),
    ),
)
def test_function_before_error_hide_input(config, input_str):
    def my_function(input_value, info):
        return input_value + 'x'

    v = SchemaValidator(
        {
            'type': 'function-before',
            'function': {'type': 'with-info', 'function': my_function},
            'schema': cs.str_schema(max_length=5),
        },
        config=config,
    )

    with pytest.raises(ValidationError, match=re.escape(f'String should have at most 5 characters [{input_str}]')):
        v.validate_python('12345')


def test_function_before_error_model():
    def f(input_value, info):
        if 'my_field' in input_value:
            input_value['my_field'] += 'x'
        return input_value

    v = SchemaValidator(
        {
            'type': 'function-before',
            'function': {'type': 'with-info', 'function': f},
            'schema': cs.typed_dict_schema(
                fields={'my_field': cs.typed_dict_field(schema=cs.str_schema(max_length=5))}
            ),
        }
    )

    assert v.validate_python({'my_field': '1234'}) == {'my_field': '1234x'}
    with pytest.raises(ValidationError) as exc_info:
        v.validate_python({'my_field': '12345'})
    assert exc_info.value.errors(include_url=False) == [
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
        (None, {}, 'ValidationInfo(config=None, context=None, data=None, field_name=None)'),
        (None, {'context': {1: 2}}, 'ValidationInfo(config=None, context={1: 2}, data=None, field_name=None)'),
        (None, {'context': None}, 'ValidationInfo(config=None, context=None, data=None, field_name=None)'),
        (
            CoreConfig(title='hello'),
            {},
            "ValidationInfo(config={'title': 'hello'}, context=None, data=None, field_name=None)",
        ),
    ],
)
def test_val_info_repr(config, kwargs, expected_repr):
    def f(input_value, info: core_schema.ValidationInfo):
        assert repr(info) == expected_repr
        assert str(info) == expected_repr
        return input_value

    v = SchemaValidator(core_schema.with_info_before_validator_function(f, core_schema.str_schema()), config=config)

    assert v.validate_python('input value', **kwargs) == 'input value'


def test_function_wrap():
    def f(input_value, validator, info):
        return validator(input_value=input_value) + ' Changed'

    v = SchemaValidator(core_schema.with_info_wrap_validator_function(f, core_schema.str_schema()))

    assert v.validate_python('input value') == 'input value Changed'


def test_function_wrap_no_info():
    def f(input_value, validator):
        return validator(input_value=input_value) + ' Changed'

    v = SchemaValidator(core_schema.no_info_wrap_validator_function(f, core_schema.str_schema()))

    assert v.validate_python('input value') == 'input value Changed'


def test_function_wrap_repr():
    def f(input_value, validator, info):
        assert repr(validator) == str(validator)
        return plain_repr(validator)

    v = SchemaValidator(core_schema.with_info_wrap_validator_function(f, core_schema.str_schema()))

    assert (
        v.validate_python('input value')
        == 'ValidatorCallable(Str(StrValidator{strict:false,coerce_numbers_to_str:false}))'
    )


def test_function_wrap_str():
    def f(input_value, validator, info):
        return plain_repr(validator)

    v = SchemaValidator(core_schema.with_info_wrap_validator_function(f, core_schema.str_schema()))

    assert (
        v.validate_python('input value')
        == 'ValidatorCallable(Str(StrValidator{strict:false,coerce_numbers_to_str:false}))'
    )


def test_wrap_error():
    def f(input_value, validator, info):
        try:
            return validator(input_value) * 2
        except ValidationError as e:
            assert e.title == 'ValidatorCallable'
            assert str(e).startswith('1 validation error for ValidatorCallable\n')
            raise e

    v = SchemaValidator(core_schema.with_info_wrap_validator_function(f, core_schema.int_schema()))

    assert v.validate_python('42') == 84
    with pytest.raises(ValidationError) as exc_info:
        v.validate_python('wrong')
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'int_parsing',
            'loc': (),
            'msg': 'Input should be a valid integer, unable to parse string as an integer',
            'input': 'wrong',
        }
    ]


@pytest.mark.parametrize(
    'config,input_str',
    (
        ({}, "type=int_parsing, input_value='wrong', input_type=str"),
        (CoreConfig(hide_input_in_errors=False), "type=int_parsing, input_value='wrong', input_type=str"),
        (CoreConfig(hide_input_in_errors=True), 'type=int_parsing'),
    ),
)
def test_function_wrap_error_hide_input(config, input_str):
    def f(input_value, validator, info):
        try:
            return validator(input_value) * 2
        except ValidationError as e:
            assert e.title == 'ValidatorCallable'
            assert str(e).startswith('1 validation error for ValidatorCallable\n')
            raise e

    v = SchemaValidator(core_schema.with_info_wrap_validator_function(f, core_schema.int_schema()), config=config)

    with pytest.raises(
        ValidationError,
        match=re.escape(f'Input should be a valid integer, unable to parse string as an integer [{input_str}]'),
    ):
        v.validate_python('wrong')


def test_function_wrap_location():
    def f(input_value, validator, info):
        return validator(input_value, outer_location='foo') + 2

    v = SchemaValidator(core_schema.with_info_wrap_validator_function(f, core_schema.int_schema()))

    assert v.validate_python(4) == 6
    with pytest.raises(ValidationError) as exc_info:
        v.validate_python('wrong')
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
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

    v = SchemaValidator(core_schema.with_info_wrap_validator_function(f, core_schema.int_schema()))

    assert v.validate_python(4) == 6

    with pytest.raises(ValidationError) as exc_info:
        v.validate_python('wrong')
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'int_parsing',
            'loc': ("('4',)",),
            'msg': 'Input should be a valid integer, unable to parse string as an integer',
            'input': 'wrong',
        }
    ]


def test_function_after():
    def f(input_value, _info):
        return input_value + ' Changed'

    v = SchemaValidator(core_schema.with_info_after_validator_function(f, core_schema.str_schema()))

    assert v.validate_python('input value') == 'input value Changed'


def test_function_no_info():
    def f(input_value):
        return input_value + ' Changed'

    v = SchemaValidator(core_schema.no_info_after_validator_function(f, core_schema.str_schema()))

    assert v.validate_python('input value') == 'input value Changed'


def test_function_after_raise():
    def f(input_value, info):
        raise ValueError('foobar')

    v = SchemaValidator(core_schema.with_info_after_validator_function(f, core_schema.str_schema()))

    with pytest.raises(ValidationError) as exc_info:
        assert v.validate_python('input value') == 'input value Changed'
    # debug(str(exc_info.value))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'value_error',
            'loc': (),
            'msg': 'Value error, foobar',
            'input': 'input value',
            'ctx': {'error': HasRepr(repr(ValueError('foobar')))},
        }
    ]


@pytest.mark.parametrize(
    'config,input_str',
    (
        ({}, "type=value_error, input_value='input value', input_type=str"),
        (CoreConfig(hide_input_in_errors=False), "type=value_error, input_value='input value', input_type=str"),
        (CoreConfig(hide_input_in_errors=True), 'type=value_error'),
    ),
)
def test_function_after_error_hide_input(config, input_str):
    def f(input_value, info):
        raise ValueError('foobar')

    v = SchemaValidator(core_schema.with_info_after_validator_function(f, core_schema.str_schema()), config=config)

    with pytest.raises(ValidationError, match=re.escape(f'Value error, foobar [{input_str}]')):
        v.validate_python('input value')


def test_function_after_config():
    f_kwargs = None

    def f(input_value, info):
        nonlocal f_kwargs
        f_kwargs = deepcopy_info(info)
        return input_value + ' Changed'

    v = SchemaValidator(
        cs.typed_dict_schema(
            fields={
                'test_field': cs.typed_dict_field(
                    schema={
                        'type': 'function-after',
                        'function': {'type': 'with-info', 'function': f, 'field_name': 'test_field'},
                        'schema': cs.str_schema(),
                    }
                )
            },
            config=CoreConfig(allow_inf_nan=True),
        )
    )

    assert v.validate_python({'test_field': b'321'}) == {'test_field': '321 Changed'}
    assert f_kwargs == {'data': {}, 'config': {'allow_inf_nan': True}, 'context': None, 'field_name': 'test_field'}


def test_config_no_model():
    f_kwargs = None

    def f(input_value, info: core_schema.ValidationInfo):
        nonlocal f_kwargs
        f_kwargs = deepcopy_info(info)
        return input_value + ' Changed'

    v = SchemaValidator(core_schema.with_info_after_validator_function(f, core_schema.str_schema()))

    assert v.validate_python(b'abc') == 'abc Changed'
    assert f_kwargs == {'data': None, 'config': None, 'context': None, 'field_name': None}


def test_function_plain():
    def f(input_value, _info):
        return input_value * 2

    v = SchemaValidator(core_schema.with_info_plain_validator_function(f))

    assert v.validate_python(1) == 2
    assert v.validate_python('x') == 'xx'


def test_function_plain_no_info():
    def f(input_value):
        return input_value * 2

    v = SchemaValidator(core_schema.no_info_plain_validator_function(f))

    assert v.validate_python(1) == 2
    assert v.validate_python('x') == 'xx'


def test_validate_assignment():
    def f(input_value):
        input_value.more = 'foobar'
        return input_value

    class Model:
        __slots__ = '__dict__', '__pydantic_fields_set__', '__pydantic_extra__', '__pydantic_private__'
        field_a: str

        def __init__(self):
            self.__pydantic_extra__ = None  # this attribute must be present for validate_assignment

    v = SchemaValidator(
        core_schema.no_info_after_validator_function(
            f,
            core_schema.model_schema(
                Model, core_schema.model_fields_schema({'field_a': core_schema.model_field(core_schema.str_schema())})
            ),
        )
    )
    m = v.validate_python({'field_a': 'test'})
    assert isinstance(m, Model)
    assert m.field_a == 'test'
    assert m.__pydantic_fields_set__ == {'field_a'}
    assert m.__dict__ == {'field_a': 'test', 'more': 'foobar'}
    assert m.__pydantic_extra__ is None

    m2 = Model()
    m2.field_a = 'test'
    assert v.validate_assignment(m2, 'field_a', b'abc') is m2
    assert m2.__dict__ == {'field_a': 'abc', 'more': 'foobar'}
    assert not hasattr(m2, '__pydantic_fields_set__')


def test_function_wrong_sig():
    def f(input_value):
        return input_value + ' Changed'

    v = SchemaValidator(core_schema.with_info_before_validator_function(f, core_schema.str_schema()))

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
            'function': {'type': 'with-info', 'function': Foobar.__validate__},
            'schema': cs.str_schema(),
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

    assert exc_info.value.errors(include_url=False) == [
        {'type': 'string_type', 'loc': (), 'msg': 'Input should be a valid string', 'input': True}
    ]


def test_raise_assertion_error():
    def f(input_value, info):
        raise AssertionError('foobar')

    v = SchemaValidator(core_schema.with_info_before_validator_function(f, core_schema.str_schema()))

    with pytest.raises(ValidationError) as exc_info:
        v.validate_python('input value')

    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'assertion_error',
            'loc': (),
            'msg': 'Assertion failed, foobar',
            'input': 'input value',
            'ctx': {'error': HasRepr(repr(AssertionError('foobar')))},
        }
    ]


def test_raise_assertion_error_plain():
    def f(input_value, info):
        raise AssertionError

    v = SchemaValidator(core_schema.with_info_before_validator_function(f, core_schema.str_schema()))

    with pytest.raises(ValidationError) as exc_info:
        v.validate_python('input value')

    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'assertion_error',
            'loc': (),
            'msg': 'Assertion failed, ',
            'input': 'input value',
            'ctx': {'error': HasRepr(repr(AssertionError()))},
        }
    ]


@pytest.mark.parametrize('base_error', [ValueError, AssertionError])
def test_error_with_error(base_error: type[Exception]):
    class MyError(base_error):
        def __str__(self):
            raise RuntimeError('internal error')

    def f(input_value, info):
        raise MyError()

    v = SchemaValidator(core_schema.with_info_before_validator_function(f, core_schema.str_schema()))

    with pytest.raises(RuntimeError, match='internal error'):
        v.validate_python('input value')


def test_raise_type_error():
    def f(input_value, info):
        raise TypeError('foobar')

    v = SchemaValidator(core_schema.with_info_before_validator_function(f, core_schema.str_schema()))

    with pytest.raises(TypeError, match='^foobar$'):
        v.validate_python('input value')


def test_model_field_before_validator() -> None:
    class Model:
        x: str

    def f(input_value: Any, info: core_schema.ValidationInfo) -> Any:
        assert info.field_name == 'x'
        assert info.data == {}
        assert repr(info) == "ValidationInfo(config=None, context=None, data={}, field_name='x')"
        assert str(info) == "ValidationInfo(config=None, context=None, data={}, field_name='x')"
        assert isinstance(input_value, bytes)
        return f'input: {input_value.decode()}'

    v = SchemaValidator(
        core_schema.model_schema(
            Model,
            core_schema.model_fields_schema(
                {
                    'x': core_schema.model_field(
                        core_schema.with_info_before_validator_function(f, core_schema.str_schema())
                    )
                }
            ),
        )
    )

    assert v.validate_python({'x': b'foo'}).x == 'input: foo'


def test_model_field_after_validator() -> None:
    class Model:
        x: str

    def f(input_value: str, info: core_schema.ValidationInfo) -> Any:
        assert info.field_name == 'x'
        assert info.data == {}
        assert isinstance(input_value, str)
        return f'input: {input_value}'

    v = SchemaValidator(
        core_schema.model_schema(
            Model,
            core_schema.model_fields_schema(
                {
                    'x': core_schema.model_field(
                        core_schema.with_info_after_validator_function(f, core_schema.str_schema())
                    )
                }
            ),
        )
    )

    assert v.validate_python({'x': b'foo'}).x == 'input: foo'


def test_model_field_plain_validator() -> None:
    class Model:
        x: str

    def f(input_value: Any, info: core_schema.ValidationInfo) -> Any:
        assert info.field_name == 'x'
        assert info.data == {}
        assert isinstance(input_value, bytes)
        return f'input: {input_value.decode()}'

    v = SchemaValidator(
        core_schema.model_schema(
            Model,
            core_schema.model_fields_schema(
                {'x': core_schema.model_field(core_schema.with_info_plain_validator_function(f))}
            ),
        )
    )

    assert v.validate_python({'x': b'foo'}).x == 'input: foo'


def test_model_field_validator_reuse() -> None:
    class Model:
        x: str
        y: str

    def f(input_value: Any, info: core_schema.ValidationInfo) -> Any:
        return f'{info.field_name}: {input_value}'

    # When a type alias with a validator function is used on multiple fields,
    # its core schema is only generated once (with the first field_name) and reused.
    # See https://github.com/pydantic/pydantic/issues/11737
    with pytest.warns(
        DeprecationWarning, match='`field_name` argument on `with_info_plain_validator_function` is deprecated'
    ):
        validator = core_schema.with_info_plain_validator_function(f, field_name='x')

    v = SchemaValidator(
        core_schema.model_schema(
            Model,
            core_schema.model_fields_schema(
                {
                    'x': core_schema.model_field(validator),
                    'y': core_schema.model_field(validator),
                }
            ),
        )
    )

    m = v.validate_python({'x': 'foo', 'y': 'bar'})
    assert m.x == 'x: foo'
    assert m.y == 'y: bar'


def test_model_field_wrap_validator() -> None:
    class Model:
        x: str

    def f(input_value: Any, val: core_schema.ValidatorFunctionWrapHandler, info: core_schema.ValidationInfo) -> Any:
        assert info.field_name == 'x'
        assert info.data == {}
        assert isinstance(input_value, bytes)
        return f'input: {val(input_value)}'

    v = SchemaValidator(
        core_schema.model_schema(
            Model,
            core_schema.model_fields_schema(
                {
                    'x': core_schema.model_field(
                        core_schema.with_info_wrap_validator_function(f, core_schema.str_schema())
                    )
                }
            ),
        )
    )

    assert v.validate_python({'x': b'foo'}).x == 'input: foo'


def test_non_model_field_before_validator_field_info() -> None:
    class Model:
        x: str

    def f(input_value: Any, info: core_schema.ValidationInfo) -> Any:
        assert info.field_name == 'x'
        assert info.data == {}
        assert isinstance(input_value, bytes)
        return f'input: {input_value.decode()}'

    v = SchemaValidator(
        core_schema.model_schema(
            Model,
            core_schema.model_fields_schema(
                {
                    'x': core_schema.model_field(
                        core_schema.with_info_before_validator_function(f, core_schema.str_schema())
                    )
                }
            ),
        )
    )

    assert v.validate_python({'x': b'foo'}).x == 'input: foo'


def test_non_model_field_after_validator_field_info() -> None:
    class Model:
        x: str

    def f(input_value: Any, info: core_schema.ValidationInfo) -> Any:
        assert info.field_name == 'x'
        assert info.data == {}
        return f'input: {input_value}'

    v = SchemaValidator(
        core_schema.model_schema(
            Model,
            core_schema.model_fields_schema(
                {
                    'x': core_schema.model_field(
                        core_schema.with_info_after_validator_function(f, core_schema.str_schema())
                    )
                }
            ),
        )
    )

    assert v.validate_python({'x': b'foo'}).x == 'input: foo'


def test_non_model_field_plain_validator_field_info() -> None:
    class Model:
        x: str

    def f(input_value: Any, info: core_schema.ValidationInfo) -> Any:
        assert info.field_name == 'x'
        assert info.data == {}
        assert isinstance(input_value, bytes)
        return f'input: {input_value.decode()}'

    v = SchemaValidator(
        core_schema.model_schema(
            Model,
            core_schema.model_fields_schema(
                {'x': core_schema.model_field(core_schema.with_info_plain_validator_function(f))}
            ),
        )
    )

    assert v.validate_python({'x': b'foo'}).x == 'input: foo'


def test_non_model_field_wrap_validator_field_info() -> None:
    class Model:
        __slots__ = '__dict__', '__pydantic_fields_set__', '__pydantic_extra__', '__pydantic_private__'
        x: str

    def f(input_value: Any, val: core_schema.ValidatorFunctionWrapHandler, info: core_schema.ValidationInfo) -> Any:
        assert info.field_name == 'x'
        assert info.data == {}
        return f'input: {val(input_value)}'

    v = SchemaValidator(
        core_schema.model_schema(
            Model,
            core_schema.model_fields_schema(
                {
                    'x': core_schema.model_field(
                        core_schema.with_info_wrap_validator_function(f, core_schema.str_schema())
                    )
                }
            ),
        )
    )

    assert v.validate_python({'x': b'foo'}).x == 'input: foo'


def test_typed_dict_data() -> None:
    info_stuff = None

    def f(input_value: Any, info: core_schema.ValidationInfo) -> Any:
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
                    core_schema.with_info_after_validator_function(f, core_schema.str_schema())
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


def test_typed_dict_validator_reuse() -> None:
    def f(input_value: Any, info: core_schema.ValidationInfo) -> Any:
        return f'{info.field_name}: {input_value}'

    # When a type alias with a validator function is used on multiple fields,
    # its core schema is only generated once (with the first field_name) and reused.
    # See https://github.com/pydantic/pydantic/issues/11737
    with pytest.warns(
        DeprecationWarning, match='`field_name` argument on `with_info_plain_validator_function` is deprecated'
    ):
        validator = core_schema.with_info_plain_validator_function(f, field_name='x')

    v = SchemaValidator(
        core_schema.typed_dict_schema(
            {
                'x': core_schema.model_field(validator),
                'y': core_schema.model_field(validator),
            }
        )
    )

    data = v.validate_python({'x': 'foo', 'y': 'bar'})
    assert data['x'] == 'x: foo'
    assert data['y'] == 'y: bar'


def test_dataclass_validator_reuse() -> None:
    @dataclass
    class Model:
        x: str
        y: str

    def f(input_value: Any, info: core_schema.ValidationInfo) -> Any:
        return f'{info.field_name}: {input_value}'

    # When a type alias with a validator function is used on multiple fields,
    # its core schema is only generated once (with the first field_name) and reused.
    # See https://github.com/pydantic/pydantic/issues/11737
    with pytest.warns(
        DeprecationWarning, match='`field_name` argument on `with_info_plain_validator_function` is deprecated'
    ):
        validator = core_schema.with_info_plain_validator_function(f, field_name='x')

    v = SchemaValidator(
        core_schema.dataclass_schema(
            Model,
            core_schema.dataclass_args_schema(
                'Model',
                [
                    core_schema.dataclass_field(name='x', schema=validator),
                    core_schema.dataclass_field(name='y', schema=validator),
                ],
            ),
            ['x', 'y'],
        )
    )

    m = v.validate_python({'x': 'foo', 'y': 'bar'})
    assert m.x == 'x: foo'
    assert m.y == 'y: bar'


@pytest.mark.parametrize(
    'mode,calls1,calls2',
    [
        ('before', {'value': {'x': b'input', 'y': '123'}}, {'value': {'x': 'different', 'y': 123}}),
        (
            'after',
            {'value': ({'x': 'input', 'y': 123}, None, {'y', 'x'})},
            {'value': ({'x': 'different', 'y': 123}, None, {'x'})},
        ),
        ('wrap', {'value': {'x': b'input', 'y': '123'}}, {'value': {'x': 'different', 'y': 123}}),
    ],
    ids=('before', 'after', 'wrap'),
)
def test_model_root_function_assignment(mode: str, calls1: Any, calls2: Any):
    calls: list[Any] = []

    class Model:
        __slots__ = '__dict__', '__pydantic_fields_set__', '__pydantic_extra__', '__pydantic_private__'
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
                'function': {'type': 'with-info', 'function': f},
                'schema': core_schema.model_fields_schema(
                    {
                        'x': core_schema.model_field(core_schema.str_schema()),
                        'y': core_schema.model_field(core_schema.int_schema()),
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


def test_function_validation_info_mode():
    calls: list[str] = []

    def f(v: Any, info: core_schema.ValidationInfo) -> Any:
        calls.append(info.mode)
        return v

    v = SchemaValidator(core_schema.with_info_before_validator_function(f, core_schema.int_schema()))
    assert v.validate_python(1) == 1
    assert calls == ['python']
    calls.clear()
    assert v.validate_json('1') == 1
    assert calls == ['json']
    calls.clear()

    v = SchemaValidator(core_schema.with_info_after_validator_function(f, core_schema.int_schema()))
    assert v.validate_python(1) == 1
    assert calls == ['python']
    calls.clear()
    assert v.validate_json('1') == 1
    assert calls == ['json']
    calls.clear()

    def f_w(v: Any, handler: core_schema.ValidatorFunctionWrapHandler, info: core_schema.ValidationInfo) -> Any:
        calls.append(info.mode)
        return handler(v)

    v = SchemaValidator(core_schema.with_info_wrap_validator_function(f_w, core_schema.int_schema()))
    assert v.validate_python(1) == 1
    assert calls == ['python']
    calls.clear()
    assert v.validate_json('1') == 1
    assert calls == ['json']
    calls.clear()


def test_function_after_doesnt_change_mode() -> None:
    # https://github.com/pydantic/pydantic/issues/7468 - function-after was
    # incorrectly forcing Python validation mode

    def identity(v):
        return v

    schema = core_schema.no_info_after_validator_function(identity, core_schema.date_schema(strict=True))
    v = SchemaValidator(schema)

    # this input should be valid JSON input, but isn't valid Python input, so
    # the following tests will pass if the after_validator is not
    # forcing the mode to Python
    assert v.validate_json(b'"2000-01-01"') == datetime.date(2000, 1, 1)
    with pytest.raises(ValidationError):
        v.validate_python(b'"2000-01-01"')
