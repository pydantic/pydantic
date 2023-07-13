# Why use Pydantic?

Today Pydantic is downloaded <span id="download-count">many</span> times a month, and used by some of the largest and most recognisable organisations in the world.

It's hard to know why so many people have adopted Pydantic since its inception six years ago, but here are a few guesses.

{% raw %}
## Type hints powering schema validation {#type-hints}
{% endraw %}

The schema that Pydantic validates against is generally defined by Python type hints.

Type hints are great for this since if you're writing modern Python, you already know how to use them.
Using type hints also means that Pydantic integrates well with static typing tools like mypy and pyright and IDEs like pycharm and vscode.

```py title="Type hints example - using a TypedDict"
from typing import Annotated, Dict, List, Literal, Tuple

from annotated_types import Gt

from pydantic import BaseModel


class Fruit(BaseModel):
    name: str  # (1)!
    color: Literal['red', 'green']  # (2)!
    weight: Annotated[float, Gt(0)]  # (3)!
    bazam: Dict[str, List[Tuple[int, bool, float]]]  # (4)!


print(
    Fruit(
        name='Apple',
        color='red',
        weight=4.2,
        bazam={'foobar': [(1, True, 0.1)]},
    )
)
#> name='Apple' color='red' weight=4.2 bazam={'foobar': [(1, True, 0.1)]}
```

