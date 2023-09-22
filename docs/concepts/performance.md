# Performance tips

In most cases Pydantic won't be your bottle neck, only follow this if you're sure it's necessary.

## Use `model_validate_json()` not `model_validate(json.loads(...))`

On `model_validate(json.loads(...))`, the JSON is parsed in Python, then converted to a dict, then it's validated internally.
On the other hand, `model_validate_json()` already performs the validation internally.

## `TypeAdapter` instantiated once

The idea here is to avoid constructing validators and serializers more than necessary. Each time a `TypeAdapter` is instantiated,
it will construct a new validator and serializer. If you're using a `TypeAdapter` in a function, it will be instantiated each time
the function is called. Instead, instantiate it once, and reuse it.

=== ":x: Bad"

    ```py lint="skip"
    from typing import List

    from pydantic import TypeAdapter


    def my_func():
        adapter = TypeAdapter(List[int])
        # do something with adapter
    ```

=== ":white_check_mark: Good"

    ```py lint="skip"
    from typing import List

    from pydantic import TypeAdapter

    adapter = TypeAdapter(List[int])

    def my_func():
        ...
        # do something with adapter
    ```

## `Sequence` vs `list` or `tuple` - `Mapping` vs `dict`

When using `Sequence`, Pydantic calls `isinstance(value, Sequence)` to check if the value is a sequence.
Also, Pydantic will try to validate against different types of sequences, like `list` and `tuple`.
If you know the value is a `list` or `tuple`, use `list` or `tuple` instead of `Sequence`.

The same applies to `Mapping` and `dict`.
If you know the value is a `dict`, use `dict` instead of `Mapping`.

## Don't do validation when you don't have to - use `Any` to keep the value unchanged

If you don't need to validate a value, use `Any` to keep the value unchanged.

```py
from typing import Any

from pydantic import BaseModel


class Model(BaseModel):
    a: Any


model = Model(a=1)
```

## Avoid extra information via subclasses of primitives

<!-- Lose information, Mongo int example look for it...
https://github.com/mongodb/mongo-python-driver/blob/9b6f2e18cfcdf56ad2afc988246060c4d20e11b8/bson/int64.py#L21
-->

<!-- TODO: I also need help here. -->

## Use tagged union, not union

Tagged union (or discriminated union) is a union with a field that indicates which type it is.

<!-- TODO: I need a good example here. My tests didn't show much difference. -->

## Use `Literal` not `Enum`

Instead of using `Enum`, use `Literal` to define the structure of the data.

??? info "Performance comparison"
    With a simple benchmark, `Literal` is about ~3x faster than `Enum`:

    ```py test="skip"
    import enum
    from timeit import timeit

    from typing_extensions import Literal

    from pydantic import TypeAdapter

    ta = TypeAdapter(Literal['a', 'b'])
    result1 = timeit(lambda: ta.validate_python('a'), number=10000)


    class AB(str, enum.Enum):
        a = 'a'
        b = 'b'


    ta = TypeAdapter(AB)
    result2 = timeit(lambda: ta.validate_python('a'), number=10000)
    print(result2 / result1)
    ```

## Use `TypedDict` over nested models

Instead of using nested models, use `TypedDict` to define the structure of the data.

??? info "Performance comparison"
    With a simple benchmark, `TypedDict` is about ~2.5x faster than nested models:

    ```py test="skip"
    from timeit import timeit

    from typing_extensions import TypedDict

    from pydantic import BaseModel, TypeAdapter


    class A(TypedDict):
        a: str
        b: int


    class TypedModel(TypedDict):
        a: A


    class B(BaseModel):
        a: str
        b: int


    class Model(BaseModel):
        b: B


    ta = TypeAdapter(TypedModel)
    result1 = timeit(
        lambda: ta.validate_python({'a': {'a': 'a', 'b': 2}}), number=10000
    )
    result2 = timeit(
        lambda: Model.model_validate({'b': {'a': 'a', 'b': 2}}), number=10000
    )
    print(result2 / result1)
    ```

## Avoid wrap validators if you really care about performance

<!-- TODO: I need help on this one. -->
