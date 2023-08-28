`Json`
: a special type wrapper which loads JSON before parsing

You can use the `Json` data type to make Pydantic first load a raw JSON string before
validating the loaded data into the parametrized type:

```py group="json"
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
    json_obj.0
      Input should be a valid integer, unable to parse string as an integer [type=int_parsing, input_value='a', input_type=str]
    json_obj.1
      Input should be a valid integer, unable to parse string as an integer [type=int_parsing, input_value='b', input_type=str]
    """
```

When you dump the model using `model_dump` or `model_dump_json`, the dumped value will be the result of validation,
not the original JSON string. However, you can use the argument `round_trip=True` to get the original JSON string back:

```py group="json"
print(ConstrainedJsonModel(json_obj='[1, 2, 3]').model_dump_json())
#> {"json_obj":[1,2,3]}
print(
    ConstrainedJsonModel(json_obj='[1, 2, 3]').model_dump_json(round_trip=True)
)
#> {"json_obj":"[1,2,3]"}
```
