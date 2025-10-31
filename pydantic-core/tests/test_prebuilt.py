from typing import Union

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

    inner_validator = SchemaValidator(inner_schema)
    inner_serializer = SchemaSerializer(inner_schema)
    InnerModel.__pydantic_complete__ = True  # pyright: ignore[reportAttributeAccessIssue]
    InnerModel.__pydantic_validator__ = inner_validator  # pyright: ignore[reportAttributeAccessIssue]
    InnerModel.__pydantic_serializer__ = inner_serializer  # pyright: ignore[reportAttributeAccessIssue]

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


def test_prebuilt_not_used_for_wrap_serializer_functions() -> None:
    class InnerModel:
        x: str

        def __init__(self, x: str) -> None:
            self.x = x

    def serialize_inner(v: InnerModel, serializer) -> Union[dict[str, str], str]:
        v.x = v.x + ' modified'
        return serializer(v)

    inner_schema = core_schema.model_schema(
        InnerModel,
        schema=core_schema.model_fields_schema(
            {'x': core_schema.model_field(schema=core_schema.str_schema())},
        ),
        serialization=core_schema.wrap_serializer_function_ser_schema(serialize_inner),
    )

    inner_serializer = SchemaSerializer(inner_schema)
    InnerModel.__pydantic_complete__ = True  # pyright: ignore[reportAttributeAccessIssue]
    InnerModel.__pydantic_serializer__ = inner_serializer  # pyright: ignore[reportAttributeAccessIssue]

    class OuterModel:
        inner: InnerModel

        def __init__(self, inner: InnerModel) -> None:
            self.inner = inner

    outer_schema = core_schema.model_schema(
        OuterModel,
        schema=core_schema.model_fields_schema(
            {
                'inner': core_schema.model_field(
                    schema=core_schema.model_schema(
                        InnerModel,
                        schema=core_schema.model_fields_schema(
                            # note, we use a simple str schema (with no custom serialization)
                            # in order to verify that the prebuilt serializer from InnerModel is not used
                            {'x': core_schema.model_field(schema=core_schema.str_schema())},
                        ),
                    )
                )
            }
        ),
    )

    outer_serializer = SchemaSerializer(outer_schema)

    # the custom serialization function does apply for the inner model
    inner_instance = InnerModel(x='hello')
    assert inner_serializer.to_python(inner_instance) == {'x': 'hello modified'}

    # but the outer model doesn't reuse the custom wrap serializer function, so we see simple str ser
    outer_instance = OuterModel(inner=InnerModel(x='hello'))
    assert outer_serializer.to_python(outer_instance) == {'inner': {'x': 'hello'}}


def test_prebuilt_not_used_for_wrap_validator_functions() -> None:
    class InnerModel:
        x: str

        def __init__(self, x: str) -> None:
            self.x = x

    def validate_inner(data, validator) -> InnerModel:
        data['x'] = data['x'] + ' modified'
        return validator(data)

    inner_schema = core_schema.no_info_wrap_validator_function(
        validate_inner,
        core_schema.model_schema(
            InnerModel,
            schema=core_schema.model_fields_schema(
                {'x': core_schema.model_field(schema=core_schema.str_schema())},
            ),
        ),
    )

    inner_validator = SchemaValidator(inner_schema)
    InnerModel.__pydantic_complete__ = True  # pyright: ignore[reportAttributeAccessIssue]
    InnerModel.__pydantic_validator__ = inner_validator  # pyright: ignore[reportAttributeAccessIssue]

    class OuterModel:
        inner: InnerModel

        def __init__(self, inner: InnerModel) -> None:
            self.inner = inner

    outer_schema = core_schema.model_schema(
        OuterModel,
        schema=core_schema.model_fields_schema(
            {
                'inner': core_schema.model_field(
                    schema=core_schema.model_schema(
                        InnerModel,
                        schema=core_schema.model_fields_schema(
                            # note, we use a simple str schema (with no custom validation)
                            # in order to verify that the prebuilt validator from InnerModel is not used
                            {'x': core_schema.model_field(schema=core_schema.str_schema())},
                        ),
                    )
                )
            }
        ),
    )

    outer_validator = SchemaValidator(outer_schema)

    # the custom validation function does apply for the inner model
    result_inner = inner_validator.validate_python({'x': 'hello'})
    assert result_inner.x == 'hello modified'

    # but the outer model doesn't reuse the custom wrap validator function, so we see simple str val
    result_outer = outer_validator.validate_python({'inner': {'x': 'hello'}})
    assert result_outer.inner.x == 'hello'


