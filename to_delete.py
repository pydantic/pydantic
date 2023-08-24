# to_delete.py

from pydantic import BaseModel, ConfigDict, Field
# from typing import Union, Optional, Dict, Mapping, Sequence
import typing
from collections import abc
import types


class Test(BaseModel):
    a: float
    b: int

class TestWithExtra(BaseModel):
    a: float
    b: int
    extra: str

class TestNoExtra(BaseModel):
    a: float
    b: int
    model_config = ConfigDict(extra="forbid")

class Standard(BaseModel):
    model: Test
    c: int

class TestUnion(BaseModel):
    model: typing.Union[Test, None]
    c: int

class TestUnionDefault(BaseModel):
    model: typing.Union[Test, None] = None
    c: int

class TestUnionType(BaseModel):
    model: Test | None
    c: int

class TestOptional(BaseModel):
    model: typing.Optional[Test] = None
    c: int

class PickFirst(BaseModel):
    model: Test | TestWithExtra
    c: int

class PickCorrect(BaseModel):
    model: TestNoExtra | TestWithExtra
    c: int

class TestTuple(BaseModel):
    tup: tuple[int, Test] # multiple type, explicit order

class TestNestedTuple(BaseModel):
    tup: tuple[int, tuple[int, Test]]

class TestTupleEllipsis(BaseModel):
    tup: tuple[Test, ...]

class TestList(BaseModel):
    lis: list[Test] # single type

class TestNestedList(BaseModel):
    lis: list[Test | list[Test]]

class TestNestedSequence(BaseModel):
    lis: typing.Sequence[Test | typing.Sequence[Test]]

class TestDict(BaseModel):
    map: dict[str, Test] # key -> value, single type

class TestTypingDict(BaseModel):
    map: typing.Dict[str, Test]

class TestTypingMapping(BaseModel):
    map: typing.Mapping[str, Test]

class TestTypingMutableMapping(BaseModel):
    map: abc.MutableMapping[str, Test]

# class TestSet(BaseModel):
#     grp: set[Test]

# class TestTypingSet(BaseModel):
#     grp: typing.Set[Test]

# class TestABCSet(BaseModel):
#     grp: abc.Set[Test]


