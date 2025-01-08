!!! note
    **Admission:** I (the primary developer of Pydantic) also develop python-devtools.

[python-devtools](https://python-devtools.helpmanual.io/) (`pip install devtools`) provides a number of tools which
are useful during Python development, including `debug()` an alternative to `print()` which formats output in a way
which should be easier to read than `print` as well as giving information about which file/line the print statement
is on and what value was printed.

Pydantic integrates with *devtools* by implementing the `__pretty__` method on most public classes.

In particular `debug()` is useful when inspecting models:


```python {test="no-print-intercept"}
from datetime import datetime
from typing import List

from devtools import debug

from pydantic import BaseModel


class Address(BaseModel):
    street: str
    country: str
    lat: float
    lng: float


class User(BaseModel):
    id: int
    name: str
    signup_ts: datetime
    friends: List[int]
    address: Address


user = User(
    id='123',
    name='John Doe',
    signup_ts='2019-06-01 12:22',
    friends=[1234, 4567, 7890],
    address=dict(street='Testing', country='uk', lat=51.5, lng=0),
)
debug(user)
print('\nshould be much easier read than:\n')
print('user:', user)
```

Will output in your terminal:

{{ devtools_example }}

!!! note
    `python-devtools` doesn't yet support Python 3.13.
