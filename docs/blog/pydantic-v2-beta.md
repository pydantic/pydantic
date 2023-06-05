# Pydantic V2 Beta Release

<aside class="blog" markdown>
![Terrence Dorsey](../img/terrencedorsey.jpg)
<div markdown>
  **Terrence Dorsey & Samuel Colvin** &bull;&nbsp;
  [:material-github:](https://github.com/pydantic) &bull;&nbsp;
  [:material-twitter:](https://twitter.com/pydantic) &bull;&nbsp;
  :octicons-calendar-24: June 3, 2023 &bull;&nbsp;
  :octicons-clock-24: 8 min read
</div>
</aside>

---

Today we're thrilled to announce the beta release of Pydantic V2!

Working from the first Pydantic V2 alpha, we've spent the last two months making further improvements based us your feedback.

At this point, we believe that the API is stable enough for you to start using it in your production projects. We'll continue to make improvements and bug fixes, but the API is (mostly) complete.

## Getting started with the Pydantic V2 beta

Your feedback will be a critical part of ensuring that we have made the right tradeoffs with the API changes in V2.

To get started with the Pydantic V2 beta release, install it from PyPI.
We recommend using a virtual environment to isolate your testing environment:

```bash
pip install --pre -U "pydantic>=2.0b1"
```

If you encounter any issues, please [create an issue in GitHub](https://github.com/pydantic/pydantic/issues)
using the `bug V2` label. This will help us to actively monitor and track errors, and to continue to improve
the library’s performance.

Thank you for your support, and we look forward to your feedback.

---

## Headlines

### `RootModel`

## Migration notes

### Overriding validators

### `@root_validator` signature changes

### `@validate_arguments` raises `TypeError` if called with an invalid signature

### Subclass checks on generics no longer work

### Handling large integers

Pydantic casts large integer values to an `i64` so values larger than `i64:MAX` may be lose precision. In addition, sub-type information is lost.

If you must use integer values larger than `i64:MAX` and want to keep subtype information, you should use an
`is-instance` validator and your own validator functions.

### Subclasses of builtins

### Support for `__root__`

### Changes to `__concrete__` and `__parameters__` on generic models

### `each_item` validators

### `parse_file` and `parse_raw` no longer supported

### `stricturl` removed

### Model equals comparison no longer considers dicts equal

### `always=True` and `validate_default` apply "standard" field validation

### JSON schema no longer preserves named tuples

### List, set, and frozenset fields no long accept plain dict or mapping as input

### Coercing fields in a union

In Pydantic V2, the `Union` type no longer coerces values to the first type in the union that can accept the value.

```python
from datetime import datetime
from typing import Union

from pydantic import BaseModel


class DateModel(BaseModel):
    just_date: date
    date_or_str: Union[date, str]


print(DateModel(just_date='2023-01-01', date_or_str='2023-01-01').dict())
#> {'just_date': datetime.date(2023, 1, 1), 'date_or_str': '2023-01-01'}
```

Pydantic V1 would coercing a value to the first member of a union even when it exactly matches a latter member of the unions.

See [#5991](https://github.com/pydantic/pydantic/issues/5991) for further details.
