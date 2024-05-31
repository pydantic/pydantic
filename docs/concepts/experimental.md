# Experimental Features

In this section you will find documentation for new, experimental features in Pydantic. These features are subject to change or removal, and we are looking for feedback and suggestions before making them a permanent part of Pydantic.

<!-- TODO: (@sydney-runkle) add link to versioning policy for experimental features -->

## Pipeline API

Pydantic v2.8.0 introduced an experimental pipeline API that allows composing parsing, constraints and transformations in a more type-safe manner than existing APIs. This API is subject to change or removal, we are looking for feedback and suggestions before making it a permanent part of Pydantic.

```python
from __future__ import annotations

from datetime import datetime

from typing_extensions import Annotated

from pydantic import BaseModel
from pydantic.experimental.pipeline import parse, parse_defer


class User(BaseModel):
    name: Annotated[str, parse(str).str.lower()]  # (1)!
    age: Annotated[int, parse(int).gt(0)]  # (2)!
    username: Annotated[str, parse(str).str.pattern(r'[a-z]+')]  # (3)!
    password: Annotated[
        str,
        parse(str)
        .transform(str.lower)
        .predicate(lambda x: x != 'password'),  # (4)!
    ]
    favorite_number: Annotated[  # (5)!
        int,
        (parse(int) | parse(str).str.strip().parse(int)).gt(0),
    ]
    friends: Annotated[list[User], parse().len(0, 100)]  # (6)!
    family: Annotated[  # (7)!
        list[User],
        parse_defer(lambda: list[User]).transform(lambda x: x[1:]),
    ]
    bio: Annotated[
        datetime, parse(int).transform(lambda x: x / 1_000_000).parse()  # (8)!
    ]
```

1. Lowercase a string.
2. Constrain an integer to be greater than zero.
3. Constrain a string to match a regex pattern.
4. You can also use the lower level transform, constrain and predicate methods.
5. Use the `|` or `&` operators to combine steps (like a logical OR or AND).
6. Calling `parse()` with no arguments implies `parse(<field type>)`. Use `parse(Any)` to accept any type.
7. For recursive types you can use `parse_defer` to reference the type itself before it's defined.
8. You can call `parse()` before or after other steps to do pre or post processing.

### Mapping from `BeforeValidator`, `AfterValidator` and `WrapValidator`

The `parse` method is a more type-safe way to define `BeforeValidator`, `AfterValidator` and `WrapValidator`:

```python
from typing_extensions import Annotated

from pydantic.experimental.pipeline import parse

# BeforeValidator
Annotated[int, parse(str).str.strip().parse()]  # (1)!
# AfterValidator
Annotated[int, parse().transform(lambda x: x * 2)]  # (2)!
# WrapValidator
Annotated[
    int, parse(str).str.strip().parse().transform(lambda x: x * 2)  # (3)!
]
```

1. Strip whitespace from a string before parsing it as an integer.
2. Multiply an integer by 2 after parsing it.
3. Strip whitespace from a string, parse it as an integer, then multiply it by 2.
