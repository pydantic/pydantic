Pydantic attempts to provide useful errors. The following sections provide details on common errors developers may
encounter when working with Pydantic, along with suggestions for addressing the error condition.

## Class not fully defined {#class-not-fully-defined}

This error is raised when a type referenced in an annotation of a pydantic-validated type
(such as a subclass of `BaseModel`, or a pydantic `dataclass`) is not defined:

```python
from typing import ForwardRef

from pydantic import BaseModel, PydanticUserError

UndefinedType = ForwardRef('UndefinedType')


class Foobar(BaseModel):
    a: UndefinedType


try:
    Foobar(a=1)
except PydanticUserError as exc_info:
    assert exc_info.code == 'class-not-fully-defined'
```

Or when the type has been defined after usage:

```python
from typing import Optional

from pydantic import BaseModel, PydanticUserError


class Foo(BaseModel):
    a: Optional['Bar'] = None


try:
    # this doesn't work, see raised error
    foo = Foo(a={'b': {'a': None}})
except PydanticUserError as exc_info:
    assert exc_info.code == 'class-not-fully-defined'


class Bar(BaseModel):
    b: 'Foo'


# this works, though
foo = Foo(a={'b': {'a': None}})
```

For BaseModel subclasses, it can be fixed by defining the type and then calling `.model_rebuild()`:

```python
from typing import Optional

from pydantic import BaseModel


class Foo(BaseModel):
    a: Optional['Bar'] = None


class Bar(BaseModel):
    b: 'Foo'


Foo.model_rebuild()

foo = Foo(a={'b': {'a': None}})
```

In other cases, the error message should indicate how to rebuild the class with the appropriate type defined.

## Custom JSON Schema {#custom-json-schema}

The `__modify_schema__` method is no longer supported in V2. You should use the `__get_pydantic_json_schema__` method instead.

The `__modify_schema__` used to receive a single argument representing the JSON schema. See the example below:

```python {title="Old way"}
from pydantic import BaseModel, PydanticUserError

try:

    class Model(BaseModel):
        @classmethod
        def __modify_schema__(cls, field_schema):
            field_schema.update(examples=['example'])

except PydanticUserError as exc_info:
    assert exc_info.code == 'custom-json-schema'
```

The new method `__get_pydantic_json_schema__` receives two arguments: the first is a dictionary denoted as `CoreSchema`,
and the second a callable `handler` that receives a `CoreSchema` as parameter, and returns a JSON schema. See the example
below:

```python {title="New way"}
from typing import Any, Dict

from pydantic_core import CoreSchema

from pydantic import BaseModel, GetJsonSchemaHandler


class Model(BaseModel):
    @classmethod
    def __get_pydantic_json_schema__(
        cls, core_schema: CoreSchema, handler: GetJsonSchemaHandler
    ) -> Dict[str, Any]:
        json_schema = super().__get_pydantic_json_schema__(core_schema, handler)
        json_schema = handler.resolve_ref_schema(json_schema)
        json_schema.update(examples=['example'])
        return json_schema


print(Model.model_json_schema())
"""
{'examples': ['example'], 'properties': {}, 'title': 'Model', 'type': 'object'}
"""
```

## Decorator on missing field {#decorator-missing-field}

This error is raised when you define a decorator with a field that is not valid.

```python
from typing import Any

from pydantic import BaseModel, PydanticUserError, field_validator

try:

    class Model(BaseModel):
        a: str

        @field_validator('b')
        def check_b(cls, v: Any):
            return v

except PydanticUserError as exc_info:
    assert exc_info.code == 'decorator-missing-field'
```

You can use `check_fields=False` if you're inheriting from the model and intended this.

```python
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

```python
from typing import Literal, Union

from pydantic import BaseModel, Field, PydanticUserError


class Cat(BaseModel):
    c: str


class Dog(BaseModel):
    pet_type: Literal['dog']
    d: str


try:

    class Model(BaseModel):
        pet: Union[Cat, Dog] = Field(discriminator='pet_type')
        number: int

except PydanticUserError as exc_info:
    assert exc_info.code == 'discriminator-no-field'
