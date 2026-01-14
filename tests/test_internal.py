"""
Tests for internal things that are complex enough to warrant their own unit tests.
"""

import sys
from copy import deepcopy
from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Union

import pytest
from dirty_equals import Contains, IsPartialDict
from pydantic_core import CoreSchema
from pydantic_core import core_schema as cs

from pydantic import BaseModel, TypeAdapter
from pydantic._internal._config import ConfigWrapper
from pydantic._internal._core_metadata import update_core_metadata
from pydantic._internal._generate_schema import GenerateSchema
from pydantic._internal._repr import Representation
from pydantic._internal._validators import _extract_decimal_digits_info
from pydantic.config import JsonDict
from pydantic.json_schema import GetJsonSchemaHandler, JsonSchemaValue, PydanticJsonSchemaWarning


def init_schema_and_cleaned_schema(type_: Any) -> tuple[CoreSchema, CoreSchema]:
    gen = GenerateSchema(ConfigWrapper(None))
    schema = gen.generate_schema(type_)
    cleaned_schema = deepcopy(schema)
    cleaned_schema = gen.clean_schema(cleaned_schema)
    assert TypeAdapter(type_).pydantic_complete  # Just to make sure it works and test setup is sane
    return schema, cleaned_schema


def test_simple_core_schema_with_no_references() -> None:
    init, cleaned = init_schema_and_cleaned_schema(list[int])
    assert init == cs.list_schema(cs.int_schema())
    assert cleaned == cs.list_schema(cs.int_schema())


@pytest.mark.parametrize('nested_ref', [False, True])
def test_core_schema_with_different_reference_depths_gets_inlined(nested_ref: bool) -> None:
    class M1(BaseModel):
        a: int

    class M2(BaseModel):
        b: M1

    init, cleaned = init_schema_and_cleaned_schema(list[M2] if nested_ref else M2)

    inner = IsPartialDict(type='definition-ref', schema_ref=Contains('M2'))
    assert init == (IsPartialDict(type='list', items_schema=inner) if nested_ref else inner)

    inner = IsPartialDict(
        type='model',
        cls=M2,
        schema=IsPartialDict(fields={'b': IsPartialDict(schema=IsPartialDict(type='model', cls=M1))}),
    )
    assert cleaned == (IsPartialDict(type='list', items_schema=inner) if nested_ref else inner)


@pytest.mark.parametrize('nested_ref', [False, True])
@pytest.mark.xfail(
    reason=(
        "While the cleaned schema is of type 'definitions', the inner schema is inlined. This is not an "
        'issue, but the test is kept so that we notice the change when tweaking core schema generation.'
    )
)
def test_core_schema_simple_recursive_schema_uses_refs(nested_ref: bool) -> None:
    class M1(BaseModel):
        a: 'M2'

    class M2(BaseModel):
        b: M1

    init, cleaned = init_schema_and_cleaned_schema(list[M1] if nested_ref else M1)

    inner = IsPartialDict(type='definition-ref', schema_ref=Contains('M1'))
    assert init == (IsPartialDict(type='list', items_schema=inner) if nested_ref else inner)

    inner = IsPartialDict(type='definition-ref', schema_ref=Contains('M1'))
    assert cleaned == IsPartialDict(
        type='definitions',
        schema=IsPartialDict(type='list', items_schema=inner) if nested_ref else inner,
        definitions=[IsPartialDict(type='model', ref=Contains('M1')), IsPartialDict(type='model', ref=Contains('M2'))],
    )


@pytest.mark.parametrize('nested_ref', [False, True])
def test_core_schema_with_deeply_nested_schema_with_multiple_references_gets_inlined(nested_ref: bool) -> None:
    class M1(BaseModel):
        a: int

    class M2(BaseModel):
        b: M1

    class M3(BaseModel):
        c: M2
        d: M1

    init, cleaned = init_schema_and_cleaned_schema(list[M3] if nested_ref else M3)

    inner = IsPartialDict(type='definition-ref', schema_ref=Contains('M3'))
    assert init == (IsPartialDict(type='list', items_schema=inner) if nested_ref else inner)

    inner = IsPartialDict(
        type='model',
        cls=M3,
        schema=IsPartialDict(
            fields={
                'c': IsPartialDict(schema=IsPartialDict(type='model', cls=M2)),
                'd': IsPartialDict(schema=IsPartialDict(type='model', cls=M1)),
            }
        ),
    )
    assert cleaned == (IsPartialDict(type='list', items_schema=inner) if nested_ref else inner)


@pytest.mark.parametrize('nested_ref', [False, True])
def test_core_schema_with_model_used_in_multiple_places(nested_ref: bool) -> None:
    class M1(BaseModel):
        a: int

    class M2(BaseModel):
        b: M1

    class M3(BaseModel):
        c: Union[M2, M1]
        d: M1

    init, cleaned = init_schema_and_cleaned_schema(list[M3] if nested_ref else M3)

    inner = IsPartialDict(type='definition-ref', schema_ref=Contains('M3'))
    assert init == (IsPartialDict(type='list', items_schema=inner) if nested_ref else inner)

    inner = IsPartialDict(type='model', cls=M3)
    assert cleaned == IsPartialDict(
        type='definitions',
        schema=(IsPartialDict(type='list', items_schema=inner) if nested_ref else inner),
        definitions=[IsPartialDict(type='model', cls=M1)],  # This was used in multiple places
    )


