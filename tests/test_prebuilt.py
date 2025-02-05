from pydantic_core import SchemaSerializer, SchemaValidator, core_schema


def test_prebuilt_val_and_ser_used() -> None:
    class InnerModel:
        x: int

    inner_schema = core_schema.model_schema(
        InnerModel,
        schema=core_schema.model_fields_schema(
            {'x': core_schema.model_field(schema=core_schema.int_schema())},
        ),
    )

    inner_schema_validator = SchemaValidator(inner_schema)
    inner_schema_serializer = SchemaSerializer(inner_schema)
    InnerModel.__pydantic_complete__ = True  # pyright: ignore[reportAttributeAccessIssue]
    InnerModel.__pydantic_validator__ = inner_schema_validator  # pyright: ignore[reportAttributeAccessIssue]
    InnerModel.__pydantic_serializer__ = inner_schema_serializer  # pyright: ignore[reportAttributeAccessIssue]

    class OuterModel:
        inner: InnerModel

    outer_schema = core_schema.model_schema(
        OuterModel,
        schema=core_schema.model_fields_schema(
            {
                'inner': core_schema.model_field(
                    schema=core_schema.model_schema(
                        InnerModel,
                        schema=core_schema.model_fields_schema(
                            # note, we use str schema here even though that's incorrect
                            # in order to verify that the prebuilt validator is used
                            # off of InnerModel with the correct int schema, not this str schema
                            {'x': core_schema.model_field(schema=core_schema.str_schema())},
                        ),
                    )
                )
            }
        ),
    )

    outer_validator = SchemaValidator(outer_schema)
    outer_serializer = SchemaSerializer(outer_schema)

    result = outer_validator.validate_python({'inner': {'x': 1}})
    assert result.inner.x == 1
    assert outer_serializer.to_python(result) == {'inner': {'x': 1}}