```

## Discriminator alias type {#discriminator-alias-type}

This error is raised when you define a non-string alias on a discriminator field.

```python
from typing import Literal, Union

from pydantic import AliasChoices, BaseModel, Field, PydanticUserError


class Cat(BaseModel):
    pet_type: Literal['cat'] = Field(
        validation_alias=AliasChoices('Pet', 'PET')
    )
    c: str


class Dog(BaseModel):
    pet_type: Literal['dog']
    d: str


try:

    class Model(BaseModel):
        pet: Union[Cat, Dog] = Field(discriminator='pet_type')
        number: int

except PydanticUserError as exc_info:
    assert exc_info.code == 'discriminator-alias-type'
```

## Discriminator needs literal {#discriminator-needs-literal}

This error is raised when you define a non-`Literal` type on a discriminator field.

```python
from typing import Literal, Union

from pydantic import BaseModel, Field, PydanticUserError


class Cat(BaseModel):
    pet_type: int
    c: str


class Dog(BaseModel):
    pet_type: Literal['dog']
    d: str


try:

    class Model(BaseModel):
        pet: Union[Cat, Dog] = Field(discriminator='pet_type')
        number: int

except PydanticUserError as exc_info:
    assert exc_info.code == 'discriminator-needs-literal'
```

## Discriminator alias {#discriminator-alias}

This error is raised when you define different aliases on discriminator fields.

```python
from typing import Literal, Union

from pydantic import BaseModel, Field, PydanticUserError


class Cat(BaseModel):
    pet_type: Literal['cat'] = Field(validation_alias='PET')
    c: str


class Dog(BaseModel):
    pet_type: Literal['dog'] = Field(validation_alias='Pet')
    d: str


try:

    class Model(BaseModel):
        pet: Union[Cat, Dog] = Field(discriminator='pet_type')
        number: int

except PydanticUserError as exc_info:
    assert exc_info.code == 'discriminator-alias'
```

## Invalid discriminator validator {#discriminator-validator}

This error is raised when you use a before, wrap, or plain validator on a discriminator field.

This is disallowed because the discriminator field is used to determine the type of the model to use for validation,
so you can't use a validator that might change its value.

```python
from typing import Literal, Union

from pydantic import BaseModel, Field, PydanticUserError, field_validator


class Cat(BaseModel):
    pet_type: Literal['cat']

    @field_validator('pet_type', mode='before')
    @classmethod
    def validate_pet_type(cls, v):
        if v == 'kitten':
            return 'cat'
        return v


class Dog(BaseModel):
    pet_type: Literal['dog']


try:

    class Model(BaseModel):
        pet: Union[Cat, Dog] = Field(discriminator='pet_type')
        number: int

except PydanticUserError as exc_info:
    assert exc_info.code == 'discriminator-validator'
```

This can be worked around by using a standard `Union`, dropping the discriminator:

```python
from typing import Literal, Union

from pydantic import BaseModel, field_validator


class Cat(BaseModel):
    pet_type: Literal['cat']

    @field_validator('pet_type', mode='before')
    @classmethod
    def validate_pet_type(cls, v):
        if v == 'kitten':
            return 'cat'
        return v


class Dog(BaseModel):
    pet_type: Literal['dog']


class Model(BaseModel):
    pet: Union[Cat, Dog]


assert Model(pet={'pet_type': 'kitten'}).pet.pet_type == 'cat'
```

## Callable discriminator case with no tag {#callable-discriminator-no-tag}

This error is raised when a `Union` that uses a callable `Discriminator` doesn't have `Tag` annotations for all cases.

```python
from typing import Union

from typing_extensions import Annotated

from pydantic import BaseModel, Discriminator, PydanticUserError, Tag


def model_x_discriminator(v):
    if isinstance(v, str):
        return 'str'
    if isinstance(v, (dict, BaseModel)):
        return 'model'


# tag missing for both union choices
try:

    class DiscriminatedModel(BaseModel):
        x: Annotated[
            Union[str, 'DiscriminatedModel'],
            Discriminator(model_x_discriminator),
        ]

