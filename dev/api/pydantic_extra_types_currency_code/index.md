Currency definitions that are based on the [ISO4217](https://en.wikipedia.org/wiki/ISO_4217).

## ISO4217

Bases: `str`

ISO4217 parses Currency in the [ISO 4217](https://en.wikipedia.org/wiki/ISO_4217) format.

```py
from pydantic import BaseModel

from pydantic_extra_types.currency_code import ISO4217


class Currency(BaseModel):
    alpha_3: ISO4217


currency = Currency(alpha_3='AED')
print(currency)
# > alpha_3='AED'

```

## Currency

Bases: `str`

Currency parses currency subset of the [ISO 4217](https://en.wikipedia.org/wiki/ISO_4217) format. It excludes bonds testing codes and precious metals.

```py
from pydantic import BaseModel

from pydantic_extra_types.currency_code import Currency


class currency(BaseModel):
    alpha_3: Currency


cur = currency(alpha_3='AED')
print(cur)
# > alpha_3='AED'

```
