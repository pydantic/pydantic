Below are details on common errors developers can see when working with pydantic, together
with some suggestions on how to fix them.

{% raw %}
## Decorator on missing field {#decorator-missing-field}

This error is raised when you define a decorator with an invalid field.

```py test="skip" lint="skip" upgrade="skip"
from typing import Any

from pydantic import BaseModel, field_validator

class Model(BaseModel):
    a: str

    @field_validator('b')
    def check_b(cls, v: Any):
        return v
```

You can use `check_fields=False` if you're inheriting from the model and intended this.

```py test="skip" lint="skip" upgrade="skip"
from typing import Any

from pydantic import BaseModel, create_model, field_validator


class Model(BaseModel):
    @field_validator('a', check_fields=False)
    def check_a(cls, v: Any):
        return v

model = create_model('FooModel', a=(str, 'cake'), __base__=Model)
```

## Discriminator no field {#discriminator-no-field}

This error is raised when a model in discriminated unions doesn't define a discriminator field.

```py test="skip" lint="skip" upgrade="skip"
from typing import Union

from pydantic import BaseModel, Field
from typing_extensions import Literal


class Cat(BaseModel):
    c: str

class Dog(BaseModel):
    pet_type: Literal['dog']
    d: str

class Model(BaseModel):
    pet: Union[Cat, Dog] = Field(..., discriminator='pet_type')
    number: int
```

## Discriminator alias type {#discriminator-alias-type}

This error is raised when you define a non-string alias on a discriminator field.

```py test="skip" lint="skip" upgrade="skip"
from typing import Union

from pydantic import AliasChoices, BaseModel, Field
from typing_extensions import Literal


class Cat(BaseModel):
    pet_type: Literal['cat'] = Field(validation_alias=AliasChoices('Pet', 'PET'))
    c: str

class Dog(BaseModel):
    pet_type: Literal['dog']
    d: str

class Model(BaseModel):
    pet: Union[Cat, Dog] = Field(..., discriminator='pet_type')
    number: int
```

## Discriminator needs literal {#discriminator-needs-literal}

This error is raised when you define a non-`Literal` type discriminator field.

```py test="skip" lint="skip" upgrade="skip"
from typing import Union

from pydantic import BaseModel, Field
from typing_extensions import Literal


class Cat(BaseModel):
    pet_type: int
    c: str

class Dog(BaseModel):
    pet_type: Literal['dog']
    d: str

class Model(BaseModel):
    pet: Union[Cat, Dog] = Field(..., discriminator='pet_type')
    number: int
```

## Discriminator alias {#discriminator-alias}

This error is raised when you define different aliases on discriminator fields.

```py test="skip" lint="skip" upgrade="skip"
from typing import Union

from pydantic import BaseModel, Field
from typing_extensions import Literal


class Cat(BaseModel):
    pet_type: Literal['cat'] = Field(validation_alias='PET')
    c: str

class Dog(BaseModel):
    pet_type: Literal['dog'] = Field(validation_alias='Pet')
    d: str

class Model(BaseModel):
    pet: Union[Cat, Dog] = Field(..., discriminator='pet_type')
    number: int
```

## TypedDict version {#typed-dict-version}

This error is raised when you use `typing_extensions.TypedDict`
instead of `typing.TypedDict` on Python < 3.11.

## Model parent field overridden {#model-field-overridden}

This error is raised when a field defined on a base class was overridden by a non-annotated attribute.

```py test="skip" lint="skip" upgrade="skip"
from pydantic import BaseModel


class Foo(BaseModel):
    a: float

class Bar(Foo):
    x: float = 12.3
    a = 123.0
```

## Model field missing annotation {#model-field-missing-annotation}

This error is raised when a field doesn't have an annotation.

```py test="skip" lint="skip" upgrade="skip"
from pydantic import BaseModel, Field


class Model(BaseModel):
    a = Field('foobar')
    b = None
```

If the field is not meant to be a field, you may be able to resolve the error
by annotating it as a `ClassVar`:

```py test="skip" lint="skip" upgrade="skip"
from typing import ClassVar
from pydantic import BaseModel


class Model(BaseModel):
    a: ClassVar[str]
```

Or updating `model_config['ignored_types']`:

```py test="skip" lint="skip" upgrade="skip"
from pydantic import BaseModel, ConfigDict


class IgnoredType:
    pass

class MyModel(BaseModel):
    model_config = ConfigDict(ignored_types=(IgnoredType,))

    _a = IgnoredType()
    _b: int = IgnoredType()
    _c: IgnoredType
    _d: IgnoredType = IgnoredType()
```

## Model not fully defined {#model-not-fully-defined}

This error is raised when a type is not defined:

```py test="skip" lint="skip" upgrade="skip"
from typing import ForwardRef

from pydantic import BaseModel

UndefinedType = ForwardRef('UndefinedType')

class Foobar(BaseModel):
    a: UndefinedType

    model_config = {'undefined_types_warning': False}

Foobar(a=1)
```

