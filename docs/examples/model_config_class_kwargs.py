from pydantic import BaseModel, ValidationError, Extra


class Model(BaseModel, extra=Extra.forbid):
    a: str


try:
    Model(a='spam', b='oh no')
except ValidationError as e:
    print(e)
