"""Tagged union cursor lookup, branch completion, and error parity."""

from typing import Annotated, Any, Literal

import pytest
from pydantic_core import SchemaValidator, core_schema

from pydantic import BaseModel, BeforeValidator, Field, TypeAdapter, ValidationError


class First(BaseModel):
    kind: Literal['first']
    values: list[int]


class Second(BaseModel):
    kind: Literal['second']
    values: list[int]


Tagged = Annotated[First | Second, Field(discriminator='kind')]


@pytest.mark.parametrize(
    'data',
    [
        '{"kind":"first","values":[1,2]}',
        '{"values":[1,2],"kind":"second"}',
        '{"kind":"first","kind":"second","values":[1]}',
        '{"kind":"invalid","values":[1]}',
        '{"values":[1]}',
        '{"kind":"first","values":[1,"invalid"]}',
        '{"kind":[],"values":[1]}',
        '[]',
        'null',
    ],
)
def test_cursor_tagged_union_matches_ordinary(data: str) -> None:
    adapter = TypeAdapter(Tagged)
    # Chain dispatch keeps the original JsonValue instead of converting it to Python.
    ordinary = SchemaValidator(core_schema.chain_schema([adapter.core_schema, core_schema.any_schema()]))
    assert 'ChainValidator' in repr(ordinary)
    try:
        expected = ordinary.validate_json(data)
    except ValidationError as error:
        with pytest.raises(ValidationError) as actual:
            adapter.validate_json(data)
        assert actual.value.json(include_url=False) == error.json(include_url=False)
    else:
        actual = adapter.validate_json(data)
        assert type(actual) is type(expected)
        assert actual.model_dump() == expected.model_dump()


@pytest.mark.parametrize('data', ['{"kind":"invalid","values":[1]}', '{"values":[1]}'])
def test_cursor_tagged_union_error_preserves_parent_position(data: str) -> None:
    calls: list[int] = []

    def record(value: int) -> int:
        calls.append(value)
        return value

    class Outer(BaseModel):
        before: Annotated[int, BeforeValidator(record)]
        value: Tagged
        following: int

    with pytest.raises(ValidationError) as error:
        Outer.model_validate_json('{"before":1,"value":' + data + ',"following":"invalid"}')
    assert len(error.value.errors()) == 2
    assert error.value.errors()[1]['loc'] == ('following',)
    assert calls == [1]


def test_cursor_tagged_union_nested_values_preserve_next_value() -> None:
    adapter = TypeAdapter(list[Tagged])
    result = adapter.validate_json('[{"kind":"second","values":[1]},{"kind":"first","values":[2]}]')
    assert [type(item) for item in result] == [Second, First]
    assert [item.values for item in result] == [[1], [2]]


@pytest.mark.parametrize(
    'data, expected',
    [
        ('{"primary":"first","secondary":"second","value":1}', 'first'),
        ('{"secondary":"second","value":1,"primary":"first"}', 'first'),
        ('{"secondary":"first","secondary":"second","value":1}', 'second'),
    ],
)
def test_cursor_tagged_union_lookup_priority_and_duplicates(data: str, expected: str) -> None:
    class A(BaseModel):
        value: int

    class B(BaseModel):
        value: int

    schema = core_schema.tagged_union_schema(
        {'first': A.__pydantic_core_schema__, 'second': B.__pydantic_core_schema__},
        discriminator=[['primary'], ['secondary']],
    )
    result = SchemaValidator(schema).validate_json(data)
    assert isinstance(result, A if expected == 'first' else B)


@pytest.mark.parametrize('data', ['{"kind":"first","values":[1]} trailing', '{"kind":"first","values":[1,]}'])
def test_cursor_tagged_union_malformed_json(data: str) -> None:
    with pytest.raises(ValidationError, check=lambda error: error.errors()[0]['type'] == 'json_invalid'):
        TypeAdapter(Tagged).validate_json(data)


def test_cursor_tagged_union_callable_discriminator_still_works() -> None:
    def tag(value: Any) -> str:
        return value['kind']

    schema = core_schema.tagged_union_schema(
        {'first': First.__pydantic_core_schema__, 'second': Second.__pydantic_core_schema__}, discriminator=tag
    )
    assert isinstance(SchemaValidator(schema).validate_json('{"kind":"second","values":[1]}'), Second)


@pytest.mark.parametrize(
    'data',
    [b'{"padding":"\xff","kind":"first","values":[1]}', b'{"kind":"first","values":[1],"padding":"\xff"}'],
)
def test_cursor_tagged_union_skipped_values_check_utf8(data: bytes) -> None:
    with pytest.raises(ValidationError, check=lambda error: error.errors()[0]['type'] == 'json_invalid'):
        TypeAdapter(Tagged).validate_json(data)


@pytest.mark.parametrize(
    'data',
    [
        b'{"kind":"invalid","padding":"\xff","values":[1]}',
        b'{"padding":"\xff","values":[1],"kind":"invalid"}',
        b'{"padding":"\xff","values":[1]}',
        b'{"values":[1],"padding":"\xff"}',
    ],
)
def test_cursor_tagged_union_tag_error_still_checks_skipped_utf8(data: bytes) -> None:
    with pytest.raises(ValidationError, check=lambda error: error.errors()[0]['type'] == 'json_invalid'):
        TypeAdapter(Tagged).validate_json(data)