except PydanticUserError as exc_info:
    assert exc_info.code == 'callable-discriminator-no-tag'

# tag missing for `'DiscriminatedModel'` union choice
try:

    class DiscriminatedModel(BaseModel):
        x: Annotated[
            Union[Annotated[str, Tag('str')], 'DiscriminatedModel'],
            Discriminator(model_x_discriminator),
        ]

except PydanticUserError as exc_info:
    assert exc_info.code == 'callable-discriminator-no-tag'

# tag missing for `str` union choice
try:

    class DiscriminatedModel(BaseModel):
        x: Annotated[
            Union[str, Annotated['DiscriminatedModel', Tag('model')]],
            Discriminator(model_x_discriminator),
        ]

except PydanticUserError as exc_info:
    assert exc_info.code == 'callable-discriminator-no-tag'
```

## `TypedDict` version {#typed-dict-version}

This error is raised when you use [typing.TypedDict][]
instead of `typing_extensions.TypedDict` on Python < 3.12.

## Model parent field overridden {#model-field-overridden}

This error is raised when a field defined on a base class was overridden by a non-annotated attribute.

```python
from pydantic import BaseModel, PydanticUserError


class Foo(BaseModel):
    a: float


try:

    class Bar(Foo):
        x: float = 12.3
        a = 123.0

except PydanticUserError as exc_info:
    assert exc_info.code == 'model-field-overridden'
```

## Model field missing annotation {#model-field-missing-annotation}

This error is raised when a field doesn't have an annotation.

```python
from pydantic import BaseModel, Field, PydanticUserError

try:

    class Model(BaseModel):
        a = Field('foobar')
        b = None

except PydanticUserError as exc_info:
    assert exc_info.code == 'model-field-missing-annotation'
```

If the field is not meant to be a field, you may be able to resolve the error
by annotating it as a `ClassVar`:

```python
from typing import ClassVar

from pydantic import BaseModel


class Model(BaseModel):
    a: ClassVar[str]
```

Or updating `model_config['ignored_types']`:

```python
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

## `Config` and `model_config` both defined {#config-both}

This error is raised when `class Config` and `model_config` are used together.

```python
from pydantic import BaseModel, ConfigDict, PydanticUserError

try:

    class Model(BaseModel):
        model_config = ConfigDict(from_attributes=True)

        a: str

        class Config:
            from_attributes = True

except PydanticUserError as exc_info:
    assert exc_info.code == 'config-both'
```

## Keyword arguments removed {#removed-kwargs}

This error is raised when the keyword arguments are not available in Pydantic V2.

For example, `regex` is removed from Pydantic V2:

```python
from pydantic import BaseModel, Field, PydanticUserError

try:

    class Model(BaseModel):
        x: str = Field(regex='test')

except PydanticUserError as exc_info:
    assert exc_info.code == 'removed-kwargs'
```

## Circular reference schema {#circular-reference-schema}

This error is raised when a circular reference is found that would otherwise result in an infinite recursion.

For example, this is a valid type alias:

```python {test="skip" lint="skip" upgrade="skip"}
type A = list[A] | None
```

while these are not:

```python {test="skip" lint="skip" upgrade="skip"}
type A = A

type B = C
type C = B
```

## JSON schema invalid type {#invalid-for-json-schema}

This error is raised when Pydantic fails to generate a JSON schema for some `CoreSchema`.

```python
from pydantic import BaseModel, ImportString, PydanticUserError


class Model(BaseModel):
    a: ImportString


try:
    Model.model_json_schema()
except PydanticUserError as exc_info:
    assert exc_info.code == 'invalid-for-json-schema'
```

## JSON schema already used {#json-schema-already-used}

This error is raised when the JSON schema generator has already been used to generate a JSON schema.
You must create a new instance to generate a new JSON schema.

## BaseModel instantiated {#base-model-instantiated}

This error is raised when you instantiate `BaseModel` directly. Pydantic models should inherit from `BaseModel`.

```python
from pydantic import BaseModel, PydanticUserError

try:
    BaseModel()
except PydanticUserError as exc_info:
    assert exc_info.code == 'base-model-instantiated'
```

