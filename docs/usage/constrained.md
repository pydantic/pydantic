

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
