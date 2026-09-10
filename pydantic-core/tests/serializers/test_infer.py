from enum import Enum

from pydantic_core import SchemaSerializer, core_schema


# serializing enum calls methods in serializers::infer
def test_infer_to_python():
    class MyEnum(Enum):
        complex_ = complex(1, 2)

    v = SchemaSerializer(core_schema.enum_schema(MyEnum, list(MyEnum.__members__.values())))
    assert v.to_python(MyEnum.complex_, mode='json') == '1+2j'


def test_infer_serialize():
    class MyEnum(Enum):
        complex_ = complex(1, 2)

    v = SchemaSerializer(core_schema.enum_schema(MyEnum, list(MyEnum.__members__.values())))
    assert v.to_json(MyEnum.complex_) == b'"1+2j"'


def test_infer_json_key():
    class MyEnum(Enum):
        complex_ = {complex(1, 2): 1}

    v = SchemaSerializer(core_schema.enum_schema(MyEnum, list(MyEnum.__members__.values())))
    assert v.to_json(MyEnum.complex_) == b'{"1+2j":1}'


# https://github.com/pydantic/pydantic/issues/13734
# Objects with a `__getattr__` that never raises AttributeError (e.g.
# unittest.mock.call) get classified as ObType::PydanticSerializable because
# `hasattr(value, '__pydantic_serializer__')` returns True, even though the
# attribute isn't actually a SchemaSerializer. This used to raise a bare
# TypeError instead of using the `fallback`.
def test_infer_to_python_fallback_on_fake_pydantic_serializer():
    from unittest.mock import call

    v = SchemaSerializer(core_schema.any_schema())
    mock_call = call(1, 2, 3)
    assert v.to_python(mock_call, fallback=lambda c: list(c.args)) == [1, 2, 3]


def test_infer_serialize_fallback_on_fake_pydantic_serializer():
    from unittest.mock import call

    v = SchemaSerializer(core_schema.any_schema())
    mock_call = call(1, 2, 3)
    assert v.to_json(mock_call, fallback=lambda c: list(c.args)) == b'[1,2,3]'


def test_infer_to_python_no_fallback_on_fake_pydantic_serializer_raises():
    from unittest.mock import call
    import pytest
    from pydantic_core import PydanticSerializationError

    v = SchemaSerializer(core_schema.any_schema())
    mock_call = call(1, 2, 3)
    with pytest.raises(PydanticSerializationError):
        v.to_python(mock_call)
