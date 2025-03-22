from typing import TypedDict

from typing_extensions import assert_type

from pydantic import ConfigDict, with_config


@with_config(ConfigDict(str_to_lower=True))
class Model1(TypedDict):
    a: str


@with_config(str_to_lower=True)
class Model2(TypedDict):
    pass


@with_config(config=ConfigDict(str_to_lower=True))  # pyright: ignore[reportDeprecated]
class Model3(TypedDict):
    pass


assert_type(Model1, type[Model1])

model = Model1(a='ABC')

assert_type(model, Model1)
