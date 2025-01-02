!!! note
    This section is part of the *internals* documentation, and is partly targeted to contributors.

Starting with Pydantic V2, part of the codebase is written in Rust in a separate package called `pydantic-core`.
This was done partly in order to improve validation and serialization performance (with the cost of limited
customization and extendibility of the internal logic).

This architecture documentation will first cover how the two `pydantic` and `pydantic-core` packages interact
together, then will go through the architecture specifics for various patterns (model definition, validation,
serialization, JSON Schema).

Usage of the Pydantic library can be divided into two parts:

- Model definition, done in the `pydantic` package.
- Model validation and serialization, done in the `pydantic-core` package.

## Model definition

Whenever a Pydantic [`BaseModel`][pydantic.main.BaseModel] is defined, the metaclass
will analyze the body of the model to collect a number of elements:

- Defined annotations to build model fields (collected in the [`model_fields`][pydantic.main.BaseModel.model_fields] attribute).
- Model configuration, set with [`model_config`][pydantic.main.BaseModel.model_config].
- Additional validators/serializers.
- Private attributes, class variables, identification of generic parametrization, etc.

### Communicating between `pydantic` and `pydantic-core`: the core schema

We then need a way to communicate the collected information from the model definition to `pydantic-core`,
so that validation and serialization is performed accordingly. To do so, Pydantic uses the concept
of a core schema: a structured (and serializable) Python dictionary (represented using
[`TypedDict`][typing.TypedDict] definitions) describing a specific validation and serialization
logic. It is the core data structure used to communicate between the `pydantic` and `pydantic-core`
packages. Every core schema has a required `type` key, and extra properties depending on this `type`.

The generation of a core schema is handled in a single place, by the `GenerateSchema` class
(no matter if it is for a Pydantic model or anything else).

!!! note
    It is not possible to define a custom core schema. A core schema needs to be understood by the
    `pydantic-core` package, and as such we only support a fixed number of core schema types.
    This is also part of the reason why the `GenerateSchema` isn't truly exposed and properly
    documented.

    The core schema definitions can be found in the [`pydantic_core.core_schema`][] module.

In the case of a Pydantic model, a core schema will be constructed and set as the
[`__pydantic_core_schema__`][pydantic.main.BaseModel.__pydantic_core_schema__] attribute.

To illustrate what a core schema looks like, we will take the example of the
[`bool`][pydantic_core.core_schema.bool_schema] core schema:

```python {lint="skip" test="skip"}
class BoolSchema(TypedDict, total=False):
    type: Required[Literal['bool']]
    strict: bool
    ref: str
    metadata: Any
    serialization: SerSchema
```

When defining a Pydantic model with a boolean field:

```python
from pydantic import BaseModel, Field


class Model(BaseModel):
    foo: bool = Field(strict=True)
```

The core schema for the `foo` field will look like:

```python
{
    'type': 'bool',
    'strict': True,
}
```

As seen in the [`BoolSchema`][pydantic_core.core_schema.bool_schema] definition,
the serialization logic is also defined in the core schema.
If we were to define a custom serialization function for `foo` (1), the `serialization` key would look like:
{ .annotate }

1.  For example using the [`field_serializer`][pydantic.functional_serializers.field_serializer] decorator:

    ```python {test="skip" lint="skip"}
    class Model(BaseModel):
        foo: bool = Field(strict=True)

        @field_serializer('foo', mode='plain')
        def serialize_foo(self, value: bool) -> Any:
            ...
    ```

```python {lint="skip" test="skip"}
{
    'type': 'function-plain',
    'function': <function Model.serialize_foo at 0x111>,
    'is_field_serializer': True,
    'info_arg': False,
    'return_schema': {'type': 'int'},
}
```

Note that this is also a core schema definition, just that it is only relevant for `pydantic-core` during serialization.

Core schemas cover a broad scope, and are used whenever we want to communicate between the Python and Rust side.
While the previous examples were related to validation and serialization, it could in theory be used for anything:
error management, extra metadata, etc.

### JSON Schema generation

You may have noticed that the previous serialization core schema has a `return_schema` key.
This is because the core schema is also used to generate the corresponding JSON Schema.

Similar to how the core schema is generated, the JSON Schema generation is handled by the
[`GenerateJsonSchema`][pydantic.json_schema.GenerateJsonSchema] class.
The [`generate`][pydantic.json_schema.GenerateJsonSchema.generate] method
is the main entry point and is given the core schema of that model.