def test_prebuilt_not_used_for_after_validator_functions() -> None:
    class InnerModel:
        x: str

        def __init__(self, x: str) -> None:
            self.x = x

    def validate_after(self) -> InnerModel:
        self.x = self.x + ' modified'
        return self

    inner_schema = core_schema.no_info_after_validator_function(
        validate_after,
        core_schema.model_schema(
            InnerModel,
            schema=core_schema.model_fields_schema(
                {'x': core_schema.model_field(schema=core_schema.str_schema())},
            ),
        ),
    )

    inner_validator = SchemaValidator(inner_schema)
    InnerModel.__pydantic_complete__ = True  # pyright: ignore[reportAttributeAccessIssue]
    InnerModel.__pydantic_validator__ = inner_validator  # pyright: ignore[reportAttributeAccessIssue]

    class OuterModel:
        inner: InnerModel

        def __init__(self, inner: InnerModel) -> None:
            self.inner = inner

    outer_schema = core_schema.model_schema(
        OuterModel,
        schema=core_schema.model_fields_schema(
            {
                'inner': core_schema.model_field(
                    schema=core_schema.model_schema(
                        InnerModel,
                        schema=core_schema.model_fields_schema(
                            # note, we use a simple str schema (with no custom validation)
                            # in order to verify that the prebuilt validator from InnerModel is not used
                            {'x': core_schema.model_field(schema=core_schema.str_schema())},
                        ),
                    )
                )
            }
        ),
    )

    outer_validator = SchemaValidator(outer_schema)

    # the custom validation function does apply for the inner model
    result_inner = inner_validator.validate_python({'x': 'hello'})
    assert result_inner.x == 'hello modified'

    # but the outer model doesn't reuse the custom after validator function, so we see simple str val
    result_outer = outer_validator.validate_python({'inner': {'x': 'hello'}})
    assert result_outer.inner.x == 'hello'


def test_reuse_plain_serializer_ok() -> None:
    class InnerModel:
        x: str

        def __init__(self, x: str) -> None:
            self.x = x

    def serialize_inner(v: InnerModel) -> str:
        return v.x + ' modified'

    inner_schema = core_schema.model_schema(
        InnerModel,
        schema=core_schema.model_fields_schema(
            {'x': core_schema.model_field(schema=core_schema.str_schema())},
        ),
        serialization=core_schema.plain_serializer_function_ser_schema(serialize_inner),
    )

    inner_serializer = SchemaSerializer(inner_schema)
    InnerModel.__pydantic_complete__ = True  # pyright: ignore[reportAttributeAccessIssue]
    InnerModel.__pydantic_serializer__ = inner_serializer  # pyright: ignore[reportAttributeAccessIssue]

    class OuterModel:
        inner: InnerModel

        def __init__(self, inner: InnerModel) -> None:
            self.inner = inner

    outer_schema = core_schema.model_schema(
        OuterModel,
        schema=core_schema.model_fields_schema(
            {
                'inner': core_schema.model_field(
                    schema=core_schema.model_schema(
                        InnerModel,
                        schema=core_schema.model_fields_schema(
                            # note, we use a simple str schema (with no custom serialization)
                            # in order to verify that the prebuilt serializer from InnerModel is used instead
                            {'x': core_schema.model_field(schema=core_schema.str_schema())},
                        ),
                    )
                )
            }
        ),
    )

    outer_serializer = SchemaSerializer(outer_schema)

    # the custom serialization function does apply for the inner model
    inner_instance = InnerModel(x='hello')
    assert inner_serializer.to_python(inner_instance) == 'hello modified'
    assert 'FunctionPlainSerializer' in repr(inner_serializer)

    # the custom ser function applies for the outer model as well, a plain serializer is permitted as a prebuilt candidate
    outer_instance = OuterModel(inner=InnerModel(x='hello'))
    assert outer_serializer.to_python(outer_instance) == {'inner': 'hello modified'}
    assert 'PrebuiltSerializer' in repr(outer_serializer)


