Pydantic models are a great way to validate and serialize data for requests and responses.
Pydantic is instrumental in many web frameworks and libraries, such as FastAPI, Django, Flask, and HTTPX.

## `httpx` requests

[`httpx`](https://www.python-httpx.org/) is an HTTP client for Python 3 with synchronous and asynchronous APIs.
In the below example, we query the [JSONPlaceholder API](https://jsonplaceholder.typicode.com/) to get a user's data and validate it with a Pydantic model.

```python {test="skip"}
import httpx

from pydantic import BaseModel, EmailStr


class User(BaseModel):
    id: int
    name: str
    email: EmailStr


url = '[https://jsonplaceholder.typicode.com/users/1](https://jsonplaceholder.typicode.com/users/1)'

response = httpx.get(url)
response.raise_for_status()

user = User.model_validate(response.json())
print(repr(user))
#> User(id=1, name='Leanne Graham', email='Sincere@april.biz')

```

The [`TypeAdapter`][pydantic.type_adapter.TypeAdapter] tool from Pydantic often comes in quite
handy when working with HTTP requests. Consider a similar example where we are validating a list of users:

```python {test="skip"}
from pprint import pprint

import httpx

from pydantic import BaseModel, EmailStr, TypeAdapter


class User(BaseModel):
    id: int
    name: str
    email: EmailStr


url = '[https://jsonplaceholder.typicode.com/users/](https://jsonplaceholder.typicode.com/users/)'  # (1)!

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

## `requests` library

The standard [`requests`](https://requests.readthedocs.io/) library is widely used for synchronous HTTP calls. Pydantic integrates with it just as easily.

```python {test="skip"}
import requests
from pydantic import BaseModel, EmailStr, ValidationError

class User(BaseModel):
    id: int
    name: str
    email: EmailStr

url = '[https://jsonplaceholder.typicode.com/users/1](https://jsonplaceholder.typicode.com/users/1)'

response = requests.get(url)
response.raise_for_status()

# requests.json() returns a dict, which we pass to model_validate
user = User.model_validate(response.json())
print(repr(user))
#> User(id=1, name='Leanne Graham', email='Sincere@april.biz')

```

## Handling Validation Errors

When working with external APIs, you cannot always guarantee the response matches your schema. It is best practice to wrap your validation logic in a `try...except` block to handle `ValidationError`.

```python {test="skip"}
import httpx
from pydantic import BaseModel, ValidationError

class User(BaseModel):
    id: int
    name: str
    email: str

# Let's simulate a broken API response (missing 'email')
malformed_response = {'id': 1, 'name': 'John Doe'}

try:
    user = User.model_validate(malformed_response)
except ValidationError as e:
    print("API Response did not match schema!")
    print(e)
    """
    API Response did not match schema!
    1 validation error for User
    email
      Field required [type=missing, input_value={'id': 1, 'name': 'John Doe'}, input_type=dict]
    """

```