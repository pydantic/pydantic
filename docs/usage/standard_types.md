---
description: Support for common types from the Python standard library.
---

Pydantic supports many common types from the Python standard library. If you need stricter processing see
[Strict Types](/usage/strict/). If you need to constrain the values allowed (e.g. to require a positive `int`) see
[Constrained Types](/usage/constrained/).

| Type | Description |
| ---- | ----------- |
| `None`, `type(None)`, or `Literal[None]` | Equivalent according to [PEP 484](https://www.python.org/dev/peps/pep-0484/#using-none). Allows only `None` value. |
| `bool` | See [Booleans](/usage/booleans/) for details on how bools are validated and what values are permitted. |
| `int` | Pydantic uses `int(v)` to coerce types to an `int`. See the [Data Conversion](/usage/models/#data-conversion) warning on loss of information during data conversion. |
| `float` | `float(v)` is used to coerce values to floats. |
| `str` | Strings are accepted as-is. `int` `float` and `Decimal` are coerced using `str(v)`. `bytes` and `bytearray` are converted using `v.decode()`. `Enum`s inheriting from `str` are converted using `v.value`. All other types cause an error. |
| `bytes` | `bytes` are accepted as-is. `bytearray` is converted using `bytes(v)`. `str` are converted using `v.encode()`. `int`, `float`, and `Decimal` are coerced using `str(v).encode()`. |
| `list` | Allows `list`, `tuple`, `set`, `frozenset`, `deque`, or generators and casts to a list. See `typing.List` for sub-type constraints. |
| `tuple` | Allows `list`, `tuple`, `set`, `frozenset`, `deque`, or generators and casts to a tuple. See `typing.Tuple` for sub-type constraints. |
| `dict`| `dict(v)` is used to attempt to convert a dictionary. See `typing.Dict` for sub-type constraints. |
| `set` | Allows `list`, `tuple`, `set`, `frozenset`, `deque`, or generators and casts to a set. See `typing.Set` below for sub-type constraints. |
| `frozenset` | Allows `list`, `tuple`, `set`, `frozenset`, `deque`, or generators and casts to a frozen set. See `typing.FrozenSet` below for sub-type constraints. |
| `deque` | Allows `list`, `tuple`, `set`, `frozenset`, `deque`, or generators and casts to a deque. See `typing.Deque` below for sub-type constraints. |
| `datetime.date` | See [Datetime Types](/usage/datetime/) below for more detail on parsing and validation. |
| `datetime.time` | See [Datetime Types](/usage/datetime/) below for more detail on parsing and validation. |
| `datetime.datetime` | See [Datetime Types](/usage/datetime/) below for more detail on parsing and validation. |
| `datetime.timedelta` | See [Datetime Types](/usage/datetime/) below for more detail on parsing and validation. |
| `typing.Any` | Allows any value including `None`, thus an `Any` field is optional. |
| `typing.Annotated` | Allows wrapping another type with arbitrary metadata, as per [PEP-593](https://www.python.org/dev/peps/pep-0593/). The `Annotated` hint may contain a single call to the [`Field` function](/usage/schema/#typingannotated-fields), but otherwise the additional metadata is ignored and the root type is used. |
| `typing.TypeVar` | Constrains the values allowed based on `constraints` or `bound`, see [TypeVar](/usage/typevars/). |
| `typing.Union` | See [Unions](/usage/unions/) below for more detail on parsing and validation. |
| `typing.Optional` | `Optional[x]` is simply short hand for `Union[x, None]`. See [Unions](/usage/unions/) below for more detail on parsing and validation and [Required Fields](/usage/models/#required-fields) for details about required fields that can receive `None` as a value. |
| `typing.List` | See [Typing Iterables](/usage/typing_iterables/) below for more detail on parsing and validation. |
| `typing.Tuple` | See [Typing Iterables](/usage/typing_iterables/) below for more detail on parsing and validation. |
| Subclass of `typing.NamedTuple` | Same as `tuple`, but instantiates with the given namedtuple and validates fields since they are annotated. See [Annotated Types](/usage/annotated_types/) below for more detail on parsing and validation. |
| Subclass of `collections.namedtuple` | Same as subclass of `typing.NamedTuple`, but all fields will have type `Any` since they are not annotated. |
| `typing.Dict` | See [Typing Iterables](/usage/typing_iterables/) below for more detail on parsing and validation. |
| Subclass of `typing.TypedDict` | Same as `dict`, but Pydantic will validate the dictionary since keys are annotated. See [Annotated Types](/usage/annotated_types/) below for more detail on parsing and validation. |
| `typing.Set` | See [Typing Iterables](/usage/typing_iterables/) below for more detail on parsing and validation. |
| `typing.FrozenSet` | See [Typing Iterables](/usage/typing_iterables/) below for more detail on parsing and validation. |
| `typing.Deque` | See [Typing Iterables](/usage/typing_iterables/) below for more detail on parsing and validation. |
| `typing.Sequence` | See [Typing Iterables](/usage/typing_iterables/) below for more detail on parsing and validation. |
| `typing.Iterable` | This is reserved for iterables that shouldn't be consumed. See [Infinite Generators](/usage/typing_iterables/#infinite-generators) below for more detail on parsing and validation. |
| `typing.Type` | See [Type](/usage/typevars/#type) below for more detail on parsing and validation. |
| `typing.Callable` | See [Callables](/usage/callables/) below for more detail on parsing and validation. |
| `typing.Pattern` | Will cause the input value to be passed to `re.compile(v)` to create a regex pattern. |
| `ipaddress.IPv4Address` | Simply uses the type itself for validation by passing the value to `IPv4Address(v)`. See [Pydantic Types](/usage/pydantic_types/) for other custom IP address types. |
| <nobr>`ipaddress.IPv4Interface`</nobr> | Simply uses the type itself for validation by passing the value to `IPv4Address(v)`. See [Pydantic Types](/usage/pydantic_types/) for other custom IP address types. |
| `ipaddress.IPv4Network` | Simply uses the type itself for validation by passing the value to `IPv4Network(v)`. See [Pydantic Types](/usage/pydantic_types/) for other custom IP address types. |
| `ipaddress.IPv6Address` | Simply uses the type itself for validation by passing the value to `IPv6Address(v)`. See [Pydantic Types](/usage/pydantic_types/) for other custom IP address types. |
| `ipaddress.IPv6Interface` | Simply uses the type itself for validation by passing the value to `IPv6Interface(v)`. See [Pydantic Types](/usage/pydantic_types/) for other custom IP address types. |
| `ipaddress.IPv6Network` | Simply uses the type itself for validation by passing the value to `IPv6Network(v)`. See [Pydantic Types](/usage/pydantic_types/) for other custom IP address types. |
| `enum.Enum` | Checks that the value is a valid `Enum` instance. |
| Subclass of `enum.Enum` | Checks that the value is a valid member of the `enum`. See [Enums and Choices](/usage/enums/) for more details. |
| `enum.IntEnum` | Checks that the value is a valid `IntEnum` instance. |
| Subclass of `enum.IntEnum` | Checks that the value is a valid member of the integer `enum`. See [Enums and Choices](/usage/enums/) for more details. |
| `decimal.Decimal` | Pydantic attempts to convert the value to a string, then passes the string to `Decimal(v)`. |
| `pathlib.Path` | Simply uses the type itself for validation by passing the value to `Path(v)`. See [Pydantic Types](/usage/pydantic_types/) for other more strict path types. |
| `uuid.UUID` | Strings and bytes (converted to strings) are passed to `UUID(v)`, with a fallback to `UUID(bytes=v)` for `bytes` and `bytearray`. See [Pydantic Types](/usage/pydantic_types/) for other stricter UUID types. |
| `ByteSize` | Converts a bytes string with units to bytes. |

## Literal Type

!!! note
    This is a new feature of the Python standard library as of Python 3.8;
    prior to Python 3.8, it requires the [typing-extensions](https://pypi.org/project/typing-extensions/) package.

*pydantic* supports the use of `typing.Literal` (or `typing_extensions.Literal` prior to Python 3.8)
as a lightweight way to specify that a field may accept only specific literal values:

```py requires="3.8"
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

```py requires="3.8"
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

```py requires="3.8"
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