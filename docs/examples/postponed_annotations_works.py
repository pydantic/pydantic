from __future__ import annotations
from pydantic import BaseModel
from pydantic import HttpUrl  # HttpUrl is defined in the module's global scope


def this_works():
    class Model(BaseModel):
        a: HttpUrl

    print(Model(a='https://example.com'))


this_works()
