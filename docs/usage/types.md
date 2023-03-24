Where possible *pydantic* uses [standard library types](#standard-library-types) to define fields, thus smoothing
the learning curve. For many useful applications, however, no standard library type exists,
so *pydantic* implements [many commonly used types](#pydantic-types).

If no existing type suits your purpose you can also implement your [own pydantic-compatible types](#custom-data-types)
with custom properties and validation.

## Standard Library Types

*pydantic* supports many common types from the Python standard library. If you need stricter processing see
[Strict Types](#strict-types); if you need to constrain the values allowed (e.g. to require a positive int) see
[Constrained Types](#constrained-types).

`None`, `type(None)` or `Literal[None]` (equivalent according to [PEP 484](https://www.python.org/dev/peps/pep-0484/#using-none))
: allows only `None` value

`bool`
: see [Booleans](#booleans) below for details on how bools are validated and what values are permitted

`int`
: *pydantic* uses `int(v)` to coerce types to an `int`;
  see [this](models.md#data-conversion) warning on loss of information during data conversion

`float`
: similarly, `float(v)` is used to coerce values to floats

`str`
: strings are accepted as-is, `int` `float` and `Decimal` are coerced using `str(v)`, `bytes` and `bytearray` are
  converted using `v.decode()`, enums inheriting from `str` are converted using `v.value`,
  and all other types cause an error

`bytes`
: `bytes` are accepted as-is, `bytearray` is converted using `bytes(v)`, `str` are converted using `v.encode()`,
  and `int`, `float`, and `Decimal` are coerced using `str(v).encode()`

`list`
: allows `list`, `tuple`, `set`, `frozenset`, `deque`, or generators and casts to a list;
  see `typing.List` below for sub-type constraints

`tuple`
: allows `list`, `tuple`, `set`, `frozenset`, `deque`, or generators and casts to a tuple;
  see `typing.Tuple` below for sub-type constraints

`dict`
: `dict(v)` is used to attempt to convert a dictionary;
  see `typing.Dict` below for sub-type constraints

`set`
: allows `list`, `tuple`, `set`, `frozenset`, `deque`, or generators and casts to a set;
  see `typing.Set` below for sub-type constraints

`frozenset`
: allows `list`, `tuple`, `set`, `frozenset`, `deque`, or generators and casts to a frozen set;
  see `typing.FrozenSet` below for sub-type constraints

`deque`
: allows `list`, `tuple`, `set`, `frozenset`, `deque`, or generators and casts to a deque;
  see `typing.Deque` below for sub-type constraints

`datetime.date`
: see [Datetime Types](#datetime-types) below for more detail on parsing and validation

`datetime.time`
: see [Datetime Types](#datetime-types) below for more detail on parsing and validation

`datetime.datetime`
: see [Datetime Types](#datetime-types) below for more detail on parsing and validation

`datetime.timedelta`
: see [Datetime Types](#datetime-types) below for more detail on parsing and validation

`typing.Any`
: allows any value including `None`, thus an `Any` field is optional

`typing.Annotated`
: allows wrapping another type with arbitrary metadata, as per [PEP-593](https://www.python.org/dev/peps/pep-0593/). The
  `Annotated` hint may contain a single call to the [`Field` function](schema.md#typingannotated-fields), but otherwise
  the additional metadata is ignored and the root type is used.

`typing.TypeVar`
: constrains the values allowed based on `constraints` or `bound`, see [TypeVar](#typevar)

`typing.Union`
: see [Unions](#unions) below for more detail on parsing and validation

`typing.Optional`
: `Optional[x]` is simply short hand for `Union[x, None]`;
  see [Unions](#unions) below for more detail on parsing and validation and [Required Fields](models.md#required-fields) for details about required fields that can receive `None` as a value.

`typing.List`
: see [Typing Iterables](#typing-iterables) below for more detail on parsing and validation

`typing.Tuple`
: see [Typing Iterables](#typing-iterables) below for more detail on parsing and validation

`subclass of typing.NamedTuple`
: Same as `tuple` but instantiates with the given namedtuple and validates fields since they are annotated.
  See [Annotated Types](#annotated-types) below for more detail on parsing and validation

`subclass of collections.namedtuple`
: Same as `subclass of typing.NamedTuple` but all fields will have type `Any` since they are not annotated

`typing.Dict`
: see [Typing Iterables](#typing-iterables) below for more detail on parsing and validation

`subclass of typing.TypedDict`
: Same as `dict` but _pydantic_ will validate the dictionary since keys are annotated.
  See [Annotated Types](#annotated-types) below for more detail on parsing and validation

`typing.Set`
: see [Typing Iterables](#typing-iterables) below for more detail on parsing and validation

`typing.FrozenSet`
: see [Typing Iterables](#typing-iterables) below for more detail on parsing and validation

`typing.Deque`
: see [Typing Iterables](#typing-iterables) below for more detail on parsing and validation

`typing.Sequence`
: see [Typing Iterables](#typing-iterables) below for more detail on parsing and validation

`typing.Iterable`
: this is reserved for iterables that shouldn't be consumed. See [Infinite Generators](#infinite-generators) below for more detail on parsing and validation

`typing.Type`
: see [Type](#type) below for more detail on parsing and validation

`typing.Callable`
: see [Callable](#callable) below for more detail on parsing and validation

`typing.Pattern`
: will cause the input value to be passed to `re.compile(v)` to create a regex pattern

`ipaddress.IPv4Address`
: simply uses the type itself for validation by passing the value to `IPv4Address(v)`;
  see [Pydantic Types](#pydantic-types) for other custom IP address types

`ipaddress.IPv4Interface`
: simply uses the type itself for validation by passing the value to `IPv4Address(v)`;
  see [Pydantic Types](#pydantic-types) for other custom IP address types

`ipaddress.IPv4Network`
: simply uses the type itself for validation by passing the value to `IPv4Network(v)`;
  see [Pydantic Types](#pydantic-types) for other custom IP address types

`ipaddress.IPv6Address`
: simply uses the type itself for validation by passing the value to `IPv6Address(v)`;
  see [Pydantic Types](#pydantic-types) for other custom IP address types

`ipaddress.IPv6Interface`
: simply uses the type itself for validation by passing the value to `IPv6Interface(v)`;
  see [Pydantic Types](#pydantic-types) for other custom IP address types

`ipaddress.IPv6Network`
: simply uses the type itself for validation by passing the value to `IPv6Network(v)`;
  see [Pydantic Types](#pydantic-types) for other custom IP address types

`enum.Enum`
: checks that the value is a valid Enum instance

`subclass of enum.Enum`
: checks that the value is a valid member of the enum;
  see [Enums and Choices](#enums-and-choices) for more details

`enum.IntEnum`
: checks that the value is a valid IntEnum instance

`subclass of enum.IntEnum`
: checks that the value is a valid member of the integer enum;
  see [Enums and Choices](#enums-and-choices) for more details

`decimal.Decimal`
: *pydantic* attempts to convert the value to a string, then passes the string to `Decimal(v)`

`pathlib.Path`
: simply uses the type itself for validation by passing the value to `Path(v)`;
  see [Pydantic Types](#pydantic-types) for other more strict path types

`uuid.UUID`
: strings and bytes (converted to strings) are passed to `UUID(v)`, with a fallback to `UUID(bytes=v)` for `bytes` and `bytearray`;
  see [Pydantic Types](#pydantic-types) for other stricter UUID types

`ByteSize`
: converts a bytes string with units to bytes

### Typing Iterables

*pydantic* uses standard library `typing` types as defined in PEP 484 to define complex objects.

```py
from typing import Deque, Dict, FrozenSet, List, Optional, Sequence, Set, Tuple, Union

from pydantic import BaseModel


class Model(BaseModel):
    simple_list: list = None
    list_of_ints: List[int] = None

    simple_tuple: tuple = None
    tuple_of_different_types: Tuple[int, float, str, bool] = None

    simple_dict: dict = None
    dict_str_float: Dict[str, float] = None

    simple_set: set = None
    set_bytes: Set[bytes] = None
    frozen_set: FrozenSet[int] = None

    str_or_bytes: Union[str, bytes] = None
    none_or_str: Optional[str] = None

    sequence_of_ints: Sequence[int] = None

    compound: Dict[Union[str, bytes], List[Set[int]]] = None

    deque: Deque[int] = None


print(Model(simple_list=['1', '2', '3']).simple_list)
#> ['1', '2', '3']
print(Model(list_of_ints=['1', '2', '3']).list_of_ints)
#> [1, 2, 3]

print(Model(simple_dict={'a': 1, b'b': 2}).simple_dict)
#> {'a': 1, b'b': 2}
print(Model(dict_str_float={'a': 1, b'b': 2}).dict_str_float)
#> {'a': 1.0, 'b': 2.0}

print(Model(simple_tuple=[1, 2, 3, 4]).simple_tuple)
#> (1, 2, 3, 4)
print(Model(tuple_of_different_types=[4, 3, '2', 1]).tuple_of_different_types)
#> (4, 3.0, '2', True)

print(Model(sequence_of_ints=[1, 2, 3, 4]).sequence_of_ints)
#> [1, 2, 3, 4]
print(Model(sequence_of_ints=(1, 2, 3, 4)).sequence_of_ints)
#> (1, 2, 3, 4)

print(Model(deque=[1, 2, 3]).deque)
#> deque([1, 2, 3])
```

### Infinite Generators

If you have a generator you can use `Sequence` as described above. In that case, the
generator will be consumed and stored on the model as a list and its values will be
validated with the sub-type of `Sequence` (e.g. `int` in `Sequence[int]`).

But if you have a generator that you don't want to be consumed, e.g. an infinite
generator or a remote data loader, you can define its type with `Iterable`:

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
    `Iterable` fields only perform a simple check that the argument is iterable and
    won't be consumed.

    No validation of their values is performed as it cannot be done without consuming
    the iterable.

!!! tip
    If you want to validate the values of an infinite generator you can create a
    separate model and use it while consuming the generator, reporting the validation
    errors as appropriate.

    pydantic can't validate the values automatically for you because it would require
    consuming the infinite generator.

#### Validating the first value

You can create a [validator](validators.md) to validate the first value in an infinite generator and still not consume it entirely.

```py test="xfail - what's going on here?"
import itertools
from typing import Iterable
from pydantic import BaseModel, field_validator, ValidationError


class Model(BaseModel):
    infinite: Iterable[int]

    @field_validator('infinite')
    # You don't need to add the "ModelField", but it will help your
    # editor give you completion and catch errors
    def infinite_first_int(cls, iterable, field):
        first_value = next(iterable)
        if field.sub_fields:
            # The Iterable had a parameter type, in this case it's int
            # We use it to validate the first value
            sub_field = field.sub_fields[0]
            v, error = sub_field.validate(first_value, {}, loc='first_value')
            if error:
                raise ValidationError([error], cls)
        # This creates a new generator that returns the first value and then
        # the rest of the values from the (already started) iterable
        return itertools.chain([first_value], iterable)


def infinite_ints():
    i = 0
    while True:
        yield i
        i += 1


m = Model(infinite=infinite_ints())
print(m)


def infinite_strs():
    while True:
        yield from 'allthesingleladies'


try:
    Model(infinite=infinite_strs())
except ValidationError as e:
    print(e)
```

### Unions

The `Union` type allows a model attribute to accept different types, e.g.:

!!! info
    You may get unexpected coercion with `Union`; see below.<br />
    Know that you can also make the check slower but stricter by using [Smart Union](model_config.md#smart-union)

```py
from uuid import UUID
from typing import Union
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

However, as can be seen above, *pydantic* will attempt to 'match' any of the types defined under `Union` and will use
the first one that matches. In the above example the `id` of `user_03` was defined as a `uuid.UUID` class (which
is defined under the attribute's `Union` annotation) but as the `uuid.UUID` can be marshalled into an `int` it
chose to match against the `int` type and disregarded the other types.

!!! warning
    `typing.Union` also ignores order when [defined](https://docs.python.org/3/library/typing.html#typing.Union),
    so `Union[int, float] == Union[float, int]` which can lead to unexpected behaviour
    when combined with matching based on the `Union` type order inside other type definitions, such as `List` and `Dict`
    types (because Python treats these definitions as singletons).
    For example, `Dict[str, Union[int, float]] == Dict[str, Union[float, int]]` with the order based on the first time it was defined.
    Please note that this can also be [affected by third party libraries](https://github.com/pydantic/pydantic/issues/2835)
    and their internal type definitions and the import orders.

As such, it is recommended that, when defining `Union` annotations, the most specific type is included first and
followed by less specific types.

In the above example, the `UUID` class should precede the `int` and `str` classes to preclude the unexpected representation as such:

```py
from uuid import UUID
from typing import Union
from pydantic import BaseModel


class User(BaseModel):
    id: Union[UUID, int, str]
    name: str


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

    See more details in [Required Fields](models.md#required-fields).

#### Discriminated Unions (a.k.a. Tagged Unions)

When `Union` is used with multiple submodels, you sometimes know exactly which submodel needs to
be checked and validated and want to enforce this.
To do that you can set the same field - let's call it `my_discriminator` - in each of the submodels
with a discriminated value, which is one (or many) `Literal` value(s).
For your `Union`, you can set the discriminator in its value: `Field(discriminator='my_discriminator')`.

Setting a discriminated union has many benefits:

- validation is faster since it is only attempted against one model
- only one explicit error is raised in case of failure
- the generated JSON schema implements the [associated OpenAPI specification](https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.2.md#discriminatorObject)

```py test="requires-3.8"
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
    1 validation error for Lizard
    pet -> dog -> barks
      Field required [type=missing, input_value={'pet_type': 'dog'}, input_type=dict]
    """
```

!!! note
    Using the [Annotated Fields syntax](../schema/#typingannotated-fields) can be handy to regroup
    the `Union` and `discriminator` information. See below for an example!

!!! warning
    Discriminated unions cannot be used with only a single variant, such as `Union[Cat]`.

    Python changes `Union[T]` into `T` at interpretation time, so it is not possible for `pydantic` to
    distinguish fields of `Union[T]` from `T`.

#### Nested Discriminated Unions

Only one discriminator can be set for a field but sometimes you want to combine multiple discriminators.
In this case you can always create "intermediate" models with `__root__` and add your discriminator.

```py test="requires-3.8"
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


# Can also be written with a custom root type
#
# class Cat(BaseModel):
#   __root__: Annotated[Union[BlackCat, WhiteCat], Field(discriminator='color')]

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
    1 validation error for Dog
    pet -> cat
      Input tag 'red' found using 'color' does not match any of the expected tags: 'black', 'white' [type=union_tag_invalid, input_value={'pet_type': 'cat', 'color': 'red'}, input_type=dict]
    """
try:
    Model(pet={'pet_type': 'cat', 'color': 'black'}, n='1')
except ValidationError as e:
    print(e)
    """
    1 validation error for Dog
    pet -> cat -> black -> black_name
      Field required [type=missing, input_value={'pet_type': 'cat', 'color': 'black'}, input_type=dict]
    """
```

### Enums and Choices

*pydantic* uses Python's standard `enum` classes to define choices.

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
      Input should be 'pear' or 'banana' [type=literal_error, input_value='other', input_type=str]
    """
```


### Datetime Types

*Pydantic* supports the following [datetime](https://docs.python.org/library/datetime.html#available-types)
types:

* `datetime` fields can be:

  * `datetime`, existing `datetime` object
  * `int` or `float`, assumed as Unix time, i.e. seconds (if >= `-2e10` or <= `2e10`) or milliseconds (if < `-2e10`or > `2e10`) since 1 January 1970
  * `str`, following formats work:

    * `YYYY-MM-DD[T]HH:MM[:SS[.ffffff]][Z or [±]HH[:]MM]`
    * `int` or `float` as a string (assumed as Unix time)

* `date` fields can be:

  * `date`, existing `date` object
  * `int` or `float`, see `datetime`
  * `str`, following formats work:

    * `YYYY-MM-DD`
    * `int` or `float`, see `datetime`

* `time` fields can be:

  * `time`, existing `time` object
  * `str`, following formats work:

    * `HH:MM[:SS[.ffffff]][Z or [±]HH[:]MM]`

* `timedelta` fields can be:

  * `timedelta`, existing `timedelta` object
  * `int` or `float`, assumed as seconds
  * `str`, following formats work:

    * `[-][DD ][HH:MM]SS[.ffffff]`
    * `[±]P[DD]DT[HH]H[MM]M[SS]S` ([ISO 8601](https://en.wikipedia.org/wiki/ISO_8601) format for timedelta)

```py
from datetime import date, datetime, time, timedelta
from pydantic import BaseModel


class Model(BaseModel):
    d: date = None
    dt: datetime = None
    t: time = None
    td: timedelta = None


m = Model(
    d=1679616000.0,
    dt='2032-04-23T10:20:30.400+02:30',
    t=time(4, 8, 16),
    td='P3DT12H30M5S',
)

print(m.model_dump())
"""
{'d': datetime.date(2023, 3, 24), 'dt': datetime.datetime(2032, 4, 23, 10, 20, 30, 400000, tzinfo=TzInfo(+02:30)), 't': datetime.time(4, 8, 16), 'td': datetime.timedelta(days=3, seconds=45005)}
"""
```

### Booleans

!!! warning
    The logic for parsing `bool` fields has changed as of version **v1.0**.

    Prior to **v1.0**, `bool` parsing never failed, leading to some unexpected results.
    The new logic is described below.

A standard `bool` field will raise a `ValidationError` if the value is not one of the following:

* A valid boolean (i.e. `True` or `False`),
* The integers `0` or `1`,
* a `str` which when converted to lower case is one of
  `'0', 'off', 'f', 'false', 'n', 'no', '1', 'on', 't', 'true', 'y', 'yes'`
* a `bytes` which is valid (per the previous rule) when decoded to `str`

!!! note
    If you want stricter boolean logic (e.g. a field which only permits `True` and `False`) you can
    use [`StrictBool`](#strict-types).

Here is a script demonstrating some of these behaviors:

```py
from pydantic import BaseModel, ValidationError


class BooleanModel(BaseModel):
    bool_value: bool


print(BooleanModel(bool_value=False))
#> bool_value=False
print(BooleanModel(bool_value='False'))
#> bool_value=False
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

### Callable

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

### Type

*pydantic* supports the use of `Type[T]` to specify that a field may only accept classes (not instances)
that are subclasses of `T`.

```py
from typing import Type

from pydantic import BaseModel
from pydantic import ValidationError


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

### TypeVar

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

## Literal Type

!!! note
    This is a new feature of the Python standard library as of Python 3.8;
    prior to Python 3.8, it requires the [typing-extensions](https://pypi.org/project/typing-extensions/) package.

*pydantic* supports the use of `typing.Literal` (or `typing_extensions.Literal` prior to Python 3.8)
as a lightweight way to specify that a field may accept only specific literal values:

```py test="requires-3.8"
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

```py test="requires-3.8"
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
    2 validation errors for IceCream
    dessert -> Cake -> kind
      Input should be 'cake' [type=literal_error, input_value='pie', input_type=str]
    dessert -> IceCream -> kind
      Input should be 'icecream' [type=literal_error, input_value='pie', input_type=str]
    """
```

With proper ordering in an annotated `Union`, you can use this to parse types of decreasing specificity:

```py test="requires-3.8"
from typing import Optional, Literal, Union

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

## Annotated Types

### NamedTuple

```py
from typing import NamedTuple

from pydantic import BaseModel, ValidationError


class Point(NamedTuple):
    x: int
    y: int


class Model(BaseModel):
    p: Point


print(Model(p=('1', '2')))
#> p=Point(x=1, y=2)

try:
    Model(p=('1.3', '2'))
except ValidationError as e:
    print(e)
    """
    1 validation error for Model
    p -> arguments -> 0
      Input should be a valid integer, got a number with a fractional part [type=int_from_float, input_value='1.3', input_type=str]
    """
```

### TypedDict

!!! note
    This is a new feature of the Python standard library as of Python 3.8.
    Prior to Python 3.8, it requires the [typing-extensions](https://pypi.org/project/typing-extensions/) package.
    But required and optional fields are properly differentiated only since Python 3.9.
    We therefore recommend using [typing-extensions](https://pypi.org/project/typing-extensions/) with Python 3.8 as well.


```py
from typing_extensions import TypedDict

from pydantic import BaseModel, Extra, ValidationError


# `total=False` means keys are non-required
class UserIdentity(TypedDict, total=False):
    name: str
    surname: str


class User(TypedDict):
    identity: UserIdentity
    age: int


class Model(BaseModel):
    model_config = dict(extra=Extra.forbid)
    u: User


print(Model(u={'identity': {'name': 'Smith', 'surname': 'John'}, 'age': '37'}))
#> u={'identity': {'name': 'Smith', 'surname': 'John'}, 'age': 37}

print(Model(u={'identity': {'surname': 'John'}, 'age': '37'}))
#> u={'identity': {'surname': 'John'}, 'age': 37}

print(Model(u={'identity': {}, 'age': '37'}))
#> u={'identity': {}, 'age': 37}


try:
    Model(u={'identity': {'name': ['Smith'], 'surname': 'John'}, 'age': '24'})
except ValidationError as e:
    print(e)
    """
    1 validation error for Model
    u -> identity -> name
      Input should be a valid string [type=string_type, input_value=['Smith'], input_type=list]
    """

try:
    Model(
        u={
            'identity': {'name': 'Smith', 'surname': 'John'},
            'age': '37',
            'email': 'john.smith@me.com',
        }
    )
except ValidationError as e:
    print(e)
    """
    1 validation error for Model
    u -> email
      Extra inputs are not permitted [type=extra_forbidden, input_value='john.smith@me.com', input_type=str]
    """
```

## Pydantic Types

*pydantic* also provides a variety of other useful types:

`FilePath`
: like `Path`, but the path must exist and be a file

`DirectoryPath`
: like `Path`, but the path must exist and be a directory

`PastDate`
: like `date`, but the date should be in the past

`FutureDate`
: like `date`, but the date should be in the future

`AwareDatetime`
: like `datetime`, but requires the value to have timezone info

`NaiveDatetime`
: like `datetime`, but requires the value to lack timezone info

`EmailStr`
: requires [email-validator](https://github.com/JoshData/python-email-validator) to be installed;
  the input string must be a valid email address, and the output is a simple string



`NameEmail`
: requires [email-validator](https://github.com/JoshData/python-email-validator) to be installed;
  the input string must be either a valid email address or in the format `Fred Bloggs <fred.bloggs@example.com>`,
  and the output is a `NameEmail` object which has two properties: `name` and `email`.
  For `Fred Bloggs <fred.bloggs@example.com>` the name would be `"Fred Bloggs"`;
  for `fred.bloggs@example.com` it would be `"fred.bloggs"`.


`ImportString`
: expects a string and loads the Python object importable at that dotted path; e.g. if `'math.cos'` was provided,
the resulting field value would be the function `cos`; see [ImportString](#importstring)


`Color`
: for parsing HTML and CSS colors; see [Color Type](#color-type)

`Json`
: a special type wrapper which loads JSON before parsing; see [JSON Type](#json-type)

`PaymentCardNumber`
: for parsing and validating payment cards; see [payment cards](#payment-card-numbers)

`AnyUrl`
: any URL; see [URLs](#urls)

`AnyHttpUrl`
: an HTTP URL; see [URLs](#urls)

`HttpUrl`
: a stricter HTTP URL; see [URLs](#urls)

`FileUrl`
: a file path URL; see [URLs](#urls)

`PostgresDsn`
: a postgres DSN style URL; see [URLs](#urls)

`MysqlDsn`
: a mysql DSN style URL; see [URLs](#urls)

`MariaDsn`
: a mariadb DSN style URL; see [URLs](#urls)

`CockroachDsn`
: a cockroachdb DSN style URL; see [URLs](#urls)

`AmqpDsn`
: an `AMQP` DSN style URL as used by RabbitMQ, StormMQ, ActiveMQ etc.; see [URLs](#urls)

`RedisDsn`
: a redis DSN style URL; see [URLs](#urls)

`MongoDsn`
: a MongoDB DSN style URL; see [URLs](#urls)

`KafkaDsn`
: a kafka DSN style URL; see [URLs](#urls)

`stricturl`
: a type method for arbitrary URL constraints; see [URLs](#urls)

`UUID1`
: requires a valid UUID of type 1; see `UUID` [above](#standard-library-types)

`UUID3`
: requires a valid UUID of type 3; see `UUID` [above](#standard-library-types)

`UUID4`
: requires a valid UUID of type 4; see `UUID` [above](#standard-library-types)

`UUID5`
: requires a valid UUID of type 5; see `UUID` [above](#standard-library-types)

`SecretBytes`
: bytes where the value is kept partially secret; see [Secrets](#secret-types)

`SecretStr`
: string where the value is kept partially secret; see [Secrets](#secret-types)

`IPvAnyAddress`
: allows either an `IPv4Address` or an `IPv6Address`

`IPvAnyInterface`
: allows either an `IPv4Interface` or an `IPv6Interface`

`IPvAnyNetwork`
: allows either an `IPv4Network` or an `IPv6Network`

`NegativeFloat`
: allows a float which is negative; uses standard `float` parsing then checks the value is less than 0;
  see [Constrained Types](#constrained-types)

`NegativeInt`
: allows an int which is negative; uses standard `int` parsing then checks the value is less than 0;
  see [Constrained Types](#constrained-types)

`PositiveFloat`
: allows a float which is positive; uses standard `float` parsing then checks the value is greater than 0;
  see [Constrained Types](#constrained-types)

`PositiveInt`
: allows an int which is positive; uses standard `int` parsing then checks the value is greater than 0;
  see [Constrained Types](#constrained-types)

`conbytes`
: type method for constraining bytes;
  see [Constrained Types](#constrained-types)

`condecimal`
: type method for constraining Decimals;
  see [Constrained Types](#constrained-types)

`confloat`
: type method for constraining floats;
  see [Constrained Types](#constrained-types)

`conint`
: type method for constraining ints;
  see [Constrained Types](#constrained-types)

`condate`
: type method for constraining dates;
  see [Constrained Types](#constrained-types)

`conlist`
: type method for constraining lists;
  see [Constrained Types](#constrained-types)

`conset`
: type method for constraining sets;
  see [Constrained Types](#constrained-types)

`confrozenset`
: type method for constraining frozen sets;
  see [Constrained Types](#constrained-types)

`constr`
: type method for constraining strs;
  see [Constrained Types](#constrained-types)

### Exotic Types
Pydantic also supports exotic types, which are described in detail below:

#### ImportString
On model instantiation, pointers will be evaluated and imported. There is
some nuance to this behavior, demonstrated in the examples below.

> A known limitation: setting a default value to a string
> won't result in validation (thus evaluation). This is actively
> being worked on.

**Good behavior:**
```py
from pydantic import BaseModel, ImportString, ValidationError


class ImportThings(BaseModel):
    obj: ImportString


# A string value will cause an automatic import
my_cos = ImportThings(obj='math.cos')

# You can use the imported function as you would expect
cos_of_0 = my_cos.obj(0)
assert cos_of_0 == 1


# A string whose value cannot be imported will raise an error
try:
    ImportThings(obj='foo.bar')
except ValidationError as e:
    print(e)
    """
    1 validation error for ImportThings
    obj
      Invalid python path: No module named 'foo' [type=import_error, input_value='foo.bar', input_type=str]
    """


# TODO sort out the module name here
# # An object defined in the current namespace can indeed be imported,
# # though you should probably avoid doing this (since the ordering of declaration
# # can have an impact on behavior).
# class Foo:
#     bar = 1
#
#
# # This now works
# my_foo = ImportThings(obj=Foo)
# # So does this
# my_foo_2 = ImportThings(obj='__main__.Foo')


# Actual python objects can be assigned as well
from math import cos  # noqa: E402

my_cos = ImportThings(obj=cos)
my_cos_2 = ImportThings(obj='math.cos')
assert my_cos == my_cos_2
```

**Serializing an `ImportString` type to json is possible with a
[custom encoder](exporting_models.md#json_encoders) which accounts for
the evaluated object:**
```py test="xfail - replace json_encoders"
from pydantic import BaseModel, ImportString
from types import BuiltinFunctionType


# The following class will not successfully serialize to JSON
# Since "obj" is evaluated to an object, not a pydantic `ImportString`
class WithCustomEncodersBad(BaseModel):
    obj: ImportString

    class Config:
        json_encoders = {ImportString: lambda x: str(x)}


# Create an instance
m = WithCustomEncodersBad(obj='math.cos')

try:
    m.json()
except TypeError as e:
    print(e)

# Let's do some sanity checks to verify that m.obj is not an "ImportString"
print(isinstance(m.obj, ImportString))
print(isinstance(m.obj, BuiltinFunctionType))


# So now that we know that after an ImportString is evaluated by Pydantic
# it results in its underlying object, we can configure our json encoder
# to account for those specific types
class WithCustomEncodersGood(BaseModel):
    obj: ImportString

    class Config:
        json_encoders = {BuiltinFunctionType: lambda x: str(x)}


m = WithCustomEncodersGood(obj='math.cos')
print(m.json())
```

### URLs

For URI/URL validation the following types are available:

- `AnyUrl`: any scheme allowed, TLD not required, host required
- `AnyHttpUrl`: scheme `http` or `https`, TLD not required, host required
- `HttpUrl`: scheme `http` or `https`, TLD required, host required, max length 2083
- `FileUrl`: scheme `file`, host not required
- `PostgresDsn`: user info required, TLD not required, host required,
  as of V.10 `PostgresDsn` supports multiple hosts. The following schemes are supported:
  - `postgres`
  - `postgresql`
  - `postgresql+asyncpg`
  - `postgresql+pg8000`
  - `postgresql+psycopg`
  - `postgresql+psycopg2`
  - `postgresql+psycopg2cffi`
  - `postgresql+py-postgresql`
  - `postgresql+pygresql`
- `MySQLDsn`: scheme `mysql`, user info required, TLD not required, host required. Also, its supported DBAPI dialects:
  - `mysql`
  - `mysql+mysqlconnector`
  - `mysql+aiomysql`
  - `mysql+asyncmy`
  - `mysql+mysqldb`
  - `mysql+pymysql`
  - `mysql+cymysql`
  - `mysql+pyodbc`
- `MariaDBDsn`: scheme `mariadb`, user info required, TLD not required, host required. Also, its supported DBAPI dialects:
  - `mariadb`
  - `mariadb+mariadbconnector`
  - `mariadb+pymysql`
- `CockroachDsn`: scheme `cockroachdb`, user info required, TLD not required, host required. Also, its supported DBAPI dialects:
  - `cockroachdb+asyncpg`
  - `cockroachdb+psycopg2`
- `AmqpDsn`: schema `amqp` or `amqps`, user info not required, TLD not required, host not required
- `RedisDsn`: scheme `redis` or `rediss`, user info not required, tld not required, host not required (CHANGED: user info) (e.g., `rediss://:pass@localhost`)
- `MongoDsn` : scheme `mongodb`, user info not required, database name not required, port
  not required from **v1.6** onwards), user info may be passed without user part (e.g., `mongodb://mongodb0.example.com:27017`)
- `stricturl`: method with the following keyword arguments:
    - `strip_whitespace: bool = True`
    - `min_length: int = 1`
    - `max_length: int = 2 ** 16`
    - `tld_required: bool = True`
    - `host_required: bool = True`
    - `allowed_schemes: Optional[Set[str]] = None`

!!! warning
    In V1.10.0 and v1.10.1 `stricturl` also took an optional `quote_plus` argument and URL components were percent
    encoded in some cases. This feature was removed in v1.10.2, see
    [#4470](https://github.com/pydantic/pydantic/pull/4470) for explanation and more details.

The above types (which all inherit from `AnyUrl`) will attempt to give descriptive errors when invalid URLs are
provided:

```py
from pydantic import BaseModel, HttpUrl, ValidationError


class MyModel(BaseModel):
    url: HttpUrl


m = MyModel(url='http://www.example.com')
print(m.url)
#> http://www.example.com/

try:
    MyModel(url='ftp://invalid.url')
except ValidationError as e:
    print(e)
    """
    1 validation error for MyModel
    url
      URL scheme should be 'http' or 'https' [type=url_scheme, input_value='ftp://invalid.url', input_type=str]
    """

try:
    MyModel(url='not a url')
except ValidationError as e:
    print(e)
    """
    1 validation error for MyModel
    url
      Input should be a valid URL, relative URL without a base [type=url_parsing, input_value='not a url', input_type=str]
    """
```

If you require a custom URI/URL type, it can be created in a similar way to the types defined above.

#### URL Properties

Assuming an input URL of `http://samuel:pass@example.com:8000/the/path/?query=here#fragment=is;this=bit`,
the above types export the following properties:

- `scheme`: always set - the url scheme (`http` above)
- `host`: always set - the url host (`example.com` above)
- `host_type`: always set - describes the type of host, either:

  - `domain`: e.g. `example.com`,
  - `int_domain`: international domain, see [below](#international-domains), e.g. `exampl£e.org`,
  - `ipv4`: an IP V4 address, e.g. `127.0.0.1`, or
  - `ipv6`: an IP V6 address, e.g. `2001:db8:ff00:42`

- `user`: optional - the username if included (`samuel` above)
- `password`: optional - the password if included (`pass` above)
- `tld`: optional - the top level domain (`com` above),
  **Note: this will be wrong for any two-level domain, e.g. "co.uk".** You'll need to implement your own list of TLDs
  if you require full TLD validation
- `port`: optional - the port (`8000` above)
- `path`: optional - the path (`/the/path/` above)
- `query`: optional - the URL query (aka GET arguments or "search string") (`query=here` above)
- `fragment`: optional - the fragment (`fragment=is;this=bit` above)

If further validation is required, these properties can be used by validators to enforce specific behaviour:

```py
from pydantic import BaseModel, HttpUrl, PostgresDsn, ValidationError, field_validator


class MyModel(BaseModel):
    url: HttpUrl


m = MyModel(url='http://www.example.com')

# the repr() method for a url will display all properties of the url
print(repr(m.url))
#> Url('http://www.example.com/')
print(m.url.scheme)
#> http
print(m.url.host)
#> www.example.com
print(m.url.port)
#> 80


class MyDatabaseModel(BaseModel):
    db: PostgresDsn

    @field_validator('db')
    def check_db_name(cls, v):
        assert v.path and len(v.path) > 1, 'database must be provided'
        return v


m = MyDatabaseModel(db='postgres://user:pass@localhost:5432/foobar')
print(m.db)
#> postgres://user:pass@localhost:5432/foobar

try:
    MyDatabaseModel(db='postgres://user:pass@localhost:5432')
except ValidationError:
    pass
    # TODO the error output here is wrong!
    # print(e)
```

#### International Domains

"International domains" (e.g. a URL where the host or TLD includes non-ascii characters) will be encoded via
[punycode](https://en.wikipedia.org/wiki/Punycode) (see
[this article](https://www.xudongz.com/blog/2017/idn-phishing/) for a good description of why this is important):

```py
from pydantic import BaseModel, HttpUrl


class MyModel(BaseModel):
    url: HttpUrl


m1 = MyModel(url='http://puny£code.com')
print(m1.url)
#> http://xn--punycode-eja.com/
m2 = MyModel(url='https://www.аррӏе.com/')
print(m2.url)
#> https://www.xn--80ak6aa92e.com/
m3 = MyModel(url='https://www.example.珠宝/')
print(m3.url)
#> https://www.example.xn--pbt977c/
```


!!! warning
    #### Underscores in Hostnames

    In *pydantic* underscores are allowed in all parts of a domain except the tld.
    Technically this might be wrong - in theory the hostname cannot have underscores, but subdomains can.

    To explain this; consider the following two cases:

    - `exam_ple.co.uk`: the hostname is `exam_ple`, which should not be allowed since it contains an underscore
    - `foo_bar.example.com` the hostname is `example`, which should be allowed since the underscore is in the subdomain

    Without having an exhaustive list of TLDs, it would be impossible to differentiate between these two. Therefore
    underscores are allowed, but you can always do further validation in a validator if desired.

    Also, Chrome, Firefox, and Safari all currently accept `http://exam_ple.com` as a URL, so we're in good
    (or at least big) company.


### Color Type

You can use the `Color` data type for storing colors as per
[CSS3 specification](http://www.w3.org/TR/css3-color/#svg-color). Colors can be defined via:

- [name](http://www.w3.org/TR/SVG11/types.html#ColorKeywords) (e.g. `"Black"`, `"azure"`)
- [hexadecimal value](https://en.wikipedia.org/wiki/Web_colors#Hex_triplet)
  (e.g. `"0x000"`, `"#FFFFFF"`, `"7fffd4"`)
- RGB/RGBA tuples (e.g. `(255, 255, 255)`, `(255, 255, 255, 0.5)`)
- [RGB/RGBA strings](https://developer.mozilla.org/en-US/docs/Web/CSS/color_value#RGB_colors)
  (e.g. `"rgb(255, 255, 255)"`, `"rgba(255, 255, 255, 0.5)"`)
- [HSL strings](https://developer.mozilla.org/en-US/docs/Web/CSS/color_value#HSL_colors)
  (e.g. `"hsl(270, 60%, 70%)"`, `"hsl(270, 60%, 70%, .5)"`)

```py
from pydantic import BaseModel, ValidationError
from pydantic.color import Color

c = Color('ff00ff')
print(c.as_named())
#> magenta
print(c.as_hex())
#> #f0f
c2 = Color('green')
print(c2.as_rgb_tuple())
#> (0, 128, 0)
print(c2.original())
#> green
print(repr(Color('hsl(180, 100%, 50%)')))
#> Color('cyan', rgb=(0, 255, 255))


class Model(BaseModel):
    color: Color


print(Model(color='purple'))
#> color=Color('purple', rgb=(128, 0, 128))
try:
    Model(color='hello')
except ValidationError as e:
    print(e)
    """
    1 validation error for Model
    color
      value is not a valid color: string not recognised as a valid color [type=color_error, input_value='hello', input_type=str]
    """
```

`Color` has the following methods:

**`original`**
: the original string or tuple passed to `Color`

**`as_named`**
: returns a named CSS3 color; fails if the alpha channel is set or no such color exists unless
  `fallback=True` is supplied, in which case it falls back to `as_hex`

**`as_hex`**
: returns a string in the format `#fff` or `#ffffff`; will contain 4 (or 8) hex values if the alpha channel is set,
  e.g. `#7f33cc26`

**`as_rgb`**
: returns a string in the format `rgb(<red>, <green>, <blue>)`, or `rgba(<red>, <green>, <blue>, <alpha>)`
  if the alpha channel is set

**`as_rgb_tuple`**
: returns a 3- or 4-tuple in RGB(a) format. The `alpha` keyword argument can be used to define whether
  the alpha channel should be included;
  options: `True` - always include, `False` - never include, `None` (default) - include if set

**`as_hsl`**
: string in the format `hsl(<hue deg>, <saturation %>, <lightness %>)`
  or `hsl(<hue deg>, <saturation %>, <lightness %>, <alpha>)` if the alpha channel is set

**`as_hsl_tuple`**
: returns a 3- or 4-tuple in HSL(a) format. The `alpha` keyword argument can be used to define whether
  the alpha channel should be included;
  options: `True` - always include, `False` - never include, `None` (the default)  - include if set

The `__str__` method for `Color` returns `self.as_named(fallback=True)`.

!!! note
    the `as_hsl*` refer to hue, saturation, lightness "HSL" as used in html and most of the world, **not**
    "HLS" as used in Python's `colorsys`.

### Secret Types

You can use the `SecretStr` and the `SecretBytes` data types for storing sensitive information
that you do not want to be visible in logging or tracebacks.
`SecretStr` and `SecretBytes` can be initialized idempotently or by using `str` or `bytes` literals respectively.
The `SecretStr` and `SecretBytes` will be formatted as either `'**********'` or `''` on conversion to json.

```py test="xfail - replace json_encoders"
from pydantic import BaseModel, SecretStr, SecretBytes, ValidationError


class SimpleModel(BaseModel):
    password: SecretStr
    password_bytes: SecretBytes


sm = SimpleModel(password='IAmSensitive', password_bytes=b'IAmSensitiveBytes')

# Standard access methods will not display the secret
print(sm)
print(sm.password)
print(sm.model_dump())
print(sm.model_dump_json())

# Use get_secret_value method to see the secret's content.
print(sm.password.get_secret_value())
print(sm.password_bytes.get_secret_value())

try:
    SimpleModel(password=[1, 2, 3], password_bytes=[1, 2, 3])
except ValidationError as e:
    print(e)


# If you want the secret to be dumped as plain-text using the json method,
# you can use json_encoders in the Config class.
class SimpleModelDumpable(BaseModel):
    password: SecretStr
    password_bytes: SecretBytes

    class Config:
        json_encoders = {
            SecretStr: lambda v: v.get_secret_value() if v else None,
            SecretBytes: lambda v: v.get_secret_value() if v else None,
        }


sm2 = SimpleModelDumpable(password='IAmSensitive', password_bytes=b'IAmSensitiveBytes')

# Standard access methods will not display the secret
print(sm2)
print(sm2.password)
print(sm2.model_dump())

# But the json method will
print(sm2.model_dump_json())
```

### Json Type

You can use `Json` data type to make *pydantic* first load a raw JSON string.
It can also optionally be used to parse the loaded object into another type base on
the type `Json` is parameterised with:

```py
from typing import Any, List

from pydantic import BaseModel, Json, ValidationError


class AnyJsonModel(BaseModel):
    json_obj: Json[Any]


class ConstrainedJsonModel(BaseModel):
    json_obj: Json[List[int]]


print(AnyJsonModel(json_obj='{"b": 1}'))
#> json_obj={'b': 1}
print(ConstrainedJsonModel(json_obj='[1, 2, 3]'))
#> json_obj=[1, 2, 3]
try:
    ConstrainedJsonModel(json_obj=12)
except ValidationError as e:
    print(e)
    """
    1 validation error for ConstrainedJsonModel
    json_obj
      JSON input should be string, bytes or bytearray [type=json_type, input_value=12, input_type=int]
    """

try:
    ConstrainedJsonModel(json_obj='[a, b]')
except ValidationError as e:
    print(e)
    """
    1 validation error for ConstrainedJsonModel
    json_obj
      Invalid JSON: expected value at line 1 column 2 [type=json_invalid, input_value='[a, b]', input_type=str]
    """

try:
    ConstrainedJsonModel(json_obj='["a", "b"]')
except ValidationError as e:
    print(e)
    """
    2 validation errors for ConstrainedJsonModel
    json_obj -> 0
      Input should be a valid integer, unable to parse string as an integer [type=int_parsing, input_value='a', input_type=str]
    json_obj -> 1
      Input should be a valid integer, unable to parse string as an integer [type=int_parsing, input_value='b', input_type=str]
    """
```

### Payment Card Numbers

The `PaymentCardNumber` type validates [payment cards](https://en.wikipedia.org/wiki/Payment_card)
(such as a debit or credit card).

```py
from datetime import date

from pydantic import BaseModel
from pydantic.types import PaymentCardBrand, PaymentCardNumber, constr


class Card(BaseModel):
    name: constr(strip_whitespace=True, min_length=1)
    number: PaymentCardNumber
    exp: date

    @property
    def brand(self) -> PaymentCardBrand:
        return self.number.brand

    @property
    def expired(self) -> bool:
        return self.exp < date.today()


card = Card(
    name='Georg Wilhelm Friedrich Hegel',
    number='4000000000000002',
    exp=date(2023, 9, 30),
)

assert card.number.brand == PaymentCardBrand.visa
assert card.number.bin == '400000'
assert card.number.last4 == '0002'
assert card.number.masked == '400000******0002'
```

`PaymentCardBrand` can be one of the following based on the BIN:

* `PaymentCardBrand.amex`
* `PaymentCardBrand.mastercard`
* `PaymentCardBrand.visa`
* `PaymentCardBrand.other`

The actual validation verifies the card number is:

* a `str` of only digits
* [luhn](https://en.wikipedia.org/wiki/Luhn_algorithm) valid
* the correct length based on the BIN, if Amex, Mastercard or Visa, and between
  12 and 19 digits for all other brands

## Constrained Types

The value of numerous common types can be restricted using `con*` type functions:

```py
from decimal import Decimal

from pydantic import (
    BaseModel,
    NegativeFloat,
    NegativeInt,
    PositiveFloat,
    PositiveInt,
    NonNegativeFloat,
    NonNegativeInt,
    NonPositiveFloat,
    NonPositiveInt,
    conbytes,
    condecimal,
    confloat,
    conint,
    conlist,
    conset,
    constr,
    Field,
)


class Model(BaseModel):
    short_bytes: conbytes(min_length=2, max_length=10)
    strict_bytes: conbytes(strict=True)

    upper_str: constr(to_upper=True)
    lower_str: constr(to_lower=True)
    short_str: constr(min_length=2, max_length=10)
    regex_str: constr(pattern=r'^apple (pie|tart|sandwich)$')
    strip_str: constr(strip_whitespace=True)

    big_int: conint(gt=1000, lt=1024)
    mod_int: conint(multiple_of=5)
    pos_int: PositiveInt
    neg_int: NegativeInt
    non_neg_int: NonNegativeInt
    non_pos_int: NonPositiveInt

    big_float: confloat(gt=1000, lt=1024)
    unit_interval: confloat(ge=0, le=1)
    mod_float: confloat(multiple_of=0.5)
    pos_float: PositiveFloat
    neg_float: NegativeFloat
    non_neg_float: NonNegativeFloat
    non_pos_float: NonPositiveFloat

    short_list: conlist(int, min_length=1, max_length=4)
    short_set: conset(int, min_length=1, max_length=4)

    decimal_positive: condecimal(gt=0)
    decimal_negative: condecimal(lt=0)
    decimal_max_digits_and_places: condecimal(max_digits=2, decimal_places=2)
    mod_decimal: condecimal(multiple_of=Decimal('0.25'))

    bigger_int: int = Field(..., gt=10000)
```

Where `Field` refers to the [field function](schema.md#field-customization).

### Arguments to `conlist`
The following arguments are available when using the `conlist` type function

- `item_type: Type[T]`: type of the list items
- `min_items: int = None`: minimum number of items in the list
- `max_items: int = None`: maximum number of items in the list
- `unique_items: bool = None`: enforces list elements to be unique

### Arguments to `conset`
The following arguments are available when using the `conset` type function

- `item_type: Type[T]`: type of the set items
- `min_items: int = None`: minimum number of items in the set
- `max_items: int = None`: maximum number of items in the set

### Arguments to `confrozenset`
The following arguments are available when using the `confrozenset` type function

- `item_type: Type[T]`: type of the frozenset items
- `min_items: int = None`: minimum number of items in the frozenset
- `max_items: int = None`: maximum number of items in the frozenset

### Arguments to `conint`
The following arguments are available when using the `conint` type function

- `strict: bool = False`: controls type coercion
- `gt: int = None`: enforces integer to be greater than the set value
- `ge: int = None`: enforces integer to be greater than or equal to the set value
- `lt: int = None`: enforces integer to be less than the set value
- `le: int = None`: enforces integer to be less than or equal to the set value
- `multiple_of: int = None`: enforces integer to be a multiple of the set value

### Arguments to `confloat`
The following arguments are available when using the `confloat` type function

- `strict: bool = False`: controls type coercion
- `gt: float = None`: enforces float to be greater than the set value
- `ge: float = None`: enforces float to be greater than or equal to the set value
- `lt: float = None`: enforces float to be less than the set value
- `le: float = None`: enforces float to be less than or equal to the set value
- `multiple_of: float = None`: enforces float to be a multiple of the set value
- `allow_inf_nan: bool = True`: whether to allows infinity (`+inf` an `-inf`) and NaN values, defaults to `True`,
  set to `False` for compatibility with `JSON`,
  see [#3994](https://github.com/pydantic/pydantic/pull/3994) for more details, added in **V1.10**

### Arguments to `condecimal`
The following arguments are available when using the `condecimal` type function

- `gt: Decimal = None`: enforces decimal to be greater than the set value
- `ge: Decimal = None`: enforces decimal to be greater than or equal to the set value
- `lt: Decimal = None`: enforces decimal to be less than the set value
- `le: Decimal = None`: enforces decimal to be less than or equal to the set value
- `max_digits: int = None`: maximum number of digits within the decimal. it does not include a zero before the decimal point or trailing decimal zeroes
- `decimal_places: int = None`: max number of decimal places allowed. it does not include trailing decimal zeroes
- `multiple_of: Decimal = None`: enforces decimal to be a multiple of the set value

### Arguments to `constr`
The following arguments are available when using the `constr` type function

- `strip_whitespace: bool = False`: removes leading and trailing whitespace
- `to_upper: bool = False`: turns all characters to uppercase
- `to_lower: bool = False`: turns all characters to lowercase
- `strict: bool = False`: controls type coercion
- `min_length: int = None`: minimum length of the string
- `max_length: int = None`: maximum length of the string
- `curtail_length: int = None`: shrinks the string length to the set value when it is longer than the set value
- `regex: str = None`: regex to validate the string against

### Arguments to `conbytes`
The following arguments are available when using the `conbytes` type function

- `strip_whitespace: bool = False`: removes leading and trailing whitespace
- `to_upper: bool = False`: turns all characters to uppercase
- `to_lower: bool = False`: turns all characters to lowercase
- `min_length: int = None`: minimum length of the byte string
- `max_length: int = None`: maximum length of the byte string
- `strict: bool = False`: controls type coercion

### Arguments to `condate`
The following arguments are available when using the `condate` type function

- `gt: date = None`: enforces date to be greater than the set value
- `ge: date = None`: enforces date to be greater than or equal to the set value
- `lt: date = None`: enforces date to be less than the set value
- `le: date = None`: enforces date to be less than or equal to the set value


## Strict Types

You can use the `StrictStr`, `StrictBytes`, `StrictInt`, `StrictFloat`, and `StrictBool` types
to prevent coercion from compatible types.
These types will only pass validation when the validated value is of the respective type or is a subtype of that type.
This behavior is also exposed via the `strict` field of the `ConstrainedStr`, `ConstrainedBytes`,
`ConstrainedFloat` and `ConstrainedInt` classes and can be combined with a multitude of complex validation rules.

The following caveats apply:

- `StrictBytes` (and the `strict` option of `ConstrainedBytes`) will accept both `bytes`,
   and `bytearray` types.
- `StrictInt` (and the `strict` option of `ConstrainedInt`) will not accept `bool` types,
    even though `bool` is a subclass of `int` in Python. Other subclasses will work.
- `StrictFloat` (and the `strict` option of `ConstrainedFloat`) will not accept `int`.

```py
from pydantic import (
    BaseModel,
    StrictBytes,
    StrictBool,
    StrictInt,
    ValidationError,
    confloat,
)


class StrictBytesModel(BaseModel):
    strict_bytes: StrictBytes


try:
    StrictBytesModel(strict_bytes='hello world')
except ValidationError as e:
    print(e)
    """
    1 validation error for StrictBytesModel
    strict_bytes
      Input should be a valid bytes [type=bytes_type, input_value='hello world', input_type=str]
    """


class StrictIntModel(BaseModel):
    strict_int: StrictInt


try:
    StrictIntModel(strict_int=3.14159)
except ValidationError as e:
    print(e)
    """
    1 validation error for StrictIntModel
    strict_int
      Input should be a valid integer [type=int_type, input_value=3.14159, input_type=float]
    """


class ConstrainedFloatModel(BaseModel):
    constrained_float: confloat(strict=True, ge=0.0)


try:
    ConstrainedFloatModel(constrained_float=3)
except ValidationError as e:
    print(e)

try:
    ConstrainedFloatModel(constrained_float=-1.23)
except ValidationError as e:
    print(e)
    """
    1 validation error for ConstrainedFloatModel
    constrained_float
      Input should be greater than or equal to 0 [type=greater_than_equal, input_value=-1.23, input_type=float]
    """


class StrictBoolModel(BaseModel):
    strict_bool: StrictBool


try:
    StrictBoolModel(strict_bool='False')
except ValidationError as e:
    print(str(e))
    """
    1 validation error for StrictBoolModel
    strict_bool
      Input should be a valid boolean [type=bool_type, input_value='False', input_type=str]
    """
```

## ByteSize

You can use the `ByteSize` data type to convert byte string representation to
raw bytes and print out human readable versions of the bytes as well.

!!! info
    Note that `1b` will be parsed as "1 byte" and not "1 bit".

```py
from pydantic import BaseModel, ByteSize


class MyModel(BaseModel):
    size: ByteSize


print(MyModel(size=52000).size)
#> 52000
print(MyModel(size='3000 KiB').size)
#> 3072000

m = MyModel(size='50 PB')
print(m.size.human_readable())
#> 44.4PiB
print(m.size.human_readable(decimal=True))
#> 50.0PB

print(m.size.to('TiB'))
#> 45474.73508864641
```

## Custom Data Types

You can also define your own custom data types. There are several ways to achieve it.

### Classes with `__get_validators__`

You use a custom class with a classmethod `__get_validators__`. It will be called
to get validators to parse and validate the input data.

!!! tip
    These validators have the same semantics as in [Validators](validators.md), you can
    declare a parameter `config`, `field`, etc.

```py test="xfail - replace with Annoated[str, PostCodeLogic]"
import re
from pydantic import BaseModel

# https://en.wikipedia.org/wiki/Postcodes_in_the_United_Kingdom#Validation
post_code_regex = re.compile(
    r'(?:'
    r'([A-Z]{1,2}[0-9][A-Z0-9]?|ASCN|STHL|TDCU|BBND|[BFS]IQQ|PCRN|TKCA) ?'
    r'([0-9][A-Z]{2})|'
    r'(BFPO) ?([0-9]{1,4})|'
    r'(KY[0-9]|MSR|VG|AI)[ -]?[0-9]{4}|'
    r'([A-Z]{2}) ?([0-9]{2})|'
    r'(GE) ?(CX)|'
    r'(GIR) ?(0A{2})|'
    r'(SAN) ?(TA1)'
    r')'
)


class PostCode(str):
    """
    Partial UK postcode validation. Note: this is just an example, and is not
    intended for use in production; in particular this does NOT guarantee
    a postcode exists, just that it has a valid format.
    """

    @classmethod
    def __get_validators__(cls):
        # one or more validators may be yielded which will be called in the
        # order to validate the input, each validator will receive as an input
        # the value returned from the previous validator
        yield cls.validate

    @classmethod
    def __pydantic_modify_json_schema__(cls, field_schema):
        # __pydantic_modify_json_schema__ should mutate the dict it receives
        # in place, the returned value will be ignored
        field_schema.update(
            # simplified regex here for brevity, see the wikipedia link above
            pattern='^[A-Z]{1,2}[0-9][A-Z0-9]? ?[0-9][A-Z]{2}$',
            # some example postcodes
            examples=['SP11 9DG', 'w1j7bu'],
        )

    @classmethod
    def validate(cls, v):
        if not isinstance(v, str):
            raise TypeError('string required')
        m = post_code_regex.fullmatch(v.upper())
        if not m:
            raise ValueError('invalid postcode format')
        # you could also return a string here which would mean model.post_code
        # would be a string, pydantic won't care but you could end up with some
        # confusion since the value's type won't match the type annotation
        # exactly
        return cls(f'{m.group(1)} {m.group(2)}')

    def __repr__(self):
        return f'PostCode({super().__repr__()})'


class Model(BaseModel):
    post_code: PostCode


model = Model(post_code='sw8 5el')
print(model)
print(model.post_code)
print(Model.model_json_schema())
```

Similar validation could be achieved using [`constr(regex=...)`](#constrained-types) except the value won't be
formatted with a space, the schema would just include the full pattern and the returned value would be a vanilla string.

See [schema](schema.md) for more details on how the model's schema is generated.

### Arbitrary Types Allowed

You can allow arbitrary types using the `arbitrary_types_allowed` config in the
[Model Config](model_config.md).

```py
from pydantic import BaseModel, ValidationError


# This is not a pydantic model, it's an arbitrary class
class Pet:
    def __init__(self, name: str):
        self.name = name


class Model(BaseModel):
    model_config = dict(arbitrary_types_allowed=True)
    pet: Pet
    owner: str


pet = Pet(name='Hedwig')
# A simple check of instance type is used to validate the data
model = Model(owner='Harry', pet=pet)
print(model)
#> pet=<__main__.Pet object at 0x0123456789ab> owner='Harry'
print(model.pet)
#> <__main__.Pet object at 0x0123456789ab>
print(model.pet.name)
#> Hedwig
print(type(model.pet))
#> <class '__main__.Pet'>
try:
    # If the value is not an instance of the type, it's invalid
    Model(owner='Harry', pet='Hedwig')
except ValidationError as e:
    print(e)
    """
    1 validation error for Model
    pet
      Input should be an instance of Pet [type=is_instance_of, input_value='Hedwig', input_type=str]
    """
# Nothing in the instance of the arbitrary type is checked
# Here name probably should have been a str, but it's not validated
pet2 = Pet(name=42)
model2 = Model(owner='Harry', pet=pet2)
print(model2)
#> pet=<__main__.Pet object at 0x0123456789ab> owner='Harry'
print(model2.pet)
#> <__main__.Pet object at 0x0123456789ab>
print(model2.pet.name)
#> 42
print(type(model2.pet))
#> <class '__main__.Pet'>
```

### Undefined Types Warning

You can suppress the Undefined Types Warning by setting `undefined_types_warning` to `False` in the
[Model Config](model_config.md).

```py test="xfail - what do we do with undefined_types_warning?"
from __future__ import annotations

from pydantic import BaseModel


# This example shows how Book and Person types reference each other.
# We will demonstrate how to suppress the undefined types warning
# when define such models.


class Book(BaseModel):
    title: str
    author: Person  # note the `Person` type is not yet defined

    # Suppress undefined types warning so we can continue defining our models.
    class Config:
        undefined_types_warning = False


class Person(BaseModel):
    name: str
    books_read: list[Book] | None = None


# Now, we can rebuild the `Book` model, since the `Person` model is now defined.
# Note: there's no need to call `model_rebuild()` on `Person`,
# it's already complete.
Book.model_rebuild()

# Let's create some instances of our models, to demonstrate that they work.
python_crash_course = Book(
    title='Python Crash Course',
    author=Person(name='Eric Matthes'),
)
jane_doe = Person(name='Jane Doe', books_read=[python_crash_course])

assert jane_doe.dict(exclude_unset=True) == {
    'name': 'Jane Doe',
    'books_read': [
        {
            'title': 'Python Crash Course',
            'author': {'name': 'Eric Matthes'},
        },
    ],
}
```

### Generic Classes as Types

!!! warning
    This is an advanced technique that you might not need in the beginning. In most of
    the cases you will probably be fine with standard *pydantic* models.

You can use
[Generic Classes](https://docs.python.org/3/library/typing.html#typing.Generic) as
field types and perform custom validation based on the "type parameters" (or sub-types)
with `__get_validators__`.

If the Generic class that you are using as a sub-type has a classmethod
`__get_validators__` you don't need to use `arbitrary_types_allowed` for it to work.

Because you can declare validators that receive the current `field`, you can extract
the `sub_fields` (from the generic class type parameters) and validate data with them.

```py test="xfail - what do we do with generic custom types"
from pydantic import BaseModel, ValidationError
from pydantic.fields import ModelField
from typing import TypeVar, Generic

AgedType = TypeVar('AgedType')
QualityType = TypeVar('QualityType')


# This is not a pydantic model, it's an arbitrary generic class
class TastingModel(Generic[AgedType, QualityType]):
    def __init__(self, name: str, aged: AgedType, quality: QualityType):
        self.name = name
        self.aged = aged
        self.quality = quality

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    # You don't need to add the "ModelField", but it will help your
    # editor give you completion and catch errors
    def validate(cls, v, field: ModelField):
        if not isinstance(v, cls):
            # The value is not even a TastingModel
            raise TypeError('Invalid value')
        if not field.sub_fields:
            # Generic parameters were not provided so we don't try to validate
            # them and just return the value as is
            return v
        aged_f = field.sub_fields[0]
        quality_f = field.sub_fields[1]
        errors = []
        # Here we don't need the validated value, but we want the errors
        valid_value, error = aged_f.validate(v.aged, {}, loc='aged')
        if error:
            errors.append(error)
        # Here we don't need the validated value, but we want the errors
        valid_value, error = quality_f.validate(v.quality, {}, loc='quality')
        if error:
            errors.append(error)
        if errors:
            raise ValidationError(errors, cls)
        # Validation passed without errors, return the same instance received
        return v


class Model(BaseModel):
    # for wine, "aged" is an int with years, "quality" is a float
    wine: TastingModel[int, float]
    # for cheese, "aged" is a bool, "quality" is a str
    cheese: TastingModel[bool, str]
    # for thing, "aged" is a Any, "quality" is Any
    thing: TastingModel


model = Model(
    # This wine was aged for 20 years and has a quality of 85.6
    wine=TastingModel(name='Cabernet Sauvignon', aged=20, quality=85.6),
    # This cheese is aged (is mature) and has "Good" quality
    cheese=TastingModel(name='Gouda', aged=True, quality='Good'),
    # This Python thing has aged "Not much" and has a quality "Awesome"
    thing=TastingModel(name='Python', aged='Not much', quality='Awesome'),
)
print(model)
print(model.wine.aged)
print(model.wine.quality)
print(model.cheese.aged)
print(model.cheese.quality)
print(model.thing.aged)
try:
    # If the values of the sub-types are invalid, we get an error
    Model(
        # For wine, aged should be an int with the years, and quality a float
        wine=TastingModel(name='Merlot', aged=True, quality='Kinda good'),
        # For cheese, aged should be a bool, and quality a str
        cheese=TastingModel(name='Gouda', aged='yeah', quality=5),
        # For thing, no type parameters are declared, and we skipped validation
        # in those cases in the Assessment.validate() function
        thing=TastingModel(name='Python', aged='Not much', quality='Awesome'),
    )
except ValidationError as e:
    print(e)
```
