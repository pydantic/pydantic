from pydantic import BaseModel, create_model

Model: type[BaseModel] = create_model('Model')

m = Model()


def example_func() -> Model:
    return m