## Undefined annotation {#undefined-annotation}

This error is raised when handling undefined annotations during `CoreSchema` generation.

```python
from pydantic import BaseModel, PydanticUndefinedAnnotation


class Model(BaseModel):
    a: 'B'  # noqa F821


try:
    Model.model_rebuild()
except PydanticUndefinedAnnotation as exc_info:
    assert exc_info.code == 'undefined-annotation'
```

## Schema for unknown type {#schema-for-unknown-type}

This error is raised when Pydantic fails to generate a `CoreSchema` for some type.

```python
from pydantic import BaseModel, PydanticUserError

try:

    class Model(BaseModel):
        x: 43 = 123

except PydanticUserError as exc_info:
    assert exc_info.code == 'schema-for-unknown-type'
```

## Import error {#import-error}

This error is raised when you try to import an object that was available in Pydantic V1, but has been removed in
Pydantic V2.

See the [Migration Guide](../migration.md) for more information.

## `create_model` field definitions {#create-model-field-definitions}

This error is raised when you provide field definitions input in `create_model` that is not valid.

```python
from pydantic import PydanticUserError, create_model

try:
    create_model('FooModel', foo=(str, 'default value', 'more'))
except PydanticUserError as exc_info:
    assert exc_info.code == 'create-model-field-definitions'
```

Or when you use [`typing.Annotated`][] with invalid input

```python
from typing_extensions import Annotated

from pydantic import PydanticUserError, create_model

try:
    create_model('FooModel', foo=Annotated[str, 'NotFieldInfoValue'])
except PydanticUserError as exc_info:
    assert exc_info.code == 'create-model-field-definitions'
```

## `create_model` config base {#create-model-config-base}

This error is raised when you use both `__config__` and `__base__` together in `create_model`.

```python
from pydantic import BaseModel, ConfigDict, PydanticUserError, create_model

try:
    config = ConfigDict(frozen=True)
    model = create_model(
        'FooModel', foo=(int, ...), __config__=config, __base__=BaseModel
    )
except PydanticUserError as exc_info:
    assert exc_info.code == 'create-model-config-base'
```

## Validator with no fields {#validator-no-fields}

This error is raised when you use validator bare (with no fields).

```python
from pydantic import BaseModel, PydanticUserError, field_validator

try:

    class Model(BaseModel):
        a: str

        @field_validator
        def checker(cls, v):
            return v

except PydanticUserError as exc_info:
    assert exc_info.code == 'validator-no-fields'
```

Validators should be used with fields and keyword arguments.

```python
from pydantic import BaseModel, field_validator


class Model(BaseModel):
    a: str

    @field_validator('a')
    def checker(cls, v):
        return v
```

## Invalid validator fields {#validator-invalid-fields}

This error is raised when you use a validator with non-string fields.

```python
from pydantic import BaseModel, PydanticUserError, field_validator

try:

    class Model(BaseModel):
        a: str
        b: str

        @field_validator(['a', 'b'])
        def check_fields(cls, v):
            return v

except PydanticUserError as exc_info:
    assert exc_info.code == 'validator-invalid-fields'
```

Fields should be passed as separate string arguments:

```python
from pydantic import BaseModel, field_validator


class Model(BaseModel):
    a: str
    b: str

    @field_validator('a', 'b')
    def check_fields(cls, v):
        return v
```

## Validator on instance method {#validator-instance-method}

This error is raised when you apply a validator on an instance method.

```python
from pydantic import BaseModel, PydanticUserError, field_validator

try:

    class Model(BaseModel):
        a: int = 1

        @field_validator('a')
        def check_a(self, value):
            return value

except PydanticUserError as exc_info:
    assert exc_info.code == 'validator-instance-method'
```

## `json_schema_input_type` used with the wrong mode {#validator-input-type}

This error is raised when you explicitly specify a value for the `json_schema_input_type`
argument and `mode` isn't set to either `'before'`, `'plain'` or `'wrap'`.

