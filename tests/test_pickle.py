import dataclasses
import gc
import pickle
from typing import Optional, Type

import cloudpickle
import pytest

import pydantic
from pydantic import BaseModel, PositiveFloat, ValidationError
from pydantic._internal._model_construction import _PydanticWeakRef


class IntWrapper:
    def __init__(self, v: int):
        self._v = v

    def get(self) -> int:
        return self._v

    def __eq__(self, other: 'IntWrapper') -> bool:
        return self.get() == other.get()


def test_pickle_pydantic_weakref():
    obj1 = IntWrapper(1)
    ref1 = _PydanticWeakRef(obj1)
    assert ref1() is obj1

    obj2 = IntWrapper(2)
    ref2 = _PydanticWeakRef(obj2)
    assert ref2() is obj2

    ref3 = _PydanticWeakRef(IntWrapper(3))
    gc.collect()  # PyPy does not use reference counting and always relies on GC.
    assert ref3() is None

    d = {
        # Hold a hard reference to the underlying object for ref1 that will also
        # be pickled.
        'hard_ref': obj1,
        # ref1's underlying object has a hard reference in the pickled object so it
        # should maintain the reference after deserialization.
        'has_hard_ref': ref1,
        # ref2's underlying object has no hard reference in the pickled object so it
        # should be `None` after deserialization.
        'has_no_hard_ref': ref2,
        # ref3's underlying object had already gone out of scope before pickling so it
        # should be `None` after deserialization.
        'ref_out_of_scope': ref3,
    }

    loaded = pickle.loads(pickle.dumps(d))
    gc.collect()  # PyPy does not use reference counting and always relies on GC.

    assert loaded['hard_ref'] == IntWrapper(1)
    assert loaded['has_hard_ref']() is loaded['hard_ref']
    assert loaded['has_no_hard_ref']() is None
    assert loaded['ref_out_of_scope']() is None


class ImportableModel(BaseModel):
    foo: str
    bar: Optional[str] = None
    val: PositiveFloat = 0.7

def model_factory() -> Type:
    class NonImportableModel(BaseModel):
        foo: str
        bar: Optional[str] = None
        val: PositiveFloat = 0.7

    return NonImportableModel

@pytest.mark.parametrize(
    "model_type,use_cloudpickle", [(ImportableModel, False), (model_factory(), True)]
)
def test_pickle_base_model(model_type: Type, use_cloudpickle: bool):
    if use_cloudpickle:
        model_type = cloudpickle.loads(cloudpickle.dumps(model_type))
    else:
        model_type = pickle.loads(pickle.dumps(model_type))

    m = model_type(foo="hi", val=1)
    assert m.foo == "hi"
    assert m.bar is None
    assert m.val == 1.0

    with pytest.raises(ValidationError):
        model_type(foo="hi", val=-1.1)


@pydantic.dataclasses.dataclass
class ImportableDataclass:
    a: int
    b: float

def dataclass_factory() -> Type:
    @pydantic.dataclasses.dataclass
    class NonImportableDataclass:
        a: int
        b: float

    return NonImportableDataclass

@dataclasses.dataclass
class ImportableBuiltinDataclass:
    a: int
    b: float

def builtin_dataclass_factory() -> Type:
    @dataclasses.dataclass
    class NonImportableBuiltinDataclass:
        a: int
        b: float

    return NonImportableBuiltinDataclass

@pytest.mark.parametrize(
    "dataclass_type,use_cloudpickle", [
        (ImportableDataclass, False),
        (dataclass_factory(), True),
        (pydantic.dataclasses.dataclass(ImportableBuiltinDataclass), True),
        (pydantic.dataclasses.dataclass(builtin_dataclass_factory()), True)
    ]
)
def test_pickle_dataclass(dataclass_type: Type, use_cloudpickle: bool):
    if use_cloudpickle:
        dataclass_type = cloudpickle.loads(cloudpickle.dumps(dataclass_type))
    else:
        dataclass_type = pickle.loads(pickle.dumps(dataclass_type))

    d = dataclass_type('1', '2.5')
    assert d.a == 1
    assert d.b == 2.5

    d = dataclass_type(b=10, a=20)
    assert d.a == 20
    assert d.b == 10
