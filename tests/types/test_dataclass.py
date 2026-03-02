import dataclasses
from typing import Any

import pytest

import pydantic
from pydantic import ConfigDict, SerializationInfo, TypeAdapter, model_serializer


@pytest.mark.parametrize('config', [True, False, None])
@pytest.mark.parametrize('runtime', [True, False, None])
@pytest.mark.parametrize('dataclass_decorator', [dataclasses.dataclass, pydantic.dataclasses.dataclass])
def test_polymorphic_serialization(config: bool, runtime: bool, dataclass_decorator: Any) -> None:
    @dataclass_decorator
    class ClassA:
        if config is not None:
            __pydantic_config__ = ConfigDict(polymorphic_serialization=config)

        a: int

    @dataclass_decorator
    class ClassB(ClassA):
        b: str

    kwargs = {}
    if runtime is not None:
        kwargs['polymorphic_serialization'] = runtime

    serializer = TypeAdapter(ClassA).serializer

    assert serializer.to_python(ClassA(a=123), **kwargs) == {'a': 123}
    assert serializer.to_json(ClassA(a=123), **kwargs) == b'{"a":123}'

    polymorphism_enabled = runtime if runtime is not None else config
    # FIXME: stdlib dataclass does not serialize with polymorphism yet
    if polymorphism_enabled and dataclass_decorator is pydantic.dataclasses.dataclass:
        assert serializer.to_python(ClassB(a=123, b='test'), **kwargs) == {'a': 123, 'b': 'test'}
        assert serializer.to_json(ClassB(a=123, b='test'), **kwargs) == b'{"a":123,"b":"test"}'
    else:
        assert serializer.to_python(ClassB(a=123, b='test'), **kwargs) == {'a': 123}
        assert serializer.to_json(ClassB(a=123, b='test'), **kwargs) == b'{"a":123}'


@pytest.mark.parametrize('config', [True, False, None])
@pytest.mark.parametrize('runtime', [True, False, None])
@pytest.mark.parametrize('dataclass_decorator', [dataclasses.dataclass, pydantic.dataclasses.dataclass])
def test_polymorphic_serialization_with_model_serializer(config: bool, runtime: bool, dataclass_decorator: Any) -> None:
    @dataclass_decorator
    class ClassA:
        if config is not None:
            __pydantic_config__ = ConfigDict(polymorphic_serialization=config)

        a: int

        @model_serializer
        def serialize(self, info: SerializationInfo) -> str:
            assert info.polymorphic_serialization is runtime
            return 'ClassA'

    @dataclass_decorator
    class ClassB(ClassA):
        b: str

        @model_serializer
        def serialize(self, info: SerializationInfo) -> str:
            assert info.polymorphic_serialization is runtime
            return 'ClassB'

    kwargs = {}
    if runtime is not None:
        kwargs['polymorphic_serialization'] = runtime

    serializer = TypeAdapter(ClassA).serializer

    kwargs = {}
    if runtime is not None:
        kwargs['polymorphic_serialization'] = runtime

    assert serializer.to_python(ClassA(a=123), **kwargs) == 'ClassA'
    assert serializer.to_json(ClassA(a=123), **kwargs) == b'"ClassA"'

    polymorphism_enabled = runtime if runtime is not None else config
    # FIXME: stdlib dataclass does not serialize with polymorphism yet
    if polymorphism_enabled and dataclass_decorator is pydantic.dataclasses.dataclass:
        assert serializer.to_python(ClassB(a=123, b='test'), **kwargs) == 'ClassB'
        assert serializer.to_json(ClassB(a=123, b='test'), **kwargs) == b'"ClassB"'
    else:
        assert serializer.to_python(ClassB(a=123, b='test'), **kwargs) == 'ClassA'
        assert serializer.to_json(ClassB(a=123, b='test'), **kwargs) == b'"ClassA"'
