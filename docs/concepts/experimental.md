# Experimental Features

In this section you will find documentation for new, experimental features in Pydantic. These features are subject to change or removal, and we are looking for feedback and suggestions before making them a permanent part of Pydantic.

<!-- TODO: (@sydney-runkle) add link to versioning policy for experimental features -->

## Pipeline API

Pydantic v2.8.0 introduced an experimental "pipeline" API that allows composing parsing, constraints and transformations in a more type-safe manner than existing APIs. This API is subject to change or removal, we are looking for feedback and suggestions before making it a permanent part of Pydantic.

```python
from __future__ import annotations

from datetime import datetime

from typing_extensions import Annotated

from pydantic import BaseModel
from pydantic.experimental.pipeline import validate_as, validate_as_deferred


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
    family: Annotated[  # (7)!
        list[User],
        validate_as_deferred(lambda: list[User]).transform(lambda x: x[1:]),
    ]
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
7. For recursive types you can use `validate_as_deferred` to reference the type itself before it's defined.
8. You can call `validate_as()` before or after other steps to do pre or post processing.

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
