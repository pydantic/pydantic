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

## Strict types

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
    StrictBool,
    StrictBytes,
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

## Constrained types

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

The value of numerous common types can be restricted using `con*` type functions:

```py
from decimal import Decimal

from pydantic import (
    BaseModel,
    Field,
    NegativeFloat,
    NegativeInt,
    NonNegativeFloat,
    NonNegativeInt,
    NonPositiveFloat,
    NonPositiveInt,
    PositiveFloat,
    PositiveInt,
    conbytes,
    condecimal,
    confloat,
    conint,
    conlist,
    conset,
    constr,
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
