from pydantic import BaseModel


class Model(BaseModel):
    pass


m = Model()


def example_func() -> Model:
    return m
