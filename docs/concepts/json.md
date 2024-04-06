!!! warning "🚧 Work in Progress"
    This page is a work in progress.

# JSON

## Json Parsing

??? api "API Documentation"
    [`pydantic.main.BaseModel.model_validate_json`][pydantic.main.BaseModel.model_validate_json]
    [`pydantic.type_adapter.TypeAdapter.validate_json`][pydantic.type_adapter.TypeAdapter.validate_json]
    [`pydantic_core.from_json`][pydantic_core.from_json]

Pydantic provides builtin JSON parsing, which helps achieve:

* Significant performance improvements without the cost of using a 3rd party library
* Support for custom errors
* Support for `strict` specifications

Here's an example of Pydantic's builtin JSON parsing via the [`model_validate_json`][pydantic.main.BaseModel.model_validate_json] method, showcasing the support for `strict` specifications while parsing JSON data that doesn't match the model's type annotations:

```py
from datetime import date
from typing import Tuple

from pydantic import BaseModel, ConfigDict, ValidationError


class Event(BaseModel):
    model_config = ConfigDict(strict=True)

    when: date
    where: Tuple[int, int]


json_data = '{"when": "1987-01-28", "where": [51, -1]}'
print(Event.model_validate_json(json_data))  # (1)!
#> when=datetime.date(1987, 1, 28) where=(51, -1)

try:
    Event.model_validate({'when': '1987-01-28', 'where': [51, -1]})  # (2)!
except ValidationError as e:
    print(e)
    """
    2 validation errors for Event
    when
      Input should be a valid date [type=date_type, input_value='1987-01-28', input_type=str]
    where
      Input should be a valid tuple [type=tuple_type, input_value=[51, -1], input_type=list]
    """
```

1. JSON has no `date` or tuple types, but Pydantic knows that so allows strings and arrays as inputs respectively when parsing JSON directly.
2. If you pass the same values to the [`model_validate`][pydantic.main.BaseModel.model_validate] method, Pydantic will raise a validation error because the `strict` configuration is enabled.

In v2.5.0 and above, Pydantic uses [`jiter`](https://docs.rs/jiter/latest/jiter/), a fast and iterable JSON parser, to parse JSON data.
Using `jiter` compared to `serde` results in modest performance improvements that will get even better in the future.

The `jiter` JSON parser is almost entirely compatible with the `serde` JSON parser,
with one noticeable enhancement being that `jiter` supports deserialization of `inf` and `NaN` values.
In the future, `jiter` is intended to enable support validation errors to include the location
in the original JSON input which contained the invalid value.

### Partial JSON Parsing

Starting in v2.7.0 and above, Pydantic's [JSON parser](https://docs.rs/jiter/latest/jiter/) offers support for partial JSON parsing, which is exposed via [`pydantic_core.from_json`][pydantic_core.from_json]. Here's an example of this feature in action:

```py
from pydantic_core import from_json


partial_json_data = '["aa", "bb", "c' # (1)!

try:
    result = from_json(partial_json_data, allow_partial=False)
except ValueError as ve:
    print(ve)
    # > EOF while parsing a string at line 1 column 15 # (2)

result = from_json(partial_json_data, allow_partial=True)
print(result)
# > ['aa', 'bb'] # (3)
```

1. The JSON list is incomplete - it's missing a closing `"]`
2. When `allow_partial` is set to `False`, a parsing error occurs.
3. When `allow_partial` is set to `True`, part of the input is deserialized successfully.

This also works for deserializing partial dictionaries. For example:

```py
from pydantic_core import from_json


partial_dog_json = '{"breed": "lab", "name": "fluffy", "friends": ["buddy", "spot", "rufus"], "age}'
dog_dict = from_json(partial_dog_json, allow_partial=True)
print(dog_dict)
#> {'breed': 'lab', 'name': 'fluffy', 'friends': ['buddy', 'spot', 'rufus']}
```

!!! tip "Validating LLM Output"
    This feature is particularly beneficial for validating LLM outputs.
    We've written some blog posts about this topic, which you can find [here](#TODO: insert link filtered on LLMs).

In future versions of Pydantic, we expect to expand support for this feature through either Pydantic's other JSON validation functions
([`pydantic.main.BaseModel.model_validate_json`][pydantic.main.BaseModel.model_validate_json] and
[`pydantic.type_adapter.TypeAdapter.validate_json`][pydantic.type_adapter.TypeAdapter.validate_json]) or model configuration. Stay tuned 🚀!

### Caching Strings

Starting in v2.7.0 and above, Pydantic's [JSON parser](https://docs.rs/jiter/latest/jiter/) offers support for string caching.
The `cache_strings` setting is exposed via both [model config][pydantic.config.ConfigDict] and [`pydantic_core.from_json`][pydantic_core.from_json].

The `cache_strings` setting can take any of the following values:

* `True` or `'all'`: cache all strings
* `keys`: cache only dictionary keys
* `False` or `none` (the default): no caching

Using the string caching feature results in performance improvements, but increases memory usage slightly.

## JSON Serialization

??? api "API Documentation"
    [`pydantic.main.BaseModel.model_dump_json`][pydantic.main.BaseModel.model_dump_json]<br>
    [`pydantic.type_adapter.TypeAdapter.dump_json`][pydantic.type_adapter.TypeAdapter.dump_json]<br>
    [`pydantic_core.to_json`][pydantic_core.to_json]<br>

For more information on JSON serialization, see the [Serialization Concepts](./serialization.md#modelmodel_dump_json) page.
