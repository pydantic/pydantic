import sys
from typing import Callable

import pytest
from typing_extensions import Annotated

from pydantic import BaseModel, Field, TypeAdapter, ValidationError

collection_callable_types = [Callable, Callable[[int], int]]
if sys.version_info >= (3, 9):
    from collections.abc import Callable as CollectionsCallable

    collection_callable_types += [CollectionsCallable, CollectionsCallable[[int], int]]


@pytest.mark.parametrize('annotation', collection_callable_types)
def test_callable(annotation):
    class Model(BaseModel):
        callback: annotation

    m = Model(callback=lambda x: x)
    assert callable(m.callback)


@pytest.mark.parametrize('annotation', collection_callable_types)
def test_non_callable(annotation):
    class Model(BaseModel):
        callback: annotation

    with pytest.raises(ValidationError):
        Model(callback=1)


def test_description_in_callable_schema() -> None:
    FooType = Annotated[int, Field(default=1, description='foo type description')]

    def func(foo: FooType):
        ...

    # Description is lost 🤔
    json_schema = TypeAdapter(func).json_schema()
    assert json_schema['properties']['foo']['description'] == 'foo type description'
