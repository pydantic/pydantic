---
description: Support for common types from the Python standard library.
---

| Type | Description |
| ---- | ----------- |
| `None`, `type(None)`, or `Literal[None]` | Equivalent according to [PEP 484](https://www.python.org/dev/peps/pep-0484/#using-none). Allows only `None` value. |
| `str` | Strings are accepted as-is. `bytes` and `bytearray` are converted using `v.decode()`. `Enum`s inheriting from `str` are converted using `v.value`. All other types cause an error. |
| `bytes` | `bytes` are accepted as-is. `bytearray` is converted using `bytes(v)`. `str` are converted using `v.encode()`. `int`, `float`, and `Decimal` are coerced using `str(v).encode()`. See [ByteSize](../../api/types.md#pydantic.types.ByteSize) for more details. |
| `list` | Allows `list`, `tuple`, `set`, `frozenset`, `deque`, or generators and casts to a list. See [`typing.List`](list_types.md) for sub-type constraints. |
| `tuple` | Allows `list`, `tuple`, `set`, `frozenset`, `deque`, or generators and casts to a tuple. See [`typing.Tuple`](list_types.md) for sub-type constraints. |
| `dict`| `dict(v)` is used to attempt to convert a dictionary. See [`typing.Dict`](dicts_mapping.md) for sub-type constraints. |
| `set` | Allows `list`, `tuple`, `set`, `frozenset`, `deque`, or generators and casts to a set. See [`typing.Set`](set_types.md) for sub-type constraints. |
| `frozenset` | Allows `list`, `tuple`, `set`, `frozenset`, `deque`, or generators and casts to a frozen set. See [`typing.FrozenSet`](set_types.md) for sub-type constraints. |
| `deque` | Allows `list`, `tuple`, `set`, `frozenset`, `deque`, or generators and casts to a deque. See [`typing.Deque`](list_types.md) for sub-type constraints. |
| `typing.Any` | Allows any value including `None`, thus an `Any` field is optional. |
| `typing.Annotated` | Allows wrapping another type with arbitrary metadata, as per [PEP-593](https://www.python.org/dev/peps/pep-0593/). The `Annotated` hint may contain a single call to the [`Field` function](../json_schema.md#typingannotated-fields), but otherwise the additional metadata is ignored and the root type is used. |
| `typing.TypeVar` | Constrains the values allowed based on `constraints` or `bound`, see [TypeVar](typevars.md). |
| `typing.Union` | See [Unions](unions.md) for more detail on parsing and validation. |
| `typing.Optional` | `Optional[x]` is simply short hand for `Union[x, None]`. See [Unions](unions.md) for more detail on parsing and validation and [Required Fields](../models.md#required-fields) for details about required fields that can receive `None` as a value. |
| `typing.List` | See [Lists and Tuples](list_types.md) for more detail on parsing and validation. |
| `typing.Tuple` | See [Lists and Tuples](list_types.md) for more detail on parsing and validation. |
| Subclass of `typing.NamedTuple` | Same as `tuple`, but instantiates with the given `namedtuple` and validates fields since they are annotated. See [Lists and Tuples](list_types.md) for more detail. |
| Subclass of `collections.namedtuple` | Same as subclass of `typing.NamedTuple`, but all fields will have type `Any` since they are not annotated. See [Lists and Tuples](list_types.md) for more detail. |
| `typing.Dict` | See [Dicts and mapping](dicts_mapping.md) for more detail on parsing and validation. |
| Subclass of `typing.TypedDict` | Same as `dict`, but Pydantic will validate the dictionary since keys are annotated. |
| `typing.Set` | See [Sets and frozenset](set_types.md) for more detail on parsing and validation. |
| `typing.FrozenSet` | See [Sets and frozenset](set_types.md) for more detail on parsing and validation. |
| `typing.Deque` | See [Sequence, Iterable & Iterator](sequence_iterable.md) for more detail on parsing and validation. |
| `typing.Sequence` | See [Sequence, Iterable & Iterator](sequence_iterable.md) for more detail on parsing and validation. |
| `typing.Iterable` | This is reserved for iterables that shouldn't be consumed. See [Sequence, Iterable & Iterator](sequence_iterable.md) for more detail on parsing and validation. |
| `typing.Type` | See [Type and Typevars](typevars.md) for more detail on parsing and validation. |
| `typing.Callable` | See [Callables](callables.md) for more detail on parsing and validation. |
| `typing.Pattern` | Will cause the input value to be passed to `re.compile(v)` to create a regular expression pattern. |
| `enum.Enum` | Checks that the value is a valid `Enum` instance. See [Enums and Choices](enums.md) for more details. |
| Subclass of `enum.Enum` | Checks that the value is a valid member of the `enum`. See [Enums and Choices](enums.md) for more details. |
| `enum.IntEnum` | Checks that the value is a valid `IntEnum` instance. See [Enums and Choices](enums.md) for more details. |
| Subclass of `enum.IntEnum` | Checks that the value is a valid member of the integer `enum`. See [Enums and Choices](enums.md) for more details. |
| `pathlib.Path` | Simply uses the type itself for validation by passing the value to `Path(v)`. |
| `uuid.UUID` | Strings and bytes (converted to strings) are passed to `UUID(v)`, with a fallback to `UUID(bytes=v)` for `bytes` and `bytearray`. See [UUIDs](uuids.md) for other, more strict UUID types. |
| `ByteSize` | Converts a bytes string with units to bytes. See [ByteSize](../../api/types.md#pydantic.types.ByteSize) for more details. |

## Type conversion

During validation, Pydantic can coerce data into expected types.

There are two modes of coercion: strict and lax. See [Conversion Table](../conversion_table.md) for more details on how Pydantic converts data in both strict and lax modes.

See [Strict mode](../models.md#strict-mode) and [Strict Types](strict_types.md) for details on enabling strict coercion.

## Literal type

!!! note
    This is a new feature of the Python standard library as of Python 3.8;
    prior to Python 3.8, it requires the [typing-extensions](https://pypi.org/project/typing-extensions/) package.

Pydantic supports the use of `typing.Literal` (or `typing_extensions.Literal` prior to Python 3.8)
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
    2 validation errors for Meal
    dessert.Cake.kind
      Input should be 'cake' [type=literal_error, input_value='pie', input_type=str]
    dessert.IceCream.kind
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
