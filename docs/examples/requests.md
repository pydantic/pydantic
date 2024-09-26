!!! warning "🚧 Work in Progress"
    This page is a work in progress. More examples will be added soon.

## `httpx` requests

[`httpx`](https://www.python-httpx.org/) is a HTTP client for Python 3 with synchronous and asynchronous APIs.
In the below example, we query the [JSONPlaceholder API](https://jsonplaceholder.typicode.com/) to get a user's data and validate it with a Pydantic model.

```python test="skip"
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

<!-- TODO: httpx, flask, Django rest framework, FastAPI -->