```python
from pydantic import BaseModel, PydanticUserError, field_validator

try:

    class Model(BaseModel):
        a: int = 1

        @field_validator('a', mode='after', json_schema_input_type=int)
        @classmethod
        def check_a(self, value):
            return value

except PydanticUserError as exc_info:
    assert exc_info.code == 'validator-input-type'
```

Documenting the JSON Schema input type is only possible for validators where the given
value can be anything. That is why it isn't available for `after` validators, where
the value is first validated against the type annotation.

## Root validator, `pre`, `skip_on_failure` {#root-validator-pre-skip}

If you use `@root_validator` with `pre=False` (the default) you MUST specify `skip_on_failure=True`.
The `skip_on_failure=False` option is no longer available.

If you were not trying to set `skip_on_failure=False`, you can safely set `skip_on_failure=True`.
If you do, this root validator will no longer be called if validation fails for any of the fields.

Please see the [Migration Guide](../migration.md) for more details.

## `model_serializer` instance methods {#model-serializer-instance-method}

`@model_serializer` must be applied to instance methods.

This error is raised when you apply `model_serializer` on an instance method without `self`:

```python
from pydantic import BaseModel, PydanticUserError, model_serializer

try:

    class MyModel(BaseModel):
        a: int

        @model_serializer
        def _serialize(slf, x, y, z):
            return slf

except PydanticUserError as exc_info:
    assert exc_info.code == 'model-serializer-instance-method'
```

Or on a class method:

```python
from pydantic import BaseModel, PydanticUserError, model_serializer

try:

    class MyModel(BaseModel):
        a: int

        @model_serializer
        @classmethod
        def _serialize(self, x, y, z):
            return self

except PydanticUserError as exc_info:
    assert exc_info.code == 'model-serializer-instance-method'
```

## `validator`, `field`, `config`, and `info` {#validator-field-config-info}

The `field` and `config` parameters are not available in Pydantic V2.
Please use the `info` parameter instead.

You can access the configuration via `info.config`,
but it is a dictionary instead of an object like it was in Pydantic V1.

The `field` argument is no longer available.

## Pydantic V1 validator signature {#validator-v1-signature}

This error is raised when you use an unsupported signature for Pydantic V1-style validator.

```python
import warnings

from pydantic import BaseModel, PydanticUserError, validator

warnings.filterwarnings('ignore', category=DeprecationWarning)

try:

    class Model(BaseModel):
        a: int

        @validator('a')
        def check_a(cls, value, foo):
            return value

except PydanticUserError as exc_info:
    assert exc_info.code == 'validator-v1-signature'
```

## Unrecognized `field_validator` signature {#validator-signature}

This error is raised when a `field_validator` or `model_validator` function has the wrong signature.

```python
from pydantic import BaseModel, PydanticUserError, field_validator

try:

    class Model(BaseModel):
        a: str

        @field_validator('a')
        @classmethod
        def check_a(cls):
            return 'a'

except PydanticUserError as exc_info:
    assert exc_info.code == 'validator-signature'
```

## Unrecognized `field_serializer` signature {#field-serializer-signature}

This error is raised when the `field_serializer` function has the wrong signature.

```python
from pydantic import BaseModel, PydanticUserError, field_serializer

try:

    class Model(BaseModel):
        x: int

        @field_serializer('x')
        def no_args():
            return 'x'

except PydanticUserError as exc_info:
    assert exc_info.code == 'field-serializer-signature'
```

Valid field serializer signatures are:

