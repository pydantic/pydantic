Pydantic attempts to provide useful errors. The following sections provide details on common errors developers may
encounter when working with Pydantic, along with suggestions for addressing the error condition.

<!-- Note: raw tag is used to avoid rendering of jinja2 template tags in the docs. -->
{% raw %}
## Class not fully defined {#class-not-fully-defined}

This error is raised when a type referenced in an annotation of a pydantic-validated type
(such as a subclass of `BaseModel`, or a pydantic `dataclass`) is not defined:

```py
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

```py
from typing import Optional

from pydantic import BaseModel, PydanticUserError


class Foo(BaseModel):
    a: Optional['Bar'] = None


class Bar(BaseModel):
    b: 'Foo'


try:
    foo = Foo(a={'b': {'a': None}})
except PydanticUserError as exc_info:
    assert exc_info.code == 'class-not-fully-defined'
```

For BaseModel subclasses, it can be fixed by defining the type and then calling `.model_rebuild()`:

```py
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

```py title="Old way"
from pydantic import BaseModel, PydanticUserError

try:

    class Model(BaseModel):
        @classmethod
        def __modify_schema__(cls, field_schema):
            field_schema.update(examples='examples')

except PydanticUserError as exc_info:
    assert exc_info.code == 'custom-json-schema'
```

The new method `__get_pydantic_json_schema__` receives two arguments: the first is a dictionary denoted as `CoreSchema`,
and the second a callable `handler` that receives a `CoreSchema` as parameter, and returns a JSON schema. See the example
below:

```py title="New way"
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
        json_schema.update(examples='examples')
        return json_schema


print(Model.model_json_schema())
"""
{'examples': 'examples', 'properties': {}, 'title': 'Model', 'type': 'object'}
"""
```

## Decorator on missing field {#decorator-missing-field}

This error is raised when you define a decorator with a field that is not valid.

```py
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

```py
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

```py
from typing import Union

from typing_extensions import Literal

from pydantic import BaseModel, Field, PydanticUserError


class Cat(BaseModel):
    c: str


class Dog(BaseModel):
    pet_type: Literal['dog']
    d: str


try:

    class Model(BaseModel):
        pet: Union[Cat, Dog] = Field(..., discriminator='pet_type')
        number: int

except PydanticUserError as exc_info:
    assert exc_info.code == 'discriminator-no-field'
```

## Discriminator alias type {#discriminator-alias-type}

This error is raised when you define a non-string alias on a discriminator field.

```py
from typing import Union

from typing_extensions import Literal

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
        pet: Union[Cat, Dog] = Field(..., discriminator='pet_type')
        number: int

except PydanticUserError as exc_info:
    assert exc_info.code == 'discriminator-alias-type'
```

## Discriminator needs literal {#discriminator-needs-literal}

This error is raised when you define a non-`Literal` type on a discriminator field.

```py
from typing import Union

from typing_extensions import Literal

from pydantic import BaseModel, Field, PydanticUserError


class Cat(BaseModel):
    pet_type: int
    c: str


class Dog(BaseModel):
    pet_type: Literal['dog']
    d: str


try:

    class Model(BaseModel):
        pet: Union[Cat, Dog] = Field(..., discriminator='pet_type')
        number: int

except PydanticUserError as exc_info:
    assert exc_info.code == 'discriminator-needs-literal'
```

## Discriminator alias {#discriminator-alias}

This error is raised when you define different aliases on discriminator fields.

```py
from typing import Union

from typing_extensions import Literal

from pydantic import BaseModel, Field, PydanticUserError


class Cat(BaseModel):
    pet_type: Literal['cat'] = Field(validation_alias='PET')
    c: str


class Dog(BaseModel):
    pet_type: Literal['dog'] = Field(validation_alias='Pet')
    d: str


try:

    class Model(BaseModel):
        pet: Union[Cat, Dog] = Field(..., discriminator='pet_type')
        number: int

except PydanticUserError as exc_info:
    assert exc_info.code == 'discriminator-alias'
```

## Invalid discriminator validator {#discriminator-validator}

This error is raised when you use a before, wrap, or plain validator on a discriminator field.

This is disallowed because the discriminator field is used to determine the type of the model to use for validation,
so you can't use a validator that might change its value.

```py
from typing import Union

from typing_extensions import Literal

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
        pet: Union[Cat, Dog] = Field(..., discriminator='pet_type')
        number: int

except PydanticUserError as exc_info:
    assert exc_info.code == 'discriminator-validator'
```

