"""Tests for TOON (Token-Oriented Object Notation) parsing and validation."""

from typing import Any

import pytest

from pydantic import BaseModel, TypeAdapter, ValidationError
from pydantic.toon import ToonParseError, parse_toon


class User(BaseModel):
    """Test user model."""

    id: int
    name: str
    age: int


class Settings(BaseModel):
    """Test settings model."""

    theme: str
    notifications: bool


class UserList(BaseModel):
    """Model with array of users."""

    users: list[User]


class NestedModel(BaseModel):
    """Model with nested structure."""

    users: list[User]
    settings: Settings


def test_parse_toon_simple_object():
    """Test parsing a simple TOON object."""
    toon_data = 'id: 1\nname: Alice\nage: 30'
    result = parse_toon(toon_data)
    assert result == {'id': 1, 'name': 'Alice', 'age': 30}


def test_parse_toon_simple_key_value():
    """Test parsing simple key-value pairs."""
    toon_data = 'theme: dark\nnotifications: true'
    result = parse_toon(toon_data)
    assert result == {'theme': 'dark', 'notifications': True}


def test_parse_toon_array():
    """Test parsing TOON array format."""
    toon_data = 'users[2]{id,name,age}:\n  1,Alice,30\n  2,Bob,25'
    result = parse_toon(toon_data)
    assert result == {
        'users': [
            {'id': 1, 'name': 'Alice', 'age': 30},
            {'id': 2, 'name': 'Bob', 'age': 25},
        ]
    }


def test_parse_toon_nested():
    """Test parsing nested TOON structure."""
    toon_data = """users[2]{id,name,age}:
  1,Alice,30
  2,Bob,25
settings:
  theme: dark
  notifications: true"""
    result = parse_toon(toon_data)
    assert result == {
        'users': [
            {'id': 1, 'name': 'Alice', 'age': 30},
            {'id': 2, 'name': 'Bob', 'age': 25},
        ],
        'settings': {'theme': 'dark', 'notifications': True},
    }


def test_parse_toon_boolean_values():
    """Test parsing boolean values."""
    toon_data = 'enabled: true\ndisabled: false'
    result = parse_toon(toon_data)
    assert result == {'enabled': True, 'disabled': False}


def test_parse_toon_null_values():
    """Test parsing null/None values."""
    toon_data = 'value: null\nempty: none'
    result = parse_toon(toon_data)
    assert result == {'value': None, 'empty': None}


def test_parse_toon_numbers():
    """Test parsing numeric values."""
    toon_data = 'int_value: 42\nfloat_value: 3.14\nnegative: -10'
    result = parse_toon(toon_data)
    assert result == {'int_value': 42, 'float_value': 3.14, 'negative': -10}


def test_parse_toon_bytes():
    """Test parsing TOON from bytes."""
    toon_data = b'id: 1\nname: Alice'
    result = parse_toon(toon_data)
    assert result == {'id': 1, 'name': 'Alice'}


def test_parse_toon_empty():
    """Test parsing empty TOON."""
    result = parse_toon('')
    assert result == {}


def test_parse_toon_with_comments():
    """Test parsing TOON with comments (should be skipped)."""
    toon_data = '# This is a comment\nid: 1\n# Another comment\nname: Alice'
    result = parse_toon(toon_data)
    assert result == {'id': 1, 'name': 'Alice'}


def test_model_validate_toon():
    """Test model_validate_toon method."""
    toon_data = 'id: 1\nname: Alice\nage: 30'
    user = User.model_validate_toon(toon_data)
    assert user.id == 1
    assert user.name == 'Alice'
    assert user.age == 30


def test_model_validate_toon_array():
    """Test validating array format with model."""
    toon_data = 'users[2]{id,name,age}:\n  1,Alice,30\n  2,Bob,25'
    user_list = UserList.model_validate_toon(toon_data)
    assert len(user_list.users) == 2
    assert user_list.users[0].id == 1
    assert user_list.users[0].name == 'Alice'
    assert user_list.users[1].id == 2
    assert user_list.users[1].name == 'Bob'


def test_model_validate_toon_nested():
    """Test validating nested structure."""
    toon_data = """users[2]{id,name,age}:
  1,Alice,30
  2,Bob,25
settings:
  theme: dark
  notifications: true"""
    model = NestedModel.model_validate_toon(toon_data)
    assert len(model.users) == 2
    assert model.settings.theme == 'dark'
    assert model.settings.notifications is True


def test_model_validate_toon_invalid_data():
    """Test validation error with invalid data."""
    toon_data = 'id: not_a_number\nname: Alice\nage: 30'
    with pytest.raises(ValidationError) as exc_info:
        User.model_validate_toon(toon_data)
    assert len(exc_info.value.errors()) > 0


