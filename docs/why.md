# Why use Pydantic?

Today, Pydantic is downloaded <span id="download-count">many</span> times a month and used by some of the largest and most recognisable organisations in the world.

It's hard to know why so many people have adopted Pydantic since its inception six years ago, but here are a few guesses.

## Type hints powering schema validation {#type-hints}

The schema that Pydantic validates against is generally defined by Python [type hints](https://docs.python.org/3/glossary.html#term-type-hint).

Type hints are great for this since, if you're writing modern Python, you already know how to use them.
Using type hints also means that Pydantic integrates well with static typing tools
(like [mypy](https://www.mypy-lang.org/) and [Pyright](https://github.com/microsoft/pyright/))
and IDEs (like [PyCharm](https://www.jetbrains.com/pycharm/) and [VSCode](https://code.visualstudio.com/)).

???+ example "Example - just type hints"
    _(This example requires Python 3.9+)_
    ```python {requires="3.9"}
    from typing import Annotated, Literal

    from annotated_types import Gt

    from pydantic import BaseModel


    class Fruit(BaseModel):
        name: str  # (1)!
        color: Literal['red', 'green']  # (2)!
        weight: Annotated[float, Gt(0)]  # (3)!
        bazam: dict[str, list[tuple[int, bool, float]]]  # (4)!


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

    1. The `name` field is simply annotated with `str` &mdash; any string is allowed.
    2. The [`Literal`][typing.Literal] type is used to enforce that `color` is either `'red'` or `'green'`.
    3. Even when we want to apply constraints not encapsulated in Python types, we can use [`Annotated`][typing.Annotated]
       and [`annotated-types`](https://github.com/annotated-types/annotated-types) to enforce constraints while still keeping typing support.
    4. I'm not claiming "bazam" is really an attribute of fruit, but rather to show that arbitrarily complex types can easily be validated.

!!! tip "Learn more"
    See the [documentation on supported types](concepts/types.md).

## Performance

Pydantic's core validation logic is implemented in a separate package ([`pydantic-core`](https://github.com/pydantic/pydantic-core)),
where validation for most types is implemented in Rust.

As a result, Pydantic is among the fastest data validation libraries for Python.

??? example "Performance Example - Pydantic vs. dedicated code"
    In general, dedicated code should be much faster than a general-purpose validator, but in this example
    Pydantic is >300% faster than dedicated code when parsing JSON and validating URLs.

    ```python {title="Performance Example" test="skip"}
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

Unlike other performance-centric libraries written in compiled languages, Pydantic also has excellent support for customizing validation via [functional validators](#customisation).

!!! tip "Learn more"
    Samuel Colvin's [talk at PyCon 2023](https://youtu.be/pWZw7hYoRVU) explains how [`pydantic-core`](https://github.com/pydantic/pydantic-core)
    works and how it integrates with Pydantic.

## Serialization

Pydantic provides functionality to serialize model in three ways:

1. To a Python `dict` made up of the associated Python objects.
2. To a Python `dict` made up only of "jsonable" types.
3. To a JSON string.

In all three modes, the output can be customized by excluding specific fields, excluding unset fields, excluding default values, and excluding `None` values.

??? example "Example - Serialization 3 ways"

    ```python
    from datetime import datetime

    from pydantic import BaseModel


    class Meeting(BaseModel):
        when: datetime
        where: bytes
        why: str = 'No idea'


    m = Meeting(when='2020-01-01T12:00', where='home')
    print(m.model_dump(exclude_unset=True))
    #> {'when': datetime.datetime(2020, 1, 1, 12, 0), 'where': b'home'}
    print(m.model_dump(exclude={'where'}, mode='json'))
    #> {'when': '2020-01-01T12:00:00', 'why': 'No idea'}
    print(m.model_dump_json(exclude_defaults=True))
    #> {"when":"2020-01-01T12:00:00","where":"home"}
    ```

!!! tip "Learn more"
    See the [documentation on serialization](concepts/serialization.md).

## JSON Schema

A [JSON Schema](https://json-schema.org/) can be generated for any Pydantic schema &mdash; allowing self-documenting APIs and integration with a wide variety of tools which support the JSON Schema format.

??? example "Example - JSON Schema"

    ```python
    from datetime import datetime

    from pydantic import BaseModel


    class Address(BaseModel):
        street: str
        city: str
        zipcode: str


    class Meeting(BaseModel):
        when: datetime
        where: Address
        why: str = 'No idea'


    print(Meeting.model_json_schema())
    """
    {
        '$defs': {
            'Address': {
                'properties': {
                    'street': {'title': 'Street', 'type': 'string'},
                    'city': {'title': 'City', 'type': 'string'},
                    'zipcode': {'title': 'Zipcode', 'type': 'string'},
                },
                'required': ['street', 'city', 'zipcode'],
                'title': 'Address',
                'type': 'object',
            }
        },
        'properties': {
            'when': {'format': 'date-time', 'title': 'When', 'type': 'string'},
            'where': {'$ref': '#/$defs/Address'},
            'why': {'default': 'No idea', 'title': 'Why', 'type': 'string'},
        },
        'required': ['when', 'where'],
        'title': 'Meeting',
        'type': 'object',
    }
    """
    ```

Pydantic is compliant with the latest version of JSON Schema specification
([2020-12](https://json-schema.org/draft/2020-12/release-notes.html)), which
is compatible with [OpenAPI 3.1](https://spec.openapis.org/oas/v3.1.0.html).

!!! tip "Learn more"
    See the [documentation on JSON Schema](concepts/json_schema.md).

## Strict mode and data coercion {#strict-lax}

By default, Pydantic is tolerant to common incorrect types and coerces data to the right type &mdash;
e.g. a numeric string passed to an `int` field will be parsed as an `int`.

Pydantic also has as [strict mode](concepts/strict_mode.md), where types are not coerced and a
validation error is raised unless the input data exactly matches the expected schema.

But strict mode would be pretty useless when validating JSON data since JSON doesn't have types matching
many common Python types like [`datetime`][datetime.datetime], [`UUID`][uuid.UUID] or [`bytes`][].

To solve this, Pydantic can parse and validate JSON in one step. This allows sensible data conversion
(e.g. when parsing strings into [`datetime`][datetime.datetime] objects). Since the JSON parsing is
implemented in Rust, it's also very performant.

??? example "Example - Strict mode that's actually useful"

    ```python
    from datetime import datetime

    from pydantic import BaseModel, ValidationError


    class Meeting(BaseModel):
        when: datetime
        where: bytes


    m = Meeting.model_validate({'when': '2020-01-01T12:00', 'where': 'home'})
    print(m)
    #> when=datetime.datetime(2020, 1, 1, 12, 0) where=b'home'
    try:
        m = Meeting.model_validate(
            {'when': '2020-01-01T12:00', 'where': 'home'}, strict=True
        )
    except ValidationError as e:
        print(e)
        """
        2 validation errors for Meeting
        when
          Input should be a valid datetime [type=datetime_type, input_value='2020-01-01T12:00', input_type=str]
        where
          Input should be a valid bytes [type=bytes_type, input_value='home', input_type=str]
        """

    m_json = Meeting.model_validate_json(
        '{"when": "2020-01-01T12:00", "where": "home"}'
    )
    print(m_json)
    #> when=datetime.datetime(2020, 1, 1, 12, 0) where=b'home'
    ```

!!! tip "Learn more"
    See the [documentation on strict mode](concepts/strict_mode.md).

## Dataclasses, TypedDicts, and more {#dataclasses-typeddict-more}

Pydantic provides four ways to create schemas and perform validation and serialization:

1. [`BaseModel`](concepts/models.md) &mdash; Pydantic's own super class with many common utilities available via instance methods.
2. [Pydantic dataclasses](concepts/dataclasses.md) &mdash; a wrapper around standard dataclasses with additional validation performed.
3. [`TypeAdapter`][pydantic.type_adapter.TypeAdapter] &mdash; a general way to adapt any type for validation and serialization.
   This allows types like [`TypedDict`](api/standard_library_types.md#typeddict) and [`NamedTuple`](api/standard_library_types.md#typingnamedtuple)
   to be validated as well as simple types (like [`int`][] or [`timedelta`][datetime.timedelta]) &mdash; [all types](concepts/types.md) supported
   can be used with [`TypeAdapter`][pydantic.type_adapter.TypeAdapter].
4. [`validate_call`](concepts/validation_decorator.md) &mdash; a decorator to perform validation when calling a function.

??? example "Example - schema based on a [`TypedDict`][typing.TypedDict]"

    ```python
    from datetime import datetime

    from typing_extensions import NotRequired, TypedDict

    from pydantic import TypeAdapter


    class Meeting(TypedDict):
        when: datetime
        where: bytes
        why: NotRequired[str]


    meeting_adapter = TypeAdapter(Meeting)
    m = meeting_adapter.validate_python(  # (1)!
        {'when': '2020-01-01T12:00', 'where': 'home'}
    )
    print(m)
    #> {'when': datetime.datetime(2020, 1, 1, 12, 0), 'where': b'home'}
    meeting_adapter.dump_python(m, exclude={'where'})  # (2)!

    print(meeting_adapter.json_schema())  # (3)!
    """
    {
        'properties': {
            'when': {'format': 'date-time', 'title': 'When', 'type': 'string'},
            'where': {'format': 'binary', 'title': 'Where', 'type': 'string'},
            'why': {'title': 'Why', 'type': 'string'},
        },
        'required': ['when', 'where'],
        'title': 'Meeting',
        'type': 'object',
    }
    """
    ```

    1. [`TypeAdapter`][pydantic.type_adapter.TypeAdapter] for a [`TypedDict`][typing.TypedDict] performing validation,
       it can also validate JSON data directly with [`validate_json`][pydantic.type_adapter.TypeAdapter.validate_json].
    2. [`dump_python`][pydantic.type_adapter.TypeAdapter.dump_python] to serialise a [`TypedDict`][typing.TypedDict]
       to a python object, it can also serialise to JSON with [`dump_json`][pydantic.type_adapter.TypeAdapter.dump_json].
    3. [`TypeAdapter`][pydantic.type_adapter.TypeAdapter] can also generate a JSON Schema.

## Customisation

Functional validators and serializers, as well as a powerful protocol for custom types, means the way Pydantic operates can be customized on a per-field or per-type basis.

??? example "Customisation Example - wrap validators"
    "wrap validators" are new in Pydantic V2 and are one of the most powerful ways to customize validation.

    ```python
    from datetime import datetime, timezone
    from typing import Any

    from pydantic_core.core_schema import ValidatorFunctionWrapHandler

    from pydantic import BaseModel, field_validator


    class Meeting(BaseModel):
        when: datetime

        @field_validator('when', mode='wrap')
        def when_now(
            cls, input_value: Any, handler: ValidatorFunctionWrapHandler
        ) -> datetime:
            if input_value == 'now':
                return datetime.now()
            when = handler(input_value)
            # in this specific application we know tz naive datetimes are in UTC
            if when.tzinfo is None:
                when = when.replace(tzinfo=timezone.utc)
            return when


    print(Meeting(when='2020-01-01T12:00+01:00'))
    #> when=datetime.datetime(2020, 1, 1, 12, 0, tzinfo=TzInfo(+01:00))
    print(Meeting(when='now'))
    #> when=datetime.datetime(2032, 1, 2, 3, 4, 5, 6)
    print(Meeting(when='2020-01-01T12:00'))
    #> when=datetime.datetime(2020, 1, 1, 12, 0, tzinfo=datetime.timezone.utc)
    ```

!!! tip "Learn more"
    See the documentation on [validators](concepts/validators.md), [custom serializers](concepts/serialization.md#custom-serializers), and [custom types](concepts/types.md#custom-types).

## Ecosystem

At the time of writing there are 466,400 repositories on GitHub and 8,119 packages on PyPI that depend on Pydantic.

Some notable libraries that depend on Pydantic:

{{ libraries }}

More libraries using Pydantic can be found at [`Kludex/awesome-pydantic`](https://github.com/Kludex/awesome-pydantic).

## Organisations using Pydantic {#using-pydantic}

Some notable companies and organisations using Pydantic together with comments on why/how we know they're using Pydantic.

The organisations below are included because they match one or more of the following criteria:

* Using Pydantic as a dependency in a public repository.
* Referring traffic to the Pydantic documentation site from an organization-internal domain &mdash; specific referrers are not included since they're generally not in the public domain.
* Direct communication between the Pydantic team and engineers employed by the organization about usage of Pydantic within the organization.

We've included some extra detail where appropriate and already in the public domain.

{{ organisations }}
