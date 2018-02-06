from pydantic import BaseModel, create_model


class StaticModel(BaseModel):
    foo: str
    bar: int = 123


DynamicModel = create_model('DynamicModel', foo=(str, ...), bar=123)
