from dataclasses import dataclass
from typing import Callable, Optional

import pytest
from typing_extensions import TypedDict

from pydantic_core import SchemaSerializer, SchemaValidator, core_schema


class ParentModel:
    x: int


class ChildModel(ParentModel):
    y: str


ParentModel.__pydantic_core_schema__ = core_schema.model_schema(
    ParentModel,
    core_schema.model_fields_schema(
        {
            'x': core_schema.model_field(core_schema.int_schema()),
        }
    ),
    ref='ParentModel',
)
ParentModel.__pydantic_validator__ = SchemaValidator(ParentModel.__pydantic_core_schema__)
ParentModel.__pydantic_serializer__ = SchemaSerializer(ParentModel.__pydantic_core_schema__)

ChildModel.__pydantic_core_schema__ = core_schema.model_schema(
    ChildModel,
    core_schema.model_fields_schema(
        {
            'x': core_schema.model_field(core_schema.int_schema()),
            'y': core_schema.model_field(core_schema.str_schema()),
        }
    ),
)
ChildModel.__pydantic_validator__ = SchemaValidator(ChildModel.__pydantic_core_schema__)
ChildModel.__pydantic_serializer__ = SchemaSerializer(ChildModel.__pydantic_core_schema__)


def test_serialize_as_any_with_models() -> None:
    child = ChildModel.__pydantic_validator__.validate_python({'x': 1, 'y': 'hopefully not a secret'})
    assert ParentModel.__pydantic_serializer__.to_python(child, serialize_as_any=False) == {'x': 1}
    assert ParentModel.__pydantic_serializer__.to_python(child, serialize_as_any=True) == {
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


def test_serialize_as_any_with_root_model_and_subclasses() -> None:
    class RModel:
        root: ParentModel

    RModel.__pydantic_core_schema__ = core_schema.model_schema(
        RModel,
        ParentModel.__pydantic_core_schema__,
        root_model=True,
    )
    RModel.__pydantic_validator__ = SchemaValidator(RModel.__pydantic_core_schema__)
    RModel.__pydantic_serializer__ = SchemaSerializer(RModel.__pydantic_core_schema__)

    value = RModel.__pydantic_validator__.validate_python({'x': 1})
    value.root = ChildModel.__pydantic_validator__.validate_python({'x': 1, 'y': 'hopefully not a secret'})

    assert RModel.__pydantic_serializer__.to_python(value, serialize_as_any=False) == {'x': 1}

    assert RModel.__pydantic_serializer__.to_python(value, serialize_as_any=True) == {
        'x': 1,
        'y': 'hopefully not a secret',
    }

    assert RModel.__pydantic_serializer__.to_json(value, serialize_as_any=False) == b'{"x":1}'
    assert (
        RModel.__pydantic_serializer__.to_json(value, serialize_as_any=True) == b'{"x":1,"y":"hopefully not a secret"}'
    )


def test_serialize_with_custom_type_and_subclasses():
    class CustomType:
        value: ParentModel

    CustomType.__pydantic_core_schema__ = core_schema.model_schema(
        CustomType,
        core_schema.model_fields_schema(
            {
                'value': core_schema.model_field(ParentModel.__pydantic_core_schema__),
            }
        ),
    )

    CustomType.__pydantic_validator__ = SchemaValidator(CustomType.__pydantic_core_schema__)
    CustomType.__pydantic_serializer__ = SchemaSerializer(CustomType.__pydantic_core_schema__)

    value = CustomType.__pydantic_validator__.validate_python({'value': {'x': 1}})
    value.value = ChildModel.__pydantic_validator__.validate_python({'x': 1, 'y': 'hopefully not a secret'})

    assert CustomType.__pydantic_serializer__.to_python(value, serialize_as_any=False) == {
        'value': {'x': 1},
    }
    assert CustomType.__pydantic_serializer__.to_python(value, serialize_as_any=True) == {
        'value': {'x': 1, 'y': 'hopefully not a secret'}
    }

    assert CustomType.__pydantic_serializer__.to_json(value, serialize_as_any=False) == b'{"value":{"x":1}}'
    assert (
        CustomType.__pydantic_serializer__.to_json(value, serialize_as_any=True)
        == b'{"value":{"x":1,"y":"hopefully not a secret"}}'
    )


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


@pytest.fixture(params=['model', 'dataclass'])
def container_schema_builder(
    request: pytest.FixtureRequest,
) -> Callable[[dict[str, core_schema.CoreSchema]], core_schema.CoreSchema]:
    if request.param == 'model':
        return lambda fields: core_schema.model_schema(
            cls=type('Test', (), {}),
            schema=core_schema.model_fields_schema(
                fields={k: core_schema.model_field(schema=v) for k, v in fields.items()},
            ),
        )
    elif request.param == 'dataclass':
        return lambda fields: core_schema.dataclass_schema(
            cls=dataclass(type('Test', (), {})),
            schema=core_schema.dataclass_args_schema(
                'Test',
                fields=[core_schema.dataclass_field(name=k, schema=v) for k, v in fields.items()],
            ),
            fields=[k for k in fields.keys()],
        )
    else:
        raise ValueError(f'Unknown container type {request.param}')


def test_serialize_as_any_with_field_serializer(container_schema_builder) -> None:
    # https://github.com/pydantic/pydantic/issues/12379

    schema = container_schema_builder(
        {
            'value': core_schema.int_schema(
                serialization=core_schema.plain_serializer_function_ser_schema(
                    lambda model, v: v * 2, is_field_serializer=True
                )
            )
        }
    )

    v = SchemaValidator(schema).validate_python({'value': 123})
    cls = type(v)
    s = SchemaSerializer(schema)
    # necessary to ensure that type inference will pick up the serializer
    cls.__pydantic_serializer__ = s

    assert s.to_python(v, serialize_as_any=False) == {'value': 246}
    assert s.to_python(v, serialize_as_any=True) == {'value': 246}
    assert s.to_json(v, serialize_as_any=False) == b'{"value":246}'
    assert s.to_json(v, serialize_as_any=True) == b'{"value":246}'


def test_serialize_as_any_with_field_serializer_root_model() -> None:
    """https://github.com/pydantic/pydantic/issues/12379."""

    schema = core_schema.model_schema(
        type('Test', (), {}),
        core_schema.int_schema(
            serialization=core_schema.plain_serializer_function_ser_schema(
                lambda model, v: v * 2, is_field_serializer=True
            )
        ),
        root_model=True,
    )

    v = SchemaValidator(schema).validate_python(123)
    cls = type(v)
    s = SchemaSerializer(schema)
    # necessary to ensure that type inference will pick up the serializer
    cls.__pydantic_serializer__ = s

    assert s.to_python(v, serialize_as_any=False) == 246
    assert s.to_python(v, serialize_as_any=True) == 246
    assert s.to_json(v, serialize_as_any=False) == b'246'
    assert s.to_json(v, serialize_as_any=True) == b'246'
