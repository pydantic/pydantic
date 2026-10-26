import pytest

from pydantic_core import MISSING, SchemaValidator, ValidationError, core_schema


def test_missing_sentinel_no_inner_schema() -> None:
    v = SchemaValidator(core_schema.missing_sentinel_schema())

    assert v.validate_python(MISSING) is MISSING

    with pytest.raises(ValidationError) as exc_info:
        v.validate_python(1)

    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'missing_sentinel_error',
            'loc': (),
            'msg': "Input should be the 'MISSING' sentinel",
            'input': 1,
        }
    ]


def test_missing_sentinel_inner_schema() -> None:
    v = SchemaValidator(core_schema.missing_sentinel_schema(core_schema.int_schema()))

    assert v.validate_python(MISSING) is MISSING
    assert v.validate_python(1) == 1
    assert v.validate_python('123') == 123
    assert v.validate_json('123') == 123

    # The `MISSING` sentinel shouldn't be mentioned as a valid input:
    with pytest.raises(ValidationError) as exc_info:
        v.validate_python('hello')

    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'int_parsing',
            'loc': (),
            'msg': 'Input should be a valid integer, unable to parse string as an integer',
            'input': 'hello',
        }
    ]

    with pytest.raises(ValidationError) as exc_info:
        v.validate_json('"hello"')

    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'int_parsing',
            'loc': (),
            'msg': 'Input should be a valid integer, unable to parse string as an integer',
            'input': 'hello',
        }
    ]


def test_missing_sentinel_inner_schema_none_not_allowed() -> None:
    v = SchemaValidator(core_schema.missing_sentinel_schema(core_schema.int_schema()))

    with pytest.raises(ValidationError) as exc_info:
        v.validate_python(None)

    assert exc_info.value.errors(include_url=False)[0]['type'] == 'int_type'


def test_missing_sentinel_model_field() -> None:
    v = SchemaValidator(
        core_schema.model_fields_schema(
            {
                'f': core_schema.model_field(
                    core_schema.with_default_schema(
                        core_schema.missing_sentinel_schema(core_schema.int_schema()), default=MISSING
                    )
                )
            }
        )
    )

    assert v.validate_python({}) == ({'f': MISSING}, None, set())
    assert v.validate_python({'f': MISSING}) == ({'f': MISSING}, None, {'f'})
    assert v.validate_python({'f': 1}) == ({'f': 1}, None, {'f'})

    with pytest.raises(ValidationError) as exc_info:
        v.validate_python({'f': 'hello'})

    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'int_parsing',
            'loc': ('f',),
            'msg': 'Input should be a valid integer, unable to parse string as an integer',
            'input': 'hello',
        }
    ]
