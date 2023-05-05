The primary means of defining objects in *pydantic* is via models
(models are simply classes which inherit from `BaseModel`).

You can think of models as similar to types in strictly typed languages, or as the requirements of a single endpoint
in an API.

Untrusted data can be passed to a model, and after parsing and validation *pydantic* guarantees that the fields
of the resultant model instance will conform to the field types defined on the model.

!!! note
    *pydantic* is primarily a parsing library, **not a validation library**.
    Validation is a means to an end: building a model which conforms to the types and constraints provided.

    In other words, *pydantic* guarantees the types and constraints of the output model, not the input data.

    This might sound like an esoteric distinction, but it is not. If you're unsure what this means or
    how it might affect your usage you should read the section about [Data Conversion](#data-conversion) below.

    Although validation is not the main purpose of *pydantic*, you **can** use this library for custom [validation](validators.md).

## Basic model usage

```py group="basic-model"
from pydantic import BaseModel


class User(BaseModel):
    id: int
    name: str = 'Jane Doe'
```

`User` here is a model with two fields `id` which is an integer and is required,
and `name` which is a string and is not required (it has a default value). The type of `name` is inferred from the
default value, and so a type annotation is not required (however note [this](#field-ordering) warning about field
order when some fields do not have type annotations).

```py group="basic-model"
user = User(id='123')
```

`user` here is an instance of `User`. Initialisation of the object will perform all parsing and validation,
if no `ValidationError` is raised, you know the resulting model instance is valid.

```py group="basic-model"
assert user.id == 123
assert isinstance(user.id, int)
# Note that 123.45 was cast to an int and its value is 123
```

More details on the casting in the case of `user_x` can be found in [Data Conversion](#data-conversion).
Fields of a model can be accessed as normal attributes of the user object.
The string '123' has been cast to an int as per the field type

```py group="basic-model"
assert user.name == 'Jane Doe'
```

`name` wasn't set when user was initialised, so it has the default value

```py group="basic-model"
assert user.model_fields_set == {'id'}
```

The fields which were supplied when user was initialised.

```py group="basic-model"
assert user.model_dump() == {'id': 123, 'name': 'Jane Doe'}
```

Either `.model_dump()` or `dict(user)` will provide a dict of fields, but `.model_dump()` can take numerous other arguments.

```py group="basic-model"
user.id = 321
assert user.id == 321
```

This model is mutable so field values can be changed.

### Model properties

The example above only shows the tip of the iceberg of what models can do.
Models possess the following methods and attributes:

`model_dump()`
: returns a dictionary of the model's fields and values;
  cf. [exporting models](exporting_models.md#modeldict)

`model_dump_json()`
: returns a JSON string representation `model_dump()`;
  cf. [exporting models](exporting_models.md#modeljson)

`copy()`
: returns a copy (by default, shallow copy) of the model; cf. [exporting models](exporting_models.md#modelcopy)

`model_validate()`
: a utility for loading any object into a model with error handling if the object is not a dictionary;
  cf. [helper functions](#helper-functions)

`parse_raw()`
: a utility for loading strings of numerous formats; cf. [helper functions](#helper-functions)

`parse_file()`
: like `parse_raw()` but for file paths; cf. [helper functions](#helper-functions)

`from_orm()`
: loads data into a model from an arbitrary class; cf. [ORM mode](#orm-mode-aka-arbitrary-class-instances)

`model_json_schema()`
: returns a dictionary representing the model as JSON Schema; cf. [schema](schema.md)

`schema_json()`
: returns a JSON string representation of `schema()`; cf. [schema](schema.md)

`model_construct()`
: a class method for creating models without running validation;
  cf. [Creating models without validation](#creating-models-without-validation)

`model_fields_set`
: Set of names of fields which were set when the model instance was initialised

`model_fields`
: a dictionary of the model's fields

`__config__`
: the configuration class for the model, cf. [model config](model_config.md)

## Recursive Models

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

For self-referencing models, see [postponed annotations](postponed_annotations.md#self-referencing-models).

## "From Attributes" (aka ORM Mode/Arbitrary Class Instances)

Pydantic models can be created from arbitrary class instances to support models that map to ORM objects.

To do this:

1. The [Config](model_config.md) property `from_attributes` must be set to `True`.
2. The special constructor `from_orm` must be used to create the model instance.

The example here uses SQLAlchemy, but the same approach should work for any ORM.

```py
from typing import List

from sqlalchemy import Column, Integer, String
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.ext.declarative import declarative_base

from pydantic import BaseModel, constr

Base = declarative_base()


class CompanyOrm(Base):
    __tablename__ = 'companies'
    id = Column(Integer, primary_key=True, nullable=False)
    public_key = Column(String(20), index=True, nullable=False, unique=True)
    name = Column(String(63), unique=True)
    domains = Column(ARRAY(String(255)))


class CompanyModel(BaseModel):
    model_config = dict(from_attributes=True)
    id: int
    public_key: constr(max_length=20)
    name: constr(max_length=63)
    domains: List[constr(max_length=255)]


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
#> id=123 public_key='foobar' name='Testing' domains=['example.com', 'foobar.com']
```

### Reserved names

You may want to name a Column after a reserved SQLAlchemy field. In that case, Field aliases will be
convenient:

```py
import typing

import sqlalchemy as sa
from sqlalchemy.ext.declarative import declarative_base

from pydantic import BaseModel, Field


class MyModel(BaseModel):
    model_config = dict(from_attributes=True)
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

### Recursive ORM models

ORM instances will be parsed with `from_orm` recursively as well as at the top level.

Here a vanilla class is used to demonstrate the principle, but any ORM class could be used instead.

```py
from typing import List

from pydantic import BaseModel


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
    model_config = dict(from_attributes=True)
    name: str
    species: str


class Person(BaseModel):
    model_config = dict(from_attributes=True)
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


### Data binding

Arbitrary classes are processed by *pydantic* using the `GetterDict` class (see
[utils.py](https://github.com/pydantic/pydantic/blob/main/pydantic/utils.py)), which attempts to
provide a dictionary-like interface to any class. You can customise how this works by setting your own
sub-class of `GetterDict` as the value of `Config.getter_dict` (see [config](model_config.md)).

You can also customise class validation using [root_validators](validators.md#root-validators) with `pre=True`.
In this case your validator function will be passed a `GetterDict` instance which you may copy and modify.

The `GetterDict` instance will be called for each field with a sentinel as a fallback (if no other default
value is set). Returning this sentinel means that the field is missing. Any other value will
be interpreted as the value of the field.

```py
from collections.abc import Mapping
from typing import Optional
from xml.etree.ElementTree import fromstring

from pydantic import BaseModel, Field

xmlstring = """
<User Id="2138">
    <FirstName>John</FirstName>
    <LastName>Foobar</LastName>
</User>
"""


class XmlMapping(Mapping):
    def __init__(self, xmlstring):
        self._xml = fromstring(xmlstring)

    def __getitem__(self, key):
        if key in {'Id', 'Status'}:
            return self._xml.attrib.get(key)
        else:
            return self._xml.find(key).text

    def __len__(self):
        return len(self._xml.attrib) + len(self._xml)

    def __iter__(self):
        ...


class User(BaseModel):
    id: int = Field(alias='Id')
    first_name: Optional[str] = Field(None, alias='FirstName')
    last_name: Optional[str] = Field(None, alias='LastName')


print(User.model_validate(XmlMapping(xmlstring)))
#> id=2138 first_name='John' last_name='Foobar'
```


## Error Handling

*pydantic* will raise `ValidationError` whenever it finds an error in the data it's validating.

!!! note
    Validation code should not raise `ValidationError` itself, but rather raise `ValueError`, `TypeError` or
    `AssertionError` (or subclasses of `ValueError` or `TypeError`) which will be caught and used to populate
    `ValidationError`.

One exception will be raised regardless of the number of errors found, that `ValidationError` will
contain information about all the errors and how they happened.

You can access these errors in several ways:

`e.errors()`
: method will return list of errors found in the input data.

`e.json()`
: method will return a JSON representation of `errors`.

`str(e)`
: method will return a human readable representation of the errors.

Each error object contains:

`loc`
: the error's location as a list. The first item in the list will be the field where the error occurred,
  and if the field is a [sub-model](models.md#recursive-models), subsequent items will be present to indicate
  the nested location of the error.

`type`
: a computer-readable identifier of the error type.

`msg`
: a human readable explanation of the error.

`ctx`
: an optional object which contains values required to render the error message.

As a demonstration:

```py
from typing import List

from pydantic import BaseModel, ValidationError, conint


class Location(BaseModel):
    lat: float = 0.1
    lng: float = 10.1


class Model(BaseModel):
    is_required: float
    gt_int: conint(gt=42)
    list_of_ints: List[int] = None
    a_float: float = None
    recursive_model: Location = None


data = dict(
    list_of_ints=['1', 2, 'bad'],
    a_float='not a float',
    recursive_model={'lat': 4.2, 'lng': 'New York'},
    gt_int=21,
)

try:
    Model(**data)
except ValidationError as e:
    print(e)
    """
    5 validation errors for Model
    is_required
      Field required [type=missing, input_value={'list_of_ints': ['1', 2,...ew York'}, 'gt_int': 21}, input_type=dict]
    gt_int
      Input should be greater than 42 [type=greater_than, input_value=21, input_type=int]
    list_of_ints.2
      Input should be a valid integer, unable to parse string as an integer [type=int_parsing, input_value='bad', input_type=str]
    a_float
      Input should be a valid number, unable to parse string as an number [type=float_parsing, input_value='not a float', input_type=str]
    recursive_model.lng
      Input should be a valid number, unable to parse string as an number [type=float_parsing, input_value='New York', input_type=str]
    """

try:
    Model(**data)
except ValidationError as e:
    # print(e.json())
    # TODO set back to .json() once we add it
    print(e.errors())
    """
    [
        {
            'type': 'missing',
            'loc': ('is_required',),
            'msg': 'Field required',
            'input': {
                'list_of_ints': ['1', 2, 'bad'],
                'a_float': 'not a float',
                'recursive_model': {'lat': 4.2, 'lng': 'New York'},
                'gt_int': 21,
            },
            'url': 'https://errors.pydantic.dev/2/v/missing',
        },
        {
            'type': 'greater_than',
            'loc': ('gt_int',),
            'msg': 'Input should be greater than 42',
            'input': 21,
            'ctx': {'gt': 42},
            'url': 'https://errors.pydantic.dev/2/v/greater_than',
        },
        {
            'type': 'int_parsing',
            'loc': ('list_of_ints', 2),
            'msg': 'Input should be a valid integer, unable to parse string as an integer',
            'input': 'bad',
            'url': 'https://errors.pydantic.dev/2/v/int_parsing',
        },
        {
            'type': 'float_parsing',
            'loc': ('a_float',),
            'msg': 'Input should be a valid number, unable to parse string as an number',
            'input': 'not a float',
            'url': 'https://errors.pydantic.dev/2/v/float_parsing',
        },
        {
            'type': 'float_parsing',
            'loc': ('recursive_model', 'lng'),
            'msg': 'Input should be a valid number, unable to parse string as an number',
            'input': 'New York',
            'url': 'https://errors.pydantic.dev/2/v/float_parsing',
        },
    ]
    """
```

### Custom Errors

In your custom data types or validators you should use `ValueError`, `TypeError` or `AssertionError` to raise errors.

See [validators](validators.md) for more details on use of the `@validator` decorator.

```py
from pydantic import BaseModel, ValidationError, field_validator


class Model(BaseModel):
    foo: str

    @field_validator('foo')
    def value_must_equal_bar(cls, v):
        if v != 'bar':
            raise ValueError('value must be "bar"')

        return v


try:
    Model(foo='ber')
except ValidationError as e:
    print(e.errors())
    """
    [
        {
            'type': 'value_error',
            'loc': ('foo',),
            'msg': 'Value error, value must be "bar"',
            'input': 'ber',
            'ctx': {'error': 'value must be "bar"'},
            'url': 'https://errors.pydantic.dev/2/v/value_error',
        }
    ]
    """
```

You can also define your own error classes, which can specify a custom error code, message template, and context:

```py
from pydantic_core import PydanticCustomError

from pydantic import BaseModel, ValidationError, field_validator


class Model(BaseModel):
    foo: str

    @field_validator('foo')
    def value_must_equal_bar(cls, v):
        if v != 'bar':
            raise PydanticCustomError(
                'not_a_bar',
                'value is not "bar", got "{wrong_value}"',
                dict(wrong_value=v),
            )
        return v


try:
    Model(foo='ber')
except ValidationError as e:
    print(e.errors())
    """
    [
        {
            'type': 'not_a_bar',
            'loc': ('foo',),
            'msg': 'value is not "bar", got "ber"',
            'input': 'ber',
            'ctx': {'wrong_value': 'ber'},
        }
    ]
    """
```

## Helper Functions

*Pydantic* provides three `classmethod` helper functions on models for parsing data:

* **`model_validate`**: this is very similar to the `__init__` method of the model, except it takes a dict
  rather than keyword arguments. If the object passed is not a dict a `ValidationError` will be raised.
* **`model_validate_json`**: this takes a *str* or *bytes* and parses it as *json*, then passes the result to `model_validate`.
  Parsing *pickle* data is also supported by setting the `content_type` argument appropriately.

```py
from datetime import datetime

from pydantic import BaseModel, ValidationError


class User(BaseModel):
    id: int
    name: str = 'John Doe'
    signup_ts: datetime = None


m = User.model_validate({'id': 123, 'name': 'James'})
print(m)
#> id=123 name='James' signup_ts=None

try:
    User.model_validate(['not', 'a', 'dict'])
except ValidationError as e:
    print(e)
    """
    1 validation error for User
      Input should be a valid dictionary [type=dict_type, input_value=['not', 'a', 'dict'], input_type=list]
    """

# assumes json as no content type passed
m = User.model_validate_json('{"id": 123, "name": "James"}')
print(m)
#> id=123 name='James' signup_ts=None
```

!!! warning
    To quote the [official `pickle` docs](https://docs.python.org/3/library/pickle.html),
    "The pickle module is not secure against erroneous or maliciously constructed data.
    Never unpickle data received from an untrusted or unauthenticated source."

!!! info
    Because it can result in arbitrary code execution, as a security measure, you need
    to explicitly pass `allow_pickle` to the parsing function in order to load `pickle` data.

### Creating models without validation

*pydantic* also provides the `model_construct()` method which allows models to be created **without validation** this
can be useful when data has already been validated or comes from a trusted source and you want to create a model
as efficiently as possible (`model_construct()` is generally around 30x faster than creating a model with full validation).

!!! warning
    `model_construct()` does not do any validation, meaning it can create models which are invalid. **You should only
    ever use the `model_construct()` method with data which has already been validated, or you trust.**

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

The `_fields_set` keyword argument to `model_construct()` is optional, but allows you to be more precise about
which fields were originally set and which weren't. If it's omitted `model_fields_set` will just be the keys
of the data provided.

For example, in the example above, if `_fields_set` was not provided,
`new_user.model_fields_set` would be `{'id', 'age', 'name'}`.

## Generic Models

Pydantic supports the creation of generic models to make it easier to reuse a common model structure.

In order to declare a generic model, you perform the following steps:

* Declare one or more `typing.TypeVar` instances to use to parameterize your model.
* Declare a pydantic model that inherits from `pydantic.generics.GenericModel` and `typing.Generic`,
  where you pass the `TypeVar` instances as parameters to `typing.Generic`.
* Use the `TypeVar` instances as annotations where you will want to replace them with other types or
  pydantic models.

Here is an example using `GenericModel` to create an easily-reused HTTP response payload wrapper:

```py
from typing import Generic, List, Optional, TypeVar

from pydantic import BaseModel, ValidationError

DataT = TypeVar('DataT')


class Error(BaseModel):
    code: int
    message: str


class DataModel(BaseModel):
    numbers: List[int]
    people: List[str]


class Response(BaseModel, Generic[DataT]):
    data: Optional[DataT] = None


data = DataModel(numbers=[1, 2, 3], people=[])
error = Error(code=404, message='Not found')

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

If you set `Config` or make use of `validator` in your generic model definition, it is applied
to concrete subclasses in the same way as when inheriting from `BaseModel`. Any methods defined on
your generic class will also be inherited.

Pydantic's generics also integrate properly with mypy, so you get all the type checking
you would expect mypy to provide if you were to declare the type without using `GenericModel`.

!!! note
    Internally, pydantic uses `create_model` to generate a (cached) concrete `BaseModel` at runtime,
    so there is essentially zero overhead introduced by making use of `GenericModel`.

To inherit from a GenericModel without replacing the `TypeVar` instance, a class must also inherit from
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

You can also create a generic subclass of a `GenericModel` that partially or fully replaces the type
parameters in the superclass.

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

If the name of the concrete subclasses is important, you can also override the default behavior:

```py
from typing import Any, Generic, Tuple, Type, TypeVar

from pydantic import BaseModel

DataT = TypeVar('DataT')


class Response(BaseModel, Generic[DataT]):
    data: DataT

    @classmethod
    def __concrete_name__(cls: Type[Any], params: Tuple[Type[Any], ...]) -> str:
        return f'{params[0].__name__.title()}Response'


print(repr(Response[int](data=1)))
#> Response[int](data=1)
print(repr(Response[str](data='a')))
#> Response[str](data='a')
```

Using the same TypeVar in nested models allows you to enforce typing relationships at different points in your model:

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
      Input should be a valid dictionary [type=dict_type, input_value=InnerT[str](inner='a'), input_type=InnerT[str]]
    """
```

Pydantic also treats `GenericModel` similarly to how it treats built-in generic types like `List` and `Dict` when it
comes to leaving them unparameterized, or using bounded `TypeVar` instances:

* If you don't specify parameters before instantiating the generic model, they will be treated as `Any`
* You can parametrize models with one or more *bounded* parameters to add subclass checks

Also, like `List` and `Dict`, any parameters specified using a `TypeVar` can later be substituted with concrete types.

```py
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
    2 validation errors for Model[int, ~IntT]
    a
      Input should be a valid integer, unable to parse string as an integer [type=int_parsing, input_value='a', input_type=str]
    b
      Input should be a valid integer, unable to parse string as an integer [type=int_parsing, input_value='a', input_type=str]
    """

concrete_model = typevar_model[int]
print(concrete_model(a=1, b=1))
#> a=1 b=1
```

## Dynamic model creation

There are some occasions where the shape of a model is not known until runtime. For this *pydantic* provides
the `create_model` method to allow models to be created on the fly.

```py
from pydantic import BaseModel, create_model

DynamicFoobarModel = create_model('DynamicFoobarModel', foo=(str, ...), bar=(int, 123))


class StaticFoobarModel(BaseModel):
    foo: str
    bar: int = 123
```

Here `StaticFoobarModel` and `DynamicFoobarModel` are identical.

!!! warning
    See the note in [Required Optional Fields](#required-optional-fields) for the distinction between an ellipsis as a
    field default and annotation-only fields.
    See [pydantic/pydantic#1047](https://github.com/pydantic/pydantic/issues/1047) for more details.

Fields are defined by either a tuple of the form `(<type>, <default value>)` or just a default value. The
special key word arguments `__config__` and `__base__` can be used to customise the new model. This includes
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
#> <class 'pydantic.main.BarModel'>
print(BarModel.model_fields.keys())
#> dict_keys(['foo', 'bar', 'apple', 'banana'])
```

You can also add validators by passing a dict to the `__validators__` argument.

```py rewrite_assert="false"
from pydantic import ValidationError, create_model, field_validator


def username_alphanumeric(cls, v):
    assert v.isalnum(), 'must be alphanumeric'
    return v


validators = {'username_validator': field_validator('username')(username_alphanumeric)}

UserModel = create_model('UserModel', username=(str, ...), __validators__=validators)

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

## Using Pydantic without creating a BaseModel

You may have types that are not `BaseModel`s that you want to validate data against.
Or you may want to validate a `List[SomeModel]`, or dump it to JSON.

To do this Pydantic provides `TypeAdapter`. A `TypeAdapter` instance behaves nearly the same as a `BaseModel` instance, with the difference that `TypeAdapter` is not an actual type so you cannot use it in type annotations and such.

```py
from typing import List

from typing_extensions import TypedDict

from pydantic import TypeAdapter, ValidationError


class User(TypedDict):
    name: str
    id: int


UserListValidator = TypeAdapter(List[User])
print(repr(UserListValidator.validate_python([{'name': 'Fred', 'id': '3'}])))
#> [{'name': 'Fred', 'id': 3}]

try:
    UserListValidator.validate_python([{'name': 'Fred', 'id': 'wrong', 'other': 'no'}])
except ValidationError as e:
    print(e)
    """
    2 validation errors for list[typed-dict]
    0.id
      Input should be a valid integer, unable to parse string as an integer [type=int_parsing, input_value='wrong', input_type=str]
    0.other
      Extra inputs are not permitted [type=extra_forbidden, input_value='no', input_type=str]
    """
```

For many use cases `TypeAdapter` can replace BaseModels with a `__root__` field in Pydantic V1.

## Custom Root Types

Pydantic models can be defined with a custom root type by declaring the `__root__` field.

The root type can be any type supported by pydantic, and is specified by the type hint on the `__root__` field.
The root value can be passed to the model `__init__` via the `__root__` keyword argument, or as
the first and only argument to `model_validate`.

```py test="xfail support/replace __root__"
import json
from typing import List

from pydantic import BaseModel
from pydantic.json_schema import models_json_schema


class Pets(BaseModel):
    __root__: List[str]


print(Pets(__root__=['dog', 'cat']))
print(Pets(__root__=['dog', 'cat']).model_dump_json())
print(Pets.model_validate(['dog', 'cat']))
print(Pets.model_json_schema())
pets_schema = models_json_schema([Pets])
print(json.dumps(pets_schema, indent=2))
```

If you call the `model_validate` method for a model with a custom root type with a *dict* as the first argument,
the following logic is used:

* If the custom root type is a mapping type (eg., `Dict` or `Mapping`),
  the argument itself is always validated against the custom root type.
* For other custom root types, if the dict has precisely one key with the value `__root__`,
  the corresponding value will be validated against the custom root type.
* Otherwise, the dict itself is validated against the custom root type.

This is demonstrated in the following example:

```py test="xfail support/replace __root__"
from typing import Dict, List

from pydantic import BaseModel, ValidationError


class Pets(BaseModel):
    __root__: List[str]


print(Pets.model_validate(['dog', 'cat']))
print(Pets.model_validate({'__root__': ['dog', 'cat']}))  # not recommended


class PetsByName(BaseModel):
    __root__: Dict[str, str]


print(PetsByName.model_validate({'Otis': 'dog', 'Milo': 'cat'}))
try:
    PetsByName.model_validate({'__root__': {'Otis': 'dog', 'Milo': 'cat'}})
except ValidationError as e:
    print(e)
```

!!! warning
    Calling the `model_validate` method on a dict with the single key `"__root__"` for non-mapping custom root types
    is currently supported for backwards compatibility, but is not recommended and may be dropped in a future version.

If you want to access items in the `__root__` field directly or to iterate over the items, you can implement custom `__iter__` and `__getitem__` functions, as shown in the following example.

```py test="xfail support/replace __root__"
from typing import List

from pydantic import BaseModel


class Pets(BaseModel):
    __root__: List[str]

    def __iter__(self):
        return iter(self.__root__)

    def __getitem__(self, item):
        return self.__root__[item]


pets = Pets.model_validate(['dog', 'cat'])
print(pets[0])
print([pet for pet in pets])
```

## Faux Immutability

Models can be configured to be immutable via `allow_mutation = False`. When this is set, attempting to change the
values of instance attributes will raise errors. See [model config](model_config.md) for more details on `Config`.

!!! warning
    Immutability in Python is never strict. If developers are determined/stupid they can always
    modify a so-called "immutable" object.

```py
from pydantic import BaseModel


class FooBarModel(BaseModel):
    model_config = dict(frozen=True)
    a: str
    b: dict


foobar = FooBarModel(a='hello', b={'apple': 'pear'})

try:
    foobar.a = 'different'
except TypeError as e:
    print(e)
    #> "FooBarModel" is frozen and does not support item assignment

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

## Abstract Base Classes

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

## Field Ordering

Field order is important in models for the following reasons:

* validation is performed in the order fields are defined; [fields validators](validators.md)
  can access the values of earlier fields, but not later ones
* field order is preserved in the model [schema](schema.md)
* field order is preserved in [validation errors](#error-handling)
* field order is preserved by [`.model_dump()` and `.model_dump_json()` etc.](exporting_models.md#modeldict)

As of **v1.0** all fields with annotations (whether annotation-only or with a default value) will precede
all fields without an annotation. Within their respective groups, fields remain in the order they were defined.

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

!!! warning
    As demonstrated by the example above, combining the use of annotated and non-annotated fields
    in the same model can result in surprising field orderings. (This is due to limitations of Python)

    Therefore, **we recommend adding type annotations to all fields**, even when a default value
    would determine the type by itself to guarantee field order is preserved.

## Required fields

To declare a field as required, you may declare it using just an annotation, or you may use an ellipsis (`...`)
as the value:

```py
from pydantic import BaseModel, Field


class Model(BaseModel):
    a: int
    b: int = ...
    c: int = Field(...)
```

Where `Field` refers to the [field function](schema.md#field-customization).

Here `a`, `b` and `c` are all required. However, use of the ellipses in `b` will not work well
with [mypy](/mypy_plugin/), and as of **v1.0** should be avoided in most cases.

### Required Optional fields

!!! warning
    Since version **v1.2** annotation only nullable (`Optional[...]`, `Union[None, ...]` and `Any`) fields and nullable
    fields with an ellipsis (`...`) as the default value, no longer mean the same thing.

    In some situations this may cause **v1.2** to not be entirely backwards compatible with earlier **v1.*** releases.

If you want to specify a field that can take a `None` value while still being required,
you can use `Optional` with `...`:

```py
from typing import Optional

from pydantic import BaseModel, ValidationError


class Model(BaseModel):
    a: Optional[int]
    b: Optional[int] = None


print(Model(a=1))
#> a=1 b=None
try:
    Model(b=2)
except ValidationError as e:
    print(e)
    """
    1 validation error for Model
    a
      Field required [type=missing, input_value={'b': 2}, input_type=dict]
    """
```

In this model, `a`, `b`, and `c` can take `None` as a value. But `a` is optional, while `b` and `c` are required.
`b` and `c` require a value, even if the value is `None`.

## Field with dynamic default value

When declaring a field with a default value, you may want it to be dynamic (i.e. different for each model).
To do this, you may want to use a `default_factory`.

!!! info "In Beta"
    The `default_factory` argument is in **beta**, it has been added to *pydantic* in **v1.5** on a
    **provisional basis**. It may change significantly in future releases and its signature or behaviour will not
    be concrete until **v2**. Feedback from the community while it's still provisional would be extremely useful;
    either comment on [#866](https://github.com/pydantic/pydantic/issues/866) or create a new issue.

Example of usage:

```py
from datetime import datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class Model(BaseModel):
    uid: UUID = Field(default_factory=uuid4)
    updated: datetime = Field(default_factory=datetime.utcnow)


m1 = Model()
m2 = Model()
assert m1.uid != m2.uid
assert m1.updated != m2.updated
```

Where `Field` refers to the [field function](schema.md#field-customization).

!!! warning
    The `default_factory` expects the field type to be set.

## Automatically excluded attributes

Class variables which begin with an underscore and attributes annotated with `typing.ClassVar` will be
automatically excluded from the model.

## Private model attributes

If you need to vary or manipulate internal attributes on instances of the model, you can declare them
using `PrivateAttr`:

```py
from datetime import datetime
from random import randint

from pydantic import BaseModel, PrivateAttr


class TimeAwareModel(BaseModel):
    _processed_at: datetime = PrivateAttr(default_factory=datetime.now)
    _secret_value: str = PrivateAttr()

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

Private attribute names must start with underscore to prevent conflicts with model fields: both `_attr` and `__attr__`
are supported.

If `Config.underscore_attrs_are_private` is `True`, any non-ClassVar underscore attribute will be treated as private:
```py test="xfail what the hell is underscore_attrs_are_private?"
from typing import ClassVar

from pydantic import BaseModel


class Model(BaseModel):
    _class_var: ClassVar[str] = 'class var value'
    _private_attr: str = 'private attr value'

    class Config:
        underscore_attrs_are_private = True


print(Model._class_var)
print(Model._private_attr)
print(Model()._private_attr)
```

Upon class creation pydantic constructs `__slots__` filled with private attributes.

## Parsing data into a specified type

Pydantic includes a standalone utility function `parse_obj_as` that can be used to apply the parsing
logic used to populate pydantic models in a more ad-hoc way. This function behaves similarly to
`BaseModel.model_validate`, but works with arbitrary pydantic-compatible types.

This is especially useful when you want to parse results into a type that is not a direct subclass of `BaseModel`.
For example:

```py
from typing import List

from pydantic import BaseModel, parse_obj_as


class Item(BaseModel):
    id: int
    name: str


# `item_data` could come from an API call, eg., via something like:
# item_data = requests.get('https://my-api.com/items').json()
item_data = [{'id': 1, 'name': 'My Item'}]

items = parse_obj_as(List[Item], item_data)
print(items)
#> [Item(id=1, name='My Item')]
```

This function is capable of parsing data into any of the types pydantic can handle as fields of a `BaseModel`.

Pydantic also includes two similar standalone functions called `parse_file_as` and `parse_raw_as`,
which are analogous to `BaseModel.parse_file` and `BaseModel.parse_raw`.

## Data Conversion

*pydantic* may cast input data to force it to conform to model field types,
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

This is a deliberate decision of *pydantic*, and in general it's the most useful approach. See
[here](https://github.com/pydantic/pydantic/issues/578) for a longer discussion on the subject.

Nevertheless, [strict type checking](types/types.md#strict-types) is partially supported.

## Model signature

All *pydantic* models will have their signature generated based on their fields:

```py
import inspect

from pydantic import BaseModel, Field


class FooModel(BaseModel):
    id: int
    name: str = None
    description: str = 'Foo'
    apple: int = Field(..., alias='pear')


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
*pydantic* prefers aliases over names, but may use field names if the alias is not a valid Python identifier.

If a field's alias and name are both invalid identifiers, a `**data` argument will be added.
In addition, the `**data` argument will always be present in the signature if `Config.extra` is `Extra.allow`.

!!! note
    Types in the model signature are the same as declared in model annotations,
    not necessarily all the types that can actually be provided to that field.
    This may be fixed one day once [#1055](https://github.com/pydantic/pydantic/issues/1055) is solved.

## Structural pattern matching

*pydantic* supports structural pattern matching for models, as introduced by [PEP 636](https://peps.python.org/pep-0636/) in Python 3.10.

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

In many cases arguments passed to the constructor will be copied in order to perform validation and, where necessary, coercion. When constructing classes with data attributes, Pydantic copies the attributes in order to efficiently iterate over its elements for validation.

In this example, note that the ID of the list changes after the class is constructed because it has been copied for validation.

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
print('id(c1.arr) == id(c2.arr)  ', id(c1.arr) == id(c2.arr))
#> id(c1.arr) == id(c2.arr)   False
```

!!! note
    There are some situations where Pydantic does not copy attributes, such as when passing models &mdash; we use the model as is. You can override this behaviour by setting [`config.revalidate_instances='always'`](/api/config/) in your model.
