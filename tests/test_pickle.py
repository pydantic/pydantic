import dataclasses
import gc
import pickle
from typing import Optional, Type

import cloudpickle
import pytest

import pydantic
from pydantic import BaseModel, PositiveFloat, ValidationError
from pydantic._internal._model_construction import _PydanticWeakRef
from pydantic.config import ConfigDict


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
    'model_type,use_cloudpickle',
    [
        # Importable model can be pickled with either pickle or cloudpickle.
        (ImportableModel, False),
        (ImportableModel, True),
        # Locally-defined model can only be pickled with cloudpickle.
        (model_factory(), True),
    ],
)
def test_pickle_model(model_type: Type, use_cloudpickle: bool):
    if use_cloudpickle:
        model_type = cloudpickle.loads(cloudpickle.dumps(model_type))
    else:
        model_type = pickle.loads(pickle.dumps(model_type))

    m = model_type(foo='hi', val=1)
    assert m.foo == 'hi'
    assert m.bar is None
    assert m.val == 1.0

    if use_cloudpickle:
        m = cloudpickle.loads(cloudpickle.dumps(m))
    else:
        m = pickle.loads(pickle.dumps(m))

    assert m.foo == 'hi'
    assert m.bar is None
    assert m.val == 1.0

    with pytest.raises(ValidationError):
        model_type(foo='hi', val=-1.1)


class ImportableNestedModel(BaseModel):
    inner: ImportableModel


def nested_model_factory() -> Type:
    class NonImportableNestedModel(BaseModel):
        inner: ImportableModel

    return NonImportableNestedModel


@pytest.mark.parametrize(
    'model_type,use_cloudpickle',
    [
        # Importable model can be pickled with either pickle or cloudpickle.
        (ImportableNestedModel, False),
        (ImportableNestedModel, True),
        # Locally-defined model can only be pickled with cloudpickle.
        (nested_model_factory(), True),
    ],
)
def test_pickle_nested_model(model_type: Type, use_cloudpickle: bool):
    if use_cloudpickle:
        model_type = cloudpickle.loads(cloudpickle.dumps(model_type))
    else:
        model_type = pickle.loads(pickle.dumps(model_type))

    m = model_type(inner=ImportableModel(foo='hi', val=1))
    assert m.inner.foo == 'hi'
    assert m.inner.bar is None
    assert m.inner.val == 1.0

    if use_cloudpickle:
        m = cloudpickle.loads(cloudpickle.dumps(m))
    else:
        m = pickle.loads(pickle.dumps(m))

    assert m.inner.foo == 'hi'
    assert m.inner.bar is None
    assert m.inner.val == 1.0


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


class ImportableChildDataclass(ImportableDataclass):
    pass


def child_dataclass_factory() -> Type:
    class NonImportableChildDataclass(ImportableDataclass):
        pass

    return NonImportableChildDataclass


@pytest.mark.parametrize(
    'dataclass_type,use_cloudpickle',
    [
        # Importable Pydantic dataclass can be pickled with either pickle or cloudpickle.
        (ImportableDataclass, False),
        (ImportableDataclass, True),
        (ImportableChildDataclass, False),
        (ImportableChildDataclass, True),
        # Locally-defined Pydantic dataclass can only be pickled with cloudpickle.
        (dataclass_factory(), True),
        (child_dataclass_factory(), True),
        # Pydantic dataclass generated from builtin can only be pickled with cloudpickle.
        (pydantic.dataclasses.dataclass(ImportableBuiltinDataclass), True),
        # Pydantic dataclass generated from locally-defined builtin can only be pickled with cloudpickle.
        (pydantic.dataclasses.dataclass(builtin_dataclass_factory()), True),
    ],
)
def test_pickle_dataclass(dataclass_type: Type, use_cloudpickle: bool):
    if use_cloudpickle:
        dataclass_type = cloudpickle.loads(cloudpickle.dumps(dataclass_type))
    else:
        dataclass_type = pickle.loads(pickle.dumps(dataclass_type))

    d = dataclass_type('1', '2.5')
    assert d.a == 1
    assert d.b == 2.5

    if use_cloudpickle:
        d = cloudpickle.loads(cloudpickle.dumps(d))
    else:
        d = pickle.loads(pickle.dumps(d))

    assert d.a == 1
    assert d.b == 2.5

    d = dataclass_type(b=10, a=20)
    assert d.a == 20
    assert d.b == 10

    if use_cloudpickle:
        d = cloudpickle.loads(cloudpickle.dumps(d))
    else:
        d = pickle.loads(pickle.dumps(d))

    assert d.a == 20
    assert d.b == 10


class ImportableNestedDataclassModel(BaseModel):
    inner: ImportableBuiltinDataclass


def nested_dataclass_model_factory() -> Type:
    class NonImportableNestedDataclassModel(BaseModel):
        inner: ImportableBuiltinDataclass

    return NonImportableNestedDataclassModel


@pytest.mark.parametrize(
    'model_type,use_cloudpickle',
    [
        # Importable model can be pickled with either pickle or cloudpickle.
        (ImportableNestedDataclassModel, False),
        (ImportableNestedDataclassModel, True),
        # Locally-defined model can only be pickled with cloudpickle.
        (nested_dataclass_model_factory(), True),
    ],
)
def test_pickle_dataclass_nested_in_model(model_type: Type, use_cloudpickle: bool):
    if use_cloudpickle:
        model_type = cloudpickle.loads(cloudpickle.dumps(model_type))
    else:
        model_type = pickle.loads(pickle.dumps(model_type))

    m = model_type(inner=ImportableBuiltinDataclass(a=10, b=20))
    assert m.inner.a == 10
    assert m.inner.b == 20

    if use_cloudpickle:
        m = cloudpickle.loads(cloudpickle.dumps(m))
    else:
        m = pickle.loads(pickle.dumps(m))

    assert m.inner.a == 10
    assert m.inner.b == 20


class ImportableModelWithConfig(BaseModel):
    model_config = ConfigDict(title='MyTitle')


def model_with_config_factory() -> Type:
    class NonImportableModelWithConfig(BaseModel):
        model_config = ConfigDict(title='MyTitle')

    return NonImportableModelWithConfig


@pytest.mark.parametrize(
    'model_type,use_cloudpickle',
    [
        (ImportableModelWithConfig, False),
        (ImportableModelWithConfig, True),
        (model_with_config_factory(), True),
    ],
)
def test_pickle_model_with_config(model_type: Type, use_cloudpickle: bool):
    if use_cloudpickle:
        model_type = cloudpickle.loads(cloudpickle.dumps(model_type))
    else:
        model_type = pickle.loads(pickle.dumps(model_type))

    assert model_type.model_config['title'] == 'MyTitle'