def test_model_validate_toon_missing_field():
    """Test validation error with missing required field."""
    toon_data = 'id: 1\nname: Alice'
    with pytest.raises(ValidationError) as exc_info:
        User.model_validate_toon(toon_data)
    errors = exc_info.value.errors()
    assert any(error['loc'] == ('age',) for error in errors)


def test_parse_toon_invalid_array_count():
    """Test parse error with mismatched array count."""
    toon_data = 'users[3]{id,name}:\n  1,Alice\n  2,Bob'
    with pytest.raises(ToonParseError):
        parse_toon(toon_data)


def test_parse_toon_invalid_array_fields():
    """Test parse error with mismatched field count."""
    toon_data = 'users[2]{id,name}:\n  1,Alice,extra\n  2,Bob'
    with pytest.raises(ToonParseError):
        parse_toon(toon_data)


def test_type_adapter_validate_toon():
    """Test TypeAdapter.validate_toon method."""
    ta = TypeAdapter(User)
    toon_data = 'id: 1\nname: Alice\nage: 30'
    user = ta.validate_toon(toon_data)
    assert user.id == 1
    assert user.name == 'Alice'
    assert user.age == 30


def test_type_adapter_validate_toon_list():
    """Test TypeAdapter with list type."""
    ta = TypeAdapter(list[User])
    toon_data = 'users[2]{id,name,age}:\n  1,Alice,30\n  2,Bob,25'
    # Note: This will parse as a dict, need to handle accordingly
    # For now, we'll test with a dict structure
    result = parse_toon(toon_data)
    users = ta.validate_python(result['users'])
    assert len(users) == 2
    assert users[0].id == 1


def test_parse_toon_complex_example():
    """Test parsing a complex real-world example."""
    toon_data = """users[3]{id,name,department,salary}:
  1,Alice,Engineering,120000
  2,Bob,Marketing,95000
  3,Charlie,Engineering,110000
settings:
  theme: dark
  notifications: true
  max_users: 100"""
    result = parse_toon(toon_data)
    assert len(result['users']) == 3
    assert result['users'][0]['name'] == 'Alice'
    assert result['users'][0]['salary'] == 120000
    assert result['settings']['theme'] == 'dark'
    assert result['settings']['max_users'] == 100


def test_parse_toon_unicode():
    """Test parsing TOON with unicode characters."""
    toon_data = 'name: José\ncity: 北京'
    result = parse_toon(toon_data)
    assert result == {'name': 'José', 'city': '北京'}


def test_parse_toon_whitespace_handling():
    """Test that whitespace is handled correctly."""
    toon_data = '  key: value  \n  another: test  '
    result = parse_toon(toon_data)
    assert result == {'key': 'value', 'another': 'test'}


def test_model_validate_toon_with_strict():
    """Test model_validate_toon with strict mode."""
    toon_data = 'id: 1\nname: Alice\nage: 30'
    user = User.model_validate_toon(toon_data, strict=True)
    assert user.id == 1
    assert user.name == 'Alice'
    assert user.age == 30


def test_parse_toon_invalid_utf8():
    """Test parsing invalid UTF-8 bytes."""
    invalid_bytes = b'\xff\xfe\x00\x00'
    with pytest.raises(ToonParseError) as exc_info:
        parse_toon(invalid_bytes)
    assert 'UTF-8' in str(exc_info.value)


def test_model_validate_toon_with_extra():
    """Test model_validate_toon with extra fields."""
    toon_data = 'id: 1\nname: Alice\nage: 30\nextra: field'
    # Should work with extra='allow'
    user = User.model_validate_toon(toon_data, extra='allow')
    assert user.id == 1
    # Extra field should be present when extra='allow'
    assert hasattr(user, 'extra')
    assert user.extra == 'field'


@pytest.mark.parametrize(
    'toon_data,expected',
    [
        ('key: value', {'key': 'value'}),
        ('a: 1\nb: 2', {'a': 1, 'b': 2}),
        ('items[2]{id,name}:\n  1,first\n  2,second', {'items': [{'id': 1, 'name': 'first'}, {'id': 2, 'name': 'second'}]}),
        ('bool_true: true\nbool_false: false', {'bool_true': True, 'bool_false': False}),
        ('null_val: null', {'null_val': None}),
    ],
)
def test_parse_toon_parametrized(toon_data: str, expected: dict[str, Any]):
    """Parametrized tests for various TOON formats."""
    result = parse_toon(toon_data)
    assert result == expected

