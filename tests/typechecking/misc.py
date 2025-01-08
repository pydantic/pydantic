from pydantic import BaseModel


class Sub(BaseModel):
    a: int
    b: int


class Model(BaseModel):
    subs: list[Sub]


def func(model: Model) -> None:
    model.model_dump(
        include={'a': {1: True}},
    )
    model.model_dump(
        include={'a': {'__all__': True}},
    )
    model.model_dump(
        include={'a': {1: {'a'}}},
    )
    model.model_dump(
        include={'a': {1, 2}},
    )

    # Invalid cases, should fail but the `IncEx` alias uses `bool` due to mypy limitations:
    model.model_dump(
        include={'a': {1: False}},
    )
