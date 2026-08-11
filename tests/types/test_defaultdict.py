import sys
from collections import defaultdict
from typing import Annotated, Any, TypeVar

import pytest
from pydantic_core import CoreSchema, core_schema
from typing_extensions import get_args  # noqa: UP035 (for `get_args`)

from pydantic import (
    Field,
    GetCoreSchemaHandler,
    PydanticSchemaGenerationError,
    TypeAdapter,
)


def test_typing_coercion_defaultdict():
    ta = TypeAdapter(defaultdict[int, str])

    d = defaultdict(str)
    d['1']
    v = ta.validate_python(d)
    assert isinstance(v, defaultdict)
    assert repr(v) == "defaultdict(<class 'str'>, {1: ''})"


def test_defaultdict_unknown_default_factory() -> None:
    """https://github.com/pydantic/pydantic/issues/4687"""
    with pytest.raises(
        PydanticSchemaGenerationError,
        match=r'Unable to infer a default factory for keys of type collections.defaultdict\[int, int\]',
    ):
        TypeAdapter(defaultdict[int, defaultdict[int, int]])


defaultdict_types_params = [
    (int, 0),
    (float, 0.0),
    (str, ''),
    (bool, False),
    (tuple, ()),
    (list[int], []),
    (list, []),
    (set, set()),
    (frozenset, frozenset()),
    (dict, {}),
]

if sys.version_info >= (3, 15):
    defaultdict_types_params.append((frozendict, frozendict()))  # noqa: F821


@pytest.mark.parametrize(
    ['default_factory_type', 'value'],
    defaultdict_types_params,
)
def test_defaultdict_infer_default_factory(default_factory_type: Any, value: Any) -> None:
    ta_list = TypeAdapter(defaultdict[int, default_factory_type])
    v = ta_list.validate_python({})
    assert v.default_factory is not None
    assert v.default_factory() == value


def test_defaultdict_explicit_default_factory() -> None:
    class MyList(list[int]):
        pass

    ta = TypeAdapter(defaultdict[int, Annotated[list[int], Field(default_factory=lambda: MyList())]])

    v = ta.validate_python({})
    assert v.default_factory is not None
    assert isinstance(v.default_factory(), MyList)


def test_defaultdict_default_factory_preserved() -> None:
    class MyList(list[int]):
        pass

    ta = TypeAdapter(defaultdict[int, list[int]])

    v = ta.validate_python(defaultdict(lambda: MyList()))
    assert v.default_factory is not None
    assert isinstance(v.default_factory(), MyList)


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
