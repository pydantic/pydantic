from enum import Enum

from pydantic_core import SchemaSerializer, core_schema


def test_json_or_python():
    def s1(v: int) -> int:
        return v + 1

    def s2(v: int) -> int:
        return v + 2

    s = SchemaSerializer(
        core_schema.json_or_python_schema(
            core_schema.int_schema(serialization=core_schema.plain_serializer_function_ser_schema(s1)),
            core_schema.int_schema(serialization=core_schema.plain_serializer_function_ser_schema(s2)),
        )
    )

    assert s.to_json(0) == b'1'
    assert s.to_python(0) == 2


def test_json_or_python_enum_dict_key():
    # See https://github.com/pydantic/pydantic/issues/6795
    class MyEnum(str, Enum):
        A = 'A'
        B = 'B'

    print(MyEnum('A'))

    s = SchemaSerializer(
        core_schema.dict_schema(
            core_schema.json_or_python_schema(
                core_schema.str_schema(), core_schema.no_info_after_validator_function(MyEnum, core_schema.str_schema())
            ),
            core_schema.int_schema(),
        )
    )

    assert s.to_json({MyEnum.A: 1, MyEnum.B: 2}) == b'{"A":1,"B":2}'
    assert s.to_python({MyEnum.A: 1, MyEnum.B: 2}) == {MyEnum.A: 1, MyEnum.B: 2}
