import typing
from collections.abc import Callable as CollectionsCallable

import pytest

from pydantic import BaseModel, ValidationError

collection_callable_types = [
    pytest.param(typing.Callable, id='typing_Callable'),
    pytest.param(typing.Callable[[int], int], id='typing_Callable_parameterized'),
    pytest.param(CollectionsCallable, id='collections_abc_Callable'),
    pytest.param(CollectionsCallable[[int], int], id='collections_abc_Callable_parameterized'),
]


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
