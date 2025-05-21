from dataclasses import dataclass
from typing import Optional

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


def test_serialize_as_any_with_nested_models() -> None:
    class Parent:
        x: int

    class Other(Parent):
        y: str

    class Outer:
        p: Parent

    Parent.__pydantic_core_schema__ = core_schema.model_schema(
        Parent,
        core_schema.model_fields_schema(
            {
                'x': core_schema.model_field(core_schema.int_schema()),
            }
        ),
        ref='Parent',
    )
    Parent.__pydantic_validator__ = SchemaValidator(Parent.__pydantic_core_schema__)
    Parent.__pydantic_serializer__ = SchemaSerializer(Parent.__pydantic_core_schema__)

    Other.__pydantic_core_schema__ = core_schema.model_schema(
        Other,
        core_schema.model_fields_schema(
            {
                'x': core_schema.model_field(core_schema.int_schema()),
                'y': core_schema.model_field(core_schema.str_schema()),
            }
        ),
        config=core_schema.CoreConfig(extra_fields_behavior='allow'),
    )
    Other.__pydantic_validator__ = SchemaValidator(Other.__pydantic_core_schema__)
    Other.__pydantic_serializer__ = SchemaSerializer(Other.__pydantic_core_schema__)

    Outer.__pydantic_core_schema__ = core_schema.definitions_schema(
        core_schema.model_schema(
            Outer,
            core_schema.model_fields_schema(
                {
                    'p': core_schema.model_field(core_schema.definition_reference_schema('Parent')),
                }
            ),
        ),
        [
            Parent.__pydantic_core_schema__,
        ],
    )
    Outer.__pydantic_validator__ = SchemaValidator(Outer.__pydantic_core_schema__)
    Outer.__pydantic_serializer__ = SchemaSerializer(Outer.__pydantic_core_schema__)

    other = Other.__pydantic_validator__.validate_python({'x': 1, 'y': 'hopefully not a secret'})
    outer = Outer()
    outer.p = other

    assert Outer.__pydantic_serializer__.to_python(outer, serialize_as_any=False) == {
        'p': {'x': 1},
    }
    assert Outer.__pydantic_serializer__.to_python(outer, serialize_as_any=True) == {
        'p': {
            'x': 1,
            'y': 'hopefully not a secret',
        }
    }

    assert Outer.__pydantic_serializer__.to_json(outer, serialize_as_any=False) == b'{"p":{"x":1}}'
    assert (
        Outer.__pydantic_serializer__.to_json(outer, serialize_as_any=True)
        == b'{"p":{"x":1,"y":"hopefully not a secret"}}'
    )


def test_serialize_with_recursive_models() -> None:
    class Node:
        next: Optional['Node'] = None
        value: int = 42

    schema = core_schema.definitions_schema(
        core_schema.definition_reference_schema('Node'),
        [
            core_schema.model_schema(
                Node,
                core_schema.model_fields_schema(
                    {
                        'value': core_schema.model_field(
                            core_schema.with_default_schema(core_schema.int_schema(), default=42)
                        ),
                        'next': core_schema.model_field(
                            core_schema.with_default_schema(
                                core_schema.nullable_schema(core_schema.definition_reference_schema('Node')),
                                default=None,
                            )
                        ),
                    }
                ),
                ref='Node',
            )
        ],
    )

    Node.__pydantic_core_schema__ = schema
    Node.__pydantic_validator__ = SchemaValidator(Node.__pydantic_core_schema__)
    Node.__pydantic_serializer__ = SchemaSerializer(Node.__pydantic_core_schema__)
    other = Node.__pydantic_validator__.validate_python({'next': {'value': 4}})

    assert Node.__pydantic_serializer__.to_python(other, serialize_as_any=False) == {
        'next': {'next': None, 'value': 4},
        'value': 42,
    }
    assert Node.__pydantic_serializer__.to_python(other, serialize_as_any=True) == {
        'next': {'next': None, 'value': 4},
        'value': 42,
    }


