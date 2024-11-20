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

```python
from typing import List

from typing_extensions import TypedDict

from pydantic import TypeAdapter, ValidationError


class User(TypedDict):
    name: str
    id: int


user_list_adapter = TypeAdapter(List[User])
user_list = user_list_adapter.validate_python([{'name': 'Fred', 'id': '3'}])
print(repr(user_list))
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

print(repr(user_list_adapter.dump_json(user_list)))
#> b'[{"name":"Fred","id":3}]'
```

!!! info "`dump_json` returns `bytes`"
    `TypeAdapter`'s `dump_json` methods returns a `bytes` object, unlike the corresponding method for `BaseModel`, `model_dump_json`, which returns a `str`.
    The reason for this discrepancy is that in V1, model dumping returned a str type, so this behavior is retained in V2 for backwards compatibility.
    For the `BaseModel` case, `bytes` are coerced to `str` types, but `bytes` are often the desired end type.
    Hence, for the new `TypeAdapter` class in V2, the return type is simply `bytes`, which can easily be coerced to a `str` type if desired.

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

```python
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

[`TypeAdapter`][pydantic.type_adapter.TypeAdapter] is capable of parsing data into any of the types Pydantic can
handle as fields of a [`BaseModel`][pydantic.main.BaseModel].

!!! info "Performance considerations"
    When creating an instance of [`TypeAdapter`][pydantic.type_adapter.TypeAdapter], the provided type must be analyzed and converted into a pydantic-core
    schema. This comes with some non-trivial overhead, so it is recommended to create a `TypeAdapter` for a given type
    just once and reuse it in loops or other performance-critical code.


## Rebuilding a `TypeAdapter`'s schema

In v2.10+, [`TypeAdapter`][pydantic.type_adapter.TypeAdapter]'s support deferred schema building and manual rebuilds. This is helpful for the case of:

* Types with forward references
* Types for which core schema builds are expensive

When you initialize a [`TypeAdapter`][pydantic.type_adapter.TypeAdapter] with a type, Pydantic analyzes the type and creates a core schema for it.
This core schema contains the information needed to validate and serialize data for that type.
See the [architecture documentation](../internals/architecture.md) for more information on core schemas.

If you set [`defer_build`][pydantic.config.ConfigDict.defer_build] to `True` when initializing a `TypeAdapter`,
Pydantic will defer building the core schema until the first time it is needed (for validation or serialization).

In order to manually trigger the building of the core schema, you can call the
[`rebuild`][pydantic.type_adapter.TypeAdapter.rebuild] method on the [`TypeAdapter`][pydantic.type_adapter.TypeAdapter] instance:

```python
from pydantic import ConfigDict, TypeAdapter

ta = TypeAdapter('MyInt', config=ConfigDict(defer_build=True))

# some time later, the forward reference is defined
MyInt = int

ta.rebuild()
assert ta.validate_python(1) == 1
```
