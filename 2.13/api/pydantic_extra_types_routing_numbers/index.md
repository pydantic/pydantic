The `pydantic_extra_types.routing_number` module provides the ABARoutingNumber data type.

## ABARoutingNumber

```python
ABARoutingNumber(routing_number: str)

```

Bases: `str`

The `ABARoutingNumber` data type is a string of 9 digits representing an ABA routing transit number.

The algorithm used to validate the routing number is described in the [ABA routing transit number](https://en.wikipedia.org/wiki/ABA_routing_transit_number#Check_digit) Wikipedia article.

```py
from pydantic import BaseModel

from pydantic_extra_types.routing_number import ABARoutingNumber


class BankAccount(BaseModel):
    routing_number: ABARoutingNumber


account = BankAccount(routing_number='122105155')
print(account)
# > routing_number='122105155'

```

Source code in `pydantic_extra_types/routing_number.py`

```python
def __init__(self, routing_number: str):
    self._validate_digits(routing_number)
    self._routing_number = self._validate_routing_number(routing_number)

```