This can be worked around by using a standard `Union`, dropping the discriminator:

```py
from typing import Union

from typing_extensions import Literal

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


## `TypedDict` version {#typed-dict-version}

This error is raised when you use `typing.TypedDict`
instead of `typing_extensions.TypedDict` on Python < 3.12.

## Model parent field overridden {#model-field-overridden}

This error is raised when a field defined on a base class was overridden by a non-annotated attribute.

```py
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

```py
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

```py
from typing import ClassVar

from pydantic import BaseModel


class Model(BaseModel):
    a: ClassVar[str]
```

Or updating `model_config['ignored_types']`:

```py
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

```py
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

```py
from pydantic import BaseModel, Field, PydanticUserError

try:

    class Model(BaseModel):
        x: str = Field(regex='test')

except PydanticUserError as exc_info:
    assert exc_info.code == 'removed-kwargs'
```

## JSON schema invalid type {#invalid-for-json-schema}

This error is raised when Pydantic fails to generate a JSON schema for some `CoreSchema`.

```py
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

```py
from pydantic import BaseModel, PydanticUserError

try:
    BaseModel()
except PydanticUserError as exc_info:
    assert exc_info.code == 'base-model-instantiated'
```

## Undefined annotation {#undefined-annotation}

This error is raised when handling undefined annotations during `CoreSchema` generation.

```py
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

```py
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

```py
from pydantic import PydanticUserError, create_model

try:
    create_model('FooModel', foo=(str, 'default value', 'more'))
except PydanticUserError as exc_info:
    assert exc_info.code == 'create-model-field-definitions'
```

## `create_model` config base {#create-model-config-base}

This error is raised when you use both `__config__` and `__base__` together in `create_model`.

```py
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

```py
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

```py
from pydantic import BaseModel, field_validator


class Model(BaseModel):
    a: str

    @field_validator('a')
    def checker(cls, v):
        return v
```

## Invalid validator fields {#validator-invalid-fields}

This error is raised when you use a validator with non-string fields.

```py
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

```py
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

```py
from pydantic import BaseModel, PydanticUserError, field_validator

try:

    class Model(BaseModel):
        a: int = 1

        @field_validator('a')
        def check_a(self, values):
            return values

except PydanticUserError as exc_info:
    assert exc_info.code == 'validator-instance-method'
```

## Root validator, `pre`, `skip_on_failure` {#root-validator-pre-skip}

If you use `@root_validator` with `pre=False` (the default) you MUST specify `skip_on_failure=True`.
The `skip_on_failure=False` option is no longer available.

If you were not trying to set `skip_on_failure=False`, you can safely set `skip_on_failure=True`.
If you do, this root validator will no longer be called if validation fails for any of the fields.

Please see the [Migration Guide](../migration.md) for more details.

## `model_serializer` instance methods {#model-serializer-instance-method}

`@model_serializer` must be applied to instance methods.

This error is raised when you apply `model_serializer` on an instance method without `self`:

```py
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

```py
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

```py
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

```py
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

```py
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

## Unrecognized `model_serializer` signature {#model-serializer-signature}

This error is raised when the `model_serializer` function has the wrong signature.

```py
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

## Multiple field serializers {#multiple-field-serializers}

This error is raised when multiple `model_serializer` functions are defined for a field.

```py
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

## Invalid annotated type {#invalid_annotated_type}

This error is raised when an annotation cannot annotate a type.

```py
from typing_extensions import Annotated

from pydantic import BaseModel, FutureDate, PydanticUserError

try:

    class Model(BaseModel):
        foo: Annotated[str, FutureDate()]

except PydanticUserError as exc_info:
    assert exc_info.code == 'invalid_annotated_type'
```

## `config` is unused with TypeAdapter {#type-adapter-config-unused}

You will get this error if you try to pass `config` to `TypeAdapter` when the type is a type that
has it's own config that cannot be overridden (currently this is only `BaseModel`, `TypedDict` and `dataclass`):

```py
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

```py
from typing_extensions import TypedDict

from pydantic import ConfigDict, TypeAdapter


class MyTypedDict(TypedDict):
    x: int

    # or `model_config = ...` for BaseModel
    __pydantic_config__ = ConfigDict(strict=True)


TypeAdapter(MyTypedDict)  # ok
```

{% endraw %}
