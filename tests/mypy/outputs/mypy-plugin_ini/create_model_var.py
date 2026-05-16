from pydantic import BaseModel, create_model


class Model(BaseModel):
    a: int


SubModel = create_model('SubModel', __base__=Model)


class Main(BaseModel):
    sub: SubModel


# This only crashes in parallel mode (see https://github.com/python/mypy/issues/21472):
def dyn_model() -> type[BaseModel]:
    Inner = create_model("Inner", __base__=BaseModel, value=(int, ...))

    class Outer(Inner):
        pass

    return Outer
