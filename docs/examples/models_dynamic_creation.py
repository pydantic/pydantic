from pydantic import BaseModel, create_model

DynamicFoobarModel = create_model('DynamicFoobarModel', foo=(str, ...), bar=123)


class StaticFoobarModel(BaseModel):
    foo: str
    bar: int = 123
