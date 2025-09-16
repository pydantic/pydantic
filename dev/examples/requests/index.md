Pydantic models are a great way to validate and serialize data for requests and responses. Pydantic is instrumental in many web frameworks and libraries, such as FastAPI, Django, Flask, and HTTPX.

## `httpx` requests

[`httpx`](https://www.python-httpx.org/) is an HTTP client for Python 3 with synchronous and asynchronous APIs. In the below example, we query the [JSONPlaceholder API](https://jsonplaceholder.typicode.com/) to get a user's data and validate it with a Pydantic model.

```python
import httpx

from pydantic import BaseModel, EmailStr


class User(BaseModel):
    id: int
    name: str
    email: EmailStr


url = 'https://jsonplaceholder.typicode.com/users/1'

response = httpx.get(url)
response.raise_for_status()

user = User.model_validate(response.json())
print(repr(user))
#> User(id=1, name='Leanne Graham', email='Sincere@april.biz')

```

The TypeAdapter tool from Pydantic often comes in quite handy when working with HTTP requests. Consider a similar example where we are validating a list of users:

```python
from pprint import pprint

import httpx

from pydantic import BaseModel, EmailStr, TypeAdapter


class User(BaseModel):
    id: int
    name: str
    email: EmailStr


url = 'https://jsonplaceholder.typicode.com/users/'  # (1)!

response = httpx.get(url)
response.raise_for_status()

users_list_adapter = TypeAdapter(list[User])

users = users_list_adapter.validate_python(response.json())
pprint([u.name for u in users])
"""
['Leanne Graham',
 'Ervin Howell',
 'Clementine Bauch',
 'Patricia Lebsack',
 'Chelsey Dietrich',
 'Mrs. Dennis Schulist',
 'Kurtis Weissnat',
 'Nicholas Runolfsdottir V',
 'Glenna Reichert',
 'Clementina DuBuque']
"""

```

1. Note, we're querying the `/users/` endpoint here to get a list of users.
