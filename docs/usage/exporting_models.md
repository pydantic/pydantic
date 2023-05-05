As well as accessing model attributes directly via their names (e.g. `model.foobar`), models can be converted
and exported in a number of ways:

## `model.model_dump(...)`

This is the primary way of converting a model to a dictionary. Sub-models will be recursively converted to dictionaries.

Arguments:

* `include`: fields to include in the returned dictionary; see [below](#advanced-include-and-exclude)
* `exclude`: fields to exclude from the returned dictionary; see [below](#advanced-include-and-exclude)
* `by_alias`: whether field aliases should be used as keys in the returned dictionary; default `False`
* `exclude_unset`: whether fields which were not explicitly set when creating the model should
  be excluded from the returned dictionary; default `False`.
  Prior to **v1.0**, `exclude_unset` was known as `skip_defaults`; use of `skip_defaults` is now deprecated
* `exclude_defaults`: whether fields which are equal to their default values (whether set or otherwise) should
  be excluded from the returned dictionary; default `False`
* `exclude_none`: whether fields which are equal to `None` should be excluded from the returned dictionary; default
  `False`

Example:

```py
from pydantic import BaseModel


class BarModel(BaseModel):
    whatever: int


class FooBarModel(BaseModel):
    banana: float
    foo: str
    bar: BarModel


m = FooBarModel(banana=3.14, foo='hello', bar={'whatever': 123})

# returns a dictionary:
print(m.model_dump())
#> {'banana': 3.14, 'foo': 'hello', 'bar': {'whatever': 123}}
print(m.model_dump(include={'foo', 'bar'}))
#> {'foo': 'hello', 'bar': {'whatever': 123}}
print(m.model_dump(exclude={'foo', 'bar'}))
#> {'banana': 3.14}
```

## `dict(model)` and iteration

*pydantic* models can also be converted to dictionaries using `dict(model)`, and you can also
iterate over a model's field using `for field_name, value in model:`. With this approach the raw field values are
returned, so sub-models will not be converted to dictionaries.

Example:

```py
from pydantic import BaseModel


class BarModel(BaseModel):
    whatever: int


class FooBarModel(BaseModel):
    banana: float
    foo: str
    bar: BarModel


m = FooBarModel(banana=3.14, foo='hello', bar={'whatever': 123})

print(dict(m))
#> {'banana': 3.14, 'foo': 'hello', 'bar': BarModel(whatever=123)}
for name, value in m:
    print(f'{name}: {value}')
    #> banana: 3.14
    #> foo: hello
    #> bar: whatever=123
```

## `model.copy(...)`

`copy()` allows models to be duplicated, which is particularly useful for immutable models.

Arguments:

* `include`: fields to include in the returned dictionary; see [below](#advanced-include-and-exclude)
* `exclude`: fields to exclude from the returned dictionary; see [below](#advanced-include-and-exclude)
* `update`: a dictionary of values to change when creating the copied model
* `deep`: whether to make a deep copy of the new model; default `False`

Example:

```py
from pydantic import BaseModel


class BarModel(BaseModel):
    whatever: int


class FooBarModel(BaseModel):
    banana: float
    foo: str
    bar: BarModel


m = FooBarModel(banana=3.14, foo='hello', bar={'whatever': 123})

# TODO!
# print(m.model_copy(include={'foo', 'bar'}))
# print(m.model_copy(exclude={'foo', 'bar'}))
print(m.model_copy(update={'banana': 0}))
#> banana=0 foo='hello' bar=BarModel(whatever=123)
print(id(m.bar) == id(m.model_copy().bar))
#> True
# normal copy gives the same object reference for bar
print(id(m.bar) == id(m.model_copy(deep=True).bar))
#> False
# deep copy gives a new object reference for `bar`
```

## `model.model_dump_json(...)`

The `.model_dump_json()` method will serialise a model to JSON. (For models with a [custom root type](models.md#custom-root-types),
only the value for the `__root__` key is serialised)

Arguments:

* `include`: fields to include in the returned dictionary; see [below](#advanced-include-and-exclude)
* `exclude`: fields to exclude from the returned dictionary; see [below](#advanced-include-and-exclude)
* `by_alias`: whether field aliases should be used as keys in the returned dictionary; default `False`
* `exclude_unset`: whether fields which were not set when creating the model and have their default values should
  be excluded from the returned dictionary; default `False`.
  Prior to **v1.0**, `exclude_unset` was known as `skip_defaults`; use of `skip_defaults` is now deprecated
* `exclude_defaults`: whether fields which are equal to their default values (whether set or otherwise) should
  be excluded from the returned dictionary; default `False`
* `exclude_none`: whether fields which are equal to `None` should be excluded from the returned dictionary; default
  `False`
* `encoder`: a custom encoder function passed to the `default` argument of `json.dumps()`; defaults to a custom
  encoder designed to take care of all common types
* `**dumps_kwargs`: any other keyword arguments are passed to `json.dumps()`, e.g. `indent`.

*pydantic* can serialise many commonly used types to JSON (e.g. `datetime`, `date` or `UUID`) which would normally
fail with a simple `json.dumps(foobar)`.

```py
from datetime import datetime

from pydantic import BaseModel


class BarModel(BaseModel):
    whatever: int


class FooBarModel(BaseModel):
    foo: datetime
    bar: BarModel


m = FooBarModel(foo=datetime(2032, 6, 1, 12, 13, 14), bar={'whatever': 123})
print(m.model_dump_json())
#> {"foo":"2032-06-01T12:13:14","bar":{"whatever":123}}
```

### `json_encoders`

Serialisation can be customised on a model using the `json_encoders` config property; the keys should be types (or names of types for forward references), and
the values should be functions which serialise that type (see the example below):

```py
from datetime import datetime, timedelta, timezone

from pydantic import BaseModel, field_serializer


class WithCustomEncoders(BaseModel):
    model_config = dict(ser_json_timedelta='iso8601')
    dt: datetime
    diff: timedelta

    @field_serializer('dt')
    def serialize_dt(self, dt: datetime, _info):
        return dt.timestamp()


m = WithCustomEncoders(
    dt=datetime(2032, 6, 1, tzinfo=timezone.utc), diff=timedelta(hours=100)
)
print(m.model_dump_json())
#> {"dt":1969660800.0,"diff":"P4DT14400S"}
```

By default, `timedelta` is encoded as a simple float of total seconds. The `timedelta_isoformat` is provided
as an optional alternative which implements [ISO 8601](https://en.wikipedia.org/wiki/ISO_8601) time diff encoding.

### Serialising self-reference or other models

By default, models are serialised as dictionaries.
If you want to serialise them differently, you can add `models_as_dict=False` when calling `json()` method
and add the classes of the model in `json_encoders`.
In case of forward references, you can use a string with the class name instead of the class itself

```py test="skip"
# TODO we need to serializers for this example
from typing import List, Optional

from pydantic import BaseModel


class Address(BaseModel):
    city: str
    country: str


class User(BaseModel):
    name: str
    address: Address
    friends: Optional[List['User']] = None

    class Config:
        json_encoders = {
            Address: lambda a: f'{a.city} ({a.country})',
            'User': lambda u: f'{u.name} in {u.address.city} '
            f'({u.address.country[:2].upper()})',
        }


User.update_forward_refs()

wolfgang = User(
    name='Wolfgang',
    address=Address(city='Berlin', country='Deutschland'),
    friends=[
        User(name='Pierre', address=Address(city='Paris', country='France')),
        User(name='John', address=Address(city='London', country='UK')),
    ],
)
print(wolfgang.model_dump_json(models_as_dict=False))
```

### Serialising subclasses

!!! note
    New in version **v1.5**.

    Subclasses of common types were not automatically serialised to JSON before **v1.5**.

Subclasses of common types are automatically encoded like their super-classes:

```py
from datetime import date, timedelta
from typing import Any, Type

from pydantic_core import core_schema

from pydantic import BaseModel
from pydantic.annotated import GetCoreSchemaHandler


class DayThisYear(date):
    """
    Contrived example of a special type of date that
    takes an int and interprets it as a day in the current year
    """

    @classmethod
    def __get_pydantic_core_schema__(
        cls, source: Type[Any], handler: GetCoreSchemaHandler
    ) -> core_schema.CoreSchema:
        return core_schema.general_after_validator_function(
            cls.validate,
            core_schema.int_schema(),
            serialization=core_schema.format_ser_schema('%Y-%m-%d'),
        )

    @classmethod
    def validate(cls, v: int, _info):
        return date.today().replace(month=1, day=1) + timedelta(days=v)


class FooModel(BaseModel):
    date: DayThisYear


m = FooModel(date=300)
print(m.model_dump_json())
#> {"date":"2023-10-28"}
```

## `pickle.dumps(model)`

Using the same plumbing as `copy()`, *pydantic* models support efficient pickling and unpickling.

```py test="skip"
# TODO need to get pickling to work
import pickle

from pydantic import BaseModel


class FooBarModel(BaseModel):
    a: str
    b: int


m = FooBarModel(a='hello', b=123)
print(m)
data = pickle.dumps(m)
print(data)
m2 = pickle.loads(data)
print(m2)
```

## Advanced include and exclude

The `dict`, `json`, and `copy` methods support `include` and `exclude` arguments which can either be
sets or dictionaries. This allows nested selection of which fields to export:

```py
from pydantic import BaseModel, SecretStr


class User(BaseModel):
    id: int
    username: str
    password: SecretStr


class Transaction(BaseModel):
    id: str
    user: User
    value: int


t = Transaction(
    id='1234567890',
    user=User(id=42, username='JohnDoe', password='hashedpassword'),
    value=9876543210,
)

# using a set:
print(t.model_dump(exclude={'user', 'value'}))
#> {'id': '1234567890'}

# using a dict:
print(t.model_dump(exclude={'user': {'username', 'password'}, 'value': True}))
#> {'id': '1234567890', 'user': {'id': 42}}

print(t.model_dump(include={'id': True, 'user': {'id'}}))
#> {'id': '1234567890', 'user': {'id': 42}}
```

The `True` indicates that we want to exclude or include an entire key, just as if we included it in a set.
Of course, the same can be done at any depth level.

Special care must be taken when including or excluding fields from a list or tuple of submodels or dictionaries.  In this scenario,
`dict` and related methods expect integer keys for element-wise inclusion or exclusion. To exclude a field from **every**
member of a list or tuple, the dictionary key `'__all__'` can be used as follows:

```py
import datetime
from typing import List

from pydantic import BaseModel, SecretStr


class Country(BaseModel):
    name: str
    phone_code: int


class Address(BaseModel):
    post_code: int
    country: Country


class CardDetails(BaseModel):
    number: SecretStr
    expires: datetime.date


class Hobby(BaseModel):
    name: str
    info: str


class User(BaseModel):
    first_name: str
    second_name: str
    address: Address
    card_details: CardDetails
    hobbies: List[Hobby]


user = User(
    first_name='John',
    second_name='Doe',
    address=Address(post_code=123456, country=Country(name='USA', phone_code=1)),
    card_details=CardDetails(
        number='4212934504460000', expires=datetime.date(2020, 5, 1)
    ),
    hobbies=[
        Hobby(name='Programming', info='Writing code and stuff'),
        Hobby(name='Gaming', info='Hell Yeah!!!'),
    ],
)

exclude_keys = {
    'second_name': True,
    'address': {'post_code': True, 'country': {'phone_code'}},
    'card_details': True,
    # You can exclude fields from specific members of a tuple/list by index:
    'hobbies': {-1: {'info'}},
}

include_keys = {
    'first_name': True,
    'address': {'country': {'name'}},
    'hobbies': {0: True, -1: {'name'}},
}

# would be the same as user.model_dump(exclude=exclude_keys) in this case:
print(user.model_dump(include=include_keys))
"""
{
    'first_name': 'John',
    'address': {'country': {'name': 'USA'}},
    'hobbies': [{'name': 'Programming', 'info': 'Writing code and stuff'}],
}
"""

# To exclude a field from all members of a nested list or tuple, use "__all__":
print(user.model_dump(exclude={'hobbies': {'__all__': {'info'}}}))
"""
{
    'first_name': 'John',
    'second_name': 'Doe',
    'address': {'post_code': 123456, 'country': {'name': 'USA', 'phone_code': 1}},
    'card_details': {
        'number': SecretStr('**********'),
        'expires': datetime.date(2020, 5, 1),
    },
    'hobbies': [{'name': 'Programming'}, {'name': 'Gaming'}],
}
"""
```

The same holds for the `json` and `copy` methods.

### Model and field level include and exclude

In addition to the explicit arguments `exclude` and `include` passed to `dict`, `json` and `copy` methods, we can also pass the `include`/`exclude` arguments directly to the `Field` constructor or the equivalent `field` entry in the models `Config` class:

```py
from pydantic import BaseModel, Field, SecretStr


class User(BaseModel):
    id: int
    username: str
    password: SecretStr = Field(..., exclude=True)


class Transaction(BaseModel):
    id: str
    user: User = Field(exclude={'username'})
    value: int = Field(exclude=True)


t = Transaction(
    id='1234567890',
    user=User(id=42, username='JohnDoe', password='hashedpassword'),
    value=9876543210,
)

print(t.model_dump())
#> {'id': '1234567890'}
# TODO this is wrong! not all of "user" should be excluded
```

In the case where multiple strategies are used, `exclude`/`include` fields are merged according to the following rules:

* First, model config level settings (via `"fields"` entry) are merged per field with the field constructor settings (i.e. `Field(..., exclude=True)`), with the field constructor taking priority.
* The resulting settings are merged per class with the explicit settings on `dict`, `json`, `copy` calls with the explicit settings taking priority.

Note that while merging settings, `exclude` entries are merged by computing the "union" of keys, while `include` entries are merged by computing the "intersection" of keys.

The resulting merged exclude settings:

```py
from pydantic import BaseModel, Field, SecretStr


class User(BaseModel):
    id: int
    username: str  # overridden by explicit exclude
    password: SecretStr = Field(exclude=True)


class Transaction(BaseModel):
    id: str
    user: User
    value: int


t = Transaction(
    id='1234567890',
    user=User(id=42, username='JohnDoe', password='hashedpassword'),
    value=9876543210,
)

print(t.model_dump(exclude={'value': True, 'user': {'username'}}))
#> {'id': '1234567890', 'user': {'id': 42}}
```

are the same as using merged include settings as follows:

```py
from pydantic import BaseModel, Field, SecretStr


class User(BaseModel):
    id: int = Field(..., include=True)
    username: str = Field(..., include=True)  # overridden by explicit include
    password: SecretStr


class Transaction(BaseModel):
    id: str
    user: User
    value: int


t = Transaction(
    id='1234567890',
    user=User(id=42, username='JohnDoe', password='hashedpassword'),
    value=9876543210,
)

print(t.model_dump(include={'id': True, 'user': {'id'}}))
#> {'id': '1234567890', 'user': {'id': 42}}
```
