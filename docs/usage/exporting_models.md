As well as accessing model attributes directly via their names (e.g. `model.foobar`), models can be converted
and exported in a number of ways:

## `model.model_dump(...)`

This is the primary way of converting a model to a dictionary. Sub-models will be recursively converted to dictionaries.

See [arguments](../api/main.md#pydantic.main.BaseModel.model_dump) for more information.

Example:

```py
from typing import Any, List, Optional

from pydantic import BaseModel, Field, Json


class BarModel(BaseModel):
    whatever: int


class FooBarModel(BaseModel):
    banana: Optional[float] = 1.1
    foo: str = Field(serialization_alias='foo_alias')
    bar: BarModel


m = FooBarModel(banana=3.14, foo='hello', bar={'whatever': 123})

# returns a dictionary:
print(m.model_dump())
#> {'banana': 3.14, 'foo': 'hello', 'bar': {'whatever': 123}}
print(m.model_dump(include={'foo', 'bar'}))
#> {'foo': 'hello', 'bar': {'whatever': 123}}
print(m.model_dump(exclude={'foo', 'bar'}))
#> {'banana': 3.14}
print(m.model_dump(by_alias=True))
#> {'banana': 3.14, 'foo_alias': 'hello', 'bar': {'whatever': 123}}
print(FooBarModel(foo='hello', bar={'whatever': 123}).model_dump(exclude_unset=True))
#> {'foo': 'hello', 'bar': {'whatever': 123}}
print(
    FooBarModel(banana=1.1, foo='hello', bar={'whatever': 123}).model_dump(
        exclude_defaults=True
    )
)
#> {'foo': 'hello', 'bar': {'whatever': 123}}
print(FooBarModel(foo='hello', bar={'whatever': 123}).model_dump(exclude_defaults=True))
#> {'foo': 'hello', 'bar': {'whatever': 123}}
print(
    FooBarModel(banana=None, foo='hello', bar={'whatever': 123}).model_dump(
        exclude_none=True
    )
)
#> {'foo': 'hello', 'bar': {'whatever': 123}}


class Model(BaseModel):
    x: List[Json[Any]]


print(Model(x=['{"a": 1}', '[1, 2]']).model_dump())
#> {'x': [{'a': 1}, [1, 2]]}
print(Model(x=['{"a": 1}', '[1, 2]']).model_dump(round_trip=True))
#> {'x': ['{"a":1}', '[1,2]']}
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

## `model_copy(...)`

`model_copy()` allows models to be duplicated, which is particularly useful for immutable models.
See [arguments](../api/main.md#pydantic.main.BaseModel.model_copy) for more information.

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

The `.model_dump_json()` method will serialise a model to JSON. (For `RootModel` [custom root type](models.md#custom-root-types),
only the values are serialised)

See [arguments](../api/main.md#pydantic.main.BaseModel.model_dump_json) for more information.

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
print(m.model_dump_json(indent=2))
"""
{
  "foo": "2032-06-01T12:13:14",
  "bar": {
    "whatever": 123
  }
}
"""
```

### Custom serializer

Serialisation can be customised on a field and model using `field_serializer` and `model_serializer` decorators. (see the example below):

```py
from datetime import datetime, timedelta, timezone
from typing import Any, Dict

from pydantic import BaseModel, ConfigDict, field_serializer, model_serializer


class WithCustomEncoders(BaseModel):
    model_config = ConfigDict(ser_json_timedelta='iso8601')

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


class Model(BaseModel):
    x: str

    @model_serializer
    def ser_model(self) -> Dict[str, Any]:
        return {'x': f'srialized {self.x}'}


print(Model(x='test value').model_dump_json())
#> {"x":"srialized test value"}
```
!!! note
    Serialisation can be customised in Pydantic V1 using the `json_encoders` config property.

### Serialising self-reference or other models

By default, models are serialised as dictionaries.
If you want to serialise them differently, you can use `model_serializer` decorator.

```py
from typing import List

from pydantic import BaseModel, field_serializer, model_serializer


class Address(BaseModel):
    city: str
    country: str

    @model_serializer
    def ser_model(self) -> str:
        return f'{self.city} ({self.country})'


class User(BaseModel):
    name: str
    address: Address
    friends: List['User'] = []

    @field_serializer('friends')
    def ser_friends(v: List['User']) -> List[str]:
        return [
            f'{friend.name} in {friend.address.city} ({friend.address.country[:2].upper()})'
            for friend in v
        ]


wolfgang = User(
    name='Wolfgang',
    address=Address(city='Berlin', country='Deutschland'),
    friends=[
        User(name='Pierre', address=Address(city='Paris', country='France')),
        User(name='John', address=Address(city='London', country='UK')),
    ],
)
print(wolfgang.model_dump_json())
"""
{"name":"Wolfgang","address":"Berlin (Deutschland)","friends":["Pierre in Paris (FR)","John in London (UK)"]}
"""
```

### Serialising subclasses

Subclasses of common types are automatically encoded like their super-classes:

```py
from datetime import date, timedelta
from typing import Any, Type

from pydantic_core import core_schema

from pydantic import BaseModel, GetCoreSchemaHandler


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

Using the same plumbing as `model_copy()`, *pydantic* models support efficient pickling and unpickling.

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

The `model_dump` and `model_dump_json` methods support `include` and `exclude` arguments which can either be
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
`model_dump` and related methods expect integer keys for element-wise inclusion or exclusion. To exclude a field from **every**
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
    'hobbies': [
        {'name': 'Programming', 'info': 'Writing code and stuff'},
        {'name': 'Gaming'},
    ],
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

The same holds for the `model_dump_json` method.

### Model and field level include and exclude

In addition to the explicit arguments `exclude` and `include` passed to `model_dump` and `model_dump_json` methods,
we can also pass the `include`/`exclude` arguments directly to the `Field` constructor:

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

Setting explicitly `exclude`/`include` on `model_dump` and `model_dump_json` has priority to
`exclude`/`include` in field constructor (i.e. `Field(..., exclude=True)`):

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
