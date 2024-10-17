# Type checking test suite

This test suite is meant to assert the correct behavior of the type hints we use in the Pydantic code.
In CI, we run both Mypy and Pyright on these files, using the [`pyproject.toml`](./pyproject.toml)
configuration file.

Note that these tests do not relate to the Mypy plugin, which is tested under the [`mypy/`](../mypy/) folder.

## Assertions

Use [`assert_type`](https://docs.python.org/3/library/typing.html#typing.assert_type) to make assertions:

```python
from typing_extensions import assert_type

from pydantic import TypeAdapter

ta1 = TypeAdapter(int)
assert_type(ta1, TypeAdapter[int])
```

To assert on invalid cases, add a `type: ignore` (for Mypy, must go first) and/or a  `pyright: ignore` (for Pyright) comment:

```python
from pydantic import BaseModel


class Model(BaseModel):
    a: int


Model()  # type: ignore[call-arg]  # pyright: ignore[reportCallIssue]
```
