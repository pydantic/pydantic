You may have types that are not `BaseModel`s that you want to validate data against.
Or you may want to validate a `List[SomeModel]`, or dump it to JSON.

??? api "API Documentation"
    [`pydantic.type_adapter.TypeAdapter`][pydantic.type_adapter.TypeAdapter]<br>

For use cases like this, Pydantic provides [`TypeAdapter`][pydantic.type_adapter.TypeAdapter],
which can be used for type validation, serialization, and JSON schema generation without needing to create a
[`BaseModel`][pydantic.main.BaseModel].

A [`TypeAdapter`][pydantic.type_adapter.TypeAdapter] instance exposes some of the functionality from
[`BaseModel`][pydantic.main.BaseModel] instance methods for types that do not have such methods
(such as dataclasses, primitive types, and more):

```py
from typing import List

from typing_extensions import TypedDict

from pydantic import TypeAdapter, ValidationError


class User(TypedDict):
    name: str
    id: int


user_list_adapter = TypeAdapter(List[User])
print(repr(user_list_adapter.validate_python([{'name': 'Fred', 'id': '3'}])))
#> [{'name': 'Fred', 'id': 3}]

try:
    user_list_adapter.validate_python(
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
    Despite some overlap in use cases with [`RootModel`][pydantic.root_model.RootModel],
    [`TypeAdapter`][pydantic.type_adapter.TypeAdapter] should not be used as a type annotation for
    specifying fields of a `BaseModel`, etc.

## Parsing data into a specified type

[`TypeAdapter`][pydantic.type_adapter.TypeAdapter] can be used to apply the parsing logic to populate Pydantic models
in a more ad-hoc way. This function behaves similarly to
[`BaseModel.model_validate`][pydantic.main.BaseModel.model_validate],
but works with arbitrary Pydantic-compatible types.

This is especially useful when you want to parse results into a type that is not a direct subclass of
[`BaseModel`][pydantic.main.BaseModel]. For example:

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
```py
from typing import List

from pydantic import BaseModel, TypeAdapter


class Item(BaseModel):
    id: int
    name: str


item_list = [Item(id=1, name="My Item")]
items = TypeAdapter(List[Item]).dump_json(item_list)
print(items)
#> b'[{"id":1,"name":"item1"}]'
```


[`TypeAdapter`][pydantic.type_adapter.TypeAdapter] is capable of parsing data into any of the types Pydantic can
handle as fields of a [`BaseModel`][pydantic.main.BaseModel].

!!! info "Performance considerations"
    When creating an instance of `TypeAdapter`, the provided type must be analyzed and converted into a pydantic-core
    schema. This comes with some non-trivial overhead, so it is recommended to create a `TypeAdapter` for a given type
    just once and reuse it in loops or other performance-critical code.

!!! info "About bytes vs string discrepancy"
    In V1, model dumping returned a str type, whereas the newly added TypeAdapter in V2 returns bytes. Returning bytes is more performant, but str return has been retained for BaseModel due to backwards compatibility reasons. For BaseModel, bytes are coerced to strings, but bytes are most often the desired end type. Hence, the return type remains bytes for the TypeAdapter case.