def main():
    # simple annotation
    instance = Standard(model=Test(a=1.3, b=321), c=9)
    instance_construct = Standard.model_construct(**instance.model_dump(), _recursive=True)
    print(instance)
    print(instance_construct)
    assert instance == instance_construct
    assert instance.model_dump() == instance_construct.model_dump()
    assert instance.model_dump_json() == instance_construct.model_dump_json()

    assert instance.model_fields_set == instance_construct.model_fields_set
    assert instance.model.model_fields_set == instance_construct.model.model_fields_set

    # union annotation with value
    instance = TestUnion(model=Test(a=1.3, b=321), c=9)
    instance_construct = TestUnion.model_construct(**instance.model_dump(), _recursive=True)
    print(instance)
    print(instance_construct)
    assert instance == instance_construct
    assert instance.model_dump() == instance_construct.model_dump()
    assert instance.model_dump_json() == instance_construct.model_dump_json()

    # union with none value
    instance = TestUnion(model=None, c=9)
    instance_construct = TestUnion.model_construct(**instance.model_dump(), _recursive=True)
    print(instance)
    print(instance_construct)
    assert instance == instance_construct
    assert instance.model_dump() == instance_construct.model_dump()
    assert instance.model_dump_json() == instance_construct.model_dump_json()

    # union with default
    instance = TestUnionDefault(c=9)
    instance_construct = TestUnionDefault.model_construct(**instance.model_dump(), _recursive=True)
    print(instance)
    print(instance_construct)
    assert instance == instance_construct
    assert instance.model_dump() == instance_construct.model_dump()
    assert instance.model_dump_json() == instance_construct.model_dump_json()

    # optional
    instance = TestOptional(c=9)
    instance_construct = TestOptional.model_construct(**instance.model_dump(), _recursive=True)
    print(instance)
    print(instance_construct)
    assert instance == instance_construct
    assert instance.model_dump() == instance_construct.model_dump()
    assert instance.model_dump_json() == instance_construct.model_dump_json()

    # union of multiple that might fit
    instance = PickFirst(model=TestWithExtra(a=1.3, b=321, extra="some string"), c=9)
    instance_construct = PickFirst.model_construct(**instance.model_dump(), _recursive=True)
    print(instance)
    print(instance_construct)
    assert instance != instance_construct
    # First class `Test` was selected from the union instead of `TestWithExtra`
    assert type(instance_construct.model) is Test
    assert isinstance(instance_construct.model, Test)

    # TODO: discriminators
    # Correct result when forbidding extra attributes
    # instance = PickCorrect(model=TestWithExtra(a=1.3, b=321, extra="some string"), c=9)
    # instance_construct = PickCorrect.model_construct(**instance.model_dump(), _recursive=True)
    # print(instance)
    # print(instance_construct)
    # assert instance == instance_construct
    # assert instance.model_dump() == instance_construct.model_dump()
    # assert instance.model_dump_json() == instance_construct.model_dump_json()

    # annotated tuple
    instance = TestTuple(tup=(10, Test(a=1.3, b=321)))
    instance_construct = TestTuple.model_construct(**instance.model_dump(), _recursive=True)
    print(instance)
    print(instance_construct)
    assert instance == instance_construct
    assert instance.model_dump() == instance_construct.model_dump()
    assert instance.model_dump_json() == instance_construct.model_dump_json()

    # nested tuple
    instance = TestNestedTuple(tup=(10, (20, Test(a=1.3, b=321))))
    instance_construct = TestNestedTuple.model_construct(**instance.model_dump(), _recursive=True)
    print(instance)
    print(instance_construct)
    assert instance == instance_construct
    assert instance.model_dump() == instance_construct.model_dump()
    assert instance.model_dump_json() == instance_construct.model_dump_json()   

    # tuple with ellipsis
    instance = TestTupleEllipsis(tup=(Test(a=1.3, b=321), Test(a=1.3, b=321)))
    instance_construct = TestTupleEllipsis.model_construct(**instance.model_dump(), _recursive=True)
    print(instance)
    print(instance_construct)
    assert instance == instance_construct
    assert instance.model_dump() == instance_construct.model_dump()
    assert instance.model_dump_json() == instance_construct.model_dump_json()

    # don't complain when not passed a tuple
    incorrect_instance = {"tup": (10, "incorrect")}
    instance_construct = TestTuple.model_construct(**incorrect_instance, _recursive=True)
    print(instance_construct)
    incorrect_instance = {"tup": (10, (20, "incorrect"))}
    instance_construct = TestNestedTuple.model_construct(**incorrect_instance, _recursive=True)
    print(instance_construct)

    # annotated list
    instance = TestList(lis=[Test(a=1.3, b=321), Test(a=2.3, b=322)])
    instance_construct = TestList.model_construct(**instance.model_dump(), _recursive=True)
    print(instance)
    print(instance_construct)
    assert instance == instance_construct
    assert instance.model_dump() == instance_construct.model_dump()
    assert instance.model_dump_json() == instance_construct.model_dump_json()

    # nested list
    instance = TestNestedList(lis=[Test(a=1.3, b=321), [Test(a=2.3, b=322)]])
    instance_construct = TestNestedList.model_construct(**instance.model_dump(), _recursive=True)
    print(instance)
    print(instance_construct)
    assert instance == instance_construct
    assert instance.model_dump() == instance_construct.model_dump()
    assert instance.model_dump_json() == instance_construct.model_dump_json() 

    # nested sequence
    instance = TestNestedSequence(lis=[Test(a=1.3, b=321), [Test(a=2.3, b=322)]])
    instance_construct = TestNestedSequence.model_construct(**instance.model_dump(), _recursive=True)
    print(instance)
    print(instance_construct)
    assert instance == instance_construct
    assert instance.model_dump() == instance_construct.model_dump()
    assert instance.model_dump_json() == instance_construct.model_dump_json() 

    # annotated dict
    instance = TestDict(map={"test": Test(a=1.3, b=321)})
    instance_construct = TestDict.model_construct(**instance.model_dump(), _recursive=True)
    print(instance)
    print(instance_construct)
    assert instance == instance_construct
    assert instance.model_dump() == instance_construct.model_dump()
    assert instance.model_dump_json() == instance_construct.model_dump_json() 

    # typing dict
    instance = TestTypingDict(map={"test": Test(a=1.3, b=321)})
    instance_construct = TestTypingDict.model_construct(**instance.model_dump(), _recursive=True)
    print(instance)
    print(instance_construct)
    assert instance == instance_construct
    assert instance.model_dump() == instance_construct.model_dump()
    assert instance.model_dump_json() == instance_construct.model_dump_json() 

    # typing mapping
    instance = TestTypingMapping(map={"test": Test(a=1.3, b=321)})
    instance_construct = TestTypingMapping.model_construct(**instance.model_dump(), _recursive=True)
    print(instance)
    print(instance_construct)
    assert instance == instance_construct
    assert instance.model_dump() == instance_construct.model_dump()
    assert instance.model_dump_json() == instance_construct.model_dump_json()

    print("test")
    print(issubclass(abc.MutableMapping, abc.Mapping))

    # typing mutablemapping
    instance = TestTypingMutableMapping(map={"test": Test(a=1.3, b=321)})
    instance_construct = TestTypingMutableMapping.model_construct(**instance.model_dump(), _recursive=True)
    print(instance)
    print(instance_construct)
    assert instance == instance_construct
    assert instance.model_dump() == instance_construct.model_dump()
    assert instance.model_dump_json() == instance_construct.model_dump_json()

    class TestAlias(BaseModel):
        model: Test = Field(..., alias="model_alias")

    instance = TestAlias(model_alias=Test(a=1.3, b=321))
    instance_construct = TestAlias.model_construct(**instance.model_dump(), _recursive=True)
    print(instance)
    print(instance_construct)
    assert instance == instance_construct
    assert instance.model_dump() == instance_construct.model_dump()
    assert instance.model_dump_json() == instance_construct.model_dump_json()

    # generic list types
    class AnotherModel(BaseModel):
        lis: typing.List[Test | abc.Sequence[Test]]
    
    instance = AnotherModel(lis=[Test(a=1.3, b=321), [Test(a=2.3, b=322)]])
    instance_construct = AnotherModel.model_construct(**instance.model_dump(), _recursive=True)
    print(instance)
    print(instance_construct)
    assert instance == instance_construct
    assert instance.model_dump() == instance_construct.model_dump()
    assert instance.model_dump_json() == instance_construct.model_dump_json()

    # unions: each argument is iterated over and attempted to be coerced to a model;
    # the resulting model is the first one that succeeds.

    # instance_construct.model_dump() # Now should no longer raise annoying warnings

    # class MapTest(BaseModel):
    #     some_map: dict[Test, Test]

    # instance = MapTest(some_map={Test(a=1.3, b=321): Test(a=1.3, b=321)})


if __name__ == "__main__":
    main()