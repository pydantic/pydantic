You may have types that are not `BaseModel`s that you want to validate data against.
Or you may want to validate a `List[SomeModel]`, or dump it to JSON.

For use cases like this, Pydantic provides `TypeAdapter`, which can be used for type validation, serialization, and
JSON schema generation without creating a `BaseModel`.

A `TypeAdapter` instance exposes some of the functionality from `BaseModel` instance methods
for types that do not have such methods (such as dataclasses, primitive types, and more):

```py
from typing import List

from typing_extensions import TypedDict

from pydantic import TypeAdapter, ValidationError


class User(TypedDict):
    name: str
    id: int


UserListValidator = TypeAdapter(List[User])
print(repr(UserListValidator.validate_python([{'name': 'Fred', 'id': '3'}])))
#> [{'name': 'Fred', 'id': 3}]

try:
    UserListValidator.validate_python(
        [{'name': 'Fred', 'id': 'wrong', 'other': 'no'}]
    )
except ValidationError as e:
    print(e)
    """
    1 validation error for list[typed-dict]
    0.id
      Input should be a valid integer, unable to parse string as an integer [type=int_parsing, input_value='wrong', input_type=str]
    """
```

!!! note
    Despite some overlap in use cases with [`RootModel`](models.md#rootmodel-and-custom-root-types),
    `TypeAdapter` should not be used as a type annotation for specifying fields of a `BaseModel`, etc.

## Parsing data into a specified type

`TypeAdapter` can be used to apply the parsing logic to populate Pydantic models in a more ad-hoc way.
This function behaves similarly to `BaseModel.model_validate`, but works with arbitrary Pydantic-compatible types.

This is especially useful when you want to parse results into a type that is not a direct subclass of `BaseModel`.
For example:

```py
from typing import List

from pydantic import BaseModel, TypeAdapter


class Item(BaseModel):
    id: int
    name: str


# `item_data` could come from an API call, eg., via something like:
# item_data = requests.get('https://my-api.com/items').json()
item_data = [{'id': 1, 'name': 'My Item'}]

items = TypeAdapter(List[Item]).validate_python(item_data)
print(items)
#> [Item(id=1, name='My Item')]
```

`TypeAdapter` is capable of parsing data into any of the types Pydantic can handle as fields of a `BaseModel`.
