from typing import Literal, Union, Optional

from pydantic import BaseModel, Field, ValidationError


class RequestV1(BaseModel):
    version: Optional[Literal[1]] = 1
    items: list[str]


class RequestV2(BaseModel):
    version: Literal[2]
    items: list[dict[str, str]]


class Body(BaseModel):
    request: Union[RequestV1, RequestV2] = Field(..., discriminator='version')


print(Body(request={'items': ['apple', 'orange']}))
print(Body(request={'version': 2, 'items': [{'name': 'apple'}]}))
try:
    Body(request={'items': [{'name': 'apple'}]})
except ValidationError as e:
    print(e)
