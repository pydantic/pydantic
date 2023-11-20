??? api "API Documentation"
    [`pydantic.json_schema`][pydantic.json_schema]<br>

Pydantic allows automatic creation and customization of JSON schemas from models.
The generated JSON schemas are compliant with the following specifications:

* [JSON Schema Draft 2020-12](https://json-schema.org/draft/2020-12/release-notes.html)
* [OpenAPI extensions](https://github.com/OAI/OpenAPI-Specification).

## Generating JSON Schema

Use the following functions to generate JSON schema:

* [`BaseModel.model_json_schema`][pydantic.main.BaseModel.model_json_schema] - returns a jsonable dict of a model's schema
* [`TypeAdapter.json_schema`][pydantic.type_adapter.TypeAdapter.json_schema] - returns a jsonable dict of an adapted type's schema

!!! note "on the "jsonable" nature of JSON schema"
    Regarding the "jsonable" nature of the [`model_json_schema`][pydantic.main.BaseModel.model_json_schema] results,
    calling `json.dumps(m.model_json_schema())`on some `BaseModel` `m` returns a valid JSON string. Similarly, for
    [`TypeAdapter.json_schema`][pydantic.type_adapter.TypeAdapter.json_schema], calling
    `json.dumps(ta.json_schema())`on some `TypeAdapter` `ta` returns a valid JSON string.

!!! note
    These methods are not to be confused with [`BaseModel.model_dump_json`][pydantic.main.BaseModel.model_dump_json]
    and [`TypeAdapter.dump_json`][pydantic.type_adapter.TypeAdapter.dump_json], which serialize instances of the
    model or adapted type, respectively. These methods return JSON strings.


!!! tip
    Pydantic offers support for both of:

    1. [Customizing JSON Schema](#customizing-json-schema)
    2. [Customizing the JSON Schema Generation Process](#customizing-the-json-schema-generation-process)

    The first approach generally has a more narrow scope, allowing for customization of the JSON schema for
    more specific cases and types. The second approach generally has a more broad scope, allowing for customization
    of the JSON schema generation process overall. The same effects can be achieved with either approach, but
    depending on your use case, one approach might offer a more simple solution than the other.

Here's an example of generating JSON schema from a `BaseModel`:

```py output="json"
import json
from enum import Enum
from typing import Union

from typing_extensions import Annotated

from pydantic import BaseModel, Field
from pydantic.config import ConfigDict


class FooBar(BaseModel):
    count: int
    size: Union[float, None] = None


class Gender(str, Enum):
    male = 'male'
    female = 'female'
    other = 'other'
    not_given = 'not_given'


class MainModel(BaseModel):
    """
    This is the description of the main model
    """

    model_config = ConfigDict(title='Main')

    foo_bar: FooBar
    gender: Annotated[Union[Gender, None], Field(alias='Gender')] = None
    snap: int = Field(
        42,
        title='The Snap',
        description='this is the value of snap',
        gt=30,
        lt=50,
    )


main_model_schema = MainModel.model_json_schema()  # (1)!
print(json.dumps(main_model_schema, indent=2))  # (2)!
"""
{
  "$defs": {
    "FooBar": {
      "properties": {
        "count": {
          "title": "Count",
          "type": "integer"
        },
        "size": {
          "anyOf": [
            {
              "type": "number"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "title": "Size"
        }
      },
      "required": [
        "count"
      ],
      "title": "FooBar",
      "type": "object"
    },
    "Gender": {
      "enum": [
        "male",
        "female",
        "other",
        "not_given"
      ],
      "title": "Gender",
      "type": "string"
    }
  },
  "description": "This is the description of the main model",
  "properties": {
    "foo_bar": {
      "$ref": "#/$defs/FooBar"
    },
    "Gender": {
      "anyOf": [
        {
          "$ref": "#/$defs/Gender"
        },
        {
          "type": "null"
        }
      ],
      "default": null
    },
    "snap": {
      "default": 42,
      "description": "this is the value of snap",
      "exclusiveMaximum": 50,
      "exclusiveMinimum": 30,
      "title": "The Snap",
      "type": "integer"
    }
  },
  "required": [
    "foo_bar"
  ],
  "title": "Main",
  "type": "object"
}
"""
```

1. This produces a "jsonable" dict of `MainModel`'s schema.
2. Calling `json.dumps` on the schema dict produces a JSON string.

The [`TypeAdapter`][pydantic.type_adapter.TypeAdapter] class lets you create an object with methods for validating, serializing,
and producing JSON schemas for arbitrary types. This serves as a complete replacement for `schema_of` in
Pydantic V1 (which is now deprecated).

Here's an example of generating JSON schema from a `TypeAdapter`:

```python
from typing import List

from pydantic import TypeAdapter

adapter = TypeAdapter(List[int])
print(adapter.json_schema())
#> {'items': {'type': 'integer'}, 'type': 'array'}
```

You can also generate JSON schemas for combinations of `BaseModel`s and `TypeAdapter`s, as shown in this example:

```py output="json"
import json
from typing import Union

from pydantic import BaseModel, TypeAdapter


class Cat(BaseModel):
    name: str
    color: str

class Dog(BaseModel):
    name: str
    breed: str


ta = TypeAdapter(Union[Cat, Dog])
ta_schema = ta.json_schema()
print(json.dumps(ta_schema, indent=2))
"""
{
  "$defs": {
    "Cat": {
      "properties": {
        "name": {
          "title": "Name",
          "type": "string"
        },
        "color": {
          "title": "Color",
          "type": "string"
        }
      },
      "required": [
        "name",
        "color"
      ],
      "title": "Cat",
      "type": "object"
    },
    "Dog": {
      "properties": {
        "name": {
          "title": "Name",
          "type": "string"
        },
        "breed": {
          "title": "Breed",
          "type": "string"
        }
      },
      "required": [
        "name",
        "breed"
      ],
      "title": "Dog",
      "type": "object"
    }
  },
  "anyOf": [
    {
      "$ref": "#/$defs/Cat"
    },
    {
      "$ref": "#/$defs/Dog"
    }
  ]
}
"""
```

## Customizing JSON Schema

The generated JSON schema can be customized at both the model level via:

1. Field-level customization with the [`Field`][pydantic.fields.Field] constructor
2. Model-level customization with [`model_config`][pydantic.config.ConfigDict]

For custom types, Pydantic offers other tools for customizing JSON schema generation:

1. Implementing `__get_pydantic_core_schema__`
2. `WithJsonSchema` annotation
3. `SkipJsonSchema` annotation

### Field-Level Customization

Optionally, the [`Field`][pydantic.fields.Field] function can be used to provide extra information about the field
and validations.

See [Customizing JSON Schema](fields.md#customizing-json-schema) for details on field parameters that are used
exclusively to customize the generated JSON schema.

#### Unenforced `Field` constraints

If Pydantic finds constraints which are not being enforced, an error will be raised. If you want to force the
constraint to appear in the schema, even though it's not being checked upon parsing, you can use variadic arguments
to `Field` with the raw schema attribute name:

```py
from pydantic import BaseModel, Field, PositiveInt

try:
    # this won't work since `PositiveInt` takes precedence over the
    # constraints defined in `Field`, meaning they're ignored
    class Model(BaseModel):
        foo: PositiveInt = Field(..., lt=10)

except ValueError as e:
    print(e)


# if you find yourself needing this, an alternative is to declare
# the constraints in `Field` (or you could use `conint()`)
# here both constraints will be enforced:
class ModelB(BaseModel):
    # Here both constraints will be applied and the schema
    # will be generated correctly
    foo: int = Field(..., gt=0, lt=10)


print(ModelB.model_json_schema())
"""
{
    'properties': {
        'foo': {
            'exclusiveMaximum': 10,
            'exclusiveMinimum': 0,
            'title': 'Foo',
            'type': 'integer',
        }
    },
    'required': ['foo'],
    'title': 'ModelB',
    'type': 'object',
}
"""
```

You can specify JSON schema modifications via the `Field` constructor via `typing.Annotated` as well:

```py
from uuid import uuid4

from typing_extensions import Annotated

from pydantic import BaseModel, Field


class Foo(BaseModel):
    id: Annotated[str, Field(default_factory=lambda: uuid4().hex)]
    name: Annotated[str, Field(max_length=256)] = Field('Bar', title='te')


print(Foo.model_json_schema())
"""
{
    'properties': {
        'id': {'title': 'Id', 'type': 'string'},
        'name': {
            'default': 'Bar',
            'maxLength': 256,
            'title': 'te',
            'type': 'string',
        },
    },
    'title': 'Foo',
    'type': 'object',
}
"""
```

### Model-Level Customization

You can also use [model config][pydantic.config.ConfigDict] to customize JSON schema generation on a model.
Specifically, the following config options are relevant:

* [`title`][pydantic.config.ConfigDict.title]
* [`json_schema_extra`][pydantic.config.ConfigDict.json_schema_extra]
* [`schema_generator`][pydantic.config.ConfigDict.schema_generator]
* [`json_schema_mode_override`][pydantic.config.ConfigDict.json_schema_mode_override]

### Implementing `__get_pydantic_core_schema__`

Custom types (used as `field_name: TheType` or `field_name: Annotated[TheType, ...]`) as well as `Annotated` metadata
(used as `field_name: Annotated[int, SomeMetadata]`)
can modify or override the generated schema by implementing `__get_pydantic_core_schema__`.
This method receives two positional arguments:

1. The type annotation that corresponds to this type (so in the case of `TheType[T][int]` it would be `TheType[int]`).
2. A handler/callback to call the next implementer of `__get_pydantic_core_schema__`.

The handler system works just like [`mode='wrap'` validators](validators.md#annotated-validators).
In this case the input is the type and the output is a `core_schema`.

Here is an example of a custom type that *overrides* the generated `core_schema`:

```py
from dataclasses import dataclass
from typing import Any, Dict, List, Type

from pydantic_core import core_schema

from pydantic import BaseModel, GetCoreSchemaHandler


@dataclass
class CompressedString:
    dictionary: Dict[int, str]
    text: List[int]

    def build(self) -> str:
        return ' '.join([self.dictionary[key] for key in self.text])

    @classmethod
    def __get_pydantic_core_schema__(
        cls, source: Type[Any], handler: GetCoreSchemaHandler
    ) -> core_schema.CoreSchema:
        assert source is CompressedString
        return core_schema.no_info_after_validator_function(
            cls._validate,
            core_schema.str_schema(),
            serialization=core_schema.plain_serializer_function_ser_schema(
                cls._serialize,
                info_arg=False,
                return_schema=core_schema.str_schema(),
            ),
        )

    @staticmethod
    def _validate(value: str) -> 'CompressedString':
        inverse_dictionary: Dict[str, int] = {}
        text: List[int] = []
        for word in value.split(' '):
            if word not in inverse_dictionary:
                inverse_dictionary[word] = len(inverse_dictionary)
            text.append(inverse_dictionary[word])
        return CompressedString(
            {v: k for k, v in inverse_dictionary.items()}, text
        )

    @staticmethod
    def _serialize(value: 'CompressedString') -> str:
        return value.build()


class MyModel(BaseModel):
    value: CompressedString


print(MyModel.model_json_schema())
"""
{
    'properties': {'value': {'title': 'Value', 'type': 'string'}},
    'required': ['value'],
    'title': 'MyModel',
    'type': 'object',
}
"""
print(MyModel(value='fox fox fox dog fox'))
"""
value = CompressedString(dictionary={0: 'fox', 1: 'dog'}, text=[0, 0, 0, 1, 0])
"""

print(MyModel(value='fox fox fox dog fox').model_dump(mode='json'))
#> {'value': 'fox fox fox dog fox'}
```

Since Pydantic would not know how to generate a schema for `CompressedString`, if you call `handler(source)` in its
`__get_pydantic_core_schema__` method you would get a `pydantic.errors.PydanticSchemaGenerationError` error.
This will be the case for most custom types, so you almost never want to call into `handler` for custom types.

The process for `Annotated` metadata is much the same except that you can generally call into `handler` to have
Pydantic handle generating the schema.

```py
from dataclasses import dataclass
from typing import Any, Sequence, Type

from pydantic_core import core_schema
from typing_extensions import Annotated

from pydantic import BaseModel, GetCoreSchemaHandler, ValidationError


@dataclass
class RestrictCharacters:
    alphabet: Sequence[str]

    def __get_pydantic_core_schema__(
        self, source: Type[Any], handler: GetCoreSchemaHandler
    ) -> core_schema.CoreSchema:
        if not self.alphabet:
            raise ValueError('Alphabet may not be empty')
        schema = handler(
            source
        )  # get the CoreSchema from the type / inner constraints
        if schema['type'] != 'str':
            raise TypeError('RestrictCharacters can only be applied to strings')
        return core_schema.no_info_after_validator_function(
            self.validate,
            schema,
        )

    def validate(self, value: str) -> str:
        if any(c not in self.alphabet for c in value):
            raise ValueError(
                f'{value!r} is not restricted to {self.alphabet!r}'
            )
        return value


class MyModel(BaseModel):
    value: Annotated[str, RestrictCharacters('ABC')]


print(MyModel.model_json_schema())
"""
{
    'properties': {'value': {'title': 'Value', 'type': 'string'}},
    'required': ['value'],
    'title': 'MyModel',
    'type': 'object',
}
"""
print(MyModel(value='CBA'))
#> value='CBA'

try:
    MyModel(value='XYZ')
except ValidationError as e:
    print(e)
    """
    1 validation error for MyModel
    value
      Value error, 'XYZ' is not restricted to 'ABC' [type=value_error, input_value='XYZ', input_type=str]
    """
```

So far we have been wrapping the schema, but if you just want to *modify* it or *ignore* it you can as well.

To modify the schema, first call the handler, then mutate the result:

```py
from typing import Any, Type

from pydantic_core import ValidationError, core_schema
from typing_extensions import Annotated

from pydantic import BaseModel, GetCoreSchemaHandler


class SmallString:
    def __get_pydantic_core_schema__(
        self,
        source: Type[Any],
        handler: GetCoreSchemaHandler,
    ) -> core_schema.CoreSchema:
        schema = handler(source)
        assert schema['type'] == 'str'
        schema['max_length'] = 10  # modify in place
        return schema


class MyModel(BaseModel):
    value: Annotated[str, SmallString()]


try:
    MyModel(value='too long!!!!!')
except ValidationError as e:
    print(e)
    """
    1 validation error for MyModel
    value
      String should have at most 10 characters [type=string_too_long, input_value='too long!!!!!', input_type=str]
    """
```

!!! tip
    Note that you *must* return a schema, even if you are just mutating it in place.

Here's another mutation example:

```py output="json"
import json

from pydantic_core import CoreSchema

from pydantic import BaseModel, GetJsonSchemaHandler
from pydantic.json_schema import JsonSchemaValue


class Person(BaseModel):
    name: str
    age: int

    @classmethod
    def __get_pydantic_json_schema__(
        cls, core_schema: CoreSchema, handler: GetJsonSchemaHandler
    ) -> JsonSchemaValue:
        json_schema = handler(core_schema)
        json_schema = handler.resolve_ref_schema(json_schema)
        json_schema['examples'] = [
            {
                'name': 'John Doe',
                'age': 25,
            }
        ]
        return json_schema


print(json.dumps(Person.model_json_schema(), indent=2))
"""
{
  "examples": [
    {
      "age": 25,
      "name": "John Doe"
    }
  ],
  "properties": {
    "name": {
      "title": "Name",
      "type": "string"
    },
    "age": {
      "title": "Age",
      "type": "integer"
    }
  },
  "required": [
    "name",
    "age"
  ],
  "title": "Person",
  "type": "object"
}
"""
```

To override the schema completely, do not call the handler and return your own
`CoreSchema`:

```py
from typing import Any, Type

from pydantic_core import ValidationError, core_schema
from typing_extensions import Annotated

from pydantic import BaseModel, GetCoreSchemaHandler


class AllowAnySubclass:
    def __get_pydantic_core_schema__(
        self, source: Type[Any], handler: GetCoreSchemaHandler
    ) -> core_schema.CoreSchema:
        # we can't call handler since it will fail for arbitrary types
        def validate(value: Any) -> Any:
            if not isinstance(value, source):
                raise ValueError(
                    f'Expected an instance of {source}, got an instance of {type(value)}'
                )

        return core_schema.no_info_plain_validator_function(validate)


class Foo:
    pass


class Model(BaseModel):
    f: Annotated[Foo, AllowAnySubclass()]


print(Model(f=Foo()))
#> f=None


class NotFoo:
    pass


try:
    Model(f=NotFoo())
except ValidationError as e:
    print(e)
    """
    1 validation error for Model
    f
      Value error, Expected an instance of <class '__main__.Foo'>, got an instance of <class '__main__.NotFoo'> [type=value_error, input_value=<__main__.NotFoo object at 0x0123456789ab>, input_type=NotFoo]
    """
```

As seen above, annotating a field with a `BaseModel` type can be used to modify or override the generated json schema.
However, if you want to take advantage of storing metadata via `Annotated`, but you don't want to override the generated JSON
schema, you can use the following approach with a no-op version of `__get_pydantic_core_schema__` implemented on the
metadata class:

```py
from typing import Type

from pydantic_core import CoreSchema
from typing_extensions import Annotated

from pydantic import BaseModel, GetCoreSchemaHandler


class Metadata(BaseModel):
    foo: str = 'metadata!'
    bar: int = 100

    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: Type[BaseModel], handler: GetCoreSchemaHandler
    ) -> CoreSchema:
        if cls is not source_type:
            return handler(source_type)
        return super().__get_pydantic_core_schema__(source_type, handler)


class Model(BaseModel):
    state: Annotated[int, Metadata()]


m = Model.model_validate({'state': 2})
print(repr(m))
#> Model(state=2)
print(m.model_fields)
"""
{
    'state': FieldInfo(
        annotation=int,
        required=True,
        metadata=[Metadata(foo='metadata!', bar=100)],
    )
}
"""
```

### `WithJsonSchema` annotation

??? api "API Documentation"
    [`pydantic.json_schema.WithJsonSchema`][pydantic.json_schema.WithJsonSchema]<br>

### `SkipJsonSchema` annotation

??? api "API Documentation"
    [`pydantic.json_schema.SkipJsonSchema`][pydantic.json_schema.SkipJsonSchema]<br>

The `SkipJsonSchema` annotation can be used to skip a including field (or part of a field's specifications)
from the generated JSON schema. See the API docs for more details.

## JSON schema types

Types, custom field types, and constraints (like `max_length`) are mapped to the corresponding spec formats in the
following priority order (when there is an equivalent available):

1. [JSON Schema Core](http://json-schema.org/latest/json-schema-core.html#rfc.section.4.3.1)
2. [JSON Schema Validation](http://json-schema.org/latest/json-schema-validation.html)
3. [OpenAPI Data Types](https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.2.md#data-types)
4. The standard `format` JSON field is used to define Pydantic extensions for more complex `string` sub-types.

The field schema mapping from Python or Pydantic to JSON schema is done as follows:

{{ schema_mappings_table }}


## Top-level schema generation

You can also generate a top-level JSON schema that only includes a list of models and related
sub-models in its `$defs`:

```py output="json"
import json

from pydantic import BaseModel
from pydantic.json_schema import models_json_schema


class Foo(BaseModel):
    a: str = None


class Model(BaseModel):
    b: Foo


class Bar(BaseModel):
    c: int


_, top_level_schema = models_json_schema(
    [(Model, 'validation'), (Bar, 'validation')], title='My Schema'
)
print(json.dumps(top_level_schema, indent=2))
"""
{
  "$defs": {
    "Bar": {
      "properties": {
        "c": {
          "title": "C",
          "type": "integer"
        }
      },
      "required": [
        "c"
      ],
      "title": "Bar",
      "type": "object"
    },
    "Foo": {
      "properties": {
        "a": {
          "default": null,
          "title": "A",
          "type": "string"
        }
      },
      "title": "Foo",
      "type": "object"
    },
    "Model": {
      "properties": {
        "b": {
          "$ref": "#/$defs/Foo"
        }
      },
      "required": [
        "b"
      ],
      "title": "Model",
      "type": "object"
    }
  },
  "title": "My Schema"
}
"""
```

## Customizing the JSON Schema Generation Process

??? api "API Documentation"
    [`pydantic.json_schema`][pydantic.json_schema.GenerateJsonSchema]<br>

If you need custom schema generation, you can use a `schema_generator`, modifying the
[`GenerateJsonSchema`][pydantic.json_schema.GenerateJsonSchema] class as necessary for your application.

The various methods that can be used to produce JSON schema accept a keyword argument `schema_generator: type[GenerateJsonSchema] = GenerateJsonSchema`, and you can pass your custom subclass to these methods in order to use your own approach to generating JSON schema.

`GenerateJsonSchema` implements the translation of a type's `pydantic-core` schema into a JSON schema.
By design, this class breaks the JSON schema generation process into smaller methods that can be easily overridden in
subclasses to modify the "global" approach to generating JSON schema.

```py
from pydantic import BaseModel
from pydantic.json_schema import GenerateJsonSchema


class MyGenerateJsonSchema(GenerateJsonSchema):
    def generate(self, schema, mode='validation'):
        json_schema = super().generate(schema, mode=mode)
        json_schema['title'] = 'Customize title'
        json_schema['$schema'] = self.schema_dialect
        return json_schema


class MyModel(BaseModel):
    x: int


print(MyModel.model_json_schema(schema_generator=MyGenerateJsonSchema))
"""
{
    'properties': {'x': {'title': 'X', 'type': 'integer'}},
    'required': ['x'],
    'title': 'Customize title',
    'type': 'object',
    '$schema': 'https://json-schema.org/draft/2020-12/schema',
}
"""
```

Below is an approach you can use to exclude any fields from the schema that don't have valid json schemas:

```py
from typing import Callable

from pydantic_core import PydanticOmit, core_schema

from pydantic import BaseModel
from pydantic.json_schema import GenerateJsonSchema, JsonSchemaValue


class MyGenerateJsonSchema(GenerateJsonSchema):
    def handle_invalid_for_json_schema(
        self, schema: core_schema.CoreSchema, error_info: str
    ) -> JsonSchemaValue:
        raise PydanticOmit


def example_callable():
    return 1


class Example(BaseModel):
    name: str = 'example'
    function: Callable = example_callable


instance_example = Example()

validation_schema = instance_example.model_json_schema(
    schema_generator=MyGenerateJsonSchema, mode='validation'
)
print(validation_schema)
"""
{
    'properties': {
        'name': {'default': 'example', 'title': 'Name', 'type': 'string'}
    },
    'title': 'Example',
    'type': 'object',
}
"""
```

## Customizing the `$ref`s in JSON Schema

The format of `$ref`s can be altered by calling [`model_json_schema()`][pydantic.main.BaseModel.model_json_schema]
or `model_dump_json()`][pydantic.main.BaseModel.model_dump_json] with the `ref_template` keyword argument.
The definitions are always stored under the key `$defs`, but a specified prefix can be used for the references.

This is useful if you need to extend or modify the JSON schema default definitions location. For example, with OpenAPI:

```py output="json"
import json

from pydantic import BaseModel
from pydantic.type_adapter import TypeAdapter


class Foo(BaseModel):
    a: int


class Model(BaseModel):
    a: Foo


adapter = TypeAdapter(Model)

print(
    json.dumps(
        adapter.json_schema(ref_template='#/components/schemas/{model}'),
        indent=2,
    )
)
"""
{
  "$defs": {
    "Foo": {
      "properties": {
        "a": {
          "title": "A",
          "type": "integer"
        }
      },
      "required": [
        "a"
      ],
      "title": "Foo",
      "type": "object"
    }
  },
  "properties": {
    "a": {
      "$ref": "#/components/schemas/Foo"
    }
  },
  "required": [
    "a"
  ],
  "title": "Model",
  "type": "object"
}
"""
```

## Miscellaneous Notes on JSON Schema Generation

* The JSON schema for `Optional` fields indicates that the value `null` is allowed.
* The `Decimal` type is exposed in JSON schema (and serialized) as a string.
* The JSON schema does not preserve `namedtuple`s as `namedtuple`s.
* When they differ, you can specify whether you want the JSON schema to represent the inputs to validation
    or the outputs from serialization.
* Sub-models used are added to the `$defs` JSON attribute and referenced, as per the spec.
* Sub-models with modifications (via the `Field` class) like a custom title, description, or default value,
    are recursively included instead of referenced.
* The `description` for models is taken from either the docstring of the class or the argument `description` to
    the `Field` class.
* The schema is generated by default using aliases as keys, but it can be generated using model
    property names instead by calling [`model_json_schema()`][pydantic.main.BaseModel.model_json_schema] or
    [`model_dump_json()`][pydantic.main.BaseModel.model_dump_json] with the `by_alias=False` keyword argument.
