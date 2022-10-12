import re
import sys
from pathlib import Path

import pytest

from pydantic_core._pydantic_core import (
    SchemaError,
    SchemaValidator,
    ValidationError,
    __version__,
    build_profile,
    list_all_errors,
)


@pytest.mark.parametrize('obj', [ValidationError, SchemaValidator, SchemaError])
def test_module(obj):
    assert obj.__module__ == 'pydantic_core._pydantic_core'


def test_version():
    assert isinstance(__version__, str)
    assert '.' in __version__


def test_build_profile():
    assert build_profile in ('debug', 'release')


def test_schema_error():
    err = SchemaError('test')
    assert isinstance(err, Exception)
    assert str(err) == 'test'
    assert repr(err) == 'SchemaError("test")'


def test_validation_error():
    v = SchemaValidator({'type': 'int'})
    with pytest.raises(ValidationError) as exc_info:
        v.validate_python(1.5)

    assert exc_info.value.title == 'int'
    assert exc_info.value.error_count() == 1
    assert (
        exc_info.value.errors()
        == exc_info.value.errors(include_context=False)
        == [
            {
                'kind': 'int_from_float',
                'loc': [],
                'message': 'Input should be a valid integer, got a number with a fractional part',
                'input_value': 1.5,
            }
        ]
    )


def test_validation_error_include_context():
    v = SchemaValidator({'type': 'list', 'max_length': 2})
    with pytest.raises(ValidationError) as exc_info:
        v.validate_python([1, 2, 3])

    assert exc_info.value.title == 'list[any]'
    assert exc_info.value.error_count() == 1
    # insert_assert(exc_info.value.errors())
    assert exc_info.value.errors() == [
        {
            'kind': 'too_long',
            'loc': [],
            'message': 'List should have at most 2 items after validation, not 3',
            'input_value': [1, 2, 3],
            'context': {'field_type': 'List', 'max_length': 2, 'actual_length': 3},
        }
    ]
    # insert_assert(exc_info.value.errors(include_context=False))
    assert exc_info.value.errors(include_context=False) == [
        {
            'kind': 'too_long',
            'loc': [],
            'message': 'List should have at most 2 items after validation, not 3',
            'input_value': [1, 2, 3],
        }
    ]


def test_custom_title():
    v = SchemaValidator({'type': 'int'}, {'title': 'MyInt'})
    with pytest.raises(ValidationError) as exc_info:
        v.validate_python(1.5)

    assert exc_info.value.title == 'MyInt'


def test_validation_error_multiple():
    class MyModel:
        # this is not required, but it avoids `__fields_set__` being included in `__dict__`
        __slots__ = '__dict__', '__fields_set__'
        field_a: str
        field_b: int

    v = SchemaValidator(
        {
            'type': 'new-class',
            'cls': MyModel,
            'schema': {
                'type': 'typed-dict',
                'return_fields_set': True,
                'fields': {'x': {'schema': {'type': 'float'}}, 'y': {'schema': {'type': 'int'}}},
            },
        }
    )
    with pytest.raises(ValidationError) as exc_info:
        v.validate_python({'x': 'x' * 60, 'y': 'y'})

    assert exc_info.value.title == 'MyModel'
    assert exc_info.value.error_count() == 2
    assert exc_info.value.errors() == [
        {
            'kind': 'float_parsing',
            'loc': ['x'],
            'message': 'Input should be a valid number, unable to parse string as an number',
            'input_value': 'x' * 60,
        },
        {
            'kind': 'int_parsing',
            'loc': ['y'],
            'message': 'Input should be a valid integer, unable to parse string as an integer',
            'input_value': 'y',
        },
    ]
    assert repr(exc_info.value) == (
        '2 validation errors for MyModel\n'
        'x\n'
        '  Input should be a valid number, unable to parse string as an number '
        "[kind=float_parsing, input_value='xxxxxxxxxxxxxxxxxxxxxxxx...xxxxxxxxxxxxxxxxxxxxxxx', input_type=str]\n"
        'y\n'
        '  Input should be a valid integer, unable to parse string as an integer '
        "[kind=int_parsing, input_value='y', input_type=str]"
    )


@pytest.mark.skipif(sys.platform == 'emscripten', reason='README.md is not mounted in wasm file system')
def test_readme(import_execute):
    this_dir = Path(__file__).parent
    readme = (this_dir / '..' / 'README.md').read_text()
    example_code = re.search(r'\n```py\n(.*?)\n```\n', readme, re.M | re.S).group(1)
    import_execute(example_code)


def test_all_errors():
    errors = list_all_errors()
    # print(f'{len(errors)=}')
    assert len(errors) == len(set(e['kind'] for e in errors)), 'error kinds are not unique'
    assert errors[:2] == [
        {
            'kind': 'invalid_json',
            'message_template': 'Invalid JSON: {error}',
            'example_message': 'Invalid JSON: ',
            'example_context': {'error': ''},
        },
        {
            'kind': 'recursion_loop',
            'message_template': 'Recursion error - cyclic reference detected',
            'example_message': 'Recursion error - cyclic reference detected',
            'example_context': None,
        },
    ]