def test_representation_integrations():
    devtools = pytest.importorskip('devtools')

    @dataclass
    class Obj(Representation):
        int_attr: int = 42
        str_attr: str = 'Marvin'

    obj = Obj()

    if sys.version_info < (3, 11) or sys.implementation.name == 'pypy':
        assert str(devtools.debug.format(obj)).split('\n')[1:] == [
            '    Obj(',
            '        int_attr=42,',
            "        str_attr='Marvin',",
            '    ) (Obj)',
        ]
    else:
        assert str(devtools.debug.format(obj)).split('\n')[1:] == [
            '    obj: Obj(',
            '        int_attr=42,',
            "        str_attr='Marvin',",
            '    ) (Obj)',
        ]
    assert list(obj.__rich_repr__()) == [('int_attr', 42), ('str_attr', 'Marvin')]


@pytest.mark.parametrize(
    'decimal,decimal_places,digits',
    [
        (Decimal('0.0'), 1, 1),
        (Decimal('0.'), 0, 1),
        (Decimal('0.000'), 3, 3),
        (Decimal('0.0001'), 4, 4),
        (Decimal('.0001'), 4, 4),
        (Decimal('123.123'), 3, 6),
        (Decimal('123.1230'), 4, 7),
    ],
)
def test_decimal_digits_calculation(decimal: Decimal, decimal_places: int, digits: int) -> None:
    assert _extract_decimal_digits_info(decimal) == (decimal_places, digits)


@pytest.mark.parametrize(
    'value',
    [Decimal.from_float(float('nan')), 1.0],
)
def test_decimal_digits_calculation_type_error(value) -> None:
    with pytest.raises(TypeError, match=f'Unable to extract decimal digits info from supplied value {value}'):
        _extract_decimal_digits_info(value)


def test_update_js_extra_as_callable_when_existing_js_extra_is_dict_type():
    """
    It should ignore the callable with a warning.
    """
    metadata: dict[str, Any] = {}

    extra_dict: JsonDict = {'testKey': 'testValue'}

    def extra_func(schema: JsonDict) -> None:
        schema['testKey'] = 'testValue'

    update_core_metadata(metadata, pydantic_js_extra=extra_dict)

    with pytest.warns(PydanticJsonSchemaWarning):
        update_core_metadata(metadata, pydantic_js_extra=extra_func)
    assert metadata['pydantic_js_extra'] is extra_dict


def test_update_js_extra_as_callable_when_existing_js_extra_is_callable_type():
    """
    It should overwrite existing js_extra with the new callable.
    """
    metadata: dict[str, Any] = {}

    def extra_func1(schema: JsonDict) -> None:
        schema['testKey1'] = 'testValue1'

    def extra_func2(schema: JsonDict) -> None:
        schema['testKey2'] = 'testValue2'

    update_core_metadata(metadata, pydantic_js_extra=extra_func1)
    update_core_metadata(metadata, pydantic_js_extra=extra_func2)
    assert metadata['pydantic_js_extra'] is extra_func2


def test_pydantic_js_functions():
    metadata: dict[str, Any] = {}

    def func(schema: CoreSchema, handler: GetJsonSchemaHandler) -> JsonSchemaValue:
        return {'type': 'string'}

    update_core_metadata(
        metadata,
        pydantic_js_functions=[func],
    )

    assert metadata['pydantic_js_functions'] == [func]


class TestGitUtilities:
    """Tests for git utilities in pydantic._internal._git."""

    def test_is_git_repo_true(self, tmp_path):
        """Test is_git_repo returns True for directories with .git folder."""
        from pydantic._internal._git import is_git_repo

        # Create a fake .git directory
        git_dir = tmp_path / '.git'
        git_dir.mkdir()

        assert is_git_repo(tmp_path) is True

    def test_is_git_repo_false(self, tmp_path):
        """Test is_git_repo returns False for directories without .git folder."""
        from pydantic._internal._git import is_git_repo

        # tmp_path has no .git directory
        assert is_git_repo(tmp_path) is False

    def test_git_revision_returns_string(self):
        """Test git_revision returns a short hash string for a valid git repo."""
        from pathlib import Path

        from pydantic._internal._git import git_revision, is_git_repo

        # Use the pydantic repo itself for testing
        pydantic_dir = Path(__file__).parents[1]

        if is_git_repo(pydantic_dir):
            revision = git_revision(pydantic_dir)
            # Git short hash is typically 7-10 characters
            assert isinstance(revision, str)
            assert len(revision) >= 7
            assert len(revision) <= 12
            # Should only contain valid hex characters
            assert all(c in '0123456789abcdef' for c in revision.lower())
