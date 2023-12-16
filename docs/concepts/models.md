??? api "API Documentation"
    [`pydantic.main.BaseModel`][pydantic.main.BaseModel]<br>

One of the primary ways of defining schema in Pydantic is via models. Models are simply classes which inherit from
[`pydantic.BaseModel`][pydantic.main.BaseModel] and define fields as annotated attributes.

You can think of models as similar to structs in languages like C, or as the requirements of a single endpoint
in an API.

Models share many similarities with Python's dataclasses, but have been designed with some subtle-yet-important
differences that streamline certain workflows related to validation, serialization, and JSON schema generation.
You can find more discussion of this in the [Dataclasses](dataclasses.md) section of the docs.

Untrusted data can be passed to a model and, after parsing and validation, Pydantic guarantees that the fields
of the resultant model instance will conform to the field types defined on the model.

!!! note "Validation — a _deliberate_ misnomer"
    ### TL;DR

    We use the term "validation" to refer to the process of instantiating a model (or other type) that adheres to specified types and
    constraints. This task, which Pydantic is well known for, is most widely recognized as "validation" in colloquial terms,
    even though in other contexts the term "validation" may be more restrictive.

    ---

    ### The long version

    The potential confusion around the term "validation" arises from the fact that, strictly speaking, Pydantic's
    primary focus doesn't align precisely with the dictionary definition of "validation":

    > ### validation
    > _noun_
    > the action of checking or proving the validity or accuracy of something.

    In Pydantic, the term "validation" refers to the process of instantiating a model (or other type) that adheres to specified
    types and constraints. Pydantic guarantees the types and constraints of the output, not the input data.
    This distinction becomes apparent when considering that Pydantic's `ValidationError` is raised
    when data cannot be successfully parsed into a model instance.

    While this distinction may initially seem subtle, it holds practical significance.
    In some cases, "validation" goes beyond just model creation, and can include the copying and coercion of data.
    This can involve copying arguments passed to the constructor in order to perform coercion to a new type
    without mutating the original input data. For a more in-depth understanding of the implications for your usage,
    refer to the [Data Conversion](#data-conversion) and [Attribute Copies](#attribute-copies) sections below.

    In essence, Pydantic's primary goal is to assure that the resulting structure post-processing (termed "validation")
    precisely conforms to the applied type hints. Given the widespread adoption of "validation" as the colloquial term
    for this process, we will consistently use it in our documentation.

    While the terms "parse" and "validation" were previously used interchangeably, moving forward, we aim to exclusively employ "validate",
    with "parse" reserved specifically for discussions related to [JSON parsing](../concepts/json.md).

## Basic model usage

```py group="basic-model"
from pydantic import BaseModel


class User(BaseModel):
    id: int
    name: str = 'Jane Doe'
```

In this example, `User` is a model with two fields:

* `id`, which is an integer and is required
* `name`, which is a string and is not required (it has a default value).

```py group="basic-model"
user = User(id='123')
```

In this example, `user` is an instance of `User`.
Initialization of the object will perform all parsing and validation.
If no `ValidationError` is raised, you know the resulting model instance is valid.

```py group="basic-model"
assert user.id == 123
assert isinstance(user.id, int)
# Note that '123' was coerced to an int and its value is 123
```

More details on pydantic's coercion logic can be found in [Data Conversion](#data-conversion).
Fields of a model can be accessed as normal attributes of the `user` object.
The string `'123'` has been converted into an int as per the field type.

```py group="basic-model"
assert user.name == 'Jane Doe'
```

`name` wasn't set when `user` was initialized, so it has the default value.

```py group="basic-model"
assert user.model_fields_set == {'id'}
```

The fields which were supplied when user was initialized.

```py group="basic-model"
assert user.model_dump() == {'id': 123, 'name': 'Jane Doe'}
```

Either `.model_dump()` or `dict(user)` will provide a dict of fields, but `.model_dump()` can take numerous other
arguments. (Note that `dict(user)` will not recursively convert nested models into dicts, but `.model_dump()` will.)

```py group="basic-model"
user.id = 321
assert user.id == 321
```

By default, models are mutable and field values can be changed through attribute assignment.

### Model methods and properties

The example above only shows the tip of the iceberg of what models can do.
Models possess the following methods and attributes:

* [`model_computed_fields`][pydantic.main.BaseModel.model_computed_fields]: a dictionary of the computed fields of this model instance.
* [`model_construct()`][pydantic.main.BaseModel.model_construct]: a class method for creating models without running validation. See
    [Creating models without validation](#creating-models-without-validation).
* [`model_copy()`][pydantic.main.BaseModel.model_copy]: returns a copy (by default, shallow copy) of the model. See
    [Serialization](serialization.md#modelcopy).
* [`model_dump()`][pydantic.main.BaseModel.model_dump]: returns a dictionary of the model's fields and values. See
    [Serialization](serialization.md#modeldump).
* [`model_dump_json()`][pydantic.main.BaseModel.model_dump_json]: returns a JSON string representation of [`model_dump()`][pydantic.main.BaseModel.model_dump]. See
    [Serialization](serialization.md#modeldumpjson).
* [`model_extra`][pydantic.main.BaseModel.model_extra]: get extra fields set during validation.
* [`model_fields_set`][pydantic.main.BaseModel.model_fields_set]: set of fields which were set when the model instance was initialized.
* [`model_json_schema()`][pydantic.main.BaseModel.model_json_schema]: returns a jsonable dictionary representing the model as JSON Schema. See [JSON Schema](json_schema.md).
* [`model_parametrized_name()`][pydantic.main.BaseModel.model_parametrized_name]: compute the class name for parametrizations of generic classes.
* [`model_post_init()`][pydantic.main.BaseModel.model_post_init]: perform additional initialization after the model is initialized.
* [`model_rebuild()`][pydantic.main.BaseModel.model_rebuild]: rebuild the model schema, which also supports building recursive generic models.
    See [Rebuild model schema](#rebuild-model-schema).
* [`model_validate()`][pydantic.main.BaseModel.model_validate]: a utility for loading any object into a model. See [Helper functions](#helper-functions).
* [`model_validate_json()`][pydantic.main.BaseModel.model_validate_json]: a utility for validating the given JSON data against the Pydantic model. See
    [Helper functions](#helper-functions).

!!! note
    See [`BaseModel`][pydantic.main.BaseModel] for the class definition including a full list of methods and attributes.

!!! tip
    See [Changes to `pydantic.BaseModel`](../migration.md#changes-to-pydanticbasemodel) in the
    [Migration Guide](../migration.md) for details on changes from Pydantic V1.

## Nested models

More complex hierarchical data structures can be defined using models themselves as types in annotations.

```py
from typing import List, Optional

from pydantic import BaseModel


class Foo(BaseModel):
    count: int
    size: Optional[float] = None


class Bar(BaseModel):
    apple: str = 'x'
    banana: str = 'y'


class Spam(BaseModel):
    foo: Foo
    bars: List[Bar]


m = Spam(foo={'count': 4}, bars=[{'apple': 'x1'}, {'apple': 'x2'}])
print(m)
"""
foo=Foo(count=4, size=None) bars=[Bar(apple='x1', banana='y'), Bar(apple='x2', banana='y')]
"""
print(m.model_dump())
"""
{
    'foo': {'count': 4, 'size': None},
    'bars': [{'apple': 'x1', 'banana': 'y'}, {'apple': 'x2', 'banana': 'y'}],
}
"""
```

For self-referencing models, see [postponed annotations](postponed_annotations.md#self-referencing-or-recursive-models).

## Rebuild model schema

The model schema can be rebuilt using [`model_rebuild()`][pydantic.main.BaseModel.model_rebuild]. This is useful for building recursive generic models.

```py
from pydantic import BaseModel, PydanticUserError


class Foo(BaseModel):
    x: 'Bar'


try:
    Foo.model_json_schema()
except PydanticUserError as e:
    print(e)
    """
    `Foo` is not fully defined; you should define `Bar`, then call `Foo.model_rebuild()`.

    For further information visit https://errors.pydantic.dev/2/u/class-not-fully-defined
    """


class Bar(BaseModel):
    pass


Foo.model_rebuild()
print(Foo.model_json_schema())
"""
{
    '$defs': {'Bar': {'properties': {}, 'title': 'Bar', 'type': 'object'}},
    'properties': {'x': {'$ref': '#/$defs/Bar'}},
    'required': ['x'],
    'title': 'Foo',
    'type': 'object',
}
"""
```

Pydantic tries to determine when this is necessary automatically and error if it wasn't done, but you may want to
call [`model_rebuild()`][pydantic.main.BaseModel.model_rebuild] proactively when dealing with recursive models or generics.

In V2, [`model_rebuild()`][pydantic.main.BaseModel.model_rebuild] replaced `update_forward_refs()` from V1. There are some slight differences with the new behavior.
The biggest change is that when calling [`model_rebuild()`][pydantic.main.BaseModel.model_rebuild] on the outermost model, it builds a core schema used for validation of the
whole model (nested models and all), so all types at all levels need to be ready before [`model_rebuild()`][pydantic.main.BaseModel.model_rebuild] is called.

## Arbitrary class instances

(Formerly known as "ORM Mode"/`from_orm`.)

Pydantic models can also be created from arbitrary class instances by reading the instance attributes corresponding
to the model field names. One common application of this functionality is integration with object-relational mappings
(ORMs).

To do this, set the config attribute `model_config['from_attributes'] = True`. See
[Model Config][pydantic.config.ConfigDict.from_attributes] and [ConfigDict][pydantic.config.ConfigDict] for more information.

The example here uses [SQLAlchemy](https://www.sqlalchemy.org/), but the same approach should work for any ORM.

```py
from typing import List

from sqlalchemy import Column, Integer, String
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import declarative_base
from typing_extensions import Annotated

from pydantic import BaseModel, ConfigDict, StringConstraints

Base = declarative_base()


class CompanyOrm(Base):
    __tablename__ = 'companies'

    id = Column(Integer, primary_key=True, nullable=False)
    public_key = Column(String(20), index=True, nullable=False, unique=True)
    name = Column(String(63), unique=True)
    domains = Column(ARRAY(String(255)))


class CompanyModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    public_key: Annotated[str, StringConstraints(max_length=20)]
    name: Annotated[str, StringConstraints(max_length=63)]
    domains: List[Annotated[str, StringConstraints(max_length=255)]]


co_orm = CompanyOrm(
    id=123,
    public_key='foobar',
    name='Testing',
    domains=['example.com', 'foobar.com'],
)
print(co_orm)
#> <__main__.CompanyOrm object at 0x0123456789ab>
co_model = CompanyModel.model_validate(co_orm)
print(co_model)
"""
id=123 public_key='foobar' name='Testing' domains=['example.com', 'foobar.com']
"""
```

### Reserved names

You may want to name a `Column` after a reserved SQLAlchemy field. In that case, `Field` aliases will be
convenient:

```py
import typing

import sqlalchemy as sa
from sqlalchemy.orm import declarative_base

from pydantic import BaseModel, ConfigDict, Field


class MyModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    metadata: typing.Dict[str, str] = Field(alias='metadata_')


Base = declarative_base()


class SQLModel(Base):
    __tablename__ = 'my_table'
    id = sa.Column('id', sa.Integer, primary_key=True)
    # 'metadata' is reserved by SQLAlchemy, hence the '_'
    metadata_ = sa.Column('metadata', sa.JSON)


sql_model = SQLModel(metadata_={'key': 'val'}, id=1)

pydantic_model = MyModel.model_validate(sql_model)

print(pydantic_model.model_dump())
#> {'metadata': {'key': 'val'}}
print(pydantic_model.model_dump(by_alias=True))
#> {'metadata_': {'key': 'val'}}
```

!!! note
    The example above works because aliases have priority over field names for
    field population. Accessing `SQLModel`'s `metadata` attribute would lead to a `ValidationError`.

### Nested attributes

When using attributes to parse models, model instances will be created from both top-level attributes and
deeper-nested attributes as appropriate.

Here is an example demonstrating the principle:

```py
from typing import List

from pydantic import BaseModel, ConfigDict


class PetCls:
    def __init__(self, *, name: str, species: str):
        self.name = name
        self.species = species


class PersonCls:
    def __init__(self, *, name: str, age: float = None, pets: List[PetCls]):
        self.name = name
        self.age = age
        self.pets = pets


class Pet(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str
    species: str


class Person(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str
    age: float = None
    pets: List[Pet]


bones = PetCls(name='Bones', species='dog')
orion = PetCls(name='Orion', species='cat')
anna = PersonCls(name='Anna', age=20, pets=[bones, orion])
anna_model = Person.model_validate(anna)
print(anna_model)
"""
name='Anna' age=20.0 pets=[Pet(name='Bones', species='dog'), Pet(name='Orion', species='cat')]
"""
```

## Error handling

Pydantic will raise `ValidationError` whenever it finds an error in the data it's validating.

A single exception of type `ValidationError` will be raised regardless of the number of errors found,
and that `ValidationError` will contain information about all of the errors and how they happened.

See [Error Handling](../errors/errors.md) for details on standard and custom errors.

As a demonstration:

```py
from typing import List

from pydantic import BaseModel, ValidationError


class Model(BaseModel):
    list_of_ints: List[int]
    a_float: float


data = dict(
    list_of_ints=['1', 2, 'bad'],
    a_float='not a float',
)

try:
    Model(**data)
except ValidationError as e:
    print(e)
    """
    2 validation errors for Model
    list_of_ints.2
      Input should be a valid integer, unable to parse string as an integer [type=int_parsing, input_value='bad', input_type=str]
    a_float
      Input should be a valid number, unable to parse string as a number [type=float_parsing, input_value='not a float', input_type=str]
    """
```

## Helper functions

*Pydantic* provides two `classmethod` helper functions on models for parsing data:

* [`model_validate()`][pydantic.main.BaseModel.model_validate]: this is very similar to the `__init__` method of the model, except it takes a dict or an object
  rather than keyword arguments. If the object passed cannot be validated, or if it's not a dictionary
  or instance of the model in question, a `ValidationError` will be raised.
* [`model_validate_json()`][pydantic.main.BaseModel.model_validate_json]: this takes a *str* or *bytes* and parses it as *json*, then passes the result to [`model_validate()`][pydantic.main.BaseModel.model_validate].

```py
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ValidationError


class User(BaseModel):
    id: int
    name: str = 'John Doe'
    signup_ts: Optional[datetime] = None


m = User.model_validate({'id': 123, 'name': 'James'})
print(m)
#> id=123 name='James' signup_ts=None

try:
    User.model_validate(['not', 'a', 'dict'])
except ValidationError as e:
    print(e)
    """
    1 validation error for User
      Input should be a valid dictionary or instance of User [type=model_type, input_value=['not', 'a', 'dict'], input_type=list]
    """

m = User.model_validate_json('{"id": 123, "name": "James"}')
print(m)
#> id=123 name='James' signup_ts=None

try:
    m = User.model_validate_json('{"id": 123, "name": 123}')
except ValidationError as e:
    print(e)
    """
    1 validation error for User
    name
      Input should be a valid string [type=string_type, input_value=123, input_type=int]
    """

try:
    m = User.model_validate_json('invalid JSON')
except ValidationError as e:
    print(e)
    """
    1 validation error for User
      Invalid JSON: expected value at line 1 column 1 [type=json_invalid, input_value='invalid JSON', input_type=str]
    """
```

If you want to validate serialized data in a format other than JSON, you should load the data into a dict yourself and
then pass it to [`model_validate`][pydantic.main.BaseModel.model_validate].

!!! note
    Depending on the types and model configs involved, [`model_validate`][pydantic.main.BaseModel.model_validate]
    and [`model_validate_json`][pydantic.main.BaseModel.model_validate_json] may have different validation behavior.
    If you have data coming from a non-JSON source, but want the same validation
    behavior and errors you'd get from [`model_validate_json`][pydantic.main.BaseModel.model_validate_json],
    our recommendation for now is to use `model_validate_json(json.dumps(data))`.

!!! note
    Learn more about JSON parsing in the [JSON](../concepts/json.md) section of the docs.

!!! note
    If you're passing in an instance of a model to [`model_validate`][pydantic.main.BaseModel.model_validate], you will want to consider setting
    [`revalidate_instances`](https://docs.pydantic.dev/latest/api/config/#pydantic.config.ConfigDict.revalidate_instances)
    in the model's config. If you don't set this value, then validation will be skipped on model instances. See the below example:


=== ":x: `revalidate_instances='never'`"
    ```py
    from pydantic import BaseModel


    class Model(BaseModel):
        a: int


    m = Model(a=0)
    # note: the `model_config` setting validate_assignment=True` can prevent this kind of misbehavior
    m.a = 'not an int'

    # doesn't raise a validation error even though m is invalid
    m2 = Model.model_validate(m)
    ```

=== ":white_check_mark: `revalidate_instances='always'`"
    ```py
    from pydantic import BaseModel, ConfigDict, ValidationError


    class Model(BaseModel):
        a: int

        model_config = ConfigDict(revalidate_instances='always')


    m = Model(a=0)
    # note: the `model_config` setting validate_assignment=True` can prevent this kind of misbehavior
    m.a = 'not an int'

    try:
        m2 = Model.model_validate(m)
    except ValidationError as e:
        print(e)
        """
        1 validation error for Model
        a
          Input should be a valid integer, unable to parse string as an integer [type=int_parsing, input_value='not an int', input_type=str]
        """
    ```

### Creating models without validation

Pydantic also provides the [`model_construct()`][pydantic.main.BaseModel.model_construct] method, which allows models to be created **without validation**. This
can be useful in at least a few cases:

* when working with complex data that is already known to be valid (for performance reasons)
* when one or more of the validator functions are non-idempotent, or
* when one or more of the validator functions have side effects that you don't want to be triggered.

!!! note
    In Pydantic V2, the performance gap between `BaseModel.__init__` and `BaseModel.model_construct` has been narrowed
    considerably. For simple models, calling `BaseModel.__init__` may even be faster. If you are using [`model_construct()`][pydantic.main.BaseModel.model_construct]
    for performance reasons, you may want to profile your use case before assuming that [`model_construct()`][pydantic.main.BaseModel.model_construct] is faster.

!!! warning
    [`model_construct()`][pydantic.main.BaseModel.model_construct] does not do any validation, meaning it can create models which are invalid. **You should only
    ever use the [`model_construct()`][pydantic.main.BaseModel.model_construct] method with data which has already been validated, or that you definitely trust.**

```py
from pydantic import BaseModel


class User(BaseModel):
    id: int
    age: int
    name: str = 'John Doe'


original_user = User(id=123, age=32)

user_data = original_user.model_dump()
print(user_data)
#> {'id': 123, 'age': 32, 'name': 'John Doe'}
fields_set = original_user.model_fields_set
print(fields_set)
#> {'age', 'id'}

# ...
# pass user_data and fields_set to RPC or save to the database etc.
# ...

# you can then create a new instance of User without
# re-running validation which would be unnecessary at this point:
new_user = User.model_construct(_fields_set=fields_set, **user_data)
print(repr(new_user))
#> User(id=123, age=32, name='John Doe')
print(new_user.model_fields_set)
#> {'age', 'id'}

# construct can be dangerous, only use it with validated data!:
bad_user = User.model_construct(id='dog')
print(repr(bad_user))
#> User(id='dog', name='John Doe')
```

The `_fields_set` keyword argument to [`model_construct()`][pydantic.main.BaseModel.model_construct] is optional, but allows you to be more precise about
which fields were originally set and which weren't. If it's omitted [`model_fields_set`][pydantic.main.BaseModel.model_fields_set] will just be the keys
of the data provided.

For example, in the example above, if `_fields_set` was not provided,
`new_user.model_fields_set` would be `{'id', 'age', 'name'}`.

Note that for subclasses of [`RootModel`](#rootmodel-and-custom-root-types), the root value can be passed to [`model_construct()`][pydantic.main.BaseModel.model_construct]
positionally, instead of using a keyword argument.

Here are some additional notes on the behavior of [`model_construct()`][pydantic.main.BaseModel.model_construct]:

* When we say "no validation is performed" — this includes converting dicts to model instances. So if you have a field
  with a `Model` type, you will need to convert the inner dict to a model yourself before passing it to
  [`model_construct()`][pydantic.main.BaseModel.model_construct].
  * In particular, the [`model_construct()`][pydantic.main.BaseModel.model_construct] method does not support recursively constructing models from dicts.
* If you do not pass keyword arguments for fields with defaults, the default values will still be used.
* For models with `model_config['extra'] == 'allow'`, data not corresponding to fields will be correctly stored in
  the `__pydantic_extra__` dict.
* For models with private attributes, the `__pydantic_private__` dict will be initialized the same as it would be when
  calling `__init__`.
* When constructing an instance using [`model_construct()`][pydantic.main.BaseModel.model_construct], no `__init__` method from the model or any of its parent
  classes will be called, even when a custom `__init__` method is defined.

## Generic models

Pydantic supports the creation of generic models to make it easier to reuse a common model structure.

In order to declare a generic model, you perform the following steps:

* Declare one or more `typing.TypeVar` instances to use to parameterize your model.
* Declare a pydantic model that inherits from `pydantic.BaseModel` and `typing.Generic`,
  where you pass the `TypeVar` instances as parameters to `typing.Generic`.
* Use the `TypeVar` instances as annotations where you will want to replace them with other types or
  pydantic models.

Here is an example using a generic `BaseModel` subclass to create an easily-reused HTTP response payload wrapper:

```py
from typing import Generic, List, Optional, TypeVar

from pydantic import BaseModel, ValidationError

DataT = TypeVar('DataT')


class DataModel(BaseModel):
    numbers: List[int]
    people: List[str]


class Response(BaseModel, Generic[DataT]):
    data: Optional[DataT] = None


data = DataModel(numbers=[1, 2, 3], people=[])

print(Response[int](data=1))
#> data=1
print(Response[str](data='value'))
#> data='value'
print(Response[str](data='value').model_dump())
#> {'data': 'value'}
print(Response[DataModel](data=data).model_dump())
#> {'data': {'numbers': [1, 2, 3], 'people': []}}
try:
    Response[int](data='value')
except ValidationError as e:
    print(e)
    """
    1 validation error for Response[int]
    data
      Input should be a valid integer, unable to parse string as an integer [type=int_parsing, input_value='value', input_type=str]
    """
```

If you set the `model_config` or make use of `@field_validator` or other Pydantic decorators in your generic model
definition, they will be applied to parametrized subclasses in the same way as when inheriting from a `BaseModel`
subclass. Any methods defined on your generic class will also be inherited.

Pydantic's generics also integrate properly with type checkers, so you get all the type checking
you would expect if you were to declare a distinct type for each parametrization.

!!! note
    Internally, Pydantic creates subclasses of `BaseModel` at runtime when generic models are parametrized.
    These classes are cached, so there should be minimal overhead introduced by the use of generics models.

To inherit from a generic model and preserve the fact that it is generic, the subclass must also inherit from
`typing.Generic`:

```py
from typing import Generic, TypeVar

from pydantic import BaseModel

TypeX = TypeVar('TypeX')


class BaseClass(BaseModel, Generic[TypeX]):
    X: TypeX


class ChildClass(BaseClass[TypeX], Generic[TypeX]):
    # Inherit from Generic[TypeX]
    pass


# Replace TypeX by int
print(ChildClass[int](X=1))
#> X=1
```

You can also create a generic subclass of a `BaseModel` that partially or fully replaces the type parameters in the
superclass:

```py
from typing import Generic, TypeVar

from pydantic import BaseModel

TypeX = TypeVar('TypeX')
TypeY = TypeVar('TypeY')
TypeZ = TypeVar('TypeZ')


class BaseClass(BaseModel, Generic[TypeX, TypeY]):
    x: TypeX
    y: TypeY


class ChildClass(BaseClass[int, TypeY], Generic[TypeY, TypeZ]):
    z: TypeZ


# Replace TypeY by str
print(ChildClass[str, int](x='1', y='y', z='3'))
#> x=1 y='y' z=3
```

If the name of the concrete subclasses is important, you can also override the default name generation:

```py
from typing import Any, Generic, Tuple, Type, TypeVar

from pydantic import BaseModel

DataT = TypeVar('DataT')


class Response(BaseModel, Generic[DataT]):
    data: DataT

    @classmethod
    def model_parametrized_name(cls, params: Tuple[Type[Any], ...]) -> str:
        return f'{params[0].__name__.title()}Response'


print(repr(Response[int](data=1)))
#> IntResponse(data=1)
print(repr(Response[str](data='a')))
#> StrResponse(data='a')
```

Using the same `TypeVar` in nested models allows you to enforce typing relationships at different points in your model:

```py
from typing import Generic, TypeVar

from pydantic import BaseModel, ValidationError

T = TypeVar('T')


class InnerT(BaseModel, Generic[T]):
    inner: T


class OuterT(BaseModel, Generic[T]):
    outer: T
    nested: InnerT[T]


nested = InnerT[int](inner=1)
print(OuterT[int](outer=1, nested=nested))
#> outer=1 nested=InnerT[int](inner=1)
try:
    nested = InnerT[str](inner='a')
    print(OuterT[int](outer='a', nested=nested))
except ValidationError as e:
    print(e)
    """
    2 validation errors for OuterT[int]
    outer
      Input should be a valid integer, unable to parse string as an integer [type=int_parsing, input_value='a', input_type=str]
    nested
      Input should be a valid dictionary or instance of InnerT[int] [type=model_type, input_value=InnerT[str](inner='a'), input_type=InnerT[str]]
    """
```

When using bound type parameters, and when leaving type parameters unspecified, Pydantic treats generic models
similarly to how it treats built-in generic types like `List` and `Dict`:

* If you don't specify parameters before instantiating the generic model, they are validated as the bound of the `TypeVar`.
* If the `TypeVar`s involved have no bounds, they are treated as `Any`.

Also, like `List` and `Dict`, any parameters specified using a `TypeVar` can later be substituted with concrete types:

```py requires="3.12"
from typing import Generic, TypeVar

from pydantic import BaseModel, ValidationError

AT = TypeVar('AT')
BT = TypeVar('BT')


class Model(BaseModel, Generic[AT, BT]):
    a: AT
    b: BT


print(Model(a='a', b='a'))
#> a='a' b='a'

IntT = TypeVar('IntT', bound=int)
typevar_model = Model[int, IntT]
print(typevar_model(a=1, b=1))
#> a=1 b=1
try:
    typevar_model(a='a', b='a')
except ValidationError as exc:
    print(exc)
    """
    2 validation errors for Model[int, TypeVar]
    a
      Input should be a valid integer, unable to parse string as an integer [type=int_parsing, input_value='a', input_type=str]
    b
      Input should be a valid integer, unable to parse string as an integer [type=int_parsing, input_value='a', input_type=str]
    """

concrete_model = typevar_model[int]
print(concrete_model(a=1, b=1))
#> a=1 b=1
```

!!! warning
    While it may not raise an error, we strongly advise against using parametrized generics in isinstance checks.

    For example, you should not do `isinstance(my_model, MyGenericModel[int])`. However, it is fine to do `isinstance(my_model, MyGenericModel)`. (Note that, for standard generics, it would raise an error to do a subclass check with a parameterized generic.)

    If you need to perform isinstance checks against parametrized generics, you can do this by subclassing the parametrized generic class. This looks like `class MyIntModel(MyGenericModel[int]): ...` and `isinstance(my_model, MyIntModel)`.

If a Pydantic model is used in a `TypeVar` bound and the generic type is never parametrized then Pydantic will use the bound for validation but treat the value as `Any` in terms of serialization:

```py
from typing import Generic, Optional, TypeVar

from pydantic import BaseModel


class ErrorDetails(BaseModel):
    foo: str


ErrorDataT = TypeVar('ErrorDataT', bound=ErrorDetails)


class Error(BaseModel, Generic[ErrorDataT]):
    message: str
    details: Optional[ErrorDataT]


class MyErrorDetails(ErrorDetails):
    bar: str


# serialized as Any
error = Error(
    message='We just had an error',
    details=MyErrorDetails(foo='var', bar='var2'),
)
assert error.model_dump() == {
    'message': 'We just had an error',
    'details': {
        'foo': 'var',
        'bar': 'var2',
    },
}

# serialized using the concrete parametrization
# note that `'bar': 'var2'` is missing
error = Error[ErrorDetails](
    message='We just had an error',
    details=ErrorDetails(foo='var'),
)
assert error.model_dump() == {
    'message': 'We just had an error',
    'details': {
        'foo': 'var',
    },
}
```

Here's another example of the above behavior, enumerating all permutations regarding bound specification and generic type parametrization:
```py
from typing import Generic

from typing_extensions import TypeVar

from pydantic import BaseModel

TBound = TypeVar('TBound', bound=BaseModel)
TNoBound = TypeVar('TNoBound')


class IntValue(BaseModel):
    value: int


class ItemBound(BaseModel, Generic[TBound]):
    item: TBound


class ItemNoBound(BaseModel, Generic[TNoBound]):
    item: TNoBound


item_bound_inferred = ItemBound(item=IntValue(value=3))
item_bound_explicit = ItemBound[IntValue](item=IntValue(value=3))
item_no_bound_inferred = ItemNoBound(item=IntValue(value=3))
item_no_bound_explicit = ItemNoBound[IntValue](item=IntValue(value=3))

# calling `print(x.model_dump())` on any of the above instances results in the following:
#> {'item': {'value': 3}}
```

If you use a `default=...` (available in Python >= 3.13 or via `typing-extensions`) or constraints (`TypeVar('T', str, int)`;
note that you rarely want to use this form of a `TypeVar`) then the default value or constraints will be used for both
validation and serialization if the type variable is not parametrized.
You can override this behavior using `pydantic.SerializeAsAny`:

```py
from typing import Generic, Optional

from typing_extensions import TypeVar

from pydantic import BaseModel, SerializeAsAny


class ErrorDetails(BaseModel):
    foo: str


ErrorDataT = TypeVar('ErrorDataT', default=ErrorDetails)


class Error(BaseModel, Generic[ErrorDataT]):
    message: str
    details: Optional[ErrorDataT]


class MyErrorDetails(ErrorDetails):
    bar: str


# serialized using the default's serializer
error = Error(
    message='We just had an error',
    details=MyErrorDetails(foo='var', bar='var2'),
)
assert error.model_dump() == {
    'message': 'We just had an error',
    'details': {
        'foo': 'var',
    },
}


class SerializeAsAnyError(BaseModel, Generic[ErrorDataT]):
    message: str
    details: Optional[SerializeAsAny[ErrorDataT]]


# serialized as Any
error = SerializeAsAnyError(
    message='We just had an error',
    details=MyErrorDetails(foo='var', bar='baz'),
)
assert error.model_dump() == {
    'message': 'We just had an error',
    'details': {
        'foo': 'var',
        'bar': 'baz',
    },
}
```

!!! note
    Note, you may run into a bit of trouble if you don't parametrize a generic when the case of validating against the generic's bound
    could cause data loss. See the example below:

```py
from typing import Generic

from typing_extensions import TypeVar

from pydantic import BaseModel

TItem = TypeVar('TItem', bound='ItemBase')


class ItemBase(BaseModel):
    ...


class IntItem(ItemBase):
    value: int


class ItemHolder(BaseModel, Generic[TItem]):
    item: TItem


loaded_data = {'item': {'value': 1}}


print(ItemHolder(**loaded_data).model_dump())  # (1)!
#> {'item': {}}

print(ItemHolder[IntItem](**loaded_data).model_dump())  # (2)!
#> {'item': {'value': 1}}
```

1. When the generic isn't parametrized, the input data is validated against the generic bound.
   Given that `ItemBase` has no fields, the `item` field information is lost.
2. In this case, the runtime type information is provided explicitly via the generic parametrization,
   so the input data is validated against the `IntItem` class and the serialization output matches what's expected.

## Dynamic model creation

There are some occasions where it is desirable to create a model using runtime information to specify the fields.
For this Pydantic provides the `create_model` function to allow models to be created on the fly:

```py
from pydantic import BaseModel, create_model

DynamicFoobarModel = create_model(
    'DynamicFoobarModel', foo=(str, ...), bar=(int, 123)
)


class StaticFoobarModel(BaseModel):
    foo: str
    bar: int = 123
```

Here `StaticFoobarModel` and `DynamicFoobarModel` are identical.

Fields are defined by a tuple of the form `(<type>, <default value>)`. The special keyword
arguments `__config__` and `__base__` can be used to customise the new model. This includes
extending a base model with extra fields.

```py
from pydantic import BaseModel, create_model


class FooModel(BaseModel):
    foo: str
    bar: int = 123


BarModel = create_model(
    'BarModel',
    apple=(str, 'russet'),
    banana=(str, 'yellow'),
    __base__=FooModel,
)
print(BarModel)
#> <class '__main__.BarModel'>
print(BarModel.model_fields.keys())
#> dict_keys(['foo', 'bar', 'apple', 'banana'])
```

You can also add validators by passing a dict to the `__validators__` argument.

```py rewrite_assert="false"
from pydantic import ValidationError, create_model, field_validator


def username_alphanumeric(cls, v):
    assert v.isalnum(), 'must be alphanumeric'
    return v


validators = {
    'username_validator': field_validator('username')(username_alphanumeric)
}

UserModel = create_model(
    'UserModel', username=(str, ...), __validators__=validators
)

user = UserModel(username='scolvin')
print(user)
#> username='scolvin'

try:
    UserModel(username='scolvi%n')
except ValidationError as e:
    print(e)
    """
    1 validation error for UserModel
    username
      Assertion failed, must be alphanumeric [type=assertion_error, input_value='scolvi%n', input_type=str]
    """
```

!!! note
    To pickle a dynamically created model:

    - the model must be defined globally
    - it must provide `__module__`

## `RootModel` and custom root types

??? api "API Documentation"
    [`pydantic.root_model.RootModel`][pydantic.root_model.RootModel]<br>

Pydantic models can be defined with a "custom root type" by subclassing [`pydantic.RootModel`][pydantic.RootModel].

The root type can be any type supported by Pydantic, and is specified by the generic parameter to `RootModel`.
The root value can be passed to the model `__init__` or [`model_validate`][pydantic.main.BaseModel.model_validate]
via the first and only argument.

Here's an example of how this works:

```py
from typing import Dict, List

from pydantic import RootModel

Pets = RootModel[List[str]]
PetsByName = RootModel[Dict[str, str]]


print(Pets(['dog', 'cat']))
#> root=['dog', 'cat']
print(Pets(['dog', 'cat']).model_dump_json())
#> ["dog","cat"]
print(Pets.model_validate(['dog', 'cat']))
#> root=['dog', 'cat']
print(Pets.model_json_schema())
"""
{'items': {'type': 'string'}, 'title': 'RootModel[List[str]]', 'type': 'array'}
"""

print(PetsByName({'Otis': 'dog', 'Milo': 'cat'}))
#> root={'Otis': 'dog', 'Milo': 'cat'}
print(PetsByName({'Otis': 'dog', 'Milo': 'cat'}).model_dump_json())
#> {"Otis":"dog","Milo":"cat"}
print(PetsByName.model_validate({'Otis': 'dog', 'Milo': 'cat'}))
#> root={'Otis': 'dog', 'Milo': 'cat'}
```

If you want to access items in the `root` field directly or to iterate over the items, you can implement
custom `__iter__` and `__getitem__` functions, as shown in the following example.

```py
from typing import List

from pydantic import RootModel


class Pets(RootModel):
    root: List[str]

    def __iter__(self):
        return iter(self.root)

    def __getitem__(self, item):
        return self.root[item]


pets = Pets.model_validate(['dog', 'cat'])
print(pets[0])
#> dog
print([pet for pet in pets])
#> ['dog', 'cat']
```

You can also create subclasses of the parametrized root model directly:

```py
from typing import List

from pydantic import RootModel


class Pets(RootModel[List[str]]):
    root: List[str]

    def describe(self) -> str:
        return f'Pets: {", ".join(self.root)}'


my_pets = Pets.model_validate(['dog', 'cat'])

print(my_pets.describe())
#> Pets: dog, cat
```


## Faux immutability

Models can be configured to be immutable via `model_config['frozen'] = True`. When this is set, attempting to change the
values of instance attributes will raise errors. See the [API reference][pydantic.config.ConfigDict.frozen] for more details.

!!! note
    This behavior was achieved in Pydantic V1 via the config setting `allow_mutation = False`.
    This config flag is deprecated in Pydantic V2, and has been replaced with `frozen`.

!!! warning
    In Python, immutability is not enforced. Developers have the ability to modify objects
    that are conventionally considered "immutable" if they choose to do so.

```py
from pydantic import BaseModel, ConfigDict, ValidationError


class FooBarModel(BaseModel):
    model_config = ConfigDict(frozen=True)

    a: str
    b: dict


foobar = FooBarModel(a='hello', b={'apple': 'pear'})

try:
    foobar.a = 'different'
except ValidationError as e:
    print(e)
    """
    1 validation error for FooBarModel
    a
      Instance is frozen [type=frozen_instance, input_value='different', input_type=str]
    """

print(foobar.a)
#> hello
print(foobar.b)
#> {'apple': 'pear'}
foobar.b['apple'] = 'grape'
print(foobar.b)
#> {'apple': 'grape'}
```

Trying to change `a` caused an error, and `a` remains unchanged. However, the dict `b` is mutable, and the
immutability of `foobar` doesn't stop `b` from being changed.

## Abstract base classes

Pydantic models can be used alongside Python's
[Abstract Base Classes](https://docs.python.org/3/library/abc.html) (ABCs).

```py
import abc

from pydantic import BaseModel


class FooBarModel(BaseModel, abc.ABC):
    a: str
    b: int

    @abc.abstractmethod
    def my_abstract_method(self):
        pass
```

## Field ordering

Field order affects models in the following ways:

* field order is preserved in the model [schema](json_schema.md)
* field order is preserved in [validation errors](#error-handling)
* field order is preserved by [`.model_dump()` and `.model_dump_json()` etc.](serialization.md#modelmodeldump)

```py
from pydantic import BaseModel, ValidationError


class Model(BaseModel):
    a: int
    b: int = 2
    c: int = 1
    d: int = 0
    e: float


print(Model.model_fields.keys())
#> dict_keys(['a', 'b', 'c', 'd', 'e'])
m = Model(e=2, a=1)
print(m.model_dump())
#> {'a': 1, 'b': 2, 'c': 1, 'd': 0, 'e': 2.0}
try:
    Model(a='x', b='x', c='x', d='x', e='x')
except ValidationError as err:
    error_locations = [e['loc'] for e in err.errors()]

print(error_locations)
#> [('a',), ('b',), ('c',), ('d',), ('e',)]
```

## Required fields

To declare a field as required, you may declare it using just an annotation, or you may use `Ellipsis`/`...`
as the value:

```py
from pydantic import BaseModel, Field


class Model(BaseModel):
    a: int
    b: int = ...
    c: int = Field(...)
```

Where `Field` refers to the [field function](json_schema.md#field-customization).

Here `a`, `b` and `c` are all required. However, this use of `b: int = ...` does not work properly
with [mypy](../integrations/mypy.md), and as of **v1.0** should be avoided in most cases.

!!! note
    In Pydantic V1, fields annotated with `Optional` or `Any` would be given an implicit default of `None` even if no
    default was explicitly specified. This behavior has changed in Pydantic V2, and there are no longer any type
    annotations that will result in a field having an implicit default value.

## Fields with non-hashable default values

A common source of bugs in python is to use a mutable object as a default value for a function or method argument,
as the same instance ends up being reused in each call.

The `dataclasses` module actually raises an error in this case, indicating that you should use the `default_factory`
argument to `dataclasses.field`.

Pydantic also supports the use of a [`default_factory`](#fields-with-dynamic-default-values) for non-hashable default
values, but it is not required. In the event that the default value is not hashable, Pydantic will deepcopy the default
value when creating each instance of the model:

```py
from typing import Dict, List

from pydantic import BaseModel


class Model(BaseModel):
    item_counts: List[Dict[str, int]] = [{}]


m1 = Model()
m1.item_counts[0]['a'] = 1
print(m1.item_counts)
#> [{'a': 1}]

m2 = Model()
print(m2.item_counts)
#> [{}]
```

## Fields with dynamic default values

When declaring a field with a default value, you may want it to be dynamic (i.e. different for each model).
To do this, you may want to use a `default_factory`.

Here is an example:

```py
from datetime import datetime, timezone
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


def datetime_now() -> datetime:
    return datetime.now(timezone.utc)


class Model(BaseModel):
    uid: UUID = Field(default_factory=uuid4)
    updated: datetime = Field(default_factory=datetime_now)


m1 = Model()
m2 = Model()
assert m1.uid != m2.uid
```

You can find more information in the documentation of the [`Field` function](fields.md).

## Automatically excluded attributes

### Class vars
Attributes annotated with `typing.ClassVar` are properly treated by Pydantic as class variables, and will not
become fields on model instances:

```py
from typing import ClassVar

from pydantic import BaseModel


class Model(BaseModel):
    x: int = 2
    y: ClassVar[int] = 1


m = Model()
print(m)
#> x=2
print(Model.y)
#> 1
```

### Private model attributes

Attributes whose name has a leading underscore are not treated as fields by Pydantic, and are not included in the
model schema. Instead, these are converted into a "private attribute" which is not validated or even set during
calls to `__init__`, `model_validate`, etc.

!!! note
    As of Pydantic v2.1.0, you will receive a NameError if trying to use the [`Field` function](fields.md) with a private attribute.
    Because private attributes are not treated as fields, the Field() function cannot be applied.

Here is an example of usage:

```py
from datetime import datetime
from random import randint

from pydantic import BaseModel, PrivateAttr


class TimeAwareModel(BaseModel):
    _processed_at: datetime = PrivateAttr(default_factory=datetime.now)
    _secret_value: str

    def __init__(self, **data):
        super().__init__(**data)
        # this could also be done with default_factory
        self._secret_value = randint(1, 5)


m = TimeAwareModel()
print(m._processed_at)
#> 2032-01-02 03:04:05.000006
print(m._secret_value)
#> 3
```

Private attribute names must start with underscore to prevent conflicts with model fields. However, dunder names
(such as `__attr__`) are not supported.

## Data conversion

Pydantic may cast input data to force it to conform to model field types,
and in some cases this may result in a loss of information.
For example:

```py
from pydantic import BaseModel


class Model(BaseModel):
    a: int
    b: float
    c: str


print(Model(a=3.000, b='2.72', c=b'binary data').model_dump())
#> {'a': 3, 'b': 2.72, 'c': 'binary data'}
```

This is a deliberate decision of Pydantic, and is frequently the most useful approach. See
[here](https://github.com/pydantic/pydantic/issues/578) for a longer discussion on the subject.

Nevertheless, [strict type checking](strict_mode.md) is also supported.

## Model signature

All Pydantic models will have their signature generated based on their fields:

```py
import inspect

from pydantic import BaseModel, Field


class FooModel(BaseModel):
    id: int
    name: str = None
    description: str = 'Foo'
    apple: int = Field(alias='pear')


print(inspect.signature(FooModel))
#> (*, id: int, name: str = None, description: str = 'Foo', pear: int) -> None
```

An accurate signature is useful for introspection purposes and libraries like `FastAPI` or `hypothesis`.

The generated signature will also respect custom `__init__` functions:

```py
import inspect

from pydantic import BaseModel


class MyModel(BaseModel):
    id: int
    info: str = 'Foo'

    def __init__(self, id: int = 1, *, bar: str, **data) -> None:
        """My custom init!"""
        super().__init__(id=id, bar=bar, **data)


print(inspect.signature(MyModel))
#> (id: int = 1, *, bar: str, info: str = 'Foo') -> None
```

To be included in the signature, a field's alias or name must be a valid Python identifier.
Pydantic will prioritize a field's alias over its name when generating the signature, but may use the field name if the
alias is not a valid Python identifier.

If a field's alias and name are _both_ not valid identifiers (which may be possible through exotic use of `create_model`),
a `**data` argument will be added. In addition, the `**data` argument will always be present in the signature if
`model_config['extra'] == 'allow'`.

## Structural pattern matching

Pydantic supports structural pattern matching for models, as introduced by [PEP 636](https://peps.python.org/pep-0636/) in Python 3.10.

```py requires="3.10" lint="skip"
from pydantic import BaseModel


class Pet(BaseModel):
    name: str
    species: str


a = Pet(name='Bones', species='dog')

match a:
    # match `species` to 'dog', declare and initialize `dog_name`
    case Pet(species='dog', name=dog_name):
        print(f'{dog_name} is a dog')
#> Bones is a dog
    # default case
    case _:
        print('No dog matched')
```

!!! note
    A match-case statement may seem as if it creates a new model, but don't be fooled;
    it is just syntactic sugar for getting an attribute and either comparing it or declaring and initializing it.

## Attribute copies

In many cases, arguments passed to the constructor will be copied in order to perform validation and, where necessary,
coercion.

In this example, note that the ID of the list changes after the class is constructed because it has been
copied during validation:

```py
from typing import List

from pydantic import BaseModel


class C1:
    arr = []

    def __init__(self, in_arr):
        self.arr = in_arr


class C2(BaseModel):
    arr: List[int]


arr_orig = [1, 9, 10, 3]


c1 = C1(arr_orig)
c2 = C2(arr=arr_orig)
print('id(c1.arr) == id(c2.arr):', id(c1.arr) == id(c2.arr))
#> id(c1.arr) == id(c2.arr): False
```

!!! note
    There are some situations where Pydantic does not copy attributes, such as when passing models &mdash; we use the
    model as is. You can override this behaviour by setting
    [`model_config['revalidate_instances'] = 'always'`](../api/config.md#pydantic.config.ConfigDict).

## Extra fields

By default, Pydantic models won't error when you provide data for unrecognized fields, they will just be ignored:

```py
from pydantic import BaseModel


class Model(BaseModel):
    x: int


m = Model(x=1, y='a')
assert m.model_dump() == {'x': 1}
```

If you want this to raise an error, you can achieve this via `model_config`:

```py
from pydantic import BaseModel, ConfigDict, ValidationError


class Model(BaseModel):
    x: int

    model_config = ConfigDict(extra='forbid')


try:
    Model(x=1, y='a')
except ValidationError as exc:
    print(exc)
    """
    1 validation error for Model
    y
      Extra inputs are not permitted [type=extra_forbidden, input_value='a', input_type=str]
    """
```

To instead preserve any extra data provided, you can set `extra='allow'`.
The extra fields will then be stored in `BaseModel.__pydantic_extra__`:

```py
from pydantic import BaseModel, ConfigDict


class Model(BaseModel):
    x: int

    model_config = ConfigDict(extra='allow')


m = Model(x=1, y='a')
assert m.__pydantic_extra__ == {'y': 'a'}
```

By default, no validation will be applied to these extra items, but you can set a type for the values by overriding
the type annotation for `__pydantic_extra__`:

```py
from typing import Dict

from pydantic import BaseModel, ConfigDict, ValidationError


class Model(BaseModel):
    __pydantic_extra__: Dict[str, int]

    x: int

    model_config = ConfigDict(extra='allow')


try:
    Model(x=1, y='a')
except ValidationError as exc:
    print(exc)
    """
    1 validation error for Model
    y
      Input should be a valid integer, unable to parse string as an integer [type=int_parsing, input_value='a', input_type=str]
    """

m = Model(x=1, y='2')
assert m.x == 1
assert m.y == 2
assert m.model_dump() == {'x': 1, 'y': 2}
assert m.__pydantic_extra__ == {'y': 2}
```

The same configurations apply to `TypedDict` and `dataclass`' except the config is controlled by setting the
`__pydantic_config__` attribute of the class to a valid `ConfigDict`.