Or when the type has been defined after usage:

```py test="skip" lint="skip" upgrade="skip"
from typing import Optional

from pydantic import BaseModel

class Foo(BaseModel, undefined_types_warning=False):
    a: Optional['Bar'] = None

class Bar(BaseModel):
    b: 'Foo'

foo = Foo(a={'b': {'a': None}})
```

It can be fixed by defining the type and then calling `.model_rebuild()`:

```py test="skip" lint="skip" upgrade="skip"
from typing import Optional

from pydantic import BaseModel

class Foo(BaseModel, undefined_types_warning=False):
    a: Optional['Bar'] = None

class Bar(BaseModel):
    b: 'Foo'

Foo.model_rebuild()

foo = Foo(a={'b': {'a': None}})
```

## Config and model_config both defined {#config-both}

This error is raised when `class Config` and `model_config` are used together.

```py test="skip" lint="skip" upgrade="skip"
from pydantic import BaseModel, ConfigDict


class Model(BaseModel):
    a: str

    model_config = ConfigDict(from_attributes=True)

    class Config:
        from_attributes = True
```

## Keyword arguments deprecated {#deprecated_kwargs}

This error is raised when the keyword arguments are not available in Pydantic V2.

For example, `regex` is removed from Pydantic V2:

```py test="skip" lint="skip" upgrade="skip"
from pydantic import BaseModel, Field


class Model(BaseModel):
    x: str = Field(regex='test')
```

## JSON Schema invalid type {#invalid-for-json-schema}

This error is raised when Pydantic fails to generate a JSON schema for some `CoreSchema`.

```py test="skip" lint="skip" upgrade="skip"
from pydantic import BaseModel, ImportString


class Model(BaseModel):
    a: ImportString


Model.model_json_schema()
```


## JSON Schema already used {#json-schema-already-used}

This error is raised when the JSON schema generator has already been used to generate a JSON schema.
You must create a new instance to generate a new JSON schema.'

## BaseModel instantiated {#base-model-instantiated}

This error is raised when you instantiate `BaseModel` directly. Pydantic models should inherit from `BaseModel`.

```py test="skip" lint="skip" upgrade="skip"
from pydantic import BaseModel


BaseModel()
```

## Undefined annotation {#undefined-annotation}

This error is raised when handling undefined annotations during `CoreSchema` generation.

```py test="skip" lint="skip" upgrade="skip"
from pydantic import BaseModel


class Model(BaseModel, undefined_types_warning=False):
    a: 'B'

Model.model_rebuild()
```

## Schema for unknown type {#schema-for-unknown-type}

This error is raised when Pydantic fails to generate a `CoreSchema` for some type.

```py test="skip" lint="skip" upgrade="skip"
from pydantic import BaseModel


class Model(BaseModel):
    x: 43 = 123
```

## Import error {#import-error}

This error is raised when you try to import an object that was available in V1 but has been removed in V2.

## create_model field definitions {#create-model-field-definitions}

This error is raised when you provide invalid field definitions input in `create_model`.

```py test="skip" lint="skip" upgrade="skip"
from pydantic import create_model


create_model('FooModel', foo=(str, 'default value', 'more'))
```

## create_model config base {#create-model-config-base}

This error is raised when you use both `__config__` and `__base__` together in `create_model`.

```py test="skip" lint="skip" upgrade="skip"
from pydantic import BaseModel, ConfigDict, create_model


config = ConfigDict(frozen=True)
model = create_model('FooModel', foo=(int, ...), __config__=config, __base__=BaseModel)
```

## Validator with no fields {#validator-no-fields}

This error is raised when you use validator bare.

```py test="skip" lint="skip" upgrade="skip"
from pydantic import BaseModel, field_validator


class Model(BaseModel):
    a: str

    @field_validator
    def checker(cls, v):
        return v
```

Should be used with fields and keyword arguments.

```py test="skip" lint="skip" upgrade="skip"
from pydantic import BaseModel, field_validator


class Model(BaseModel):
    a: str

    @field_validator('a')
    def checker(cls, v):
        return v
```

## Invalid validator fields {#validator-invalid-fields}

This error is raised when you use validator with non-string fields.

```py test="skip" lint="skip" upgrade="skip"
from pydantic import BaseModel, field_validator


class Model(BaseModel):
    a: str
    b: str

    @field_validator(['a', 'b'])
    def check_fields(cls, v):
        return v
```

Fields should be passed as separate string args:

```py test="skip" lint="skip" upgrade="skip"
from pydantic import BaseModel, field_validator


class Model(BaseModel):
    a: str
    b: str

    @field_validator('a', 'b')
    def check_fields(cls, v):
        return v
```

## Validator on instance method {#validator-instance-method}

This error is raised when you apply validator on an instance method.

```py test="skip" lint="skip" upgrade="skip"
from pydantic import BaseModel, field_validator


class Model(BaseModel):
    a: int = 1

    @field_validator('a')
    def check_a(self, values):
        return values
```

