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