```python {test="skip" lint="skip" upgrade="skip"}
from pydantic import FieldSerializationInfo, SerializerFunctionWrapHandler, field_serializer

# an instance method with the default mode or `mode='plain'`
@field_serializer('x')  # or @field_serializer('x', mode='plain')
def ser_x(self, value: Any, info: FieldSerializationInfo): ...

# a static method or function with the default mode or `mode='plain'`
@field_serializer('x')  # or @field_serializer('x', mode='plain')
@staticmethod
def ser_x(value: Any, info: FieldSerializationInfo): ...

# equivalent to
def ser_x(value: Any, info: FieldSerializationInfo): ...
serializer('x')(ser_x)

# an instance method with `mode='wrap'`
@field_serializer('x', mode='wrap')
def ser_x(self, value: Any, nxt: SerializerFunctionWrapHandler, info: FieldSerializationInfo): ...

# a static method or function with `mode='wrap'`
@field_serializer('x', mode='wrap')
@staticmethod
def ser_x(value: Any, nxt: SerializerFunctionWrapHandler, info: FieldSerializationInfo): ...

# equivalent to
def ser_x(value: Any, nxt: SerializerFunctionWrapHandler, info: FieldSerializationInfo): ...
serializer('x')(ser_x)

# For all of these, you can also choose to omit the `info` argument, for example:
@field_serializer('x')
def ser_x(self, value: Any): ...

@field_serializer('x', mode='wrap')
def ser_x(self, value: Any, handler: SerializerFunctionWrapHandler): ...
```

## Unrecognized `model_serializer` signature {#model-serializer-signature}

This error is raised when the `model_serializer` function has the wrong signature.

```python
from pydantic import BaseModel, PydanticUserError, model_serializer

try:

    class MyModel(BaseModel):
        a: int

        @model_serializer
        def _serialize(self, x, y, z):
            return self

except PydanticUserError as exc_info:
    assert exc_info.code == 'model-serializer-signature'
```

Valid model serializer signatures are:

```python {test="skip" lint="skip" upgrade="skip"}
from pydantic import SerializerFunctionWrapHandler, SerializationInfo, model_serializer

# an instance method with the default mode or `mode='plain'`
@model_serializer  # or model_serializer(mode='plain')
def mod_ser(self, info: SerializationInfo): ...

# an instance method with `mode='wrap'`
@model_serializer(mode='wrap')
def mod_ser(self, handler: SerializerFunctionWrapHandler, info: SerializationInfo):

# For all of these, you can also choose to omit the `info` argument, for example:
@model_serializer(mode='plain')
def mod_ser(self): ...

@model_serializer(mode='wrap')
def mod_ser(self, handler: SerializerFunctionWrapHandler): ...
```

## Multiple field serializers {#multiple-field-serializers}

This error is raised when multiple `model_serializer` functions are defined for a field.

```python
from pydantic import BaseModel, PydanticUserError, field_serializer

try:

    class MyModel(BaseModel):
        x: int
        y: int

        @field_serializer('x', 'y')
        def serializer1(v):
            return f'{v:,}'

        @field_serializer('x')
        def serializer2(v):
            return v

except PydanticUserError as exc_info:
    assert exc_info.code == 'multiple-field-serializers'
```

## Invalid annotated type {#invalid-annotated-type}

This error is raised when an annotation cannot annotate a type.

```python
from typing_extensions import Annotated

from pydantic import BaseModel, FutureDate, PydanticUserError

try:

    class Model(BaseModel):
        foo: Annotated[str, FutureDate()]

except PydanticUserError as exc_info:
    assert exc_info.code == 'invalid-annotated-type'
```

## `config` is unused with `TypeAdapter` {#type-adapter-config-unused}

You will get this error if you try to pass `config` to `TypeAdapter` when the type is a type that
has its own config that cannot be overridden (currently this is only `BaseModel`, `TypedDict` and `dataclass`):

```python
from typing_extensions import TypedDict

from pydantic import ConfigDict, PydanticUserError, TypeAdapter


class MyTypedDict(TypedDict):
    x: int


try:
    TypeAdapter(MyTypedDict, config=ConfigDict(strict=True))
except PydanticUserError as exc_info:
    assert exc_info.code == 'type-adapter-config-unused'
```

Instead you'll need to subclass the type and override or set the config on it:

```python
from typing_extensions import TypedDict

from pydantic import ConfigDict, TypeAdapter


class MyTypedDict(TypedDict):
    x: int

    # or `model_config = ...` for BaseModel
    __pydantic_config__ = ConfigDict(strict=True)


TypeAdapter(MyTypedDict)  # ok
```

## Cannot specify `model_config['extra']` with `RootModel` {#root-model-extra}

Because `RootModel` is not capable of storing or even accepting extra fields during initialization, we raise an error
if you try to specify a value for the config setting `'extra'` when creating a subclass of `RootModel`:

