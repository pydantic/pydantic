from enum import IntEnum
from pydantic import BaseModel

class MyEnum(IntEnum):
    A = 1
    B = 2

class Model(BaseModel):
    data: dict[MyEnum, int]

def test_enum_key_schema():
    schema = Model.model_json_schema()
    prop_names = schema["properties"]["data"].get("propertyNames", {})
    assert "$ref" in prop_names
    assert prop_names["$ref"] == "#/$defs/MyEnum"
    defs = schema.get("$defs", {})
    my_enum = defs.get("MyEnum", {})
    assert my_enum.get("type") == "integer"



