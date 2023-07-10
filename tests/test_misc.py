import copy
import pickle
import re

import pytest
from typing_extensions import get_args

from pydantic_core import CoreSchema, CoreSchemaType, PydanticUndefined, core_schema
from pydantic_core._pydantic_core import (
    SchemaError,
    SchemaValidator,
    ValidationError,
    __version__,
    build_info,
    build_profile,
)


@pytest.mark.parametrize('obj', [ValidationError, SchemaValidator, SchemaError])
def test_module(obj):
    assert obj.__module__ == 'pydantic_core._pydantic_core'


def test_version():
    assert isinstance(__version__, str)
    assert '.' in __version__


def test_build_profile():
    assert build_profile in ('debug', 'release')


def test_build_info():
    assert isinstance(build_info, str)


def test_schema_error():
    err = SchemaError('test')
    assert isinstance(err, Exception)
    assert str(err) == 'test'
    assert repr(err) == 'SchemaError("test")'


def test_validation_error(pydantic_version):
    v = SchemaValidator({'type': 'int'})
    with pytest.raises(ValidationError) as exc_info:
        v.validate_python(1.5)

    assert exc_info.value.title == 'int'
    assert exc_info.value.error_count() == 1
    assert (
        exc_info.value.errors(include_url=False)
        == exc_info.value.errors(include_url=False, include_context=False)
        == [
            {
                'type': 'int_from_float',
                'loc': (),
                'msg': 'Input should be a valid integer, got a number with a fractional part',
                'input': 1.5,
            }
        ]
    )
    # insert_assert(exc_info.value.errors())
    assert exc_info.value.errors() == [
        {
            'type': 'int_from_float',
            'loc': (),
            'msg': 'Input should be a valid integer, got a number with a fractional part',
            'input': 1.5,
            'url': f'https://errors.pydantic.dev/{pydantic_version}/v/int_from_float',
        }
    ]


def test_validation_error_include_context():
    v = SchemaValidator({'type': 'list', 'max_length': 2})
    with pytest.raises(ValidationError) as exc_info:
        v.validate_python([1, 2, 3])

    assert exc_info.value.title == 'list[any]'
    assert exc_info.value.error_count() == 1
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'too_long',
            'loc': (),
            'msg': 'List should have at most 2 items after validation, not 3',
            'input': [1, 2, 3],
            'ctx': {'field_type': 'List', 'max_length': 2, 'actual_length': 3},
        }
    ]
    # insert_assert(exc_info.value.errors(include_url=False, include_context=False))
    assert exc_info.value.errors(include_url=False, include_context=False) == [
        {
            'type': 'too_long',
            'loc': (),
            'msg': 'List should have at most 2 items after validation, not 3',
            'input': [1, 2, 3],
        }
    ]


def test_custom_title():
    v = SchemaValidator({'type': 'int'}, {'title': 'MyInt'})
    with pytest.raises(ValidationError) as exc_info:
        v.validate_python(1.5)

    assert exc_info.value.title == 'MyInt'


def test_validation_error_multiple(pydantic_version):
    class MyModel:
        # this is not required, but it avoids `__pydantic_fields_set__` being included in `__dict__`
        __slots__ = '__dict__', '__pydantic_fields_set__', '__pydantic_extra__', '__pydantic_private__'
        field_a: str
        field_b: int

    v = SchemaValidator(
        {
            'type': 'model',
            'cls': MyModel,
            'schema': {
                'type': 'model-fields',
                'fields': {
                    'x': {'type': 'model-field', 'schema': {'type': 'float'}},
                    'y': {'type': 'model-field', 'schema': {'type': 'int'}},
                },
            },
        }
    )
    with pytest.raises(ValidationError) as exc_info:
        v.validate_python({'x': 'x' * 60, 'y': 'y'})

    assert exc_info.value.title == 'MyModel'
    assert exc_info.value.error_count() == 2
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'float_parsing',
            'loc': ('x',),
            'msg': 'Input should be a valid number, unable to parse string as a number',
            'input': 'x' * 60,
        },
        {
            'type': 'int_parsing',
            'loc': ('y',),
            'msg': 'Input should be a valid integer, unable to parse string as an integer',
            'input': 'y',
        },
    ]
    assert repr(exc_info.value) == (
        '2 validation errors for MyModel\n'
        'x\n'
        '  Input should be a valid number, unable to parse string as a number '
        "[type=float_parsing, input_value='xxxxxxxxxxxxxxxxxxxxxxxx...xxxxxxxxxxxxxxxxxxxxxxx', input_type=str]\n"
        f'    For further information visit https://errors.pydantic.dev/{pydantic_version}/v/float_parsing\n'
        'y\n'
        '  Input should be a valid integer, unable to parse string as an integer '
        "[type=int_parsing, input_value='y', input_type=str]\n"
        f'    For further information visit https://errors.pydantic.dev/{pydantic_version}/v/int_parsing'
    )


def test_core_schema_type_literal():
    def get_type_value(schema):
        type_ = schema.__annotations__['type']
        m = re.search(r"Literal\['(.+?)']", type_.__forward_arg__)
        assert m, f'Unknown schema type: {type_}'
        return m.group(1)

    schema_types = tuple(get_type_value(x) for x in CoreSchema.__args__)
    schema_types = tuple(dict.fromkeys(schema_types))  # remove duplicates while preserving order
    if get_args(CoreSchemaType) != schema_types:
        literal = ''.join(f'\n    {e!r},' for e in schema_types)
        print(
            f'python code (near end of python/pydantic_core/core_schema.py):\n\nCoreSchemaType = Literal[{literal}\n]'
        )
        pytest.fail('core_schema.CoreSchemaType needs to be updated')


def test_undefined():
    with pytest.raises(NotImplementedError, match='UndefinedType'):
        PydanticUndefined.__class__()

    undefined_copy = copy.copy(PydanticUndefined)
    undefined_deepcopy = copy.deepcopy(PydanticUndefined)

    assert undefined_copy is PydanticUndefined
    assert undefined_deepcopy is PydanticUndefined

    assert pickle.loads(pickle.dumps(PydanticUndefined)) is PydanticUndefined


def test_unicode_error_input_repr() -> None:
    """https://github.com/pydantic/pydantic/issues/6448"""

    schema = core_schema.int_schema()

    validator = SchemaValidator(schema)

    danger_str = 'ÿ' * 1000
    expected = "1 validation error for int\n  Input should be a valid integer, unable to parse string as an integer [type=int_parsing, input_value='ÿÿÿÿÿÿÿÿÿÿÿÿ...ÿÿÿÿÿÿÿÿÿÿÿ', input_type=str]"  # noqa: E501
    with pytest.raises(ValidationError) as exc_info:
        validator.validate_python(danger_str)
    actual = repr(exc_info.value).split('For further information visit ')[0].strip()

    assert expected == actual
