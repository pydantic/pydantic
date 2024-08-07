Starting with Pydantic V2, part of the codebase is written in Rust in a separate package called `pydantic-core`.
This architecture documentation will partly focus on how the two `pydantic` and `pydantic-core` packages interacts together.

Usage of the Pydantic library can be divided into two parts:

- Model definition, done in the `pydantic` package.
- Model validation and serialization, done in the `pydantic-core` package.

## Model definition

Whenever a Pydantic [`BaseModel`][pydantic.main.BaseModel] is defined, the metaclass
will analyze the body of the model to collect a number of elements:

- Defined annotations to build model fields (collected in the [`model_fields`][pydantic.main.BaseModel.model_fields] attribute).
- Model configuration, set with [`model_config`][pydantic.main.BaseModel.model_config].
- Additional validators/serializers.
- Private attributes, identification of generic parametrization, etc.

### Communicating between `pydantic` and `pydantic-core`

Once the model class is successfully built, a core schema for the model will be constructed
and set as the [`__pydantic_core_schema__`][pydantic.main.BaseModel.__pydantic_core_schema__]
attribute (this is done by the `GenerateSchema` class). A core schema is a structured Python
dictionary (represented using [`TypedDict`][typing.TypedDict] definitions) representing a
specific validation and serialization logic. It is the core data structure used to communicate
between the `pydantic` and `pydantic-core` packages. Every core schema has a required `type` key,
and extra properties depending on the `type`.

!!! note
    It is not possible to define a custom core schema. A core schema needs to be understood by the
    `pydantic-core` package, and as such we only support a fixed number of core schema types.

    The core schema definitions can be found in the [`pydantic_core.core_schema`][] module.

To illustrate what a core schema looks like, we will take the example of the
[`bool`][pydantic_core.core_schema.bool_schema] core schema:

```python
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

1.  For example using the [`field_serializer`][pydantic.functional_serializers.field_serializer] decorator.

```python
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


### JSON Schema generation

You may have noticed that the previous serialization core schema has a `return_schema` key.
This is because the core schema is also used to generate the corresponding JSON Schema.

The JSON Schema generation of a model is handled by the [`GenerateJsonSchema`][pydantic.json_schema.GenerateJsonSchema] class.
The [`generate`][pydantic.json_schema.GenerateJsonSchema.generate] method is the main entry point and is given the core schema of that model.

### Customizing the core schema and JSON schema

!!! abstract "Usage Documentation"
    [Custom types](concepts/types.md#custom-types)

While the `GenerateSchema` and [`GenerateJsonSchema`][pydantic.json_schema.GenerateJsonSchema] classes handle
the creation of the corresponding schemas, Pydantic offers a way to customize them, following a wrapper pattern.
This customization is done through the `__get_pydantic_core_schema__` and `__get_pydantic_json_schema__` methods.

To understand this wrapper pattern, we will take the following example:

```python
from typing import Annotated, Any

from pydantic import GetCoreSchemaHandler, TypeAdapter
from pydantic_core import CoreSchema

class MyStrict:
    @classmethod
    def __get_pydantic_core_schema__(cls, source: Any, handler: GetCoreSchemaHandler) -> CoreSchema:
        schema = handler(source) # (1)!
        schema['strict'] = True
        return schema

class MyGt:
    @classmethod
    def __get_pydantic_core_schema__(cls, source: Any, handler: GetCoreSchemaHandler) -> CoreSchema:
        schema = handler(source) # (2)!
        schema['gt'] = 1
        return schema

ta = TypeAdapter(Annotated[int, MyStrict(), MyGt()])
```

1. `MyStrict` is the first annotation to be applied. At this point, `schema = {'type': 'int'}`.
2. `MyGt` is the last annotation to be applied. At this point, `schema = {'type': 'int', 'strict': True}`.

When the `GenerateSchema` class builds the core schema for `Annotated[int, MyStrict(), MyGt()]`, it will first
build an [`IntSchema`][pydantic_core.core_schema.int_schema] for the `int` type, and then call the two
`__get_pydantic_core_schema__` methods by providing a handler to be called. TODO what about the `source` arg?

## Model validation and serialization

While model definition was scoped to the _class_ level (i.e. when defining your model), model validation
and serialization happens at the _instance_ level. Both these concepts are handled in `pydantic-core`,
as it will use the previously built core schema to do so.

`pydantic-core` exposes a [`SchemaValidator`][pydantic_core.SchemaValidator] and
[`SchemaSerializer`][pydantic_core.SchemaSerializer] class to perform these tasks.

In a real life use case, when doing the following:

```python
from pydantic import BaseModel

class Model(BaseModel):
    foo: int

model = Model.model_validate({'foo': 1}).model_dump()
```

The steps described below happen:

- The provided data is sent to `pydantic-core` by using the
  [`SchemaValidator.validate_python`][pydantic_core.SchemaValidator.validate_python] method.
  `pydantic-core` will validate (following the core schema of the model) the data and populate
  the model's `__dict__` attribute.
- The `model` instance is sent to `pydantic-core` by using the
  [`SchemaSerializer.to_python`][pydantic_core.SchemaSerializer.to_python] method.
  `pydantic-core` will read the instance's `__dict__` attribute and built the appropriate result
  (again, following the core schema of the model).
