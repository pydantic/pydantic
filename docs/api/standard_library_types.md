---
description: Support for common types from the Python standard library.
---

Pydantic supports many common types from the Python standard library. If you need stricter processing see
[Strict Types](../usage/types/strict_types.md), including if you need to constrain the values allowed (e.g. to require a positive `int`).

## Booleans

A standard `bool` field will raise a `ValidationError` if the value is not one of the following:

* A valid boolean (i.e. `True` or `False`),
* The integers `0` or `1`,
* a `str` which when converted to lower case is one of
  `'0', 'off', 'f', 'false', 'n', 'no', '1', 'on', 't', 'true', 'y', 'yes'`
* a `bytes` which is valid per the previous rule when decoded to `str`

!!! note
    If you want stricter boolean logic (e.g. a field which only permits `True` and `False`) you can
    use [`StrictBool`](../api/types.md#pydantic.types.StrictBool).

Here is a script demonstrating some of these behaviors:

```py
from pydantic import BaseModel, ValidationError


class BooleanModel(BaseModel):
    bool_value: bool


print(BooleanModel(bool_value=False))
#> bool_value=False
print(BooleanModel(bool_value='False'))
#> bool_value=False
print(BooleanModel(bool_value=1))
#> bool_value=True
try:
    BooleanModel(bool_value=[])
except ValidationError as e:
    print(str(e))
    """
    1 validation error for BooleanModel
    bool_value
      Input should be a valid boolean [type=bool_type, input_value=[], input_type=list]
    """
```

## Datetime Types

Pydantic supports the following [datetime](https://docs.python.org/library/datetime.html#available-types)
types:

### `datetime.datetime`
* `datetime` fields will accept values of type:

    * `datetime`; an existing `datetime` object
    * `int` or `float`; assumed as Unix time, i.e. seconds (if >= `-2e10` and <= `2e10`) or milliseconds
      (if < `-2e10`or > `2e10`) since 1 January 1970
    * `str`; the following formats are accepted:
        * `YYYY-MM-DD[T]HH:MM[:SS[.ffffff]][Z or [±]HH[:]MM]`
        * `int` or `float` as a string (assumed as Unix time)

```py
from datetime import datetime

from pydantic import BaseModel


class Event(BaseModel):
    dt: datetime = None


event = Event(dt='2032-04-23T10:20:30.400+02:30')

print(event.model_dump())
"""
{'dt': datetime.datetime(2032, 4, 23, 10, 20, 30, 400000, tzinfo=TzInfo(+02:30))}
"""
```

### `datetime.date`
* `date` fields will accept values of type:

    * `date`; an existing `date` object
    * `int` or `float`; handled the same as described for `datetime` above
    * `str`; the following formats are accepted:
        * `YYYY-MM-DD`
        * `int` or `float` as a string (assumed as Unix time)

```py
from datetime import date

from pydantic import BaseModel


class Birthday(BaseModel):
    d: date = None


my_birthday = Birthday(d=1679616000.0)

print(my_birthday.model_dump())
#> {'d': datetime.date(2023, 3, 24)}
```

### `datetime.time`
* `time` fields will accept values of type:

    * `time`; an existing `time` object
    * `str`; the following formats are accepted:
        * `HH:MM[:SS[.ffffff]][Z or [±]HH[:]MM]`

```py
from datetime import time

from pydantic import BaseModel


class Meeting(BaseModel):
    t: time = None


m = Meeting(t=time(4, 8, 16))

print(m.model_dump())
#> {'t': datetime.time(4, 8, 16)}
```

### `datetime.timedelta`
* `timedelta` fields will accept values of type:

    * `timedelta`; an existing `timedelta` object
    * `int` or `float`; assumed to be seconds
    * `str`; the following formats are accepted:
        * `[-][DD ][HH:MM]SS[.ffffff]`
        * `[±]P[DD]DT[HH]H[MM]M[SS]S` ([ISO 8601](https://en.wikipedia.org/wiki/ISO_8601) format for timedelta)

```py
from datetime import timedelta

from pydantic import BaseModel


class Model(BaseModel):
    td: timedelta = None


m = Model(td='P3DT12H30M5S')

print(m.model_dump())
#> {'td': datetime.timedelta(days=3, seconds=45005)}
```

## Number Types

Pydantic supports the following numeric types from the Python standard library:

### `int`

* Pydantic uses `int(v)` to coerce types to an `int`;
  see [Data conversion](../usage/models.md#data-conversion) for details on loss of information during data conversion.

### `float`

* Pydantic uses `float(v)` to coerce values to floats.

### `enum.IntEnum`

* Validation: Pydantic checks that the value is a valid `IntEnum` instance.

#### subclass of `enum.IntEnum`

* Validation: checks that the value is a valid member of the integer enum;
  see [Enums and Choices](#enum) for more details.

### `decimal.Decimal`

* Validation: Pydantic attempts to convert the value to a string, then passes the string to `Decimal(v)`.
* Serialization: Pydantic serializes `Decimal` types as strings.
You can use a custom serializer to override this behavior if desired. For example:

```py
from decimal import Decimal

from typing_extensions import Annotated

from pydantic import BaseModel, PlainSerializer


class Model(BaseModel):
    x: Decimal
    y: Annotated[
        Decimal,
        PlainSerializer(
            lambda x: float(x), return_type=float, when_used='json'
        ),
    ]


my_model = Model(x=Decimal('1.1'), y=Decimal('2.1'))

print(my_model.model_dump())  # (1)!
#> {'x': Decimal('1.1'), 'y': Decimal('2.1')}
print(my_model.model_dump(mode='json'))  # (2)!
#> {'x': '1.1', 'y': 2.1}
print(my_model.model_dump_json())  # (3)!
#> {"x":"1.1","y":2.1}
```

1. Using [`model_dump`][pydantic.main.BaseModel.model_dump], both `x` and `y` remain instances of the `Decimal` type
2. Using [`model_dump`][pydantic.main.BaseModel.model_dump] with `mode='json'`, `x` is serialized as a `string`, and `y` is serialized as a `float` because of the custom serializer applied.
3. Using [`model_dump_json`][pydantic.main.BaseModel.model_dump_json], `x` is serialized as a `string`, and `y` is serialized as a `float` because of the custom serializer applied.

## Enum

Pydantic uses Python's standard `enum` classes to define choices.

### `enum.Enum`

Checks that the value is a valid `Enum` instance.

### Subclass of `enum.Enum`

Checks that the value is a valid member of the enum.

### `enum.IntEnum`

Checks that the value is a valid `IntEnum` instance.

### Subclass of `enum.IntEnum`

Checks that the value is a valid member of the integer enum.

```py
from enum import Enum, IntEnum

from pydantic import BaseModel, ValidationError


class FruitEnum(str, Enum):
    pear = 'pear'
    banana = 'banana'


class ToolEnum(IntEnum):
    spanner = 1
    wrench = 2


class CookingModel(BaseModel):
    fruit: FruitEnum = FruitEnum.pear
    tool: ToolEnum = ToolEnum.spanner


print(CookingModel())
#> fruit=<FruitEnum.pear: 'pear'> tool=<ToolEnum.spanner: 1>
print(CookingModel(tool=2, fruit='banana'))
#> fruit=<FruitEnum.banana: 'banana'> tool=<ToolEnum.wrench: 2>
try:
    CookingModel(fruit='other')
except ValidationError as e:
    print(e)
    """
    1 validation error for CookingModel
    fruit
      Input should be 'pear' or 'banana' [type=enum, input_value='other', input_type=str]
    """
```

## List

### `list`

Allows `list`, `tuple`, `set`, `frozenset`, `deque`, or generators and casts to a `list`.
When a generic parameter is provided, the appropriate validation is applied to all items of the list.

### `typing.List`

Handled the same as `list` above.

```py
from typing import List, Optional

from pydantic import BaseModel


class Model(BaseModel):
    simple_list: Optional[list] = None
    list_of_ints: Optional[List[int]] = None


print(Model(simple_list=['1', '2', '3']).simple_list)
#> ['1', '2', '3']
print(Model(list_of_ints=['1', '2', '3']).list_of_ints)
#> [1, 2, 3]
```

## Tuple

### `tuple`

Allows `list`, `tuple`, `set`, `frozenset`, `deque`, or generators and casts to a `tuple`.
When generic parameters are provided, the appropriate validation is applied to the respective items of the tuple

### `typing.Tuple`

Handled the same as `tuple` above.

```py
from typing import Optional, Tuple

from pydantic import BaseModel


class Model(BaseModel):
    simple_tuple: Optional[tuple] = None
    tuple_of_different_types: Optional[Tuple[int, float, bool]] = None


print(Model(simple_tuple=[1, 2, 3, 4]).simple_tuple)
#> (1, 2, 3, 4)
print(Model(tuple_of_different_types=[3, 2, 1]).tuple_of_different_types)
#> (3, 2.0, True)
```

## Deque

### `deque`

Allows `list`, `tuple`, `set`, `frozenset`, `deque`, or generators and casts to a `deque`.
When generic parameters are provided, the appropriate validation is applied to the respective items of the `deque`

### `typing.Deque`

Handled the same as `deque` above.

```py
from typing import Deque, Optional

from pydantic import BaseModel


class Model(BaseModel):
    deque: Optional[Deque[int]] = None


print(Model(deque=[1, 2, 3]).deque)
#> deque([1, 2, 3])
```

## NamedTuple

### Subclasses of `typing.NamedTuple`

Similar to `tuple`, but creates instances of the given `namedtuple` class.

### Types returned from `collections.namedtuple`

Similar to `subclass of typing.NamedTuple`, but since field types are not specified,
all fields are treated as having type `Any`.

```py
from typing import NamedTuple

from pydantic import BaseModel, ValidationError


class Point(NamedTuple):
    x: int
    y: int


class Model(BaseModel):
    p: Point


try:
    Model(p=('1.3', '2'))
except ValidationError as e:
    print(e)
    """
    1 validation error for Model
    p.0
      Input should be a valid integer, unable to parse string as an integer [type=int_parsing, input_value='1.3', input_type=str]
    """
```

## Set

### `set`

Allows `list`, `tuple`, `set`, `frozenset`, `deque`, or generators and casts to a `set`.
When a generic parameter is provided, the appropriate validation is applied to all items of the set.

### `typing.Set`

Handled the same as `set` above.

```py
from typing import Optional, Set

from pydantic import BaseModel


class Model(BaseModel):
    simple_set: Optional[set] = None
    set_of_ints: Optional[Set[int]] = None


print(Model(simple_set={'1', '2', '3'}).simple_set)
#> {'1', '2', '3'}
print(Model(simple_set=['1', '2', '3']).simple_set)
#> {'1', '2', '3'}
print(Model(set_of_ints=['1', '2', '3']).set_of_ints)
#> {1, 2, 3}
```

## Frozenset

### `frozenset`

Allows `list`, `tuple`, `set`, `frozenset`, `deque`, or generators and casts to a `frozenset`.
When a generic parameter is provided, the appropriate validation is applied to all items of the frozen set.

### `typing.FrozenSet`

Handled the same as `frozenset` above.

```py
from typing import FrozenSet, Optional

from pydantic import BaseModel


class Model(BaseModel):
    simple_frozenset: Optional[frozenset] = None
    frozenset_of_ints: Optional[FrozenSet[int]] = None


m1 = Model(simple_frozenset=['1', '2', '3'])
print(type(m1.simple_frozenset))
#> <class 'frozenset'>
print(sorted(m1.simple_frozenset))
#> ['1', '2', '3']

m2 = Model(frozenset_of_ints=['1', '2', '3'])
print(type(m2.frozenset_of_ints))
#> <class 'frozenset'>
print(sorted(m2.frozenset_of_ints))
#> [1, 2, 3]
```


## Support for iterable types

### `typing.Sequence`

This is intended for use when the provided value should meet the requirements of the `Sequence` protocol, and it is
desirable to do eager validation of the values in the container. Note that when validation must be performed on the
values of the container, the type of the container may not be preserved since validation may end up replacing values.
We guarantee that the validated value will be a valid `typing.Sequence`, but it may have a different type than was
provided (generally, it will become a `list`).

### `typing.Iterable`

This is intended for use when the provided value may be an iterable that shouldn't be consumed.
See [Infinite Generators](#infinite-generators) below for more detail on parsing and validation.
Similar to `typing.Sequence`, we guarantee that the validated result will be a valid `typing.Iterable`,
but it may have a different type than was provided. In particular, even if a non-generator type such as a `list`
is provided, the post-validation value of a field of type `typing.Iterable` will be a generator.

Here is a simple example using `typing.Sequence`:

```py
from typing import Sequence

from pydantic import BaseModel


class Model(BaseModel):
    sequence_of_ints: Sequence[int] = None


print(Model(sequence_of_ints=[1, 2, 3, 4]).sequence_of_ints)
#> [1, 2, 3, 4]
print(Model(sequence_of_ints=(1, 2, 3, 4)).sequence_of_ints)
#> (1, 2, 3, 4)
```

### Strings aren't Sequences

While instances of `str` are technically valid instances of the `Sequence[str]` protocol from a type-checker's point of
view, this is frequently not intended as is a common source of bugs.

As a result, Pydantic raises a `ValidationError` if you attempt to pass a `str` or `bytes` instance into a field of type
`Sequence[str]` or `Sequence[bytes]`:

```py
from typing import Optional, Sequence

from pydantic import BaseModel, ValidationError


class Model(BaseModel):
    sequence_of_strs: Optional[Sequence[str]] = None
    sequence_of_bytes: Optional[Sequence[bytes]] = None


print(Model(sequence_of_strs=['a', 'bc']).sequence_of_strs)
#> ['a', 'bc']
print(Model(sequence_of_strs=('a', 'bc')).sequence_of_strs)
#> ('a', 'bc')
print(Model(sequence_of_bytes=[b'a', b'bc']).sequence_of_bytes)
#> [b'a', b'bc']
print(Model(sequence_of_bytes=(b'a', b'bc')).sequence_of_bytes)
#> (b'a', b'bc')


try:
    Model(sequence_of_strs='abc')
except ValidationError as e:
    print(e)
    """
    1 validation error for Model
    sequence_of_strs
      'str' instances are not allowed as a Sequence value [type=sequence_str, input_value='abc', input_type=str]
    """
try:
    Model(sequence_of_bytes=b'abc')
except ValidationError as e:
    print(e)
    """
    1 validation error for Model
    sequence_of_bytes
      'bytes' instances are not allowed as a Sequence value [type=sequence_str, input_value=b'abc', input_type=bytes]
    """
```

### Infinite Generators

If you have a generator you want to validate, you can still use `Sequence` as described above.
In that case, the generator will be consumed and stored on the model as a list and its values will be
validated against the type parameter of the `Sequence` (e.g. `int` in `Sequence[int]`).

However, if you have a generator that you _don't_ want to be eagerly consumed (e.g. an infinite
generator or a remote data loader), you can use a field of type `Iterable`:

```py
from typing import Iterable

from pydantic import BaseModel


class Model(BaseModel):
    infinite: Iterable[int]


def infinite_ints():
    i = 0
    while True:
        yield i
        i += 1


m = Model(infinite=infinite_ints())
print(m)
"""
infinite=ValidatorIterator(index=0, schema=Some(Int(IntValidator { strict: false })))
"""

for i in m.infinite:
    print(i)
    #> 0
    #> 1
    #> 2
    #> 3
    #> 4
    #> 5
    #> 6
    #> 7
    #> 8
    #> 9
    #> 10
    if i == 10:
        break
```

!!! warning
    During initial validation, `Iterable` fields only perform a simple check that the provided argument is iterable.
    To prevent it from being consumed, no validation of the yielded values is performed eagerly.


Though the yielded values are not validated eagerly, they are still validated when yielded, and will raise a
`ValidationError` at yield time when appropriate:

```python
from typing import Iterable

from pydantic import BaseModel, ValidationError


class Model(BaseModel):
    int_iterator: Iterable[int]


def my_iterator():
    yield 13
    yield '27'
    yield 'a'


m = Model(int_iterator=my_iterator())
print(next(m.int_iterator))
#> 13
print(next(m.int_iterator))
#> 27
try:
    next(m.int_iterator)
except ValidationError as e:
    print(e)
    """
    1 validation error for ValidatorIterator
    2
      Input should be a valid integer, unable to parse string as an integer [type=int_parsing, input_value='a', input_type=str]
    """
```

## Mapping Types

### `dict`

`dict(v)` is used to attempt to convert a dictionary. see `typing.Dict` below for sub-type constraints.

```py
from pydantic import BaseModel, ValidationError


class Model(BaseModel):
    x: dict


m = Model(x={'foo': 1})
print(m.model_dump())
#> {'x': {'foo': 1}}

try:
    Model(x='test')
except ValidationError as e:
    print(e)
    """
    1 validation error for Model
    x
      Input should be a valid dictionary [type=dict_type, input_value='test', input_type=str]
    """
```

### `typing.Dict`

```py
from typing import Dict

from pydantic import BaseModel, ValidationError


class Model(BaseModel):
    x: Dict[str, int]


m = Model(x={'foo': 1})
print(m.model_dump())
#> {'x': {'foo': 1}}

try:
    Model(x={'foo': '1'})
except ValidationError as e:
    print(e)
    """
    1 validation error for Model
    x
      Input should be a valid dictionary [type=dict_type, input_value='test', input_type=str]
    """
```

### TypedDict

!!! note
    This is a new feature of the Python standard library as of Python 3.8.
    Because of limitations in `typing.TypedDict` before 3.12, the [typing-extensions](https://pypi.org/project/typing-extensions/)
    package is required for Python <3.12. You'll need to import `TypedDict` from `typing_extensions` instead of `typing` and will
    get a build time error if you don't.

[TypedDict](https://docs.python.org/3/library/typing.html#typing.TypedDict) declares a dictionary type that expects all of
its instances to have a certain set of keys, where each key is associated with a value of a consistent type.

It is same as `dict` but Pydantic will validate the dictionary since keys are annotated.

```py
from typing_extensions import TypedDict

from pydantic import TypeAdapter, ValidationError


class User(TypedDict):
    name: str
    id: int


ta = TypeAdapter(User)

print(ta.validate_python({'name': 'foo', 'id': 1}))
#> {'name': 'foo', 'id': 1}

try:
    ta.validate_python({'name': 'foo'})
except ValidationError as e:
    print(e)
    """
    1 validation error for typed-dict
    id
      Field required [type=missing, input_value={'name': 'foo'}, input_type=dict]
    """
```

You can define `__pydantic_config__` to change the model inherited from `TypedDict`.
See [Model Config](../usage/model_config.md) for more details.

```py
from typing import Optional

from typing_extensions import TypedDict

from pydantic import ConfigDict, TypeAdapter, ValidationError


# `total=False` means keys are non-required
class UserIdentity(TypedDict, total=False):
    name: Optional[str]
    surname: str


class User(TypedDict):
    __pydantic_config__ = ConfigDict(extra='forbid')

    identity: UserIdentity
    age: int


ta = TypeAdapter(User)

print(
    ta.validate_python(
        {'identity': {'name': 'Smith', 'surname': 'John'}, 'age': 37}
    )
)
#> {'identity': {'name': 'Smith', 'surname': 'John'}, 'age': 37}

print(
    ta.validate_python(
        {'identity': {'name': None, 'surname': 'John'}, 'age': 37}
    )
)
#> {'identity': {'name': None, 'surname': 'John'}, 'age': 37}

print(ta.validate_python({'identity': {}, 'age': 37}))
#> {'identity': {}, 'age': 37}


try:
    ta.validate_python(
        {'identity': {'name': ['Smith'], 'surname': 'John'}, 'age': 24}
    )
except ValidationError as e:
    print(e)
    """
    1 validation error for typed-dict
    identity.name
      Input should be a valid string [type=string_type, input_value=['Smith'], input_type=list]
    """

try:
    ta.validate_python(
        {
            'identity': {'name': 'Smith', 'surname': 'John'},
            'age': '37',
            'email': 'john.smith@me.com',
        }
    )
except ValidationError as e:
    print(e)
    """
    1 validation error for typed-dict
    email
      Extra inputs are not permitted [type=extra_forbidden, input_value='john.smith@me.com', input_type=str]
    """
```

## Callable

See below for more detail on parsing and validation

Fields can also be of type `Callable`:

```py
from typing import Callable

from pydantic import BaseModel


class Foo(BaseModel):
    callback: Callable[[int], int]


m = Foo(callback=lambda x: x)
print(m)
#> callback=<function <lambda> at 0x0123456789ab>
```

!!! warning
    Callable fields only perform a simple check that the argument is
    callable; no validation of arguments, their types, or the return
    type is performed.

## IP Address Types

* `ipaddress.IPv4Address`: Uses the type itself for validation by passing the value to `IPv4Address(v)`.
* `ipaddress.IPv4Interface`: Uses the type itself for validation by passing the value to `IPv4Address(v)`.
* `ipaddress.IPv4Network`: Uses the type itself for validation by passing the value to `IPv4Network(v)`.
* `ipaddress.IPv6Address`: Uses the type itself for validation by passing the value to `IPv6Address(v)`.
* `ipaddress.IPv6Interface`: Uses the type itself for validation by passing the value to `IPv6Interface(v)`.
* `ipaddress.IPv6Network`: Uses the type itself for validation by passing the value to `IPv6Network(v)`.

See [Network Types](../api/networks.md) for other custom IP address types.

## UUID

For UUID, Pydantic tries to use the type itself for validation by passing the value to `UUID(v)`.
There's a fallback to `UUID(bytes=v)` for `bytes` and `bytearray`.

In case you want to constrained the UUID version, you can check the following types:

* [`UUID1`][pydantic.types.UUID1]: requires UUID version 1.
* [`UUID3`][pydantic.types.UUID3]: requires UUID version 3.
* [`UUID4`][pydantic.types.UUID4]: requires UUID version 4.
* [`UUID5`][pydantic.types.UUID5]: requires UUID version 5.

## Union

The `Union` type allows a model attribute to accept different types, e.g.:

```py
from typing import Union
from uuid import UUID

from pydantic import BaseModel


class User(BaseModel):
    id: Union[int, str, UUID]
    name: str


user_01 = User(id=123, name='John Doe')
print(user_01)
#> id=123 name='John Doe'
print(user_01.id)
#> 123
user_02 = User(id='1234', name='John Doe')
print(user_02)
#> id='1234' name='John Doe'
print(user_02.id)
#> 1234
user_03_uuid = UUID('cf57432e-809e-4353-adbd-9d5c0d733868')
user_03 = User(id=user_03_uuid, name='John Doe')
print(user_03)
#> id=UUID('cf57432e-809e-4353-adbd-9d5c0d733868') name='John Doe'
print(user_03.id)
#> cf57432e-809e-4353-adbd-9d5c0d733868
print(user_03_uuid.int)
#> 275603287559914445491632874575877060712
```

!!! tip
    The type `Optional[x]` is a shorthand for `Union[x, None]`.

    `Optional[x]` can also be used to specify a required field that can take `None` as a value.

    See more details in [Required fields](../usage/models.md#required-fields).

#### Union Mode

By default `Union` validation will try to return the variant which is the best match for the input.

Consider for example the case of `Union[int, str]`. When [`strict` mode](../usage/strict_mode.md) is not enabled
then `int` fields will accept `str` inputs. In the example below, the `id` field (which is `Union[int, str]`)
will accept the string `'123'` as an input, and preserve it as a string:

```py
from typing import Union

from pydantic import BaseModel


class User(BaseModel):
    id: Union[int, str]
    age: int


print(User(id='123', age='45'))
#> id='123' age=45

print(type(User(id='123', age='45').id))
#> <class 'str'>
```

This is known as `'smart'` mode for `Union` validation.

At present only one other `Union` validation mode exists, called `'left_to_right'` validation. In this mode
variants are attempted from left to right and the first successful validation is accepted as input.

Consider the same example, this time with `union_mode='left_to_right'` set as a [`Field`](../usage/fields.md)
parameter on `id`. With this validation mode, the `int` variant will coerce strings of digits into `int`
values:

```py
from typing import Union

from pydantic import BaseModel, Field


class User(BaseModel):
    id: Union[int, str] = Field(..., union_mode='left_to_right')
    age: int


print(User(id='123', age='45'))
#> id=123 age=45


print(type(User(id='123', age='45').id))
#> <class 'int'>
```

### Discriminated Unions (a.k.a. Tagged Unions)

When `Union` is used with multiple submodels, you sometimes know exactly which submodel needs to
be checked and validated and want to enforce this.
To do that you can set the same field - let's call it `my_discriminator` - in each of the submodels
with a discriminated value, which is one (or many) `Literal` value(s).
For your `Union`, you can set the discriminator in its value: `Field(discriminator='my_discriminator')`.

Setting a discriminated union has many benefits:

- validation is faster since it is only attempted against one model
- only one explicit error is raised in case of failure
- the generated JSON schema implements the [associated OpenAPI specification](https://github.com/OAI/OpenAPI-Specification/blob/main/versions/3.1.0.md#discriminator-object)

```py requires="3.8"
from typing import Literal, Union

from pydantic import BaseModel, Field, ValidationError


class Cat(BaseModel):
    pet_type: Literal['cat']
    meows: int


class Dog(BaseModel):
    pet_type: Literal['dog']
    barks: float


class Lizard(BaseModel):
    pet_type: Literal['reptile', 'lizard']
    scales: bool


class Model(BaseModel):
    pet: Union[Cat, Dog, Lizard] = Field(..., discriminator='pet_type')
    n: int


print(Model(pet={'pet_type': 'dog', 'barks': 3.14}, n=1))
#> pet=Dog(pet_type='dog', barks=3.14) n=1
try:
    Model(pet={'pet_type': 'dog'}, n=1)
except ValidationError as e:
    print(e)
    """
    1 validation error for Model
    pet.dog.barks
      Field required [type=missing, input_value={'pet_type': 'dog'}, input_type=dict]
    """
```

!!! note
    Using the [`typing.Annotated` fields syntax](../usage/json_schema.md#typingannotated-fields) can be handy to regroup
    the `Union` and `discriminator` information. See below for an example!

!!! warning
    Discriminated unions cannot be used with only a single variant, such as `Union[Cat]`.

    Python changes `Union[T]` into `T` at interpretation time, so it is not possible for `pydantic` to
    distinguish fields of `Union[T]` from `T`.

#### Nested Discriminated Unions

Only one discriminator can be set for a field but sometimes you want to combine multiple discriminators.
You can do it by creating nested `Annotated` types, e.g.:

```py requires="3.8"
from typing import Literal, Union

from typing_extensions import Annotated

from pydantic import BaseModel, Field, ValidationError


class BlackCat(BaseModel):
    pet_type: Literal['cat']
    color: Literal['black']
    black_name: str


class WhiteCat(BaseModel):
    pet_type: Literal['cat']
    color: Literal['white']
    white_name: str


Cat = Annotated[Union[BlackCat, WhiteCat], Field(discriminator='color')]


class Dog(BaseModel):
    pet_type: Literal['dog']
    name: str


Pet = Annotated[Union[Cat, Dog], Field(discriminator='pet_type')]


class Model(BaseModel):
    pet: Pet
    n: int


m = Model(pet={'pet_type': 'cat', 'color': 'black', 'black_name': 'felix'}, n=1)
print(m)
#> pet=BlackCat(pet_type='cat', color='black', black_name='felix') n=1
try:
    Model(pet={'pet_type': 'cat', 'color': 'red'}, n='1')
except ValidationError as e:
    print(e)
    """
    1 validation error for Model
    pet.cat
      Input tag 'red' found using 'color' does not match any of the expected tags: 'black', 'white' [type=union_tag_invalid, input_value={'pet_type': 'cat', 'color': 'red'}, input_type=dict]
    """
try:
    Model(pet={'pet_type': 'cat', 'color': 'black'}, n='1')
except ValidationError as e:
    print(e)
    """
    1 validation error for Model
    pet.cat.black.black_name
      Field required [type=missing, input_value={'pet_type': 'cat', 'color': 'black'}, input_type=dict]
    """
```

## Support for `Type[T]` and `TypeVar``

### `type`

Pydantic supports the use of `type[T]` to specify that a field may only accept classes (not instances)
that are subclasses of `T`.

### `typing.Type`

Handled the same as `type` above.

```py
from typing import Type

from pydantic import BaseModel, ValidationError


class Foo:
    pass


class Bar(Foo):
    pass


class Other:
    pass


class SimpleModel(BaseModel):
    just_subclasses: Type[Foo]


SimpleModel(just_subclasses=Foo)
SimpleModel(just_subclasses=Bar)
try:
    SimpleModel(just_subclasses=Other)
except ValidationError as e:
    print(e)
    """
    1 validation error for SimpleModel
    just_subclasses
      Input should be a subclass of Foo [type=is_subclass_of, input_value=<class '__main__.Other'>, input_type=type]
    """
```

You may also use `Type` to specify that any class is allowed.

```py upgrade="skip"
from typing import Type

from pydantic import BaseModel, ValidationError


class Foo:
    pass


class LenientSimpleModel(BaseModel):
    any_class_goes: Type


LenientSimpleModel(any_class_goes=int)
LenientSimpleModel(any_class_goes=Foo)
try:
    LenientSimpleModel(any_class_goes=Foo())
except ValidationError as e:
    print(e)
    """
    1 validation error for LenientSimpleModel
    any_class_goes
      Input should be a type [type=is_type, input_value=<__main__.Foo object at 0x0123456789ab>, input_type=Foo]
    """
```

### `typing.TypeVar`

`TypeVar` is supported either unconstrained, constrained or with a bound.

```py
from typing import TypeVar

from pydantic import BaseModel

Foobar = TypeVar('Foobar')
BoundFloat = TypeVar('BoundFloat', bound=float)
IntStr = TypeVar('IntStr', int, str)


class Model(BaseModel):
    a: Foobar  # equivalent of ": Any"
    b: BoundFloat  # equivalent of ": float"
    c: IntStr  # equivalent of ": Union[int, str]"


print(Model(a=[1], b=4.2, c='x'))
#> a=[1] b=4.2 c='x'

# a may be None
print(Model(a=None, b=1, c=1))
#> a=None b=1.0 c=1
```
