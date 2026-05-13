from pydantic import BaseModel, create_model


class Model(BaseModel):
    a: int


SubModel = create_model('SubModel', __base__=Model)


class Main(BaseModel):
    sub: SubModel


def dyn_model() -> type[BaseModel]:
    Inner = create_model("Inner", __base__=BaseModel, value=(int, ...))

    class Outer(Inner):
        pass

    return Outer