## Root Validator, pre, skip_on_failure {#root-validator-pre-skip}

If you use `@root_validator` with pre=False (the default) you MUST specify `skip_on_failure=True`.
The `skip_on_failure=False` option is no longer available.
If you were not trying to set `skip_on_failure=False` you can safely set `skip_on_failure=True`.
If you do, this root validator will no longer be called if validation fails for any of the fields.

Please see the migration guide for more details. TODO link

## model_validator instance methods {#model-serializer-instance-method}

`@model_serializer` must be applied to instance methods.

This error is raised when you apply `model_serializer` on an instance method without `self`:

```py test="skip" lint="skip" upgrade="skip"
from pydantic import BaseModel, model_serializer


class MyModel(BaseModel):
    a: int

    @model_serializer
    def _serialize(slf, x, y, z):
        return slf
```

Or on a class method:

```py test="skip" lint="skip" upgrade="skip"
from pydantic import BaseModel, model_serializer


class MyModel(BaseModel):
    a: int

    @model_serializer
    @classmethod
    def _serialize(self, x, y, z):
        return self
```

## validator, field, config and info {#validator-field-config-info}

The `field` and `config` parameters are not available in Pydantic V2.
Please use the `info` parameter instead. You can access the configuration via `info.config`
but it is a dictionary instead of an object like it was in Pydantic V1.
The `field` argument is no longer available.

## V1 validator signature {#validator-v1-signature}

This error is raised when you use an unsupported signature for V1 style validator.

```py test="skip" lint="skip" upgrade="skip"
from pydantic import BaseModel, validator


class Model(BaseModel):
    a: int

    @validator('a')
    def check_a(cls, value, foo):
        return value
```

## Unrecognized field_validator signature {#validator-signature}

This error is raised when a `field_validator` or `model_validator` function has the wrong signature.

```py test="skip" lint="skip" upgrade="skip"
from pydantic import BaseModel, field_validator


class Model(BaseModel):
    a: str

    @field_validator('a')
    @classmethod
    def check_a(cls):
        return 'a'
```

## Unrecognized field_serializer signature {#field-serializer-signature}

This error is raised when `field_serializer` function has the wrong signature.

```py test="skip" lint="skip" upgrade="skip"
from pydantic import BaseModel, field_serializer


class Model(BaseModel):
    x: int

    @field_serializer('x')
    def no_args():
        return 'x'
```

Valid serializer signatures are:

```py test="skip" lint="skip" upgrade="skip"
from pydantic import model_serializer

# an instance method with the default mode or `mode='plain'`
@model_serializer('x')  # or @serialize('x', mode='plain')
def ser_x(self, value: Any, info: pydantic.FieldSerializationInfo): ...

# a static method or free-standing function with the default mode or `mode='plain'`
@model_serializer('x')  # or @serialize('x', mode='plain')
@staticmethod
def ser_x(value: Any, info: pydantic.FieldSerializationInfo): ...
# equivalent to
def ser_x(value: Any, info: pydantic.FieldSerializationInfo): ...
serializer('x')(ser_x)

# an instance method with `mode='wrap'`
@model_serializer('x', mode='wrap')
def ser_x(self, value: Any, nxt: pydantic.SerializerFunctionWrapHandler, info: pydantic.FieldSerializationInfo): ...

# a static method or free-standing function with `mode='wrap'`
@model_serializer('x', mode='wrap')
@staticmethod
def ser_x(value: Any, nxt: pydantic.SerializerFunctionWrapHandler, info: pydantic.FieldSerializationInfo): ...
# equivalent to
def ser_x(value: Any, nxt: pydantic.SerializerFunctionWrapHandler, info: pydantic.FieldSerializationInfo): ...
serializer('x')(ser_x)

For all of these, you can also choose to omit the `info` argument, for example:

@model_serializer('x')
def ser_x(self, value: Any): ...

@model_serializer('x', mode='wrap')
def ser_x(self, value: Any, handler: pydantic.SerializerFunctionWrapHandler): ...
```

## Unrecognized model_serializer signature {#model-serializer-signature}

This error is raised when `model_serializer` function has the wrong signature.

```py test="skip" lint="skip" upgrade="skip"
from pydantic import BaseModel, model_serializer


class MyModel(BaseModel):
    a: int

    @model_serializer
    def _serialize(self, x, y, z):
        return self
```

## Multiple field serializers {#multiple-field-serializers}

This error is raised when multiple `model_serializer` functions are defined for a field.

```py test="skip" lint="skip" upgrade="skip"
from pydantic import BaseModel, field_serializer


class MyModel(BaseModel):
    x: int
    y: int

    @field_serializer('x', 'y', json_return_type='str')
    def serializer1(v):
        return f'{v:,}'

    @field_serializer('x', json_return_type='str')
    def serializer2(v):
        return v
```
{% endraw %}
