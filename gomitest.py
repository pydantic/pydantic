from pydantic import ConfigDict, BaseModel, ValidationError
from pydantic.dataclasses import dataclass

# Throws error:
# frozen is none and wrapper is True
@dataclass(config=ConfigDict(frozen=True))
class Location:
    latitude: float
    longitude: float

location = Location(latitude=0, longitude=0)
print(hash(location))
# TypeError: unhashable type: 'Location'


# Works:
# frozen is not none and wrapper is False
@dataclass(frozen=True)
class Location:
    latitude: float
    longitude: float

location = Location(latitude=0, longitude=0)
print(hash(location))
# -8458139203682520985


@dataclass(frozen=True, config=ConfigDict(frozen=True))
class Location:
    latitude: float
    longitude: float

location = Location(latitude=0, longitude=0)
print(hash(location))
# -8458139203682520985

class Model(BaseModel):
    x: int

    model_config = ConfigDict(frozen=True)

m = Model(x=1)

try:
    m.x = 2
    print("m.x = 2 is ok")
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'frozen_instance'