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
    ta = TypeAdapter(defaultdict[int, str])

    d = defaultdict(str)
    d['1']
    v = ta.validate_python(d)
    assert isinstance(v, defaultdict)
    assert repr(v) == "defaultdict(<class 'str'>, {1: ''})"


def test_defaultdict_unknown_default_factory() -> None:
    """
    https://github.com/pydantic/pydantic/issues/4687
    """
    with pytest.raises(
        PydanticSchemaGenerationError,
        match=r'Unable to infer a default factory for keys of type collections.defaultdict\[int, int\]',
    ):
        TypeAdapter(defaultdict[int, defaultdict[int, int]])


def test_defaultdict_infer_default_factory() -> None:
    ta_list = TypeAdapter(defaultdict[int, list[int]])
    v = ta_list.validate_python({})
    assert v.default_factory is not None
    assert v.default_factory() == []

    ta_int = TypeAdapter(defaultdict[int, int])
    v = ta_int.validate_python({})
    assert v.default_factory is not None
    assert v.default_factory() == 0

    ta_set = TypeAdapter(defaultdict[int, set])
    v = ta_set.validate_python({})
    assert v.default_factory is not None
    assert v.default_factory() == set()

    ta_dict = TypeAdapter(defaultdict[str, dict])
    v = ta_dict.validate_python({})
    assert v.default_factory is not None
    assert v.default_factory() == {}
    v['a']['b'] = 1
    assert v == {'a': {'b': 1}}

    ta_dict_params = TypeAdapter(defaultdict[str, dict[str, int]])
    v = ta_dict_params.validate_python({})
    assert v.default_factory is not None
    assert v.default_factory() == {}

    ta_frozenset = TypeAdapter(defaultdict[str, frozenset])
    v = ta_frozenset.validate_python({})
    assert v.default_factory is not None
    assert v.default_factory() == frozenset()

    ta_frozenset_params = TypeAdapter(defaultdict[str, frozenset[int]])
    v = ta_frozenset_params.validate_python({})
    assert v.default_factory is not None
    assert v.default_factory() == frozenset()


def test_defaultdict_dict_value_on_model() -> None:
    """https://github.com/pydantic/pydantic/issues/13617"""

    class ModelWithDefault(BaseModel):
        prop: defaultdict[str, dict] = defaultdict(dict)

    # Schema generation used to fail while constructing the class.
    m = ModelWithDefault()
    m.prop['a']['b'] = 1
    assert m.prop == {'a': {'b': 1}}
    # Class-level defaultdict default is copied per instance.
    assert ModelWithDefault().prop == {}

    class Model(BaseModel):
        prop: defaultdict[str, dict]

    # Plain mapping input uses the inferred factory (not factory preservation).
    m2 = Model.model_validate({'prop': {'x': {'y': 2}}})
    assert isinstance(m2.prop, defaultdict)
    assert m2.prop['x'] == {'y': 2}
    assert m2.prop.default_factory is not None
    assert m2.prop.default_factory() == {}
    m2.prop['missing']['k'] = 1
    assert m2.prop['missing'] == {'k': 1}


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
