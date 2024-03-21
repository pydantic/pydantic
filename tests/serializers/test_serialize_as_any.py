from dataclasses import dataclass

from typing_extensions import TypedDict

from pydantic_core import SchemaSerializer, SchemaValidator, core_schema


def test_serialize_as_any_with_models() -> None:
    class Parent:
        x: int

    class Child(Parent):
        y: str

    Parent.__pydantic_core_schema__ = core_schema.model_schema(
        Parent,
        core_schema.model_fields_schema(
            {
                'x': core_schema.model_field(core_schema.int_schema()),
            }
        ),
    )
    Parent.__pydantic_validator__ = SchemaValidator(Parent.__pydantic_core_schema__)
    Parent.__pydantic_serializer__ = SchemaSerializer(Parent.__pydantic_core_schema__)

    Child.__pydantic_core_schema__ = core_schema.model_schema(
        Child,
        core_schema.model_fields_schema(
            {
                'x': core_schema.model_field(core_schema.int_schema()),
                'y': core_schema.model_field(core_schema.str_schema()),
            }
        ),
    )
    Child.__pydantic_validator__ = SchemaValidator(Child.__pydantic_core_schema__)
    Child.__pydantic_serializer__ = SchemaSerializer(Child.__pydantic_core_schema__)

    child = Child.__pydantic_validator__.validate_python({'x': 1, 'y': 'hopefully not a secret'})
    assert Parent.__pydantic_serializer__.to_python(child, serialize_as_any=False) == {'x': 1}
    assert Parent.__pydantic_serializer__.to_python(child, serialize_as_any=True) == {
        'x': 1,
        'y': 'hopefully not a secret',
    }


def test_serialize_as_any_with_dataclass() -> None:
    @dataclass
    class Parent:
        x: int

    class Child(Parent):
        y: str

    Parent.__pydantic_core_schema__ = core_schema.dataclass_schema(
        Parent,
        core_schema.dataclass_args_schema(
            'Parent',
            [
                core_schema.dataclass_field(name='x', schema=core_schema.int_schema()),
            ],
        ),
        ['x'],
    )
    Parent.__pydantic_validator__ = SchemaValidator(Parent.__pydantic_core_schema__)
    Parent.__pydantic_serializer__ = SchemaSerializer(Parent.__pydantic_core_schema__)

    Child.__pydantic_core_schema__ = core_schema.dataclass_schema(
        Child,
        core_schema.dataclass_args_schema(
            'Child',
            [
                core_schema.dataclass_field(name='x', schema=core_schema.int_schema()),
                core_schema.dataclass_field(name='y', schema=core_schema.str_schema()),
            ],
        ),
        ['x', 'y'],
    )
    Child.__pydantic_validator__ = SchemaValidator(Child.__pydantic_core_schema__)
    Child.__pydantic_serializer__ = SchemaSerializer(Child.__pydantic_core_schema__)

    child = Child.__pydantic_validator__.validate_python({'x': 1, 'y': 'hopefully not a secret'})
    assert Parent.__pydantic_serializer__.to_python(child, serialize_as_any=False) == {'x': 1}
    assert Parent.__pydantic_serializer__.to_python(child, serialize_as_any=True) == {
        'x': 1,
        'y': 'hopefully not a secret',
    }


def test_serialize_as_any_with_typeddict() -> None:
    class Parent(TypedDict):
        x: int

    class Child(Parent):
        y: str

    Parent.__pydantic_core_schema__ = core_schema.typed_dict_schema(
        {
            'x': core_schema.typed_dict_field(core_schema.int_schema()),
        }
    )
    Parent.__pydantic_validator__ = SchemaValidator(Parent.__pydantic_core_schema__)
    Parent.__pydantic_serializer__ = SchemaSerializer(Parent.__pydantic_core_schema__)

    Child.__pydantic_core_schema__ = core_schema.typed_dict_schema(
        {
            'x': core_schema.typed_dict_field(core_schema.int_schema()),
            'y': core_schema.typed_dict_field(core_schema.str_schema()),
        }
    )
    Child.__pydantic_validator__ = SchemaValidator(Child.__pydantic_core_schema__)
    Child.__pydantic_serializer__ = SchemaSerializer(Child.__pydantic_core_schema__)

    child = Child.__pydantic_validator__.validate_python({'x': 1, 'y': 'hopefully not a secret'})
    assert Parent.__pydantic_serializer__.to_python(child, serialize_as_any=False) == {'x': 1}
    assert Parent.__pydantic_serializer__.to_python(child, serialize_as_any=True) == {
        'x': 1,
        'y': 'hopefully not a secret',
    }


def test_serialize_as_any_with_unrelated_models() -> None:
    class Parent:
        x: int

    class Other:
        y: str

    Parent.__pydantic_core_schema__ = core_schema.model_schema(
        Parent,
        core_schema.model_fields_schema(
            {
                'x': core_schema.model_field(core_schema.int_schema()),
            }
        ),
    )
    Parent.__pydantic_validator__ = SchemaValidator(Parent.__pydantic_core_schema__)
    Parent.__pydantic_serializer__ = SchemaSerializer(Parent.__pydantic_core_schema__)

    Other.__pydantic_core_schema__ = core_schema.model_schema(
        Other,
        core_schema.model_fields_schema(
            {
                'y': core_schema.model_field(core_schema.str_schema()),
            }
        ),
        config=core_schema.CoreConfig(extra_fields_behavior='allow'),
    )
    Other.__pydantic_validator__ = SchemaValidator(Other.__pydantic_core_schema__)
    Other.__pydantic_serializer__ = SchemaSerializer(Other.__pydantic_core_schema__)

    other = Other.__pydantic_validator__.validate_python({'x': 1, 'y': 'hopefully not a secret'})
    assert Parent.__pydantic_serializer__.to_python(other, serialize_as_any=False) == {}
    # note, without extra='allow', the 'x' field would not be included, as it's not in the schema
    assert Parent.__pydantic_serializer__.to_python(other, serialize_as_any=True) == {
        'x': 1,
        'y': 'hopefully not a secret',
    }
