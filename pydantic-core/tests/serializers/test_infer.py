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
