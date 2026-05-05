from pydantic import BaseModel, create_model


class Model(BaseModel):
    a: int


SubModel = create_model('SubModel', __base__=Model)


class Main(BaseModel):
    sub: SubModel
