# Pydantic Validation

[![CI](https://img.shields.io/github/actions/workflow/status/pydantic/pydantic/ci.yml?branch=main&logo=github&label=CI)](https://github.com/pydantic/pydantic/actions?query=event%3Apush+branch%3Amain+workflow%3ACI)
[![Coverage](https://coverage-badge.samuelcolvin.workers.dev/pydantic/pydantic.svg)](https://coverage-badge.samuelcolvin.workers.dev/redirect/pydantic/pydantic)
[![pypi](https://img.shields.io/pypi/v/pydantic.svg)](https://pypi.python.org/pypi/pydantic)
[![CondaForge](https://img.shields.io/conda/v/conda-forge/pydantic.svg)](https://anaconda.org/conda-forge/pydantic)
[![downloads](https://static.pepy.tech/badge/pydantic/month)](https://pepy.tech/project/pydantic)
[![versions](https://img.shields.io/pypi/pyversions/pydantic.svg)](https://github.com/pydantic/pydantic)
[![license](https://img.shields.io/github/license/pydantic/pydantic.svg)](https://github.com/pydantic/pydantic/blob/main/LICENSE)
[![Pydantic v2](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/pydantic/pydantic/main/docs/badge/v2.json)](https://docs.pydantic.dev/latest/contributing/#badges)
[![llms.txt](https://img.shields.io/badge/llms.txt-green)](https://docs.pydantic.dev/latest/llms.txt)

Data validation using Python type hints.

Fast and extensible, Pydantic plays nicely with your linters/IDE/brain.
Define how data should be in pure, canonical Python 3.9+; validate it with Pydantic.

## Pydantic Logfire :fire:

We've recently launched Pydantic Logfire to help you monitor your applications.
[Learn more](https://pydantic.dev/articles/logfire-announcement)

## Pydantic V1.10 vs. V2

Pydantic V2 is a ground-up rewrite that offers many new features, performance improvements, and some breaking changes compared to Pydantic V1.

If you're using Pydantic V1 you may want to look at the
[pydantic V1.10 Documentation](https://docs.pydantic.dev/) or,
[`1.10.X-fixes` git branch](https://github.com/pydantic/pydantic/tree/1.10.X-fixes). Pydantic V2 also ships with the latest version of Pydantic V1 built in so that you can incrementally upgrade your code base and projects: `from pydantic import v1 as pydantic_v1`.

## Help

See [documentation](https://docs.pydantic.dev/) for more details.

## Installation

Install using `pip install -U pydantic` or `conda install pydantic -c conda-forge`.
For more installation options to make Pydantic even faster,
see the [Install](https://docs.pydantic.dev/install/) section in the documentation.

## A Simple Example

```python
from datetime import datetime
from typing import Optional
from pydantic import BaseModel

class User(BaseModel):
    id: int
    name: str = 'John Doe'
    signup_ts: Optional[datetime] = None
    friends: list[int] = []

external_data = {'id': '123', 'signup_ts': '2017-06-01 12:22', 'friends': [1, '2', b'3']}
user = User(**external_data)
print(user)
#> User id=123 name='John Doe' signup_ts=datetime.datetime(2017, 6, 1, 12, 22) friends=[1, 2, 3]
print(user.id)
#> 123
```

## Model Injector Decorator

Pydantic now includes a `model_inject` decorator that automatically instantiates Pydantic models from function keyword arguments, similar to FastAPI's behavior:

```python
from pydantic import BaseModel, Field, model_inject

class UserModel(BaseModel):
    name: str = Field(..., description="User's name")
    age: int = Field(..., ge=0, le=150, description="User's age")
    email: str = Field(..., description="User's email")

@model_inject
def create_user(user: UserModel) -> str:
    """Create a user profile from user data."""
    return f"User: {user.name} (Age: {user.age}) - {user.email}"

# Usage - the decorator automatically instantiates UserModel from kwargs
result = create_user(
    name="John Doe",
    age=30,
    email="john@example.com"
)
print(result)  # Output: "User: John Doe (Age: 30) - john@example.com"
```

The decorator supports multiple models, nested models, positional arguments, and provides enhanced error messages with model and field context.

### Positional Arguments Support

The decorator also supports positional arguments for model parameters:

```python
from pydantic import BaseModel, Field, model_inject

class UserModel(BaseModel):
    name: str = Field(..., description="User's name")
    age: int = Field(..., ge=0, le=150, description="User's age")

@model_inject
def create_user(user: UserModel) -> str:
    return f"User: {user.name} (Age: {user.age})"

# Positional dict argument
result = create_user({
    "name": "John Doe",
    "age": 30
})

# Positional single value (uses first field)
result = create_user("Alice Johnson")  # Sets name="Alice Johnson"
```

For multiple model parameters, positional arguments are assigned in sequence:

```python
@model_inject
def setup_user(user: UserModel, settings: SettingsModel) -> dict:
    return {"user": user.name, "theme": settings.theme}

# Both models as positional arguments
result = setup_user(
    {"name": "Jane", "age": 25},  # user parameter
    {"theme": "dark"}             # settings parameter
)
```

## Contributing

For guidance on setting up a development environment and how to make a
contribution to Pydantic, see
[Contributing to Pydantic](https://docs.pydantic.dev/contributing/).

## Reporting a Security Vulnerability

See our [security policy](https://github.com/pydantic/pydantic/security/policy).
