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

This behavior is also exposed via the `strict` field of the constrained types and can be combined with a multitude of complex validation rules. See the individual type signatures for supported arguments.

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
