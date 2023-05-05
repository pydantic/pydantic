[![CI](https://github.com/pydantic/pydantic/workflows/CI/badge.svg?event=push)](https://github.com/pydantic/pydantic/actions?query=event%3Apush+branch%3Amain+workflow%3ACI)
[![Coverage](https://coverage-badge.samuelcolvin.workers.dev/pydantic/pydantic.svg)](https://github.com/pydantic/pydantic/actions?query=event%3Apush+branch%3Amain+workflow%3ACI)
[![pypi](https://img.shields.io/pypi/v/pydantic.svg)](https://pypi.python.org/pypi/pydantic)
[![CondaForge](https://img.shields.io/conda/v/conda-forge/pydantic.svg)](https://anaconda.org/conda-forge/pydantic)
[![downloads](https://pepy.tech/badge/pydantic/month)](https://pepy.tech/project/pydantic)
[![license](https://img.shields.io/github/license/pydantic/pydantic.svg)](https://github.com/pydantic/pydantic/blob/main/LICENSE)

{{ version }}.

Pydantic is the most widely used data validation library for Python.

With Pydantic, Python type annotations become more than tools for documentation and type checking. Pydantic **enforces type hints** at runtime, and provides **user-friendly errors** when data is invalid.

Pydantic is simple to use, even when doing complex things, and enables you to define and validate data in pure, canonical Python.

Try Pydantic today! [Installation](/install/) is as simple as: [`pip install pydantic`](/install/).

## Example

```py
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class User(BaseModel):
    id: int
    name: str = 'John Doe'
    signup_ts: Optional[datetime] = None
    friends: List[int] = []


external_data = {
    'id': '123',
    'signup_ts': '2019-06-01 12:22',
    'friends': [1, 2, '3'],
}
user = User(**external_data)
print(user.id)
#> 123
print(repr(user.signup_ts))
#> datetime.datetime(2019, 6, 1, 12, 22)
print(user.friends)
#> [1, 2, 3]
print(user.model_dump())
"""
{
    'id': 123,
    'name': 'John Doe',
    'signup_ts': datetime.datetime(2019, 6, 1, 12, 22),
    'friends': [1, 2, 3],
}
"""
```

What's going on here:

* `id` is of type int; the annotation-only declaration tells Pydantic that this field is required. Strings,
  bytes, or floats will be coerced to ints if possible; otherwise an exception will be raised.
* `name` is inferred as a string from the provided default; because it has a default, it is not required.
* `signup_ts` is a datetime field that is not required (and takes the value ``None`` if it's not supplied).
  Pydantic will process either a unix timestamp int (e.g. `1496498400`) or a string representing the date and time.
* `friends` uses Python's typing system, and requires a list of integers. As with `id`, integer-like objects
  will be converted to integers.

If validation fails, Pydantic will raise an error with a breakdown of what was wrong:

```py
from index_main import User

# ignore-above
from pydantic import ValidationError

try:
    User(signup_ts='broken', friends=[1, 2, 'not number'])
except ValidationError as e:
    print(e.errors())
    """
    [
        {
            'type': 'missing',
            'loc': ('id',),
            'msg': 'Field required',
            'input': {'signup_ts': 'broken', 'friends': [1, 2, 'not number']},
            'url': 'https://errors.pydantic.dev/2/v/missing',
        },
        {
            'type': 'datetime_parsing',
            'loc': ('signup_ts',),
            'msg': 'Input should be a valid datetime, input is too short',
            'input': 'broken',
            'ctx': {'error': 'input is too short'},
            'url': 'https://errors.pydantic.dev/2/v/datetime_parsing',
        },
        {
            'type': 'int_parsing',
            'loc': ('friends', 2),
            'msg': 'Input should be a valid integer, unable to parse string as an integer',
            'input': 'not number',
            'url': 'https://errors.pydantic.dev/2/v/int_parsing',
        },
    ]
    """
```


## Rationale

Pydantic uses some cool new language features, but why should I actually go and use it?

**Plays nicely with your IDE/linter/brain**
: There's no new schema definition micro-language to learn. If you know how to use Python type hints,
  you know how to use Pydantic. Data structures are just instances of classes you define with type annotations,
  so auto-completion, linting, [mypy](/integrations/mypy/), IDEs (especially [PyCharm](/integrations/pycharm/)),
  and your intuition should all work properly with your validated data.

**Fast**
: Pydantic has always taken performance seriously. The core validation logic of Pydantic 2 uses a separate `pydantic-core` package, written in Rust using the excellent `pyo3` library. This provides a significant speed up over the already excellent performance of Prefect 1.

**Validate complex structures**
: Use of [recursive Pydantic models](/usage/models/#recursive-models), `typing`'s
  [standard types](/usage/types/#standard-library-types) (e.g. `List`, `Tuple`, `Dict` etc.) and
  [validators](/usage/validators/) allow
  complex data schemas to be clearly and easily defined, validated, and parsed.

**Extensible**
: Pydantic allows [custom data types](/usage/types/#custom-data-types) to be defined or you can extend validation
  with methods on a model decorated with the [`validator`](/usage/validators/) decorator.

**Dataclasses integration**
: As well as `BaseModel`, Pydantic provides
  a [`dataclass`](/usage/dataclasses/) decorator which creates (almost) vanilla Python dataclasses with input
  data parsing and validation.

## Using Pydantic

Hundreds of organisations and packages are using Pydantic, including:

[FastAPI](https://fastapi.tiangolo.com/)
: A high performance API framework, easy to learn,
  fast to code and ready for production, based on Pydantic and Starlette.

[Project Jupyter](https://jupyter.org/)
: Developers of the Jupyter notebook are using Pydantic
  [for subprojects](https://github.com/pydantic/pydantic/issues/773), through the FastAPI-based Jupyter server
  [Jupyverse](https://github.com/jupyter-server/jupyverse), and for [FPS](https://github.com/jupyter-server/fps)'s
  configuration management.

**Microsoft**
: Using Pydantic (via FastAPI) for
  [numerous services](https://github.com/tiangolo/fastapi/pull/26#issuecomment-463768795), some of which are
  "getting integrated into the core Windows product and some Office products."

**Amazon Web Services**
: Uusing Pydantic in [gluon-ts](https://github.com/awslabs/gluon-ts), an open-source probabilistic time series
  modeling library.

**The NSA**
: Using Pydantic in [WALKOFF](https://github.com/nsacyber/WALKOFF), an open-source automation framework.

**Uber**
: Using Pydantic in [Ludwig](https://github.com/uber/ludwig), an open-source TensorFlow wrapper.

**Cuenca**
: A Mexican neobank that uses Pydantic for several internal
  tools (including API validation) and for open source projects like
  [stpmex](https://github.com/cuenca-mx/stpmex-python), which is used to process real-time, 24/7, inter-bank
  transfers in Mexico.

[The Molecular Sciences Software Institute](https://molssi.org)
: Using Pydantic in [QCFractal](https://github.com/MolSSI/QCFractal), a massively distributed compute framework
  for quantum chemistry.

[Reach](https://www.reach.vote)
: Trusts Pydantic (via FastAPI) and [*arq*](https://github.com/samuelcolvin/arq) (Samuel's excellent
  asynchronous task queue) to reliably power multiple mission-critical microservices.

[Robusta.dev](https://robusta.dev/)
: Using Pydantic to automate Kubernetes troubleshooting and maintenance. For example, their open source
  [tools to debug and profile Python applications on Kubernetes](https://home.robusta.dev/python/) use
  Pydantic models.

For a more comprehensive list of open-source projects using Pydantic see the
[list of dependents on github](https://github.com/pydantic/pydantic/network/dependents), or you can find some awesome projects using Pydantic in [awesome-pydantic](https://github.com/Kludex/awesome-pydantic).

## Discussion of Pydantic

Podcasts and videos discussing Pydantic.

[Talk Python To Me](https://talkpython.fm/episodes/show/313/automate-your-data-exchange-with-pydantic){target=_blank}
: Michael Kennedy and Samuel Colvin, the creator of Pydantic, dive into the history of Pydantic and its many uses and benefits.

[Podcast.\_\_init\_\_](https://www.pythonpodcast.com/pydantic-data-validation-episode-263/){target=_blank}
: Discussion about where Pydantic came from and ideas for where it might go next with
  Samuel Colvin the creator of Pydantic.

[Python Bytes Podcast](https://pythonbytes.fm/episodes/show/157/oh-hai-pandas-hold-my-hand){target=_blank}
: "*This is a sweet simple framework that solves some really nice problems... Data validations and settings management
  using Python type annotations, and it's the Python type annotations that makes me really extra happy... It works
  automatically with all the IDE's you already have.*" --Michael Kennedy

[Python Pydantic Introduction – Give your data classes super powers](https://www.youtube.com/watch?v=WJmqgJn9TXg){target=_blank}
: A talk by Alexander Hultnér originally for the Python Pizza Conference introducing new users to Pydantic and walking
  through the core features of Pydantic.
