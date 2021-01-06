import sys

import pytest

from pydantic import BaseModel, conint
from pydantic.fragments import Fragment

skip_36 = pytest.mark.skipif(sys.version_info < (3, 7), reason='generics only supported for python 3.7 and above')


@pytest.fixture
def OriginalModel():
    class Cheese(BaseModel):
        name: str
        origin: str
        strength: conint(ge=0, le=10) = 5

    return Cheese


@skip_36
def test_fragment_of_model(OriginalModel):
    """Test that no ValidationError is raised for missing fields in Fragment."""
    Fragment[OriginalModel](name='Red Leicester')


@skip_36
def test_dict_export_of_fragment(OriginalModel):
    """Test that exporting a fragment instance includes only set fields."""
    expected = {'name': 'Stilton'}
    crumb = Fragment[OriginalModel](name='Stilton')
    assert crumb.dict() == expected


@skip_36
def test_schema_of_fragment(OriginalModel):
    """Test that the only differences to original schema are title and required."""
    fragment_schema = Fragment[OriginalModel].schema()
    title = fragment_schema.pop('title')
    required = fragment_schema.pop('required')
    title == 'CheeseFragment'
    required == []

    original_schema = OriginalModel.schema()
    original_schema.pop('title')
    original_schema.pop('required')
    assert str(fragment_schema) == str(original_schema)
