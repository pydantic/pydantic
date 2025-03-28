The `pydantic_extra_types.coordinate` module provides the Latitude, Longitude, and Coordinate data types.

## Latitude

Bases: `float`

Latitude value should be between -90 and 90, inclusive.

```py
from pydantic import BaseModel
from pydantic_extra_types.coordinate import Latitude

class Location(BaseModel):
    latitude: Latitude

location = Location(latitude=41.40338)
print(location)
#> latitude=41.40338

```

## Longitude

Bases: `float`

Longitude value should be between -180 and 180, inclusive.

```py
from pydantic import BaseModel

from pydantic_extra_types.coordinate import Longitude

class Location(BaseModel):
    longitude: Longitude

location = Location(longitude=2.17403)
print(location)
#> longitude=2.17403

```

## Coordinate

```python
Coordinate(latitude: Latitude, longitude: Longitude)

```

Bases: `Representation`

Coordinate parses Latitude and Longitude.

You can use the `Coordinate` data type for storing coordinates. Coordinates can be defined using one of the following formats:

1. Tuple: `(Latitude, Longitude)`. For example: `(41.40338, 2.17403)`.
1. `Coordinate` instance: `Coordinate(latitude=Latitude, longitude=Longitude)`.

```py
from pydantic import BaseModel

from pydantic_extra_types.coordinate import Coordinate

class Location(BaseModel):
    coordinate: Coordinate

location = Location(coordinate=(41.40338, 2.17403))
#> coordinate=Coordinate(latitude=41.40338, longitude=2.17403)

```
