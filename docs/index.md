[![CI](https://github.com/pydantic/pydantic/workflows/CI/badge.svg?event=push)](https://github.com/pydantic/pydantic/actions?query=event%3Apush+branch%3Amain+workflow%3ACI)
[![Coverage](https://coverage-badge.samuelcolvin.workers.dev/pydantic/pydantic.svg)](https://github.com/pydantic/pydantic/actions?query=event%3Apush+branch%3Amain+workflow%3ACI)<br>
[![pypi](https://img.shields.io/pypi/v/pydantic.svg)](https://pypi.python.org/pypi/pydantic)
[![CondaForge](https://img.shields.io/conda/v/conda-forge/pydantic.svg)](https://anaconda.org/conda-forge/pydantic)
[![downloads](https://pepy.tech/badge/pydantic/month)](https://pepy.tech/project/pydantic)<br>
[![license](https://img.shields.io/github/license/pydantic/pydantic.svg)](https://github.com/pydantic/pydantic/blob/main/LICENSE)

{{ version }}.

Pydantic is the most widely used data validation library for Python.

!!! success "Migrating to Pydantic V2"
    Already using Pydantic V1? See the [Migration Guide](migration.md) for notes on upgrading to Pydantic V2 in your applications!

```py lint="skip" upgrade="skip" title="Pydantic Example" requires="3.10"
from pydantic import BaseModel

class MyModel(BaseModel):
    a: int
    b: list[str]

m = MyModel(a=123, b=['a', 'b', 'c'])
print(m.model_dump())
#> {'a': 123, 'b': ['a', 'b', 'c']}
```

## Why use Pydantic?

- **Powered by type hints** &mdash; with Pydantic, schema validation and serialization are controlled by type annotations; less to learn, less code to write and integration with your IDE and static analysis tools.
- **Speed** &mdash; Pydantic's core validation logic is written in Rust, as a result Pydantic is among the fastest data validation libraries for Python.
- **JSON Schema** &mdash; Pydantic models can emit JSON Schema allowing for easy integration with other tools.
- **Strict** and **Lax** mode &mdash; Pydantic can run in either `strict=True` mode (where data is not converted) or `strict=False` mode where Pydantic tries to coerce data to the correct type where appropriate.
- **Dataclasses**, **TypedDicts** and more &mdash; Pydantic supports validation of many standard library types including `dataclass` and `TypedDict`.
- **Customisation** &mdash; Pydantic allows custom validators and serializers to alter how data is processed in many powerful ways.
- **Ecosystem** &mdash; around 8,000 packages on PyPI use Pydantic, including massively popular libraries like
  [FastAPI](https://github.com/tiangolo/fastapi),
  [huggingface/transformers](https://github.com/huggingface/transformers),
  [Django Ninja](https://github.com/vitalik/django-ninja),
  [SQLModel](https://github.com/tiangolo/sqlmodel),
  and [LangChain](https://github.com/hwchase17/langchain).
- **Battle tested** &mdash; Pydantic is downloaded >70m times/month and is used by all FAANG companies and 20 of the 25 largest companies on NASDAQ &mdash; if you're trying to do something with Pydantic, someone else has probably already done it.

[Installing Pydantic](install.md) is as simple as: [`pip install pydantic`](install.md)

## Pydantic examples

To see Pydantic at work, let's start with a simple example, creating a custom class that inherits from `BaseModel`:

```py upgrade="skip" title="Validation Successful" requires="3.10"
from datetime import datetime

from pydantic import BaseModel, PositiveInt


class User(BaseModel):
    id: int  # (1)!
    name: str = 'John Doe'  # (2)!
    signup_ts: datetime | None  # (3)!
    tastes: dict[str, PositiveInt]  # (4)!


external_data = {
    'id': 123,
    'signup_ts': '2019-06-01 12:22',  # (5)!
    'tastes': {
        'wine': 9,
        b'cheese': 7,  # (6)!
        'cabbage': '1',  # (7)!
    },
}

user = User(**external_data)  # (8)!

print(user.id)  # (9)!
#> 123
print(user.model_dump())  # (10)!
"""
{
    'id': 123,
    'name': 'John Doe',
    'signup_ts': datetime.datetime(2019, 6, 1, 12, 22),
    'tastes': {'wine': 9, 'cheese': 7, 'cabbage': 1},
}
"""
```

1. `id` is of type `int`; the annotation-only declaration tells Pydantic that this field is required. Strings,
  bytes, or floats will be coerced to ints if possible; otherwise an exception will be raised.
2. `name` is a string; because it has a default, it is not required.
3. `signup_ts` is a `datetime` field that is required, but the value `None` may be provided;
  Pydantic will process either a unix timestamp int (e.g. `1496498400`) or a string representing the date and time.
4. `tastes` is a dictionary with string keys and positive integer values. The `PositiveInt` type is shorthand for `Annotated[int, annotated_types.Gt(0)]`.
5. The input here is an ISO8601 formatted datetime, Pydantic will convert it to a `datetime` object.
6. The key here is `bytes`, but Pydantic will take care of coercing it to a string.
7. Similarly, Pydantic will coerce the string `'1'` to an integer `1`.
8. Here we create instance of `User` by passing our external data to `User` as keyword arguments
9. We can access fields as attributes of the model
10. We can convert the model to a dictionary with `model_dump()`

If validation fails, Pydantic will raise an error with a breakdown of what was wrong:

```py upgrade="skip" title="Validation Error" requires="3.10"
from datetime import datetime

from pydantic import BaseModel, PositiveInt, ValidationError


class User(BaseModel):
    id: int
    name: str = 'John Doe'
    signup_ts: datetime | None
    tastes: dict[str, PositiveInt]


external_data = {'id': 'not an int', 'tastes': {}}  # (1)!

try:
    User(**external_data)  # (2)!
except ValidationError as e:
    print(e.errors())
    """
    [
        {
            'type': 'int_parsing',
            'loc': ('id',),
            'msg': 'Input should be a valid integer, unable to parse string as an integer',
            'input': 'not an int',
            'url': 'https://errors.pydantic.dev/2/v/int_parsing',
        },
        {
            'type': 'missing',
            'loc': ('signup_ts',),
            'msg': 'Field required',
            'input': {'id': 'not an int', 'tastes': {}},
            'url': 'https://errors.pydantic.dev/2/v/missing',
        },
    ]
    """
```

1. The input data is wrong here &mdash; `id` is not a valid integer, and `signup_ts` is missing
2. `User(...)` will raise a `ValidationError` with a list of errors

## Who is using Pydantic?

Hundreds of organisations and packages are using Pydantic. Some of the prominent companies and organizations around the world who are using Pydantic include:

<div id="grid-container">
<div id="company-grid" class="grid"></div>
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

<script>
const companies = [
  {
    name: 'Adobe',
    logoUrl: 'logos/adobe_logo.png'
  },
  {
    name: 'AMD',
    logoUrl: 'logos/amd_logo.png'
  },
  {
    name: 'Amazon',
    logoUrl: 'logos/amazon_logo.png'
  },
  {
    name: 'Apple',
    logoUrl: 'logos/apple_logo.png'
  },
  {
    name: 'ASML',
    logoUrl: 'logos/asml_logo.png'
  },
  {
    name: 'AstraZeneca',
    logoUrl: 'logos/astrazeneca_logo.png'
  },
  {
    name: 'Broadcom',
    logoUrl: 'logos/broadcom_logo.png'
  },
  {
    name: 'Cisco Systems',
    logoUrl: 'logos/cisco_logo.png'
  },
  {
    name: 'Comcast',
    logoUrl: 'logos/comcast_logo.png'
  },
  {
    name: 'Datadog',
    logoUrl: 'logos/datadog_logo.png'
  },
  {
    name: 'Facebook',
    logoUrl: 'logos/facebook_logo.png'
  },
  {
    name: 'FastAPI',
    logoUrl: 'logos/fastapi_logo.png'
  },
  {
    name: 'Google',
    logoUrl: 'logos/google_logo.png'
  },
  {
    name: 'IBM',
    logoUrl: 'logos/ibm_logo.png'
  },
  {
    name: 'Intel',
    logoUrl: 'logos/intel_logo.png'
  },
  {
    name: 'Intuit',
    logoUrl: 'logos/intuit_logo.png'
  },
  {
    name: 'IPCC',
    logoUrl: 'logos/ipcc_logo.png'
  },
  {
    name: 'JPMorgan',
    logoUrl: 'logos/jpmorgan_logo.png'
  },
  {
    name: 'Jupyter',
    logoUrl: 'logos/jupyter_logo.png'
  },
  {
    name: 'Microsoft',
    logoUrl: 'logos/microsoft_logo.png'
  },
  {
    name: 'Molssi',
    logoUrl: 'logos/molssi_logo.png'
  },
  {
    name: 'NASA',
    logoUrl: 'logos/nasa_logo.png'
  },
  {
    name: 'Netflix',
    logoUrl: 'logos/netflix_logo.png'
  },
  {
    name: 'NSA',
    logoUrl: 'logos/nsa_logo.png'
  },
  {
    name: 'NVIDIA',
    logoUrl: 'logos/nvidia_logo.png'
  },
  {
    name: 'Qualcomm',
    logoUrl: 'logos/qualcomm_logo.png'
  },
  {
    name: 'Red Hat',
    logoUrl: 'logos/redhat_logo.png'
  },
  {
    name: 'Robusta',
    logoUrl: 'logos/robusta_logo.png'
  },
  {
    name: 'Salesforce',
    logoUrl: 'logos/salesforce_logo.png'
  },
  {
    name: 'Starbucks',
    logoUrl: 'logos/starbucks_logo.png'
  },
  {
    name: 'Texas Instruments',
    logoUrl: 'logos/ti_logo.png'
  },
  {
    name: 'Twilio',
    logoUrl: 'logos/twilio_logo.png'
  },
  {
    name: 'Twitter',
    logoUrl: 'logos/twitter_logo.png'
  },
  {
    name: 'UK Home Office',
    logoUrl: 'logos/ukhomeoffice_logo.png'
  }
];

const grid = document.getElementById('company-grid');

for (const company of companies) {
  const tile = document.createElement('div');
  tile.classList.add('tile');
  tile.innerHTML = `
    <img src="${company.logoUrl}" alt="${company.name}" />
  `;
  grid.appendChild(tile);
}
</script>
