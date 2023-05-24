[![CI](https://github.com/pydantic/pydantic/workflows/CI/badge.svg?event=push)](https://github.com/pydantic/pydantic/actions?query=event%3Apush+branch%3Amain+workflow%3ACI)
[![Coverage](https://coverage-badge.samuelcolvin.workers.dev/pydantic/pydantic.svg)](https://github.com/pydantic/pydantic/actions?query=event%3Apush+branch%3Amain+workflow%3ACI)<br>
[![pypi](https://img.shields.io/pypi/v/pydantic.svg)](https://pypi.python.org/pypi/pydantic)
[![CondaForge](https://img.shields.io/conda/v/conda-forge/pydantic.svg)](https://anaconda.org/conda-forge/pydantic)
[![downloads](https://pepy.tech/badge/pydantic/month)](https://pepy.tech/project/pydantic)<br>
[![license](https://img.shields.io/github/license/pydantic/pydantic.svg)](https://github.com/pydantic/pydantic/blob/main/LICENSE)

{{ version }}.

Pydantic is the most widely used Python library for data validation and coercion using Python type annotations.

## Why use Pydantic?

Built-in Python type annotations are a useful way to hint about the expected type of data, improving code clarity and supporting development tools. However, Python's type annotations are optional and don't affect the runtime behavior of the program.

Static type checkers like [mypy](https://mypy-lang.org/) use type annotations to catch potential type-related errors before running the program. But static type checkers can't catch all errors, and they don't affect the runtime behavior of the program.

Pydantic, on the other hand, uses type annotations to perform [data validation](/usage/validators.md) and [type coercion](/usage/conversion_table.md) at runtime, which is particularly useful for ensuring the correctness of user or external data.

Pydantic enables you to convert input data to Python [standard library types and custom types](/usage/types/types.md) in a controlled manner, ensuring they meet the specifications you've provided. This eliminates a significant amount of manual data validation and transformation code, making your program more robust and less prone to errors. It's particularly helpful when dealing with untrusted user input such as form data, [JSON documents](/usage/schema.md), and other data types.

By providing a simple, declarative way of defining how data should be shaped, Pydantic helps you write cleaner, safer, and more reliable code.

## Features of Pydantic

Some of the main features of Pydantic include:

- [**Data validation**](/usage/validators.md): Pydantic validates data as it is assigned to ensure it meets the requirements. It automatically handles a broad range of data types, including custom types and custom validators.
- [**Standard library and custom data types**](/usage/types/types.md): Pydantic supports all of the Python standard library types, and you can define custom data types and specify how they should be validated and converted.
- [**Conversion types**](/usage/conversion_table.md): Pydantic will not only validate data, but also convert it to the appropriate type if possible. For instance, a string containing a number will be converted to the proper numerical type.
- [**Custom and nested models**](/usage/models.md): You can define models (similar to classes) that contain other models, allowing for complex data structures to be neatly and efficiently represented.
- [**Generic models**](/usage/models.md/#generic-models): Pydantic supports generic models, which allow the declaration of models that are "parameterized" on one or more fields.
- [**Dataclasses**](/usage/dataclasses.md): Pydantic supports `dataclasses.dataclass`, offering same data validation as using `BaseModel`.
- [**Model schema generation**](/usage/schema.md): Pydantic models can be converted to and from a JSON Schema, which can be useful for documentation, code generation, or other purposes.
- [**Error handling**](/errors/errors.md): Pydantic models raise informative errors when invalid data is provided, with the option to create your own [custom errors](/errors/errors.md/#custom-errors).
- [**Settings management**](/usage/pydantic_settings.md): The `BaseSettings` class from [pydantic-settings](https://github.com/pydantic/pydantic-settings) provides a way to validate, document, and provide default values for environment variables.

Pydantic is simple to use, even when doing complex things, and enables you to define and validate data in pure, canonical Python.

[Installing Pydantic](install.md) is as simple as: [`pip install pydantic`](install.md).

## Pydantic examples

To see Pydantic at work, let's start with a simple example, creating a custom class that inherits from `BaseModel`:

```py
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class User(BaseModel):
    id: int
    name: str = 'John Doe'
    signup_ts: Optional[datetime] = None


external_data = {
    'id': '123',
    'signup_ts': '2019-06-01 12:22',
}

user = User(**external_data)

print(user.model_dump())
#> {'id': 123, 'name': 'John Doe', 'signup_ts': datetime.datetime(2019, 6, 1, 12, 22)}
```

What's going on here:

* `id` is of type `int`; the annotation-only declaration tells Pydantic that this field is required. Strings,
  bytes, or floats will be coerced to ints if possible; otherwise an exception will be raised.
* `name` is inferred as a string from the provided default; because it has a default, it is not required.
* `signup_ts` is a `datetime` field that is not required (and takes the value `None` if a value is not supplied).
  Pydantic will process either a unix timestamp int (e.g. `1496498400`) or a string representing the date and time.

If validation fails, Pydantic will raise an error with a breakdown of what was wrong:

```py
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ValidationError


class User(BaseModel):
    id: int
    name: str = 'John Doe'
    signup_ts: Optional[datetime] = None


try:
    User(name=1234)
except ValidationError as e:
    print(e.errors())
    """
    [
        {
            'type': 'missing',
            'loc': ('id',),
            'msg': 'Field required',
            'input': {'name': 1234},
            'url': 'https://errors.pydantic.dev/2/v/missing',
        },
        {
            'type': 'string_type',
            'loc': ('name',),
            'msg': 'Input should be a valid string',
            'input': 1234,
            'url': 'https://errors.pydantic.dev/2/v/string_type',
        },
    ]
    """
```

## Who is using Pydantic?

Hundreds of organisations and packages are using Pydantic.

Some of the prominent projects using Pydantic include:

[FastAPI](https://fastapi.tiangolo.com/) &mdash; A high-performance API framework, easy to learn,
  fast to code and ready for production, based on Pydantic and Starlette.

[Project Jupyter](https://jupyter.org/) &mdash; Developers of the Jupyter notebook are using Pydantic
  [for subprojects](https://github.com/pydantic/pydantic/issues/773), through the FastAPI-based Jupyter server
  [Jupyverse](https://github.com/jupyter-server/jupyverse), and for [FPS](https://github.com/jupyter-server/fps)'s
  configuration management.

[The Molecular Sciences Software Institute](https://molssi.org) &mdash; Using Pydantic in
  [QCFractal](https://github.com/MolSSI/QCFractal), a massively distributed compute framework
  for quantum chemistry.

[Reach](https://www.reach.vote) &mdash; Trusts Pydantic (via FastAPI) and [*arq*](https://github.com/samuelcolvin/arq)
  (Samuel's excellent asynchronous task queue) to reliably power multiple mission-critical microservices.

[Robusta.dev](https://robusta.dev/) &mdash; Using Pydantic to automate Kubernetes troubleshooting and maintenance.
  For example, their open source
  [tools to debug and profile Python applications on Kubernetes](https://home.robusta.dev/python/) use
  Pydantic models.

And these are just a few of the companies and organizations around the world who are using Pydantic:

<div style="float: left; width: 50%;">
<ul>
<li>Adobe
<li>Advanced Micro Devices
<li>Amazon
<li>Apple
<li>ASML
<li>AstraZeneca
<li>Broadcom
<li>Cisco Systems
<li>Comcast
<li>Datadog
<li>Exoflare
<li>Exposion AI
<li>Facebook
<li>Forethought AI
<li>Google
</ul>
</div>
<div style="float: right; width: 50%;">
<ul>
<li>IBM
<li>Intel
<li>Intuit
<li>Microsoft
<li>Netflix
<li>NSA
<li>NVIDIA
<li>Qualcomm
<li>Red Hat
<li>Salesforce
<li>Starbucks
<li>Telstra
<li>Texas Instruments
<li>Twilio
<li>UK Home Office
</ul>
</div>

For a more comprehensive list of open-source projects using Pydantic see the
[list of dependents on github](https://github.com/pydantic/pydantic/network/dependents), or you can find some awesome projects using Pydantic in [awesome-pydantic](https://github.com/Kludex/awesome-pydantic).

<!-- ## Discussion of Pydantic

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
  through the core features of Pydantic. -->
