# Performance tips

In most cases Pydantic won't be your bottle neck, only follow this if you're sure it's necessary.

## In general, use `model_validate_json()` not `model_validate(json.loads(...))`

On `model_validate(json.loads(...))`, the JSON is parsed in Python, then converted to a dict, then it's validated internally.
On the other hand, `model_validate_json()` already performs the validation internally.

There are a few cases where `model_validate(json.loads(...))` may be faster. Specifically, when using a `'before'` or `'wrap'` validator
on a model, validation may be faster with the two step method. You can read more about these special cases in
[this discussion](https://github.com/pydantic/pydantic/discussions/6388#discussioncomment-8193105).

Many performance improvements are currently in the works for `pydantic-core`, as discussed
[here](https://github.com/pydantic/pydantic/discussions/6388#discussioncomment-8194048). Once these changes are merged, we should be at
the point where `model_validate_json()` is always faster than `model_validate(json.loads(...))`.

## `TypeAdapter` instantiated once

The idea here is to avoid constructing validators and serializers more than necessary. Each time a `TypeAdapter` is instantiated,
it will construct a new validator and serializer. If you're using a `TypeAdapter` in a function, it will be instantiated each time
the function is called. Instead, instantiate it once, and reuse it.

=== ":x: Bad"

    ```python {lint="skip"}
    from typing import List

    from pydantic import TypeAdapter


    def my_func():
        adapter = TypeAdapter(List[int])
        # do something with adapter
    ```

=== ":white_check_mark: Good"

    ```python {lint="skip"}
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

```python
from typing import Any

from pydantic import BaseModel


class Model(BaseModel):
    a: Any


model = Model(a=1)
```

## Avoid extra information via subclasses of primitives

=== "Don't do this"

    ```python
    class CompletedStr(str):
        def __init__(self, s: str):
            self.s = s
            self.done = False
    ```

=== "Do this"

    ```python
    from pydantic import BaseModel


    class CompletedModel(BaseModel):
        s: str
        done: bool = False
    ```

## Use tagged union, not union

Tagged union (or discriminated union) is a union with a field that indicates which type it is.

```python {test="skip"}
from typing import Any, Literal

from pydantic import BaseModel, Field


class DivModel(BaseModel):
    el_type: Literal['div'] = 'div'
    class_name: str | None = None
    children: list[Any] | None = None


class SpanModel(BaseModel):
    el_type: Literal['span'] = 'span'
    class_name: str | None = None
    contents: str | None = None


class ButtonModel(BaseModel):
    el_type: Literal['button'] = 'button'
    class_name: str | None = None
    contents: str | None = None


class InputModel(BaseModel):
    el_type: Literal['input'] = 'input'
    class_name: str | None = None
    value: str | None = None


class Html(BaseModel):
    contents: DivModel | SpanModel | ButtonModel | InputModel = Field(
        discriminator='el_type'
    )
```

See [Discriminated Unions] for more details.

## Use `TypedDict` over nested models

Instead of using nested models, use `TypedDict` to define the structure of the data.

??? info "Performance comparison"
    With a simple benchmark, `TypedDict` is about ~2.5x faster than nested models:

    ```python {test="skip"}
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

Wrap validators are generally slower than other validators. This is because they require
that data is materialized in Python during validation. Wrap validators can be incredibly useful
for complex validation logic, but if you're looking for the best performance, you should avoid them.

## Failing early with `FailFast`

Starting in v2.8+, you can apply the `FailFast` annotation to sequence types to fail early if any item in the sequence fails validation.
If you use this annotation, you won't get validation errors for the rest of the items in the sequence if one fails, so you're effectively
trading off visibility for performance.

```python
from typing import List

from typing_extensions import Annotated

from pydantic import FailFast, TypeAdapter, ValidationError

ta = TypeAdapter(Annotated[List[bool], FailFast()])
try:
    ta.validate_python([True, 'invalid', False, 'also invalid'])
except ValidationError as exc:
    print(exc)
    """
    1 validation error for list[bool]
    1
      Input should be a valid boolean, unable to interpret input [type=bool_parsing, input_value='invalid', input_type=str]
    """
```

Read more about `FailFast` [here][pydantic.types.FailFast].

[Discriminated Unions]: ../concepts/unions.md#discriminated-unions
