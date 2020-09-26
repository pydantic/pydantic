# pydantic

[![CI](https://github.com/samuelcolvin/pydantic/workflows/CI/badge.svg?event=push)](https://github.com/samuelcolvin/pydantic/actions?query=event%3Apush+branch%3Amaster+workflow%3ACI)
[![Coverage](https://codecov.io/gh/samuelcolvin/pydantic/branch/master/graph/badge.svg)](https://codecov.io/gh/samuelcolvin/pydantic)
[![pypi](https://img.shields.io/pypi/v/pydantic.svg)](https://pypi.python.org/pypi/pydantic)
[![CondaForge](https://img.shields.io/conda/v/conda-forge/pydantic.svg)](https://anaconda.org/conda-forge/pydantic)
[![downloads](https://img.shields.io/pypi/dm/pydantic.svg)](https://pypistats.org/packages/pydantic)
[![versions](https://img.shields.io/pypi/pyversions/pydantic.svg)](https://github.com/samuelcolvin/pydantic)
[![license](https://img.shields.io/github/license/samuelcolvin/pydantic.svg)](https://github.com/samuelcolvin/pydantic/blob/master/LICENSE)

Data validation and settings management using Python type hinting.

Fast and extensible, *pydantic* plays nicely with your linters/IDE/brain.
Define how data should be in pure, canonical Python 3.6+; validate it with *pydantic*.

## Help

See [documentation](https://pydantic-docs.helpmanual.io/) for more details.

## Installation

Install using `pip install -U pydantic` or `conda install pydantic -c conda-forge`.
For more installation options to make *pydantic* even faster,
see the [Install](https://pydantic-docs.helpmanual.io/install/) section in the documentation.

## A Simple Example

```py
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel

class User(BaseModel):
    id: int
    name = 'John Doe'
    signup_ts: Optional[datetime] = None
    friends: List[int] = []

external_data = {'id': '123', 'signup_ts': '2017-06-01 12:22', 'friends': [1, '2', b'3']}
user = User(**external_data)
print(user)
#> User id=123 name='John Doe' signup_ts=datetime.datetime(2017, 6, 1, 12, 22) friends=[1, 2, 3]
print(user.id)
#> 123
```

## Contributing

For guidance on setting up a development environment and how to make a
contribution to *pydantic*, see
[Contributing to Pydantic](https://pydantic-docs.helpmanual.io/contributing/).

## Reporting a Security Vulnerability

See our [security policy](https://github.com/samuelcolvin/pydantic/security/policy).
