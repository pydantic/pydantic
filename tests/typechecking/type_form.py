from typing import Annotated

from pydantic import ValidateAs, create_model, field_serializer

Model = create_model(
    'Model',
    f1=int | str,
    f2=(Annotated[int, ...], 1),
)


def hook_1(v: int | str): ...


ValidateAs(int | str, hook_1)
ValidateAs(Annotated[float, ...], hook_1)  # type: ignore[arg-type]  # pyright: ignore[reportArgumentType]


field_serializer('a', return_type=int | str)
