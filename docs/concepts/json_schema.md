??? api "API Documentation"
    [`pydantic.json_schema`][pydantic.json_schema]<br>

Pydantic allows automatic creation and customization of JSON schemas from models.
The generated JSON schemas are compliant with the following specifications:

* [JSON Schema Draft 2020-12](https://json-schema.org/draft/2020-12/release-notes.html)
* [OpenAPI Specification v3.1.0](https://github.com/OAI/OpenAPI-Specification).

## Generating JSON Schema

Use the following functions to generate JSON schema:

* [`BaseModel.model_json_schema`][pydantic.main.BaseModel.model_json_schema] returns a jsonable dict of a model's schema.
* [`TypeAdapter.json_schema`][pydantic.type_adapter.TypeAdapter.json_schema] returns a jsonable dict of an adapted type's schema.

!!! note
    These methods are not to be confused with [`BaseModel.model_dump_json`][pydantic.main.BaseModel.model_dump_json]
    and [`TypeAdapter.dump_json`][pydantic.type_adapter.TypeAdapter.dump_json], which serialize instances of the
    model or adapted type, respectively. These methods return JSON strings. In comparison,
    [`BaseModel.model_json_schema`][pydantic.main.BaseModel.model_json_schema] and
    [`TypeAdapter.json_schema`][pydantic.type_adapter.TypeAdapter.json_schema] return a jsonable dict
    representing the JSON schema of the model or adapted type, respectively.

!!! note "on the "jsonable" nature of JSON schema"
    Regarding the "jsonable" nature of the [`model_json_schema`][pydantic.main.BaseModel.model_json_schema] results,
    calling `json.dumps(m.model_json_schema())`on some `BaseModel` `m` returns a valid JSON string. Similarly, for
    [`TypeAdapter.json_schema`][pydantic.type_adapter.TypeAdapter.json_schema], calling
    `json.dumps(TypeAdapter(<some_type>).json_schema())` returns a valid JSON string.


!!! tip
    Pydantic offers support for both of:

    1. [Customizing JSON Schema](#customizing-json-schema)
    2. [Customizing the JSON Schema Generation Process](#customizing-the-json-schema-generation-process)

    The first approach generally has a more narrow scope, allowing for customization of the JSON schema for
    more specific cases and types. The second approach generally has a more broad scope, allowing for customization
    of the JSON schema generation process overall. The same effects can be achieved with either approach, but
    depending on your use case, one approach might offer a more simple solution than the other.

Here's an example of generating JSON schema from a `BaseModel`:

```python {output="json"}
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
        default=42,
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

Here's an example of generating JSON schema from a [`TypeAdapter`][pydantic.type_adapter.TypeAdapter]:

```python
from typing import List

from pydantic import TypeAdapter

adapter = TypeAdapter(List[int])
print(adapter.json_schema())
#> {'items': {'type': 'integer'}, 'type': 'array'}
```

You can also generate JSON schemas for combinations of [`BaseModel`s][pydantic.main.BaseModel]
and [`TypeAdapter`s][pydantic.type_adapter.TypeAdapter], as shown in this example:

```python {output="json"}
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

### Configuring the `JsonSchemaMode`

Specify the mode of JSON schema generation via the `mode` parameter in the
[`model_json_schema`][pydantic.main.BaseModel.model_json_schema] and
[`TypeAdapter.json_schema`][pydantic.type_adapter.TypeAdapter.json_schema] methods. By default, the mode is set to
`'validation'`, which produces a JSON schema corresponding to the model's validation schema.

The [`JsonSchemaMode`][pydantic.json_schema.JsonSchemaMode] is a type alias that represents the available options for the `mode` parameter:

* `'validation'`
* `'serialization'`

Here's an example of how to specify the `mode` parameter, and how it affects the generated JSON schema:

```python
from decimal import Decimal

from pydantic import BaseModel


class Model(BaseModel):
    a: Decimal = Decimal('12.34')


print(Model.model_json_schema(mode='validation'))
"""
{
    'properties': {
        'a': {
            'anyOf': [{'type': 'number'}, {'type': 'string'}],
            'default': '12.34',
            'title': 'A',
        }
    },
    'title': 'Model',
    'type': 'object',
}
"""

print(Model.model_json_schema(mode='serialization'))
"""
{
    'properties': {'a': {'default': '12.34', 'title': 'A', 'type': 'string'}},
    'title': 'Model',
    'type': 'object',
}
"""
```


## Customizing JSON Schema

The generated JSON schema can be customized at both the field level and model level via:

1. [Field-level customization](#field-level-customization) with the [`Field`][pydantic.fields.Field] constructor
2. [Model-level customization](#model-level-customization) with [`model_config`][pydantic.config.ConfigDict]

At both the field and model levels, you can use the `json_schema_extra` option to add extra information to the JSON schema.
The [Using `json_schema_extra`](#using-json_schema_extra) section below provides more details on this option.

For custom types, Pydantic offers other tools for customizing JSON schema generation:

1. [`WithJsonSchema` annotation](#withjsonschema-annotation)
2. [`SkipJsonSchema` annotation](#skipjsonschema-annotation)
3. [Implementing `__get_pydantic_core_schema__`](#implementing_get_pydantic_core_schema)
4. [Implementing `__get_pydantic_json_schema__`](#implementing_get_pydantic_json_schema)

### Field-Level Customization

Optionally, the [`Field`][pydantic.fields.Field] function can be used to provide extra information about the field
and validations.

Some field parameters are used exclusively to customize the generated JSON Schema:

* `title`: The title of the field.
* `description`: The description of the field.
* `examples`: The examples of the field.
* `json_schema_extra`: Extra JSON Schema properties to be added to the field.
* `field_title_generator`: A function that programmatically sets the field's title, based on its name and info.

Here's an example:

```python {output="json"}
import json

from pydantic import BaseModel, EmailStr, Field, SecretStr


class User(BaseModel):
    age: int = Field(description='Age of the user')
    email: EmailStr = Field(examples=['marcelo@mail.com'])
    name: str = Field(title='Username')
    password: SecretStr = Field(
        json_schema_extra={
            'title': 'Password',
            'description': 'Password of the user',
            'examples': ['123456'],
        }
    )


print(json.dumps(User.model_json_schema(), indent=2))
"""
{
  "properties": {
    "age": {
      "description": "Age of the user",
      "title": "Age",
      "type": "integer"
    },
    "email": {
      "examples": [
        "marcelo@mail.com"
      ],
      "format": "email",
      "title": "Email",
      "type": "string"
    },
    "name": {
      "title": "Username",
      "type": "string"
    },
    "password": {
      "description": "Password of the user",
      "examples": [
        "123456"
      ],
      "format": "password",
      "title": "Password",
      "type": "string",
      "writeOnly": true
    }
  },
  "required": [
    "age",
    "email",
    "name",
    "password"
  ],
  "title": "User",
  "type": "object"
}
"""
```

#### Unenforced `Field` constraints

If Pydantic finds constraints which are not being enforced, an error will be raised. If you want to force the
constraint to appear in the schema, even though it's not being checked upon parsing, you can use variadic arguments
to [`Field`][pydantic.fields.Field] with the raw schema attribute name:

```python
from pydantic import BaseModel, Field, PositiveInt

try:
    # this won't work since `PositiveInt` takes precedence over the
    # constraints defined in `Field`, meaning they're ignored
    class Model(BaseModel):
        foo: PositiveInt = Field(lt=10)

except ValueError as e:
    print(e)


# if you find yourself needing this, an alternative is to declare
# the constraints in `Field` (or you could use `conint()`)
# here both constraints will be enforced:
class ModelB(BaseModel):
    # Here both constraints will be applied and the schema
    # will be generated correctly
    foo: int = Field(gt=0, lt=10)


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

You can specify JSON schema modifications via the [`Field`][pydantic.fields.Field] constructor via [`typing.Annotated`][] as well:

```python {output="json"}
import json
from uuid import uuid4

from typing_extensions import Annotated

from pydantic import BaseModel, Field


class Foo(BaseModel):
    id: Annotated[str, Field(default_factory=lambda: uuid4().hex)]
    name: Annotated[str, Field(max_length=256)] = Field(
        'Bar', title='CustomName'
    )


print(json.dumps(Foo.model_json_schema(), indent=2))
"""
{
  "properties": {
    "id": {
      "title": "Id",
      "type": "string"
    },
    "name": {
      "default": "Bar",
      "maxLength": 256,
      "title": "CustomName",
      "type": "string"
    }
  },
  "title": "Foo",
  "type": "object"
}
"""
```

### Programmatic field title generation

The `field_title_generator` parameter can be used to programmatically generate the title for a field based on its name and info.

See the following example:

```python
import json

from pydantic import BaseModel, Field
from pydantic.fields import FieldInfo


def make_title(field_name: str, field_info: FieldInfo) -> str:
    return field_name.upper()


class Person(BaseModel):
    name: str = Field(field_title_generator=make_title)
    age: int = Field(field_title_generator=make_title)


print(json.dumps(Person.model_json_schema(), indent=2))
"""
{
  "properties": {
    "name": {
      "title": "NAME",
      "type": "string"
    },
    "age": {
      "title": "AGE",
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

### Model-Level Customization

You can also use [model config][pydantic.config.ConfigDict] to customize JSON schema generation on a model.
Specifically, the following config options are relevant:

* [`title`][pydantic.config.ConfigDict.title]
* [`json_schema_extra`][pydantic.config.ConfigDict.json_schema_extra]
* [`json_schema_mode_override`][pydantic.config.ConfigDict.json_schema_mode_override]
* [`field_title_generator`][pydantic.config.ConfigDict.field_title_generator]
* [`model_title_generator`][pydantic.config.ConfigDict.model_title_generator]

### Using `json_schema_extra`

The `json_schema_extra` option can be used to add extra information to the JSON schema, either at the
[Field level](#field-level-customization) or at the [Model level](#model-level-customization).
You can pass a `dict` or a `Callable` to `json_schema_extra`.

#### Using `json_schema_extra` with a `dict`

You can pass a `dict` to `json_schema_extra` to add extra information to the JSON schema:

```python {output="json"}
import json

from pydantic import BaseModel, ConfigDict


class Model(BaseModel):
    a: str

    model_config = ConfigDict(json_schema_extra={'examples': [{'a': 'Foo'}]})


print(json.dumps(Model.model_json_schema(), indent=2))
"""
{
  "examples": [
    {
      "a": "Foo"
    }
  ],
  "properties": {
    "a": {
      "title": "A",
      "type": "string"
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

#### Using `json_schema_extra` with a `Callable`

You can pass a `Callable` to `json_schema_extra` to modify the JSON schema with a function:

```python {output="json"}
import json

from pydantic import BaseModel, Field


def pop_default(s):
    s.pop('default')


class Model(BaseModel):
    a: int = Field(default=1, json_schema_extra=pop_default)


print(json.dumps(Model.model_json_schema(), indent=2))
"""
{
  "properties": {
    "a": {
      "title": "A",
      "type": "integer"
    }
  },
  "title": "Model",
  "type": "object"
}
"""
```

#### Merging `json_schema_extra`

Starting in v2.9, Pydantic merges `json_schema_extra` dictionaries from annotated types.
This pattern offers a more additive approach to merging rather than the previous override behavior.
This can be quite helpful for cases of reusing json schema extra information across multiple types.

We viewed this change largely as a bug fix, as it resolves unintentional differences in the `json_schema_extra` merging behavior
between `BaseModel` and `TypeAdapter` instances - see [this issue](https://github.com/pydantic/pydantic/issues/9210)
for more details.

```python
import json

from typing_extensions import Annotated, TypeAlias

from pydantic import Field, TypeAdapter

ExternalType: TypeAlias = Annotated[
    int, Field(json_schema_extra={'key1': 'value1'})
]

ta = TypeAdapter(
    Annotated[ExternalType, Field(json_schema_extra={'key2': 'value2'})]
)
print(json.dumps(ta.json_schema(), indent=2))
"""
{
  "key1": "value1",
  "key2": "value2",
  "type": "integer"
}
"""
```

!!! note
    We no longer (and never fully did) support composing a mix of `dict` and `callable` type `json_schema_extra` specifications.
    If this is a requirement for your use case, please [open a pydantic issue](https://github.com/pydantic/pydantic/issues/new/choose) and explain your situation - we'd be happy to reconsider this decision when presented with a compelling case.

### `WithJsonSchema` annotation

??? api "API Documentation"
    [`pydantic.json_schema.WithJsonSchema`][pydantic.json_schema.WithJsonSchema]<br>

!!! tip
    Using [`WithJsonSchema`][pydantic.json_schema.WithJsonSchema]] is preferred over
    [implementing `__get_pydantic_json_schema__`](#implementing_get_pydantic_json_schema) for custom types,
    as it's more simple and less error-prone.

The [`WithJsonSchema`][pydantic.json_schema.WithJsonSchema] annotation can be used to override the generated (base)
JSON schema for a given type without the need to implement `__get_pydantic_core_schema__`
or `__get_pydantic_json_schema__` on the type itself.

This provides a way to set a JSON schema for types that would otherwise raise errors when producing a JSON schema,
such as `Callable`, or types that have an [`is-instance`][pydantic_core.core_schema.is_instance_schema] core schema.

For example, the use of a [`PlainValidator`][pydantic.functional_validators.PlainValidator] in the following example
would otherwise raise an error when producing a JSON schema because the [`PlainValidator`][pydantic.functional_validators.PlainValidator]
is a `Callable`. However, by using the [`WithJsonSchema`][pydantic.json_schema.WithJsonSchema]
annotation, we can override the generated JSON schema for the custom `MyInt` type:

```python {output="json"}
import json

from typing_extensions import Annotated

from pydantic import BaseModel, PlainValidator, WithJsonSchema

MyInt = Annotated[
    int,
    PlainValidator(lambda v: int(v) + 1),
    WithJsonSchema({'type': 'integer', 'examples': [1, 0, -1]}),
]


class Model(BaseModel):
    a: MyInt


print(Model(a='1').a)
#> 2

print(json.dumps(Model.model_json_schema(), indent=2))
"""
{
  "properties": {
    "a": {
      "examples": [
        1,
        0,
        -1
      ],
      "title": "A",
      "type": "integer"
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

!!! note
    As discussed in [this issue](https://github.com/pydantic/pydantic/issues/8208), in the future, it's likely that Pydantic will add
    builtin support for JSON schema generation for types like [`PlainValidator`][pydantic.functional_validators.PlainValidator],
    but the [`WithJsonSchema`][pydantic.json_schema.WithJsonSchema] annotation will still be useful for other custom types.

### `SkipJsonSchema` annotation

??? api "API Documentation"
    [`pydantic.json_schema.SkipJsonSchema`][pydantic.json_schema.SkipJsonSchema]<br>

The [`SkipJsonSchema`][pydantic.json_schema.SkipJsonSchema] annotation can be used to skip a including field (or part of a field's specifications)
from the generated JSON schema. See the API docs for more details.

### Implementing `__get_pydantic_core_schema__` <a name="implementing_get_pydantic_core_schema"></a>

Custom types (used as `field_name: TheType` or `field_name: Annotated[TheType, ...]`) as well as `Annotated` metadata
(used as `field_name: Annotated[int, SomeMetadata]`)
can modify or override the generated schema by implementing `__get_pydantic_core_schema__`.
This method receives two positional arguments:

1. The type annotation that corresponds to this type (so in the case of `TheType[T][int]` it would be `TheType[int]`).
2. A handler/callback to call the next implementer of `__get_pydantic_core_schema__`.

The handler system works just like [`mode='wrap'` validators](validators.md#annotated-validators).
In this case the input is the type and the output is a `core_schema`.

Here is an example of a custom type that *overrides* the generated `core_schema`:

```python
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

```python
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

```python
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

To override the schema completely, do not call the handler and return your own
`CoreSchema`:

```python
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

### Implementing `__get_pydantic_json_schema__` <a name="implementing_get_pydantic_json_schema"></a>

You can also implement `__get_pydantic_json_schema__` to modify or override the generated json schema.
Modifying this method only affects the JSON schema - it doesn't affect the core schema, which is used for validation and serialization.

Here's an example of modifying the generated JSON schema:

```python {output="json"}
import json
from typing import Any

from pydantic_core import core_schema as cs

from pydantic import GetCoreSchemaHandler, GetJsonSchemaHandler, TypeAdapter
from pydantic.json_schema import JsonSchemaValue


class Person:
    name: str
    age: int

    def __init__(self, name: str, age: int):
        self.name = name
        self.age = age

    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: Any, handler: GetCoreSchemaHandler
    ) -> cs.CoreSchema:
        return cs.typed_dict_schema(
            {
                'name': cs.typed_dict_field(cs.str_schema()),
                'age': cs.typed_dict_field(cs.int_schema()),
            },
        )

    @classmethod
    def __get_pydantic_json_schema__(
        cls, core_schema: cs.CoreSchema, handler: GetJsonSchemaHandler
    ) -> JsonSchemaValue:
        json_schema = handler(core_schema)
        json_schema = handler.resolve_ref_schema(json_schema)
        json_schema['examples'] = [
            {
                'name': 'John Doe',
                'age': 25,
            }
        ]
        json_schema['title'] = 'Person'
        return json_schema


print(json.dumps(TypeAdapter(Person).json_schema(), indent=2))
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


### Using `field_title_generator`

The `field_title_generator` parameter can be used to programmatically generate the title for a field based on its name and info.
This is similar to the field level `field_title_generator`, but the `ConfigDict` option will be applied to all fields of the class.

See the following example:

```python
import json

from pydantic import BaseModel, ConfigDict


class Person(BaseModel):
    model_config = ConfigDict(
        field_title_generator=lambda field_name, field_info: field_name.upper()
    )
    name: str
    age: int


print(json.dumps(Person.model_json_schema(), indent=2))
"""
{
  "properties": {
    "name": {
      "title": "NAME",
      "type": "string"
    },
    "age": {
      "title": "AGE",
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

### Using `model_title_generator`

The `model_title_generator` config option is similar to the `field_title_generator` option, but it applies to the title of the model itself,
and accepts the model class as input.

See the following example:

```python
import json
from typing import Type

from pydantic import BaseModel, ConfigDict


def make_title(model: Type) -> str:
    return f'Title-{model.__name__}'


class Person(BaseModel):
    model_config = ConfigDict(model_title_generator=make_title)
    name: str
    age: int


print(json.dumps(Person.model_json_schema(), indent=2))
"""
{
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
  "title": "Title-Person",
  "type": "object"
}
"""
```

## JSON schema types

Types, custom field types, and constraints (like `max_length`) are mapped to the corresponding spec formats in the
following priority order (when there is an equivalent available):

1. [JSON Schema Core](https://json-schema.org/draft/2020-12/json-schema-core)
2. [JSON Schema Validation](https://json-schema.org/draft/2020-12/json-schema-validation)
3. [OpenAPI Data Types](https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.2.md#data-types)
4. The standard `format` JSON field is used to define Pydantic extensions for more complex `string` sub-types.

The field schema mapping from Python or Pydantic to JSON schema is done as follows:

{{ schema_mappings_table }}


## Top-level schema generation

You can also generate a top-level JSON schema that only includes a list of models and related
sub-models in its `$defs`:

```python {output="json"}
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

```python
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

```python
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

### JSON schema sorting

By default, Pydantic recursively sorts JSON schemas by alphabetically sorting keys. Notably, Pydantic skips sorting the values of the `properties` key,
to preserve the order of the fields as they were defined in the model.

If you would like to customize this behavior, you can override the `sort` method in your custom `GenerateJsonSchema` subclass. The below example
uses a no-op `sort` method to disable sorting entirely, which is reflected in the preserved order of the model fields and `json_schema_extra` keys:

```python
import json
from typing import Optional

from pydantic import BaseModel, Field
from pydantic.json_schema import GenerateJsonSchema, JsonSchemaValue


class MyGenerateJsonSchema(GenerateJsonSchema):
    def sort(
        self, value: JsonSchemaValue, parent_key: Optional[str] = None
    ) -> JsonSchemaValue:
        """No-op, we don't want to sort schema values at all."""
        return value


class Bar(BaseModel):
    c: str
    b: str
    a: str = Field(json_schema_extra={'c': 'hi', 'b': 'hello', 'a': 'world'})


json_schema = Bar.model_json_schema(schema_generator=MyGenerateJsonSchema)
print(json.dumps(json_schema, indent=2))
"""
{
  "type": "object",
  "properties": {
    "c": {
      "type": "string",
      "title": "C"
    },
    "b": {
      "type": "string",
      "title": "B"
    },
    "a": {
      "type": "string",
      "c": "hi",
      "b": "hello",
      "a": "world",
      "title": "A"
    }
  },
  "required": [
    "c",
    "b",
    "a"
  ],
  "title": "Bar"
}
"""
```

## Customizing the `$ref`s in JSON Schema

The format of `$ref`s can be altered by calling [`model_json_schema()`][pydantic.main.BaseModel.model_json_schema]
or [`model_dump_json()`][pydantic.main.BaseModel.model_dump_json] with the `ref_template` keyword argument.
The definitions are always stored under the key `$defs`, but a specified prefix can be used for the references.

This is useful if you need to extend or modify the JSON schema default definitions location. For example, with OpenAPI:

```python {output="json"}
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
* Since the `namedtuple` type doesn't exist in JSON, a model's JSON schema does not preserve `namedtuple`s as `namedtuple`s.
* Sub-models used are added to the `$defs` JSON attribute and referenced, as per the spec.
* Sub-models with modifications (via the `Field` class) like a custom title, description, or default value,
    are recursively included instead of referenced.
* The `description` for models is taken from either the docstring of the class or the argument `description` to
    the `Field` class.
* The schema is generated by default using aliases as keys, but it can be generated using model
    property names instead by calling [`model_json_schema()`][pydantic.main.BaseModel.model_json_schema] or
    [`model_dump_json()`][pydantic.main.BaseModel.model_dump_json] with the `by_alias=False` keyword argument.
