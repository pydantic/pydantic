from uuid import uuid4

from pydantic import BaseModel, Field
from typing_extensions import Annotated


class Foo(BaseModel):
    id: Annotated[str, Field(default_factory=lambda: uuid4().hex)]
    name: Annotated[str, Field(max_length=256)] = 'Bar'
