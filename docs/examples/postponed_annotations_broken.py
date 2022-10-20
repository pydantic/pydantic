from __future__ import annotations
from pydantic import BaseModel
from pydantic.errors import PydanticUserError


def this_is_broken():
    from pydantic import HttpUrl  # HttpUrl is defined in functuon local scope

    class Model(BaseModel):
        a: HttpUrl

    try:
        Model(a='https://example.com')
    except PydanticUserError as e:
        print(e)

    try:
        Model.update_forward_refs()
    except NameError as e:
        print(e)


this_is_broken()