Coming back to our `bool` field example, the [`bool_schema`][pydantic.json_schema.GenerateJsonSchema.bool_schema]
method will be given the previously generated [boolean core schema][pydantic_core.core_schema.bool_schema]
and will return the following JSON Schema:

```json
{
    {"type": "boolean"}
}
```

### Customizing the core schema and JSON schema

!!! abstract "Usage Documentation"
    [Custom types](../concepts/types.md#custom-types)

    [Implementing `__get_pydantic_core_schema__`](../concepts/json_schema.md#implementing-__get_pydantic_core_schema__)

    [Implementing `__get_pydantic_json_schema__`](../concepts/json_schema.md#implementing-__get_pydantic_json_schema__)

While the `GenerateSchema` and [`GenerateJsonSchema`][pydantic.json_schema.GenerateJsonSchema] classes handle
the creation of the corresponding schemas, Pydantic offers a way to customize them in some cases, following a wrapper pattern.
This customization is done through the `__get_pydantic_core_schema__` and `__get_pydantic_json_schema__` methods.

To understand this wrapper pattern, we will take the example of metadata classes used with [`Annotated`][typing.Annotated],
where the `__get_pydantic_core_schema__` method can be used:

```python
from typing import Any

from pydantic_core import CoreSchema
from typing_extensions import Annotated

from pydantic import GetCoreSchemaHandler, TypeAdapter


class MyStrict:
    @classmethod
    def __get_pydantic_core_schema__(
        cls, source: Any, handler: GetCoreSchemaHandler
    ) -> CoreSchema:
        schema = handler(source)  # (1)!
        schema['strict'] = True
        return schema


class MyGt:
    @classmethod
    def __get_pydantic_core_schema__(
        cls, source: Any, handler: GetCoreSchemaHandler
    ) -> CoreSchema:
        schema = handler(source)  # (2)!
        schema['gt'] = 1
        return schema


ta = TypeAdapter(Annotated[int, MyStrict(), MyGt()])
```

1. `MyStrict` is the first annotation to be applied. At this point, `schema = {'type': 'int'}`.
2. `MyGt` is the last annotation to be applied. At this point, `schema = {'type': 'int', 'strict': True}`.

When the `GenerateSchema` class builds the core schema for `Annotated[int, MyStrict(), MyGt()]`, it will
create an instance of a `GetCoreSchemaHandler` to be passed to the `MyGt.__get_pydantic_core_schema__` method. (1)
{ .annotate }

1.  In the case of our [`Annotated`][typing.Annotated] pattern, the `GetCoreSchemaHandler` is defined in a nested way.
    Calling it will recursively call the other `__get_pydantic_core_schema__` methods until it reaches the `int` annotation,
    where a simple `{'type': 'int'}` schema is returned.

The `source` argument depends on the core schema generation pattern. In the case of [`Annotated`][typing.Annotated],
the `source` will be the type being annotated. When [defining a custom type](../concepts/types.md#as-a-method-on-a-custom-type),
the `source` will be the actual class where `__get_pydantic_core_schema__` is defined.

## Model validation and serialization

While model definition was scoped to the _class_ level (i.e. when defining your model), model validation
and serialization happens at the _instance_ level. Both these concepts are handled in `pydantic-core`
(providing a 5 to 20 performance increase compared to Pydantic V1), by using the previously built core schema.

`pydantic-core` exposes a [`SchemaValidator`][pydantic_core.SchemaValidator] and
[`SchemaSerializer`][pydantic_core.SchemaSerializer] class to perform these tasks:

```python
from pydantic import BaseModel


class Model(BaseModel):
    foo: int


model = Model.model_validate({'foo': 1})  # (1)!
dumped = model.model_dump()  # (2)!
```

1. The provided data is sent to `pydantic-core` by using the
   [`SchemaValidator.validate_python`][pydantic_core.SchemaValidator.validate_python] method.
   `pydantic-core` will validate (following the core schema of the model) the data and populate
   the model's `__dict__` attribute.
2. The `model` instance is sent to `pydantic-core` by using the
   [`SchemaSerializer.to_python`][pydantic_core.SchemaSerializer.to_python] method.
   `pydantic-core` will read the instance's `__dict__` attribute and built the appropriate result
   (again, following the core schema of the model).
