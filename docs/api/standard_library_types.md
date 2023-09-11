
# bool


A standard `bool` field will raise a `ValidationError` if the value is not one of the following:

* A valid boolean (i.e. `True` or `False`),
* The integers `0` or `1`,
* a `str` which when converted to lower case is one of
  `'0', 'off', 'f', 'false', 'n', 'no', '1', 'on', 't', 'true', 'y', 'yes'`
* a `bytes` which is valid per the previous rule when decoded to `str`

!!! note
    If you want stricter boolean logic (e.g. a field which only permits `True` and `False`) you can
    use [`StrictBool`](../usage/types/standard_types.md#strict-types).

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
