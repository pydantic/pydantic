from pydantic import BaseModel, PrivateAttr


# private attributes should be excluded from
# the synthesized `__init__` method:
class ModelWithPrivateAttr(BaseModel):
    _private_field: str = PrivateAttr()


m = ModelWithPrivateAttr()
