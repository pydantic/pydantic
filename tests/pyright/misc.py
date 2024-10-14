from pydantic import BaseModel


class Sub(BaseModel):
    a: int
    b: int


class Model(BaseModel):
    subs: list[Sub]


def func(model: Model) -> None:
    model.model_dump(
        include={'a': {1: True}},  # type: ignore[arg-type]
    )
    model.model_dump(
        include={'a': {'__all__': True}},  # type: ignore[arg-type]
    )
    model.model_dump(
        include={'a': {1: {'a'}}},
    )
    model.model_dump(
        include={'a': {1, 2}},
    )

    # Invalid cases:
    model.model_dump(
        include={'a': {1: False}},  # type: ignore[arg-type]  # pyright: ignore[reportArgumentType]
    )
