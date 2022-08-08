from pydantic import Field, validate_arguments
from pydantic.typing import Annotated


@validate_arguments
def how_many(num: Annotated[int, Field(gt=10, alias='number')]):
    return num


how_many(number=42)