def test_reuse_plain_validator_ok() -> None:
    class InnerModel:
        x: str

        def __init__(self, x: str) -> None:
            self.x = x

    def validate_inner(data) -> InnerModel:
        data['x'] = data['x'] + ' modified'
        return InnerModel(**data)

    inner_schema = core_schema.no_info_plain_validator_function(validate_inner)

    inner_validator = SchemaValidator(inner_schema)
    InnerModel.__pydantic_complete__ = True  # pyright: ignore[reportAttributeAccessIssue]
    InnerModel.__pydantic_validator__ = inner_validator  # pyright: ignore[reportAttributeAccessIssue]

    class OuterModel:
        inner: InnerModel

        def __init__(self, inner: InnerModel) -> None:
            self.inner = inner

    outer_schema = core_schema.model_schema(
        OuterModel,
        schema=core_schema.model_fields_schema(
            {
                'inner': core_schema.model_field(
                    schema=core_schema.model_schema(
                        InnerModel,
                        schema=core_schema.model_fields_schema(
                            # note, we use a simple str schema (with no custom validation)
                            # in order to verify that the prebuilt validator from InnerModel is used instead
                            {'x': core_schema.model_field(schema=core_schema.str_schema())},
                        ),
                    )
                )
            }
        ),
    )

    outer_validator = SchemaValidator(outer_schema)

    # the custom validation function does apply for the inner model
    result_inner = inner_validator.validate_python({'x': 'hello'})
    assert result_inner.x == 'hello modified'
    assert 'FunctionPlainValidator' in repr(inner_validator)

    # the custom validation function does apply for the outer model as well, a plain validator is permitted as a prebuilt candidate
    result_outer = outer_validator.validate_python({'inner': {'x': 'hello'}})
    assert result_outer.inner.x == 'hello modified'
    assert 'PrebuiltValidator' in repr(outer_validator)


def test_reuse_before_validator_ok() -> None:
    class InnerModel:
        x: str

        def __init__(self, x: str) -> None:
            self.x = x

    def validate_before(data) -> dict:
        data['x'] = data['x'] + ' modified'
        return data

    inner_schema = core_schema.no_info_before_validator_function(
        validate_before,
        core_schema.model_schema(
            InnerModel,
            schema=core_schema.model_fields_schema(
                {'x': core_schema.model_field(schema=core_schema.str_schema())},
            ),
        ),
    )

    inner_validator = SchemaValidator(inner_schema)
    InnerModel.__pydantic_complete__ = True  # pyright: ignore[reportAttributeAccessIssue]
    InnerModel.__pydantic_validator__ = inner_validator  # pyright: ignore[reportAttributeAccessIssue]

    class OuterModel:
        inner: InnerModel

        def __init__(self, inner: InnerModel) -> None:
            self.inner = inner

    outer_schema = core_schema.model_schema(
        OuterModel,
        schema=core_schema.model_fields_schema(
            {
                'inner': core_schema.model_field(
                    schema=core_schema.model_schema(
                        InnerModel,
                        schema=core_schema.model_fields_schema(
                            # note, we use a simple str schema (with no custom validation)
                            # in order to verify that the prebuilt validator from InnerModel is used instead
                            {'x': core_schema.model_field(schema=core_schema.str_schema())},
                        ),
                    )
                )
            }
        ),
    )

    outer_validator = SchemaValidator(outer_schema)
    print(inner_validator)
    print(outer_validator)

    # the custom validation function does apply for the inner model
    result_inner = inner_validator.validate_python({'x': 'hello'})
    assert result_inner.x == 'hello modified'
    assert 'FunctionBeforeValidator' in repr(inner_validator)

    # the custom validation function does apply for the outer model as well, a before validator is permitted as a prebuilt candidate
    result_outer = outer_validator.validate_python({'inner': {'x': 'hello'}})
    assert result_outer.inner.x == 'hello modified'
    assert 'PrebuiltValidator' in repr(outer_validator)
