from typing import Union

import pytest

from pydantic import (
    BaseModel,
    ConfigDict,
    SerializationInfo,
    TypeAdapter,
    ValidationInfo,
    field_validator,
    model_serializer,
)


@pytest.mark.parametrize('config', [True, False, None])
@pytest.mark.parametrize('runtime', [True, False, None])
def test_polymorphic_serialization(config: Union[bool, None], runtime: Union[bool, None]) -> None:
    class ModelA(BaseModel):
        if config is not None:
            model_config = ConfigDict(polymorphic_serialization=config)

        a: int

    class ModelB(ModelA):
        b: str

    kwargs = {}
    if runtime is not None:
        kwargs['polymorphic_serialization'] = runtime

    serializer = TypeAdapter(ModelA).serializer

    assert serializer.to_python(ModelA(a=123), **kwargs) == {'a': 123}
    assert serializer.to_json(ModelA(a=123), **kwargs) == b'{"a":123}'

    polymorphism_enabled = runtime if runtime is not None else config
    if polymorphism_enabled:
        assert serializer.to_python(ModelB(a=123, b='test'), **kwargs) == {'a': 123, 'b': 'test'}
        assert serializer.to_json(ModelB(a=123, b='test'), **kwargs) == b'{"a":123,"b":"test"}'
    else:
        assert serializer.to_python(ModelB(a=123, b='test'), **kwargs) == {'a': 123}
        assert serializer.to_json(ModelB(a=123, b='test'), **kwargs) == b'{"a":123}'


@pytest.mark.parametrize('config', [True, False, None])
@pytest.mark.parametrize('runtime', [True, False, None])
def test_polymorphic_serialization_with_model_serializer(config: bool, runtime: bool) -> None:
    class ModelA(BaseModel):
        if config is not None:
            model_config = ConfigDict(polymorphic_serialization=config)

        a: int

        @model_serializer
        def serialize(self, info: SerializationInfo) -> str:
            assert info.polymorphic_serialization is runtime
            return 'ModelA'

    class ModelB(ModelA):
        b: str

        @model_serializer
        def serialize(self, info: SerializationInfo) -> str:
            assert info.polymorphic_serialization is runtime
            return 'ModelB'

    kwargs = {}
    if runtime is not None:
        kwargs['polymorphic_serialization'] = runtime

    serializer = TypeAdapter(ModelA).serializer

    kwargs = {}
    if runtime is not None:
        kwargs['polymorphic_serialization'] = runtime

    assert serializer.to_python(ModelA(a=123), **kwargs) == 'ModelA'
    assert serializer.to_json(ModelA(a=123), **kwargs) == b'"ModelA"'

    polymorphism_enabled = runtime if runtime is not None else config
    if polymorphism_enabled:
        assert serializer.to_python(ModelB(a=123, b='test'), **kwargs) == 'ModelB'
        assert serializer.to_json(ModelB(a=123, b='test'), **kwargs) == b'"ModelB"'
    else:
        assert serializer.to_python(ModelB(a=123, b='test'), **kwargs) == 'ModelA'
        assert serializer.to_json(ModelB(a=123, b='test'), **kwargs) == b'"ModelA"'


def test_model_validate_by_json_with_validation_info_data():
    """https://github.com/pydantic/pydantic/issues/13074"""

    class Foo(BaseModel):
        field1: int
        field2: int

        @field_validator('field2')
        @classmethod
        def _validate_field2(cls, v: str, info: ValidationInfo) -> int:
            return v + info.data['field1']

    f1 = Foo.model_validate({'field1': 1, 'field2': 2})
    f2 = Foo.model_validate_json('{"field1": 1, "field2": 2}')

    assert f1.field1 == f2.field1 == 1
    assert f1.field2 == f2.field2 == 3
