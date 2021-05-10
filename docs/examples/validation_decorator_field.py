from datetime import datetime
from pydantic import validate_arguments, Field, ValidationError
from pydantic.typing import Annotated


@validate_arguments
def how_many(num: Annotated[int, Field(gt=10)]):
    return num


try:
    how_many(1)
except ValidationError as e:
    print(e)


@validate_arguments
def when(dt: datetime = Field(default_factory=datetime.now)):
    return dt


print(type(when()))
