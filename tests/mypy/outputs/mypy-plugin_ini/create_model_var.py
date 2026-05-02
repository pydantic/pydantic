from typing import Any

from typing_extensions import Self

from pydantic import BaseModel, create_model


class Model(BaseModel):
    a: int


SubModel = create_model('SubModel', __base__=Model)


class Main(BaseModel):
    sub: SubModel


class ClassmethodModel(BaseModel):
    @classmethod
    def composite(cls) -> type[Self]:
        fields: dict[str, Any] = {'plugin_id': (int, ...)}
        model = create_model(cls.__name__, __base__=cls, **fields)
        return model
