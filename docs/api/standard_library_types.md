---
description: Support for common types from the Python standard library.
---

Pydantic supports many common types from the Python standard library. If you need stricter processing see
[Strict Types](../concepts/types.md#strict-types), including if you need to constrain the values allowed (e.g. to require a positive `int`).

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

```python
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

### [`datetime.datetime`][]
* `datetime` fields will accept values of type:

    * `datetime`; an existing `datetime` object
    * `int` or `float`; assumed as Unix time, i.e. seconds (if >= `-2e10` and <= `2e10`) or milliseconds
      (if < `-2e10`or > `2e10`) since 1 January 1970
    * `str`; the following formats are accepted:
        * `YYYY-MM-DD[T]HH:MM[:SS[.ffffff]][Z or [±]HH[:]MM]`
        * `YYYY-MM-DD` is accepted in lax mode, but not in strict mode
        * `int` or `float` as a string (assumed as Unix time)
    * [`datetime.date`][] instances are accepted in lax mode, but not in strict mode

```python
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

### [`datetime.date`][]
* `date` fields will accept values of type:

    * `date`; an existing `date` object
    * `int` or `float`; handled the same as described for `datetime` above
    * `str`; the following formats are accepted:
        * `YYYY-MM-DD`
        * `int` or `float` as a string (assumed as Unix time)

```python
from datetime import date

from pydantic import BaseModel


class Birthday(BaseModel):
    d: date = None


my_birthday = Birthday(d=1679616000.0)

print(my_birthday.model_dump())
#> {'d': datetime.date(2023, 3, 24)}
```

### [`datetime.time`][]
* `time` fields will accept values of type:

    * `time`; an existing `time` object
    * `str`; the following formats are accepted:
        * `HH:MM[:SS[.ffffff]][Z or [±]HH[:]MM]`

```python
from datetime import time

from pydantic import BaseModel


class Meeting(BaseModel):
    t: time = None


m = Meeting(t=time(4, 8, 16))

print(m.model_dump())
#> {'t': datetime.time(4, 8, 16)}
```

### [`datetime.timedelta`][]
* `timedelta` fields will accept values of type:

    * `timedelta`; an existing `timedelta` object
    * `int` or `float`; assumed to be seconds
    * `str`; the following formats are accepted:
        * `[-][[DD]D,]HH:MM:SS[.ffffff]`
            * Ex: `'1d,01:02:03.000004'` or `'1D01:02:03.000004'` or `'01:02:03'`
        * `[±]P[DD]DT[HH]H[MM]M[SS]S` ([ISO 8601](https://en.wikipedia.org/wiki/ISO_8601) format for timedelta)

```python
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

### [`int`][]

* Pydantic uses `int(v)` to coerce types to an `int`;
  see [Data conversion](../concepts/models.md#data-conversion) for details on loss of information during data conversion.

### [`float`][]

* Pydantic uses `float(v)` to coerce values to floats.

### [`enum.IntEnum`][]

* Validation: Pydantic checks that the value is a valid `IntEnum` instance.
* Validation for subclass of `enum.IntEnum`: checks that the value is a valid member of the integer enum;
  see [Enums and Choices](#enum) for more details.

### [`decimal.Decimal`][]

* Validation: Pydantic attempts to convert the value to a string, then passes the string to `Decimal(v)`.
* Serialization: Pydantic serializes [`Decimal`][decimal.Decimal] types as strings.
You can use a custom serializer to override this behavior if desired. For example:

```python
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

### [`complex`][]

* Validation: Pydantic supports `complex` types or `str` values that can be converted to a `complex` type.
* Serialization: Pydantic serializes [`complex`][] types as strings.

### [`fractions.Fraction`][fractions.Fraction]

* Validation: Pydantic attempts to convert the value to a `Fraction` using `Fraction(v)`.
* Serialization: Pydantic serializes [`Fraction`][fractions.Fraction] types as strings.

## [`Enum`][enum.Enum]

Pydantic uses Python's standard [`enum`][] classes to define choices.

`enum.Enum` checks that the value is a valid `Enum` instance.
Subclass of `enum.Enum` checks that the value is a valid member of the enum.

```python
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

## Lists and Tuples

### [`list`][]

Allows [`list`][], [`tuple`][], [`set`][], [`frozenset`][], [`deque`][collections.deque], or generators and casts to a [`list`][].
When a generic parameter is provided, the appropriate validation is applied to all items of the list.

### [`typing.List`][]

Handled the same as `list` above.

```python
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

### [`tuple`][]

Allows [`list`][], [`tuple`][], [`set`][], [`frozenset`][], [`deque`][collections.deque], or generators and casts to a [`tuple`][].
When generic parameters are provided, the appropriate validation is applied to the respective items of the tuple

### [`typing.Tuple`][]

Handled the same as `tuple` above.

```python
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

### [`typing.NamedTuple`][]

Subclasses of [`typing.NamedTuple`][] are similar to `tuple`, but create instances of the given `namedtuple` class.

Subclasses of [`collections.namedtuple`][] are similar to subclass of [`typing.NamedTuple`][], but since field types are not specified,
all fields are treated as having type [`Any`][typing.Any].

```python
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

## Deque

### [`deque`][collections.deque]

Allows [`list`][], [`tuple`][], [`set`][], [`frozenset`][], [`deque`][collections.deque], or generators and casts to a [`deque`][collections.deque].
When generic parameters are provided, the appropriate validation is applied to the respective items of the `deque`.

### [`typing.Deque`][]

Handled the same as `deque` above.

```python
from typing import Deque, Optional

from pydantic import BaseModel


class Model(BaseModel):
    deque: Optional[Deque[int]] = None


print(Model(deque=[1, 2, 3]).deque)
#> deque([1, 2, 3])
```

## Sets

### [`set`][]

Allows [`list`][], [`tuple`][], [`set`][], [`frozenset`][], [`deque`][collections.deque], or generators and casts to a [`set`][].
When a generic parameter is provided, the appropriate validation is applied to all items of the set.

### [`typing.Set`][]

Handled the same as `set` above.

```python
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

### [`frozenset`][]

Allows [`list`][], [`tuple`][], [`set`][], [`frozenset`][], [`deque`][collections.deque], or generators and casts to a [`frozenset`][].
When a generic parameter is provided, the appropriate validation is applied to all items of the frozen set.

### [`typing.FrozenSet`][]

Handled the same as `frozenset` above.

```python
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


## Other Iterables

### [`typing.Sequence`][]

This is intended for use when the provided value should meet the requirements of the `Sequence` ABC, and it is
desirable to do eager validation of the values in the container. Note that when validation must be performed on the
values of the container, the type of the container may not be preserved since validation may end up replacing values.
We guarantee that the validated value will be a valid [`typing.Sequence`][], but it may have a different type than was
provided (generally, it will become a `list`).

### [`typing.Iterable`][]

This is intended for use when the provided value may be an iterable that shouldn't be consumed.
See [Infinite Generators](#infinite-generators) below for more detail on parsing and validation.
Similar to [`typing.Sequence`][], we guarantee that the validated result will be a valid [`typing.Iterable`][],
but it may have a different type than was provided. In particular, even if a non-generator type such as a `list`
is provided, the post-validation value of a field of type [`typing.Iterable`][] will be a generator.

Here is a simple example using [`typing.Sequence`][]:

```python
from typing import Sequence

from pydantic import BaseModel


class Model(BaseModel):
    sequence_of_ints: Sequence[int] = None


print(Model(sequence_of_ints=[1, 2, 3, 4]).sequence_of_ints)
#> [1, 2, 3, 4]
print(Model(sequence_of_ints=(1, 2, 3, 4)).sequence_of_ints)
#> (1, 2, 3, 4)
```

### Infinite Generators

If you have a generator you want to validate, you can still use `Sequence` as described above.
In that case, the generator will be consumed and stored on the model as a list and its values will be
validated against the type parameter of the `Sequence` (e.g. `int` in `Sequence[int]`).

However, if you have a generator that you _don't_ want to be eagerly consumed (e.g. an infinite
generator or a remote data loader), you can use a field of type [`Iterable`][typing.Iterable]:

```python
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

### [`dict`][]

`dict(v)` is used to attempt to convert a dictionary. see [`typing.Dict`][] below for sub-type constraints.

```python
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

### [`typing.Dict`][]

```python
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
    Because of limitations in [typing.TypedDict][] before 3.12, the [typing-extensions](https://pypi.org/project/typing-extensions/)
    package is required for Python <3.12. You'll need to import `TypedDict` from `typing_extensions` instead of `typing` and will
    get a build time error if you don't.

[`TypedDict`][typing.TypedDict] declares a dictionary type that expects all of
its instances to have a certain set of keys, where each key is associated with a value of a consistent type.

It is same as [`dict`][] but Pydantic will validate the dictionary since keys are annotated.

```python
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

You can define `__pydantic_config__` to change the model inherited from [`TypedDict`][typing.TypedDict].
See the [`ConfigDict` API reference][pydantic.config.ConfigDict] for more details.

```python
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

Fields can also be of type [`Callable`][typing.Callable]:

```python
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

* [`ipaddress.IPv4Address`][]: Uses the type itself for validation by passing the value to `IPv4Address(v)`.
* [`ipaddress.IPv4Interface`][]: Uses the type itself for validation by passing the value to `IPv4Address(v)`.
* [`ipaddress.IPv4Network`][]: Uses the type itself for validation by passing the value to `IPv4Network(v)`.
* [`ipaddress.IPv6Address`][]: Uses the type itself for validation by passing the value to `IPv6Address(v)`.
* [`ipaddress.IPv6Interface`][]: Uses the type itself for validation by passing the value to `IPv6Interface(v)`.
* [`ipaddress.IPv6Network`][]: Uses the type itself for validation by passing the value to `IPv6Network(v)`.

See [Network Types](../api/networks.md) for other custom IP address types.

## UUID

For UUID, Pydantic tries to use the type itself for validation by passing the value to `UUID(v)`.
There's a fallback to `UUID(bytes=v)` for `bytes` and `bytearray`.

In case you want to constrain the UUID version, you can check the following types:

* [`UUID1`][pydantic.types.UUID1]: requires UUID version 1.
* [`UUID3`][pydantic.types.UUID3]: requires UUID version 3.
* [`UUID4`][pydantic.types.UUID4]: requires UUID version 4.
* [`UUID5`][pydantic.types.UUID5]: requires UUID version 5.

## Union

Pydantic has extensive support for union validation, both [`typing.Union`][] and Python 3.10's pipe syntax (`A | B`) are supported.
Read more in the [`Unions`](../concepts/unions.md) section of the concepts docs.

## [`Type`][typing.Type] and [`TypeVar`][typing.TypeVar]

### [`type`][]

Pydantic supports the use of `type[T]` to specify that a field may only accept classes (not instances)
that are subclasses of `T`.

### [`typing.Type`][]

Handled the same as `type` above.

```python
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

```python {upgrade="skip"}
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

### [`typing.TypeVar`][]

[`TypeVar`][typing.TypeVar] is supported either unconstrained, constrained or with a bound.

```python
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

## None Types

[`None`][], `type(None)`, or `Literal[None]` are all equivalent according to [the typing specification](https://typing.readthedocs.io/en/latest/spec/special-types.html#none).
Allows only `None` value.

## Strings

- [`str`][]: Strings are accepted as-is.
- [`bytes`][] and [`bytearray`][] are converted using the [`decode()`][bytes.decode] method.
- Enums inheriting from [`str`][] are converted using the [`value`][enum.Enum.value] attribute.

All other types cause an error.
<!-- * TODO: add note about optional number to string conversion from lig's PR -->

!!! warning "Strings aren't Sequences"

    While instances of `str` are technically valid instances of the `Sequence[str]` protocol from a type-checker's point of
    view, this is frequently not intended as is a common source of bugs.

    As a result, Pydantic raises a `ValidationError` if you attempt to pass a `str` or `bytes` instance into a field of type
    `Sequence[str]` or `Sequence[bytes]`:

```python
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

## Bytes

[`bytes`][] are accepted as-is. [`bytearray`][] is converted using `bytes(v)`. `str` are converted using `v.encode()`. `int`, `float`, and `Decimal` are coerced using `str(v).encode()`. See [ByteSize](types.md#pydantic.types.ByteSize) for more details.


## [`typing.Literal`][]

Pydantic supports the use of [`typing.Literal`][] as a lightweight way to specify that a field may accept only specific literal values:

```python
from typing import Literal

from pydantic import BaseModel, ValidationError


class Pie(BaseModel):
    flavor: Literal['apple', 'pumpkin']


Pie(flavor='apple')
Pie(flavor='pumpkin')
try:
    Pie(flavor='cherry')
except ValidationError as e:
    print(str(e))
    """
    1 validation error for Pie
    flavor
      Input should be 'apple' or 'pumpkin' [type=literal_error, input_value='cherry', input_type=str]
    """
```

One benefit of this field type is that it can be used to check for equality with one or more specific values
without needing to declare custom validators:

```python
from typing import ClassVar, List, Literal, Union

from pydantic import BaseModel, ValidationError


class Cake(BaseModel):
    kind: Literal['cake']
    required_utensils: ClassVar[List[str]] = ['fork', 'knife']


class IceCream(BaseModel):
    kind: Literal['icecream']
    required_utensils: ClassVar[List[str]] = ['spoon']


class Meal(BaseModel):
    dessert: Union[Cake, IceCream]


print(type(Meal(dessert={'kind': 'cake'}).dessert).__name__)
#> Cake
print(type(Meal(dessert={'kind': 'icecream'}).dessert).__name__)
#> IceCream
try:
    Meal(dessert={'kind': 'pie'})
except ValidationError as e:
    print(str(e))
    """
    2 validation errors for Meal
    dessert.Cake.kind
      Input should be 'cake' [type=literal_error, input_value='pie', input_type=str]
    dessert.IceCream.kind
      Input should be 'icecream' [type=literal_error, input_value='pie', input_type=str]
    """
```

With proper ordering in an annotated `Union`, you can use this to parse types of decreasing specificity:

```python
from typing import Literal, Optional, Union

from pydantic import BaseModel


class Dessert(BaseModel):
    kind: str


class Pie(Dessert):
    kind: Literal['pie']
    flavor: Optional[str]


class ApplePie(Pie):
    flavor: Literal['apple']


class PumpkinPie(Pie):
    flavor: Literal['pumpkin']


class Meal(BaseModel):
    dessert: Union[ApplePie, PumpkinPie, Pie, Dessert]


print(type(Meal(dessert={'kind': 'pie', 'flavor': 'apple'}).dessert).__name__)
#> ApplePie
print(type(Meal(dessert={'kind': 'pie', 'flavor': 'pumpkin'}).dessert).__name__)
#> PumpkinPie
print(type(Meal(dessert={'kind': 'pie'}).dessert).__name__)
#> Dessert
print(type(Meal(dessert={'kind': 'cake'}).dessert).__name__)
#> Dessert
```

## [`typing.Any`][]

Allows any value, including `None`.

## [`typing.Hashable`][]

* From Python, supports any data that passes an `isinstance(v, Hashable)` check.
* From JSON, first loads the data via an `Any` validator, then checks if the data is hashable with `isinstance(v, Hashable)`.

## [`typing.Annotated`][]

Allows wrapping another type with arbitrary metadata, as per [PEP-593](https://www.python.org/dev/peps/pep-0593/). The `Annotated` hint may contain a single call to the [`Field` function](../concepts/types.md#composing-types-via-annotated), but otherwise the additional metadata is ignored and the root type is used.


## [`typing.Pattern`][]

Will cause the input value to be passed to `re.compile(v)` to create a regular expression pattern.


## [`pathlib.Path`][]

Simply uses the type itself for validation by passing the value to `Path(v)`.