```python
from pydantic import PydanticUserError, RootModel

try:

    class MyRootModel(RootModel):
        model_config = {'extra': 'allow'}
        root: int

except PydanticUserError as exc_info:
    assert exc_info.code == 'root-model-extra'
```

## Cannot evaluate type annotation {#unevaluable-type-annotation}

Because type annotations are evaluated *after* assignments, you might get unexpected results when using a type annotation name
that clashes with one of your fields. We raise an error in the following case:

```python {test="skip"}
from datetime import date

from pydantic import BaseModel, Field


class Model(BaseModel):
    date: date = Field(description='A date')
```

As a workaround, you can either use an alias or change your import:

```python {lint="skip"}
import datetime
# Or `from datetime import date as _date`

from pydantic import BaseModel, Field


class Model(BaseModel):
    date: datetime.date = Field(description='A date')
```

## Incompatible `dataclass` `init` and `extra` settings {#dataclass-init-false-extra-allow}

Pydantic does not allow the specification of the `extra='allow'` setting on a dataclass
while any of the fields have `init=False` set.

Thus, you may not do something like the following:

```python {test="skip"}
from pydantic import ConfigDict, Field
from pydantic.dataclasses import dataclass


@dataclass(config=ConfigDict(extra='allow'))
class A:
    a: int = Field(init=False, default=1)
```

The above snippet results in the following error during schema building for the `A` dataclass:

```
pydantic.errors.PydanticUserError: Field a has `init=False` and dataclass has config setting `extra="allow"`.
This combination is not allowed.
```

## Incompatible `init` and `init_var` settings on `dataclass` field {#clashing-init-and-init-var}

The `init=False` and `init_var=True` settings are mutually exclusive. Doing so results in the `PydanticUserError` shown in the example below.

```python {test="skip"}
from pydantic import Field
from pydantic.dataclasses import dataclass


@dataclass
class Foo:
    bar: str = Field(init=False, init_var=True)


"""
pydantic.errors.PydanticUserError: Dataclass field bar has init=False and init_var=True, but these are mutually exclusive.
"""
```

## `model_config` is used as a model field {#model-config-invalid-field-name}

This error is raised when `model_config` is used as the name of a field.

```python
from pydantic import BaseModel, PydanticUserError

try:

    class Model(BaseModel):
        model_config: str

except PydanticUserError as exc_info:
    assert exc_info.code == 'model-config-invalid-field-name'
```

## [`with_config`][pydantic.config.with_config] is used on a `BaseModel` subclass {#with-config-on-model}

This error is raised when the [`with_config`][pydantic.config.with_config] decorator is used on a class which is already a Pydantic model (use the `model_config` attribute instead).

```python
from pydantic import BaseModel, PydanticUserError, with_config

try:

    @with_config({'allow_inf_nan': True})
    class Model(BaseModel):
        bar: str

except PydanticUserError as exc_info:
    assert exc_info.code == 'with-config-on-model'
```

## `dataclass` is used on a `BaseModel` subclass {#dataclass-on-model}

This error is raised when the Pydantic `dataclass` decorator is used on a class which is already
a Pydantic model.

```python
from pydantic import BaseModel, PydanticUserError
from pydantic.dataclasses import dataclass

try:

    @dataclass
    class Model(BaseModel):
        bar: str

except PydanticUserError as exc_info:
    assert exc_info.code == 'dataclass-on-model'
```

## Unsupported type for `validate_call` {#validate-call-type}

`validate_call` has some limitations on the callables it can validate. This error is raised when you try to use it with an unsupported callable. Currently the supported callables are functions (including lambdas) and methods and instances of [`partial`][functools.partial]. In the case of [`partial`][functools.partial], the function being partially applied must be one of the supported callables.

### `@classmethod`, `@staticmethod`, and `@property`

These decorators must be put before `validate_call`.

```python
from pydantic import PydanticUserError, validate_call

# error
try:

    class A:
        @validate_call
        @classmethod
        def f1(cls): ...

except PydanticUserError as exc_info:
    assert exc_info.code == 'validate-call-type'


# correct
@classmethod
@validate_call
def f2(cls): ...
```

