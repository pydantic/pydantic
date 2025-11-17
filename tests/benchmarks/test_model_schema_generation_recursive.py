from typing import Generic, Literal, Optional, TypeVar, Union

import pytest

from pydantic import Field

from .shared import DeferredModel, rebuild_model


@pytest.mark.benchmark(group='model_schema_generation_recursive')
def test_simple_recursive_model_schema_generation(benchmark):
    class Foo(DeferredModel):
        a: int = 123
        sibling: 'Foo' = None

    benchmark(rebuild_model, Foo)


@pytest.mark.benchmark(group='model_schema_generation_recursive')
def test_generic_recursive_model_schema_generation(benchmark):
    T = TypeVar('T')

    class GenericFoo(DeferredModel, Generic[T]):
        value: T
        sibling: Optional['GenericFoo[T]'] = None

    benchmark(rebuild_model, GenericFoo[int])


@pytest.mark.benchmark(group='model_schema_generation_recursive')
def test_nested_recursive_model_schema_generation(benchmark):
    class Node(DeferredModel):
        value: int
        left: Optional['Node'] = None
        right: Optional['Node'] = None

    class Tree(DeferredModel):
        root: Node
        metadata: dict[str, 'Tree'] = Field(default_factory=dict)

    benchmark(rebuild_model, Tree)


@pytest.mark.benchmark(group='model_schema_generation_recursive')
def test_nested_recursive_generic_model_schema_generation(benchmark):
    T = TypeVar('T')

    class GenericNode(DeferredModel, Generic[T]):
        value: T
        left: Optional['GenericNode[T]'] = None
        right: Optional['GenericNode[T]'] = None

    class GenericTree(DeferredModel, Generic[T]):
        root: GenericNode[T]
        metadata: 'dict[str, GenericTree[T]]' = Field(default_factory=dict)

    benchmark(rebuild_model, GenericTree[int])


@pytest.mark.benchmark(group='model_schema_generation_recursive')
def test_recursive_discriminated_union_with_base_model(benchmark) -> None:
    class Foo(DeferredModel):
        type: Literal['foo']
        x: 'Foobar'

    class Bar(DeferredModel):
        type: Literal['bar']

    class Foobar(DeferredModel):
        value: Union[Foo, Bar] = Field(discriminator='type')

    benchmark(rebuild_model, Foobar)


@pytest.mark.benchmark(group='model_schema_generation_recursive')
def test_deeply_nested_recursive_model_schema_generation(benchmark):
    class A(DeferredModel):
        b: 'B'

    class B(DeferredModel):
        c: 'C'

    class C(DeferredModel):
        a: Optional['A']

    benchmark(rebuild_model, C)