def test_serialize_with_custom_type_and_subclasses():
    class Node:
        x: int

    Node.__pydantic_core_schema__ = core_schema.model_schema(
        Node,
        core_schema.model_fields_schema(
            {
                'x': core_schema.model_field(core_schema.int_schema()),
            }
        ),
        ref='Node',
    )
    Node.__pydantic_validator__ = SchemaValidator(Node.__pydantic_core_schema__)
    Node.__pydantic_serializer__ = SchemaSerializer(Node.__pydantic_core_schema__)

    class NodeSubClass(Node):
        y: int

    NodeSubClass.__pydantic_core_schema__ = core_schema.model_schema(
        NodeSubClass,
        core_schema.model_fields_schema(
            {
                'x': core_schema.model_field(core_schema.int_schema()),
                'y': core_schema.model_field(core_schema.int_schema()),
            }
        ),
    )
    NodeSubClass.__pydantic_validator__ = SchemaValidator(NodeSubClass.__pydantic_core_schema__)
    NodeSubClass.__pydantic_serializer__ = SchemaSerializer(NodeSubClass.__pydantic_core_schema__)

    class CustomType:
        values: list[Node]

    CustomType.__pydantic_core_schema__ = core_schema.model_schema(
        CustomType,
        core_schema.definitions_schema(
            core_schema.model_fields_schema(
                {
                    'values': core_schema.model_field(
                        core_schema.list_schema(core_schema.definition_reference_schema('Node'))
                    ),
                }
            ),
            [
                Node.__pydantic_core_schema__,
            ],
        ),
    )
    CustomType.__pydantic_validator__ = SchemaValidator(CustomType.__pydantic_core_schema__)
    CustomType.__pydantic_serializer__ = SchemaSerializer(CustomType.__pydantic_core_schema__)

    value = CustomType.__pydantic_validator__.validate_python({'values': [{'x': 1}, {'x': 2}]})
    value.values.append(NodeSubClass.__pydantic_validator__.validate_python({'x': 3, 'y': 4}))

    assert CustomType.__pydantic_serializer__.to_python(value, serialize_as_any=False) == {
        'values': [{'x': 1}, {'x': 2}, {'x': 3}],
    }
    assert CustomType.__pydantic_serializer__.to_python(value, serialize_as_any=True) == {
        'values': [{'x': 1}, {'x': 2}, {'x': 3, 'y': 4}],
    }


def test_serialize_as_any_wrap_serializer_applied_once() -> None:
    # https://github.com/pydantic/pydantic/issues/11139

    class InnerModel:
        an_inner_field: int

    InnerModel.__pydantic_core_schema__ = core_schema.model_schema(
        InnerModel,
        core_schema.model_fields_schema({'an_inner_field': core_schema.model_field(core_schema.int_schema())}),
    )
    InnerModel.__pydantic_validator__ = SchemaValidator(InnerModel.__pydantic_core_schema__)
    InnerModel.__pydantic_serializer__ = SchemaSerializer(InnerModel.__pydantic_core_schema__)

    class MyModel:
        a_field: InnerModel

        def a_model_serializer(self, handler, info):
            return {k + '_wrapped': v for k, v in handler(self).items()}

    MyModel.__pydantic_core_schema__ = core_schema.model_schema(
        MyModel,
        core_schema.model_fields_schema({'a_field': core_schema.model_field(InnerModel.__pydantic_core_schema__)}),
        serialization=core_schema.wrap_serializer_function_ser_schema(
            MyModel.a_model_serializer,
            info_arg=True,
        ),
    )
    MyModel.__pydantic_validator__ = SchemaValidator(MyModel.__pydantic_core_schema__)
    MyModel.__pydantic_serializer__ = SchemaSerializer(MyModel.__pydantic_core_schema__)

    instance = MyModel.__pydantic_validator__.validate_python({'a_field': {'an_inner_field': 1}})
    assert MyModel.__pydantic_serializer__.to_python(instance, serialize_as_any=True) == {
        'a_field_wrapped': {'an_inner_field': 1},
    }
