# Type checking test suite

Use [`assert_type`](https://docs.python.org/3/library/typing.html#typing.assert_type) to make assertions:

```python
from typing_extensions import assert_type

from pydantic import TypeAdapter

ta1 = TypeAdapter(int)
assert_type(ta1, TypeAdapter[int])
```

To assert on invalid cases, add a `type: ignore` (for Mypy) and/or a  `pyright: ignore` (for Pyright) comment:

```python
from pydantic import BaseModel


class Model(BaseModel):
    a: int


Model()  # type: ignore[call-arg]  # pyright: ignore[reportCallIssue]
```
