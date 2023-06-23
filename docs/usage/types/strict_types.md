Strict types enable you to prevent coercion from compatible types.

## Strict types


Pydantic provides the following strict types:

- [`StrictBool`][pydantic.types.StrictBool]
- [`StrictBytes`][pydantic.types.StrictBytes]
- [`StrictFloat`][pydantic.types.StrictFloat]
- [`StrictInt`][pydantic.types.StrictInt]
- [`StrictStr`][pydantic.types.StrictStr]

These types will only pass validation when the validated value is of the respective type or is a subtype of that type.

## Constrained types

This behavior is also exposed via the `strict` field of the constrained types and can be combined with a multitude of complex validation rules.

- [`conbytes()`][pydantic.types.conbytes]
- [`condate()`][pydantic.types.condate]
- [`condecimal()`][pydantic.types.condecimal]
- [`confloat()`][pydantic.types.confloat]
- [`confrozenset()`][pydantic.types.confrozenset]
- [`conint()`][pydantic.types.conint]
- [`conlist()`][pydantic.types.conlist]
- [`conset()`][pydantic.types.conset]
- [`constr()`][pydantic.types.constr]

The following caveats apply:

- `StrictBytes` (and the `strict` option of `conbytes()`) will accept both `bytes`,
   and `bytearray` types.
- `StrictInt` (and the `strict` option of `conint()`) will not accept `bool` types,
    even though `bool` is a subclass of `int` in Python. Other subclasses will work.
- `StrictFloat` (and the `strict` option of `confloat()`) will not accept `int`.

Besides the above, you can also have a [`FiniteFloat`][pydantic.types.FiniteFloat] type that will only accept finite values (i.e. not `inf`, `-inf` or `nan`).

```py
from pydantic import BaseModel, FiniteFloat, StrictInt, ValidationError


class StrictIntModel(BaseModel):
    strict_int: StrictInt


class Model(BaseModel):
    finite: FiniteFloat


try:
    StrictIntModel(strict_int=3.14159)
except ValidationError as e:
    print(e)
    """
    1 validation error for StrictIntModel
    strict_int
      Input should be a valid integer [type=int_type, input_value=3.14159, input_type=float]
    """
m = Model(finite=1.0)
print(m)
#> finite=1.0
```

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

### Arguments to `condecimal`
The following arguments are available when using the `condecimal` type function

- `gt: Decimal = None`: enforces decimal to be greater than the set value
- `ge: Decimal = None`: enforces decimal to be greater than or equal to the set value
- `lt: Decimal = None`: enforces decimal to be less than the set value
- `le: Decimal = None`: enforces decimal to be less than or equal to the set value
- `max_digits: int = None`: maximum number of digits within the decimal. it does not include a zero before the decimal point or trailing decimal zeroes
- `decimal_places: int = None`: max number of decimal places allowed. it does not include trailing decimal zeroes
- `multiple_of: Decimal = None`: enforces decimal to be a multiple of the set value

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
