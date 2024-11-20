# Experimental Features

In this section you will find documentation for new, experimental features in Pydantic. These features are subject to change or removal, and we are looking for feedback and suggestions before making them a permanent part of Pydantic.

See our [Version Policy](../version-policy.md#experimental-features) for more information on experimental features.

## Feedback

We welcome feedback on experimental features! Please open an issue on the [Pydantic GitHub repository](https://github.com/pydantic/pydantic/issues/new/choose) to share your thoughts, requests, or suggestions.

We also encourage you to read through existing feedback and add your thoughts to existing issues.

## Warnings on Import

When you import an experimental feature from the `experimental` module, you'll see a warning message that the feature is experimental. You can disable this warning with the following:

```python
import warnings

from pydantic import PydanticExperimentalWarning

warnings.filterwarnings('ignore', category=PydanticExperimentalWarning)
```

## Pipeline API

Pydantic v2.8.0 introduced an experimental "pipeline" API that allows composing of parsing (validation), constraints and transformations in a more type-safe manner than existing APIs. This API is subject to change or removal, we are looking for feedback and suggestions before making it a permanent part of Pydantic.

??? api "API Documentation"
    [`pydantic.experimental.pipeline`][pydantic.experimental.pipeline]<br>

Generally, the pipeline API is used to define a sequence of steps to apply to incoming data during validation. The pipeline API is designed to be more type-safe and composable than the existing Pydantic API.

Each step in the pipeline can be:

* A validation step that runs pydantic validation on the provided type
* A transformation step that modifies the data
* A constraint step that checks the data against a condition
* A predicate step that checks the data against a condition and raises an error if it returns `False`

<!-- TODO: (@sydney-runkle) add more documentation once we solidify the API during the experimental phase -->

Note that the following example attempts to be exhaustive at the cost of complexity: if you find yourself writing this many transformations in type annotations you may want to consider having a `UserIn` and `UserOut` model (example below) or similar where you make the transformations via idomatic plain Python code.
These APIs are meant for situations where the code savings are significant and the added complexity is relatively small.

```python
from __future__ import annotations

from datetime import datetime

from typing_extensions import Annotated

from pydantic import BaseModel
from pydantic.experimental.pipeline import validate_as


class User(BaseModel):
    name: Annotated[str, validate_as(str).str_lower()]  # (1)!
    age: Annotated[int, validate_as(int).gt(0)]  # (2)!
    username: Annotated[str, validate_as(str).str_pattern(r'[a-z]+')]  # (3)!
    password: Annotated[
        str,
        validate_as(str)
        .transform(str.lower)
        .predicate(lambda x: x != 'password'),  # (4)!
    ]
    favorite_number: Annotated[  # (5)!
        int,
        (validate_as(int) | validate_as(str).str_strip().validate_as(int)).gt(
            0
        ),
    ]
    friends: Annotated[list[User], validate_as(...).len(0, 100)]  # (6)!
    bio: Annotated[
        datetime,
        validate_as(int)
        .transform(lambda x: x / 1_000_000)
        .validate_as(...),  # (8)!
    ]
```

1. Lowercase a string.
2. Constrain an integer to be greater than zero.
3. Constrain a string to match a regex pattern.
4. You can also use the lower level transform, constrain and predicate methods.
5. Use the `|` or `&` operators to combine steps (like a logical OR or AND).
6. Calling `validate_as(...)` with `Ellipsis`, `...` as the first positional argument implies `validate_as(<field type>)`. Use `validate_as(Any)` to accept any type.
7. You can call `validate_as()` before or after other steps to do pre or post processing.

### Mapping from `BeforeValidator`, `AfterValidator` and `WrapValidator`

The `validate_as` method is a more type-safe way to define `BeforeValidator`, `AfterValidator` and `WrapValidator`:

```python
from typing_extensions import Annotated

from pydantic.experimental.pipeline import transform, validate_as

# BeforeValidator
Annotated[int, validate_as(str).str_strip().validate_as(...)]  # (1)!
# AfterValidator
Annotated[int, transform(lambda x: x * 2)]  # (2)!
# WrapValidator
Annotated[
    int,
    validate_as(str)
    .str_strip()
    .validate_as(...)
    .transform(lambda x: x * 2),  # (3)!
]
```

1. Strip whitespace from a string before parsing it as an integer.
2. Multiply an integer by 2 after parsing it.
3. Strip whitespace from a string, validate it as an integer, then multiply it by 2.


### Alternative patterns

There are many alternative patterns to use depending on the scenario.
Just as an example, consider the `UserIn` and `UserOut` pattern mentioned above:

```python
from __future__ import annotations

from pydantic import BaseModel


class UserIn(BaseModel):
    favorite_number: int | str


class UserOut(BaseModel):
    favorite_number: int


def my_api(user: UserIn) -> UserOut:
    favorite_number = user.favorite_number
    if isinstance(favorite_number, str):
        favorite_number = int(user.favorite_number.strip())

    return UserOut(favorite_number=favorite_number)


assert my_api(UserIn(favorite_number=' 1 ')).favorite_number == 1
```

This example uses plain idiomatic Python code that may be easier to understand, type-check, etc. than the examples above.
The approach you choose should really depend on your use case.
You will have to compare verbosity, performance, ease of returning meaningful errors to your users, etc. to choose the right pattern.
Just be mindful of abusing advanced patterns like the pipeline API just because you can.

## Partial Validation

Pydantic v2.10.0 introduces experimental support for "partial validation".

This allows you to validate an incomplete JSON string, or a Python object representing incomplete input data.

Partial validation is particularly helpful when processing the output of an LLM, where the model streams structured responses, and you may wish to begin validating the stream while you're still receiving data (e.g. to show partial data to users).

!!! warning
    Partial validation is an experimental feature and may change in future versions of Pydantic. The current implementation should be considered a proof of concept at this time and has a number of [limitations](#limitations-of-partial-validation).

Partial validation can be enabled when using the three validation methods on `TypeAdapter`: [`TypeAdapter.validate_json()`][pydantic.TypeAdapter.validate_json], [`TypeAdapter.validate_python()`][pydantic.TypeAdapter.validate_python], and [`TypeAdapter.validate_strings()`][pydantic.TypeAdapter.validate_strings]. This allows you to parse and validation incomplete JSON, but also to validate Python objects created by parsing incomplete data of any format.

The `experimental_allow_partial` flag can be passed to these methods to enable partial validation.
It can take the following values (and is `False`, by default):

* `False` or `'off'` - disable partial validation
* `True` or `'on'` - enable partial validation, but don't support trailing strings
* `'trailing-strings'` - enable partial validation and support trailing strings

!!! info "`'trailing-strings'` mode"
    `'trailing-strings'` mode allows for trailing incomplete strings at the end of partial JSON to be included in the output.
    For example, if you're validating against the following model:

    ```python
    from typing import TypedDict


    class Model(TypedDict):
        a: str
        b: str
    ```

    Then the following JSON input would be considered valid, despite the incomplete string at the end:

    ```json
    '{"a": "hello", "b": "wor'
    ```

    And would be validated as:

    ```python {test="skip" lint="skip"}
    {'a': 'hello', 'b': 'wor'}
    ```

`experiment_allow_partial` in action:

```python
from typing import List

from annotated_types import MinLen
from typing_extensions import Annotated, NotRequired, TypedDict

from pydantic import TypeAdapter


class Foobar(TypedDict):  # (1)!
    a: int
    b: NotRequired[float]
    c: NotRequired[Annotated[str, MinLen(5)]]


ta = TypeAdapter(List[Foobar])

v = ta.validate_json('[{"a": 1, "b"', experimental_allow_partial=True)  # (2)!
print(v)
#> [{'a': 1}]

v = ta.validate_json(
    '[{"a": 1, "b": 1.0, "c": "abcd', experimental_allow_partial=True  # (3)!
)
print(v)
#> [{'a': 1, 'b': 1.0}]

v = ta.validate_json(
    '[{"b": 1.0, "c": "abcde"', experimental_allow_partial=True  # (4)!
)
print(v)
#> []

v = ta.validate_json(
    '[{"a": 1, "b": 1.0, "c": "abcde"},{"a": ', experimental_allow_partial=True
)
print(v)
#> [{'a': 1, 'b': 1.0, 'c': 'abcde'}]

v = ta.validate_python([{'a': 1}], experimental_allow_partial=True)  # (5)!
print(v)
#> [{'a': 1}]

v = ta.validate_python(
    [{'a': 1, 'b': 1.0, 'c': 'abcd'}], experimental_allow_partial=True  # (6)!
)
print(v)
#> [{'a': 1, 'b': 1.0}]

v = ta.validate_json(
    '[{"a": 1, "b": 1.0, "c": "abcdefg',
    experimental_allow_partial='trailing-strings',  # (7)!
)
print(v)
#> [{'a': 1, 'b': 1.0, 'c': 'abcdefg'}]
```

1. The TypedDict `Foobar` has three field, but only `a` is required, that means that a valid instance of `Foobar` can be created even if the `b` and `c` fields are missing.
2. Parsing JSON, the input is valid JSON up to the point where the string is truncated.
3. In this case truncation of the input means the value of `c` (`abcd`) is invalid as input to `c` field, hence it's omitted.
4. The `a` field is required, so validation on the only item in the list fails and is dropped.
5. Partial validation also works with Python objects, it should have the same semantics as with JSON except of course you can't have a genuinely "incomplete" Python object.
6. The same as above but with a Python object, `c` is dropped as it's not required and failed validation.
7. The `trailing-strings` mode allows for incomplete strings at the end of partial JSON to be included in the output, in this case the input is valid JSON up to the point where the string is truncated, so the last string is included.

### How Partial Validation Works

Partial validation follows the zen of Pydantic — it makes no guarantees about what the input data might have been, but it does guarantee to return a valid instance of the type you required, or raise a validation error.

To do this, the `experimental_allow_partial` flag enables two pieces of behavior:

#### 1. Partial JSON parsing

The [jiter](https://github.com/pydantic/jiter) JSON parser used by Pydantic already supports parsing partial JSON,
`experimental_allow_partial` is simply passed to jiter via the `allow_partial` argument.

!!! note
    If you just want pure JSON parsing with support for partial JSON, you can use the [`jiter`](https://pypi.org/project/jiter/) Python library directly, or pass the `allow_partial` argument when calling [`pydantic_core.from_json`][pydantic_core.from_json].

#### 2. Ignore errors in the last element of the input {#2-ignore-errors-in-last}

Only having access to part of the input data means errors can commonly occur in the last element of the input data.

For example:

* if a string has a constraint `MinLen(5)`, when you only see part of the input, validation might fail because part of the string is missing (e.g. `{"name": "Sam` instead of `{"name": "Samuel"}`)
* if an `int` field has a constraint `Ge(10)`, when you only see part of the input, validation might fail because the number is too small (e.g. `1` instead of `10`)
* if a `TypedDict` field has 3 required fields, but the partial input only has two of the fields, validation would fail because some field are missing
* etc. etc. — there are lost more cases like this

The point is that if you only see part of some valid input data, validation errors can often occur in the last element of a sequence or last value of mapping.

To avoid these errors breaking partial validation, Pydantic will ignore ALL errors in the last element of the input data.

```python {title="Errors in last element ignored"}
from typing import List

from annotated_types import MinLen
from typing_extensions import Annotated

from pydantic import BaseModel, TypeAdapter


class MyModel(BaseModel):
    a: int
    b: Annotated[str, MinLen(5)]


ta = TypeAdapter(List[MyModel])
v = ta.validate_json(
    '[{"a": 1, "b": "12345"}, {"a": 1,',
    experimental_allow_partial=True,
)
print(v)
#> [MyModel(a=1, b='12345')]
```

### Limitations of Partial Validation

#### TypeAdapter only

You can only pass `experiment_allow_partial` to [`TypeAdapter`][pydantic.TypeAdapter] methods, it's not yet supported via other Pydantic entry points like [`BaseModel`][pydantic.BaseModel].

#### Types supported

Right now only a subset of collection validators know how to handle partial validation:

- `list`
- `set`
- `frozenset`
- `dict` (as in `dict[X, Y]`)
- `TypedDict` — only non-required fields may be missing, e.g. via [`NotRequired`][typing.NotRequired] or [`total=False`][typing.TypedDict.__total__])

While you can use `experimental_allow_partial` while validating against types that include other collection validators, those types will be validated "all or nothing", and partial validation will not work on more nested types.

E.g. in the [above](#2-ignore-errors-in-last) example partial validation works although the second item in the list is dropped completely since `BaseModel` doesn't (yet) support partial validation.

But partial validation won't work at all in the follow example because `BaseModel` doesn't support partial validation so it doesn't forward the `allow_partial` instruction down to the list validator in `b`:

```python
from typing import List

from annotated_types import MinLen
from typing_extensions import Annotated

from pydantic import BaseModel, TypeAdapter, ValidationError


class MyModel(BaseModel):
    a: int = 1
    b: List[Annotated[str, MinLen(5)]] = []  # (1)!


ta = TypeAdapter(MyModel)
try:
    v = ta.validate_json(
        '{"a": 1, "b": ["12345", "12', experimental_allow_partial=True
    )
except ValidationError as e:
    print(e)
    """
    1 validation error for MyModel
    b.1
      String should have at least 5 characters [type=string_too_short, input_value='12', input_type=str]
    """
```

1. The list validator for `b` doesn't get the `allow_partial` instruction passed down to it by the model validator so it doesn't know to ignore errors in the last element of the input.

#### Some invalid but complete JSON will be accepted

The way [jiter](https://github.com/pydantic/jiter) (the JSON parser used by Pydantic) works means it's currently not possible to differentiate between complete JSON like `{"a": 1, "b": "12"}` and incomplete JSON like `{"a": 1, "b": "12`.

This means that some invalid JSON will be accepted by Pydantic when using `experimental_allow_partial`, e.g.:

```python
from annotated_types import MinLen
from typing_extensions import Annotated, TypedDict

from pydantic import TypeAdapter


class Foobar(TypedDict, total=False):
    a: int
    b: Annotated[str, MinLen(5)]


ta = TypeAdapter(Foobar)

v = ta.validate_json(
    '{"a": 1, "b": "12', experimental_allow_partial=True  # (1)!
)
print(v)
#> {'a': 1}

v = ta.validate_json(
    '{"a": 1, "b": "12"}', experimental_allow_partial=True  # (2)!
)
print(v)
#> {'a': 1}
```

1. This will pass validation as expected although the last field will be omitted as it failed validation.
2. This will also pass validation since the binary representation of the JSON data passed to pydantic-core is indistinguishable from the previous case.

#### Any error in the last field of the input will be ignored

As described [above](#2-ignore-errors-in-last), many errors can result from truncating the input. Rather than trying to specifically ignore errors that could result from truncation, Pydantic ignores all errors in the last element of the input in partial validation mode.

This means clearly invalid data will pass validation if the error is in the last field of the input:

```python
from typing import List

from annotated_types import Ge
from typing_extensions import Annotated

from pydantic import TypeAdapter

ta = TypeAdapter(List[Annotated[int, Ge(10)]])
v = ta.validate_python([20, 30, 4], experimental_allow_partial=True)  # (1)!
print(v)
#> [20, 30]

ta = TypeAdapter(List[int])

v = ta.validate_python([1, 2, 'wrong'], experimental_allow_partial=True)  # (2)!
print(v)
#> [1, 2]
```

1. As you would expect, this will pass validation since Pydantic correctly ignores the error in the (truncated) last item.
2. This will also pass validation since the error in the last item is ignored.