### Classes

While classes are callables themselves, `validate_call` can't be applied on them, as it needs to know about which method to use (`__init__` or `__new__`) to fetch type annotations. If you want to validate the constructor of a class, you should put `validate_call` on top of the appropriate method instead.

```python
from pydantic import PydanticUserError, validate_call

# error
try:

    @validate_call
    class A1: ...

except PydanticUserError as exc_info:
    assert exc_info.code == 'validate-call-type'


# correct
class A2:
    @validate_call
    def __init__(self): ...

    @validate_call
    def __new__(cls): ...
```

### Custom callable

Although you can create custom callable types in Python by implementing a `__call__` method, currently the instances of these types cannot be validated with `validate_call`. This may change in the future, but for now, you should use `validate_call` explicitly on `__call__` instead.

```python
from pydantic import PydanticUserError, validate_call

# error
try:

    class A1:
        def __call__(self): ...

    validate_call(A1())

except PydanticUserError as exc_info:
    assert exc_info.code == 'validate-call-type'


# correct
class A2:
    @validate_call
    def __call__(self): ...
```

### Invalid signature

This is generally less common, but a possible reason is that you are trying to validate a method that doesn't have at least one argument (usually `self`).

```python
from pydantic import PydanticUserError, validate_call

try:

    class A:
        def f(): ...

    validate_call(A().f)
except PydanticUserError as exc_info:
    assert exc_info.code == 'validate-call-type'
```

## [`Unpack`][typing.Unpack] used without a [`TypedDict`][typing.TypedDict] {#unpack-typed-dict}

This error is raised when [`Unpack`][typing.Unpack] is used with something other than
a [`TypedDict`][typing.TypedDict] class object to type hint variadic keyword parameters.

For reference, see the [related specification section] and [PEP 692].

```python
from typing_extensions import Unpack

from pydantic import PydanticUserError, validate_call

try:

    @validate_call
    def func(**kwargs: Unpack[int]):
        pass

except PydanticUserError as exc_info:
    assert exc_info.code == 'unpack-typed-dict'
```

## Overlapping unpacked [`TypedDict`][typing.TypedDict] fields and arguments {#overlapping-unpack-typed-dict}

This error is raised when the typed dictionary used to type hint variadic keywords parameters has field names
overlapping with other parameters (unless [positional only][positional-only_parameter]).

For reference, see the [related specification section] and [PEP 692].

```python
from typing_extensions import TypedDict, Unpack

from pydantic import PydanticUserError, validate_call


class TD(TypedDict):
    a: int


try:

    @validate_call
    def func(a: int, **kwargs: Unpack[TD]):
        pass

except PydanticUserError as exc_info:
    assert exc_info.code == 'overlapping-unpack-typed-dict'
```

[related specification section]: https://typing.readthedocs.io/en/latest/spec/callables.html#unpack-for-keyword-arguments
[PEP 692]: https://peps.python.org/pep-0692/

## Invalid `Self` type {#invalid-self-type}

Currently, [`Self`][typing.Self] can only be used to annotate a field of a class (specifically, subclasses of [`BaseModel`][pydantic.BaseModel], [`NamedTuple`][typing.NamedTuple], [`TypedDict`][typing.TypedDict], or dataclasses). Attempting to use [`Self`][typing.Self] in any other ways will raise this error.

```python
from typing_extensions import Self

from pydantic import PydanticUserError, validate_call

try:

    @validate_call
    def func(self: Self):
        pass

except PydanticUserError as exc_info:
    assert exc_info.code == 'invalid-self-type'
```

The following example of [`validate_call()`][pydantic.validate_call] will also raise this error, even though it is correct from a type-checking perspective. This may be supported in the future.

```python
from typing_extensions import Self

from pydantic import BaseModel, PydanticUserError, validate_call

try:

    class A(BaseModel):
        @validate_call
        def func(self, arg: Self):
            pass

except PydanticUserError as exc_info:
    assert exc_info.code == 'invalid-self-type'
```
