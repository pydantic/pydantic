from collections import defaultdict
from typing import Annotated, Any, TypeVar

import pytest
from pydantic_core import CoreSchema, core_schema
from typing_extensions import get_args  # noqa: UP035 (for `get_args`)

from pydantic import (
    BaseModel,
    Field,
    GetCoreSchemaHandler,
    PydanticSchemaGenerationError,
    TypeAdapter,
)


def test_typing_coercion_defaultdict():
    class Model(BaseModel):
        x: defaultdict[int, str]

    d = defaultdict(str)
    d['1']
    m = Model(x=d)
    assert isinstance(m.x, defaultdict)
    assert repr(m.x) == "defaultdict(<class 'str'>, {1: ''})"


def test_defaultdict_unknown_default_factory() -> None:
    """
    https://github.com/pydantic/pydantic/issues/4687
    """
    with pytest.raises(
        PydanticSchemaGenerationError,
        match=r'Unable to infer a default factory for keys of type collections.defaultdict\[int, int\]',
    ):

        class Model(BaseModel):
            d: defaultdict[int, defaultdict[int, int]]


def test_defaultdict_infer_default_factory() -> None:
    class Model(BaseModel):
        a: defaultdict[int, list[int]]
        b: defaultdict[int, int]
        c: defaultdict[int, set]

    m = Model(a={}, b={}, c={})
    assert m.a.default_factory is not None
    assert m.a.default_factory() == []
    assert m.b.default_factory is not None
    assert m.b.default_factory() == 0
    assert m.c.default_factory is not None
    assert m.c.default_factory() == set()


def test_defaultdict_explicit_default_factory() -> None:
    class MyList(list[int]):
        pass

    class Model(BaseModel):
        a: defaultdict[int, Annotated[list[int], Field(default_factory=lambda: MyList())]]

    m = Model(a={})
    assert m.a.default_factory is not None
    assert isinstance(m.a.default_factory(), MyList)


def test_defaultdict_default_factory_preserved() -> None:
    class Model(BaseModel):
        a: defaultdict[int, list[int]]

    class MyList(list[int]):
        pass

    m = Model(a=defaultdict(lambda: MyList()))
    assert m.a.default_factory is not None
    assert isinstance(m.a.default_factory(), MyList)


def test_custom_default_dict() -> None:
    KT = TypeVar('KT')
    VT = TypeVar('VT')

    class CustomDefaultDict(defaultdict[KT, VT]):
        @classmethod
        def __get_pydantic_core_schema__(cls, source_type: Any, handler: GetCoreSchemaHandler) -> CoreSchema:
            keys_type, values_type = get_args(source_type)
            return core_schema.no_info_after_validator_function(
                lambda x: cls(x.default_factory, x), handler(defaultdict[keys_type, values_type])
            )

    ta = TypeAdapter(CustomDefaultDict[str, int])

    assert ta.validate_python({'a': 1}) == CustomDefaultDict(int, {'a': 1})
