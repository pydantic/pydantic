The `pydantic_extra_types.coordinate` module provides the Latitude, Longitude, and Coordinate data types.

## Latitude

Bases: `float`

Latitude value should be between -90 and 90, inclusive.

Supports both float and Decimal types.

```py
from decimal import Decimal
from pydantic import BaseModel
from pydantic_extra_types.coordinate import Latitude


class Location(BaseModel):
    latitude: Latitude


# Using float
location1 = Location(latitude=41.40338)
# Using Decimal
location2 = Location(latitude=Decimal('41.40338'))

```

## Longitude

Bases: `float`

Longitude value should be between -180 and 180, inclusive.

Supports both float and Decimal types.

```py
from decimal import Decimal
from pydantic import BaseModel

from pydantic_extra_types.coordinate import Longitude


class Location(BaseModel):
    longitude: Longitude


# Using float
location1 = Location(longitude=2.17403)
# Using Decimal
location2 = Location(longitude=Decimal('2.17403'))

```

## Coordinate

```python
Coordinate(latitude: Latitude, longitude: Longitude)

```

Bases: `Representation`

Coordinate parses Latitude and Longitude.

You can use the `Coordinate` data type for storing coordinates. Coordinates can be defined using one of the following formats:

1. Tuple: `(Latitude, Longitude)`. For example: `(41.40338, 2.17403)` or `(Decimal('41.40338'), Decimal('2.17403'))`.
1. `Coordinate` instance: `Coordinate(latitude=Latitude, longitude=Longitude)`.

```py
from decimal import Decimal
from pydantic import BaseModel

from pydantic_extra_types.coordinate import Coordinate


class Location(BaseModel):
    coordinate: Coordinate


# Using float values
location1 = Location(coordinate=(41.40338, 2.17403))
# > coordinate=Coordinate(latitude=41.40338, longitude=2.17403)

# Using Decimal values
location2 = Location(coordinate=(Decimal('41.40338'), Decimal('2.17403')))
# > coordinate=Coordinate(latitude=41.40338, longitude=2.17403)

```
