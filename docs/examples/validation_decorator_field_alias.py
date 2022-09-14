from pydantic import Field, validate_arguments
from typing_extensions import Annotated


@validate_arguments
def how_many(num: Annotated[int, Field(gt=10, alias='number')]):
    return num


how_many(number=42)