1. The `name` field is simply annotated with `str` - any string is allowed.
2. The [`Literal`](https://docs.python.org/3/library/typing.html#typing.Literal) type is used to enforce that `color` is either `'red'` or `'green'`.
3. Even when we want to apply constraints not encapsulated in python types, we can use [`Annotated`](https://docs.python.org/3/library/typing.html#typing.Literal) and [`annotated-types`](https://github.com/annotated-types/annotated-types) to enforce constraints without breaking type hints.
4. I'm not claiming "bazam" is really an attribute of fruit, but rather to show that arbitrarily complex types can easily be validated.

## Performance

Pydantic's core validation logic is implemented in separate package [`pydantic-core`](https://github.com/pydantic/pydantic-core) where validation for most types is implemented in Rust.

As a result Pydantic is among the fastest data validation libraries for Python.

??? example "Performance example - Pydantic vs. dedicated code"
    In general, dedicate code should be much faster that a general purpose validator, but in this example
    Pydantic is >300% faster than dedicated code when parsing JSON and validating URLs.

    ```py title="Performance Example" test="skip"
    import json
    import timeit
    from urllib.parse import urlparse

    import requests

    from pydantic import HttpUrl, TypeAdapter

    reps = 7
    number = 100
    r = requests.get('https://api.github.com/emojis')
    r.raise_for_status()
    emojis_json = r.content


    def emojis_pure_python(raw_data):
        data = json.loads(raw_data)
        output = {}
        for key, value in data.items():
            assert isinstance(key, str)
            url = urlparse(value)
            assert url.scheme in ('https', 'http')
            output[key] = url


    emojis_pure_python_times = timeit.repeat(
        'emojis_pure_python(emojis_json)',
        globals={
            'emojis_pure_python': emojis_pure_python,
            'emojis_json': emojis_json,
        },
        repeat=reps,
        number=number,
    )
    print(f'pure python: {min(emojis_pure_python_times) / number * 1000:0.2f}ms')
    #> pure python: 5.32ms

    type_adapter = TypeAdapter(dict[str, HttpUrl])
    emojis_pydantic_times = timeit.repeat(
        'type_adapter.validate_json(emojis_json)',
        globals={
            'type_adapter': type_adapter,
            'HttpUrl': HttpUrl,
            'emojis_json': emojis_json,
        },
        repeat=reps,
        number=number,
    )
    print(f'pydantic: {min(emojis_pydantic_times) / number * 1000:0.2f}ms')
    #> pydantic: 1.54ms

    print(
        f'Pydantic {min(emojis_pure_python_times) / min(emojis_pydantic_times):0.2f}x faster'
    )
    #> Pydantic 3.45x faster
    ```

Unlike other performance centric libraries written in compiled languages, Pydantic also has excellent support for customising validation via [functional validators](#customisation).

## Serialization

Pydantic provide functionality to serialize model in three ways:

1. To a Python `dict` made up of the associated Python objects
2. To a Python `dict` made up only of "jsonable" types
3. To a JSON string

In all three modes the output can be customised by excluding fields, exclude default values, excluding `None` values and more.

TODO example of serialization 3 ways

## JSON Schema

[JSON Schema](https://json-schema.org/) (2020-12) can be generated for any Pydantic model &mdash; allowing self documenting APIs and integration with a wide variety of tools which support JSON Schema.

TODO example of JSON schema

{% raw %}
## Strict mode and data coercion {#strict-lax}
{% endraw %}

By default, Pydantic is tolerant to common incorrect types and coerces data to the right type - e.g. a numeric string passed to an `int` field will be parsed as an `int`.

Pydantic also has `strict=True` mode, where types are not coerced and a validation error is raised unless the input data exactly matches the schema or type hint.

TODO example of strict and lax mode

{% raw %}
## Dataclasses, TypedDicts and more {#typeddict}
{% endraw %}

Pydantic provides X ways to design schemas and perform validation and serialization:

1. `BaseModel` &mdash; Pydantic own super class with many common utilities available via instance methods
2. `pydantic.dataclasses.dataclass` &mdash; a wrapper around standard dataclasses which performs validation when a dataclass is initialised
3. `TypeAdapter` &mdash; general way to adapt any type for validation and serialization, this allows types like [`TypedDict`](https://docs.python.org/3/library/typing.html#typing.TypedDict) and [`NampedTuple`](https://docs.python.org/3/library/typing.html#typing.NamedTuple) to be validated as well as simple scalar values like `int` or `timedelta`
4. `validate_call` &mdash; decorator to perform validation when calling a function

TODO example of `TypedDict`.

## Customisation

Functional validators and serializers as well as a powerful protocol for custom types means the way Pydantic operates can be customised on a per field or per type basis.

TODO links and example of wrap validator

## Ecosystem

Some notable libraries that depend on Pydantic:

TODO proper list with stars auto collected

* [FastAPI](https://github.com/tiangolo/fastapi)
* [huggingface/transformers](https://github.com/huggingface/transformers)
* [Django Ninja](https://github.com/vitalik/django-ninja)
* [SQLModel](https://github.com/tiangolo/sqlmodel)
* [LangChain](https://github.com/hwchase17/langchain)

{% raw %}
## Organisations using Pydantic {#using-pydantic}

Some notable companies and organisations using Pydantic:

### Adobe {#org-adobe}

Traffic to the Pydantic docs from their internal wiki and git hosting under the `adobe.com` domain.

### AMD {#org-amd}

?

### Amazon {#org-amazon}

[powertools-lambda-python](https://github.com/aws-powertools/powertools-lambda-python) uses Pydantic, AWS sponsored Samuel Colvin $5,000 to work on Pydantic in 2022.

### Apple {#org-apple}

Traffic to the Pydantic docs from multiple enterprise GitHub instances under the `apple.com` domain.

### ASML {#org-asml}

Traffic to the Pydantic docs from enterprise bitbucket and jira instances under the `asml.com` domain.

### AstraZeneca {#org-astrazeneca}

Traffic to the Pydantic docs from a sub-domain of `astrazeneca.com` domain.

[Multiple repos](https://github.com/search?q=org%3AAstraZeneca+pydantic&type=code) in the `AstraZeneca` GitHub org depend on Pydantic.

### Broadcom {#org-broadcom}

?

### Cisco Systems {#org-cisco}

Pydantic is listed in their report of [Open Source Used In RADKit](https://www.cisco.com/c/dam/en_us/about/doing_business/open_source/docs/RADKit-149-1687424532.pdf).

[`cisco/webex-assistant-sdk`](https://github.com/cisco/webex-assistant-sdk) repo depends on Pydantic.

### Comcast {#org-comcast}

Traffic to the Pydantic docs from an internal wiki and enterprise GitHub instance under the `comcast.com` domain.

### Datadog {#org-datadog}

Extensive use of Pydantic in [`DataDog/integrations-core`](https://github.com/DataDog/integrations-core) and other repos.

Communication with engineers from Datadog about how they use Pydantic.

### Facebook {#org-facebook}

[Multiple repos](https://github.com/search?q=org%3Afacebookresearch+pydantic&type=code) in the `facebookresearch` GitHub org depend on Pydantic.

### Google {#org-google}

Extensive use of Pydantic in [`google/turbinia`](https://github.com/google/turbinia) and other repos.

### IBM {#org-ibm}

[Multiple repos](https://github.com/search?q=org%3AIBM+pydantic&type=code) in the `IBM` GitHub org depend on Pydantic.

Traffic to the Pydantic docs from an enterprise GitHub instance under the `ibm.com` domain.

### Intel {#org-intel}

Traffic to the Pydantic docs from wikis and jira instances under the `intel.com` domain.

### Intuit {#org-intuit}

Traffic to the Pydantic docs from an enterprise GitHub instance under the `ntuit.com` domain.

### Intergovernmental Panel on Climate Change {#org-ipcc}

[Tweet](https://twitter.com/daniel_huppmann/status/1563461797973110785) explaining how the IPCC use Pydantic.

### JPMorgan {#org-jpmorgan}

Traffic to the Pydantic docs from an enterprise bitbucket instances under the `jpmchase.net` domain.

### Jupyter {#org-jupyter}

TODO

### Microsoft {#org-microsoft}

TODO

### Molssi {#org-molssi}

TODO

### NASA {#org-nasa}

TODO

### Netflix {#org-netflix}

TODO

### NSA {#org-nsa}

TODO

### NVIDIA {#org-nvidia}

TODO

### Qualcomm {#org-qualcomm}

TODO

### Red Hat {#org-redhat}

TODO

### Robusta {#org-robusta}

TODO

### Salesforce {#org-salesforce}

TODO

### Starbucks {#org-starbucks}

TODO

### Texas Instruments {#org-ti}

TODO

### Twilio {#org-twilio}

TODO

### Twitter {#org-twitter}

TODO

### UK Home Office {#org-ukhomeoffice}
{% endraw %}
